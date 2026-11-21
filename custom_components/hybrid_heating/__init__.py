"""Hybrid Heating: cost-optimised control of an airco + CV thermostat."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .controller import HybridHeatingController

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.NUMBER, Platform.TIME]

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
                await e.runtime_data.async_reset_learning()

        hass.services.async_register(DOMAIN, "reset_learning", _reset)

    ctrl.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HybridConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        await entry.runtime_data.async_shutdown()
    return ok


async def _async_update_listener(hass: HomeAssistant, entry: HybridConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
