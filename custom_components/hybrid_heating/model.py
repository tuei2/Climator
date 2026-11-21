"""Physics-based thermal model of the room (pure python, no Home Assistant imports).

    dT/dt = -k * (T_in - T_out)                 heat loss to outside
            + (ga0 + ga1 * T_out) * P_airco     air conditioner, P in kW electric
            + gab * P_airco * boost             extra heat per kW when the fan blows hard
            + gc * G_cv                          boiler, G in m3 gas per hour
            + gs * S                             sun, S = solar power in kW (optional)

All terms are in degC per hour. The parameters are learned with exponentially
weighted least squares on 15-minute samples, regularised towards sensible priors so
the model behaves well before there is data. Every 15-minute sample (also in "learn
only" mode and while heating is off) improves the model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

PARAMS = ["k", "ga0", "ga1", "gc", "gs", "gab"]
N = len(PARAMS)
PRIOR = {"k": 0.04, "ga0": 0.85, "ga1": 0.03, "gc": 2.0, "gs": 0.0, "gab": 0.0}
# typical magnitude of each feature, used to scale the prior strength
FEATURE_SCALE = {"k": 15.0, "ga0": 0.8, "ga1": 6.0, "gc": 0.8, "gs": 1.5, "gab": 1.0}
PRIOR_SAMPLES = 5.0
FORGET = 0.999          # per sample (15 min) -> half-life ~7 days
SAMPLE_MINUTES = 15
BOUNDS = {"k": (0.003, 0.5), "ga0": (0.0, 10.0), "ga1": (-0.2, 0.3),
          "gc": (0.0, 15.0), "gs": (-0.5, 5.0), "gab": (-1.0, 3.0)}
# maximum input per source: airco (soft/auto fan) and airco_boost in kW electric, cv in m3/h
DEFAULT_PMAX = {"airco": 0.8, "airco_boost": 1.2, "cv": 1.0}
BUFFER_MAX = 7 * 24 * 60 // SAMPLE_MINUTES  # keep 7 days of samples


def _solve(a: list[list[float]], b: list[float]) -> list[float] | None:
    """Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            return None
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r != col:
                f = m[r][col] / m[col][col]
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def _inverse_diag(a: list[list[float]]) -> list[float]:
    n = len(a)
    out = []
    for i in range(n):
        e = [1.0 if j == i else 0.0 for j in range(n)]
        col = _solve(a, e)
        out.append(col[i] if col else float("inf"))
    return out


@dataclass
class Sample:
    """One 15-minute observation."""

    t: float          # unix timestamp at the end of the window
    t_in0: float      # room temp at start
    t_in1: float      # room temp at end
    t_out: float      # mean outdoor temp
    p_airco: float    # mean airco power, kW electric
    g_cv: float       # mean gas use, m3/h
    solar: float      # mean solar power, kW
    hours: float
    boost: float = 0.0  # fraction of the window the airco fan blew hard

    @property
    def slope(self) -> float:
        return (self.t_in1 - self.t_in0) / self.hours

    @property
    def t_mid(self) -> float:
        return (self.t_in0 + self.t_in1) / 2

    def features(self) -> list[float]:
        return [self.t_out - self.t_mid, self.p_airco, self.p_airco * self.t_out,
                self.g_cv, self.solar, self.p_airco * self.boost]

    def to_list(self) -> list:
        return [round(self.t), round(self.t_in0, 2), round(self.t_in1, 2), round(self.t_out, 2),
                round(self.p_airco, 3), round(self.g_cv, 4), round(self.solar, 3),
                round(self.hours, 4), round(self.boost, 2)]

    @classmethod
    def from_list(cls, v: list) -> "Sample":
        return cls(*v)


