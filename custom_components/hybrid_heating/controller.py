"""Home Assistant side: reads entities, runs the planner, controls the climates."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AIRCO, CONF_AIRCO_ENERGY, CONF_AIRCO_MIN_OUTDOOR, CONF_AIRCO_OFFSET,
    CONF_ALLOW_BOTH, CONF_CV, CONF_CV_OFFSET, CONF_CV_SETBACK, CONF_DHW, CONF_GAS,
    CONF_HYSTERESIS, CONF_MAX_HEATUP, CONF_MAX_PREHEAT, CONF_MIN_SWITCH,
    CONF_OUTDOOR_SENSOR, CONF_OVERRIDE_MINUTES, CONF_PREHEAT_MARGIN, CONF_PRICE_GAS, CONF_PRICE_KWH,
    CONF_ROOM_SENSOR, DEFAULT_OPTIONS, DEFAULT_SETTINGS, DOMAIN, MODE_HEAT, MODE_OFF,
    STORAGE_VERSION, UPDATE_INTERVAL_SECONDS,
)
from .planner import (
    PHASE_HEAT, PHASE_MAINTAIN, PHASE_OFF, STRAT_AIRCO, STRAT_BOTH, STRAT_CV, STRAT_OFF,
    Decision, Inputs, Learner,
    LearningModel, Planner, Prices, parse_time,
)

_LOGGER = logging.getLogger(__name__)

BAD_STATES = (STATE_UNAVAILABLE, STATE_UNKNOWN, None, "")
RESEND_AFTER = timedelta(minutes=5)
OVERRIDE_GRACE = timedelta(seconds=120)
HEAT_MODES = ("heat", "heat_cool", "auto")


class HybridHeatingController:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.conf = {**DEFAULT_OPTIONS, **entry.data, **entry.options}
        self._store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.settings: dict = dict(DEFAULT_SETTINGS)
        self.model = LearningModel()
        self.planner = Planner()
        self.learner = Learner(self.model)
        self.decision: Decision = Decision(STRAT_OFF, "off", None, "opstarten")
        self.t_in: float | None = None
        self.t_out: float | None = None
        self._listeners: list[Callable[[], None]] = []
        self._unsub = None
        self._last_cmd: dict[str, tuple] = {}
        # entity_id -> ((mode, temp), since): what we expect the device to show
        self._expected: dict[str, tuple] = {}
        self.override_until: datetime | None = None
        self.override_entity: str | None = None

    # ---- lifecycle ----------------------------------------------------
    async def async_setup(self) -> None:
        data = await self._store.async_load() or {}
        self.settings.update(data.get("settings", {}))
        self.model.data = data.get("model", {})

    @callback
    def async_start(self) -> None:
        self._unsub = async_track_time_interval(
            self.hass, self._async_tick, timedelta(seconds=UPDATE_INTERVAL_SECONDS))
        self.hass.async_create_task(self._async_tick())

    async def async_shutdown(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        await self._store.async_save(self._data())

    def _data(self) -> dict:
        return {"settings": self.settings, "model": self.model.data}

    def _save(self) -> None:
        self._store.async_delay_save(self._data, 30)

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
        if key in ("mode", "manual_target"):
            self.learner.reset()
        self._save()
        await self._async_tick()

    async def async_set_manual_target(self, value: float) -> None:
        self.settings["manual_target"] = value
        self.settings["mode"] = MODE_HEAT
        self._clear_override()
        self.learner.reset()
        self._save()
        await self._async_tick()

    async def async_reset_learning(self) -> None:
        self.model.data.clear()
        self.learner.reset()
        self._save()
        self._notify()

    # ---- helpers ------------------------------------------------------
    def _float(self, key: str) -> float | None:
        entity_id = self.conf.get(key)
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
        if unit == "Wh":
            val /= 1000
        elif unit == "MWh":
            val *= 1000
        elif unit == "L":
            val /= 1000
        return val

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
        return Prices(float(self.conf[CONF_PRICE_KWH]), float(self.conf[CONF_PRICE_GAS]))

    # ---- main loop ----------------------------------------------------
    async def _async_tick(self, _now: datetime | None = None) -> None:
        now = dt_util.now()
        self.t_in = self._float(CONF_ROOM_SENSOR)
        self.t_out = self._float(CONF_OUTDOOR_SENSOR)
        c = self.conf
        s = self.settings
        inputs = Inputs(
            now=now, t_in=self.t_in, t_out=self.t_out, mode=s["mode"],
            manual_target=float(s["manual_target"]),
            comfort_temp=float(s["comfort_temp"]), eco_temp=float(s["eco_temp"]),
            comfort_start=parse_time(s["comfort_start"]),
            comfort_end=parse_time(s["comfort_end"]),
            strategies=self._strategies(self.t_out), prices=self.prices,
            hysteresis=float(c[CONF_HYSTERESIS]),
            max_heatup_h=float(c[CONF_MAX_HEATUP]) / 60,
            max_preheat_h=float(c[CONF_MAX_PREHEAT]) / 60,
            preheat_margin_h=float(c[CONF_PREHEAT_MARGIN]) / 60,
            min_switch=timedelta(minutes=float(c[CONF_MIN_SWITCH])),
        )
        prev = self.decision

        if s["mode"] != MODE_OFF and self.override_until is None:
            if entity := self._detect_override():
                minutes = float(c[CONF_OVERRIDE_MINUTES])
                if minutes > 0:
                    self.override_until = now + timedelta(minutes=minutes)
                    self.override_entity = entity
                    _LOGGER.info("Handmatige bediening op %s: module pauzeert tot %s",
                                 entity, self.override_until)
        if self.override_until and now >= self.override_until:
            self._clear_override()

        controlling = s["mode"] != MODE_OFF and self.override_until is None
        if controlling:
            self.decision = self.planner.decide(inputs, self.model)
        else:
            self.planner._off("")
            self._expected.clear()
            reason = ("alleen leren" if s["mode"] == MODE_OFF
                      else f"handmatig bediend tot {self.override_until:%H:%M}")
            self.decision = self._observe(reason, float(c[CONF_HYSTERESIS]))
        d = self.decision
        if (d.strategy, d.phase) != (prev.strategy, prev.phase):
            _LOGGER.info("Strategie %s / fase %s (%s)", d.strategy, d.phase, d.reason)

        dhw = False
        if c.get(CONF_DHW):
            st = self.hass.states.get(c[CONF_DHW])
            dhw = st is not None and st.state == STATE_ON
        kwh = self._float(CONF_AIRCO_ENERGY)
        m3 = self._float(CONF_GAS)
        if self.learner.tick(now, d, self.t_in, self.t_out, kwh, m3, dhw):
            _LOGGER.debug("Geleerd: %s", self.learner.last_event)
            self._save()

        if controlling and d.strategy != STRAT_OFF:
            await self._apply(d)
        self._notify()

    def _detect_override(self) -> str | None:
        """Return entity_id whose state no longer matches what we set (remote, app, dial)."""
        now = dt_util.utcnow()
        for entity_id, ((mode, temp), since) in self._expected.items():
            if now - since < OVERRIDE_GRACE:
                continue
            st = self.hass.states.get(entity_id)
            if st is None or st.state in BAD_STATES:
                continue
            if mode and st.state != mode:
                return entity_id
            cur = st.attributes.get("temperature")
            if temp is not None and mode != "off" and cur is not None:
                if abs(float(cur) - temp) > 0.25:
                    return entity_id
        return None

    def _observe(self, reason: str, hysteresis: float) -> Decision:
        """Derive what is running from the devices themselves (for learning only)."""
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

    async def _apply(self, d: Decision) -> None:
        c = self.conf
        airco_on = d.strategy in (STRAT_AIRCO, STRAT_BOTH)
        cv_on = d.strategy in (STRAT_CV, STRAT_BOTH)
        if airco_on:
            await self._set_climate(c[CONF_AIRCO], "heat", d.target + c[CONF_AIRCO_OFFSET])
        else:
            await self._set_climate(c[CONF_AIRCO], "off", None)
        cv_temp = d.target + c[CONF_CV_OFFSET] if cv_on else c[CONF_CV_SETBACK]
        await self._set_climate(c[CONF_CV], "heat", cv_temp)

    async def _set_climate(self, entity_id: str, mode: str, temp: float | None) -> None:
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

        cmd = (mode, temp)
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
        except (HomeAssistantError, ValueError) as err:
            _LOGGER.warning("Aansturen %s mislukt: %s", entity_id, err)
            return
        if sent:
            self._last_cmd[entity_id] = (cmd, now)
