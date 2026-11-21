"""Comfort / eco temperature numbers."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import HybridEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    ctrl = entry.runtime_data
    async_add_entities([TempNumber(ctrl, "comfort_temp"), TempNumber(ctrl, "eco_temp")])


class TempNumber(HybridEntity, NumberEntity):
    _attr_native_min_value = 10
    _attr_native_max_value = 25
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, ctrl, key: str) -> None:
        super().__init__(ctrl, key)
        self._key = key

    @property
    def native_value(self) -> float:
        return float(self.ctrl.settings[self._key])

    async def async_set_native_value(self, value: float) -> None:
        await self.ctrl.async_set_setting(self._key, value)
