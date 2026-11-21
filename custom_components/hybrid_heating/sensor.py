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
    PHASE_HEAT, PHASE_MAINTAIN, PHASE_OFF, PHASE_PAUSED, REASONS, STRAT_AIRCO, STRAT_BOTH,
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
        CostTodaySensor(ctrl, "total"), ComfortSensor(ctrl), AccuracySensor(ctrl),
        DiagnosticsSensor(ctrl), ExpectedCostSensor(ctrl), PresenceSensor(ctrl),
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
    _attr_options = [PHASE_HEAT, PHASE_MAINTAIN, PHASE_OFF, PHASE_PAUSED]

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
    """Expected heat-up speed right now (model, full power, after losses)."""

    _attr_native_unit_of_measurement = "°C/h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, ctrl, strategy: str) -> None:
        super().__init__(ctrl, f"heat_rate_{strategy}")
        self._strategy = strategy

    @property
    def native_value(self) -> float | None:
        c = self.ctrl
        if c.t_out is None or c.t_in is None:
            return None
        m = c.model
        return round(m.slope(c.t_in, c.t_out, m.heat_rate(self._strategy, c.t_out),
                             c.solar_kw or 0.0), 3)


class HeatCostSensor(_Sensor):
    """Cost to raise the room 1 °C with this source at the current outdoor temperature."""

    _attr_native_unit_of_measurement = "EUR/°C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, ctrl, strategy: str) -> None:
        super().__init__(ctrl, f"heat_cost_{strategy}")
        self._strategy = strategy

    @property
    def native_value(self) -> float | None:
        c = self.ctrl
        if c.t_out is None:
            return None
        m, p = c.model, c.prices
        srcs = ["airco", "cv"] if self._strategy == "both" else [self._strategy]
        cost_h = sum(m.pmax[s] * (p.kwh if s == "airco" else p.gas) for s in srcs)
        return round(cost_h / max(m.heat_rate(self._strategy, c.t_out), 1e-3), 4)


class LearningSensor(_Sensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _unrecorded_attributes = frozenset({"parameters", "confidence", "excluded"})

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "learning")

    @property
    def native_value(self) -> int:
        return round(self.ctrl.model.n_eff)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        m = self.ctrl.model
        return {"parameters": {k: round(v, 4) for k, v in m.theta.items()},
                "confidence": m.confidence(), "excluded": m.excluded,
                "last_sample": self.ctrl.last_sample_reason}


class ComfortSensor(_Sensor):
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "comfort_score")

    @property
    def native_value(self) -> float | None:
        return self.ctrl.comfort_score(1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"last_7_days": self.ctrl.comfort_score(7)}


class AccuracySensor(_Sensor):
    """Average error of a 1-hour-ahead model prediction over the last 3 days."""

    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "model_accuracy")

    @property
    def native_value(self) -> float | None:
        mae = self.ctrl.model.check()["mae_1h"]
        return round(mae, 3) if mae is not None else None


class DiagnosticsSensor(_Sensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unrecorded_attributes = frozenset({"checks"})

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "diagnostics")

    @property
    def native_value(self) -> int:
        return sum(1 for d in self.ctrl.diagnostics() if d["status"] in ("warn", "error"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"checks": {d["id"]: d["status"] for d in self.ctrl.diagnostics()}}


class ExpectedCostSensor(_Sensor):
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "EUR"
    _attr_suggested_display_precision = 2

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "expected_cost_24h")

    @property
    def native_value(self) -> float | None:
        return self.ctrl.forecast_result.get("cost")


class PresenceSensor(_Sensor):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["home", "away", "vacation"]

    def __init__(self, ctrl) -> None:
        super().__init__(ctrl, "presence")

    @property
    def native_value(self) -> str:
        return self.ctrl.presence

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"open_windows": self.ctrl.open_windows, "window_paused": self.ctrl.window_open}
