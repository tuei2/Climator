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
        + gab · P_airco · boost              extra heat when the fan blows hard
        + gc · G_cv                           boiler (G in m³ gas per hour)
        + gs · S                              sun (S = solar panel power in kW)
```

Every 15 minutes it takes a sample (room and outdoor temperature, airco energy, gas, solar)
and updates the parameters with weighted least squares — **in every mode, also in Learn only
and while the heating is off** (cooling down teaches it the heat loss). Older data slowly
fades out (half-life about a week). Until there is enough data, sensible defaults are used.
Samples are skipped when hot water is running, a window is open, a meter jumps or data is missing.

Each kind of sample (air conditioner, boiler, both, nothing) only ages when new samples of
the same kind arrive. A source that is not used for weeks therefore **keeps what was learned
about it** instead of drifting back to the defaults.

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

## Self-testing
If Climator always picks the air conditioner, it would never learn how the boiler really
performs. With **self-testing** (on by default, switch off in the panel) Climator deliberately
uses a source when it knows too little about it (confidence *none* or *low*) or when the source
gave no data for a number of days (default 5):
- only during normal heating moments (comfort, eco, preheat, fixed temperature), never at night,
  when away, on vacation or with a window open;
- only if the room is still warm in time (preheat deadlines are respected);
- only within a **weekly budget** for the extra cost (default € 1);
- a test stops after about an hour of useful data, after 2 hours, or when comfort would suffer.

The panel shows a banner while testing, and the **Model** tab lists per source how recent the
data is and the last tests with their cost. *Learn only* mode never tests (it controls nothing).

## Smart night temperature
Letting the room cool down is not always cheaper: after a deep cool-down the morning heat-up may
need the boiler or both sources at the coldest moment of the day, while keeping the room a bit
warmer could be done by the air conditioner on a soft fan. With **smart night temperature**
(on by default) Climator simulates every level from your eco temperature up to a maximum
(default 19 °C) — and "off at night" when that is enabled — for the coming setback period,
including heating up again, using the model and the weather forecast. It picks the cheapest
level that is just as comfortable, and only deviates from your own setting when that saves at
least € 0.03 (or 2 %). Re-evaluated every 30 minutes. The **Forecast** tab shows the chosen
level, the saving and the expected cost of every level.

## Off at night
Optional (**Settings → Off at night**): during a time window (default 23:00–06:00) the air
conditioner is switched **off** and the boiler goes to a low temperature (default 12 °C), which
also acts as frost guard. Preheating for the next comfort block still starts in time — also
during the window. In *Fixed temperature* mode the room is preheated for the end of the window.

## Air conditioner fan
Climator lets the fan **blow hard while heating up** (fastest, used for preheating) and
**softly while keeping warm** (quiet comfort). Which fan modes are used is chosen automatically
from the modes your air conditioner offers, or set in the panel (**Settings → Air conditioner
fan**). The model learns the maximum power for both and how much extra heat per kWh blowing
hard gives (`gab`). When the soft fan cannot keep up (hard frost) it blows harder.
Changing the fan with the remote counts as a manual change (Climator pauses).

## Forecast and where to save
The **Forecast** tab simulates the next **3 days** with the model and the weather forecast:
- expected cost for the rest of today, tomorrow, 3 days and per week;
- the plan (target, expected room temperature, source and fan) and **cost per hour** in a chart;
- a **timeline of upcoming actions**: what happens when, until when, temperature change and cost;
- cost per day, and where the money goes (heating up vs keeping warm, airco vs boiler);
- **Where can you save?** — the forecast is re-run with one change at a time (comfort 0.5/1 °C
  lower, comfort 30 min later, eco ±1 °C, only airco, only boiler, never both, no fan control)
  showing the saving per week and the effect on comfort (hours too cold).

In *Learn only* mode the forecast shows what the schedule *would* do.

## Functions — each can be switched off
| Function | What it does | Needs |
|---|---|---|
| Smart night temperature | Cheapest night/eco level between eco and a maximum, from model + forecast | — |
| Off at night | Airco off and boiler low in a time window (off by default) | — |
| Self-testing | Use a less known source now and then to keep learning, within a budget | airco + boiler |
| Fan speeds | Hard fan while heating up, soft fan while keeping warm | airco with fan modes |
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
A **Climator** item in the sidebar with five tabs: **Status** (live values, chart with past and
expected temperature), **Forecast** (3-day plan, actions, costs, savings), **Costs**
(per day/month), **Model** (see above) and **Settings** (mode, schedule, fan, functions,
presence, prices).

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
| `sensor.climator_expected_cost_24h`, `sensor.climator_expected_cost_week` | Expected heating cost next 24 h / per week |
| `sensor.climator_next_action` | Time of the next planned change; attributes describe it |
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
