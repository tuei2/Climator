"""Base entity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .controller import HybridHeatingController


class HybridEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, ctrl: HybridHeatingController, key: str) -> None:
        self.ctrl = ctrl
        self._attr_unique_id = f"{ctrl.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ctrl.entry.entry_id)},
            name=ctrl.entry.title,
            manufacturer="Custom",
            model="Hybrid Heating",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.ctrl.async_add_listener(self.async_write_ha_state))
