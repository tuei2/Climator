"""Home Assistant side: reads entities, learns the model, runs the planner, controls devices."""

from __future__ import annotations

import copy
import logging
from datetime import datetime, timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AIRCO, CONF_AIRCO_ENERGY, CONF_AIRCO_MIN_OUTDOOR, CONF_AIRCO_OFFSET,
    CONF_ALLOW_BOTH, CONF_AWAY_DELAY, CONF_BUFFER_DEG, CONF_BUFFER_THRESHOLD, CONF_CV,
    CONF_CV_OFFSET, CONF_CV_SETBACK, CONF_DHW, CONF_GAS, CONF_HYSTERESIS, CONF_MAX_HEATUP,
    CONF_MAX_PREHEAT, CONF_MIN_SWITCH, CONF_NOTIFY_AFTER, CONF_OUTDOOR_SENSOR,
    CONF_OVERRIDE_MINUTES, CONF_PREHEAT_MARGIN, CONF_PRESENCE, CONF_PRICE_GAS, CONF_PRICE_KWH,
    CONF_ROOM_SENSOR, CONF_SOLAR, CONF_WEATHER, CONF_WINDOW_DELAY, CONF_WINDOWS,
    DEFAULT_FEATURES, DEFAULT_OPTIONS, DEFAULT_SETTINGS, DOMAIN, MODE_HEAT, MODE_OFF,
    STORAGE_VERSION, UPDATE_INTERVAL_SECONDS, VERSION,
)
from .history import async_build_samples
from .model import SampleCollector, ThermalModel
from .planner import (
    PHASE_HEAT, PHASE_MAINTAIN, PHASE_OFF, STRAT_AIRCO, STRAT_BOTH, STRAT_CV, STRAT_OFF,
    Decision, Inputs, Planner, Prices, choose_setback, forecast, what_if,
)
from .schedule import _t as parse_hhmm
from .schedule import DEFAULT_SCHEDULE, comfort_at, validate

_LOGGER = logging.getLogger(__name__)

BAD_STATES = (STATE_UNAVAILABLE, STATE_UNKNOWN, None, "")
RESEND_AFTER = timedelta(minutes=5)
OVERRIDE_GRACE = timedelta(seconds=120)
HEAT_MODES = ("heat", "heat_cool", "auto")
HOME_STATES = ("home", "on", "true")
WINDOW_LEARN_BLOCK = timedelta(minutes=15)
FORECAST_REFRESH = timedelta(minutes=30)
NOTIFY_ID = "climator_{}"
SETBACK_EVERY = timedelta(minutes=30)
EXPLORE_MAX = timedelta(minutes=120)
EXPLORE_SAMPLES = 4             # ~1 hour of useful data ends a test
EXPLORE_REASONS = ("comfort", "eco", "preheat", "manual")
FORECAST_EVERY = timedelta(minutes=10)
SCENARIOS_EVERY = timedelta(minutes=60)
FORECAST_HOURS = 72
BOOST_WORDS = ["powerful", "turbo", "max", "high", "5", "strong", "mediumhigh", "4"]
SOFT_WORDS = ["quiet", "silence", "silent", "night", "low", "1", "lowmedium", "2"]


def _as_list(v) -> list[str]:
    if not v:
        return []
    return [v] if isinstance(v, str) else list(v)


