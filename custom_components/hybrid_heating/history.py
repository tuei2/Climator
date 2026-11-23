"""Build model samples from Home Assistant's recorder.

Two sources are used:
* state history (default the last 10 days, minute resolution): replayed through the same
  SampleCollector as live data, including hot water / window exclusions and fan mode;
* long-term hourly statistics (kept much longer) for the period before that: hourly
  samples from mean temperatures and meter sums. Hot water and windows are unknown there.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AIRCO, CONF_AIRCO_ENERGY, CONF_DHW, CONF_GAS, CONF_OUTDOOR_SENSOR, CONF_ROOM_SENSOR,
    CONF_SOLAR, CONF_WINDOWS,
)
from .model import Sample, SampleCollector

_LOGGER = logging.getLogger(__name__)

BAD = ("unavailable", "unknown", "", None)
HEAT_MODES = ("heat", "heat_cool", "auto")
WINDOW_BLOCK_MIN = 15


def _as_list(v) -> list[str]:
    if not v:
        return []
    return [v] if isinstance(v, str) else list(v)


def _scale(unit: str | None) -> float:
    return {"Wh": 0.001, "W": 0.001, "MWh": 1000.0, "MW": 1000.0, "L": 0.001}.get(unit or "", 1.0)


def _num(state: State | None) -> float | None:
    if state is None or state.state in BAD:
        return None
    try:
        return float(state.state) * _scale(state.attributes.get("unit_of_measurement"))
    except (TypeError, ValueError):
        return None


def _steps(states: list[State]) -> list[tuple[float, State]]:
    return sorted(((s.last_updated.timestamp(), s) for s in states), key=lambda x: x[0])


class _Cursor:
    """Walks a step function forward in time."""

    def __init__(self, steps):
        self.steps, self.i, self.cur = steps, 0, None

    def at(self, ts: float):
        while self.i < len(self.steps) and self.steps[self.i][0] <= ts:
            self.cur = self.steps[self.i][1]
            self.i += 1
        return self.cur


def _replay_states(hist: dict, conf: dict, boost_mode: str | None, start: datetime,
                   end: datetime) -> tuple[list[Sample], dict]:
    """Minute-by-minute replay of recorded states (runs in a worker thread)."""
    cur = {k: _Cursor(_steps(hist.get(conf.get(k) or "", []))) for k in
           (CONF_ROOM_SENSOR, CONF_OUTDOOR_SENSOR, CONF_AIRCO_ENERGY, CONF_GAS, CONF_SOLAR,
            CONF_DHW, CONF_AIRCO)}
    windows = [_Cursor(_steps(hist.get(w, []))) for w in _as_list(conf.get(CONF_WINDOWS))]
    col = SampleCollector()
    samples, excluded = [], {}
    window_closed_at = None
    ts = start.replace(second=0, microsecond=0).timestamp()
    end_ts = end.timestamp()
    while ts <= end_ts:
        room = _num(cur[CONF_ROOM_SENSOR].at(ts))
        out = _num(cur[CONF_OUTDOOR_SENSOR].at(ts))
        kwh = _num(cur[CONF_AIRCO_ENERGY].at(ts))
        m3 = _num(cur[CONF_GAS].at(ts))
        solar = _num(cur[CONF_SOLAR].at(ts)) if conf.get(CONF_SOLAR) else 0.0
        dhw = cur[CONF_DHW].at(ts) if conf.get(CONF_DHW) else None
        airco = cur[CONF_AIRCO].at(ts)
        any_open = any((w.at(ts) is not None and w.cur.state == "on") for w in windows)
        if any_open:
            window_closed_at = ts
        reason = None
        if dhw is not None and dhw.state == "on":
            reason = "hot_water"
        elif any_open or (window_closed_at and ts - window_closed_at < WINDOW_BLOCK_MIN * 60):
            reason = "window"
        boost = bool(airco is not None and airco.state in HEAT_MODES and boost_mode
                     and airco.attributes.get("fan_mode") == boost_mode)
        s, why = col.tick(ts, room, out, kwh, m3, max(solar or 0.0, 0.0), reason, boost)
        if s:
            samples.append(s)
        elif why:
            excluded[why] = excluded.get(why, 0) + 1
        ts += 60
    return samples, excluded


def _hourly_samples(stats: dict, conf: dict, units: dict, before: datetime) -> list[Sample]:
    """Hourly samples from long-term statistics (runs in a worker thread)."""
    def series(key, field):
        rows = stats.get(conf.get(key) or "", [])
        sc = _scale(units.get(conf.get(key)))
        out = {}
        for r in rows:
            v = r.get(field)
            if v is not None:
                out[int(r["start"] if isinstance(r["start"], (int, float)) else r["start"].timestamp())] = v * sc
        return out

    room = series(CONF_ROOM_SENSOR, "mean")
    outd = series(CONF_OUTDOOR_SENSOR, "mean")
    kwh = series(CONF_AIRCO_ENERGY, "sum")
    gas = series(CONF_GAS, "sum")
    sol = series(CONF_SOLAR, "mean") if conf.get(CONF_SOLAR) else {}
    samples = []
    limit = before.timestamp()
    for h in sorted(room):
        if h + 3600 > limit:
            break
        prev, nxt = h - 3600, h + 3600
        needed = (room.get(prev), room.get(nxt), outd.get(h), kwh.get(h), kwh.get(prev),
                  gas.get(h), gas.get(prev))
        if any(v is None for v in needed):
            continue
        d_kwh, d_m3 = kwh[h] - kwh[prev], gas[h] - gas[prev]
        if d_kwh < 0 or d_m3 < 0 or d_kwh > 6 or d_m3 > 5:
            continue
        t0 = (room[prev] + room[h]) / 2
        t1 = (room[h] + room[nxt]) / 2
        samples.append(Sample(h + 3600, t0, t1, outd[h], d_kwh, d_m3, max(sol.get(h, 0.0), 0.0), 1.0, 0.0))
    return samples


async def async_build_samples(hass: HomeAssistant, conf: dict, boost_mode: str | None,
                              days: int) -> dict:
    """Collect samples from the recorder for the last `days` days."""
    from homeassistant.components.recorder import get_instance, history, statistics

    if "recorder" not in hass.config.components:
        raise RuntimeError("recorder not available")
    rec = get_instance(hass)
    end = dt_util.utcnow()
    start = end - timedelta(days=days)
    ids = [conf.get(k) for k in (CONF_ROOM_SENSOR, CONF_OUTDOOR_SENSOR, CONF_AIRCO_ENERGY,
                                 CONF_GAS, CONF_SOLAR, CONF_DHW, CONF_AIRCO) if conf.get(k)]
    ids += _as_list(conf.get(CONF_WINDOWS))

    hist = await rec.async_add_executor_job(
        lambda: history.get_significant_states(
            hass, start, end, ids, None, True, False, False, False))
    # state history only covers the recorder's purge window; find where it starts
    first_ts = [s[0].last_updated for k in (CONF_ROOM_SENSOR, CONF_AIRCO_ENERGY, CONF_GAS)
                if (s := hist.get(conf.get(k) or "")) and s]
    state_start = max(first_ts) if first_ts else end
    state_start = max(state_start, start)

    samples, excluded = await hass.async_add_executor_job(
        _replay_states, hist, conf, boost_mode, state_start, end)

    hourly: list[Sample] = []
    if state_start - start > timedelta(hours=6):
        stat_ids = {conf.get(k) for k in (CONF_ROOM_SENSOR, CONF_OUTDOOR_SENSOR,
                                          CONF_AIRCO_ENERGY, CONF_GAS, CONF_SOLAR) if conf.get(k)}
        stats = await rec.async_add_executor_job(
            statistics.statistics_during_period, hass, start, state_start, stat_ids, "hour",
            None, {"mean", "sum"})
        units = {}
        for eid in stat_ids:
            st = hass.states.get(eid)
            units[eid] = st.attributes.get("unit_of_measurement") if st else None
        hourly = await hass.async_add_executor_job(_hourly_samples, stats, conf, units, state_start)

    return {
        "samples": hourly + samples, "excluded": excluded,
        "from": start.isoformat(), "state_from": state_start.isoformat(), "to": end.isoformat(),
        "n_state": len(samples), "n_hourly": len(hourly),
    }
