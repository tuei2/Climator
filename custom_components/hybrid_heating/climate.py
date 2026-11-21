"""Climate entity that represents the whole hybrid system."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity, ClimateEntityFeature, HVACAction, HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MODE_AUTO, MODE_HEAT, MODE_OFF
from .entity import HybridEntity
from .planner import PHASE_HEAT, PHASE_OFF

MODE_MAP = {MODE_OFF: HVACMode.OFF, MODE_HEAT: HVACMode.HEAT, MODE_AUTO: HVACMode.AUTO}


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    async_add_entities([HybridClimate(entry.runtime_data)])


class HybridClimate(HybridEntity, ClimateEntity):
    _platform_domain = "climate"
    _attr_name = None
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 10
    _attr_max_temp = 25

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "climate")

    @property
    def current_temperature(self):
        return self.ctrl.t_in

    @property
    def target_temperature(self):
        d = self.ctrl.decision
        if d.target is not None:
            return d.target
        return self.ctrl.settings["manual_target"]

    @property
    def hvac_mode(self) -> HVACMode:
        return MODE_MAP[self.ctrl.settings["mode"]]

    @property
    def hvac_action(self) -> HVACAction:
        phase = self.ctrl.decision.phase
        if phase == PHASE_OFF:
            return HVACAction.OFF
        return HVACAction.HEATING if phase == PHASE_HEAT else HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self.ctrl.decision
        return {
            "strategy": d.strategy,
            "phase": d.phase,
            "reason": d.reason,
            "preheat_start": d.preheat_start.isoformat() if d.preheat_start else None,
            "deadline": d.deadline.isoformat() if d.deadline else None,
            "override_until": (self.ctrl.override_until.isoformat()
                               if self.ctrl.override_until else None),
            "override_entity": self.ctrl.override_entity,
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self.ctrl.async_set_manual_target(float(temp))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        mode = {v: k for k, v in MODE_MAP.items()}[hvac_mode]
        await self.ctrl.async_set_setting("mode", mode)

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.AUTO)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)
