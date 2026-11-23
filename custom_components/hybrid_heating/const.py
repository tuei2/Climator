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
CONF_WINDOWS = "window_sensors"
CONF_PRESENCE = "presence_entities"
CONF_WEATHER = "weather_entity"
CONF_SOLAR = "solar_sensor"

ENTITY_KEYS = [
    CONF_ROOM_SENSOR,
    CONF_OUTDOOR_SENSOR,
    CONF_AIRCO,
    CONF_CV,
    CONF_AIRCO_ENERGY,
    CONF_GAS,
    CONF_DHW,
    CONF_WINDOWS,
    CONF_PRESENCE,
    CONF_WEATHER,
    CONF_SOLAR,
]
OPTIONAL_ENTITY_KEYS = [CONF_DHW, CONF_WINDOWS, CONF_PRESENCE, CONF_WEATHER, CONF_SOLAR]

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
CONF_WINDOW_DELAY = "window_delay_minutes"
CONF_AWAY_DELAY = "away_delay_minutes"
CONF_BUFFER_DEG = "buffer_degrees"
CONF_BUFFER_THRESHOLD = "buffer_threshold_percent"
CONF_NOTIFY_AFTER = "notify_after_minutes"

DEFAULT_OPTIONS = {
    CONF_PRICE_KWH: 0.25,
    CONF_PRICE_GAS: 1.35,
    CONF_AIRCO_OFFSET: 1.0,
    CONF_CV_OFFSET: 0.0,
    CONF_CV_SETBACK: 15.0,
    CONF_AIRCO_MIN_OUTDOOR: -10.0,
    CONF_ALLOW_BOTH: True,
    CONF_MAX_HEATUP: 60,
    CONF_MAX_PREHEAT: 240,
    CONF_PREHEAT_MARGIN: 15,
    CONF_MIN_SWITCH: 20,
    CONF_HYSTERESIS: 0.3,
    CONF_OVERRIDE_MINUTES: 120,
    CONF_WINDOW_DELAY: 3,
    CONF_AWAY_DELAY: 15,
    CONF_BUFFER_DEG: 0.5,
    CONF_BUFFER_THRESHOLD: 15,
    CONF_NOTIFY_AFTER: 30,
}

# Runtime settings (changeable via entities, persisted in storage)
MODE_OFF = "off"
MODE_HEAT = "heat"  # manual target
MODE_AUTO = "auto"  # schedule + preheating

DEFAULT_SETTINGS = {
    "mode": MODE_OFF,
    "manual_target": 20.0,
    "eco_temp": 17.0,
    "away_temp": 16.0,
    "vacation_temp": 14.0,
    "vacation": False,
    "guest": False,
    "fan_boost_mode": None,     # None = pick automatically from the airco's fan modes
    "fan_comfort_mode": None,
    "explore_budget": 1.0,      # EUR per week that test runs may cost extra
    "explore_days": 5,          # test a source when it gave no data for this many days
    "night_start": "23:00",     # night: airco off, boiler at night_min (feature "night")
    "night_end": "06:00",
    "night_min": 12.0,
    "setback_max": 19.0,        # smart setback: highest level considered (lowest = eco_temp)
}

# Optional functions; each can be switched off (switch entity + panel).
FEATURES = ["smart_setback", "night", "explore", "fan", "windows", "presence", "forecast", "buffer", "solar", "notifications",
            "suggestions"]
DEFAULT_FEATURES = {f: f not in ("buffer", "night") for f in FEATURES}

UPDATE_INTERVAL_SECONDS = 60
STORAGE_VERSION = 1
VERSION = "0.10.0"
