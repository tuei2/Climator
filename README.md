# Climator

Cost-optimised hybrid heating for Home Assistant: combines an air conditioner (air-to-air
heat pump) with a gas boiler thermostat. Climator learns how fast and at what cost each
source heats your room, per outdoor temperature, picks the cheapest way to heat up and to
keep the room warm, and preheats so the room is warm at the time you set.

Works with any `climate` entity (tested with a Daikin + Faikin and a Plugwise Anna).
The integration UI is available in **English and Dutch**.

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
| Hot water active (optional) | Plugwise `binary_sensor …dhw_state` — excludes shower gas from learning and costs |

Advanced settings (offsets, setback temperature, pause after manual change, …) are under
**Configure** on the integration.

## Entities
All entities have fixed ids starting with `climator_`, independent of language.

| Entity | Purpose |
|---|---|
| `climate.climator` | Off = learn only, Heat = fixed temperature, Auto = schedule + preheat |
| `select.climator_mode` | Same modes: *Learn only*, *Manual temperature*, *Schedule + preheat* |
| `number.climator_price_kwh`, `number.climator_price_gas` | **Energy prices** used for every decision |
| `number.climator_comfort_temp`, `number.climator_eco_temp` | Schedule temperatures |
| `time.climator_comfort_start`, `time.climator_comfort_end` | Comfort period |
| `sensor.climator_strategy` / `_phase` / `_reason` | What Climator is doing and why |
| `sensor.climator_preheat_start` | When preheating starts |
| `sensor.climator_cost_today_*` | Heating cost since midnight (air conditioner, boiler, total) |
| `sensor.climator_cost_*` | Cumulative heating cost (long-term statistics: per day/week/month) |
| `sensor.climator_heat_rate_*` | Learned heat-up rate (°C/h) at the current outdoor temperature |
| `sensor.climator_heat_cost_*` | Learned cost to heat up 1 °C |
| `sensor.climator_maintain_cost_*` | Cost per hour to keep the room at temperature |
| `sensor.climator_learning` | Number of learned samples; attribute `table` holds all learned data |

Service `hybrid_heating.reset_learning` clears the learned data.

## Climator panel
After installation a **Climator** item appears in the sidebar: a dedicated dashboard page
(English or Dutch, following your Home Assistant language) with four tabs:

- **Status** — room, outdoor, current heat source, preheat time, cost today, and a temperature
  chart: room, target, outdoor and device setpoints, coloured bands showing which source was
  heating, and the planned target for the coming hours.
- **Costs** — heating cost today, yesterday, last 7/30 days, per day (30 days) and per month,
  split into air conditioner and boiler.
- **Learning** — cheapest source right now, learned heat-up rate and costs, coverage per
  outdoor temperature band and the full learned data table.
- **Settings** — mode, schedule, energy prices and a link to the advanced settings.

## Lovelace dashboard (optional)
[`dashboards/climator.yaml`](dashboards/climator.yaml) contains a ready-made dashboard with
three views: **Status**, **Costs** (cost per day and per month) and **Learning** (learned
rates, costs and a table per outdoor temperature). Create a new dashboard, open the
*Raw configuration editor* and paste the file.

## Learn only
Set the mode to **Learn only** (or turn `climate.climator` off). Climator then controls
nothing, but watches what the air conditioner and boiler do and learns from it. Run it like
this for a week, then switch to *Schedule + preheat*.

## Manual changes (remote, thermostat dial, app)
When you change the air conditioner or boiler yourself while Climator is in control, it
detects this after about 2 minutes and pauses (default 120 minutes, configurable; 0 = Climator
reverts your change). It keeps learning during the pause. Changing Climator's own mode or
temperature ends the pause immediately.

## How decisions are made
- **Heating up**: for each option (air conditioner, boiler, both) duration and cost are
  calculated from the learned °C/h and kWh or m³ per °C. The cheapest option that is ready in
  time wins; otherwise the fastest.
- **Keeping warm**: the source with the lowest cost per hour
  (consumption per hour per degree of indoor/outdoor difference × price).
- **Preheating** (schedule): start = comfort start − expected heat-up time − margin.
- The inactive air conditioner is switched off; the inactive boiler gets the setback
  temperature (default 15 °C).

## Notes
- **Plugwise Anna**: while Climator is in control it sets the Anna to *heat* (manual), which
  disables the Anna's own schedule. In *Learn only* mode nothing is changed.
- Learning uses measurement windows (heat-up 15–45 min, keeping warm 60 min). Until enough data
  exists, sensible defaults are used.
- DSMR4 meters report gas only once per hour; DSMR5 (every 5 minutes) gives better results.
- Gas costs count all gas except while hot water is active, so cooking gas is included.

## Releasing a new version
Bump `version` in `custom_components/hybrid_heating/manifest.json` and push to `main`.
The release workflow creates the GitHub release; HACS then offers the update.
