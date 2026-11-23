"""Websocket API used by the Climator panel."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, FEATURES

SETTING_KEYS = {"eco_temp", "away_temp", "vacation_temp", "manual_target", "vacation", "guest",
                "price_kwh", "price_gas", "mode", "fan_boost_mode", "fan_comfort_mode",
                "explore_budget", "explore_days", "night_start", "night_end", "night_min",
                "setback_max"}


def _ctrl(hass: HomeAssistant, entry_id: str | None):
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    for e in entries:
        if entry_id is None or e.entry_id == entry_id:
            return e.runtime_data
    return None


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_info)
    websocket_api.async_register_command(hass, ws_update)
    websocket_api.async_register_command(hass, ws_suggestion)
    websocket_api.async_register_command(hass, ws_reset)
    websocket_api.async_register_command(hass, ws_train_history)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/info",
                                  vol.Optional("entry_id"): str})
@callback
def ws_info(hass, connection, msg):
    ctrl = _ctrl(hass, msg.get("entry_id"))
    if ctrl is None:
        connection.send_error(msg["id"], "not_found", "Climator is not set up")
        return
    connection.send_result(msg["id"], ctrl.info())


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/update",
    vol.Optional("entry_id"): str,
    vol.Optional("settings"): dict,
    vol.Optional("features"): dict,
    vol.Optional("schedule"): dict,
})
@websocket_api.async_response
async def ws_update(hass, connection, msg):
    ctrl = _ctrl(hass, msg.get("entry_id"))
    if ctrl is None:
        connection.send_error(msg["id"], "not_found", "Climator is not set up")
        return
    try:
        for key, value in (msg.get("settings") or {}).items():
            if key not in SETTING_KEYS:
                raise ValueError(f"unknown setting {key}")
            await ctrl.async_set_setting(key, value)
        for key, value in (msg.get("features") or {}).items():
            if key not in FEATURES:
                raise ValueError(f"unknown feature {key}")
            await ctrl.async_set_feature(key, bool(value))
        if msg.get("schedule") is not None:
            await ctrl.async_set_schedule(msg["schedule"])
    except (ValueError, KeyError, TypeError) as err:
        connection.send_error(msg["id"], "invalid", str(err))
        return
    connection.send_result(msg["id"], ctrl.info())


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/suggestion",
    vol.Optional("entry_id"): str,
    vol.Required("suggestion_id"): str,
    vol.Required("action"): vol.In(["apply", "dismiss"]),
})
@websocket_api.async_response
async def ws_suggestion(hass, connection, msg):
    ctrl = _ctrl(hass, msg.get("entry_id"))
    if ctrl is None:
        connection.send_error(msg["id"], "not_found", "Climator is not set up")
        return
    await ctrl.async_respond_suggestion(msg["suggestion_id"], msg["action"])
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/reset",
    vol.Optional("entry_id"): str,
    vol.Required("scope"): vol.In(["all", "model", "costs", "comfort", "suggestions", "weather"]),
})
@websocket_api.async_response
async def ws_reset(hass, connection, msg):
    ctrl = _ctrl(hass, msg.get("entry_id"))
    if ctrl is None:
        connection.send_error(msg["id"], "not_found", "Climator is not set up")
        return
    await ctrl.async_reset(msg["scope"])
    connection.send_result(msg["id"], ctrl.info())


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/train_history",
    vol.Optional("entry_id"): str,
    vol.Optional("days", default=30): vol.All(int, vol.Range(min=1, max=365)),
})
@websocket_api.async_response
async def ws_train_history(hass, connection, msg):
    ctrl = _ctrl(hass, msg.get("entry_id"))
    if ctrl is None:
        connection.send_error(msg["id"], "not_found", "Climator is not set up")
        return
    result = await ctrl.async_train_from_history(msg["days"])
    connection.send_result(msg["id"], {"result": result, "info": ctrl.info()})
