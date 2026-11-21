/* Climator sidebar panel — plain web component, no external dependencies. */

const E = {
  climate: "climate.climator",
  mode: "select.climator_mode",
  strategy: "sensor.climator_strategy",
  phase: "sensor.climator_phase",
  reason: "sensor.climator_reason",
  preheat: "sensor.climator_preheat_start",
  costToday: (w) => `sensor.climator_cost_today_${w}`,
  costTotal: (w) => `sensor.climator_cost_${w}`,
  maintain: (w) => `sensor.climator_maintain_cost_${w}`,
  expected: "sensor.climator_expected_cost_24h",
  comfort: "sensor.climator_comfort_score",
};

const COLORS = {
  room: "#42a5f5", target: "#ffa726", outdoor: "#9e9e9e", airco: "#26c6da", cv: "#ef5350",
  both: "#ab47bc", model: "#ffca28",
};
const STRATS = ["airco", "cv", "both"];
const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
const FEATURES = ["fan", "windows", "presence", "forecast", "buffer", "solar", "notifications", "suggestions"];

const I18N = {
  en: {
    tabs: { status: "Status", forecast: "Forecast", costs: "Costs", model: "Model", settings: "Settings" },
    modes: { learn_only: "Learn only", manual: "Fixed temperature", schedule: "Schedule + preheat" },
    strategy: { airco: "Air conditioner", cv: "Boiler", both: "Both", off: "Off" },
    phase: { heat_up: "Heating up", maintain: "Keeping warm", off: "Off", paused: "Paused" },
    reason: {
      off: "Off", sensor_unavailable: "Sensor unavailable", no_source: "No heat source available",
      comfort: "Comfort period", eco: "Eco period", preheat: "Preheating", manual: "Fixed temperature",
      learn_only: "Learn only", manual_override: "Paused after manual change", window_open: "Window open",
      away: "Away", vacation: "Vacation", buffer: "Buffering heat",
    },
    presence: { home: "Home", away: "Away", vacation: "Vacation" },
    banner: {
      learn: "Learn only — Climator watches and learns, but does not change the air conditioner or thermostat.",
      enable: "Turn on schedule",
      paused: (t, e) => `Paused until ${t} because ${e} was changed manually. Climator keeps learning.`,
      resume: "Resume now",
      window: (w) => `Heating paused: ${w} open.`,
      away: "Nobody home — away temperature is used.",
      vacation: "Vacation mode is on.", vacationOff: "Turn off vacation",
    },
    unavailable: "Climator entities not found. Is the integration set up?",
    room: "Room", outdoor: "Outdoor", target: "Target", now: "Now", strategyNow: "Heat source",
    preheatStart: "Preheat starts", nextComfort: "Next comfort", costToday: "Heating cost today",
    keepWarm: "Keep warm now", perHour: "/h", aircoSet: "Air conditioner setpoint", cvSet: "Boiler setpoint",
    temperature: "Temperature (°C)", past: "Past", ahead: "Ahead", expectedRoom: "Expected room", plan: "Planned target",
    outdoorFc: "Outdoor forecast", noHistory: "No history yet.", comfortScore: "Comfort score",
    today: "Today", week: "7 days", expected24: "Expected cost next 24 h", presenceLbl: "Presence",
    costPerDay: "Heating cost per day", costPerMonth: "Heating cost per month",
    yesterday: "Yesterday", last7: "Last 7 days", last30: "Last 30 days", thisMonth: "This month",
    noStats: "No statistics yet — they appear after the first full hour.",
    fitTitle: "How well does the model predict?",
    fitText: "Every 15 minutes Climator predicts the room temperature one hour ahead using what the heating did, and compares it with what really happened.",
    fitLabels: { good: "Good", ok: "Reasonable", bad: "Poor", none: "Not enough data yet" },
    fitValue: (v) => `On average ${v} °C off, one hour ahead`,
    bias: (v) => (v > 0 ? `Tends to predict ${v} °C too warm` : `Tends to predict ${Math.abs(v)} °C too cold`),
    replayTitle: "Reality vs model (last 48 h)", real: "Measured", modelLine: "Model",
    replayText: "The model restarts from the measured value every 3 hours. If the lines stay close, the model understands your room.",
    knowsTitle: "What Climator learned about your room",
    loss: "Heat loss", lossText: (v) => `With 10 °C difference to outside, the room cools ${v} °C per hour without heating.`,
    lossNight: (a, b, h) => `From ${a} °C it drops to about ${b} °C in ${h} hours at the current outdoor temperature.`,
    aircoK: "Air conditioner", aircoText: (g, t) => `1 kW of electricity adds ${g} °C per hour (at ${t} °C outside).`,
    cvK: "Boiler", cvText: (g) => `1 m³ of gas per hour adds ${g} °C per hour.`,
    solarK: "Sun", solarText: (g) => `1 kW of solar panel output adds ${g} °C per hour.`,
    solarOff: "Solar gain is off or no solar sensor is configured.",
    maxPower: (v, u) => `Learned maximum: ${v} ${u}`, costDeg: (v) => `Heating 1 °C costs ${v}`,
    conf: { none: "no data", low: "low", medium: "medium", high: "high" }, confidence: "confidence",
    samplesBasis: (n) => `based on ${n} samples`,
    breakevenTitle: "Which source is cheaper per outdoor temperature?",
    breakeven: (t) => `Below ${t} °C outside the boiler is cheaper per degree; above it the air conditioner.`,
    noBreakeven: (s) => `In the range −15…20 °C the ${s} is always cheaper.`,
    nowWord: "now",
    diagTitle: "Checks", dataTitle: "Data used", used: "Samples in model", excluded: "Skipped",
    lastSample: "Last sample",
    exReasons: { hot_water: "hot water", window: "window open", gap: "gap in data", meter_missing: "meter unavailable",
      meter_jump: "meter jump", temp_jump: "temperature jump", ok: "used" },
    suggTitle: "Suggestions", noSugg: "No suggestions. Climator looks for patterns after 7–14 days.",
    apply: "Apply", dismiss: "Dismiss",
    sugg: {
      frequent_overrides: (p) => `You changed the heating manually ${p.count} times in two weeks, often around ${p.hour}:00. Adjust the schedule around that time?`,
      low_comfort: (p) => `The room was warm enough only ${p.score}% of comfort time this week. Increase the preheat margin to ${p.margin} minutes?`,
      windows_often_open: (p) => `A window was open ${p.count} times in two weeks while heating. Ventilate briefly and close doors to save energy.`,
      model_inaccurate: (p) => `The model is on average ${p.mae} °C off. Check the room sensor location (not near the air conditioner, sun or radiator).`,
      breakeven: (p) => `Below ${p.temp} °C outside the boiler is cheaper than the air conditioner. Climator already uses this.`,
    },
    resetTitle: "Reset", resetConfirm: (s) => `Reset “${s}”? This cannot be undone.`,
    scopes: { model: "Thermal model", comfort: "Comfort score", costs: "Costs", suggestions: "Suggestions", weather: "Weather correction", all: "Everything" },
    diag: {
      entity_room_sensor: "Room temperature sensor", entity_outdoor_sensor: "Outdoor sensor",
      entity_airco_climate: "Air conditioner", entity_cv_climate: "Boiler thermostat",
      entity_airco_energy_sensor: "Air conditioner energy meter", entity_gas_sensor: "Gas meter",
      room_fresh: "Room sensor updates", airco_meter: "Air conditioner meter counts while heating",
      gas_meter: "Gas meter counts while heating", dhw_missing: "Hot water exclusion",
      model_bounds: "Model values plausible", model_accuracy: "Model accuracy", many_excluded: "Enough usable data",
      forecast: "Weather forecast", feature_windows_unconfigured: "Window detection",
      feature_presence_unconfigured: "Presence", feature_forecast_unconfigured: "Weather forecast",
      feature_solar_unconfigured: "Solar gain",
    },
    diagText: {
      entity: (st, p) => st === "ok" ? `${p.entity} OK` : st === "warn" ? `${p.entity} is unavailable` : `${p.entity || "Not set"} not found`,
      room_fresh: (st, p) => st === "ok" ? `Last update ${p.hours} h ago` : `No update for ${p.hours} hours — check the sensor`,
      airco_meter: (st, p) => st === "ok" ? `${p.kwh} kWh in ${p.minutes} min heating` : `Air conditioner should be heating for ${p.minutes} min but its energy meter did not move`,
      gas_meter: (st, p) => st === "ok" ? `${p.m3} m³ in ${p.minutes} min heating` : `Boiler should be heating for ${p.minutes} min but the gas meter did not move`,
      dhw_missing: () => "No hot-water sensor: shower gas can disturb learning and costs",
      model_bounds: (st, p) => `Values at their limit: ${p.params.join(", ")} — data may be unreliable`,
      model_accuracy: (st, p) => p.mae === undefined ? `Not enough data yet (${p.n} checks)` : `${p.mae} °C average error, bias ${p.bias} °C`,
      many_excluded: (st, p) => `Many samples skipped (${p.excluded}), mostly: ${p.reason}`,
      forecast: (st, p) => p.error !== undefined ? `No forecast received${p.error ? ": " + p.error : ""}` : `Received; correction vs your sensor ${p.bias} °C`,
      unconfigured: () => "Switched on, but no entity configured (see advanced settings)",
    },
    status: { ok: "OK", info: "Info", warn: "Check", error: "Error" },
    fc: {
      hypothetical: "Climator is in Learn only: this is what the schedule would do.",
      restToday: "Rest of today", tomorrow: "Tomorrow", next3: "Next 3 days", perWeek: "Per week (estimate)",
      shortfall: "Too cold (comfort)", shortfallSub: (h) => `${h} h below comfort in 3 days`,
      planTitle: "Plan for the next 3 days", costHourTitle: "Expected cost per hour", costDayTitle: "Expected cost per day",
      actionsTitle: "Upcoming actions", splitTitle: "Where does the money go?",
      heatUp: "Heating up", keepWarm: "Keeping warm",
      savingsTitle: "Where can you save?",
      savingsText: (w) => `Each line re-runs the 3-day forecast with one change. Current settings: about ${w} per week.`,
      perWeekShort: "per week", comfortEffect: "Comfort", noEffect: "no difference",
      colder: (h) => `${h} h/week too cold`, warmer: (h) => `${h} h/week less too cold`,
      scen: {
        comfort_minus_05: ["Comfort temperature 0.5 °C lower", "All schedule blocks half a degree cooler."],
        comfort_minus_1: ["Comfort temperature 1 °C lower", "All schedule blocks one degree cooler."],
        comfort_later_30: ["Comfort blocks start 30 min later", "Shorter comfort time, less preheating."],
        eco_minus_1: ["Eco temperature 1 °C lower", "Cooler at night / outside the schedule."],
        eco_plus_1: ["Eco temperature 1 °C higher", "Warmer at night: less heating up, more keeping warm."],
        manual_minus_05: ["Temperature 0.5 °C lower", "Fixed temperature half a degree cooler."],
        manual_minus_1: ["Temperature 1 °C lower", "Fixed temperature one degree cooler."],
        only_airco: ["Only the air conditioner", "Never use the boiler."],
        only_cv: ["Only the boiler", "Never use the air conditioner."],
        no_both: ["Never both at once", "No combined boost of air conditioner and boiler."],
        no_fan_control: ["Don't control the fan", "No hard blowing while heating up."],
      },
      act: {
        heat_up: (tg, s) => `Heat up to ${tg} °C with ${s}`,
        maintain: (tg, s) => `Keep at ${tg} °C with ${s}`,
        off: (te) => `Heating off — room cools to about ${te} °C`,
        coolThen: (tg, s) => `Let it cool to ${tg} °C, then keep it there with ${s}`,
        preheatFor: (t) => `for ${t}`, until: "until", now: "Now",
      },
      noForecast: "No forecast yet (needs room and outdoor temperature).",
    },
    fan: { boost: "blowing hard", comfort: "blowing softly" },
    fanTitle: "Air conditioner fan", fanText: "While heating up the fan blows hard; while keeping warm it blows softly (quiet).",
    fanBoost: "Fan while heating up", fanComfort: "Fan while keeping warm", fanAuto: "automatic choice",
    fanNone: "The air conditioner reports no fan modes.",
    fanCard: "Fan", fanGain: (p) => `Blowing hard gives ${p} heat per kWh than softly.`,
    fanRates: (b, c, u) => `Max heat-up: hard ${b} °C/${u} · soft ${c} °C/${u}`,
    mode: "Mode", functions: "Functions", functionsText: "Optional functions. Switch off what you don't want; Climator then simply ignores it.",
    feat: {
      fan: ["Fan speeds", "Blow hard while heating up, softly while keeping warm."],
      windows: ["Window detection", "Pause heating while a window or door is open."],
      presence: ["Presence", "Use the away temperature when nobody is home."],
      forecast: ["Weather forecast", "Use the hourly forecast for preheating and the 24-hour plan."],
      buffer: ["Heat buffer", "Store a little extra heat when the air conditioner is clearly cheaper now than later."],
      solar: ["Solar gain", "Learn how much the sun warms the room (via solar panel power)."],
      notifications: ["Notifications", "Notify when a sensor or device is unavailable."],
      suggestions: ["Suggestions", "Suggest improvements after 1–2 weeks of data."],
    },
    active: "active", notConfigured: "not configured", off: "off",
    schedule: "Schedule", workday: "Workday", weekend: "Weekend", weekendOn: "Use a separate weekend schedule",
    days: { mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun" },
    from: "From", until: "Until", addBlock: "Add block", save: "Save schedule",
    unsaved: "Unsaved changes", ecoTemp: "Temperature outside the schedule",
    presenceTitle: "Presence & vacation", awayTemp: "Away temperature", vacTemp: "Vacation temperature",
    vacation: "Vacation", guest: "Guests (ignore away)", prices: "Energy prices", electricity: "Electricity", gas: "Gas",
    pricesHint: "All decisions and costs use these prices.",
    advanced: "Advanced settings (entities, offsets, delays)", open: "Open",
  },
  nl: {
    tabs: { status: "Status", forecast: "Vooruitblik", costs: "Kosten", model: "Model", settings: "Instellingen" },
    modes: { learn_only: "Alleen leren", manual: "Vaste temperatuur", schedule: "Schema + voorverwarmen" },
    strategy: { airco: "Airco", cv: "CV", both: "Beide", off: "Uit" },
    phase: { heat_up: "Opwarmen", maintain: "Op temperatuur houden", off: "Uit", paused: "Gepauzeerd" },
    reason: {
      off: "Uit", sensor_unavailable: "Sensor onbeschikbaar", no_source: "Geen warmtebron beschikbaar",
      comfort: "Comfortperiode", eco: "Ecoperiode", preheat: "Voorverwarmen", manual: "Vaste temperatuur",
      learn_only: "Alleen leren", manual_override: "Gepauzeerd na handmatige bediening", window_open: "Raam open",
      away: "Afwezig", vacation: "Vakantie", buffer: "Warmte bufferen",
    },
    presence: { home: "Thuis", away: "Afwezig", vacation: "Vakantie" },
    banner: {
      learn: "Alleen leren — Climator kijkt mee en leert, maar wijzigt de airco en thermostaat niet.",
      enable: "Schema inschakelen",
      paused: (t, e) => `Gepauzeerd tot ${t} omdat ${e} handmatig is bediend. Climator blijft leren.`,
      resume: "Nu hervatten",
      window: (w) => `Verwarming gepauzeerd: ${w} open.`,
      away: "Niemand thuis — de afwezig-temperatuur wordt gebruikt.",
      vacation: "Vakantiestand staat aan.", vacationOff: "Vakantie uitzetten",
    },
    unavailable: "Climator-entiteiten niet gevonden. Is de integratie ingesteld?",
    room: "Kamer", outdoor: "Buiten", target: "Doel", now: "Nu", strategyNow: "Warmtebron",
    preheatStart: "Voorverwarmen start", nextComfort: "Volgende comfort", costToday: "Stookkosten vandaag",
    keepWarm: "Warm houden nu", perHour: "/u", aircoSet: "Setpoint airco", cvSet: "Setpoint CV",
    temperature: "Temperatuur (°C)", past: "Verleden", ahead: "Vooruit", expectedRoom: "Verwachte kamer", plan: "Gepland doel",
    outdoorFc: "Verwachting buiten", noHistory: "Nog geen geschiedenis.", comfortScore: "Comfortscore",
    today: "Vandaag", week: "7 dagen", expected24: "Verwachte kosten komende 24 u", presenceLbl: "Aanwezigheid",
    costPerDay: "Stookkosten per dag", costPerMonth: "Stookkosten per maand",
    yesterday: "Gisteren", last7: "Laatste 7 dagen", last30: "Laatste 30 dagen", thisMonth: "Deze maand",
    noStats: "Nog geen statistieken — die verschijnen na het eerste volle uur.",
    fitTitle: "Hoe goed voorspelt het model?",
    fitText: "Elk kwartier voorspelt Climator de kamertemperatuur een uur vooruit op basis van wat de verwarming deed, en vergelijkt dat met wat er echt gebeurde.",
    fitLabels: { good: "Goed", ok: "Redelijk", bad: "Slecht", none: "Nog te weinig data" },
    fitValue: (v) => `Gemiddeld ${v} °C ernaast, een uur vooruit`,
    bias: (v) => (v > 0 ? `Voorspelt gemiddeld ${v} °C te warm` : `Voorspelt gemiddeld ${Math.abs(v)} °C te koud`),
    replayTitle: "Werkelijkheid vs model (laatste 48 u)", real: "Gemeten", modelLine: "Model",
    replayText: "Het model start elke 3 uur opnieuw vanaf de gemeten waarde. Blijven de lijnen dicht bij elkaar, dan begrijpt het model je kamer.",
    knowsTitle: "Wat Climator over je kamer heeft geleerd",
    loss: "Warmteverlies", lossText: (v) => `Bij 10 °C verschil met buiten koelt de kamer ${v} °C per uur af zonder verwarming.`,
    lossNight: (a, b, h) => `Van ${a} °C zakt hij in ${h} uur naar ongeveer ${b} °C bij de huidige buitentemperatuur.`,
    aircoK: "Airco", aircoText: (g, t) => `1 kW stroom geeft +${g} °C per uur (bij ${t} °C buiten).`,
    cvK: "CV", cvText: (g) => `1 m³ gas per uur geeft +${g} °C per uur.`,
    solarK: "Zon", solarText: (g) => `1 kW vermogen van de zonnepanelen geeft +${g} °C per uur.`,
    solarOff: "Zonnewinst staat uit of er is geen zonnepanelen-sensor ingesteld.",
    maxPower: (v, u) => `Geleerd maximum: ${v} ${u}`, costDeg: (v) => `1 °C opwarmen kost ${v}`,
    conf: { none: "geen data", low: "laag", medium: "middel", high: "hoog" }, confidence: "betrouwbaarheid",
    samplesBasis: (n) => `op basis van ${n} metingen`,
    breakevenTitle: "Welke bron is goedkoper per buitentemperatuur?",
    breakeven: (t) => `Onder ${t} °C buiten is de CV goedkoper per graad, daarboven de airco.`,
    noBreakeven: (s) => `Tussen −15 en 20 °C is de ${s} altijd goedkoper.`,
    nowWord: "nu",
    diagTitle: "Controles", dataTitle: "Gebruikte data", used: "Metingen in model", excluded: "Overgeslagen",
    lastSample: "Laatste meting",
    exReasons: { hot_water: "tapwater", window: "raam open", gap: "gat in data", meter_missing: "meter onbeschikbaar",
      meter_jump: "sprong in meter", temp_jump: "sprong in temperatuur", ok: "gebruikt" },
    suggTitle: "Suggesties", noSugg: "Geen suggesties. Climator zoekt na 7–14 dagen naar patronen.",
    apply: "Toepassen", dismiss: "Negeren",
    sugg: {
      frequent_overrides: (p) => `Je hebt de verwarming in twee weken ${p.count} keer handmatig aangepast, vaak rond ${p.hour}:00. Schema rond die tijd aanpassen?`,
      low_comfort: (p) => `De kamer was deze week maar ${p.score}% van de comforttijd warm genoeg. Voorverwarmmarge verhogen naar ${p.margin} minuten?`,
      windows_often_open: (p) => `Er stond in twee weken ${p.count} keer een raam open tijdens het stoken. Kort luchten en deuren dicht bespaart energie.`,
      model_inaccurate: (p) => `Het model zit gemiddeld ${p.mae} °C ernaast. Controleer de plek van de kamersensor (niet bij de airco, zon of radiator).`,
      breakeven: (p) => `Onder ${p.temp} °C buiten is de CV goedkoper dan de airco. Climator houdt hier al rekening mee.`,
    },
    resetTitle: "Wissen", resetConfirm: (s) => `„${s}” wissen? Dit kan niet ongedaan worden.`,
    scopes: { model: "Thermisch model", comfort: "Comfortscore", costs: "Kosten", suggestions: "Suggesties", weather: "Weercorrectie", all: "Alles" },
    diag: {
      entity_room_sensor: "Kamertemperatuursensor", entity_outdoor_sensor: "Buitensensor",
      entity_airco_climate: "Airco", entity_cv_climate: "CV-thermostaat",
      entity_airco_energy_sensor: "Energiemeter airco", entity_gas_sensor: "Gasmeter",
      room_fresh: "Kamersensor werkt bij", airco_meter: "Airco-meter telt tijdens stoken",
      gas_meter: "Gasmeter telt tijdens stoken", dhw_missing: "Tapwater uitsluiten",
      model_bounds: "Modelwaarden aannemelijk", model_accuracy: "Nauwkeurigheid model", many_excluded: "Genoeg bruikbare data",
      forecast: "Weersverwachting", feature_windows_unconfigured: "Raamdetectie",
      feature_presence_unconfigured: "Aanwezigheid", feature_forecast_unconfigured: "Weersverwachting",
      feature_solar_unconfigured: "Zonnewinst",
    },
    diagText: {
      entity: (st, p) => st === "ok" ? `${p.entity} OK` : st === "warn" ? `${p.entity} is onbeschikbaar` : `${p.entity || "Niet ingesteld"} niet gevonden`,
      room_fresh: (st, p) => st === "ok" ? `Laatste update ${p.hours} u geleden` : `Al ${p.hours} uur geen update — controleer de sensor`,
      airco_meter: (st, p) => st === "ok" ? `${p.kwh} kWh in ${p.minutes} min stoken` : `Airco hoort al ${p.minutes} min te stoken maar de energiemeter loopt niet`,
      gas_meter: (st, p) => st === "ok" ? `${p.m3} m³ in ${p.minutes} min stoken` : `CV hoort al ${p.minutes} min te stoken maar de gasmeter loopt niet`,
      dhw_missing: () => "Geen tapwatersensor: gas van de douche kan het leren en de kosten verstoren",
      model_bounds: (st, p) => `Waarden op hun grens: ${p.params.join(", ")} — data is mogelijk onbetrouwbaar`,
      model_accuracy: (st, p) => p.mae === undefined ? `Nog te weinig data (${p.n} controles)` : `${p.mae} °C gemiddelde fout, afwijking ${p.bias} °C`,
      many_excluded: (st, p) => `Veel metingen overgeslagen (${p.excluded}), vooral: ${p.reason}`,
      forecast: (st, p) => p.error !== undefined ? `Geen verwachting ontvangen${p.error ? ": " + p.error : ""}` : `Ontvangen; correctie t.o.v. je sensor ${p.bias} °C`,
      unconfigured: () => "Aangezet, maar geen entiteit ingesteld (zie geavanceerde instellingen)",
    },
    status: { ok: "OK", info: "Info", warn: "Controleer", error: "Fout" },
    fc: {
      hypothetical: "Climator staat op Alleen leren: dit is wat het schema zou doen.",
      restToday: "Rest van vandaag", tomorrow: "Morgen", next3: "Komende 3 dagen", perWeek: "Per week (schatting)",
      shortfall: "Te koud (comfort)", shortfallSub: (h) => `${h} u onder comfort in 3 dagen`,
      planTitle: "Planning komende 3 dagen", costHourTitle: "Verwachte kosten per uur", costDayTitle: "Verwachte kosten per dag",
      actionsTitle: "Komende acties", splitTitle: "Waar gaat het geld naartoe?",
      heatUp: "Opwarmen", keepWarm: "Warm houden",
      savingsTitle: "Waar kun je besparen?",
      savingsText: (w) => `Elke regel rekent de 3-daagse verwachting opnieuw door met één wijziging. Huidige instellingen: ongeveer ${w} per week.`,
      perWeekShort: "per week", comfortEffect: "Comfort", noEffect: "geen verschil",
      colder: (h) => `${h} u/week te koud`, warmer: (h) => `${h} u/week minder te koud`,
      scen: {
        comfort_minus_05: ["Comforttemperatuur 0,5 °C lager", "Alle schemablokken een halve graad koeler."],
        comfort_minus_1: ["Comforttemperatuur 1 °C lager", "Alle schemablokken een graad koeler."],
        comfort_later_30: ["Comfortblokken 30 min later starten", "Kortere comforttijd, minder voorverwarmen."],
        eco_minus_1: ["Eco-temperatuur 1 °C lager", "Koeler 's nachts / buiten het schema."],
        eco_plus_1: ["Eco-temperatuur 1 °C hoger", "Warmer 's nachts: minder opwarmen, meer warm houden."],
        manual_minus_05: ["Temperatuur 0,5 °C lager", "Vaste temperatuur een halve graad koeler."],
        manual_minus_1: ["Temperatuur 1 °C lager", "Vaste temperatuur een graad koeler."],
        only_airco: ["Alleen de airco", "De CV nooit gebruiken."],
        only_cv: ["Alleen de CV", "De airco nooit gebruiken."],
        no_both: ["Nooit beide tegelijk", "Geen gecombineerde boost van airco en CV."],
        no_fan_control: ["Ventilator niet aansturen", "Niet hard blazen bij het opwarmen."],
      },
      act: {
        heat_up: (tg, s) => `Opwarmen naar ${tg} °C met ${s}`,
        maintain: (tg, s) => `Op ${tg} °C houden met ${s}`,
        off: (te) => `Verwarming uit — kamer koelt af naar ongeveer ${te} °C`,
        coolThen: (tg, s) => `Laten afkoelen naar ${tg} °C, daarna vasthouden met ${s}`,
        preheatFor: (t) => `voor ${t}`, until: "tot", now: "Nu",
      },
      noForecast: "Nog geen verwachting (heeft kamer- en buitentemperatuur nodig).",
    },
    fan: { boost: "hard blazen", comfort: "zacht blazen" },
    fanTitle: "Ventilator airco", fanText: "Bij opwarmen blaast de airco hard; bij warm houden zacht (stil).",
    fanBoost: "Ventilator bij opwarmen", fanComfort: "Ventilator bij warm houden", fanAuto: "automatisch kiezen",
    fanNone: "De airco meldt geen ventilatorstanden.",
    fanCard: "Ventilator", fanGain: (p) => `Hard blazen geeft ${p} warmte per kWh dan zacht.`,
    fanRates: (b, c, u) => `Max opwarmen: hard ${b} °C/${u} · zacht ${c} °C/${u}`,
    mode: "Modus", functions: "Functies", functionsText: "Optionele functies. Zet uit wat je niet wilt; Climator negeert het dan gewoon.",
    feat: {
      fan: ["Ventilatorstanden", "Hard blazen bij opwarmen, zacht blazen bij warm houden."],
      windows: ["Raamdetectie", "Verwarming pauzeren als een raam of deur open staat."],
      presence: ["Aanwezigheid", "Afwezig-temperatuur gebruiken als niemand thuis is."],
      forecast: ["Weersverwachting", "De uurverwachting gebruiken voor voorverwarmen en de 24-uursplanning."],
      buffer: ["Warmtebuffer", "Een beetje extra warmte opslaan als de airco nu duidelijk goedkoper is dan straks."],
      solar: ["Zonnewinst", "Leren hoeveel de zon de kamer opwarmt (via het vermogen van de zonnepanelen)."],
      notifications: ["Meldingen", "Een melding als een sensor of apparaat onbeschikbaar is."],
      suggestions: ["Suggesties", "Na 1–2 weken data verbeteringen voorstellen."],
    },
    active: "actief", notConfigured: "niet ingesteld", off: "uit",
    schedule: "Schema", workday: "Werkdag", weekend: "Weekend", weekendOn: "Apart weekendschema gebruiken",
    days: { mon: "Ma", tue: "Di", wed: "Wo", thu: "Do", fri: "Vr", sat: "Za", sun: "Zo" },
    from: "Van", until: "Tot", addBlock: "Blok toevoegen", save: "Schema opslaan",
    unsaved: "Niet-opgeslagen wijzigingen", ecoTemp: "Temperatuur buiten het schema",
    presenceTitle: "Aanwezigheid & vakantie", awayTemp: "Afwezig-temperatuur", vacTemp: "Vakantietemperatuur",
    vacation: "Vakantie", guest: "Gasten (afwezigheid negeren)", prices: "Energieprijzen", electricity: "Stroom", gas: "Gas",
    pricesHint: "Alle beslissingen en kosten gebruiken deze prijzen.",
    advanced: "Geavanceerde instellingen (entiteiten, offsets, vertragingen)", open: "Openen",
  },
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

class ClimatorPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = "status";
    this._past = 24;
    this._ahead = 24;
    this._history = null;
    this._stats = null;
    this._info = null;
    this._draft = null;
    this._lastSig = "";
    this._hidden = new Set();
  }

  set narrow(v) { this._narrow = v; if (this._menu) this._menu.narrow = v; }
  set panel(v) { this._panel = v; }
  set route(v) { this._route = v; }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (this._menu) this._menu.hass = hass;
    if (first) {
      this._setup();
      this._loadInfo();
      this._loadHistory();
      this._timers = [
        setInterval(() => this._loadInfo(), 60 * 1000),
        setInterval(() => { this._loadHistory(); if (this._tab === "costs") this._loadStats(); }, 5 * 60 * 1000),
      ];
    }
    const sig = this._signature();
    if (sig !== this._lastSig) {
      this._lastSig = sig;
      this._render();
    }
  }

  disconnectedCallback() {
    (this._timers || []).forEach(clearInterval);
    this._ro?.disconnect();
  }

  get lang() { return this._hass?.locale?.language || this._hass?.language || "en"; }
  get t() { return I18N[this.lang.slice(0, 2)] || I18N.en; }
  get _hUnit() { return this.lang.startsWith("nl") ? "u" : "h"; }

  _st(id) { return this._hass?.states[id]; }
  _num(id) { const s = this._st(id); const v = s ? parseFloat(s.state) : NaN; return Number.isFinite(v) ? v : null; }

  _signature() {
    const ids = [E.climate, E.mode, E.strategy, E.phase, E.reason, E.preheat, E.expected, E.comfort];
    ["airco", "cv", "total"].forEach((w) => ids.push(E.costToday(w)));
    ["airco", "cv"].forEach((w) => ids.push(E.maintain(w)));
    const src = this._st(E.climate)?.attributes?.source_entities || {};
    Object.values(src).forEach((i) => i && ids.push(i));
    return ids.map((i) => this._st(i)?.last_updated || "-").join("|");
  }

  // ---------------------------------------------------------------- formatting
  _fmt(v, d = 1) {
    if (v === null || v === undefined || Number.isNaN(v) || !Number.isFinite(+v)) return "–";
    return new Intl.NumberFormat(this.lang, { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
  }
  _eur(v, d = 2) {
    if (v === null || v === undefined || !Number.isFinite(+v)) return "–";
    return new Intl.NumberFormat(this.lang, { style: "currency", currency: "EUR", minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
  }
  _time(d) { return d.toLocaleTimeString(this.lang, { hour: "2-digit", minute: "2-digit" }); }
  _when(d) {
    const today = new Date().toDateString() === d.toDateString();
    return today ? this._time(d) : `${d.toLocaleDateString(this.lang, { weekday: "short" })} ${this._time(d)}`;
  }

  // ---------------------------------------------------------------- data
  async _ws(msg) { return this._hass.callWS(msg); }

  async _loadInfo() {
    try {
      this._info = await this._ws({ type: "hybrid_heating/info" });
      this._infoError = null;
    } catch (err) {
      this._infoError = err?.message || String(err);
    }
    this._render(this._tab === "settings" && !this._draft);
  }

  async _update(payload) {
    try {
      this._info = await this._ws({ type: "hybrid_heating/update", ...payload });
      this._toast = null;
    } catch (err) {
      this._toast = err?.message || String(err);
    }
    this._render(true);
  }

  async _loadHistory() {
    if (!this._hass) return;
    const src = this._st(E.climate)?.attributes?.source_entities || {};
    const ids = [E.climate, E.strategy, src.room, src.outdoor, src.airco, src.cv].filter(Boolean);
    const start = new Date(Date.now() - this._past * 3600 * 1000);
    try {
      const res = await this._ws({
        type: "history/history_during_period", start_time: start.toISOString(), entity_ids: ids,
        minimal_response: false, no_attributes: false, significant_changes_only: false,
      });
      this._history = { res, src, start };
    } catch (err) {
      console.warn("Climator: history failed", err);
      this._history = { res: {}, src, start };
    }
    if (this._tab === "status") this._drawChart();
  }

  async _loadStats() {
    const now = new Date();
    const dayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 29);
    const monthStart = new Date(now.getFullYear(), now.getMonth() - 11, 1);
    const ids = [E.costTotal("airco"), E.costTotal("cv")];
    try {
      const [day, month] = await Promise.all([
        this._ws({ type: "recorder/statistics_during_period", start_time: dayStart.toISOString(), statistic_ids: ids, period: "day", types: ["change"] }),
        this._ws({ type: "recorder/statistics_during_period", start_time: monthStart.toISOString(), statistic_ids: ids, period: "month", types: ["change"] }),
      ]);
      this._stats = { day, month };
    } catch (err) {
      console.warn("Climator: statistics failed", err);
      this._stats = { day: {}, month: {} };
    }
    if (this._tab === "costs") this._render(true);
  }

  // ---------------------------------------------------------------- layout
  _setup() {
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <div class="toolbar">
        <span class="menu"></span>
        <div class="title">Climator</div>
        <nav class="tabs"></nav>
        <div class="status"></div>
      </div>
      <main class="content"></main>`;
    this._menu = document.createElement("ha-menu-button");
    this._menu.hass = this._hass;
    this._menu.narrow = this._narrow;
    this.shadowRoot.querySelector(".menu").appendChild(this._menu);
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this.shadowRoot.addEventListener("change", (ev) => this._onChange(ev));
    this._ro = new ResizeObserver(() => {
      if (this._tab === "status") this._drawChart();
      if (this._tab === "model") this._drawModelCharts();
      if (this._tab === "forecast") this._drawForecastCharts();
    });
  }

  _render(force = false) {
    const content = this.shadowRoot.querySelector(".content");
    if (!content) return;
    const t = this.t;
    this.shadowRoot.querySelector(".tabs").innerHTML = Object.entries(t.tabs).map(
      ([k, v]) => `<button class="tab ${k === this._tab ? "active" : ""}" data-tab="${k}">${v}</button>`).join("");
    const mode = this._st(E.mode)?.state;
    const reason = this._st(E.reason)?.state;
    const ok = !!this._st(E.climate) && this._st(E.climate).state !== "unavailable";
    const warn = (this._info?.diagnostics || []).some((d) => d.status === "warn" || d.status === "error");
    this.shadowRoot.querySelector(".status").innerHTML = ok
      ? `<span class="dot ${reason === "manual_override" || warn ? "warn" : "ok"}"></span>${esc(t.modes[mode] || mode || "")}${this._info ? ` · v${esc(this._info.version)}` : ""}`
      : `<span class="dot err"></span>`;
    // never wipe a form the user is editing
    if (!force && this._tab === "settings") return;
    if (!ok) { content.innerHTML = `<div class="banner err">${t.unavailable}</div>`; return; }
    const fn = { status: this._status, forecast: this._forecast, costs: this._costs, model: this._model, settings: this._settings }[this._tab];
    const scroll = window.scrollY;
    content.innerHTML = (this._toast ? `<div class="banner err">${esc(this._toast)}</div>` : "") + fn.call(this);
    this._ro.disconnect();
    content.querySelectorAll(".chart").forEach((el) => this._ro.observe(el));
    if (this._tab === "status") this._drawChart();
    if (this._tab === "model") this._drawModelCharts();
    if (this._tab === "forecast") this._drawForecastCharts();
    window.scrollTo(0, scroll);
  }

  _banners() {
    const t = this.t;
    const mode = this._st(E.mode)?.state;
    const reason = this._st(E.reason)?.state;
    const info = this._info || {};
    const out = [];
    if (mode === "learn_only") {
      out.push(`<div class="banner warn"><div>${esc(t.banner.learn)}</div><button class="btn" data-action="mode" data-value="schedule">${t.banner.enable}</button></div>`);
    }
    if (reason === "manual_override") {
      const a = this._st(E.climate).attributes;
      const until = a.override_until ? this._time(new Date(a.override_until)) : "?";
      const ent = this._st(a.override_entity)?.attributes?.friendly_name || a.override_entity || "?";
      out.push(`<div class="banner warn"><div>${esc(t.banner.paused(until, ent))}</div><button class="btn" data-action="mode" data-value="${esc(mode)}">${t.banner.resume}</button></div>`);
    }
    if (info.window_open || reason === "window_open") {
      const names = (info.open_windows || []).map((e) => this._st(e)?.attributes?.friendly_name || e).join(", ");
      out.push(`<div class="banner warn"><div>${esc(t.banner.window(names || "?"))}</div></div>`);
    }
    if (info.presence === "vacation") {
      out.push(`<div class="banner"><div>${t.banner.vacation}</div><button class="btn" data-action="setting" data-key="vacation" data-value="false">${t.banner.vacationOff}</button></div>`);
    } else if (info.presence === "away" && mode !== "learn_only") {
      out.push(`<div class="banner"><div>${t.banner.away}</div></div>`);
    }
    return out.join("");
  }

  _card(label, value, sub = "", cls = "") {
    return `<div class="card stat ${cls}"><div class="label">${label}</div><div class="value">${value}</div>${sub ? `<div class="sub">${sub}</div>` : ""}</div>`;
  }

  _chip(s) { return `<span class="chip ${esc(s)}">${esc(this.t.strategy[s] || s)}</span>`; }

  // ---------------------------------------------------------------- status tab
  _status() {
    const t = this.t;
    const a = this._st(E.climate).attributes;
    const src = a.source_entities || {};
    const info = this._info || {};
    const strategy = this._st(E.strategy)?.state || "off";
    const phase = this._st(E.phase)?.state || "off";
    const reason = this._st(E.reason)?.state || "off";
    const pre = this._st(E.preheat)?.state;
    const preDate = pre && !["unknown", "unavailable"].includes(pre) ? new Date(pre) : null;
    const keepA = this._num(E.maintain("airco"));
    const keepC = this._num(E.maintain("cv"));
    const finite = [keepA, keepC].filter((v) => v !== null && Number.isFinite(v));
    const airco = this._st(src.airco);
    const cv = this._st(src.cv);
    const fmtState = (s) => (this._hass.formatEntityState ? this._hass.formatEntityState(s) : s.state);
    const devSub = (s) => s ? `${esc(fmtState(s))} · ${this._fmt(s.attributes.temperature)} °C` : "–";
    const comfort = info.comfort || {};
    const next = this._nextBlock();

    return `${this._banners()}
      <div class="grid">
        ${this._card(t.room, `${this._fmt(a.current_temperature)} °C`, `${t.target} ${this._fmt(a.temperature)} °C`)}
        ${this._card(t.outdoor, `${this._fmt(a.outdoor_temperature)} °C`)}
        ${this._card(t.strategyNow, this._chip(strategy), `${t.phase[phase] || phase} · ${t.reason[reason] || reason}`)}
        ${this._card(preDate ? t.preheatStart : t.nextComfort, preDate ? this._when(preDate) : (next ? this._when(next.start) : "–"), next ? `${t.nextComfort} ${this._when(next.start)} · ${this._fmt(next.temp)} °C` : "")}
        ${this._card(t.costToday, this._eur(this._num(E.costToday("total"))), `${t.strategy.airco} ${this._eur(this._num(E.costToday("airco")))} · ${t.strategy.cv} ${this._eur(this._num(E.costToday("cv")))}`)}
        ${this._card(t.expected24, this._eur(this._fcCost(24)), "")}
        ${this._card(t.keepWarm, finite.length ? `${this._eur(Math.min(...finite), 3)}${t.perHour}` : "–", `${t.strategy.airco} ${this._eur(keepA, 3)} · ${t.strategy.cv} ${this._eur(keepC, 3)}`)}
        ${this._card(t.comfortScore, comfort.today != null ? `${this._fmt(comfort.today, 0)}%` : "–", `${t.week}: ${comfort.week != null ? this._fmt(comfort.week, 0) + "%" : "–"}`)}
        ${this._card(t.presenceLbl, esc(t.presence[info.presence] || "–"), "")}
        ${this._card(t.strategy.airco, `${this._fmt(airco?.attributes?.current_temperature)} °C`, devSub(airco))}
        ${this._card(t.strategy.cv, `${this._fmt(cv?.attributes?.current_temperature)} °C`, devSub(cv))}
      </div>
      <div class="card">
        <div class="card-head">
          <h2>${t.temperature}</h2>
          <div class="ranges">
            <span class="muted">${t.past}</span>
            ${[6, 12, 24, 72, 168].map((h) => `<button class="pill ${h === this._past ? "on" : ""}" data-action="past" data-value="${h}">${h < 48 ? h + this._hUnit : h / 24 + "d"}</button>`).join("")}
            <span class="muted">${t.ahead}</span>
            ${[0, 12, 24, 48, 72].map((h) => `<button class="pill ${h === this._ahead ? "on" : ""}" data-action="ahead" data-value="${h}">${h ? h + this._hUnit : "–"}</button>`).join("")}
          </div>
        </div>
        <div class="legend">${this._legend()}</div>
        <div class="chart" data-chart="main"></div>
      </div>`;
  }

  _nextBlock() {
    const s = this._info?.schedule;
    if (!s) return null;
    const now = new Date();
    let best = null;
    for (let i = 0; i < 3; i++) {
      const day = new Date(now); day.setDate(day.getDate() + i);
      let prof = s.days[DAYS[(day.getDay() + 6) % 7]];
      if (prof === "weekend" && !s.weekend_enabled) prof = "workday";
      for (const b of s.profiles[prof] || []) {
        if (!b.enabled) continue;
        const [h, m] = b.start.split(":").map(Number);
        const st = new Date(day); st.setHours(h, m, 0, 0);
        if (st > now && (!best || st < best.start)) best = { start: st, temp: b.temp };
      }
    }
    return best;
  }

  _legend() {
    const t = this.t;
    const items = [
      ["room", t.room, COLORS.room], ["expected", t.expectedRoom, COLORS.room, true], ["target", t.target, COLORS.target],
      ["outdoor", t.outdoor, COLORS.outdoor], ["aircoSet", t.aircoSet, COLORS.airco, true], ["cvSet", t.cvSet, COLORS.cv, true],
    ];
    const bands = STRATS.map((s) => `<span class="band-key"><i style="background:${COLORS[s]}"></i>${t.strategy[s]}</span>`).join("");
    return items.map(([k, label, col, dash]) => `<button class="lg ${this._hidden.has(k) ? "off" : ""}" data-action="toggle" data-value="${k}"><i class="${dash ? "dash" : ""}" style="--c:${col}"></i>${label}</button>`).join("") + `<span class="sep"></span>${bands}`;
  }

  _series() {
    const h = this._history;
    if (!h) return null;
    const { res, src } = h;
    const ts = (e) => (e.lu ?? e.lc ?? 0) * 1000;
    const num = (id) => (res[id] || []).map((e) => [ts(e), e.s === undefined || e.s === null ? null : parseFloat(e.s)])
      .map(([x, v]) => [x, Number.isFinite(v) ? v : null]);
    const attrSeries = (id, attr, onlyWhen) => {
      let last = null;
      return (res[id] || []).map((e) => {
        if (e.a && attr in e.a) last = e.a[attr];
        const v = onlyWhen && !onlyWhen(e.s) ? null : last;
        return [ts(e), v === null || v === undefined ? null : parseFloat(v)];
      });
    };
    return {
      room: num(src.room), outdoor: num(src.outdoor),
      target: attrSeries(E.climate, "temperature"),
      aircoSet: attrSeries(src.airco, "temperature", (s) => ["heat", "heat_cool", "auto"].includes(s)),
      cvSet: attrSeries(src.cv, "temperature", (s) => s && s !== "off"),
      strategy: (res[E.strategy] || []).map((e) => [ts(e), e.s]),
    };
  }

  _svgChart(box, cfg) {
    const W = Math.max(box.clientWidth, 300);
    const H = cfg.height || 300;
    const m = { l: cfg.yFmt ? 54 : 40, r: cfg.right?.length ? 44 : 14, t: 18, b: 28 };
    const { x0, x1 } = cfg;
    const vals = (arr) => arr.flatMap((s) => s.pts.filter(([x, v]) => v !== null && x >= x0 - 3600e3 && x <= x1).map(([, v]) => v));
    const range = (vs, pad, min) => {
      if (!vs.length) return [0, min];
      let a = Math.floor(Math.min(...vs) - pad), b = Math.ceil(Math.max(...vs) + pad);
      if (b - a < min) b = a + min;
      return [a, b];
    };
    const [y0, y1] = cfg.yRange || range(vals(cfg.left), 0.5, 4);
    const [o0, o1] = range(vals(cfg.right || []), 1, 4);
    const X = (x) => m.l + ((x - x0) / (x1 - x0)) * (W - m.l - m.r);
    const Y = (v) => m.t + (1 - (v - y0) / (y1 - y0)) * (H - m.t - m.b);
    const YO = (v) => m.t + (1 - (v - o0) / (o1 - o0)) * (H - m.t - m.b);
    const clip = (pts) => {
      const before = pts.filter(([x]) => x < x0);
      const after = pts.filter(([x]) => x >= x0 && x <= x1 + 1);
      return before.length ? [[x0, before[before.length - 1][1]], ...after] : after;
    };
    const path = (pts, yf, step) => {
      let d = "", prev = false;
      for (const [x, v] of clip(pts)) {
        if (v === null || v === undefined) { prev = false; continue; }
        const px = X(x).toFixed(1), py = yf(v).toFixed(1);
        d += prev ? (step ? `H${px}V${py}` : `L${px},${py}`) : `M${px},${py}`;
        prev = true;
      }
      return d;
    };
    let g = "";
    const ystep = cfg.yStep || (y1 - y0 > 12 ? 2 : 1);
    for (let v = y0; v <= y1 + 1e-9; v += ystep) {
      g += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" class="gl"/><text x="${m.l - 6}" y="${Y(v) + 4}" class="ax" text-anchor="end">${cfg.yFmt ? cfg.yFmt(v) : v + "°"}</text>`;
    }
    if (cfg.right?.length) {
      const st = o1 - o0 > 12 ? 4 : 2;
      for (let v = Math.ceil(o0 / st) * st; v <= o1; v += st) g += `<text x="${W - m.r + 6}" y="${YO(v) + 4}" class="ax out">${v}°</text>`;
    }
    if (cfg.xNumeric) {
      for (let x = Math.ceil(x0 / 5) * 5; x <= x1; x += 5) g += `<line x1="${X(x)}" x2="${X(x)}" y1="${m.t}" y2="${H - m.b}" class="gl v"/><text x="${X(x)}" y="${H - 8}" class="ax" text-anchor="middle">${x}°</text>`;
    } else {
      const span = x1 - x0;
      const stepH = span > 96 * 3600e3 ? 24 : span > 36 * 3600e3 ? 6 : span > 14 * 3600e3 ? 3 : 1;
      const first = new Date(x0); first.setMinutes(0, 0, 0);
      for (let x = first.getTime(); x <= x1; x += 3600e3) {
        const d = new Date(x);
        if (d.getHours() % stepH !== 0 || x < x0) continue;
        const label = stepH === 24 ? d.toLocaleDateString(this.lang, { weekday: "short", day: "numeric" }) : this._time(d);
        g += `<line x1="${X(x)}" x2="${X(x)}" y1="${m.t}" y2="${H - m.b}" class="gl v"/><text x="${X(x)}" y="${H - 8}" class="ax" text-anchor="middle">${label}</text>`;
      }
    }
    let bands = "";
    for (const b of cfg.bands || []) {
      if (b.x1 <= x0 || b.x0 >= x1) continue;
      const a = Math.max(b.x0, x0), z = Math.min(b.x1, x1);
      bands += `<rect x="${X(a).toFixed(1)}" y="${m.t}" width="${Math.max(X(z) - X(a), 0).toFixed(1)}" height="${H - m.t - m.b}" fill="${b.color}" opacity="${b.opacity ?? 0.13}"/>`;
    }
    const lines = [...(cfg.right || []).map((s) => ({ ...s, yf: YO })), ...cfg.left.map((s) => ({ ...s, yf: Y }))]
      .map((s) => `<path d="${path(s.pts, s.yf, s.step)}" fill="none" stroke="${s.color}" stroke-width="${s.width || 2.2}" ${s.dash ? `stroke-dasharray="${s.dash}"` : ""} stroke-linejoin="round" ${s.opacity ? `opacity="${s.opacity}"` : ""}/>`).join("");
    let marks = "";
    if (cfg.now) marks += `<line x1="${X(cfg.now)}" x2="${X(cfg.now)}" y1="${m.t}" y2="${H - m.b}" class="nowline"/><text x="${X(cfg.now)}" y="${m.t - 5}" class="ax" text-anchor="middle">${this.t.now.toUpperCase()}</text>`;
    for (const mk of cfg.markers || []) {
      if (mk.x < x0 || mk.x > x1) continue;
      marks += `<line x1="${X(mk.x)}" x2="${X(mk.x)}" y1="${m.t}" y2="${H - m.b}" stroke="${mk.color}" stroke-dasharray="2 3"/><circle cx="${X(mk.x)}" cy="${m.t + 6}" r="5" fill="${mk.color}"><title>${esc(mk.title)}</title></circle>`;
    }
    box.innerHTML = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${bands}${g}${lines}${marks}
      <rect class="hover" x="${m.l}" y="${m.t}" width="${W - m.l - m.r}" height="${H - m.t - m.b}" fill="transparent"/>
      <g class="tip" style="display:none"><line class="tipline" y1="${m.t}" y2="${H - m.b}"/><rect class="tipbox" rx="6"/><text class="tiptext"></text></g></svg>`;
    if (!cfg.tip) return;
    const svg = box.querySelector("svg");
    const tip = svg.querySelector(".tip");
    svg.querySelector(".hover").addEventListener("mousemove", (ev) => {
      const r = svg.getBoundingClientRect();
      const px = ev.clientX - r.left;
      const x = x0 + ((px - m.l) / (W - m.l - m.r)) * (x1 - x0);
      const rows = cfg.tip(x);
      const text = tip.querySelector(".tiptext");
      text.innerHTML = rows.map((l, i) => `<tspan x="0" dy="${i ? 16 : 0}">${esc(l)}</tspan>`).join("");
      tip.style.display = "";
      tip.querySelector(".tipline").setAttribute("x1", px);
      tip.querySelector(".tipline").setAttribute("x2", px);
      const bw = 200, bh = rows.length * 16 + 12;
      const bx = px + bw + 12 > W ? px - bw - 8 : px + 8;
      const tb = tip.querySelector(".tipbox");
      tb.setAttribute("x", bx); tb.setAttribute("y", m.t + 4); tb.setAttribute("width", bw); tb.setAttribute("height", bh);
      text.setAttribute("transform", `translate(${bx + 10},${m.t + 20})`);
    });
    svg.querySelector(".hover").addEventListener("mouseleave", () => { tip.style.display = "none"; });
  }

  _drawChart() {
    const box = this.shadowRoot.querySelector('[data-chart="main"]');
    if (!box) return;
    const s = this._series();
    if (!s) { box.innerHTML = `<div class="muted pad">…</div>`; return; }
    const now = Date.now();
    const x0 = now - this._past * 3600e3, x1 = now + this._ahead * 3600e3;
    const a = this._st(E.climate).attributes;
    const src = this._history.src;
    const live = (arr, v) => { if (v !== null && v !== undefined && Number.isFinite(+v)) arr.push([now, +v]); return arr; };
    live(s.room, this._num(src.room)); live(s.outdoor, this._num(src.outdoor)); live(s.target, a.temperature);
    s.strategy.push([now, this._st(E.strategy)?.state]);
    const fc = this._ahead ? (this._info?.forecast?.points || []).filter((p) => p[0] <= x1) : [];
    const fcTarget = fc.map((p) => [p[0], p[1]]);
    const fcRoom = fc.map((p) => [p[0], p[2]]);
    const outFc = this._ahead ? (this._info?.outdoor_forecast || []).filter(([x]) => x >= now) : [];
    if (outFc.length && s.outdoor.length) outFc.unshift([now, s.outdoor[s.outdoor.length - 1][1]]);
    if (!s.room.length && !fcRoom.length) { box.innerHTML = `<div class="muted pad">${this.t.noHistory}</div>`; return; }
    const bands = [];
    for (let i = 0; i < s.strategy.length; i++) {
      const [x, v] = s.strategy[i];
      const xe = i + 1 < s.strategy.length ? s.strategy[i + 1][0] : now;
      if (COLORS[v] && v !== "off") bands.push({ x0: x, x1: xe, color: COLORS[v] });
    }
    for (let i = 0; i + 1 < fc.length; i++) {
      if (COLORS[fc[i][3]] && fc[i][3] !== "off") bands.push({ x0: fc[i][0], x1: fc[i + 1][0], color: COLORS[fc[i][3]], opacity: 0.07 });
    }
    bands.push({ x0: now, x1, color: "#888", opacity: 0.06 });
    const H = (k) => this._hidden.has(k);
    const left = [
      !H("aircoSet") && { pts: s.aircoSet, color: COLORS.airco, step: true, dash: "5 4", width: 1.5 },
      !H("cvSet") && { pts: s.cvSet, color: COLORS.cv, step: true, dash: "5 4", width: 1.5 },
      !H("target") && { pts: s.target, color: COLORS.target, step: true },
      !H("target") && fcTarget.length && { pts: fcTarget, color: COLORS.target, step: true, dash: "6 4", opacity: 0.9 },
      !H("room") && { pts: s.room, color: COLORS.room },
      !H("expected") && fcRoom.length && { pts: fcRoom, color: COLORS.room, dash: "3 3", opacity: 0.9 },
    ].filter(Boolean);
    const right = H("outdoor") ? [] : [{ pts: s.outdoor, color: COLORS.outdoor, width: 1.5 }, outFc.length && { pts: outFc, color: COLORS.outdoor, width: 1.5, dash: "3 3" }].filter(Boolean);
    const pre = this._st(E.preheat)?.state;
    const markers = [];
    if (pre && !["unknown", "unavailable"].includes(pre)) markers.push({ x: new Date(pre).getTime(), color: COLORS.target, title: `${this.t.preheatStart} ${this._time(new Date(pre))}` });
    const at = (pts, x) => { let v = null; for (const [px, pv] of pts) { if (px <= x) v = pv; else break; } return v; };
    this._svgChart(box, {
      x0, x1, left, right, bands, markers, now, height: 320,
      tip: (x) => {
        const t = this.t;
        const rows = x > now
          ? [[t.plan, at(fcTarget, x)], [t.expectedRoom, at(fcRoom, x)], [t.outdoorFc, at(outFc, x)]]
          : [[t.room, at(s.room, x)], [t.target, at(s.target, x)], [t.outdoor, at(s.outdoor, x)]];
        const st = x > now ? at(fc.map((p) => [p[0], p[3]]), x) : at(s.strategy, x);
        const out = [this._when(new Date(x)), ...rows.filter(([, v]) => v !== null && v !== undefined).map(([k, v]) => `${k}: ${this._fmt(v)} °C`)];
        if (st && st !== "off") out.push(t.strategy[st] || st);
        return out;
      },
    });
  }


  _fcCost(hours, fromTs = null, toTs = null) {
    const hourly = this._info?.forecast?.hourly || [];
    if (!hourly.length) return null;
    const start = fromTs ?? hourly[0][0];
    const end = toTs ?? start + hours * 3600e3;
    return hourly.filter(([h]) => h >= start && h < end).reduce((s, [, a, c]) => s + a + c, 0);
  }

  _stratText(strategy, fan) {
    const t = this.t;
    const name = t.strategy[strategy] || strategy;
    return fan ? `${name} (${t.fan[fan]})` : name;
  }

  _actionText(a) {
    const t = this.t, A = t.fc.act;
    if (a.strategy === "off" || a.target == null) {
      return a.phase === "paused" ? t.reason.window_open : A.off(this._fmt(a.t_end, 1));
    }
    let txt = (a.phase === "heat_up" ? A.heat_up : A.maintain)(this._fmt(a.target, 1), this._stratText(a.strategy, a.fan));
    if (a.phase !== "heat_up" && a.t_start != null && a.t_start > a.target + 0.3) txt = A.coolThen(this._fmt(a.target, 1), this._stratText(a.strategy, a.fan));
    if (a.reason === "preheat" && a.deadline) txt += ` ${A.preheatFor(this._time(new Date(a.deadline)))}`;
    return txt;
  }

  _forecast() {
    const t = this.t, F = t.fc;
    const info = this._info;
    if (!info) return `<div class="muted pad">${esc(this._infoError || "…")}</div>`;
    const fc = info.forecast || {};
    if (!fc.points || !fc.points.length) return `<div class="banner">${F.noForecast}</div>`;
    const now = Date.now();
    const midnight = new Date(); midnight.setHours(24, 0, 0, 0);
    const m2 = new Date(midnight); m2.setDate(m2.getDate() + 1);
    const daySplit = (from, to) => {
      const rows = (fc.hourly || []).filter(([h]) => h >= from && h < to);
      return { a: rows.reduce((s, r) => s + r[1], 0), c: rows.reduce((s, r) => s + r[2], 0) };
    };
    const today = daySplit(0, midnight.getTime());
    const tomorrow = daySplit(midnight.getTime(), m2.getTime());
    const split = fc.split || {};
    const totalSplit = (split.heat_up || 0) + (split.maintain || 0);
    const pct = (v) => (totalSplit > 0 ? Math.round((100 * v) / totalSplit) : 0);
    const week = fc.cost != null ? (fc.cost * 168) / (fc.hours || 72) : null;
    const sub = (x) => `${t.strategy.airco} ${this._eur(x.a)} · ${t.strategy.cv} ${this._eur(x.c)}`;

    const acts = (fc.actions || []).slice(0, 16).map((a, i) => {
      const start = new Date(a.t), end = new Date(a.end);
      const mins = Math.round((a.end - a.t) / 60000);
      const dur = mins >= 60 ? `${Math.floor(mins / 60)}${this._hUnit} ${String(mins % 60).padStart(2, "0")}m` : `${mins}m`;
      const cls = a.strategy === "off" ? "off" : a.strategy;
      return `<div class="act ${a.phase}">
        <div class="when">${i === 0 ? F.act.now : this._when(start)}</div>
        <div class="dotline"><span class="adot ${cls}"></span></div>
        <div class="what"><b>${esc(this._actionText(a))}</b>
          <div class="sub">${esc(t.reason[a.reason] || a.reason)} · ${F.act.until} ${this._when(end)} (${dur})${a.t_end != null ? ` · ${this._fmt(a.t_start, 1)} → ${this._fmt(a.t_end, 1)} °C` : ""}</div></div>
        <div class="acost">${a.cost > 0.005 ? this._eur(a.cost) : "–"}</div></div>`;
    }).join("");

    const sc = info.scenarios || {};
    const scen = (sc.scenarios || []).map((x) => {
      const lbl = F.scen[x.id] || [x.id, ""];
      const good = x.delta_week < -0.005, bad = x.delta_week > 0.005;
      const cmf = Math.abs(x.delta_deficit_h) < 0.25 ? F.noEffect : x.delta_deficit_h > 0 ? F.colder(this._fmt(x.delta_deficit_h, 1)) : F.warmer(this._fmt(-x.delta_deficit_h, 1));
      return `<tr><td><b>${esc(lbl[0])}</b><div class="sub">${esc(lbl[1])}</div></td>
        <td class="num ${good ? "save" : bad ? "more" : ""}">${x.delta_week > 0 ? "+" : ""}${this._eur(x.delta_week)}<div class="sub">${F.perWeekShort}</div></td>
        <td class="${x.delta_deficit_h > 0.25 ? "more" : ""}">${esc(cmf)}</td></tr>`;
    }).join("");

    return `${info.forecast_hypothetical ? `<div class="banner warn"><div>${F.hypothetical}</div></div>` : ""}
      <div class="grid">
        ${this._card(F.restToday, this._eur(today.a + today.c), sub(today))}
        ${this._card(F.tomorrow, this._eur(tomorrow.a + tomorrow.c), sub(tomorrow))}
        ${this._card(F.next3, this._eur(fc.cost))}
        ${this._card(F.perWeek, this._eur(week))}
        ${this._card(F.shortfall, `${this._fmt(fc.deficit_h, 1)} ${this._hUnit}`, F.shortfallSub(this._fmt(fc.deficit_h, 1)))}
      </div>
      <div class="card"><h2>${F.planTitle}</h2>
        <div class="legend"><span class="band-key"><i class="line dash" style="--c:${COLORS.room}"></i>${t.expectedRoom}</span>
          <span class="band-key"><i class="line" style="--c:${COLORS.target}"></i>${t.plan}</span>
          <span class="band-key"><i class="line dash" style="--c:${COLORS.outdoor}"></i>${t.outdoorFc}</span><span class="sep"></span>
          ${STRATS.map((s) => `<span class="band-key"><i style="background:${COLORS[s]}"></i>${t.strategy[s]}</span>`).join("")}</div>
        <div class="chart" data-chart="fc-temp"></div>
        <h3 class="mt2">${F.costHourTitle}</h3>
        <div class="chart small" data-chart="fc-cost"></div>
        <div class="legend small"><span class="band-key"><i style="background:${COLORS.airco}"></i>${t.strategy.airco}</span><span class="band-key"><i style="background:${COLORS.cv}"></i>${t.strategy.cv}</span></div>
      </div>
      <div class="two">
        <div class="card"><h2>${F.actionsTitle}</h2><div class="timeline">${acts}</div></div>
        <div>
          <div class="card"><h2>${F.costDayTitle}</h2>${this._bars((fc.daily || []).map(([d, a, c]) => ({ d: new Date(d + "T12:00:00"), a, c })), (r) => r.d.toLocaleDateString(this.lang, { weekday: "short", day: "numeric" }), (r) => r.d.toLocaleDateString(this.lang, { weekday: "long", day: "numeric", month: "long" }))}</div>
          <div class="card mt"><h2>${F.splitTitle}</h2>
            ${this._splitBar([[F.heatUp, split.heat_up || 0, COLORS.target], [F.keepWarm, split.maintain || 0, COLORS.room]])}
            ${this._splitBar([[t.strategy.airco, split.airco || 0, COLORS.airco], [t.strategy.cv, split.cv || 0, COLORS.cv]])}
          </div>
        </div>
      </div>
      <div class="card"><h2>${F.savingsTitle}</h2>
        <div class="muted">${sc.base ? F.savingsText(this._eur(sc.base.week)) : ""}</div>
        <table class="tbl scen"><tbody>${scen}</tbody></table></div>`;
  }

  _splitBar(parts) {
    const total = parts.reduce((s, p) => s + p[1], 0) || 1;
    return `<div class="splitbar">${parts.map(([l, v, c]) => `<div style="width:${(100 * v / total).toFixed(1)}%;background:${c}" title="${esc(l)}: ${this._eur(v)}"></div>`).join("")}</div>
      <div class="splitlbl">${parts.map(([l, v, c]) => `<span><i style="background:${c}"></i>${esc(l)} ${Math.round(100 * v / total)}% · ${this._eur(v)}</span>`).join("")}</div>`;
  }

  _drawForecastCharts() {
    const fc = this._info?.forecast;
    if (!fc?.points?.length) return;
    const pts = fc.points;
    const x0 = pts[0][0], x1 = pts[pts.length - 1][0];
    const box = this.shadowRoot.querySelector('[data-chart="fc-temp"]');
    const target = pts.map((p) => [p[0], p[1]]), room = pts.map((p) => [p[0], p[2]]);
    const outFc = (this._info.outdoor_forecast || []).filter(([x]) => x >= x0 && x <= x1);
    const bands = [];
    for (let i = 0; i + 1 < pts.length; i++) {
      if (COLORS[pts[i][3]] && pts[i][3] !== "off") bands.push({ x0: pts[i][0], x1: pts[i + 1][0], color: COLORS[pts[i][3]], opacity: pts[i][4] === "boost" ? 0.22 : 0.12 });
    }
    const at = (arr, x) => { let v = null; for (const [px, pv] of arr) { if (px <= x) v = pv; else break; } return v; };
    const midnights = [];
    const d = new Date(x0); d.setHours(24, 0, 0, 0);
    for (; d.getTime() < x1; d.setDate(d.getDate() + 1)) midnights.push({ x: d.getTime(), color: "#888", title: d.toLocaleDateString(this.lang, { weekday: "long" }) });
    if (box) this._svgChart(box, {
      x0, x1, height: 280, bands, markers: midnights,
      left: [{ pts: target, color: COLORS.target, step: true }, { pts: room, color: COLORS.room, dash: "4 3" }],
      right: outFc.length ? [{ pts: outFc, color: COLORS.outdoor, dash: "3 3", width: 1.5 }] : [],
      tip: (x) => {
        const p = pts.filter((q) => q[0] <= x).pop() || pts[0];
        const out = [this._when(new Date(x)), `${this.t.plan}: ${this._fmt(p[1])} °C`, `${this.t.expectedRoom}: ${this._fmt(p[2])} °C`];
        const o = at(outFc, x); if (o != null) out.push(`${this.t.outdoorFc}: ${this._fmt(o)} °C`);
        if (p[3] !== "off") out.push(this._stratText(p[3], p[4]));
        return out;
      },
    });
    const cb = this.shadowRoot.querySelector('[data-chart="fc-cost"]');
    if (cb) {
      const W = Math.max(cb.clientWidth, 300), H = 120, m = { l: 54, r: 44, t: 8, b: 22 };
      const hourly = (fc.hourly || []).filter(([h]) => h >= x0 - 3600e3 && h <= x1);
      const max = Math.max(...hourly.map(([, a, c]) => a + c), 0.01);
      const X = (x) => m.l + ((x - x0) / (x1 - x0)) * (W - m.l - m.r);
      const bw = Math.max(((W - m.l - m.r) / ((x1 - x0) / 3600e3)) - 1, 1);
      const Y = (v) => (v / max) * (H - m.t - m.b);
      let bars = "";
      for (const [h, a, c] of hourly) {
        const x = X(Math.max(h, x0));
        const ha = Y(a), hc = Y(c);
        bars += `<rect x="${x.toFixed(1)}" y="${(H - m.b - hc).toFixed(1)}" width="${bw.toFixed(1)}" height="${hc.toFixed(1)}" fill="${COLORS.cv}"><title>${this._when(new Date(h))}: ${this._eur(a + c)}</title></rect>`;
        bars += `<rect x="${x.toFixed(1)}" y="${(H - m.b - hc - ha).toFixed(1)}" width="${bw.toFixed(1)}" height="${ha.toFixed(1)}" fill="${COLORS.airco}"><title>${this._when(new Date(h))}: ${this._eur(a + c)}</title></rect>`;
      }
      let axis = `<text x="${m.l - 6}" y="${m.t + 8}" class="ax" text-anchor="end">${this._eur(max)}</text><text x="${m.l - 6}" y="${H - m.b}" class="ax" text-anchor="end">${this._eur(0, 0)}</text>`;
      for (const mk of midnights) axis += `<line x1="${X(mk.x)}" x2="${X(mk.x)}" y1="${m.t}" y2="${H - m.b}" class="gl v"/><text x="${X(mk.x) + 4}" y="${H - 6}" class="ax">${esc(mk.title)}</text>`;
      cb.innerHTML = `<svg width="${W}" height="${H}">${axis}${bars}<line x1="${m.l}" x2="${W - m.r}" y1="${H - m.b}" y2="${H - m.b}" class="gl"/></svg>`;
    }
  }

  // ---------------------------------------------------------------- costs tab
  _costs() {
    const t = this.t;
    if (!this._stats) this._loadStats();
    const day = this._stats?.day || {}, month = this._stats?.month || {};
    const A = E.costTotal("airco"), C = E.costTotal("cv");
    const byKey = (rows) => Object.fromEntries((rows || []).map((r) => [new Date(r.start).toDateString(), Math.max(r.change || 0, 0)]));
    const dA = byKey(day[A]), dC = byKey(day[C]);
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const days = [];
    for (let i = 29; i >= 0; i--) {
      const d = new Date(today); d.setDate(d.getDate() - i);
      days.push({ d, a: dA[d.toDateString()] || 0, c: dC[d.toDateString()] || 0 });
    }
    days[29].a = this._num(E.costToday("airco")) ?? days[29].a;
    days[29].c = this._num(E.costToday("cv")) ?? days[29].c;
    const mA = byKey(month[A]), mC = byKey(month[C]);
    const months = [];
    for (let i = 11; i >= 0; i--) {
      const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
      months.push({ d, a: mA[d.toDateString()] || 0, c: mC[d.toDateString()] || 0 });
    }
    const sum = (arr) => arr.reduce((s, x) => s + x.a + x.c, 0);
    const monthNow = days.filter((x) => x.d.getMonth() === today.getMonth());
    const hasStats = Object.keys(day).length > 0;
    const split = (x) => `${t.strategy.airco} ${this._eur(x.a)} · ${t.strategy.cv} ${this._eur(x.c)}`;
    return `<div class="grid">
        ${this._card(t.today, this._eur(days[29].a + days[29].c), split(days[29]))}
        ${this._card(t.yesterday, this._eur(days[28].a + days[28].c), split(days[28]))}
        ${this._card(t.expected24, this._eur(this._fcCost(24)))}
        ${this._card(t.last7, this._eur(sum(days.slice(-7))))}
        ${this._card(t.thisMonth, this._eur(sum(monthNow)))}
        ${this._card(t.last30, this._eur(sum(days)))}
      </div>
      ${hasStats ? "" : `<div class="banner">${t.noStats}</div>`}
      <div class="card"><h2>${t.costPerDay}</h2>${this._bars(days, (d) => d.d.getDate(), (d) => d.d.toLocaleDateString(this.lang, { weekday: "short", day: "numeric", month: "short" }))}</div>
      <div class="card"><h2>${t.costPerMonth}</h2>${this._bars(months, (d) => d.d.toLocaleDateString(this.lang, { month: "short" }), (d) => d.d.toLocaleDateString(this.lang, { month: "long", year: "numeric" }))}</div>`;
  }

  _bars(rows, label, title) {
    const max = Math.max(...rows.map((r) => r.a + r.c), 0.01);
    const h = (v) => `${((v / max) * 100).toFixed(1)}%`;
    return `<div class="bars">${rows.map((r) => `<div class="barcol" title="${esc(title(r))}: ${this._eur(r.a + r.c)} (${this.t.strategy.airco} ${this._eur(r.a)}, ${this.t.strategy.cv} ${this._eur(r.c)})">
        <div class="barval">${r.a + r.c > 0 ? this._eur(r.a + r.c, r.a + r.c < 10 ? 2 : 0) : ""}</div>
        <div class="stack"><div style="height:${h(r.c)};background:${COLORS.cv}"></div><div style="height:${h(r.a)};background:${COLORS.airco}"></div></div>
        <div class="barlbl">${esc(label(r))}</div></div>`).join("")}</div>
      <div class="legend small"><span class="band-key"><i style="background:${COLORS.airco}"></i>${this.t.strategy.airco}</span><span class="band-key"><i style="background:${COLORS.cv}"></i>${this.t.strategy.cv}</span></div>`;
  }

  // ---------------------------------------------------------------- model tab
  _prices() {
    const s = this._info?.settings || {};
    return { kwh: +(s.price_kwh ?? 0.25), gas: +(s.price_gas ?? 1.35) };
  }

  _model() {
    const t = this.t;
    const info = this._info;
    if (!info) return `<div class="muted pad">${esc(this._infoError || "…")}</div>`;
    const m = info.model;
    const th = m.theta, conf = m.confidence, sd = m.std;
    const tOut = m.t_out ?? 5;
    const chk = m.check || {};
    const mae = chk.mae_1h;
    const level = mae == null ? "none" : mae <= 0.3 ? "good" : mae <= 0.5 ? "ok" : "bad";
    const badge = (c) => `<span class="conf ${c}">${t.confidence}: ${t.conf[c]}</span>`;
    const pm = (v, s, d = 2) => `${this._fmt(v, d)}${s > 0 && Number.isFinite(s) ? ` <span class="muted">± ${this._fmt(s, d)}</span>` : ""}`;
    const pr = this._prices();
    const u = this._hUnit;
    const gainA = Math.max(th.ga0 + th.ga1 * tOut, 0.05);
    const night = tOut + (20 - tOut) * Math.exp(-th.k * 8);
    const solarActive = info.features_active?.solar;

    const params = `
      <div class="pgrid">
        <div class="pcard"><div class="phead"><b>${t.loss}</b>${badge(conf.k)}</div>
          <div class="pbig">${pm(th.k * 10, sd.k * 10)} °C/${u}</div>
          <div class="sub">${t.lossText(this._fmt(th.k * 10, 2))} ${t.lossNight("20", this._fmt(night, 1), 8)}</div>
          <div class="muted">${t.samplesBasis(Math.round((m.counts.passive || 0) + 0.3 * ((m.counts.airco || 0) + (m.counts.cv || 0))))}</div></div>
        <div class="pcard"><div class="phead">${this._chip("airco")}${badge(conf.ga0)}</div>
          <div class="pbig">+${pm(gainA, sd.ga0)} °C/${u} <span class="muted">per kW</span></div>
          <div class="sub">${t.aircoText(this._fmt(gainA, 2), this._fmt(tOut, 1))} ${t.costDeg(this._eur(m.sources.airco.cost_per_degree, 3))}.</div>
          <div class="muted">${t.maxPower(this._fmt(m.pmax.airco, 2), "kW")} → ${this._fmt(m.sources.airco.max_rate, 2)} °C/${u} · ${t.samplesBasis(Math.round(m.counts.airco || 0))}</div></div>
        <div class="pcard"><div class="phead">${this._chip("cv")}${badge(conf.gc)}</div>
          <div class="pbig">+${pm(th.gc, sd.gc)} °C/${u} <span class="muted">per m³/${u}</span></div>
          <div class="sub">${t.cvText(this._fmt(th.gc, 2))} ${t.costDeg(this._eur(m.sources.cv.cost_per_degree, 3))}.</div>
          <div class="muted">${t.maxPower(this._fmt(m.pmax.cv, 2), "m³/" + u)} → ${this._fmt(m.sources.cv.max_rate, 2)} °C/${u} · ${t.samplesBasis(Math.round(m.counts.cv || 0))}</div></div>
        <div class="pcard"><div class="phead"><b>☀ ${t.solarK}</b>${solarActive ? badge(conf.gs) : ""}</div>
          ${solarActive ? `<div class="pbig">+${pm(th.gs, sd.gs)} °C/${u} <span class="muted">per kW</span></div>
          <div class="sub">${t.solarText(this._fmt(th.gs, 2))}</div><div class="muted">${t.samplesBasis(Math.round(m.counts.solar || 0))}</div>` : `<div class="sub">${t.solarOff}</div>`}</div>
        ${info.fan?.active ? `<div class="pcard"><div class="phead"><b>🌀 ${t.fanCard}</b>${badge(conf.gab || "none")}</div>
          <div class="pbig">${th.gab >= 0 ? "+" : ""}${pm(gainA ? (100 * th.gab) / gainA : 0, gainA ? (100 * (sd.gab || 0)) / gainA : 0, 0)}%</div>
          <div class="sub">${t.fanGain((th.gab >= 0 ? "+" : "") + this._fmt(gainA ? (100 * th.gab) / gainA : 0, 0) + "%")}
          ${t.fanRates(this._fmt(m.sources.airco.boost_max_rate, 2), this._fmt(m.sources.airco.max_rate, 2), u)}</div>
          <div class="muted">${t.maxPower(this._fmt(m.pmax.airco_boost, 2), "kW")} (${t.fan.boost}) · ${this._fmt(m.pmax.airco, 2)} kW (${t.fan.comfort}) · ${t.samplesBasis(Math.round(m.counts.boost || 0))}</div></div>` : ""}
      </div>`;

    let be = null;
    for (let x = 20; x >= -15; x--) {
      const ca = pr.kwh / Math.max(th.ga0 + th.ga1 * x, 0.05), cc = pr.gas / Math.max(th.gc, 0.05);
      if (ca > cc) { be = x; break; }
    }
    const caNow = pr.kwh / gainA, ccNow = pr.gas / Math.max(th.gc, 0.05);
    const beText = be === null ? t.noBreakeven(t.strategy.airco) : be >= 20 ? t.noBreakeven(t.strategy.cv) : t.breakeven(be + 1);

    const diag = (info.diagnostics || []).map((d) => {
      const tx = t.diagText;
      let text;
      if (d.id.startsWith("entity_")) text = tx.entity(d.status, d.params);
      else if (d.id.startsWith("feature_")) text = tx.unconfigured();
      else text = (tx[d.id] || (() => ""))(d.status, d.params);
      return `<div class="diag ${d.status}"><span class="dicon">${{ ok: "✓", info: "i", warn: "!", error: "✕" }[d.status]}</span>
        <div><b>${esc(t.diag[d.id] || d.id)}</b><div class="sub">${esc(text)}</div></div><span class="dstat">${t.status[d.status]}</span></div>`;
    }).join("");

    const excluded = Object.entries(m.excluded || {}).sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${esc(t.exReasons[k] || k)}: ${v}`).join(" · ") || "–";
    const sugg = (info.suggestions || []).map((s) => `<div class="sugg"><div>${esc((t.sugg[s.kind] || (() => s.kind))(s.params))}</div>
      <div class="actions">${s.action ? `<button class="btn" data-action="suggest" data-id="${esc(s.id)}" data-value="apply">${t.apply}</button>` : ""}
      <button class="btn" data-action="suggest" data-id="${esc(s.id)}" data-value="dismiss">${t.dismiss}</button></div></div>`).join("");
    const bias = chk.bias_1h;

    return `<div class="card fit ${level}">
        <div class="fit-l"><div class="label">${t.fitTitle}</div>
          <div class="value">${t.fitLabels[level]}</div>
          <div class="sub">${mae != null ? t.fitValue(this._fmt(mae, 2)) : ""}${bias != null && Math.abs(bias) >= 0.1 ? "<br>" + t.bias(Math.round(bias * 100) / 100) : ""}</div></div>
        <div class="muted fit-r">${t.fitText}</div></div>
      <div class="card"><h2>${t.replayTitle}</h2>
        <div class="legend"><span class="band-key"><i class="line" style="--c:${COLORS.room}"></i>${t.real}</span><span class="band-key"><i class="line dash" style="--c:${COLORS.model}"></i>${t.modelLine}</span></div>
        <div class="chart" data-chart="replay"></div><div class="muted">${t.replayText}</div></div>
      <div class="card"><h2>${t.knowsTitle}</h2>${params}</div>
      <div class="card"><h2>${t.breakevenTitle}</h2>
        <div class="sub">${beText} (${t.strategy.airco} ${this._eur(caNow, 3)}/°C · ${t.strategy.cv} ${this._eur(ccNow, 3)}/°C ${t.nowWord})</div>
        <div class="legend"><span class="band-key"><i class="line" style="--c:${COLORS.airco}"></i>${t.strategy.airco}</span><span class="band-key"><i class="line" style="--c:${COLORS.cv}"></i>${t.strategy.cv}</span></div>
        <div class="chart" data-chart="breakeven"></div></div>
      <div class="two">
        <div class="card"><h2>${t.diagTitle}</h2>${diag}</div>
        <div class="card"><h2>${t.suggTitle}</h2>${sugg || `<div class="muted">${t.noSugg}</div>`}
          <h2 class="mt">${t.dataTitle}</h2>
          <div class="kv"><span>${t.used}</span><b>${Math.round(m.n_eff)}</b></div>
          <div class="kv"><span>${t.excluded}</span><b>${excluded}</b></div>
          <div class="kv"><span>${t.lastSample}</span><b>${esc(t.exReasons[m.last_sample] || m.last_sample || "–")}</b></div>
          <h2 class="mt">${t.resetTitle}</h2>
          <div class="resets">${Object.entries(t.scopes).map(([k, v]) => `<button class="btn ${k === "all" ? "danger" : ""}" data-action="reset" data-value="${k}">${v}</button>`).join("")}</div>
        </div>
      </div>`;
  }

  _drawModelCharts() {
    const info = this._info;
    if (!info) return;
    const box = this.shadowRoot.querySelector('[data-chart="replay"]');
    const rp = info.model.replay || [];
    const at = (pts, x) => { let v = null; for (const [px, pv] of pts) { if (px <= x) v = pv; else break; } return v; };
    if (box) {
      if (rp.length < 2) box.innerHTML = `<div class="muted pad">${this.t.fitLabels.none}</div>`;
      else {
        const real = rp.map((r) => [r[0], r[1]]), mod = rp.map((r) => [r[0], r[2]]);
        this._svgChart(box, {
          x0: rp[0][0], x1: rp[rp.length - 1][0], height: 240,
          left: [{ pts: real, color: COLORS.room }, { pts: mod, color: COLORS.model, dash: "5 3" }],
          tip: (x) => [this._when(new Date(x)), `${this.t.real}: ${this._fmt(at(real, x))} °C`, `${this.t.modelLine}: ${this._fmt(at(mod, x))} °C`],
        });
      }
    }
    const be = this.shadowRoot.querySelector('[data-chart="breakeven"]');
    if (be) {
      const th = info.model.theta;
      const pr = this._prices();
      const a = [], c = [];
      for (let x = -15; x <= 20; x++) {
        a.push([x, pr.kwh / Math.max(th.ga0 + th.ga1 * x, 0.05)]);
        c.push([x, pr.gas / Math.max(th.gc, 0.05)]);
      }
      const top = Math.max(...[...a, ...c].map((p) => p[1])) * 1.15;
      const step = top > 1 ? 0.25 : top > 0.4 ? 0.1 : 0.05;
      this._svgChart(be, {
        x0: -15, x1: 20, xNumeric: true, height: 200, yRange: [0, Math.ceil(top / step) * step], yStep: step,
        yFmt: (v) => this._eur(v, 2),
        left: [{ pts: a, color: COLORS.airco }, { pts: c, color: COLORS.cv }],
        tip: (x) => {
          const xi = Math.round(x);
          return [`${xi} °C`, `${this.t.strategy.airco}: ${this._eur(pr.kwh / Math.max(th.ga0 + th.ga1 * xi, 0.05), 3)}/°C`,
            `${this.t.strategy.cv}: ${this._eur(pr.gas / Math.max(th.gc, 0.05), 3)}/°C`];
        },
      });
    }
  }

  // ---------------------------------------------------------------- settings tab
  _settings() {
    const t = this.t;
    const info = this._info;
    if (!info) return `<div class="muted pad">${esc(this._infoError || "…")}</div>`;
    const mode = this._st(E.mode)?.state;
    if (!this._draft) this._draft = JSON.parse(JSON.stringify(info.schedule));
    const d = this._draft;
    const dirty = JSON.stringify(d) !== JSON.stringify(info.schedule);
    const s = info.settings;
    const num = (key, value, step, unit, min = 5, max = 30) =>
      `<label class="field"><input type="number" step="${step}" min="${min}" max="${max}" value="${esc(value)}" data-setting="${key}"><span>${unit}</span></label>`;

    const feats = FEATURES.map((f) => {
      const on = !!info.features[f];
      const act = info.features_active[f];
      const state = !on ? t.off : act ? t.active : t.notConfigured;
      return `<div class="feat"><div><b>${t.feat[f][0]}</b><div class="sub">${t.feat[f][1]}</div></div>
        <span class="fstate ${!on ? "off" : act ? "on" : "warn"}">${state}</span>
        <label class="switch"><input type="checkbox" data-feature="${f}" ${on ? "checked" : ""}><span></span></label></div>`;
    }).join("");

    const profile = (name) => `<div class="profile"><h3>${t[name]}</h3>
      <div class="blocks">${(d.profiles[name] || []).map((b, i) => `<div class="block ${b.enabled ? "" : "disabled"}">
        <label class="switch small"><input type="checkbox" data-block="${name}:${i}:enabled" ${b.enabled ? "checked" : ""}><span></span></label>
        <label class="field"><span>${t.from}</span><input type="time" value="${esc(b.start)}" data-block="${name}:${i}:start"></label>
        <label class="field"><span>${t.until}</span><input type="time" value="${esc(b.end)}" data-block="${name}:${i}:end"></label>
        <label class="field"><input type="number" step="0.5" min="5" max="28" value="${esc(b.temp)}" data-block="${name}:${i}:temp"><span>°C</span></label>
        <button class="icon" data-action="del-block" data-value="${name}:${i}" title="×">✕</button></div>`).join("")}</div>
      <button class="btn" data-action="add-block" data-value="${name}">+ ${t.addBlock}</button></div>`;

    return `<div class="card"><h2>${t.mode}</h2>
        <div class="seg">${Object.entries(t.modes).map(([k, v]) => `<button class="${k === mode ? "on" : ""}" data-action="mode" data-value="${k}">${v}</button>`).join("")}</div></div>
      <div class="card"><h2>${t.schedule}</h2>
        <label class="check"><input type="checkbox" data-action="weekend-toggle" ${d.weekend_enabled ? "checked" : ""}> ${t.weekendOn}</label>
        ${d.weekend_enabled ? `<div class="days">${DAYS.map((day) => `<button class="daychip ${d.days[day]}" data-action="day" data-value="${day}">${t.days[day]}<small>${t[d.days[day]]}</small></button>`).join("")}</div>` : ""}
        <div class="profiles">${profile("workday")}${d.weekend_enabled ? profile("weekend") : ""}</div>
        <div class="form"><div>${t.ecoTemp}</div>${num("eco_temp", s.eco_temp, 0.5, "°C")}</div>
        <div class="actions"><span class="muted">${dirty ? t.unsaved : ""}</span><button class="btn primary" data-action="save-schedule" ${dirty ? "" : "disabled"}>${t.save}</button></div></div>
      <div class="card"><h2>${t.fanTitle}</h2><div class="muted">${t.fanText}</div>
        ${(info.fan?.modes || []).length ? `<div class="form">
          <div>${t.fanBoost}</div><select data-setting-str="fan_boost_mode">${this._fanOptions(s.fan_boost_mode, info.fan.boost)}</select>
          <div>${t.fanComfort}</div><select data-setting-str="fan_comfort_mode">${this._fanOptions(s.fan_comfort_mode, info.fan.comfort)}</select>
        </div>` : `<div class="sub">${t.fanNone}</div>`}</div>
      <div class="card"><h2>${t.functions}</h2><div class="muted">${t.functionsText}</div>${feats}</div>
      <div class="card"><h2>${t.presenceTitle}</h2>
        <div class="form">
          <div>${t.awayTemp}</div>${num("away_temp", s.away_temp, 0.5, "°C")}
          <div>${t.vacTemp}</div>${num("vacation_temp", s.vacation_temp, 0.5, "°C")}
          <div>${t.vacation}</div><label class="switch"><input type="checkbox" data-setting-bool="vacation" ${s.vacation ? "checked" : ""}><span></span></label>
          <div>${t.guest}</div><label class="switch"><input type="checkbox" data-setting-bool="guest" ${s.guest ? "checked" : ""}><span></span></label>
        </div></div>
      <div class="card"><h2>${t.prices}</h2><div class="muted">${t.pricesHint}</div>
        <div class="form">
          <div>${t.electricity}</div>${num("price_kwh", s.price_kwh, 0.001, "€/kWh", 0, 2)}
          <div>${t.gas}</div>${num("price_gas", s.price_gas, 0.001, "€/m³", 0, 5)}
        </div></div>
      <div class="card row"><div>${t.advanced}</div><a class="btn" href="/config/integrations/integration/hybrid_heating" target="_top">${t.open}</a></div>`;
  }

  _fanOptions(chosen, effective) {
    const modes = this._info?.fan?.modes || [];
    return `<option value="" ${!chosen ? "selected" : ""}>${this.t.fanAuto} (${esc(effective || "–")})</option>` +
      modes.map((m) => `<option value="${esc(m)}" ${m === chosen ? "selected" : ""}>${esc(m)}</option>`).join("");
  }

  // ---------------------------------------------------------------- events
  _onClick(ev) {
    const el = ev.target.closest("[data-tab],[data-action]");
    if (!el || el.disabled || el.tagName === "INPUT") return;
    if (el.dataset.tab) {
      this._tab = el.dataset.tab;
      if (this._tab === "costs") this._loadStats();
      if (this._tab === "settings") this._draft = null;
      this._render(true);
      return;
    }
    const v = el.dataset.value;
    const d = this._draft;
    switch (el.dataset.action) {
      case "mode": this._hass.callService("select", "select_option", { entity_id: E.mode, option: v }).then(() => this._loadInfo()); break;
      case "setting": this._update({ settings: { [el.dataset.key]: v === "true" ? true : v === "false" ? false : v } }); break;
      case "past": this._past = +v; this._render(true); this._loadHistory(); break;
      case "ahead": this._ahead = +v; this._render(true); break;
      case "toggle": this._hidden.has(v) ? this._hidden.delete(v) : this._hidden.add(v); this._render(true); break;
      case "suggest": this._ws({ type: "hybrid_heating/suggestion", suggestion_id: el.dataset.id, action: v }).then(() => this._loadInfo()); break;
      case "reset":
        if (confirm(this.t.resetConfirm(this.t.scopes[v]))) this._ws({ type: "hybrid_heating/reset", scope: v }).then((r) => { this._info = r; this._render(true); });
        break;
      case "day": d.days[v] = d.days[v] === "workday" ? "weekend" : "workday"; this._render(true); break;
      case "add-block": {
        const list = d.profiles[v];
        const last = list[list.length - 1];
        list.push({ start: last ? last.end : "07:00", end: "22:00", temp: last ? last.temp : 20, enabled: true });
        this._render(true); break;
      }
      case "del-block": { const [p, i] = v.split(":"); d.profiles[p].splice(+i, 1); this._render(true); break; }
      case "save-schedule": this._update({ schedule: d }).then(() => { this._draft = null; this._render(true); }); break;
    }
  }

  _onChange(ev) {
    const el = ev.target;
    const ds = el.dataset;
    if (ds.setting) {
      const v = parseFloat(el.value);
      if (Number.isFinite(v)) this._update({ settings: { [ds.setting]: v } });
    } else if (ds.settingStr) {
      this._update({ settings: { [ds.settingStr]: el.value || null } });
    } else if (ds.settingBool) {
      this._update({ settings: { [ds.settingBool]: el.checked } });
    } else if (ds.feature) {
      this._update({ features: { [ds.feature]: el.checked } });
    } else if (ds.block) {
      const [p, i, key] = ds.block.split(":");
      const b = this._draft.profiles[p][+i];
      b[key] = key === "enabled" ? el.checked : key === "temp" ? parseFloat(el.value) : el.value;
      this._render(true);
    } else if (ds.action === "weekend-toggle") {
      this._draft.weekend_enabled = el.checked;
      this._render(true);
    }
  }
}

