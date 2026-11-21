"""Status, cost and learning sensors."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import HybridEntity
from .planner import (
    BIN_LABELS, PHASE_HEAT, PHASE_MAINTAIN, PHASE_OFF, REASONS, STRAT_AIRCO, STRAT_BOTH,
    STRAT_CV, STRAT_OFF, STRATEGIES,
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    ctrl = entry.runtime_data
    entities: list[SensorEntity] = [
        StrategySensor(ctrl), PhaseSensor(ctrl), ReasonSensor(ctrl), PreheatSensor(ctrl),
        MaintainCostSensor(ctrl, STRAT_AIRCO), MaintainCostSensor(ctrl, STRAT_CV),
        CostTotalSensor(ctrl, STRAT_AIRCO), CostTotalSensor(ctrl, STRAT_CV),
        CostTotalSensor(ctrl, "total"), LearningSensor(ctrl),
        CostTodaySensor(ctrl, STRAT_AIRCO), CostTodaySensor(ctrl, STRAT_CV),
        CostTodaySensor(ctrl, "total"),
    ]
    for s in STRATEGIES:
        entities += [HeatRateSensor(ctrl, s), HeatCostSensor(ctrl, s)]
    async_add_entities(entities)


class _Sensor(HybridEntity, SensorEntity):
    _platform_domain = "sensor"


class StrategySensor(_Sensor):
    _unrecorded_attributes = frozenset({"heat_up_options", "maintain_cost_eur_per_hour"})
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
            "target": d.target,
            "heat_up_options": {
                o.strategy: {"minutes": round(o.duration_h * 60), "cost_eur": round(o.cost, 3)}
                for o in d.heat_options
            },
            "maintain_cost_eur_per_hour": {k: round(v, 3) for k, v in d.maintain_costs.items()},
        }


class PhaseSensor(_Sensor):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [PHASE_HEAT, PHASE_MAINTAIN, PHASE_OFF]

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "phase")

    @property
    def native_value(self) -> str:
        return self.ctrl.decision.phase


class ReasonSensor(_Sensor):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = REASONS

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "reason")

    @property
    def native_value(self) -> str:
        return self.ctrl.decision.reason

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        c = self.ctrl
        return {
            "override_until": c.override_until.isoformat() if c.override_until else None,
            "override_entity": c.override_entity,
        }


class PreheatSensor(_Sensor):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "preheat_start")

    @property
    def native_value(self) -> datetime | None:
        return self.ctrl.decision.preheat_start


class MaintainCostSensor(_Sensor):
    _attr_native_unit_of_measurement = "EUR/h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, ctrl, strategy: str) -> None:
        super().__init__(ctrl, f"maintain_cost_{strategy}")
        self._strategy = strategy

    @property
    def native_value(self) -> float | None:
        c = self.ctrl.decision.maintain_costs.get(self._strategy)
        return round(c, 4) if c is not None else None


class CostTotalSensor(_Sensor):
    """Cumulative heating cost; use with statistics graph (daily/weekly/monthly)."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "EUR"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2

    def __init__(self, ctrl, which: str) -> None:
        super().__init__(ctrl, f"cost_{which}")
        self._which = which

    @property
    def native_value(self) -> float:
        costs = self.ctrl.costs
        val = sum(costs.values()) if self._which == "total" else costs[self._which]
        return round(val, 4)


class CostTodaySensor(_Sensor):
    """Heating cost since midnight."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "EUR"
    _attr_suggested_display_precision = 2

    def __init__(self, ctrl, which: str) -> None:
        super().__init__(ctrl, f"cost_today_{which}")
        self._which = which

    @property
    def native_value(self) -> float:
        return round(self.ctrl.cost_today(self._which), 4)


class HeatRateSensor(_Sensor):
    """Learned heat-up speed at the current outdoor temperature."""

    _attr_native_unit_of_measurement = "°C/h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, ctrl, strategy: str) -> None:
        super().__init__(ctrl, f"heat_rate_{strategy}")
        self._strategy = strategy

    @property
    def native_value(self) -> float | None:
        if self.ctrl.t_out is None:
            return None
        return round(self.ctrl.model.params(self._strategy, self.ctrl.t_out)["rate"], 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.ctrl.t_out is None:
            return {}
        return {"learned": self.ctrl.model.params(self._strategy, self.ctrl.t_out)["learned"]}


class HeatCostSensor(_Sensor):
    """Learned cost to raise the room 1 °C at the current outdoor temperature."""

    _attr_native_unit_of_measurement = "EUR/°C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, ctrl, strategy: str) -> None:
        super().__init__(ctrl, f"heat_cost_{strategy}")
        self._strategy = strategy

    @property
    def native_value(self) -> float | None:
        if self.ctrl.t_out is None:
            return None
        p = self.ctrl.model.params(self._strategy, self.ctrl.t_out)
        pr = self.ctrl.prices
        return round(p["kwh_per_deg"] * pr.kwh + p["m3_per_deg"] * pr.gas, 4)


class LearningSensor(_Sensor):
    _unrecorded_attributes = frozenset({"table", "last_event"})
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "learning")

    @property
    def native_value(self) -> int:
        return self.ctrl.model.sample_count()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        model = self.ctrl.model
        pr = self.ctrl.prices
        table = []
        for strat in STRATEGIES:
            for idx, label in enumerate(BIN_LABELS):
                b = model.data.get(strat, {}).get(str(idx))
                if not b or (b.get("n_heat", 0) + b.get("n_maint", 0)) == 0:
                    continue
                table.append({
                    "strategy": strat,
                    "outdoor": label,
                    "heat_samples": b.get("n_heat", 0),
                    "maintain_samples": b.get("n_maint", 0),
                    "rate": round(b["rate"], 2),
                    "cost_per_deg": round(b["kwh_per_deg"] * pr.kwh + b["m3_per_deg"] * pr.gas, 3),
                    "maintain_cost_per_hour_per_k": round(
                        b["kwh_per_hk"] * pr.kwh + b["m3_per_hk"] * pr.gas, 4),
                })
        return {"last_event": self.ctrl.learner.last_event, "table": table}
