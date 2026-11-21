# Climator

Cost-optimised hybrid heating for Home Assistant: combines an air conditioner (air-to-air
heat pump) with a gas boiler thermostat. Climator learns a physical model of your room,
picks the cheapest way to heat up and to keep warm, and preheats so the room is warm at the
time you set.

Works with any `climate` entity (tested with a Daikin + Faikin and a Plugwise Anna).
The integration and its panel are available in **English and Dutch**.

## Installation (HACS)
1. HACS → ⋮ → *Custom repositories* → `https://github.com/tuei2/Climator`, type *Integration*.
2. Install **Climator** and restart Home Assistant.
3. Settings → Devices & services → *Add integration* → **Climator**.

## Setup
| Field | Example |
|---|---|
| Room temperature (source) | any temperature sensor in the room |
| Outdoor temperature | your outdoor sensor |
| Air conditioner | `climate.<faikin>` |
| Boiler thermostat | `climate.anna` |
| Air conditioner energy (kWh, total increasing) | Faikin energy sensor, or an *Integral* helper on its power |
| Gas meter (m³, total increasing) | P1/DSMR gas meter reading |
| Hot water active *(optional)* | Plugwise `binary_sensor …dhw_state` — excludes shower gas from learning and costs |
| Window/door sensors *(optional)* | binary sensors of the room |
| Presence *(optional)* | `person.*`, device trackers, binary sensors or input booleans |
| Weather forecast *(optional)* | any `weather.*` entity with an hourly forecast |
| Solar panel power *(optional)* | inverter power sensor (W or kW) |

Optional entities can be added or removed later via **Configure** on the integration, where
you also find the advanced settings (offsets, delays, buffer size, …).

## How the model works
Climator describes the room with one simple physics equation, in °C per hour:

```
dT/dt = − k · (T_room − T_outside)          heat loss
        + (ga0 + ga1 · T_outside) · P_airco  air conditioner (P in kW electric)
        + gc · G_cv                           boiler (G in m³ gas per hour)
        + gs · S                              sun (S = solar panel power in kW)
```

Every 15 minutes it takes a sample (room and outdoor temperature, airco energy, gas, solar)
and updates the parameters with weighted least squares — **in every mode, also in Learn only
and while the heating is off** (cooling down teaches it the heat loss). Older data slowly
fades out (half-life about a week). Until there is enough data, sensible defaults are used.
Samples are skipped when hot water is running, a window is open, a meter jumps or data is missing.

With the model Climator can:
- calculate how long each source needs to heat up and what it costs;
- calculate the cost per hour to keep the room warm with each source;
- simulate the coming 24 hours (expected room temperature, plan and cost);
- find the latest preheat start that still reaches the comfort temperature in time.

### Is the model right?
The **Model** tab of the panel shows:
- **prediction error** — every sample, Climator predicts one hour ahead and compares with
  reality (good ≤ 0.3 °C);
- a **reality vs model** chart of the last 48 hours;
- every learned value **in plain language** with a confidence level (none / low / medium / high)
  and its uncertainty (±);
- **which source is cheaper at which outdoor temperature**;
- **checks**: sensors available, meters counting while heating, model values plausible,
  enough usable data, forecast received;
- skipped samples per reason, suggestions, and reset buttons per part.

## Functions — each can be switched off
| Function | What it does | Needs |
|---|---|---|
| Window detection | Pauses heating while a window/door is open (after a delay) | window sensors |
| Presence | Away temperature when nobody is home (after a delay); *Guests* switch ignores it | presence entities |
| Weather forecast | Uses the hourly forecast (corrected for your own sensor) for preheating and the 24-hour plan | weather entity |
| Heat buffer | Stores a little extra heat when the airco is clearly cheaper now than later in the comfort period | weather entity (off by default) |
| Solar gain | Learns how much the sun warms the room | solar power sensor |
| Notifications | Persistent notification when a sensor or device is unavailable | — |
| Suggestions | After 1–2 weeks: frequent manual changes, low comfort, windows, model accuracy, break-even temperature | — |