const STYLE = `
:host { display:block; min-height:100vh; background:var(--primary-background-color); color:var(--primary-text-color);
  font-family:var(--paper-font-body1_-_font-family, Roboto, system-ui, sans-serif); --r:12px; }
.toolbar { display:flex; align-items:center; gap:16px; height:56px; padding:0 16px; border-bottom:1px solid var(--divider-color);
  background:var(--app-header-background-color, var(--primary-background-color)); color:var(--app-header-text-color, var(--primary-text-color));
  position:sticky; top:0; z-index:2; }
.title { font-size:20px; font-weight:600; white-space:nowrap; }
.tabs { display:flex; gap:4px; overflow-x:auto; flex:1; }
.tab { background:none; border:0; color:inherit; font:inherit; font-size:15px; padding:8px 14px; border-radius:8px; cursor:pointer; opacity:.75; white-space:nowrap; }
.tab:hover { background:rgba(127,127,127,.12); opacity:1; }
.tab.active { background:rgba(127,127,127,.18); opacity:1; font-weight:600; }
.status { font-size:13px; color:var(--secondary-text-color); white-space:nowrap; display:flex; align-items:center; gap:6px; }
.dot { width:9px; height:9px; border-radius:50%; display:inline-block; }
.dot.ok { background:#4caf50; } .dot.warn { background:#ffa726; } .dot.err { background:#ef5350; }
.content { padding:16px; max-width:1400px; margin:0 auto; display:flex; flex-direction:column; gap:16px; }
.card { background:var(--card-background-color, var(--ha-card-background)); border:1px solid var(--divider-color); border-radius:var(--r); padding:16px; }
.card h2 { font-size:17px; margin:0 0 12px; font-weight:600; }
.card h2.mt { margin-top:20px; }
.card h3 { font-size:15px; margin:0 0 8px; }
.card.row { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.card-head { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }
.card-head h2 { margin:0; }
.grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(190px, 1fr)); gap:12px; }
.two { display:grid; grid-template-columns:repeat(auto-fit, minmax(380px, 1fr)); gap:16px; align-items:start; }
.stat .label, .fit .label { font-size:13px; color:var(--secondary-text-color); }
.stat .value, .fit .value { font-size:26px; font-weight:600; margin:6px 0 4px; line-height:1.15; }
.stat .value .chip { font-size:18px; padding:3px 12px; }
.sub { font-size:13px; color:var(--secondary-text-color); line-height:1.45; }
.banner { border:1px solid var(--divider-color); border-radius:var(--r); padding:12px 16px; display:flex; justify-content:space-between; align-items:center; gap:12px; }
.banner.warn { border-color:#ffa726; background:rgba(255,167,38,.12); }
.banner.err { border-color:#ef5350; background:rgba(239,83,80,.12); }
.btn { background:transparent; color:var(--primary-text-color); border:1px solid var(--divider-color); border-radius:8px; padding:7px 14px; font:inherit; font-size:14px; cursor:pointer; text-decoration:none; white-space:nowrap; }
.btn:hover { background:rgba(127,127,127,.12); }
.btn:disabled { opacity:.4; cursor:default; }
.btn.primary { background:var(--primary-color); border-color:var(--primary-color); color:var(--text-primary-color, #fff); }
.btn.danger { border-color:#ef5350; color:#ef5350; }
.icon { background:none; border:0; color:var(--secondary-text-color); cursor:pointer; font-size:16px; padding:4px 8px; }
.chip { display:inline-block; padding:2px 10px; border-radius:999px; font-size:.8em; font-weight:600; color:#fff; background:#757575; }
.chip.airco { background:${COLORS.airco}; } .chip.cv { background:${COLORS.cv}; } .chip.both { background:${COLORS.both}; }
.muted { color:var(--secondary-text-color); font-size:13px; }
.pad { padding:24px; }
.ranges { display:flex; gap:4px; align-items:center; flex-wrap:wrap; }
.ranges .muted { margin:0 4px 0 10px; }
.pill { border:1px solid var(--divider-color); background:transparent; color:var(--primary-text-color); border-radius:999px; padding:4px 11px; font:inherit; font-size:13px; cursor:pointer; }
.pill.on { background:var(--primary-color); border-color:var(--primary-color); color:var(--text-primary-color, #fff); }
.legend { display:flex; gap:6px 14px; flex-wrap:wrap; margin:12px 0 4px; font-size:13px; align-items:center; }
.legend.small { margin-top:8px; }
.lg { background:none; border:0; color:var(--primary-text-color); font:inherit; font-size:13px; cursor:pointer; display:flex; align-items:center; gap:6px; padding:2px; }
.lg.off { opacity:.35; text-decoration:line-through; }
.lg i, .band-key i.line { width:16px; height:0; border-top:3px solid var(--c); display:inline-block; }
.lg i.dash, .band-key i.line.dash { border-top-style:dashed; }
.band-key { display:flex; align-items:center; gap:6px; color:var(--secondary-text-color); }
.band-key i { width:14px; height:10px; border-radius:2px; display:inline-block; opacity:.55; }
.band-key i.line { opacity:1; border-radius:0; }
.sep { width:1px; height:14px; background:var(--divider-color); }
.chart { width:100%; min-height:200px; }
.chart svg { display:block; }
line.gl { stroke:var(--divider-color); stroke-width:1; }
line.gl.v { stroke-dasharray:2 4; }
.ax { fill:var(--secondary-text-color); font-size:11px; }
.ax.out { fill:${COLORS.outdoor}; }
.nowline { stroke:var(--primary-text-color); stroke-dasharray:3 3; opacity:.6; }
.tipline { stroke:var(--secondary-text-color); stroke-width:1; }
.tipbox { fill:var(--card-background-color, #222); stroke:var(--divider-color); }
.tiptext { fill:var(--primary-text-color); font-size:12px; }
.bars { display:flex; gap:4px; align-items:flex-end; height:220px; padding-top:8px; }
.barcol { flex:1; display:flex; flex-direction:column; align-items:center; height:100%; min-width:0; }
.barval { font-size:10px; color:var(--secondary-text-color); height:14px; white-space:nowrap; overflow:hidden; }
.stack { flex:1; width:100%; max-width:42px; display:flex; flex-direction:column-reverse; }
.stack div { width:100%; border-radius:2px; }
.barlbl { font-size:11px; color:var(--secondary-text-color); margin-top:4px; white-space:nowrap; }
.fit { display:flex; gap:24px; align-items:center; border-left:6px solid #9e9e9e; }
.fit.good { border-left-color:#4caf50; } .fit.ok { border-left-color:#ffa726; } .fit.bad { border-left-color:#ef5350; }
.fit-l { min-width:260px; } .fit-r { flex:1; line-height:1.5; }
.pgrid { display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:12px; }
.pcard { border:1px solid var(--divider-color); border-radius:10px; padding:14px; display:flex; flex-direction:column; gap:6px; }
.phead { display:flex; justify-content:space-between; align-items:center; gap:8px; }
.pbig { font-size:22px; font-weight:600; }
.conf { font-size:11px; padding:2px 8px; border-radius:999px; background:rgba(127,127,127,.18); color:var(--secondary-text-color); white-space:nowrap; }
.conf.low { background:rgba(255,167,38,.2); color:#ffa726; } .conf.medium { background:rgba(66,165,245,.2); color:#42a5f5; } .conf.high { background:rgba(76,175,80,.22); color:#66bb6a; }
.diag { display:flex; gap:12px; align-items:flex-start; padding:9px 0; border-bottom:1px solid var(--divider-color); }
.diag:last-child { border-bottom:0; }
.dicon { width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex:none; color:#fff; background:#9e9e9e; }
.diag.ok .dicon { background:#4caf50; } .diag.warn .dicon { background:#ffa726; } .diag.error .dicon { background:#ef5350; } .diag.info .dicon { background:#42a5f5; }
.diag > div { flex:1; }
.dstat { font-size:12px; color:var(--secondary-text-color); }
.sugg { border:1px solid var(--divider-color); border-radius:10px; padding:12px; margin-bottom:8px; display:flex; flex-direction:column; gap:8px; line-height:1.45; font-size:14px; }
.sugg .actions { margin:0; justify-content:flex-start; gap:8px; }
.kv { display:flex; justify-content:space-between; gap:12px; padding:5px 0; font-size:14px; }
.kv span { color:var(--secondary-text-color); } .kv b { font-weight:500; text-align:right; }
.resets { display:flex; flex-wrap:wrap; gap:8px; }
.actions { margin-top:14px; display:flex; justify-content:flex-end; align-items:center; gap:12px; }
.seg { display:flex; flex-wrap:wrap; gap:8px; }
.seg button { flex:1; min-width:150px; padding:12px; border-radius:10px; border:1px solid var(--divider-color); background:transparent; color:var(--primary-text-color); font:inherit; cursor:pointer; }
.seg button.on { background:var(--primary-color); border-color:var(--primary-color); color:var(--text-primary-color, #fff); font-weight:600; }
.form { display:grid; grid-template-columns:minmax(160px, 260px) auto; gap:10px 16px; align-items:center; margin-top:12px; justify-content:start; }
.field { display:flex; align-items:center; gap:8px; }
.field input { width:96px; padding:7px 10px; border-radius:8px; border:1px solid var(--divider-color); background:var(--secondary-background-color, transparent); color:var(--primary-text-color); font:inherit; }
.field input[type=time] { width:110px; }
.field span { color:var(--secondary-text-color); font-size:13px; }
.feat { display:flex; align-items:center; gap:16px; padding:12px 0; border-bottom:1px solid var(--divider-color); }
.feat:last-child { border-bottom:0; } .feat > div { flex:1; }
.fstate { font-size:12px; padding:2px 10px; border-radius:999px; white-space:nowrap; }
.fstate.on { background:rgba(76,175,80,.2); color:#66bb6a; } .fstate.off { background:rgba(127,127,127,.18); color:var(--secondary-text-color); } .fstate.warn { background:rgba(255,167,38,.2); color:#ffa726; }
.switch { position:relative; display:inline-block; width:42px; height:24px; flex:none; }
.switch.small { width:36px; height:20px; }
.switch input { opacity:0; width:0; height:0; }
.switch span { position:absolute; inset:0; background:rgba(127,127,127,.35); border-radius:999px; transition:.15s; cursor:pointer; }
.switch span:before { content:""; position:absolute; width:18px; height:18px; left:3px; top:3px; background:#fff; border-radius:50%; transition:.15s; }
.switch.small span:before { width:14px; height:14px; }
.switch input:checked + span { background:var(--primary-color); }
.switch input:checked + span:before { transform:translateX(18px); }
.switch.small input:checked + span:before { transform:translateX(16px); }
.days { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px; }
.daychip { display:flex; flex-direction:column; align-items:center; min-width:66px; padding:6px 10px; border-radius:10px; border:1px solid var(--divider-color); background:transparent; color:var(--primary-text-color); font:inherit; cursor:pointer; }
.daychip small { font-size:11px; color:var(--secondary-text-color); }
.daychip.weekend { border-color:${COLORS.both}; background:rgba(171,71,188,.12); }
.check { display:flex; align-items:center; gap:8px; font-size:14px; margin:0 0 12px; }
.profiles { display:grid; grid-template-columns:repeat(auto-fit, minmax(440px, 1fr)); gap:16px; }
.profile { border:1px solid var(--divider-color); border-radius:10px; padding:12px; }
.blocks { display:flex; flex-direction:column; gap:8px; margin-bottom:10px; }
.block { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.block.disabled .field { opacity:.45; }
select { padding:7px 10px; border-radius:8px; border:1px solid var(--divider-color); background:var(--secondary-background-color, transparent); color:var(--primary-text-color); font:inherit; }
.card.mt { margin-top:16px; } h3.mt2 { margin-top:18px; }
.chart.small { min-height:120px; }
.timeline { display:flex; flex-direction:column; }
.act { display:grid; grid-template-columns:92px 18px 1fr auto; gap:10px; align-items:start; padding:8px 0; }
.act .when { font-size:13px; color:var(--secondary-text-color); padding-top:2px; white-space:nowrap; }
.act .dotline { position:relative; height:100%; display:flex; justify-content:center; }
.act .dotline:before { content:""; position:absolute; top:0; bottom:-16px; width:2px; background:var(--divider-color); }
.act:last-child .dotline:before { display:none; }
.adot { position:relative; width:12px; height:12px; border-radius:50%; margin-top:4px; background:#757575; }
.adot.airco { background:${COLORS.airco}; } .adot.cv { background:${COLORS.cv}; } .adot.both { background:${COLORS.both}; }
.act .what b { font-weight:500; font-size:14px; }
.acost { font-size:13px; color:var(--secondary-text-color); white-space:nowrap; padding-top:2px; }
.splitbar { display:flex; height:14px; border-radius:7px; overflow:hidden; margin:10px 0 6px; background:rgba(127,127,127,.15); }
.splitlbl { display:flex; gap:16px; flex-wrap:wrap; font-size:13px; color:var(--secondary-text-color); margin-bottom:6px; }
.splitlbl i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; }
.tbl { width:100%; border-collapse:collapse; font-size:14px; margin-top:10px; }
.tbl td { padding:10px 8px; border-bottom:1px solid var(--divider-color); color:var(--primary-text-color); }
.tbl tr:last-child td { border-bottom:0; }
.tbl.scen td { vertical-align:top; }
.tbl.scen td.num { text-align:right; white-space:nowrap; font-weight:600; }
.save { color:#66bb6a; } .more { color:#ef5350; }
@media (max-width: 700px) {
  .toolbar { flex-wrap:wrap; height:auto; padding:8px; gap:8px; }
  .status { display:none; }
  .content { padding:8px; }
  .stat .value { font-size:21px; }
  .bars .barval { display:none; }
  .fit { flex-direction:column; align-items:flex-start; }
  .two, .profiles { grid-template-columns:1fr; }
}
`;

customElements.define("climator-panel", ClimatorPanel);
