/* Climator sidebar panel — plain web component, no external dependencies. */

const E = {
  climate: "climate.climator",
  mode: "select.climator_mode",
  strategy: "sensor.climator_strategy",
  phase: "sensor.climator_phase",
  reason: "sensor.climator_reason",
  preheat: "sensor.climator_preheat_start",
  learning: "sensor.climator_learning",
  comfortTemp: "number.climator_comfort_temp",
  ecoTemp: "number.climator_eco_temp",
  comfortStart: "time.climator_comfort_start",
  comfortEnd: "time.climator_comfort_end",
  priceKwh: "number.climator_price_kwh",
  priceGas: "number.climator_price_gas",
  costToday: (w) => `sensor.climator_cost_today_${w}`,
  costTotal: (w) => `sensor.climator_cost_${w}`,
  maintain: (w) => `sensor.climator_maintain_cost_${w}`,
  rate: (w) => `sensor.climator_heat_rate_${w}`,
  heatCost: (w) => `sensor.climator_heat_cost_${w}`,
};

const COLORS = {
  room: "#42a5f5",
  target: "#ffa726",
  outdoor: "#9e9e9e",
  airco: "#26c6da",
  cv: "#ef5350",
  both: "#ab47bc",
};

const I18N = {
  en: {
    tabs: { status: "Status", costs: "Costs", learning: "Learning", settings: "Settings" },
    modes: { learn_only: "Learn only", manual: "Fixed temperature", schedule: "Schedule + preheat" },
    strategy: { airco: "Air conditioner", cv: "Boiler", both: "Both", off: "Off" },
    phase: { heat_up: "Heating up", maintain: "Keeping warm", off: "Off" },
    reason: {
      off: "Off", sensor_unavailable: "Sensor unavailable", no_source: "No heat source available",
      comfort: "Comfort period", eco: "Eco period", preheat: "Preheating", manual: "Fixed temperature",
      learn_only: "Learn only", manual_override: "Paused after manual change",
    },
    learnBanner: "Learn only — Climator watches and learns, but does not change the air conditioner or thermostat.",
    enableSchedule: "Turn on schedule",
    pausedBanner: (t, e) => `Paused until ${t} because ${e} was changed manually. Climator keeps learning.`,
    resume: "Resume now",
    unavailable: "Climator entities not found. Is the integration set up?",
    room: "Room", outdoor: "Outdoor", target: "Target", now: "Now", strategyNow: "Heat source",
    preheatStart: "Preheat starts", nextComfort: "Comfort from", costToday: "Heating cost today",
    keepWarm: "Keep warm now", perHour: "/h", aircoSet: "Air conditioner setpoint", cvSet: "Boiler setpoint",
    temperature: "Temperature (°C)", past: "Past", ahead: "Ahead", plan: "Plan",
    noHistory: "No history yet.", costPerDay: "Heating cost per day", costPerMonth: "Heating cost per month",
    today: "Today", yesterday: "Yesterday", last7: "Last 7 days", last30: "Last 30 days", thisMonth: "This month",
    total: "Total", noStats: "No statistics yet — they appear after the first full hour.",
    cheapestHeat: "Cheapest to heat up now", cheapestKeep: "Cheapest to keep warm now",
    rate: "Heat-up rate", costPerDeg: "Cost per °C", keepCost: "Keep warm",
    learnedAt: (t) => `At the current outdoor temperature (${t} °C)`,
    estimated: "estimate", learned: "learned",
    table: "Learned data per outdoor temperature", source: "Source", outdoorBand: "Outdoor",
    samples: "Samples", heatKeep: "heat / keep", perHourK: "€ per h per K",
    nothingLearned: "Nothing learned yet. Climator learns from every heating period, also in Learn only mode.",
    coverage: "Coverage", lastEvent: "Last learned", reset: "Reset learning data",
    resetConfirm: "Delete all learned data? This cannot be undone.",
    mode: "Mode", schedule: "Schedule", comfortTemp: "Comfort temperature", ecoTemp: "Eco temperature",
    from: "From", until: "Until", prices: "Energy prices", electricity: "Electricity", gas: "Gas",
    advanced: "Advanced settings (entities, offsets, pause time)", open: "Open",
    pricesHint: "All decisions and costs use these prices.",
  },
  nl: {
    tabs: { status: "Status", costs: "Kosten", learning: "Leren", settings: "Instellingen" },
    modes: { learn_only: "Alleen leren", manual: "Vaste temperatuur", schedule: "Schema + voorverwarmen" },
    strategy: { airco: "Airco", cv: "CV", both: "Beide", off: "Uit" },
    phase: { heat_up: "Opwarmen", maintain: "Op temperatuur houden", off: "Uit" },
    reason: {
      off: "Uit", sensor_unavailable: "Sensor onbeschikbaar", no_source: "Geen warmtebron beschikbaar",
      comfort: "Comfortperiode", eco: "Ecoperiode", preheat: "Voorverwarmen", manual: "Vaste temperatuur",
      learn_only: "Alleen leren", manual_override: "Gepauzeerd na handmatige bediening",
    },
    learnBanner: "Alleen leren — Climator kijkt mee en leert, maar wijzigt de airco en thermostaat niet.",
    enableSchedule: "Schema inschakelen",
    pausedBanner: (t, e) => `Gepauzeerd tot ${t} omdat ${e} handmatig is bediend. Climator blijft leren.`,
    resume: "Nu hervatten",
    unavailable: "Climator-entiteiten niet gevonden. Is de integratie ingesteld?",
    room: "Kamer", outdoor: "Buiten", target: "Doel", now: "Nu", strategyNow: "Warmtebron",
    preheatStart: "Voorverwarmen start", nextComfort: "Comfort vanaf", costToday: "Stookkosten vandaag",
    keepWarm: "Warm houden nu", perHour: "/u", aircoSet: "Setpoint airco", cvSet: "Setpoint CV",
    temperature: "Temperatuur (°C)", past: "Verleden", ahead: "Vooruit", plan: "Plan",
    noHistory: "Nog geen geschiedenis.", costPerDay: "Stookkosten per dag", costPerMonth: "Stookkosten per maand",
    today: "Vandaag", yesterday: "Gisteren", last7: "Laatste 7 dagen", last30: "Laatste 30 dagen", thisMonth: "Deze maand",
    total: "Totaal", noStats: "Nog geen statistieken — die verschijnen na het eerste volle uur.",
    cheapestHeat: "Goedkoopst opwarmen nu", cheapestKeep: "Goedkoopst warm houden nu",
    rate: "Opwarmsnelheid", costPerDeg: "Kosten per °C", keepCost: "Warm houden",
    learnedAt: (t) => `Bij de huidige buitentemperatuur (${t} °C)`,
    estimated: "schatting", learned: "geleerd",
    table: "Geleerde data per buitentemperatuur", source: "Bron", outdoorBand: "Buiten",
    samples: "Metingen", heatKeep: "opwarmen / warm houden", perHourK: "€ per u per K",
    nothingLearned: "Nog niets geleerd. Climator leert van elke stookperiode, ook in de stand Alleen leren.",
    coverage: "Dekking", lastEvent: "Laatst geleerd", reset: "Leerdata wissen",
    resetConfirm: "Alle geleerde data wissen? Dit kan niet ongedaan worden.",
    mode: "Modus", schedule: "Schema", comfortTemp: "Comforttemperatuur", ecoTemp: "Ecotemperatuur",
    from: "Vanaf", until: "Tot", prices: "Energieprijzen", electricity: "Stroom", gas: "Gas",
    advanced: "Geavanceerde instellingen (entiteiten, offsets, pauzetijd)", open: "Openen",
    pricesHint: "Alle beslissingen en kosten gebruiken deze prijzen.",
  },
};

