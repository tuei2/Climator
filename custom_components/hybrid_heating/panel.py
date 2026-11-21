"""Sidebar panel (custom HTML/JS dashboard)."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

URL_BASE = "/climator_static"
PANEL_PATH = "climator"
_DATA = f"{DOMAIN}_panel"


async def async_register_panel(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(_DATA, {"static": False, "panel": False})
    if not data["static"]:
        await hass.http.async_register_static_paths([
            StaticPathConfig(URL_BASE, str(Path(__file__).parent / "frontend"), False)
        ])
        data["static"] = True
    if data["panel"]:
        return
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_PATH,
        webcomponent_name="climator-panel",
        sidebar_title="Climator",
        sidebar_icon="mdi:thermostat-auto",
        module_url=f"{URL_BASE}/climator-panel.js?v={manifest['version']}",
        require_admin=False,
        config={},
    )
    data["panel"] = True


@callback
def async_unregister_panel(hass: HomeAssistant) -> None:
    data = hass.data.get(_DATA)
    if data and data["panel"]:
        frontend.async_remove_panel(hass, PANEL_PATH)
        data["panel"] = False
