"""Operating mode select: learn only / manual / schedule."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MODE_AUTO, MODE_HEAT, MODE_OFF
from .entity import HybridEntity

OPTIONS = {MODE_OFF: "learn_only", MODE_HEAT: "manual", MODE_AUTO: "schedule"}


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    async_add_entities([ModeSelect(entry.runtime_data)])


class ModeSelect(HybridEntity, SelectEntity):
    _platform_domain = "select"
    _attr_options = list(OPTIONS.values())

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "mode")

    @property
    def current_option(self) -> str:
        return OPTIONS[self.ctrl.settings["mode"]]

    async def async_select_option(self, option: str) -> None:
        mode = {v: k for k, v in OPTIONS.items()}[option]
        await self.ctrl.async_set_setting("mode", mode)