@dataclass
class ThermalModel:
    ata: list = field(default_factory=lambda: [[0.0] * N for _ in range(N)])
    atb: list = field(default_factory=lambda: [0.0] * N)
    n_eff: float = 0.0
    counts: dict = field(default_factory=lambda: {
        "passive": 0.0, "airco": 0.0, "cv": 0.0, "solar": 0.0, "boost": 0.0})
    res2: float = 0.04          # EMA of squared residual (degC/h)^2
    pmax: dict = field(default_factory=lambda: dict(DEFAULT_PMAX))
    samples: list = field(default_factory=list)   # recent Sample objects
    excluded: dict = field(default_factory=dict)  # reason -> count
    theta: dict = field(default_factory=lambda: dict(PRIOR))
    clamped: list = field(default_factory=list)

    def __post_init__(self) -> None:
        self.solve()

    # ---- persistence ----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "ata": self.ata, "atb": self.atb, "n_eff": self.n_eff, "counts": self.counts,
            "res2": self.res2, "pmax": self.pmax, "excluded": self.excluded,
            "samples": [s.to_list() for s in self.samples],
        }

    @classmethod
    def from_dict(cls, d: dict | None) -> "ThermalModel":
        m = cls()
        if d and "ata" in d:
            m.ata, m.atb = d["ata"], d["atb"]
            n_old = len(m.atb)
            if n_old < N:  # model grew (new parameter): pad with zeros
                m.ata = [row + [0.0] * (N - n_old) for row in m.ata] + [[0.0] * N for _ in range(N - n_old)]
                m.atb = m.atb + [0.0] * (N - n_old)
            m.n_eff = d.get("n_eff", 0.0)
            m.counts.update(d.get("counts", {}))
            m.res2 = d.get("res2", 0.04)
            old_pmax = d.get("pmax", {})
            m.pmax.update(old_pmax)
            if "airco_boost" not in old_pmax and "airco" in old_pmax:
                m.pmax["airco_boost"] = max(old_pmax["airco"], DEFAULT_PMAX["airco_boost"])
            m.excluded = d.get("excluded", {})
            m.samples = [Sample.from_list(v) for v in d.get("samples", [])]
        m.solve()
        return m

    def reset(self) -> None:
        fresh = ThermalModel()
        self.__dict__.update(fresh.__dict__)

    # ---- learning -------------------------------------------------------
    def _prior(self):
        a = [[0.0] * N for _ in range(N)]
        b = [0.0] * N
        for i, p in enumerate(PARAMS):
            w = PRIOR_SAMPLES * FEATURE_SCALE[p] ** 2
            a[i][i] = w
            b[i] = w * PRIOR[p]
        return a, b

    def solve(self) -> None:
        pa, pb = self._prior()
        a = [[pa[i][j] + self.ata[i][j] for j in range(N)] for i in range(N)]
        b = [pb[i] + self.atb[i] for i in range(N)]
        sol = _solve(a, b) or [PRIOR[p] for p in PARAMS]
        self.clamped = []
        theta = {}
        for p, v in zip(PARAMS, sol):
            lo, hi = BOUNDS[p]
            if v < lo or v > hi:
                self.clamped.append(p)
            theta[p] = min(hi, max(lo, v))
        self.theta = theta
        self._a_full = a

    def predict_slope(self, s: Sample) -> float:
        return sum(self.theta[p] * x for p, x in zip(PARAMS, s.features()))

    def add_sample(self, s: Sample, learn: bool = True) -> float:
        """Store the sample; if learn, update the model. Returns the residual."""
        residual = s.slope - self.predict_slope(s)
        self.samples.append(s)
        if len(self.samples) > BUFFER_MAX:
            del self.samples[: len(self.samples) - BUFFER_MAX]
        if not learn:
            return residual
        x = s.features()
        for i in range(N):
            self.atb[i] = FORGET * self.atb[i] + x[i] * s.slope
            for j in range(N):
                self.ata[i][j] = FORGET * self.ata[i][j] + x[i] * x[j]
        self.n_eff = FORGET * self.n_eff + 1
        for k in self.counts:
            self.counts[k] *= FORGET
        if s.p_airco < 0.05 and s.g_cv < 0.01:
            self.counts["passive"] += 1
        if s.p_airco >= 0.05:
            self.counts["airco"] += 1
        if s.g_cv >= 0.01:
            self.counts["cv"] += 1
        if s.solar >= 0.1:
            self.counts["solar"] += 1
        if s.p_airco >= 0.05 and s.boost >= 0.5:
            self.counts["boost"] += 1
        self.res2 = 0.98 * self.res2 + 0.02 * residual ** 2
        self.solve()
        return residual

    def exclude(self, reason: str) -> None:
        self.excluded[reason] = self.excluded.get(reason, 0) + 1

    def observe_power(self, source: str, power: float, heating_up: bool) -> None:
        """Track the maximum power a source delivers while it is heating up."""
        if not heating_up or power <= 0:
            return
        cur = self.pmax[source]
        rate = 0.3 if power > cur else 0.02
        self.pmax[source] = cur + rate * (power - cur)

    # ---- confidence -----------------------------------------------------
    def std_errors(self) -> dict:
        diag = _inverse_diag(self._a_full)
        return {p: math.sqrt(max(self.res2 * d, 0.0)) for p, d in zip(PARAMS, diag)}

    def confidence(self) -> dict:
        """none / low / medium / high per parameter, from informative sample counts."""
        def level(n: float) -> str:
            return "none" if n < 4 else "low" if n < 24 else "medium" if n < 96 else "high"
        return {
            "k": level(self.counts["passive"] + 0.3 * (self.counts["airco"] + self.counts["cv"])),
            "ga0": level(self.counts["airco"]),
            "ga1": level(self.counts["airco"] / 2),
            "gc": level(self.counts["cv"]),
            "gs": level(self.counts["solar"]),
            "gab": level(self.counts.get("boost", 0.0)),
        }

    # ---- physics helpers ------------------------------------------------
    def gain(self, source: str, t_out: float, boost: float = 0.0) -> float:
        """degC per hour per unit of input (kW for airco, m3/h for cv)."""
        th = self.theta
        if source == "airco":
            return max(th["ga0"] + th["ga1"] * t_out + th["gab"] * boost, 0.05)
        return max(th["gc"], 0.05)

    def pmax_key(self, source: str, boost: bool) -> str:
        return "airco_boost" if source == "airco" and boost else source

    def pmax_of(self, source: str, boost: bool) -> float:
        """Learned maximum input; blowing hard never delivers less than blowing softly."""
        if source == "airco" and boost:
            return max(self.pmax["airco_boost"], self.pmax["airco"])
        return self.pmax[source]

    def heat_rate(self, strategy: str, t_out: float, boost: bool = False) -> float:
        """degC/h added at full power by a strategy (before losses)."""
        srcs = ["airco", "cv"] if strategy == "both" else [strategy]
        return sum(self.gain(s, t_out, 1.0 if boost else 0.0) * self.pmax_of(s, boost) for s in srcs)

    def input_rate(self, strategy: str, boost: bool = False) -> dict:
        """Full-power input per source: {'airco': kW, 'cv': m3/h}."""
        srcs = ["airco", "cv"] if strategy == "both" else [strategy]
        return {s: self.pmax_of(s, boost) for s in srcs}

    def slope(self, t_in, t_out, heat=0.0, solar=0.0) -> float:
        return -self.theta["k"] * (t_in - t_out) + heat + self.theta["gs"] * solar

    def time_to(self, t0, target, t_out, heat, solar=0.0) -> float | None:
        """Hours to go from t0 to target with constant heat input; None if unreachable."""
        k = self.theta["k"]
        if target <= t0:
            return 0.0
        t_eq = t_out + (heat + self.theta["gs"] * solar) / k
        if t_eq <= target + 0.05:
            return None
        return -math.log((t_eq - target) / (t_eq - t0)) / k

    def decay(self, t0, hours, t_out, floor=None, solar=0.0) -> float:
        """Room temperature after `hours` without heating (or held at floor)."""
        k = self.theta["k"]
        t_eq = t_out + self.theta["gs"] * solar / k
        t = t_eq + (t0 - t_eq) * math.exp(-k * hours)
        return max(t, floor) if floor is not None else t

    def maintain_input(self, source: str, target, t_out, solar=0.0, boost: bool = False) -> float:
        """Power (kW or m3/h) needed to keep the room at target."""
        need = self.theta["k"] * (target - t_out) - self.theta["gs"] * solar
        return max(need, 0.0) / self.gain(source, t_out, 1.0 if boost else 0.0)

    # ---- validation -----------------------------------------------------
    def check(self, horizon_steps: int = 4, max_age_h: float = 72) -> dict:
        """Open-loop prediction 1 hour ahead from each sample, compared with reality."""
        if len(self.samples) < horizon_steps + 1:
            return {"mae_1h": None, "bias_1h": None, "n": 0}
        newest = self.samples[-1].t
        errs = []
        for i in range(len(self.samples) - horizon_steps):
            seg = self.samples[i: i + horizon_steps]
            if newest - seg[0].t > max_age_h * 3600:
                continue
            if any(abs(seg[j + 1].t - seg[j].t - seg[j].hours * 3600) > 120 for j in range(horizon_steps - 1)):
                continue  # gap in data
            t = seg[0].t_in0
            for s in seg:
                t += self.slope(t, s.t_out, self.gain("airco", s.t_out, s.boost) * s.p_airco
                                + self.gain("cv", s.t_out) * s.g_cv, s.solar) * s.hours
            errs.append(t - seg[-1].t_in1)
        if not errs:
            return {"mae_1h": None, "bias_1h": None, "n": 0}
        return {"mae_1h": sum(abs(e) for e in errs) / len(errs),
                "bias_1h": sum(errs) / len(errs), "n": len(errs)}

    def replay(self, hours: float = 48, reset_every: int = 12) -> list:
        """Model simulation over recent samples, restarting from reality every 3 h."""
        if not self.samples:
            return []
        newest = self.samples[-1].t
        recent = [s for s in self.samples if newest - s.t <= hours * 3600]
        out, t = [], None
        for i, s in enumerate(recent):
            gap = i and abs(s.t - recent[i - 1].t - s.hours * 3600) > 120
            if t is None or i % reset_every == 0 or gap:
                t = s.t_in0
            t += self.slope(t, s.t_out, self.gain("airco", s.t_out, s.boost) * s.p_airco
                            + self.gain("cv", s.t_out) * s.g_cv, s.solar) * s.hours
            out.append([round(s.t * 1000), round(s.t_in1, 2), round(t, 2)])
        return out


