"""Switches: vacation, guest mode and on/off for each optional function."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import FEATURES
from .entity import HybridEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    ctrl = entry.runtime_data
    ents: list[SwitchEntity] = [SettingSwitch(ctrl, "vacation"), SettingSwitch(ctrl, "guest")]
    ents += [FeatureSwitch(ctrl, f) for f in FEATURES]
    async_add_entities(ents)


class SettingSwitch(HybridEntity, SwitchEntity):
    _platform_domain = "switch"

    def __init__(self, ctrl, key: str) -> None:
        super().__init__(ctrl, key)
        self._key = key

    @property
    def is_on(self) -> bool:
        return bool(self.ctrl.settings.get(self._key))

    async def async_turn_on(self, **kwargs) -> None:
        await self.ctrl.async_set_setting(self._key, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.ctrl.async_set_setting(self._key, False)


class FeatureSwitch(HybridEntity, SwitchEntity):
    _platform_domain = "switch"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, ctrl, feature: str) -> None:
        super().__init__(ctrl, f"feature_{feature}")
        self._feature = feature

    @property
    def is_on(self) -> bool:
        return bool(self.ctrl.features.get(self._feature))

    @property
    def extra_state_attributes(self):
        return {"active": self.ctrl.feature_active(self._feature)}

    async def async_turn_on(self, **kwargs) -> None:
        await self.ctrl.async_set_feature(self._feature, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.ctrl.async_set_feature(self._feature, False)