Switch them in the panel (**Settings → Functions**) or with `switch.climator_feature_*`.
A function that is on but has no entity configured simply does nothing.

## Schedule
A week schedule with a **workday** and a **weekend** profile, each with comfort blocks
(start, end, temperature) that can be switched on/off individually. Assign each weekday to a
profile, or switch the weekend profile off to use the workday profile every day. Outside the
blocks the *eco* temperature applies. Edit it in the panel (**Settings → Schedule**).

Vacation (`switch.climator_vacation`) uses the vacation temperature and ignores the schedule.

## Modes
| Mode | Behaviour |
|---|---|
| Learn only | Controls nothing, only learns (also `climate.climator` *off*) |
| Fixed temperature | Keeps the temperature set on `climate.climator` |
| Schedule + preheat | Follows the schedule and preheats |

When you change the air conditioner or boiler yourself (remote, dial, app), Climator pauses
(default 120 minutes) and keeps learning.

## Climator panel
A **Climator** item in the sidebar with four tabs: **Status** (live values, chart with past and
expected temperature, plan and outdoor forecast), **Costs** (per day/month), **Model** (see
above) and **Settings** (mode, schedule, functions, presence, prices).

## Entities
All entity ids are fixed and start with `climator_`.

| Entity | Purpose |
|---|---|
| `climate.climator`, `select.climator_mode` | Mode and fixed temperature |
| `number.climator_price_kwh`, `number.climator_price_gas` | Energy prices used for every decision |
| `number.climator_eco_temp`, `_away_temp`, `_vacation_temp` | Temperatures outside the schedule |
| `switch.climator_vacation`, `switch.climator_guest` | Vacation and guest mode |
| `switch.climator_feature_*` | Optional functions on/off |
| `sensor.climator_strategy` / `_phase` / `_reason` / `_presence` | What Climator does and why |
| `sensor.climator_preheat_start` | When preheating starts |
| `sensor.climator_cost_today_*`, `sensor.climator_cost_*` | Heating cost today and cumulative (statistics) |
| `sensor.climator_expected_cost_24h` | Expected heating cost for the next 24 hours |
| `sensor.climator_comfort_score` | % of comfort time the room was warm enough (today, 7 days) |
| `sensor.climator_model_accuracy` | Average 1-hour-ahead prediction error |
| `sensor.climator_diagnostics` | Number of failed checks |
| `sensor.climator_heat_rate_*`, `sensor.climator_heat_cost_*` | Heat-up speed now and cost per °C |
| `sensor.climator_maintain_cost_*` | Cost per hour to keep warm |
| `sensor.climator_learning` | Samples in the model; attributes hold the parameters |

Service `hybrid_heating.reset_learning` with `scope`: `model`, `costs`, `comfort`,
`suggestions`, `weather` or `all`.

## Notes
- **Plugwise Anna**: while Climator is in control it sets the Anna to *heat* (manual), which
  disables the Anna's own schedule. In *Learn only* nothing is changed.
- **Air conditioner offset**: Climator assumes the airco setpoint is 1 °C above the wanted room
  temperature (configurable).
- DSMR4 meters report gas only once per hour; DSMR5 (every 5 minutes) gives better results.
- Radiators keep heating for a while after the boiler stops; the 15-minute samples smooth this out.
- Upgrading from 0.4 or older: the previous learning data is replaced by the new model, and the
  single comfort block becomes the first block of the new week schedule.

## Optional Lovelace dashboard
[`dashboards/climator.yaml`](dashboards/climator.yaml) contains a dashboard built from standard cards.

## Releasing a new version
Bump `version` in `custom_components/hybrid_heating/manifest.json` (and `VERSION` in `const.py`)
and push to `main`. The release workflow creates the GitHub release; HACS then offers the update.
