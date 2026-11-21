"""Decision logic on top of the thermal model (pure python, no Home Assistant imports)."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from .model import ThermalModel
from .schedule import comfort_at, next_block

STRAT_AIRCO = "airco"
STRAT_CV = "cv"
STRAT_BOTH = "both"
STRAT_OFF = "off"
STRATEGIES = [STRAT_AIRCO, STRAT_CV, STRAT_BOTH]

PHASE_HEAT = "heat_up"
PHASE_MAINTAIN = "maintain"
PHASE_OFF = "off"
PHASE_PAUSED = "paused"

REASONS = ["off", "sensor_unavailable", "no_source", "comfort", "eco", "preheat", "manual",
           "learn_only", "manual_override", "window_open", "away", "vacation", "buffer"]

INF = float("inf")


@dataclass
class Prices:
    kwh: float
    gas: float


def source_price(source: str, prices: Prices) -> float:
    return prices.kwh if source == STRAT_AIRCO else prices.gas


def _sources(strategy: str) -> list[str]:
    return [STRAT_AIRCO, STRAT_CV] if strategy == STRAT_BOTH else [strategy]


@dataclass
class HeatOption:
    strategy: str
    duration_h: float
    cost: float


def heatup_options(model: ThermalModel, strategies, t_in, target, t_out, prices,
                   solar=0.0) -> list[HeatOption]:
    out = []
    for s in strategies:
        dur = model.time_to(t_in, target, t_out, model.heat_rate(s, t_out), solar)
        if dur is None:
            out.append(HeatOption(s, INF, INF))
            continue
        cost_h = sum(model.pmax[src] * source_price(src, prices) for src in _sources(s))
        out.append(HeatOption(s, dur, dur * cost_h))
    return out


def maintain_costs(model: ThermalModel, strategies, target, t_out, prices,
                   solar=0.0) -> dict[str, float]:
    """EUR per hour to keep the room at target, per single source (inf if too weak)."""
    out = {}
    for s in strategies:
        if s == STRAT_BOTH:
            continue
        need = model.maintain_input(s, target, t_out, solar)
        out[s] = INF if need > model.pmax[s] * 1.05 else need * source_price(s, prices)
    return out


def choose_heatup(options: list[HeatOption], max_hours: float) -> HeatOption:
    fitting = [o for o in options if o.duration_h <= max_hours]
    if fitting:
        return min(fitting, key=lambda o: (o.cost, o.duration_h))
    return min(options, key=lambda o: (o.duration_h, o.cost))


@dataclass
class Inputs:
    now: datetime
    t_in: float | None
    t_out: float | None
    mode: str                       # "off" (learn only) | "heat" (fixed) | "auto" (schedule)
    manual_target: float
    eco_temp: float
    schedule: dict
    strategies: list[str]
    prices: Prices
    solar: float = 0.0
    tout_at: Callable[[datetime], float] | None = None
    presence: str = "home"          # home | away | vacation
    away_temp: float = 16.0
    vacation_temp: float = 14.0
    window_open: bool = False
    buffer_deg: float = 0.0         # 0 = buffering off
    buffer_threshold: float = 0.15
    hysteresis: float = 0.3
    max_heatup_h: float = 1.0
    max_preheat_h: float = 3.0
    preheat_margin_h: float = 0.25
    min_switch: timedelta = timedelta(minutes=20)

    def outdoor(self, when: datetime) -> float:
        if self.tout_at is not None:
            try:
                return self.tout_at(when)
            except Exception:  # noqa: BLE001
                pass
        return self.t_out


@dataclass
class Decision:
    strategy: str
    phase: str
    target: float | None
    reason: str
    preheat_start: datetime | None = None
    deadline: datetime | None = None
    heat_options: list[HeatOption] = field(default_factory=list)
    maintain_costs: dict = field(default_factory=dict)
    next_comfort: tuple | None = None


class Planner:
    def __init__(self) -> None:
        self.strategy = STRAT_OFF
        self.phase = PHASE_OFF
        self.last_switch: datetime | None = None
        self.preheat_deadline: datetime | None = None
        self.preheat_temp: float | None = None

    def reset(self) -> None:
        self.__init__()

    def _off(self, reason: str, phase: str = PHASE_OFF) -> Decision:
        self.strategy = STRAT_OFF
        self.phase = phase
        self.preheat_deadline = None
        return Decision(STRAT_OFF, phase, None, reason)

    # ---- preheat --------------------------------------------------------
    def _preheat_plan(self, i: Inputs, model: ThermalModel, start: datetime, temp: float):
        """Best strategy + start time to reach temp at start. Returns (start_dt, option)."""
        best = None
        for s in i.strategies:
            lead = 0.0
            dur = None
            for _ in range(5):
                begin = start - timedelta(hours=lead + i.preheat_margin_h)
                wait = max((begin - i.now).total_seconds() / 3600, 0.0)
                mid = i.now + timedelta(hours=wait / 2)
                t_begin = model.decay(i.t_in, wait, i.outdoor(mid), floor=min(i.eco_temp, i.t_in))
                t_out = i.outdoor(begin)
                dur = model.time_to(t_begin, temp, t_out, model.heat_rate(s, t_out))
                if dur is None:
                    break
                if abs(dur - lead) < 0.02:
                    lead = dur
                    break
                lead = dur
            if dur is None:
                continue
            cost_h = sum(model.pmax[src] * source_price(src, i.prices) for src in _sources(s))
            opt = HeatOption(s, lead, lead * cost_h)
            fits = lead + i.preheat_margin_h <= i.max_preheat_h
            key = (not fits, opt.cost if fits else opt.duration_h)
            if best is None or key < best[0]:
                best = (key, opt)
        if best is None:
            return None, None
        opt = best[1]
        return start - timedelta(hours=opt.duration_h + i.preheat_margin_h), opt

    # ---- main -----------------------------------------------------------
    def decide(self, i: Inputs, model: ThermalModel) -> Decision:
        if i.mode == "off":
            return self._off("off")
        if i.t_in is None or i.t_out is None:
            return self._off("sensor_unavailable")
        if not i.strategies:
            return self._off("no_source")
        if i.window_open:
            return self._off("window_open", PHASE_PAUSED)

        now = i.now
        deadline = preheat_start = next_comfort = None

        if i.presence == "vacation":
            target, reason = i.vacation_temp, "vacation"
            self.preheat_deadline = None
        elif i.mode == "heat":
            target, reason = i.manual_target, "manual"
            if i.presence == "away":
                target, reason = min(i.manual_target, i.away_temp), "away"
        else:
            comfort = comfort_at(i.schedule, now)
            if i.presence == "away":
                target, reason = (min(comfort, i.away_temp) if comfort else min(i.eco_temp, i.away_temp)), "away"
                self.preheat_deadline = None
            elif comfort is not None:
                target, reason = comfort, "comfort"
                self.preheat_deadline = None
            else:
                target, reason = i.eco_temp, "eco"
                nb = next_block(i.schedule, now)
                next_comfort = nb
                if self.preheat_deadline and now < self.preheat_deadline:
                    target, deadline, reason = self.preheat_temp, self.preheat_deadline, "preheat"
                elif nb and nb[1] > i.t_in:
                    self.preheat_deadline = None
                    preheat_start, _ = self._preheat_plan(i, model, nb[0], nb[1])
                    if preheat_start and now >= preheat_start:
                        self.preheat_deadline, self.preheat_temp = nb[0], nb[1]
                        target, deadline, reason = nb[1], nb[0], "preheat"
                else:
                    self.preheat_deadline = None

        maint = maintain_costs(model, i.strategies, target, i.t_out, i.prices, i.solar)

        # heat buffering: store heat now when the air conditioner is clearly cheaper
        if (i.buffer_deg > 0 and reason == "comfort" and i.tout_at is not None
                and STRAT_AIRCO in i.strategies):
            now_cost = i.prices.kwh / model.gain(STRAT_AIRCO, i.t_out)
            later = []
            for h in (2, 4, 6):
                when = now + timedelta(hours=h)
                if comfort_at(i.schedule, when) is None:
                    continue
                t_o = i.outdoor(when)
                later.append(min(i.prices.kwh / model.gain(STRAT_AIRCO, t_o),
                                 i.prices.gas / model.gain(STRAT_CV, t_o)))
            cheapest_now = min(maint, key=maint.get) if maint else None
            if later and cheapest_now == STRAT_AIRCO and now_cost < (1 - i.buffer_threshold) * min(later):
                target, reason = target + i.buffer_deg, "buffer"

        # phase with hysteresis
        if self.phase == PHASE_HEAT:
            heating = i.t_in < target - 0.1
        else:
            heating = (target - i.t_in) > i.hysteresis

        opts: list[HeatOption] = []
        if heating:
            opts = heatup_options(model, i.strategies, i.t_in, target, i.t_out, i.prices, i.solar)
            if deadline:
                # the preheat margin is spare time: it may be used before switching to faster
                max_h = max((deadline - now).total_seconds() / 3600, 0)
            else:
                max_h = i.max_heatup_h
            choice = choose_heatup(opts, max_h)
            current = next((o for o in opts if o.strategy == self.strategy), None)
            if (self.phase == PHASE_HEAT and current and choice.strategy != current.strategy
                    and choice.duration_h > current.duration_h
                    and choice.duration_h > 0.8 * max_h):
                choice = current
            new_strategy, new_phase = choice.strategy, PHASE_HEAT
        else:
            new_phase = PHASE_MAINTAIN
            feasible = {k: v for k, v in maint.items() if v < INF}
            if feasible:
                new_strategy = min(feasible, key=feasible.get)
            elif STRAT_BOTH in i.strategies:
                new_strategy = STRAT_BOTH
            else:
                new_strategy = min(maint, key=lambda k: model.pmax[k]) if maint else i.strategies[0]

        if (new_phase == self.phase and new_strategy != self.strategy
                and self.strategy in i.strategies and self.last_switch
                and now - self.last_switch < i.min_switch):
            new_strategy = self.strategy
        if new_strategy != self.strategy:
            self.last_switch = now
        self.strategy, self.phase = new_strategy, new_phase

        return Decision(self.strategy, self.phase, target, reason, preheat_start, deadline,
                        opts, maint, next_comfort)


def forecast(planner: Planner, base: Inputs, model: ThermalModel, hours: float = 24,
             step_min: int = 10) -> dict:
    """Simulate the coming hours: expected room temperature, target, source and cost."""
    if base.t_in is None or base.t_out is None or base.mode == "off":
        return {"points": [], "cost": None}
    p = copy.deepcopy(planner)
    t = base.t_in
    cost = 0.0
    pts = []
    step_h = step_min / 60
    now = base.now
    for n in range(int(hours * 60 / step_min) + 1):
        when = now + timedelta(minutes=n * step_min)
        t_out = base.outdoor(when)
        inp = copy.copy(base)
        inp.now, inp.t_in, inp.t_out, inp.solar, inp.window_open = when, t, t_out, 0.0, False
        d = p.decide(inp, model)
        pts.append([int(when.timestamp() * 1000), d.target, round(t, 2), d.strategy])
        if d.strategy == STRAT_OFF or d.target is None:
            t = model.decay(t, step_h, t_out)
            continue
        if d.phase == PHASE_HEAT or t < d.target - 0.05:
            heat = model.heat_rate(d.strategy, t_out)
            new_t = t + model.slope(t, t_out, heat) * step_h
            if new_t > d.target:
                frac = (d.target - t) / max(new_t - t, 1e-6)
                new_t = d.target
            else:
                frac = 1.0
            cost += frac * step_h * sum(model.pmax[s] * source_price(s, base.prices)
                                        for s in _sources(d.strategy))
            t = new_t
        elif t > d.target + 0.05:
            t = max(model.decay(t, step_h, t_out), d.target)
        else:
            src = d.strategy if d.strategy != STRAT_BOTH else STRAT_AIRCO
            cost += step_h * model.maintain_input(src, d.target, t_out) * source_price(src, base.prices)
            t = d.target
        if math.isnan(t):
            break
    return {"points": pts, "cost": round(cost, 3)}