class SampleCollector:
    """Builds 15-minute samples from 1-minute readings."""

    def __init__(self) -> None:
        self.start = None

    def reset(self) -> None:
        self.start = None

    def tick(self, now_ts, t_in, t_out, kwh, m3, solar_kw, excluded_reason, boost=False):
        """Returns (Sample | None, reason | None) at the end of a window."""
        if None in (t_in, t_out):
            self.start = None
            return None, None
        if self.start is None:
            self.start = {"t": now_ts, "t_in": t_in, "kwh": kwh, "m3": m3, "boost": [1.0 if boost else 0.0],
                          "outs": [t_out], "sol": [solar_kw or 0.0], "excl": excluded_reason}
            return None, None
        w = self.start
        w["outs"].append(t_out)
        w["sol"].append(solar_kw or 0.0)
        w["boost"].append(1.0 if boost else 0.0)
        if excluded_reason and not w["excl"]:
            w["excl"] = excluded_reason
        elapsed = now_ts - w["t"]
        if elapsed < SAMPLE_MINUTES * 60 - 5:
            return None, None
        self.start = {"t": now_ts, "t_in": t_in, "kwh": kwh, "m3": m3, "boost": [1.0 if boost else 0.0],
                      "outs": [t_out], "sol": [solar_kw or 0.0], "excl": excluded_reason}
        hours = elapsed / 3600
        if elapsed > SAMPLE_MINUTES * 60 * 1.6:
            return None, "gap"
        if w["excl"]:
            return None, w["excl"]
        if None in (kwh, m3, w["kwh"], w["m3"]):
            return None, "meter_missing"
        d_kwh, d_m3 = kwh - w["kwh"], m3 - w["m3"]
        if d_kwh < 0 or d_m3 < 0 or d_kwh / hours > 6 or d_m3 / hours > 5:
            return None, "meter_jump"
        if abs(t_in - w["t_in"]) / hours > 6:
            return None, "temp_jump"
        s = Sample(now_ts, w["t_in"], t_in, sum(w["outs"]) / len(w["outs"]),
                   d_kwh / hours, d_m3 / hours, sum(w["sol"]) / len(w["sol"]), hours,
                   sum(w["boost"]) / len(w["boost"]))
        return s, None
