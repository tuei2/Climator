"""Status sensors."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import HybridEntity
from .planner import (
    PHASE_HEAT, PHASE_MAINTAIN, PHASE_OFF, STRAT_AIRCO, STRAT_BOTH, STRAT_CV, STRAT_OFF,
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    ctrl = entry.runtime_data
    async_add_entities([
        StrategySensor(ctrl),
        PhaseSensor(ctrl),
        PreheatSensor(ctrl),
        MaintainCostSensor(ctrl, STRAT_AIRCO),
        MaintainCostSensor(ctrl, STRAT_CV),
        LearningSensor(ctrl),
    ])


class StrategySensor(HybridEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [STRAT_AIRCO, STRAT_CV, STRAT_BOTH, STRAT_OFF]

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "strategy")

    @property
    def native_value(self) -> str:
        return self.ctrl.decision.strategy

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self.ctrl.decision
        return {
            "reason": d.reason,
            "target": d.target,
            "heat_up_options": {
                o.strategy: {"minutes": round(o.duration_h * 60), "cost_eur": round(o.cost, 3)}
                for o in d.heat_options
            },
            "maintain_cost_eur_per_hour": {k: round(v, 3) for k, v in d.maintain_costs.items()},
        }


class PhaseSensor(HybridEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [PHASE_HEAT, PHASE_MAINTAIN, PHASE_OFF]

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "phase")

    @property
    def native_value(self) -> str:
        return self.ctrl.decision.phase


class PreheatSensor(HybridEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "preheat_start")

    @property
    def native_value(self) -> datetime | None:
        return self.ctrl.decision.preheat_start


class MaintainCostSensor(HybridEntity, SensorEntity):
    _attr_native_unit_of_measurement = "€/h"
    _attr_suggested_display_precision = 3

    def __init__(self, ctrl, strategy: str) -> None:
        super().__init__(ctrl, f"maintain_cost_{strategy}")
        self._strategy = strategy

    @property
    def native_value(self) -> float | None:
        c = self.ctrl.decision.maintain_costs.get(self._strategy)
        return round(c, 4) if c is not None else None


class LearningSensor(HybridEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "metingen"

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "learning")

    @property
    def native_value(self) -> int:
        return self.ctrl.model.sample_count()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"last_event": self.ctrl.learner.last_event, **self.ctrl.model.summary()}
