"""Pure-python learning model and decision logic (no Home Assistant imports).

Model per strategy (airco / cv / both) and per outdoor-temperature bin:
  rate        heat-up speed in degC per hour
  kwh_per_deg electricity used per degC of heat-up
  m3_per_deg  gas used per degC of heat-up
  kwh_per_hk  electricity per hour per K (room target - outdoor) while maintaining
  m3_per_hk   gas per hour per K while maintaining
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

STRAT_AIRCO = "airco"
STRAT_CV = "cv"
STRAT_BOTH = "both"
STRAT_OFF = "off"
STRATEGIES = [STRAT_AIRCO, STRAT_CV, STRAT_BOTH]

PHASE_HEAT = "heat_up"
PHASE_MAINTAIN = "maintain"
PHASE_OFF = "off"

REASONS = ["off", "sensor_unavailable", "no_source", "comfort", "eco", "preheat",
           "manual", "learn_only", "manual_override"]

BIN_EDGES = [-5.0, 0.0, 5.0, 10.0, 15.0]
BIN_LABELS = ["<-5", "-5..0", "0..5", "5..10", "10..15", ">15"]

HEAT_KEYS = ("rate", "kwh_per_deg", "m3_per_deg")
MAINT_KEYS = ("kwh_per_hk", "m3_per_hk")

DEFAULT_PARAMS = {
    STRAT_AIRCO: {"rate": 1.5, "kwh_per_deg": 0.5, "m3_per_deg": 0.0,
                  "kwh_per_hk": 0.035, "m3_per_hk": 0.0},
    STRAT_CV: {"rate": 1.0, "kwh_per_deg": 0.0, "m3_per_deg": 0.12,
               "kwh_per_hk": 0.0, "m3_per_hk": 0.012},
}
# Heat pumps get less efficient in the cold: scale default airco energy per bin.
AIRCO_DEFAULT_SCALE = [1.6, 1.3, 1.1, 1.0, 0.9, 0.85]

LIMITS = {
    "rate": (0.05, 10.0),
    "kwh_per_deg": (0.0, 10.0),
    "m3_per_deg": (0.0, 2.0),
    "kwh_per_hk": (0.0, 1.0),
    "m3_per_hk": (0.0, 0.2),
}
ALPHA_MIN = 0.1


def bin_index(t_out: float) -> int:
    idx = 0
    for edge in BIN_EDGES:
        if t_out >= edge:
            idx += 1
    return idx


def _clamp(key: str, value: float) -> float:
    lo, hi = LIMITS[key]
    return max(lo, min(hi, value))


class LearningModel:
    """Stores learned parameters; data is JSON-serialisable."""

    def __init__(self, data: dict | None = None) -> None:
        self.data: dict = data or {}

    # ---- lookup -------------------------------------------------------
    def _default(self, strategy: str, idx: int) -> dict:
        p = dict(DEFAULT_PARAMS[strategy])
        if strategy == STRAT_AIRCO:
            s = AIRCO_DEFAULT_SCALE[idx]
            p["kwh_per_deg"] *= s
            p["kwh_per_hk"] *= s
        return p

    def _nearest(self, strategy: str, idx: int, count_key: str) -> dict | None:
        bins = self.data.get(strategy, {})
        for dist in range(len(BIN_LABELS)):
            for cand in (idx - dist, idx + dist):
                b = bins.get(str(cand))
                if b and b.get(count_key, 0) > 0:
                    return b
        return None

    def params(self, strategy: str, t_out: float) -> dict:
        idx = bin_index(t_out)
        if strategy == STRAT_BOTH:
            learned = self._nearest(STRAT_BOTH, idx, "n_heat")
            if learned:
                p = {k: learned[k] for k in HEAT_KEYS}
                p["learned"] = True
            else:
                a = self.params(STRAT_AIRCO, t_out)
                c = self.params(STRAT_CV, t_out)
                rate = a["rate"] + c["rate"]
                p = {
                    "rate": rate,
                    "kwh_per_deg": a["kwh_per_deg"] * a["rate"] / rate,
                    "m3_per_deg": c["m3_per_deg"] * c["rate"] / rate,
                    "learned": False,
                }
            p["kwh_per_hk"] = 0.0
            p["m3_per_hk"] = 0.0
            return p

        p = self._default(strategy, idx)
        heat = self._nearest(strategy, idx, "n_heat")
        maint = self._nearest(strategy, idx, "n_maint")
        if heat:
            p.update({k: heat[k] for k in HEAT_KEYS})
        if maint:
            p.update({k: maint[k] for k in MAINT_KEYS})
        p["learned"] = bool(heat or maint)
        return p

    # ---- update -------------------------------------------------------
    def _bin(self, strategy: str, t_out: float) -> dict:
        idx = bin_index(t_out)
        bins = self.data.setdefault(strategy, {})
        b = bins.get(str(idx))
        if b is None:
            base = (self.params(strategy, t_out) if strategy == STRAT_BOTH
                    else self._default(strategy, idx))
            b = {k: base[k] for k in HEAT_KEYS + MAINT_KEYS}
            b["n_heat"] = 0
            b["n_maint"] = 0
            bins[str(idx)] = b
        return b

    @staticmethod
    def _ema(old: float, new: float, n: int) -> float:
        alpha = max(ALPHA_MIN, 1.0 / (n + 1))
        return old + alpha * (new - old)

    def update_heat(self, strategy, t_out, rate, kwh_per_deg, m3_per_deg) -> None:
        b = self._bin(strategy, t_out)
        n = b["n_heat"]
        for key, val in (("rate", rate), ("kwh_per_deg", kwh_per_deg),
                         ("m3_per_deg", m3_per_deg)):
            b[key] = self._ema(b[key], _clamp(key, val), n)
        b["n_heat"] = n + 1

    def update_maint(self, strategy, t_out, kwh_per_hk, m3_per_hk) -> None:
        b = self._bin(strategy, t_out)
        n = b["n_maint"]
        for key, val in (("kwh_per_hk", kwh_per_hk), ("m3_per_hk", m3_per_hk)):
            b[key] = self._ema(b[key], _clamp(key, val), n)
        b["n_maint"] = n + 1

    def summary(self) -> dict:
        out = {}
        for strat, bins in self.data.items():
            for idx, b in bins.items():
                out[f"{strat} {BIN_LABELS[int(idx)]}"] = {
                    k: (round(v, 4) if isinstance(v, float) else v)
                    for k, v in b.items()
                }
        return out

    def sample_count(self) -> int:
        return sum(b.get("n_heat", 0) + b.get("n_maint", 0)
                   for bins in self.data.values() for b in bins.values())


# ---------------------------------------------------------------------------
@dataclass
class Prices:
    kwh: float
    gas: float


@dataclass
class HeatOption:
    strategy: str
    duration_h: float
    cost: float


def heatup_options(model, strategies, t_in, target, t_out, prices) -> list[HeatOption]:
    delta = max(0.0, target - t_in)
    out = []
    for s in strategies:
        p = model.params(s, t_out)
        cost = delta * (p["kwh_per_deg"] * prices.kwh + p["m3_per_deg"] * prices.gas)
        out.append(HeatOption(s, delta / p["rate"], cost))
    return out


def maintain_costs(model, strategies, target, t_out, prices) -> dict[str, float]:
    k = max(target - t_out, 0.5)
    out = {}
    for s in strategies:
        if s == STRAT_BOTH:
            continue
        p = model.params(s, t_out)
        out[s] = k * (p["kwh_per_hk"] * prices.kwh + p["m3_per_hk"] * prices.gas)
    return out


def choose_heatup(options: list[HeatOption], max_hours: float) -> HeatOption:
    fitting = [o for o in options if o.duration_h <= max_hours]
    if fitting:
        return min(fitting, key=lambda o: (o.cost, o.duration_h))
    return min(options, key=lambda o: (o.duration_h, o.cost))


def parse_time(value: str | time) -> time:
    if isinstance(value, time):
        return value
    h, m = str(value).split(":")[:2]
    return time(int(h), int(m))


def in_window(now: time, start: time, end: time) -> bool:
    if start == end:
        return False
    if start < end:
        return start <= now < end
    return now >= start or now < end


def next_start(now: datetime, start: time) -> datetime:
    cand = now.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
    if cand <= now:
        cand += timedelta(days=1)
    return cand


# ---------------------------------------------------------------------------
@dataclass
class Inputs:
    now: datetime
    t_in: float | None
    t_out: float | None
    mode: str
    manual_target: float
    comfort_temp: float
    eco_temp: float
    comfort_start: time
    comfort_end: time
    strategies: list[str]          # usable strategies right now
    prices: Prices
    hysteresis: float = 0.3
    max_heatup_h: float = 1.0
    max_preheat_h: float = 3.0
    preheat_margin_h: float = 0.25
    min_switch: timedelta = timedelta(minutes=20)


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


class Planner:
    def __init__(self) -> None:
        self.strategy = STRAT_OFF
        self.phase = PHASE_OFF
        self.last_switch: datetime | None = None
        self.preheat_deadline: datetime | None = None

    def _off(self, reason: str, target=None) -> Decision:
        self.strategy = STRAT_OFF
        self.phase = PHASE_OFF
        self.preheat_deadline = None
        return Decision(STRAT_OFF, PHASE_OFF, target, reason)

    def decide(self, i: Inputs, model: LearningModel) -> Decision:
        if i.mode == "off":
            return self._off("off")
        if i.t_in is None or i.t_out is None:
            return self._off("sensor_unavailable")
        if not i.strategies:
            return self._off("no_source")

        now = i.now
        deadline = None
        preheat_start = None
        reason = ""

        if i.mode == "auto":
            if in_window(now.time(), i.comfort_start, i.comfort_end):
                target = i.comfort_temp
                self.preheat_deadline = None
                reason = "comfort"
            else:
                target = i.eco_temp
                reason = "eco"
                nxt = next_start(now, i.comfort_start)
                if self.preheat_deadline and now < self.preheat_deadline:
                    target, deadline = i.comfort_temp, self.preheat_deadline
                    preheat_start = None
                    reason = "preheat"
                else:
                    self.preheat_deadline = None
                    if i.comfort_temp > i.t_in:
                        opts = heatup_options(model, i.strategies, i.t_in,
                                              i.comfort_temp, i.t_out, i.prices)
                        best = choose_heatup(
                            opts, max(i.max_preheat_h - i.preheat_margin_h, 0))
                        lead = timedelta(hours=best.duration_h + i.preheat_margin_h)
                        preheat_start = nxt - lead
                        if now >= preheat_start:
                            self.preheat_deadline = nxt
                            target, deadline = i.comfort_temp, nxt
                            reason = "preheat"
        else:
            target = i.manual_target
            reason = "manual"

        # Phase with hysteresis
        if self.phase == PHASE_HEAT:
            heating = i.t_in < target - 0.1
        else:
            heating = (target - i.t_in) > i.hysteresis

        maint = maintain_costs(model, i.strategies, target, i.t_out, i.prices)
        opts: list[HeatOption] = []
        if heating:
            opts = heatup_options(model, i.strategies, i.t_in, target, i.t_out, i.prices)
            if deadline:
                max_h = max((deadline - now).total_seconds() / 3600 - i.preheat_margin_h, 0)
            else:
                max_h = i.max_heatup_h
            choice = choose_heatup(opts, max_h)
            # Only fall back from a faster to a slower (cheaper) source with slack
            current = next((o for o in opts if o.strategy == self.strategy), None)
            if (self.phase == PHASE_HEAT and current and choice.strategy != current.strategy
                    and choice.duration_h > current.duration_h
                    and choice.duration_h > 0.8 * max_h):
                choice = current
            new_strategy = choice.strategy
            new_phase = PHASE_HEAT
        else:
            new_phase = PHASE_MAINTAIN
            if maint:
                new_strategy = min(maint, key=maint.get)
            else:  # only "both" usable
                new_strategy = i.strategies[0]

        # Avoid flapping within the same phase
        if (new_phase == self.phase and new_strategy != self.strategy
                and self.strategy in i.strategies and self.last_switch
                and now - self.last_switch < i.min_switch):
            new_strategy = self.strategy

        if new_strategy != self.strategy or new_phase != self.phase:
            if new_strategy != self.strategy:
                self.last_switch = now
            self.strategy, self.phase = new_strategy, new_phase

        return Decision(self.strategy, self.phase, target, reason,
                        preheat_start, deadline, opts, maint)


# ---------------------------------------------------------------------------
@dataclass
class _Window:
    key: tuple
    start: datetime
    t_in: float
    kwh: float
    m3: float
    t_outs: list


class Learner:
    """Collects measurement windows and feeds the model."""

    HEAT_MIN_H = 0.25
    HEAT_MAX_H = 0.75
    MAINT_H = 1.0

    def __init__(self, model: LearningModel) -> None:
        self.model = model
        self.win: _Window | None = None
        self.last_event: str | None = None

    def reset(self) -> None:
        self.win = None

    def tick(self, now, d: Decision, t_in, t_out, kwh, m3, dhw_active) -> str | None:
        if (d.strategy == STRAT_OFF or d.target is None or None in (t_in, t_out, kwh, m3)
                or dhw_active):
            self.win = None
            return None
        key = (d.strategy, d.phase, round(d.target, 1))
        w = self.win
        if w is not None and w.key != key:
            self._finish_heat(now, w, t_in, kwh, m3)
            w = None
        if w is None:
            self.win = _Window(key, now, t_in, kwh, m3, [t_out])
            return None
        w.t_outs.append(t_out)
        hours = (now - w.start).total_seconds() / 3600
        d_kwh, d_m3 = kwh - w.kwh, m3 - w.m3
        if d_kwh < 0 or d_m3 < 0:  # meter reset
            self.win = _Window(key, now, t_in, kwh, m3, [t_out])
            return None
        t_out_avg = sum(w.t_outs) / len(w.t_outs)
        event = None

        if d.phase == PHASE_HEAT:
            reached = t_in >= d.target - 0.1
            if hours >= self.HEAT_MAX_H or (reached and hours >= self.HEAT_MIN_H):
                event = self._finish_heat(now, w, t_in, kwh, m3)
                self.win = _Window(key, now, t_in, kwh, m3, [t_out])
        elif hours >= self.MAINT_H:
            d_k = d.target - t_out_avg
            stable = abs(t_in - d.target) <= 0.5 and abs(t_in - w.t_in) <= 0.5
            if stable and d_k >= 2:
                self.model.update_maint(d.strategy, t_out_avg,
                                        d_kwh / hours / d_k, d_m3 / hours / d_k)
                event = f"maintain {d.strategy}"
            self.win = _Window(key, now, t_in, kwh, m3, [t_out])

        if event:
            self.last_event = event
        return event

    def _finish_heat(self, now, w: _Window, t_in, kwh, m3) -> str | None:
        """Store a heat-up window if it is long enough and showed a real rise."""
        strategy, phase, _ = w.key
        hours = (now - w.start).total_seconds() / 3600
        d_t = t_in - w.t_in
        d_kwh, d_m3 = kwh - w.kwh, m3 - w.m3
        if (phase != PHASE_HEAT or hours < self.HEAT_MIN_H or d_t < 0.2
                or d_kwh < 0 or d_m3 < 0):
            return None
        t_out_avg = sum(w.t_outs) / len(w.t_outs)
        self.model.update_heat(strategy, t_out_avg, d_t / hours, d_kwh / d_t, d_m3 / d_t)
        self.last_event = f"heat-up {strategy}: {d_t / hours:.2f} °C/h"
        return self.last_event
