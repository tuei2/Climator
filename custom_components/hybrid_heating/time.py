"""Comfort start / end time entities."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import HybridEntity
from .planner import parse_time


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    ctrl = entry.runtime_data
    async_add_entities([ComfortTime(ctrl, "comfort_start"), ComfortTime(ctrl, "comfort_end")])


class ComfortTime(HybridEntity, TimeEntity):
    def __init__(self, ctrl, key: str) -> None:
        super().__init__(ctrl, key)
        self._key = key

    @property
    def native_value(self) -> time:
        return parse_time(self.ctrl.settings[self._key])

    async def async_set_value(self, value: time) -> None:
        await self.ctrl.async_set_setting(self._key, value.strftime("%H:%M"))
