"""Constants for Hybrid Heating."""

DOMAIN = "hybrid_heating"

# Entities (config)
CONF_NAME = "name"
CONF_ROOM_SENSOR = "room_sensor"
CONF_OUTDOOR_SENSOR = "outdoor_sensor"
CONF_AIRCO = "airco_climate"
CONF_CV = "cv_climate"
CONF_AIRCO_ENERGY = "airco_energy_sensor"
CONF_GAS = "gas_sensor"
CONF_DHW = "dhw_sensor"

ENTITY_KEYS = [
    CONF_ROOM_SENSOR,
    CONF_OUTDOOR_SENSOR,
    CONF_AIRCO,
    CONF_CV,
    CONF_AIRCO_ENERGY,
    CONF_GAS,
    CONF_DHW,
]

# Options
CONF_PRICE_KWH = "price_kwh"
CONF_PRICE_GAS = "price_gas"
CONF_AIRCO_OFFSET = "airco_offset"
CONF_CV_OFFSET = "cv_offset"
CONF_CV_SETBACK = "cv_setback"
CONF_AIRCO_MIN_OUTDOOR = "airco_min_outdoor"
CONF_ALLOW_BOTH = "allow_both"
CONF_MAX_HEATUP = "max_heatup_minutes"
CONF_MAX_PREHEAT = "max_preheat_minutes"
CONF_PREHEAT_MARGIN = "preheat_margin_minutes"
CONF_MIN_SWITCH = "min_switch_minutes"
CONF_HYSTERESIS = "hysteresis"
CONF_OVERRIDE_MINUTES = "override_minutes"

DEFAULT_OPTIONS = {
    CONF_PRICE_KWH: 0.25,
    CONF_PRICE_GAS: 1.35,
    CONF_AIRCO_OFFSET: 1.0,
    CONF_CV_OFFSET: 0.0,
    CONF_CV_SETBACK: 15.0,
    CONF_AIRCO_MIN_OUTDOOR: -10.0,
    CONF_ALLOW_BOTH: True,
    CONF_MAX_HEATUP: 60,
    CONF_MAX_PREHEAT: 180,
    CONF_PREHEAT_MARGIN: 15,
    CONF_MIN_SWITCH: 20,
    CONF_HYSTERESIS: 0.3,
    CONF_OVERRIDE_MINUTES: 120,
}

# Runtime settings (changeable via entities, persisted in storage)
MODE_OFF = "off"
MODE_HEAT = "heat"  # manual target
MODE_AUTO = "auto"  # schedule + preheating

DEFAULT_SETTINGS = {
    "mode": MODE_OFF,
    "manual_target": 20.0,
    "comfort_temp": 20.5,
    "eco_temp": 17.0,
    "comfort_start": "07:00",
    "comfort_end": "22:30",
}

UPDATE_INTERVAL_SECONDS = 60
STORAGE_VERSION = 1
