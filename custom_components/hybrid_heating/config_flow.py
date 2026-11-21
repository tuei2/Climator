"""Config and options flow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector as sel

from .const import (
    CONF_AWAY_DELAY, CONF_BUFFER_DEG, CONF_BUFFER_THRESHOLD, CONF_NOTIFY_AFTER, CONF_PRESENCE,
    CONF_SOLAR, CONF_WEATHER, CONF_WINDOW_DELAY, CONF_WINDOWS,
    CONF_AIRCO, CONF_AIRCO_ENERGY, CONF_AIRCO_MIN_OUTDOOR, CONF_AIRCO_OFFSET,
    CONF_ALLOW_BOTH, CONF_CV, CONF_CV_OFFSET, CONF_CV_SETBACK, CONF_DHW, CONF_GAS,
    CONF_HYSTERESIS, CONF_MAX_HEATUP, CONF_MAX_PREHEAT, CONF_MIN_SWITCH, CONF_NAME,
    CONF_OUTDOOR_SENSOR, CONF_OVERRIDE_MINUTES, CONF_PREHEAT_MARGIN,
    CONF_ROOM_SENSOR, DEFAULT_OPTIONS, DOMAIN, ENTITY_KEYS,
)


def _ent(domain, device_class: str | None = None, multiple: bool = False) -> sel.EntitySelector:
    kw = {"domain": domain, "multiple": multiple}
    if device_class:
        kw["device_class"] = device_class
    return sel.EntitySelector(sel.EntitySelectorConfig(**kw))


def _num(lo, hi, step, unit=None) -> sel.NumberSelector:
    return sel.NumberSelector(sel.NumberSelectorConfig(
        min=lo, max=hi, step=step, unit_of_measurement=unit,
        mode=sel.NumberSelectorMode.BOX))


def _entity_schema(d: dict) -> dict:
    return {
        vol.Required(CONF_ROOM_SENSOR, default=d.get(CONF_ROOM_SENSOR, vol.UNDEFINED)):
            _ent("sensor", "temperature"),
        vol.Required(CONF_OUTDOOR_SENSOR, default=d.get(CONF_OUTDOOR_SENSOR, vol.UNDEFINED)):
            _ent("sensor", "temperature"),
        vol.Required(CONF_AIRCO, default=d.get(CONF_AIRCO, vol.UNDEFINED)): _ent("climate"),
        vol.Required(CONF_CV, default=d.get(CONF_CV, vol.UNDEFINED)): _ent("climate"),
        vol.Required(CONF_AIRCO_ENERGY, default=d.get(CONF_AIRCO_ENERGY, vol.UNDEFINED)):
            _ent("sensor"),
        vol.Required(CONF_GAS, default=d.get(CONF_GAS, vol.UNDEFINED)): _ent("sensor"),
        vol.Optional(CONF_DHW, description={"suggested_value": d.get(CONF_DHW)}):
            _ent("binary_sensor"),
        vol.Optional(CONF_WINDOWS, description={"suggested_value": d.get(CONF_WINDOWS)}):
            _ent("binary_sensor", multiple=True),
        vol.Optional(CONF_PRESENCE, description={"suggested_value": d.get(CONF_PRESENCE)}):
            _ent(["person", "device_tracker", "binary_sensor", "input_boolean", "group", "zone"],
                 multiple=True),
        vol.Optional(CONF_WEATHER, description={"suggested_value": d.get(CONF_WEATHER)}):
            _ent("weather"),
        vol.Optional(CONF_SOLAR, description={"suggested_value": d.get(CONF_SOLAR)}):
            _ent("sensor", "power"),
    }


def _option_schema(o: dict) -> dict:
    g = lambda k: o.get(k, DEFAULT_OPTIONS[k])  # noqa: E731
    return {
        vol.Required(CONF_AIRCO_OFFSET, default=g(CONF_AIRCO_OFFSET)): _num(-3, 5, 0.5, "°C"),
        vol.Required(CONF_CV_OFFSET, default=g(CONF_CV_OFFSET)): _num(-3, 3, 0.1, "°C"),
        vol.Required(CONF_CV_SETBACK, default=g(CONF_CV_SETBACK)): _num(5, 20, 0.5, "°C"),
        vol.Required(CONF_AIRCO_MIN_OUTDOOR, default=g(CONF_AIRCO_MIN_OUTDOOR)):
            _num(-25, 15, 1, "°C"),
        vol.Required(CONF_ALLOW_BOTH, default=g(CONF_ALLOW_BOTH)): sel.BooleanSelector(),
        vol.Required(CONF_MAX_HEATUP, default=g(CONF_MAX_HEATUP)): _num(10, 480, 5, "min"),
        vol.Required(CONF_MAX_PREHEAT, default=g(CONF_MAX_PREHEAT)): _num(15, 720, 5, "min"),
        vol.Required(CONF_PREHEAT_MARGIN, default=g(CONF_PREHEAT_MARGIN)): _num(0, 120, 5, "min"),
        vol.Required(CONF_MIN_SWITCH, default=g(CONF_MIN_SWITCH)): _num(0, 120, 5, "min"),
        vol.Required(CONF_HYSTERESIS, default=g(CONF_HYSTERESIS)): _num(0.1, 2, 0.1, "°C"),
        vol.Required(CONF_OVERRIDE_MINUTES, default=g(CONF_OVERRIDE_MINUTES)):
            _num(0, 1440, 15, "min"),
        vol.Required(CONF_WINDOW_DELAY, default=g(CONF_WINDOW_DELAY)): _num(0, 60, 1, "min"),
        vol.Required(CONF_AWAY_DELAY, default=g(CONF_AWAY_DELAY)): _num(0, 240, 5, "min"),
        vol.Required(CONF_BUFFER_DEG, default=g(CONF_BUFFER_DEG)): _num(0.5, 2, 0.5, "°C"),
        vol.Required(CONF_BUFFER_THRESHOLD, default=g(CONF_BUFFER_THRESHOLD)): _num(5, 50, 5, "%"),
        vol.Required(CONF_NOTIFY_AFTER, default=g(CONF_NOTIFY_AFTER)): _num(5, 1440, 5, "min"),
    }


def _validate(user_input: dict) -> dict:
    if user_input[CONF_AIRCO] == user_input[CONF_CV]:
        return {CONF_CV: "same_climate"}
    return {}


class HybridHeatingConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                title = user_input.pop(CONF_NAME)
                return self.async_create_entry(
                    title=title, data=user_input, options=dict(DEFAULT_OPTIONS))
        schema = vol.Schema({
            vol.Required(CONF_NAME, default="Hybride verwarming"): str,
            **_entity_schema(user_input or {}),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HybridHeatingOptionsFlow()


class HybridHeatingOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                for key in ENTITY_KEYS:  # allow clearing optional entities
                    user_input.setdefault(key, None)
                return self.async_create_entry(data=user_input)
            current.update(user_input)
        schema = vol.Schema({**_entity_schema(current), **_option_schema(current)})
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