const BIN_LABELS = ["<-5", "-5..0", "0..5", "5..10", "10..15", ">15"];
const STRATS = ["airco", "cv", "both"];

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
      this._loadHistory();
      this._timer = setInterval(() => { this._loadHistory(); if (this._tab === "costs") this._loadStats(); }, 5 * 60 * 1000);
    }
    const sig = this._signature();
    if (sig !== this._lastSig) {
      this._lastSig = sig;
      this._render();
    }
  }

  disconnectedCallback() {
    clearInterval(this._timer);
    this._ro?.disconnect();
  }

  get t() {
    const lang = (this._hass?.locale?.language || this._hass?.language || "en").slice(0, 2);
    return I18N[lang] || I18N.en;
  }

  get lang() { return this._hass?.locale?.language || this._hass?.language || "en"; }

  _st(id) { return this._hass?.states[id]; }
  _num(id) { const s = this._st(id); const v = s ? parseFloat(s.state) : NaN; return Number.isFinite(v) ? v : null; }

  _signature() {
    const ids = Object.values(E).filter((v) => typeof v === "string");
    STRATS.forEach((s) => ids.push(E.rate(s), E.heatCost(s)));
    ["airco", "cv", "total"].forEach((w) => ids.push(E.costToday(w)));
    ["airco", "cv"].forEach((w) => ids.push(E.maintain(w)));
    const src = this._st(E.climate)?.attributes?.source_entities || {};
    Object.values(src).forEach((i) => i && ids.push(i));
    return ids.map((i) => this._st(i)?.last_updated || "-").join("|");
  }

  // ---------------------------------------------------------------- formatting
  _fmtNum(v, d = 1) {
    if (v === null || v === undefined || Number.isNaN(v)) return "–";
    return new Intl.NumberFormat(this.lang, { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
  }
  _eur(v, d = 2) {
    if (v === null || v === undefined || Number.isNaN(v)) return "–";
    return new Intl.NumberFormat(this.lang, { style: "currency", currency: "EUR", minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
  }
  _time(d) {
    return d.toLocaleTimeString(this.lang, { hour: "2-digit", minute: "2-digit" });
  }

  // ---------------------------------------------------------------- services
  _call(domain, service, data) { return this._hass.callService(domain, service, data); }

  // ---------------------------------------------------------------- data
  async _loadHistory() {
    if (!this._hass) return;
    const src = this._st(E.climate)?.attributes?.source_entities || {};
    const ids = [E.climate, E.strategy, src.room, src.outdoor, src.airco, src.cv].filter(Boolean);
    const start = new Date(Date.now() - this._past * 3600 * 1000);
    try {
      const res = await this._hass.callWS({
        type: "history/history_during_period",
        start_time: start.toISOString(),
        entity_ids: ids,
        minimal_response: false,
        no_attributes: false,
        significant_changes_only: false,
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
        this._hass.callWS({ type: "recorder/statistics_during_period", start_time: dayStart.toISOString(), statistic_ids: ids, period: "day", types: ["change"] }),
        this._hass.callWS({ type: "recorder/statistics_during_period", start_time: monthStart.toISOString(), statistic_ids: ids, period: "month", types: ["change"] }),
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
    this._ro = new ResizeObserver(() => { if (this._tab === "status") this._drawChart(); });
  }

  _render(force = false) {
    if (!this.shadowRoot.querySelector(".content")) return;
    const t = this.t;
    // tabs + status line
    this.shadowRoot.querySelector(".tabs").innerHTML = Object.entries(t.tabs).map(
      ([k, v]) => `<button class="tab ${k === this._tab ? "active" : ""}" data-tab="${k}">${v}</button>`).join("");
    const mode = this._st(E.mode)?.state;
    const reason = this._st(E.reason)?.state;
    const ok = !!this._st(E.climate) && this._st(E.climate).state !== "unavailable";
    this.shadowRoot.querySelector(".status").innerHTML = ok
      ? `<span class="dot ${reason === "manual_override" ? "warn" : "ok"}"></span>${esc(t.modes[mode] || mode || "")}`
      : `<span class="dot err"></span>`;

    const content = this.shadowRoot.querySelector(".content");
    // don't wipe settings inputs while the user is typing
    if (!force && this._tab === "settings" && this.shadowRoot.activeElement?.tagName === "INPUT") return;
    if (!ok) { content.innerHTML = `<div class="banner err">${t.unavailable}</div>`; return; }
    const fn = { status: this._status, costs: this._costs, learning: this._learning, settings: this._settings }[this._tab];
    content.innerHTML = fn.call(this);
    if (this._tab === "status") {
      this._ro.disconnect();
      const box = this.shadowRoot.querySelector(".chart");
      if (box) this._ro.observe(box);
      this._drawChart();
    }
  }

  _banner() {
    const t = this.t;
    const mode = this._st(E.mode)?.state;
    const reason = this._st(E.reason)?.state;
    if (mode === "learn_only") {
      return `<div class="banner warn"><div>${esc(t.learnBanner)}</div>
        <button class="btn" data-action="mode" data-value="schedule">${t.enableSchedule}</button></div>`;
    }
    if (reason === "manual_override") {
      const a = this._st(E.reason).attributes;
      const until = a.override_until ? this._time(new Date(a.override_until)) : "?";
      const ent = this._st(a.override_entity)?.attributes?.friendly_name || a.override_entity || "?";
      return `<div class="banner warn"><div>${esc(t.pausedBanner(until, ent))}</div>
        <button class="btn" data-action="mode" data-value="${esc(mode)}">${t.resume}</button></div>`;
    }
    return "";
  }

  _card(label, value, sub = "", cls = "") {
    return `<div class="card stat ${cls}"><div class="label">${label}</div><div class="value">${value}</div>${sub ? `<div class="sub">${sub}</div>` : ""}</div>`;
  }

  // ---------------------------------------------------------------- status tab
  _status() {
    const t = this.t;
    const c = this._st(E.climate);
    const a = c.attributes;
    const src = a.source_entities || {};
    const strategy = this._st(E.strategy)?.state || "off";
    const phase = this._st(E.phase)?.state || "off";
    const reason = this._st(E.reason)?.state || "off";
    const pre = this._st(E.preheat)?.state;
    const preDate = pre && !["unknown", "unavailable"].includes(pre) ? new Date(pre) : null;
    const comfortStart = (this._st(E.comfortStart)?.state || "").slice(0, 5);
    const keepA = this._num(E.maintain("airco"));
    const keepC = this._num(E.maintain("cv"));
    const airco = this._st(src.airco);
    const cv = this._st(src.cv);
    const devSub = (s) => s ? `${esc(this._hass.formatEntityState ? this._hass.formatEntityState(s) : s.state)} · ${this._fmtNum(s.attributes.temperature)} °C` : "–";

    return `${this._banner()}
      <div class="grid">
        ${this._card(t.room, `${this._fmtNum(a.current_temperature)} °C`, `${t.target} ${this._fmtNum(a.temperature)} °C`)}
        ${this._card(t.outdoor, `${this._fmtNum(a.outdoor_temperature)} °C`)}
        ${this._card(t.strategyNow, `<span class="chip ${strategy}">${t.strategy[strategy] || strategy}</span>`, `${t.phase[phase] || phase} · ${t.reason[reason] || reason}`)}
        ${this._card(preDate ? t.preheatStart : t.nextComfort, preDate ? this._time(preDate) : esc(comfortStart || "–"), preDate ? `${t.nextComfort} ${esc(comfortStart)}` : "")}
        ${this._card(t.costToday, this._eur(this._num(E.costToday("total"))), `${t.strategy.airco} ${this._eur(this._num(E.costToday("airco")))} · ${t.strategy.cv} ${this._eur(this._num(E.costToday("cv")))}`)}
        ${this._card(t.keepWarm, `${this._eur(Math.min(keepA ?? Infinity, keepC ?? Infinity), 3)}${t.perHour}`, `${t.strategy.airco} ${this._eur(keepA, 3)} · ${t.strategy.cv} ${this._eur(keepC, 3)}`)}
        ${this._card(t.strategy.airco, `${this._fmtNum(airco?.attributes?.current_temperature)} °C`, devSub(airco))}
        ${this._card(t.strategy.cv, `${this._fmtNum(cv?.attributes?.current_temperature)} °C`, devSub(cv))}
      </div>
      <div class="card">
        <div class="card-head">
          <h2>${t.temperature}</h2>
          <div class="ranges">
            <span class="muted">${t.past}</span>
            ${[6, 12, 24, 72, 168].map((h) => `<button class="pill ${h === this._past ? "on" : ""}" data-action="past" data-value="${h}">${h < 48 ? h + (this.lang.startsWith("nl") ? "u" : "h") : h / 24 + "d"}</button>`).join("")}
            <span class="muted">${t.ahead}</span>
            ${[0, 12, 24].map((h) => `<button class="pill ${h === this._ahead ? "on" : ""}" data-action="ahead" data-value="${h}">${h ? h + (this.lang.startsWith("nl") ? "u" : "h") : "–"}</button>`).join("")}
          </div>
        </div>
        <div class="legend">${this._legend()}</div>
        <div class="chart"></div>
      </div>`;
  }

  _legend() {
    const t = this.t;
    const items = [
      ["room", t.room, COLORS.room], ["target", t.target, COLORS.target], ["outdoor", t.outdoor, COLORS.outdoor],
      ["aircoSet", t.aircoSet, COLORS.airco], ["cvSet", t.cvSet, COLORS.cv],
    ];
    const bands = STRATS.map((s) => `<span class="band-key"><i style="background:${COLORS[s]}"></i>${t.strategy[s]}</span>`).join("");
    return items.map(([k, label, col]) => `<button class="lg ${this._hidden.has(k) ? "off" : ""}" data-action="toggle" data-value="${k}"><i style="background:${col}"></i>${label}</button>`).join("") + `<span class="sep"></span>${bands}`;
  }

  _series() {
    const h = this._history;
    if (!h) return null;
    const { res, src } = h;
    const ts = (e) => (e.lu ?? e.lc ?? 0) * 1000;
    const num = (id, attr) => (res[id] || []).map((e) => {
      const v = attr ? e.a?.[attr] : e.s;
      return [ts(e), v === undefined || v === null ? null : parseFloat(v)];
    }).filter(([, v]) => v === null || Number.isFinite(v));
    // attributes are only sent when they change; carry them forward
    const attrSeries = (id, attr, onlyWhen) => {
      let last = null;
      return (res[id] || []).map((e) => {
        if (e.a && attr in e.a) last = e.a[attr];
        const v = onlyWhen && !onlyWhen(e.s) ? null : last;
        return [ts(e), v === null || v === undefined ? null : parseFloat(v)];
      });
    };
    const heating = (s) => ["heat", "heat_cool", "auto"].includes(s);
    return {
      room: num(src.room),
      outdoor: num(src.outdoor),
      target: attrSeries(E.climate, "temperature"),
      aircoSet: attrSeries(src.airco, "temperature", heating),
      cvSet: attrSeries(src.cv, "temperature", (s) => s && s !== "off"),
      strategy: (res[E.strategy] || []).map((e) => [ts(e), e.s]),
    };
  }

  _plan(now, end) {
    // Expected target for the coming hours, from the schedule entities.
    const mode = this._st(E.mode)?.state;
    const climate = this._st(E.climate);
    if (!climate || mode === "learn_only") return [];
    if (mode === "manual") return [[now, climate.attributes.temperature], [end, climate.attributes.temperature]];
    const comfort = this._num(E.comfortTemp);
    const eco = this._num(E.ecoTemp);
    const parse = (s) => (s || "00:00").split(":").map(Number);
    const [sh, sm] = parse(this._st(E.comfortStart)?.state);
    const [eh, em] = parse(this._st(E.comfortEnd)?.state);
    const pre = this._st(E.preheat)?.state;
    const preT = pre && !["unknown", "unavailable"].includes(pre) ? new Date(pre).getTime() : null;
    const inWindow = (d) => {
      const m = d.getHours() * 60 + d.getMinutes();
      const s = sh * 60 + sm, e = eh * 60 + em;
      if (s === e) return false;
      return s < e ? m >= s && m < e : m >= s || m < e;
    };
    let nextStart = null;
    const pts = [];
    for (let t = now; t <= end; t += 5 * 60 * 1000) {
      const d = new Date(t);
      let target = inWindow(d) ? comfort : eco;
      if (!inWindow(d) && preT && t >= preT) {
        if (nextStart === null) {
          const n = new Date(preT); n.setHours(sh, sm, 0, 0);
          if (n.getTime() <= preT) n.setDate(n.getDate() + 1);
          nextStart = n.getTime();
        }
        if (t < nextStart) target = comfort;
      }
      pts.push([t, target]);
    }
    return pts;
  }

  _drawChart() {
    const box = this.shadowRoot.querySelector(".chart");
    if (!box) return;
    const s = this._series();
    if (!s) { box.innerHTML = `<div class="muted pad">…</div>`; return; }
    const W = Math.max(box.clientWidth, 320);
    const H = 320;
    const m = { l: 40, r: 44, t: 16, b: 28 };
    const now = Date.now();
    const x0 = now - this._past * 3600e3;
    const x1 = now + this._ahead * 3600e3;
    const c = this._st(E.climate).attributes;
    const src = this._history.src;

    // append live values at "now"
    const live = (arr, v) => { if (v !== null && v !== undefined && Number.isFinite(+v)) arr.push([now, +v]); return arr; };
    live(s.room, this._num(src.room));
    live(s.outdoor, this._num(src.outdoor));
    live(s.target, c.temperature);
    s.strategy.push([now, this._st(E.strategy)?.state]);
    const plan = this._ahead ? this._plan(now, x1) : [];

    const left = [...s.room, ...s.target, ...(this._hidden.has("aircoSet") ? [] : s.aircoSet), ...(this._hidden.has("cvSet") ? [] : s.cvSet), ...plan]
      .filter(([tt, v]) => v !== null && tt >= x0 - 3600e3).map(([, v]) => v);
    if (!left.length) { box.innerHTML = `<div class="muted pad">${this.t.noHistory}</div>`; return; }
    let y0 = Math.floor(Math.min(...left) - 0.5), y1 = Math.ceil(Math.max(...left) + 0.5);
    if (y1 - y0 < 4) { y0 -= 1; y1 = y0 + 5; }
    const outs = s.outdoor.filter(([, v]) => v !== null).map(([, v]) => v);
    let o0 = outs.length ? Math.floor(Math.min(...outs) - 1) : 0, o1 = outs.length ? Math.ceil(Math.max(...outs) + 1) : 10;
    if (o1 - o0 < 4) o1 = o0 + 4;

    const X = (tt) => m.l + ((tt - x0) / (x1 - x0)) * (W - m.l - m.r);
    const Y = (v) => m.t + (1 - (v - y0) / (y1 - y0)) * (H - m.t - m.b);
    const YO = (v) => m.t + (1 - (v - o0) / (o1 - o0)) * (H - m.t - m.b);

    const path = (pts, yf, step) => {
      let d = "", prev = null;
      for (const [tt, v] of pts) {
        const ct = Math.max(tt, x0);
        if (tt < x0 - 1 && pts.length > 1) { prev = [ct, v]; continue; }
        if (v === null) { prev = null; continue; }
        const px = X(ct).toFixed(1), py = yf(v).toFixed(1);
        if (prev === null) d += `M${px},${py}`;
        else d += step ? `H${px}V${py}` : `L${px},${py}`;
        prev = [ct, v];
      }
      // carry the first value that started before the window
      return d;
    };
    const clipStart = (pts) => {
      // keep last point before x0 (as x0) so step lines start at the left edge
      const before = pts.filter(([tt]) => tt < x0);
      const after = pts.filter(([tt]) => tt >= x0);
      return before.length ? [[x0, before[before.length - 1][1]], ...after] : after;
    };

    // strategy bands
    let bands = "";
    const strat = clipStart(s.strategy);
    for (let i = 0; i < strat.length; i++) {
      const [tt, v] = strat[i];
      const te = i + 1 < strat.length ? strat[i + 1][0] : now;
      if (COLORS[v] && v !== "off") {
        bands += `<rect x="${X(tt).toFixed(1)}" y="${m.t}" width="${Math.max(X(te) - X(tt), 0).toFixed(1)}" height="${H - m.t - m.b}" fill="${COLORS[v]}" opacity="0.13"/>`;
      }
    }

    // grid + axes
    let grid = "";
    for (let v = y0; v <= y1; v++) {
      grid += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" class="grid"/><text x="${m.l - 6}" y="${Y(v) + 4}" class="ax" text-anchor="end">${v}°</text>`;
    }
    const ostep = o1 - o0 > 12 ? 4 : 2;
    for (let v = Math.ceil(o0 / ostep) * ostep; v <= o1; v += ostep) {
      grid += `<text x="${W - m.r + 6}" y="${YO(v) + 4}" class="ax out">${v}°</text>`;
    }
    const span = x1 - x0;
    const stepH = span > 96 * 3600e3 ? 24 : span > 36 * 3600e3 ? 6 : span > 14 * 3600e3 ? 3 : 1;
    const first = new Date(x0); first.setMinutes(0, 0, 0);
    for (let tt = first.getTime(); tt <= x1; tt += 3600e3) {
      const d = new Date(tt);
      if (d.getHours() % stepH !== 0 || tt < x0) continue;
      const label = stepH === 24 ? d.toLocaleDateString(this.lang, { weekday: "short", day: "numeric" }) : this._time(d);
      grid += `<line x1="${X(tt)}" x2="${X(tt)}" y1="${m.t}" y2="${H - m.b}" class="grid v"/><text x="${X(tt)}" y="${H - 8}" class="ax" text-anchor="middle">${label}</text>`;
    }

    const line = (key, pts, yf, color, opts = "") => this._hidden.has(key) ? "" :
      `<path d="${path(clipStart(pts), yf, opts.includes("step"))}" fill="none" stroke="${color}" stroke-width="${opts.includes("thin") ? 1.5 : 2.2}" ${opts.includes("dash") ? 'stroke-dasharray="5 4"' : ""} stroke-linejoin="round"/>`;

    // future
    let future = "";
    if (this._ahead) {
      future += `<rect x="${X(now)}" y="${m.t}" width="${X(x1) - X(now)}" height="${H - m.t - m.b}" class="future"/>`;
      if (plan.length && !this._hidden.has("target")) {
        future += `<path d="${path(plan, Y, true)}" fill="none" stroke="${COLORS.target}" stroke-width="2.2" stroke-dasharray="6 4" opacity="0.9"/>`;
      }
      const pre = this._st(E.preheat)?.state;
      if (pre && !["unknown", "unavailable"].includes(pre)) {
        const pt = new Date(pre).getTime();
        if (pt > now && pt < x1) {
          future += `<line x1="${X(pt)}" x2="${X(pt)}" y1="${m.t}" y2="${H - m.b}" stroke="${COLORS.target}" stroke-dasharray="2 3"/>
            <circle cx="${X(pt)}" cy="${m.t + 6}" r="5" fill="${COLORS.target}"><title>${this.t.preheatStart} ${this._time(new Date(pt))}</title></circle>`;
        }
      }
    }

    box.innerHTML = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      ${bands}${grid}${future}
      ${line("outdoor", s.outdoor, YO, COLORS.outdoor, "thin")}
      ${line("aircoSet", s.aircoSet, Y, COLORS.airco, "step dash thin")}
      ${line("cvSet", s.cvSet, Y, COLORS.cv, "step dash thin")}
      ${line("target", s.target, Y, COLORS.target, "step")}
      ${line("room", s.room, Y, COLORS.room)}
      <line x1="${X(now)}" x2="${X(now)}" y1="${m.t}" y2="${H - m.b}" class="nowline"/>
      <text x="${X(now)}" y="${m.t - 4}" class="ax" text-anchor="middle">${this.t.now.toUpperCase()}</text>
      <rect class="hover" x="${m.l}" y="${m.t}" width="${W - m.l - m.r}" height="${H - m.t - m.b}" fill="transparent"/>
      <g class="tip" style="display:none"><line class="tipline" y1="${m.t}" y2="${H - m.b}"/><rect class="tipbox" rx="6"/><text class="tiptext"></text></g>
    </svg>`;

    // tooltip
    const svg = box.querySelector("svg");
    const tip = svg.querySelector(".tip");
    const valueAt = (pts, tt) => { let v = null; for (const [pt, pv] of pts) { if (pt <= tt) v = pv; else break; } return v; };
    svg.querySelector(".hover").addEventListener("mousemove", (ev) => {
      const r = svg.getBoundingClientRect();
      const px = ev.clientX - r.left;
      const tt = x0 + ((px - m.l) / (W - m.l - m.r)) * (x1 - x0);
      const isFuture = tt > now;
      const rows = isFuture
        ? [[this.t.plan, valueAt(plan, tt)]]
        : [[this.t.room, valueAt(s.room, tt)], [this.t.target, valueAt(s.target, tt)], [this.t.outdoor, valueAt(s.outdoor, tt)]];
      const st = isFuture ? null : valueAt(s.strategy, tt);
      const lines = [this._time(new Date(tt)), ...rows.filter(([, v]) => v !== null).map(([k, v]) => `${k}: ${this._fmtNum(v)} °C`)];
      if (st) lines.push(this.t.strategy[st] || st);
      const text = tip.querySelector(".tiptext");
      text.innerHTML = lines.map((l, i) => `<tspan x="0" dy="${i ? 16 : 0}">${esc(l)}</tspan>`).join("");
      tip.style.display = "";
      tip.querySelector(".tipline").setAttribute("x1", px);
      tip.querySelector(".tipline").setAttribute("x2", px);
      const bw = 170, bh = lines.length * 16 + 12;
      const bx = px + bw + 12 > W ? px - bw - 8 : px + 8;
      const bx2 = tip.querySelector(".tipbox");
      bx2.setAttribute("x", bx); bx2.setAttribute("y", m.t + 4); bx2.setAttribute("width", bw); bx2.setAttribute("height", bh);
      text.setAttribute("transform", `translate(${bx + 10},${m.t + 20})`);
      text.querySelectorAll("tspan").forEach((ts) => ts.setAttribute("x", 0));
    });
    svg.querySelector(".hover").addEventListener("mouseleave", () => { tip.style.display = "none"; });
  }

  // ---------------------------------------------------------------- costs tab
  _costs() {
    const t = this.t;
    if (!this._stats) { this._loadStats(); }
    const day = this._stats?.day || {};
    const month = this._stats?.month || {};
    const A = E.costTotal("airco"), C = E.costTotal("cv");
    const byKey = (rows) => Object.fromEntries((rows || []).map((r) => [new Date(r.start).toDateString(), Math.max(r.change || 0, 0)]));
    const dA = byKey(day[A]), dC = byKey(day[C]);
    const days = [];
    const today = new Date(); today.setHours(0, 0, 0, 0);
    for (let i = 29; i >= 0; i--) {
      const d = new Date(today); d.setDate(d.getDate() - i);
      const k = d.toDateString();
      days.push({ d, a: dA[k] || 0, c: dC[k] || 0 });
    }
    // today from live sensors (statistics lag up to an hour)
    days[29].a = this._num(E.costToday("airco")) ?? days[29].a;
    days[29].c = this._num(E.costToday("cv")) ?? days[29].c;
    const mA = byKey(month[A]), mC = byKey(month[C]);
    const months = [];
    for (let i = 11; i >= 0; i--) {
      const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
      const k = d.toDateString();
      months.push({ d, a: mA[k] || 0, c: mC[k] || 0 });
    }
    const sum = (arr) => arr.reduce((s, x) => s + x.a + x.c, 0);
    const monthNow = days.filter((x) => x.d.getMonth() === today.getMonth() && x.d.getFullYear() === today.getFullYear());
    const hasStats = Object.keys(day).length > 0;

    return `<div class="grid">
        ${this._card(t.today, this._eur(days[29].a + days[29].c), `${t.strategy.airco} ${this._eur(days[29].a)} · ${t.strategy.cv} ${this._eur(days[29].c)}`)}
        ${this._card(t.yesterday, this._eur(days[28].a + days[28].c), `${t.strategy.airco} ${this._eur(days[28].a)} · ${t.strategy.cv} ${this._eur(days[28].c)}`)}
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
    return `<div class="bars">${rows.map((r) => {
      const h = (v) => `${((v / max) * 100).toFixed(1)}%`;
      return `<div class="barcol" title="${esc(title(r))}: ${this._eur(r.a + r.c)} (${this.t.strategy.airco} ${this._eur(r.a)}, ${this.t.strategy.cv} ${this._eur(r.c)})">
        <div class="barval">${r.a + r.c > 0 ? this._eur(r.a + r.c, r.a + r.c < 10 ? 2 : 0) : ""}</div>
        <div class="stack"><div style="height:${h(r.c)};background:${COLORS.cv}"></div><div style="height:${h(r.a)};background:${COLORS.airco}"></div></div>
        <div class="barlbl">${esc(label(r))}</div></div>`;
    }).join("")}</div>
    <div class="legend small"><span class="band-key"><i style="background:${COLORS.airco}"></i>${this.t.strategy.airco}</span><span class="band-key"><i style="background:${COLORS.cv}"></i>${this.t.strategy.cv}</span></div>`;
  }

  // ---------------------------------------------------------------- learning tab
  _learning() {
    const t = this.t;
    const out = this._st(E.climate).attributes.outdoor_temperature;
    const rows = STRATS.map((s) => ({
      s,
      rate: this._num(E.rate(s)),
      learned: this._st(E.rate(s))?.attributes?.learned,
      cost: this._num(E.heatCost(s)),
      keep: s === "both" ? null : this._num(E.maintain(s)),
    }));
    const valid = rows.filter((r) => r.cost !== null);
    const cheapHeat = valid.length ? valid.reduce((a, b) => (b.cost < a.cost ? b : a)) : null;
    const keeps = rows.filter((r) => r.keep !== null);
    const cheapKeep = keeps.length ? keeps.reduce((a, b) => (b.keep < a.keep ? b : a)) : null;
    const L = this._st(E.learning);
    const table = L?.attributes?.table || [];

    const coverage = STRATS.map((s) => `<tr><th>${t.strategy[s]}</th>${BIN_LABELS.map((b) => {
      const r = table.find((x) => x.strategy === s && x.outdoor === b);
      const n = r ? r.heat_samples + r.maintain_samples : 0;
      const lvl = n === 0 ? 0 : n < 3 ? 1 : n < 10 ? 2 : 3;
      return `<td class="cov l${lvl}" title="${n} ${t.samples.toLowerCase()}">${n || ""}</td>`;
    }).join("")}</tr>`).join("");

    return `<div class="grid">
        ${this._card(t.cheapestHeat, cheapHeat ? `<span class="chip ${cheapHeat.s}">${t.strategy[cheapHeat.s]}</span>` : "–", cheapHeat ? `${this._eur(cheapHeat.cost, 3)} / °C` : "")}
        ${this._card(t.cheapestKeep, cheapKeep ? `<span class="chip ${cheapKeep.s}">${t.strategy[cheapKeep.s]}</span>` : "–", cheapKeep ? `${this._eur(cheapKeep.keep, 3)}${t.perHour}` : "")}
        ${this._card(t.samples, esc(L?.state ?? "0"), `${t.lastEvent}: ${esc(L?.attributes?.last_event || "–")}`)}
      </div>
      <div class="card"><h2>${t.learnedAt(this._fmtNum(out))}</h2>
        <table class="tbl"><thead><tr><th>${t.source}</th><th>${t.rate}</th><th>${t.costPerDeg}</th><th>${t.keepCost}</th><th></th></tr></thead><tbody>
        ${rows.map((r) => `<tr><td><span class="chip ${r.s}">${t.strategy[r.s]}</span></td>
          <td>${this._fmtNum(r.rate, 2)} °C${t.perHour}</td><td>${this._eur(r.cost, 3)}</td>
          <td>${r.keep === null ? "–" : this._eur(r.keep, 3) + t.perHour}</td>
          <td class="muted">${r.learned ? t.learned : t.estimated}</td></tr>`).join("")}
        </tbody></table></div>
      <div class="card"><h2>${t.coverage}</h2>
        <table class="tbl cov-tbl"><thead><tr><th></th>${BIN_LABELS.map((b) => `<th>${b} °C</th>`).join("")}</tr></thead><tbody>${coverage}</tbody></table></div>
      <div class="card"><h2>${t.table}</h2>
        ${table.length ? `<table class="tbl"><thead><tr><th>${t.source}</th><th>${t.outdoorBand}</th><th>${t.rate}</th><th>${t.costPerDeg}</th><th>${t.perHourK}</th><th>${t.samples} (${t.heatKeep})</th></tr></thead><tbody>
          ${table.map((r) => `<tr><td><span class="chip ${r.strategy}">${t.strategy[r.strategy]}</span></td><td>${esc(r.outdoor)} °C</td><td>${this._fmtNum(r.rate, 2)} °C${t.perHour}</td><td>${this._eur(r.cost_per_deg, 3)}</td><td>${this._eur(r.maintain_cost_per_hour_per_k, 4)}</td><td>${r.heat_samples} / ${r.maintain_samples}</td></tr>`).join("")}
        </tbody></table>` : `<div class="muted">${t.nothingLearned}</div>`}
        <div class="actions"><button class="btn danger" data-action="reset">${t.reset}</button></div>
      </div>`;
  }

  // ---------------------------------------------------------------- settings tab
  _settings() {
    const t = this.t;
    const mode = this._st(E.mode)?.state;
    const num = (id, step, unit) => {
      const s = this._st(id);
      return `<label class="field"><input type="number" step="${step}" min="${s?.attributes?.min ?? 0}" max="${s?.attributes?.max ?? 100}" value="${esc(s?.state)}" data-entity="${id}" data-kind="number"><span>${unit}</span></label>`;
    };
    const time = (id) => `<label class="field"><input type="time" value="${esc((this._st(id)?.state || "").slice(0, 5))}" data-entity="${id}" data-kind="time"></label>`;
    return `<div class="card"><h2>${t.mode}</h2>
        <div class="seg">${Object.entries(t.modes).map(([k, v]) => `<button class="${k === mode ? "on" : ""}" data-action="mode" data-value="${k}">${v}</button>`).join("")}</div></div>
      <div class="card"><h2>${t.schedule}</h2>
        <div class="form">
          <div>${t.comfortTemp}</div>${num(E.comfortTemp, 0.5, "°C")}
          <div>${t.ecoTemp}</div>${num(E.ecoTemp, 0.5, "°C")}
          <div>${t.from}</div>${time(E.comfortStart)}
          <div>${t.until}</div>${time(E.comfortEnd)}
        </div></div>
      <div class="card"><h2>${t.prices}</h2><div class="muted">${t.pricesHint}</div>
        <div class="form">
          <div>${t.electricity}</div>${num(E.priceKwh, 0.001, "€/kWh")}
          <div>${t.gas}</div>${num(E.priceGas, 0.001, "€/m³")}
        </div></div>
      <div class="card row"><div>${t.advanced}</div><a class="btn" href="/config/integrations/integration/hybrid_heating" target="_top">${t.open}</a></div>`;
  }

  // ---------------------------------------------------------------- events
  _onClick(ev) {
    const el = ev.target.closest("[data-tab],[data-action]");
    if (!el) return;
    if (el.dataset.tab) {
      this._tab = el.dataset.tab;
      if (this._tab === "costs") this._loadStats();
      this._render(true);
      return;
    }
    const v = el.dataset.value;
    switch (el.dataset.action) {
      case "mode":
        this._call("select", "select_option", { entity_id: E.mode, option: v });
        break;
      case "past":
        this._past = +v; this._render(true); this._loadHistory();
        break;
      case "ahead":
        this._ahead = +v; this._render(true);
        break;
      case "toggle":
        this._hidden.has(v) ? this._hidden.delete(v) : this._hidden.add(v);
        this._render(true);
        break;
      case "reset":
        if (confirm(this.t.resetConfirm)) this._call("hybrid_heating", "reset_learning", {});
        break;
    }
  }

  _onChange(ev) {
    const el = ev.target;
    if (!el.dataset.entity) return;
    if (el.dataset.kind === "number") {
      const v = parseFloat(el.value);
      if (Number.isFinite(v)) this._call("number", "set_value", { entity_id: el.dataset.entity, value: v });
    } else if (el.dataset.kind === "time" && el.value) {
      this._call("time", "set_value", { entity_id: el.dataset.entity, time: `${el.value}:00` });
    }
    el.blur();
  }
}

const STYLE = `
:host { display:block; min-height:100vh; background:var(--primary-background-color); color:var(--primary-text-color);
  font-family:var(--paper-font-body1_-_font-family, Roboto, system-ui, sans-serif); --cl-radius:12px; }
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
.card { background:var(--card-background-color, var(--ha-card-background)); border:1px solid var(--divider-color); border-radius:var(--cl-radius); padding:16px; }
.card h2 { font-size:17px; margin:0 0 12px; font-weight:600; }
.card.row { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.card-head { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }
.card-head h2 { margin:0; }
.grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(190px, 1fr)); gap:12px; }
.stat .label { font-size:13px; color:var(--secondary-text-color); }
.stat .value { font-size:26px; font-weight:600; margin:6px 0 4px; line-height:1.15; }
.stat .sub { font-size:13px; color:var(--secondary-text-color); line-height:1.35; }
.banner { border:1px solid var(--divider-color); border-radius:var(--cl-radius); padding:12px 16px; display:flex; justify-content:space-between; align-items:center; gap:12px; }
.banner.warn { border-color:#ffa726; background:rgba(255,167,38,.12); }
.banner.err { border-color:#ef5350; background:rgba(239,83,80,.12); }
.btn { background:transparent; color:var(--primary-text-color); border:1px solid var(--divider-color); border-radius:8px; padding:7px 14px; font:inherit; font-size:14px; cursor:pointer; text-decoration:none; white-space:nowrap; }
.btn:hover { background:rgba(127,127,127,.12); }
.btn.danger { border-color:#ef5350; color:#ef5350; }
.chip { display:inline-block; padding:2px 10px; border-radius:999px; font-size:.8em; font-weight:600; color:#fff; background:#757575; }
.stat .value .chip { font-size:18px; padding:3px 12px; }
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
.lg i, .band-key i { width:14px; height:4px; border-radius:2px; display:inline-block; }
.band-key { display:flex; align-items:center; gap:6px; color:var(--secondary-text-color); }
.band-key i { height:10px; opacity:.5; }
.sep { width:1px; height:14px; background:var(--divider-color); }
.chart { width:100%; min-height:320px; }
.chart svg { display:block; }
.grid line, line.grid { stroke:var(--divider-color); stroke-width:1; }
line.grid.v { stroke-dasharray:2 4; }
.ax { fill:var(--secondary-text-color); font-size:11px; }
.ax.out { fill:${COLORS.outdoor}; }
.future { fill:rgba(127,127,127,.07); }
.nowline { stroke:var(--primary-text-color); stroke-dasharray:3 3; opacity:.6; }
.tipline { stroke:var(--secondary-text-color); stroke-width:1; }
.tipbox { fill:var(--card-background-color, #222); stroke:var(--divider-color); }
.tiptext { fill:var(--primary-text-color); font-size:12px; }
.bars { display:flex; gap:4px; align-items:flex-end; height:220px; padding-top:8px; }
.barcol { flex:1; display:flex; flex-direction:column; align-items:center; height:100%; min-width:0; }
.barval { font-size:10px; color:var(--secondary-text-color); height:14px; white-space:nowrap; overflow:hidden; }
.stack { flex:1; width:100%; max-width:42px; display:flex; flex-direction:column-reverse; justify-content:flex-start; }
.stack div { width:100%; border-radius:2px; }
.stack div + div { margin-bottom:1px; }
.barlbl { font-size:11px; color:var(--secondary-text-color); margin-top:4px; white-space:nowrap; }
.tbl { width:100%; border-collapse:collapse; font-size:14px; }
.tbl th { text-align:left; font-weight:500; color:var(--secondary-text-color); font-size:12px; padding:6px 8px; border-bottom:1px solid var(--divider-color); }
.tbl td { padding:8px; border-bottom:1px solid var(--divider-color); color:var(--primary-text-color); font-size:14px; }
.cov-tbl td.cov { text-align:center; font-weight:600; border:2px solid var(--card-background-color); border-radius:6px; }
.cov.l0 { background:rgba(127,127,127,.08); } .cov.l1 { background:rgba(76,175,80,.25); } .cov.l2 { background:rgba(76,175,80,.5); } .cov.l3 { background:rgba(76,175,80,.8); color:#fff; }
.actions { margin-top:14px; display:flex; justify-content:flex-end; }
.seg { display:flex; flex-wrap:wrap; gap:8px; }
.seg button { flex:1; min-width:150px; padding:12px; border-radius:10px; border:1px solid var(--divider-color); background:transparent; color:var(--primary-text-color); font:inherit; cursor:pointer; }
.seg button.on { background:var(--primary-color); border-color:var(--primary-color); color:var(--text-primary-color, #fff); font-weight:600; }
.form { display:grid; grid-template-columns:minmax(140px, 240px) 200px; gap:10px 16px; align-items:center; margin-top:10px; }
.field { display:flex; align-items:center; gap:8px; }
.field input { width:110px; padding:7px 10px; border-radius:8px; border:1px solid var(--divider-color); background:var(--secondary-background-color, transparent); color:var(--primary-text-color); font:inherit; }
.field span { color:var(--secondary-text-color); font-size:13px; }
@media (max-width: 700px) {
  .toolbar { flex-wrap:wrap; height:auto; padding:8px; gap:8px; }
  .status { display:none; }
  .content { padding:8px; }
  .stat .value { font-size:21px; }
  .bars .barval { display:none; }
}
`;

customElements.define("climator-panel", ClimatorPanel);