class HybridHeatingController:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.conf = {**DEFAULT_OPTIONS, **entry.data, **entry.options}
        self._store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.settings: dict = dict(DEFAULT_SETTINGS)
        self.features: dict = dict(DEFAULT_FEATURES)
        self.schedule: dict = validate(DEFAULT_SCHEDULE)
        self.model = ThermalModel()
        self.collector = SampleCollector()
        self.planner = Planner()
        self.decision: Decision = Decision(STRAT_OFF, PHASE_OFF, None, "off")
        self.forecast_result: dict = {"points": [], "cost": None}
        self.t_in: float | None = None
        self.t_out: float | None = None
        self.solar_kw: float | None = None
        self._listeners: list[Callable[[], None]] = []
        self._unsub = None
        self._last_cmd: dict[str, tuple] = {}
        self._expected: dict[str, tuple] = {}
        self.override_until: datetime | None = None
        self.override_entity: str | None = None
        self.costs: dict = {"airco": 0.0, "cv": 0.0}
        self._prev_meter: tuple | None = None
        self.day_start: dict = {"date": None, "airco": 0.0, "cv": 0.0}
        # windows / presence
        self.window_open = False
        self.open_windows: list[str] = []
        self._window_since: datetime | None = None
        self._window_closed_at: datetime | None = None
        self.presence = "home"
        self._away_since: datetime | None = None
        # weather forecast
        self._forecast: list[tuple[float, float]] = []   # (timestamp, temp)
        self._forecast_fetched: datetime | None = None
        self.weather_bias = 0.0
        self.forecast_error: str | None = None
        # insight
        self.comfort: dict = {}            # date -> [ok_minutes, total_minutes]
        self.events: dict = {"overrides": [], "windows": []}
        self.suggestions: list[dict] = []
        self.diag_counters: dict = {"airco_on_min": 0, "airco_kwh": 0.0,
                                    "cv_on_min": 0, "cv_m3": 0.0}
        self._unavailable_since: dict[str, datetime] = {}
        self._notified: set[str] = set()
        self.last_sample_reason: str | None = None
        self._last_daily: str | None = None
        self._last_forecast_calc: datetime | None = None
        self._last_scenarios: datetime | None = None
        self._forecast_busy = False
        self.forecast_hypothetical = False
        self.scenarios: dict = {"base": None, "scenarios": []}
        # smart setback: chosen night/eco level for the current setback period
        self.setback: dict | None = None
        self._last_setback: datetime | None = None
        # training from recorder history
        self.history_result: dict | None = None
        self.history_busy = False
        # self-testing ("explore")
        self.explore: dict | None = None        # running test session
        self.explore_log: list = []
        self.explore_spent: dict = {}           # iso week -> EUR

    # ---- lifecycle ----------------------------------------------------
    async def async_setup(self) -> None:
        data = await self._store.async_load() or {}
        old = data.get("settings", {})
        self.settings.update({k: v for k, v in old.items() if k in DEFAULT_SETTINGS
                              or k in (CONF_PRICE_KWH, CONF_PRICE_GAS)})
        self.features.update(data.get("features", {}))
        if "schedule" in data:
            try:
                self.schedule = validate(data["schedule"])
            except (ValueError, KeyError, TypeError):
                _LOGGER.warning("Stored schedule invalid, using default")
        elif "comfort_start" in old:  # migrate the single comfort block of v0.3/0.4
            block = {"start": old["comfort_start"], "end": old.get("comfort_end", "22:30"),
                     "temp": old.get("comfort_temp", 20.5), "enabled": True}
            self.schedule = validate({"profiles": {"workday": [block], "weekend": [block]},
                                      "days": DEFAULT_SCHEDULE["days"]})
        self.model = ThermalModel.from_dict(data.get("thermal"))
        self.costs.update(data.get("costs", {}))
        self.day_start.update(data.get("day_start", {}))
        self.comfort = data.get("comfort", {})
        self.events.update(data.get("events", {}))
        self.suggestions = data.get("suggestions", [])
        self.weather_bias = data.get("weather_bias", 0.0)
        self.explore_log = data.get("explore_log", [])
        self.history_result = data.get("history_result")
        self.explore_spent = data.get("explore_spent", {})
        for key in (CONF_PRICE_KWH, CONF_PRICE_GAS):
            self.settings.setdefault(key, float(self.conf[key]))

    @callback
    def async_start(self) -> None:
        self._unsub = async_track_time_interval(
            self.hass, self._async_tick, timedelta(seconds=UPDATE_INTERVAL_SECONDS))
        self.hass.async_create_task(self._async_tick())
        if self.model.n_eff < 20 and self.history_result is None:
            # fresh model: learn from what Home Assistant already recorded
            from homeassistant.helpers.event import async_call_later

            async def _bootstrap(_now) -> None:
                await self.async_train_from_history(30, automatic=True)

            self._unsub_boot = async_call_later(self.hass, 90, _bootstrap)

    async def async_train_from_history(self, days: int = 30, automatic: bool = False) -> dict:
        """Rebuild the model from recorder history (replaces the learned data)."""
        if self.history_busy:
            return {"error": "busy"}
        self.history_busy = True
        self._notify()
        before = self.model.check()
        try:
            res = await async_build_samples(self.hass, self.conf, self.fan_mode_for("boost"), days)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Training from history failed: %s", err)
            self.history_result = {"error": str(err), "time": dt_util.now().isoformat()}
            self.history_busy = False
            self._notify()
            return self.history_result
        samples = res["samples"]
        if len(samples) < 8:
            self.history_result = {"error": "too_little_data", "time": dt_util.now().isoformat(),
                                   "n_state": res["n_state"], "n_hourly": res["n_hourly"]}
        else:
            new = ThermalModel()

            def _train() -> None:
                for smp in samples:
                    new.add_sample(smp)
                new.estimate_pmax(samples)
                new.excluded = dict(res["excluded"])

            await self.hass.async_add_executor_job(_train)
            self.model.__dict__.update(new.__dict__)
            self.collector.reset()
            after = self.model.check()
            self.history_result = {
                "time": dt_util.now().isoformat(), "days": days, "automatic": automatic,
                "from": res["from"], "state_from": res["state_from"], "to": res["to"],
                "n_state": res["n_state"], "n_hourly": res["n_hourly"],
                "excluded": res["excluded"],
                "mae_before": round(before["mae_1h"], 3) if before["mae_1h"] is not None else None,
                "mae_after": round(after["mae_1h"], 3) if after["mae_1h"] is not None else None,
            }
            self._last_forecast_calc = None
            self._last_setback = None
            self._last_scenarios = None
            _LOGGER.info("Model rebuilt from history: %s state samples, %s hourly samples",
                         res["n_state"], res["n_hourly"])
        self.history_busy = False
        await self._store.async_save(self._data())
        self._notify()
        return self.history_result

    async def async_shutdown(self) -> None:
        if getattr(self, "_unsub_boot", None):
            self._unsub_boot()
            self._unsub_boot = None
        if self._unsub:
            self._unsub()
            self._unsub = None
        await self._store.async_save(self._data())

    def _data(self) -> dict:
        return {
            "version": VERSION, "settings": self.settings, "features": self.features,
            "schedule": self.schedule, "thermal": self.model.to_dict(), "costs": self.costs,
            "day_start": self.day_start, "comfort": self.comfort, "events": self.events,
            "suggestions": self.suggestions, "weather_bias": self.weather_bias,
            "explore_log": self.explore_log, "explore_spent": self.explore_spent,
            "history_result": self.history_result,
        }

    def _save(self) -> None:
        self._store.async_delay_save(self._data, 60)

    # ---- listeners ----------------------------------------------------
    @callback
    def async_add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(cb)
        return lambda: self._listeners.remove(cb)

    @callback
    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb()

    # ---- settings -----------------------------------------------------
    def _clear_override(self) -> None:
        self.override_until = None
        self.override_entity = None
        self._expected.clear()
        self._last_cmd.clear()

    async def async_set_setting(self, key: str, value) -> None:
        self.settings[key] = value
        self._clear_override()
        self._last_forecast_calc = None
        self._last_setback = None
        self._save()
        await self._async_tick()

    async def async_set_manual_target(self, value: float) -> None:
        self.settings["manual_target"] = value
        await self.async_set_setting("mode", MODE_HEAT)

    async def async_set_feature(self, feature: str, on: bool) -> None:
        self.features[feature] = bool(on)
        self._last_scenarios = None
        self._last_setback = None
        if feature == "notifications" and not on:
            for nid in list(self._notified):
                self._dismiss(nid)
        self._last_forecast_calc = None
        self._save()
        await self._async_tick()

    async def async_set_schedule(self, schedule: dict) -> None:
        self.schedule = validate(schedule)
        self.planner.reset()
        self._last_setback = None
        self._last_forecast_calc = None
        self._save()
        await self._async_tick()

    async def async_reset(self, scope: str = "all") -> None:
        if scope in ("all", "model"):
            self.model.reset()
            self.collector.reset()
        if scope in ("all", "costs"):
            self.costs = {"airco": 0.0, "cv": 0.0}
            self.day_start = {"date": None, "airco": 0.0, "cv": 0.0}
        if scope in ("all", "comfort"):
            self.comfort = {}
        if scope in ("all", "suggestions"):
            self.suggestions = []
            self.events = {"overrides": [], "windows": []}
        if scope in ("all", "weather"):
            self.weather_bias = 0.0
        self._save()
        self._notify()

    def feature_active(self, feature: str) -> bool:
        if not self.features.get(feature, False):
            return False
        if feature == "fan":
            return len(self.fan_modes()) >= 2
        if feature == "explore":
            return len(self._strategies(self.t_out)) >= 2
        need = {"windows": CONF_WINDOWS, "presence": CONF_PRESENCE, "forecast": CONF_WEATHER,
                "buffer": CONF_WEATHER, "solar": CONF_SOLAR}.get(feature)
        return not need or bool(_as_list(self.conf.get(need)))

    # ---- fan ----------------------------------------------------------
    def fan_modes(self) -> list[str]:
        st = self.hass.states.get(self.conf.get(CONF_AIRCO) or "")
        return list(st.attributes.get("fan_modes") or []) if st else []

    def fan_mode_for(self, kind: str) -> str | None:
        """The airco fan mode used for 'boost' (heating up) or 'comfort' (keeping warm)."""
        modes = self.fan_modes()
        if not modes:
            return None
        chosen = self.settings.get(f"fan_{kind}_mode")
        if chosen in modes:
            return chosen
        real = [m for m in modes if str(m).lower() not in ("auto", "automatic")] or modes
        words = BOOST_WORDS if kind == "boost" else SOFT_WORDS
        for w in words:
            for m in real:
                if str(m).lower().replace(" ", "").replace("_", "") == w:
                    return m
        return real[-1] if kind == "boost" else real[0]

    def _airco_boosting(self) -> bool:
        st = self.hass.states.get(self.conf.get(CONF_AIRCO) or "")
        if not st or st.state not in HEAT_MODES:
            return False
        boost = self.fan_mode_for("boost")
        return boost is not None and st.attributes.get("fan_mode") == boost

    # ---- helpers ------------------------------------------------------
    def _float_entity(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        st = self.hass.states.get(entity_id)
        if st is None or st.state in BAD_STATES:
            return None
        try:
            val = float(st.state)
        except ValueError:
            return None
        unit = st.attributes.get("unit_of_measurement")
        if unit in ("Wh", "W"):
            val /= 1000
        elif unit in ("MWh", "MW"):
            val *= 1000
        elif unit == "L":
            val /= 1000
        return val

    def _float(self, key: str) -> float | None:
        return self._float_entity(self.conf.get(key))

    def _available(self, key: str) -> bool:
        st = self.hass.states.get(self.conf.get(key) or "")
        return st is not None and st.state not in BAD_STATES

    def _strategies(self, t_out: float | None) -> list[str]:
        out = []
        airco_ok = self._available(CONF_AIRCO) and (
            t_out is None or t_out >= self.conf[CONF_AIRCO_MIN_OUTDOOR])
        cv_ok = self._available(CONF_CV)
        if airco_ok:
            out.append(STRAT_AIRCO)
        if cv_ok:
            out.append(STRAT_CV)
        if airco_ok and cv_ok and self.conf[CONF_ALLOW_BOTH]:
            out.append(STRAT_BOTH)
        return out

    @property
    def prices(self) -> Prices:
        s = self.settings
        return Prices(float(s.get(CONF_PRICE_KWH, self.conf[CONF_PRICE_KWH])),
                      float(s.get(CONF_PRICE_GAS, self.conf[CONF_PRICE_GAS])))

    def cost_today(self, which: str) -> float:
        keys = ("airco", "cv") if which == "total" else (which,)
        return sum(self.costs[k] - self.day_start.get(k, 0.0) for k in keys)

    # ---- windows & presence -------------------------------------------
    def _update_windows(self, now: datetime) -> None:
        if not self.feature_active("windows"):
            self.window_open, self.open_windows = False, []
            self._window_since = None
            return
        opened = [e for e in _as_list(self.conf.get(CONF_WINDOWS))
                  if (st := self.hass.states.get(e)) and st.state == STATE_ON]
        self.open_windows = opened
        delay = timedelta(minutes=float(self.conf[CONF_WINDOW_DELAY]))
        if opened:
            self._window_since = self._window_since or now
            if not self.window_open and now - self._window_since >= delay:
                self.window_open = True
                self._log_event("windows", now)
        else:
            if self.window_open:
                self._window_closed_at = now
            self.window_open = False
            self._window_since = None

    def _window_blocks_learning(self, now: datetime) -> bool:
        if self.open_windows:
            return True
        return bool(self._window_closed_at and now - self._window_closed_at < WINDOW_LEARN_BLOCK)

    def _update_presence(self, now: datetime) -> None:
        s = self.settings
        if s.get("vacation"):
            self.presence = "vacation"
            return
        if s.get("guest") or not self.feature_active("presence"):
            self.presence, self._away_since = "home", None
            return
        ents = _as_list(self.conf.get(CONF_PRESENCE))
        home = False
        for e in ents:
            st = self.hass.states.get(e)
            if st is None or st.state in BAD_STATES:
                home = True  # unknown -> assume home (safe for comfort)
                continue
            try:
                if st.domain == "zone" and int(float(st.state)) > 0:
                    home = True
            except ValueError:
                pass
            if st.state.lower() in HOME_STATES:
                home = True
        if home:
            self.presence, self._away_since = "home", None
            return
        self._away_since = self._away_since or now
        delay = timedelta(minutes=float(self.conf[CONF_AWAY_DELAY]))
        self.presence = "away" if now - self._away_since >= delay else "home"

    # ---- weather forecast ---------------------------------------------
    async def _refresh_forecast(self, now: datetime) -> None:
        if not (self.feature_active("forecast") or self.feature_active("buffer")):
            self._forecast = []
            return
        if self._forecast_fetched and now - self._forecast_fetched < FORECAST_REFRESH:
            return
        self._forecast_fetched = now
        entity = self.conf.get(CONF_WEATHER)
        try:
            resp = await self.hass.services.async_call(
                "weather", "get_forecasts", {"entity_id": entity, "type": "hourly"},
                blocking=True, return_response=True)
            items = (resp or {}).get(entity, {}).get("forecast", [])
            pts = []
            for it in items:
                ts = dt_util.parse_datetime(it.get("datetime", ""))
                if ts is not None and it.get("temperature") is not None:
                    pts.append((ts.timestamp(), float(it["temperature"])))
            self._forecast = sorted(pts)
            self.forecast_error = None if pts else "empty"
        except (HomeAssistantError, ValueError, KeyError) as err:
            self._forecast = []
            self.forecast_error = str(err)
            _LOGGER.debug("Weather forecast failed: %s", err)

    def _raw_forecast(self, ts: float) -> float | None:
        f = self._forecast
        if not f:
            return None
        if ts <= f[0][0]:
            return f[0][1]
        for (t0, v0), (t1, v1) in zip(f, f[1:]):
            if t0 <= ts <= t1:
                return v0 + (v1 - v0) * (ts - t0) / (t1 - t0)
        return f[-1][1]

    def tout_at(self, when: datetime) -> float:
        """Outdoor temperature forecast, corrected for the bias versus your own sensor."""
        raw = self._raw_forecast(when.timestamp())
        if raw is None:
            return self.t_out
        corrected = raw + self.weather_bias
        # blend from the measured value now towards the forecast over 3 hours
        hours = max((when - dt_util.now()).total_seconds() / 3600, 0)
        w = min(hours / 3, 1.0)
        return (1 - w) * self.t_out + w * corrected if self.t_out is not None else corrected

    # ---- main loop ----------------------------------------------------
    async def _async_tick(self, _now: datetime | None = None) -> None:
        now = dt_util.now()
        c, s = self.conf, self.settings
        self.t_in = self._float(CONF_ROOM_SENSOR)
        self.t_out = self._float(CONF_OUTDOOR_SENSOR)
        self.solar_kw = self._float(CONF_SOLAR) if self.feature_active("solar") else None
        if self.solar_kw is not None:
            self.solar_kw = max(self.solar_kw, 0.0)
        self._update_windows(now)
        self._update_presence(now)
        await self._refresh_forecast(now)
        if self._forecast and self.t_out is not None:
            raw = self._raw_forecast(now.timestamp())
            if raw is not None:
                self.weather_bias += 0.01 * ((self.t_out - raw) - self.weather_bias)
        use_forecast = self.feature_active("forecast") and bool(self._forecast)

        inputs = Inputs(
            now=now, t_in=self.t_in, t_out=self.t_out, mode=s["mode"],
            manual_target=float(s["manual_target"]), eco_temp=float(s["eco_temp"]),
            schedule=self.schedule, strategies=self._strategies(self.t_out),
            prices=self.prices, solar=self.solar_kw or 0.0,
            tout_at=self.tout_at if use_forecast else None,
            presence=self.presence, away_temp=float(s["away_temp"]),
            vacation_temp=float(s["vacation_temp"]), window_open=self.window_open,
            fan_control=self.feature_active("fan"),
            night=(parse_hhmm(s["night_start"]), parse_hhmm(s["night_end"]))
            if self.features.get("night") else None,
            night_min=float(s["night_min"]),
            buffer_deg=float(c[CONF_BUFFER_DEG]) if self.feature_active("buffer") and self._forecast else 0.0,
            buffer_threshold=float(c[CONF_BUFFER_THRESHOLD]) / 100,
            hysteresis=float(c[CONF_HYSTERESIS]),
            max_heatup_h=float(c[CONF_MAX_HEATUP]) / 60,
            max_preheat_h=float(c[CONF_MAX_PREHEAT]) / 60,
            preheat_margin_h=float(c[CONF_PREHEAT_MARGIN]) / 60,
            min_switch=timedelta(minutes=float(c[CONF_MIN_SWITCH])),
        )
        prev = self.decision
        raw_inputs = copy.copy(inputs)
        self._apply_setback(inputs, now)

        if s["mode"] != MODE_OFF and self.override_until is None:
            if entity := self._detect_override():
                minutes = float(c[CONF_OVERRIDE_MINUTES])
                if minutes > 0:
                    self.override_until = now + timedelta(minutes=minutes)
                    self.override_entity = entity
                    self._log_event("overrides", now)
                    _LOGGER.info("Manual change on %s: pausing control until %s",
                                 entity, self.override_until)
        if self.override_until and now >= self.override_until:
            self._clear_override()

        controlling = s["mode"] != MODE_OFF and self.override_until is None
        if controlling:
            self.decision = self._decide_with_explore(inputs, now)
        else:
            self._end_explore(now, "stopped")
            self.planner.reset()
            self._expected.clear()
            reason = "learn_only" if s["mode"] == MODE_OFF else "manual_override"
            self.decision = self._observe(reason, float(c[CONF_HYSTERESIS]))
        d = self.decision
        if (d.strategy, d.phase, d.reason) != (prev.strategy, prev.phase, prev.reason):
            _LOGGER.info("Strategy %s / phase %s (%s)", d.strategy, d.phase, d.reason)

        # forecast + what-if scenarios (heavy: run in a worker thread)
        if not self._forecast_busy and (
                self._last_forecast_calc is None or now - self._last_forecast_calc >= FORECAST_EVERY):
            self._last_forecast_calc = now
            self.hass.async_create_task(self._async_forecast(inputs, controlling, now, raw_inputs))

        # learning + costs
        dhw = False
        if c.get(CONF_DHW):
            st = self.hass.states.get(c[CONF_DHW])
            dhw = st is not None and st.state == STATE_ON
        kwh = self._float(CONF_AIRCO_ENERGY)
        m3 = self._float(CONF_GAS)
        excluded = "hot_water" if dhw else ("window" if self._window_blocks_learning(now) else None)
        boosting = self._airco_boosting()
        sample, why = self.collector.tick(now.timestamp(), self.t_in, self.t_out, kwh, m3,
                                          self.solar_kw or 0.0, excluded, boosting)
        if sample:
            heating_up = d.target is not None and d.target - sample.t_in0 > 0.5
            self.model.observe_power(self.model.pmax_key("airco", sample.boost >= 0.5), sample.p_airco,
                                     heating_up and d.strategy in (STRAT_AIRCO, STRAT_BOTH))
            self.model.observe_power("cv", sample.g_cv, heating_up and d.strategy in (STRAT_CV, STRAT_BOTH))
            self.model.add_sample(sample)
            self.last_sample_reason = "ok"
            self._save()
        elif why:
            self.model.exclude(why)
            self.last_sample_reason = why
        self._track_costs(kwh, m3, dhw)
        self._track_diag(kwh, m3)
        self._track_comfort(now)

        if controlling and (d.phase == "paused" or (d.reason == "night_off" and d.strategy == STRAT_OFF)):
            await self._apply_all_off(float(s["night_min"]) if d.reason == "night_off" else None)
        elif controlling and d.strategy != STRAT_OFF:
            await self._apply(d)

        await self._daily(now)
        await self._check_health(now)
        self._notify()

    # ---- self-testing ---------------------------------------------------
    def _week_key(self, now: datetime) -> str:
        y, w, _ = now.isocalendar()
        return f"{y}-W{w:02d}"

    def explore_budget_left(self, now: datetime | None = None) -> float:
        now = now or dt_util.now()
        spent = self.explore_spent.get(self._week_key(now), 0.0)
        return max(float(self.settings["explore_budget"]) - spent, 0.0)

    def explore_needs(self, now: datetime) -> list[dict]:
        """Which sources need data, most urgent first."""
        conf = self.model.confidence()
        days = float(self.settings["explore_days"])
        out = []
        for src, param in (("airco", "ga0"), ("cv", "gc")):
            seen = self.model.last_seen.get(src)
            age = (now.timestamp() - seen) / 86400 if seen else None
            level = conf[param]
            urgency = 3 if level == "none" else 2 if level == "low" else 1 if (age is None or age >= days) else 0
            out.append({"source": src, "confidence": level, "days_ago": round(age, 1) if age is not None else None,
                        "urgency": urgency})
        return sorted(out, key=lambda x: (-x["urgency"], -(x["days_ago"] or 999)))

    def _decide_with_explore(self, inputs: Inputs, now: datetime) -> Decision:
        ex = self.explore
        if ex:  # running test: keep using the test source while comfort allows
            inputs.explore_source = ex["source"]
            d = self.planner.decide(inputs, self.model)
            gained = self.model.counts.get(ex["source"], 0.0) - ex["count0"]
            if not d.exploring:
                ex["misses"] = ex.get("misses", 0) + 1
            if (gained >= EXPLORE_SAMPLES or now - ex["since"] >= EXPLORE_MAX
                    or d.reason not in EXPLORE_REASONS or ex.get("misses", 0) >= 3):
                self._end_explore(now, "done" if gained >= EXPLORE_SAMPLES else "stopped")
            return d
        d = self.planner.decide(inputs, self.model)
        if not self.feature_active("explore") or d.reason not in EXPLORE_REASONS:
            return d
        if d.strategy in (STRAT_BOTH, STRAT_OFF):
            return d
        need = next((n for n in self.explore_needs(now) if n["urgency"]
                     and n["source"] in inputs.strategies and n["source"] != d.strategy), None)
        if not need:
            return d
        src = need["source"]
        if d.phase == PHASE_HEAT:
            alt = next((o for o in d.heat_options if o.strategy == src), None)
            cur = next((o for o in d.heat_options if o.strategy == d.strategy), None)
            if not alt or not cur or alt.cost == float("inf"):
                return d
            premium = max(alt.cost - cur.cost, 0.0)
        else:
            alt_c, cur_c = d.maintain_costs.get(src), d.maintain_costs.get(d.strategy)
            if alt_c is None or cur_c is None or alt_c == float("inf"):
                return d
            premium = max(alt_c - cur_c, 0.0) * 1.5
        if premium > self.explore_budget_left(now):
            return d
        test = copy.copy(inputs)
        test.explore_source = src
        d2 = self.planner.decide(test, self.model)
        if not d2.exploring:
            return d
        wk = self._week_key(now)
        self.explore_spent[wk] = round(self.explore_spent.get(wk, 0.0) + premium, 3)
        self.explore_spent = dict(sorted(self.explore_spent.items())[-8:])
        self.explore = {"source": src, "since": now, "premium": round(premium, 3),
                        "count0": self.model.counts.get(src, 0.0), "phase": d2.phase,
                        "instead_of": d.strategy}
        _LOGGER.info("Self-test: using %s instead of %s to learn (≈ € %.2f extra)",
                     src, d.strategy, premium)
        self._save()
        return d2

    def _end_explore(self, now: datetime, result: str) -> None:
        ex = self.explore
        if not ex:
            return
        self.explore = None
        self.explore_log.append({
            "start": ex["since"].isoformat(), "end": now.isoformat(), "source": ex["source"],
            "instead_of": ex["instead_of"], "phase": ex["phase"], "premium": ex["premium"],
            "samples": round(self.model.counts.get(ex["source"], 0.0) - ex["count0"], 1),
            "result": result,
        })
        self.explore_log = self.explore_log[-20:]
        self._save()

    def _apply_setback(self, inputs: Inputs, now: datetime) -> None:
        """Use the smart setback level (if any) instead of the fixed eco temperature."""
        sb = self.setback
        if (not sb or not self.features.get("smart_setback") or inputs.mode != "auto"
                or now.timestamp() * 1000 >= sb["until"]):
            return
        if sb["level"] is not None:
            inputs.eco_temp = sb["level"]
            inputs.night = None

    async def _async_forecast(self, inputs: Inputs, controlling: bool, now: datetime,
                              raw_inputs: Inputs | None = None) -> None:
        self._forecast_busy = True
        try:
            if (raw_inputs is not None and self.features.get("smart_setback")
                    and (self._last_setback is None or now - self._last_setback >= SETBACK_EVERY
                         or (self.setback and now.timestamp() * 1000 >= self.setback["until"]))):
                self._last_setback = now
                raw = copy.copy(raw_inputs)
                raw.explore_source = None
                if raw.mode == "off":
                    raw.mode = "auto"   # learn only: show what it would choose
                new = await self.hass.async_add_executor_job(
                    choose_setback, raw, self.model, float(self.settings["setback_max"]), True)
                old = self.setback
                if (new and old and old["level"] != new["level"] and old["until"] == new["until"]):
                    # keep the current choice unless switching clearly pays off
                    old_cost = next((o["cost"] for o in new["options"] if o["level"] == old["level"]), None)
                    if old_cost is not None and old_cost - new["cost"] < 0.05:
                        new = {**new, "level": old["level"], "cost": old_cost}
                self.setback = new
                inputs = copy.copy(raw_inputs)
                self._apply_setback(inputs, now)
            elif not self.features.get("smart_setback"):
                self.setback = None
            base = copy.copy(inputs)
            base.explore_source = None   # the forecast shows normal operation
            planner = copy.deepcopy(self.planner)
            hypothetical = not controlling
            if hypothetical:  # learn only / paused: show what the schedule would do
                base.mode = "auto" if self.settings["mode"] == MODE_OFF else base.mode
                base.window_open = False
                planner = Planner()
            if base.t_in is None or base.t_out is None:
                return
            self.forecast_result = await self.hass.async_add_executor_job(
                forecast, planner, base, self.model, FORECAST_HOURS)
            self.forecast_hypothetical = hypothetical
            if self._last_scenarios is None or now - self._last_scenarios >= SCENARIOS_EVERY:
                self._last_scenarios = now
                self.scenarios = await self.hass.async_add_executor_job(
                    what_if, planner, base, self.model, FORECAST_HOURS)
            self._notify()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Forecast failed")
        finally:
            self._forecast_busy = False

    def expected_cost(self, hours: float) -> float | None:
        hourly = self.forecast_result.get("hourly") or []
        if not hourly:
            return None
        start = hourly[0][0]
        return round(sum(a + c for h, a, c in hourly if h < start + hours * 3600 * 1000), 3)

    # ---- bookkeeping --------------------------------------------------
    def _log_event(self, kind: str, now: datetime) -> None:
        lst = self.events.setdefault(kind, [])
        lst.append(now.isoformat())
        cutoff = (now - timedelta(days=30)).isoformat()
        self.events[kind] = [e for e in lst if e >= cutoff][-200:]
        self._save()

    def _track_costs(self, kwh: float | None, m3: float | None, dhw: bool) -> None:
        today = dt_util.now().date().isoformat()
        if self.day_start.get("date") != today:
            self.day_start = {"date": today, **{k: v for k, v in self.costs.items()}}
            self._save()
        if kwh is None or m3 is None:
            self._prev_meter = None
            return
        prev, self._prev_meter = self._prev_meter, (kwh, m3)
        if prev is None:
            return
        d_kwh, d_m3 = kwh - prev[0], m3 - prev[1]
        p = self.prices
        if 0 <= d_kwh < 5:
            self.costs["airco"] += d_kwh * p.kwh
            self.diag_counters["airco_kwh"] += d_kwh
        if 0 <= d_m3 < 2 and not dhw:
            self.costs["cv"] += d_m3 * p.gas
            self.diag_counters["cv_m3"] += d_m3

    def _track_diag(self, kwh, m3) -> None:
        """Count minutes a device should be heating, to check that its meter moves."""
        c = self.conf
        a = self.hass.states.get(c[CONF_AIRCO])
        if a and a.state in HEAT_MODES and self.t_in is not None:
            sp = a.attributes.get("temperature")
            if sp is not None and float(sp) - c[CONF_AIRCO_OFFSET] > self.t_in + 0.5:
                self.diag_counters["airco_on_min"] += 1
        v = self.hass.states.get(c[CONF_CV])
        if v and v.state not in BAD_STATES and v.state != "off" and self.t_in is not None:
            sp = v.attributes.get("temperature")
            if sp is not None and float(sp) > self.t_in + 0.7:
                self.diag_counters["cv_on_min"] += 1

    def _track_comfort(self, now: datetime) -> None:
        if self.t_in is None or self.presence != "home":
            return
        comfort = comfort_at(self.schedule, now)
        if comfort is None:
            return
        key = now.date().isoformat()
        rec = self.comfort.setdefault(key, [0, 0])
        rec[1] += 1
        if self.t_in >= comfort - 0.5:
            rec[0] += 1
        if len(self.comfort) > 40:
            for k in sorted(self.comfort)[:-40]:
                del self.comfort[k]

    def comfort_score(self, days: int = 1) -> float | None:
        today = dt_util.now().date()
        ok = total = 0
        for i in range(days):
            rec = self.comfort.get((today - timedelta(days=i)).isoformat())
            if rec:
                ok, total = ok + rec[0], total + rec[1]
        return round(100 * ok / total, 1) if total >= 10 else None

    async def _daily(self, now: datetime) -> None:
        key = now.date().isoformat()
        if self._last_daily == key:
            return
        self._last_daily = key
        self.diag_counters = {"airco_on_min": 0, "airco_kwh": 0.0, "cv_on_min": 0, "cv_m3": 0.0}
        if self.features.get("suggestions"):
            self._make_suggestions(now)

    # ---- suggestions --------------------------------------------------
    def _suggest(self, sid: str, kind: str, params: dict, action: dict | None = None) -> None:
        for sg in self.suggestions:
            if sg["id"] == sid:
                if sg.get("status") == "open":
                    sg["params"] = params
                return
        self.suggestions.append({"id": sid, "kind": kind, "params": params, "action": action,
                                 "status": "open", "created": dt_util.now().isoformat()})
        self.suggestions = self.suggestions[-30:]
        self._save()

    def _make_suggestions(self, now: datetime) -> None:
        days_of_data = len(self.comfort)
        week = now.isocalendar()
        tag = f"{week[0]}w{week[1]}"
        # 1. frequent manual changes
        cutoff = (now - timedelta(days=14)).isoformat()
        overrides = [e for e in self.events.get("overrides", []) if e >= cutoff]
        if days_of_data >= 14 and len(overrides) >= 4:
            hours = sorted(int(e[11:13]) for e in overrides)
            self._suggest(f"overrides-{tag}", "frequent_overrides",
                          {"count": len(overrides), "hour": hours[len(hours) // 2]})
        # 2. comfort not reached
        score = self.comfort_score(7)
        if days_of_data >= 7 and score is not None and score < 85:
            new_margin = min(float(self.conf[CONF_PREHEAT_MARGIN]) + 15, 120)
            self._suggest(f"comfort-{tag}", "low_comfort", {"score": score, "margin": new_margin},
                          {"option": CONF_PREHEAT_MARGIN, "value": new_margin})
        # 3. windows often open while heating
        wins = [e for e in self.events.get("windows", []) if e >= cutoff]
        if days_of_data >= 14 and len(wins) >= 10:
            self._suggest(f"windows-{tag}", "windows_often_open", {"count": len(wins)})
        # 4. model does not fit well
        chk = self.model.check()
        if chk["n"] >= 50 and chk["mae_1h"] is not None and chk["mae_1h"] > 0.5:
            self._suggest(f"model-{tag}", "model_inaccurate", {"mae": round(chk["mae_1h"], 2)})
        # 5. below which outdoor temperature is the boiler cheaper?
        p = self.prices
        conf = self.model.confidence()
        if conf["ga0"] in ("medium", "high") and conf["gc"] in ("medium", "high"):
            for t in range(15, -16, -1):
                if p.kwh / self.model.gain("airco", t) > p.gas / self.model.gain("cv", t):
                    self._suggest(f"breakeven-{tag}", "breakeven", {"temp": t})
                    break

    async def async_respond_suggestion(self, sid: str, action: str) -> None:
        for sg in self.suggestions:
            if sg["id"] != sid:
                continue
            if action == "apply" and sg.get("action"):
                opt = sg["action"]
                new = {**self.entry.options, opt["option"]: opt["value"]}
                sg["status"] = "applied"
                self._save()
                await self._store.async_save(self._data())
                self.hass.config_entries.async_update_entry(self.entry, options=new)
                return
            sg["status"] = "dismissed"
        self._save()
        self._notify()

    # ---- health & diagnostics -----------------------------------------
    def diagnostics(self) -> list[dict]:
        """Plain checks shown in the panel: ok / info / warn / error."""
        c = self.conf
        out = []

        def add(cid, status, **params):
            out.append({"id": cid, "status": status, "params": params})

        for key in (CONF_ROOM_SENSOR, CONF_OUTDOOR_SENSOR, CONF_AIRCO, CONF_CV,
                    CONF_AIRCO_ENERGY, CONF_GAS):
            ent = c.get(key)
            st = self.hass.states.get(ent or "")
            if st is None:
                add(f"entity_{key}", "error", entity=ent)
            elif st.state in BAD_STATES:
                add(f"entity_{key}", "warn", entity=ent)
            else:
                add(f"entity_{key}", "ok", entity=ent)
        room = self.hass.states.get(c.get(CONF_ROOM_SENSOR) or "")
        if room is not None and room.state not in BAD_STATES:
            seen = getattr(room, "last_reported", None) or room.last_updated
            age = (dt_util.utcnow() - seen).total_seconds() / 3600
            add("room_fresh", "warn" if age > 3 else "ok", hours=round(age, 1))
        dc = self.diag_counters
        if dc["airco_on_min"] >= 90:
            add("airco_meter", "warn" if dc["airco_kwh"] < 0.05 else "ok",
                minutes=dc["airco_on_min"], kwh=round(dc["airco_kwh"], 2))
        if dc["cv_on_min"] >= 90:
            add("gas_meter", "warn" if dc["cv_m3"] < 0.01 else "ok",
                minutes=dc["cv_on_min"], m3=round(dc["cv_m3"], 3))
        if not c.get(CONF_DHW):
            add("dhw_missing", "info")
        if self.model.clamped:
            crit = [p for p in self.model.clamped if p in ("k", "ga0", "gc")]
            add("model_bounds", "warn" if crit else "info", params=self.model.clamped)
        chk = self.model.check()
        if chk["mae_1h"] is None:
            add("model_accuracy", "info", n=chk["n"])
        else:
            mae = chk["mae_1h"]
            add("model_accuracy", "ok" if mae <= 0.3 else "info" if mae <= 0.5 else "warn",
                mae=round(mae, 2), bias=round(chk["bias_1h"], 2), n=chk["n"])
        total_ex = sum(self.model.excluded.values())
        used = int(self.model.n_eff + 0.5)
        if total_ex and total_ex > max(used, 1) * 1.5:
            top = max(self.model.excluded, key=self.model.excluded.get)
            add("many_excluded", "warn", reason=top, excluded=total_ex)
        if self.feature_active("forecast") or self.feature_active("buffer"):
            if not self._forecast:
                add("forecast", "warn", error=self.forecast_error)
            else:
                add("forecast", "warn" if abs(self.weather_bias) > 3 else "ok",
                    bias=round(self.weather_bias, 1))
        if self.features.get("windows") and not _as_list(c.get(CONF_WINDOWS)):
            add("feature_windows_unconfigured", "info")
        if self.features.get("presence") and not _as_list(c.get(CONF_PRESENCE)):
            add("feature_presence_unconfigured", "info")
        if (self.features.get("forecast") or self.features.get("buffer")) and not c.get(CONF_WEATHER):
            add("feature_forecast_unconfigured", "info")
        if self.features.get("solar") and not c.get(CONF_SOLAR):
            add("feature_solar_unconfigured", "info")
        return out

    async def _check_health(self, now: datetime) -> None:
        if not self.features.get("notifications"):
            return
        limit = timedelta(minutes=float(self.conf[CONF_NOTIFY_AFTER]))
        for key in (CONF_ROOM_SENSOR, CONF_OUTDOOR_SENSOR, CONF_AIRCO, CONF_CV,
                    CONF_AIRCO_ENERGY, CONF_GAS):
            ent = self.conf.get(key)
            st = self.hass.states.get(ent or "")
            nid = NOTIFY_ID.format(key)
            if st is None or st.state in BAD_STATES:
                since = self._unavailable_since.setdefault(key, now)
                if now - since >= limit and nid not in self._notified:
                    self._notified.add(nid)
                    lang = (self.hass.config.language or "en")[:2]
                    title = "Climator"
                    msg = (f"{ent} is al {int((now - since).total_seconds() // 60)} minuten niet beschikbaar. "
                           "Climator kan daardoor niet goed sturen of leren."
                           if lang == "nl" else
                           f"{ent} has been unavailable for {int((now - since).total_seconds() // 60)} minutes. "
                           "Climator cannot control or learn properly.")
                    await self.hass.services.async_call(
                        "persistent_notification", "create",
                        {"title": title, "message": msg, "notification_id": nid})
            else:
                self._unavailable_since.pop(key, None)
                if nid in self._notified:
                    self._dismiss(nid)

    def _dismiss(self, nid: str) -> None:
        self._notified.discard(nid)
        self.hass.async_create_task(self.hass.services.async_call(
            "persistent_notification", "dismiss", {"notification_id": nid}))

    # ---- panel data ---------------------------------------------------
    def info(self) -> dict[str, Any]:
        m = self.model
        t_out = self.t_out if self.t_out is not None else 5.0
        p = self.prices
        sources = {}
        for src in ("airco", "cv"):
            g = m.gain(src, t_out)
            price = p.kwh if src == "airco" else p.gas
            sources[src] = {
                "gain": round(g, 3), "pmax": round(m.pmax[src], 3),
                "max_rate": round(m.heat_rate(src, t_out), 2),
                "cost_per_degree": round(price / g, 4),
                "maintain_input": round(m.maintain_input(src, 20.0, t_out), 3),
            }
        sources["airco"]["boost_gain"] = round(m.gain("airco", t_out, 1.0), 3)
        sources["airco"]["boost_max_rate"] = round(m.heat_rate("airco", t_out, True), 2)
        sources["airco"]["boost_cost_per_degree"] = round(p.kwh / m.gain("airco", t_out, 1.0), 4)
        chk = m.check()
        return {
            "version": VERSION,
            "model": {
                "theta": {k: round(v, 5) for k, v in m.theta.items()},
                "std": {k: round(v, 5) for k, v in m.std_errors().items()},
                "confidence": m.confidence(),
                "counts": {k: round(v, 1) for k, v in m.counts.items()},
                "pmax": {k: round(v, 3) for k, v in m.pmax.items()},
                "samples": len(m.samples), "n_eff": round(m.n_eff, 1),
                "excluded": m.excluded, "clamped": m.clamped,
                "rmse_slope": round(m.res2 ** 0.5, 3),
                "check": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in chk.items()},
                "replay": m.replay(48),
                "sources": sources, "t_out": self.t_out,
                "last_sample": self.last_sample_reason,
            },
            "diagnostics": self.diagnostics(),
            "suggestions": [sg for sg in self.suggestions if sg.get("status") == "open"],
            "forecast": self.forecast_result,
            "forecast_hypothetical": self.forecast_hypothetical,
            "scenarios": self.scenarios,
            "setback": self.setback if self.features.get("smart_setback") else None,
            "history": {"busy": self.history_busy, "result": self.history_result},
            "explore": {
                "active": self.feature_active("explore"),
                "session": ({**self.explore, "since": self.explore["since"].isoformat()}
                            if self.explore else None),
                "needs": self.explore_needs(dt_util.now()),
                "budget": float(self.settings["explore_budget"]),
                "left": round(self.explore_budget_left(), 2),
                "log": self.explore_log[-10:],
            },
            "fan": {"modes": self.fan_modes(), "boost": self.fan_mode_for("boost"),
                    "comfort": self.fan_mode_for("comfort"), "active": self.feature_active("fan"),
                    "boosting": self._airco_boosting()},
            "outdoor_forecast": [[int(t * 1000), round(v + self.weather_bias, 1)]
                                 for t, v in self._forecast[:48]],
            "weather_bias": round(self.weather_bias, 2),
            "features": self.features,
            "features_active": {f: self.feature_active(f) for f in self.features},
            "schedule": self.schedule,
            "settings": self.settings,
            "presence": self.presence,
            "open_windows": self.open_windows,
            "window_open": self.window_open,
            "comfort": {"today": self.comfort_score(1), "week": self.comfort_score(7),
                        "days": {k: (round(100 * v[0] / v[1], 1) if v[1] else None)
                                 for k, v in sorted(self.comfort.items())[-30:]}},
            "configured": {
                "windows": _as_list(self.conf.get(CONF_WINDOWS)),
                "presence": _as_list(self.conf.get(CONF_PRESENCE)),
                "weather": self.conf.get(CONF_WEATHER), "solar": self.conf.get(CONF_SOLAR),
                "dhw": self.conf.get(CONF_DHW),
            },
        }

    # ---- device control -----------------------------------------------
    def _detect_override(self) -> str | None:
        now = dt_util.utcnow()
        for entity_id, ((mode, temp, fan), since) in self._expected.items():
            if now - since < OVERRIDE_GRACE:
                continue
            st = self.hass.states.get(entity_id)
            if st is None or st.state in BAD_STATES:
                continue
            if mode and st.state != mode:
                return entity_id
            if fan is not None and mode != "off" and st.attributes.get("fan_mode") not in (None, fan):
                return entity_id
            cur = st.attributes.get("temperature")
            if temp is not None and mode != "off" and cur is not None:
                if abs(float(cur) - temp) > 0.25:
                    return entity_id
        return None

    def _observe(self, reason: str, hysteresis: float) -> Decision:
        c = self.conf
        if self.t_in is None:
            return Decision(STRAT_OFF, PHASE_OFF, None, reason)
        targets = []
        airco_on = cv_on = False
        a = self.hass.states.get(c[CONF_AIRCO])
        if a and a.state in HEAT_MODES and a.attributes.get("temperature") is not None:
            airco_on = True
            targets.append(float(a.attributes["temperature"]) - c[CONF_AIRCO_OFFSET])
        v = self.hass.states.get(c[CONF_CV])
        if (v and v.state not in BAD_STATES and v.state != "off"
                and v.attributes.get("temperature") is not None):
            tv = float(v.attributes["temperature"]) - c[CONF_CV_OFFSET]
            if tv >= self.t_in - 0.3:
                cv_on = True
                targets.append(tv)
        if airco_on and cv_on:
            strategy = STRAT_BOTH
        elif airco_on:
            strategy = STRAT_AIRCO
        elif cv_on:
            strategy = STRAT_CV
        else:
            return Decision(STRAT_OFF, PHASE_OFF, None, reason)
        target = round(max(targets), 1)
        phase = PHASE_HEAT if target - self.t_in > hysteresis else PHASE_MAINTAIN
        return Decision(strategy, phase, target, reason)

    async def _apply_all_off(self, cv_temp: float | None = None) -> None:
        c = self.conf
        await self._set_climate(c[CONF_AIRCO], "off", None)
        await self._set_climate(c[CONF_CV], "heat", cv_temp if cv_temp is not None else c[CONF_CV_SETBACK])

    async def _apply(self, d: Decision) -> None:
        c = self.conf
        airco_on = d.strategy in (STRAT_AIRCO, STRAT_BOTH)
        cv_on = d.strategy in (STRAT_CV, STRAT_BOTH)
        if airco_on:
            fan = self.fan_mode_for(d.fan) if d.fan else None
            await self._set_climate(c[CONF_AIRCO], "heat", d.target + c[CONF_AIRCO_OFFSET], fan)
        else:
            await self._set_climate(c[CONF_AIRCO], "off", None)
        cv_temp = d.target + c[CONF_CV_OFFSET] if cv_on else c[CONF_CV_SETBACK]
        await self._set_climate(c[CONF_CV], "heat", cv_temp)

    async def _set_climate(self, entity_id: str, mode: str, temp: float | None,
                           fan: str | None = None) -> None:
        st = self.hass.states.get(entity_id)
        if st is None or st.state in BAD_STATES:
            return
        attrs = st.attributes
        modes = attrs.get("hvac_modes") or []
        if mode not in modes:
            if mode == "heat" and "heat_cool" in modes:
                mode = "heat_cool"
            else:
                mode = None
        if temp is not None:
            step = attrs.get("target_temp_step") or 0.5
            temp = round(round(temp / step) * step, 1)
            temp = max(attrs.get("min_temp", 5), min(attrs.get("max_temp", 30), temp))

        if fan is not None and fan not in (attrs.get("fan_modes") or []):
            fan = None
        cmd = (mode, temp, fan)
        now = dt_util.utcnow()
        exp = self._expected.get(entity_id)
        if exp is None or exp[0] != cmd:
            self._expected[entity_id] = (cmd, now)
        last = self._last_cmd.get(entity_id)
        if last and last[0] == cmd and now - last[1] < RESEND_AFTER:
            return

        sent = False
        try:
            if mode and st.state != mode:
                await self.hass.services.async_call(
                    "climate", "set_hvac_mode",
                    {"entity_id": entity_id, "hvac_mode": mode}, blocking=True)
                sent = True
            if temp is not None and mode != "off":
                cur = attrs.get("temperature")
                if sent or cur is None or abs(float(cur) - temp) >= 0.05:
                    await self.hass.services.async_call(
                        "climate", "set_temperature",
                        {"entity_id": entity_id, "temperature": temp}, blocking=True)
                    sent = True
            if fan is not None and mode != "off" and attrs.get("fan_mode") != fan:
                await self.hass.services.async_call(
                    "climate", "set_fan_mode", {"entity_id": entity_id, "fan_mode": fan},
                    blocking=True)
                sent = True
        except (HomeAssistantError, ValueError) as err:
            _LOGGER.warning("Controlling %s failed: %s", entity_id, err)
            return
        if sent:
            self._last_cmd[entity_id] = (cmd, now)
