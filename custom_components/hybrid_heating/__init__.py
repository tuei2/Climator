"""Climator: cost-optimised control of an airco (heat pump) + gas boiler thermostat."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .controller import HybridHeatingController
from .panel import async_register_panel, async_unregister_panel
from .websocket import async_register as async_register_ws

RESET_SCOPES = ["all", "model", "costs", "comfort", "suggestions", "weather"]

PLATFORMS = [
    Platform.CLIMATE, Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH,
]

type HybridConfigEntry = ConfigEntry[HybridHeatingController]


async def async_setup_entry(hass: HomeAssistant, entry: HybridConfigEntry) -> bool:
    ctrl = HybridHeatingController(hass, entry)
    await ctrl.async_setup()
    entry.runtime_data = ctrl
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, "reset_learning"):
        async def _reset(call: ServiceCall) -> None:
            for e in hass.config_entries.async_loaded_entries(DOMAIN):
                await e.runtime_data.async_reset(call.data.get("scope", "model"))

        hass.services.async_register(
            DOMAIN, "reset_learning", _reset,
            schema=vol.Schema({vol.Optional("scope", default="model"): vol.In(RESET_SCOPES)}))
        async_register_ws(hass)

        async def _train(call: ServiceCall) -> None:
            for e in hass.config_entries.async_loaded_entries(DOMAIN):
                await e.runtime_data.async_train_from_history(call.data.get("days", 30))

        hass.services.async_register(
            DOMAIN, "train_from_history", _train,
            schema=vol.Schema({vol.Optional("days", default=30): vol.All(int, vol.Range(min=1, max=365))}))

    await async_register_panel(hass)
    ctrl.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HybridConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        await entry.runtime_data.async_shutdown()
        if not [e for e in hass.config_entries.async_loaded_entries(DOMAIN)
                if e.entry_id != entry.entry_id]:
            async_unregister_panel(hass)
    return ok


async def _async_update_listener(hass: HomeAssistant, entry: HybridConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
