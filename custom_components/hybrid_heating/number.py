"""Comfort / eco temperature numbers."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_PRICE_GAS, CONF_PRICE_KWH
from .entity import HybridEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    ctrl = entry.runtime_data
    async_add_entities([
        TempNumber(ctrl, "eco_temp"), TempNumber(ctrl, "away_temp"),
        TempNumber(ctrl, "vacation_temp"),
        PriceNumber(ctrl, CONF_PRICE_KWH, "EUR/kWh", 2.0),
        PriceNumber(ctrl, CONF_PRICE_GAS, "EUR/m³", 5.0),
    ])


class TempNumber(HybridEntity, NumberEntity):
    _platform_domain = "number"
    _attr_native_min_value = 5
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


class PriceNumber(HybridEntity, NumberEntity):
    """Energy price used for all cost decisions."""

    _platform_domain = "number"
    _attr_native_min_value = 0
    _attr_native_step = 0.001
    _attr_mode = NumberMode.BOX

    def __init__(self, ctrl, key: str, unit: str, maximum: float) -> None:
        super().__init__(ctrl, key)
        self._key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_native_max_value = maximum

    @property
    def native_value(self) -> float:
        return float(self.ctrl.prices.kwh if self._key == CONF_PRICE_KWH
                     else self.ctrl.prices.gas)

    async def async_set_native_value(self, value: float) -> None:
        await self.ctrl.async_set_setting(self._key, value)
