#!/usr/bin/env python3
"""EE4525 metrics from LTspice results: settling (D4), noise (D5), kT/C, SNR, FoM.

All formulas follow brief/spec.md. Library + CLI:
  uv run tools/metrics.py tran  RUN.raw --net RUN.net [--plot report/figures/d4_settling.pdf]
  uv run tools/metrics.py noise RUN.raw [--plot report/figures/d5_noise.pdf]
  uv run tools/metrics.py loop  RUN.raw [--plot loop.pdf]        (design/templates/bench_loop.cir)
  uv run tools/metrics.py budget --vout 1.13 --cin 3.24p [--vn-amp 326u]

Bench conventions (override with flags): amplifier inputs (summing nodes) vip/vin,
outputs vop/von, amplifier supply source Vdd, params VoutStep, tstep, Tsettle, Cin, Cfb, Cload.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

K_B = 1.380649e-23
T_K = 300.15  # LTspice default 27 C
VDD = 1.8
KTC_FACTOR = 42.0  # differential: 2 x (Cin -> 16, Cfb -> 4, Cload -> 1) x kT/Cin, with Cin = 4 Cfb = Cload
SPEC = {"A": 78.0, "Abeta": 66.0, "SNR": 66.0, "Tsettle": 25e-9}

_SUF = {"t": 1e12, "g": 1e9, "meg": 1e6, "k": 1e3, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15}


def spice_num(s: str) -> float:
    s = s.strip().lower()
    m = re.match(r"^([-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?)(meg|[tgkmunpf])?", s)
    if not m:
        raise ValueError(s)
    return float(m.group(1)) * _SUF.get(m.group(2) or "", 1.0)


def _safe_eval(expr: str, names: dict) -> float:
    """Arithmetic-only evaluator for .param expressions (no eval of arbitrary code)."""
    import ast
    import operator as op

    bins = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow}
    funcs = {k: getattr(math, k) for k in ("sqrt", "log", "log10", "exp")}

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in bins:
            return bins[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            return -ev(n.operand) if isinstance(n.op, ast.USub) else ev(n.operand)
        if isinstance(n, ast.Name):
            if n.id == "pi":
                return math.pi
            return float(names[n.id])
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in funcs and len(n.args) == 1:
            return funcs[n.func.id](ev(n.args[0]))
        raise ValueError(f"unsupported expression: {expr}")

    return ev(ast.parse(expr.replace("**", "^").replace("^", "**"), mode="eval"))


def net_params(net: Path) -> dict[str, float]:
    """Evaluate `.param` assignments of a netlist (numbers, suffixes, {expressions})."""
    text = Path(net).read_text(errors="replace")
    assigns: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip().lower().startswith(".param"):
            continue
        body = line.strip()[6:]
        for m in re.finditer(r"(\w+)\s*=\s*(\{[^}]*\}|[^\s]+)", body):
            assigns[m.group(1).lower()] = m.group(2).strip("{}")
    vals: dict[str, float] = {}
    for _ in range(10):
        for k, expr in assigns.items():
            if k in vals:
                continue
            e = re.sub(r"(?<![\w.])((?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)(meg|Meg|MEG|[tTgGkKmMuUnNpPfF])(?![\w])",
                       lambda m: repr(spice_num(m.group(1) + m.group(2))), expr)
            try:
                vals[k] = _safe_eval(e.lower(), vals)
            except (ValueError, KeyError, SyntaxError, ZeroDivisionError, TypeError):
                pass
    return vals


# ----------------------------------------------------------------------------- raw access


class Raw:
    def __init__(self, path: str | Path):
        from spicelib import RawRead

        self.r = RawRead(str(path), verbose=False)
        names = self.r.get_trace_names()
        self.names = {n.lower(): n for n in names}
        # spicelib 1.6 loads lazily: get_axis() raises until a trace is read, so read the
        # axis (time / frequency = first trace) by name.
        self.x = np.abs(np.real(np.asarray(self.r.get_trace(names[0]).get_wave())))

    def has(self, name: str) -> bool:
        return name.lower() in self.names

    def __getitem__(self, name: str) -> np.ndarray:
        return np.asarray(self.r.get_trace(self.names[name.lower()]).get_wave())


def _cross_up(t, y, level, t0):
    """First upward crossing of `level` after t0 (linear interpolation)."""
    idx = np.where((t[1:] > t0) & (y[:-1] < level) & (y[1:] >= level))[0]
    if not len(idx):
        return math.nan
    i = idx[0]
    return t[i] + (level - y[i]) * (t[i + 1] - t[i]) / (y[i + 1] - y[i])


def _last_below(t, y, level, t0):
    """Settling time: last instant after t0 where the curve is below `level`."""
    m = t >= t0
    below = np.where(m & (y < level))[0]
    if not len(below):
        return t0
    i = below[-1]
    if i == len(t) - 1:
        return math.inf
    return t[i] + (level - y[i]) * (t[i + 1] - t[i]) / (y[i + 1] - y[i])


def _avg(t, y, a, b):
    m = (t >= a) & (t <= b)
    if m.sum() < 2:
        return math.nan
    return float(np.trapezoid(y[m], t[m]) / (t[m][-1] - t[m][0]))


def tran_metrics(raw_path, net_path=None, *, vg=("vip", "vin"), out=("vop", "von"), supply="Vdd",
                 vout_step=None, tstep=None, tsettle=25e-9) -> dict:
    p = net_params(Path(net_path)) if net_path else {}
    vmax = vout_step if vout_step is not None else p.get("voutstep")
    t_step = tstep if tstep is not None else p.get("tstep")
    if vmax is None or t_step is None:
        raise SystemExit("need VoutStep and tstep (params in the netlist or --vout-step/--tstep)")
    tsettle = p.get("tsettle", tsettle)
    r = Raw(raw_path)
    t = r.x
    v = lambda n: np.real(r[f"V({n})"])
    vgd = v(vg[0]) - v(vg[1])
    vo = v(out[0]) - v(out[1])
    if vo[-1] < 0:
        vo = -vo
    A = 20 * np.log10(vmax / (np.abs(vgd) + 1e-9))
    Ab = 20 * np.log10(vmax / (np.abs(vmax - vo) + 1e-9))
    t25 = t_step + tsettle
    after = t >= t25

    # gap between the curves right after the step = 20 log10(1/beta_actual)
    w = (t >= t_step) & (t <= t_step + 0.5e-9)
    i0 = np.where(w)[0][np.argmin(A[w])] if w.any() else 0
    gap = float(A[i0] - Ab[i0])
    Ab_shift = A - A[i0]  # alternative Abeta definition (A shifted to start at 0 dB)

    T30 = _cross_up(t, Ab, 30.0, t_step)
    T386 = _cross_up(t, Ab, 38.6, t_step)
    Ts_A = _last_below(t, A, SPEC["A"], t_step)
    Ts_Ab = _last_below(t, Ab, SPEC["Abeta"], t_step)

    # first significant accuracy peak (spike/bump with >= 3 dB prominence) after the step
    def first_peak(y):
        from scipy.signal import find_peaks

        m = t > t_step + 0.2e-9
        pk, _ = find_peaks(y[m], prominence=3.0)
        return float(t[m][pk[0]] - t_step) if len(pk) else math.inf

    pk_A, pk_Ab = first_peak(A), first_peak(Ab)

    dvo = np.gradient(vo, t)
    k = (t >= t_step) & (t <= t25)
    res = {
        "VoutStep_V": vmax,
        "tstep_s": t_step,
        "A_at_25ns_dB": float(np.interp(t25, t, A)),
        "Abeta_at_25ns_dB": float(np.interp(t25, t, Ab)),
        "Abeta_shift_at_25ns_dB": float(np.interp(t25, t, Ab_shift)),
        "A_floor_dB": float(A[after].min()) if after.any() else math.nan,
        "Abeta_floor_dB": float(Ab[after].min()) if after.any() else math.nan,
        "t_end_after_deadline_ns": float((t[-1] - t25) * 1e9),
        "Tsettle_A_ns": (Ts_A - t_step) * 1e9,
        "Tsettle_Abeta_ns": (Ts_Ab - t_step) * 1e9,
        "T30_ns": (T30 - t_step) * 1e9,
        "T38p6_ns": (T386 - t_step) * 1e9,
        "tau_ns": (T386 - T30) * 1e9,
        "gap_dB": gap,
        "beta_actual": 10 ** (-gap / 20),
        "first_peak_A_ns": pk_A * 1e9,
        "first_peak_Abeta_ns": pk_Ab * 1e9,
        "slew_max_V_per_us": float(np.max(np.abs(dvo[k])) / 1e6) if k.any() else math.nan,
        "Vout_final_V": float(vo[-1]),
    }
    if p.get("cin") and p.get("cfb"):
        res["beta_ideal"] = p["cfb"] / (p["cin"] + p["cfb"])
    if r.has(f"I({supply})"):
        idd = -np.real(r[f"I({supply})"])
        i_q = _avg(t, idd, max(t[0], t_step - 5e-9), t_step)
        i_set = _avg(t, idd, t_step, t25)
        i_all = _avg(t, idd, t_step, t[-1])
        res.update({"I_quiescent_mA": i_q * 1e3, "I_settle_window_mA": i_set * 1e3, "I_after_step_mA": i_all * 1e3})
        # Reported power: the larger of quiescent and the 25 ns amplification-window average
        # (brief: "that current (the average) x Vdd"). State this window in the report.
        i_rep = np.nanmax([i_q, i_set])
        res["I_report_mA"] = float(i_rep * 1e3)
        res["P_report_mW"] = float(i_rep * VDD * 1e3)
    res["checks"] = {
        "A_at_25ns": res["A_at_25ns_dB"] >= SPEC["A"],
        "Abeta_at_25ns": res["Abeta_at_25ns_dB"] >= SPEC["Abeta"],
        "A_floor_after_25ns": res["A_floor_dB"] >= SPEC["A"],
        "Abeta_floor_after_25ns": res["Abeta_floor_dB"] >= SPEC["Abeta"],
        "first_peak_after_25ns": min(pk_A, pk_Ab) * 1e9 > tsettle * 1e9,
        "sim_long_enough": res["t_end_after_deadline_ns"] >= 30.0,
        "Abeta_defs_agree": abs(res["Abeta_at_25ns_dB"] - res["Abeta_shift_at_25ns_dB"]) < 3.0,
    }
    res["_curves"] = (t, A, Ab, t_step, t25)
    return res


def plot_settling(m: dict, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t, A, Ab, t_step, t25 = m["_curves"]
    # start just after the input edge: at t_step itself the virtual-ground error is still zero and A sits on the
    # 1 nV floor (a meaningless vertical spike at t = 0); Abeta is 0 dB from the first plotted sample
    s = t > t_step + 0.06e-9
    x = (t[s] - t_step) * 1e9
    sb = t >= t_step  # Abeta from the step itself: exactly 0 dB at t_step (output not yet moved)
    xb = (t[sb] - t_step) * 1e9
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(x, A[s], color="tab:red", lw=1.2, label=r"$A$ (amplifier accuracy, virtual ground)")
    ax.plot(xb, Ab[sb], color="tab:blue", lw=1.2, label=r"$A\beta$ (loop accuracy, output error)")
    for tt, lvl in ((m["T30_ns"], 30.0), (m["T38p6_ns"], 38.6)):
        if math.isfinite(tt):
            ax.plot([tt], [lvl], "o", ms=3, color="tab:blue")
    if math.isfinite(m["tau_ns"]):
        ax.annotate(f"$\\tau$ = T$_{{38.6}}$ - T$_{{30}}$ = {m['tau_ns']:.3f} ns", (m["T30_ns"], 30),
                    xytext=(0.6, 52), fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.6))
    ax.axvline(25, color="k", ls="--", lw=0.8)
    ax.text(25.3, 2, "25 ns", fontsize=8)
    ax.axhline(SPEC["A"], color="tab:red", ls=":", lw=0.8)
    ax.axhline(SPEC["Abeta"], color="tab:blue", ls=":", lw=0.8)
    xr = max(x.max(), 40)
    ax.text(xr - 1, SPEC["A"] + 1, "A spec 78 dB", fontsize=7, color="tab:red", ha="right", va="bottom")
    ax.text(xr - 1, SPEC["Abeta"] + 1, r"A$\beta$ spec 66 dB", fontsize=7, color="tab:blue", ha="right", va="bottom")
    ax.annotate(f"A = {m['A_at_25ns_dB']:.2f} dB", (25, m["A_at_25ns_dB"]), xytext=(27, m["A_at_25ns_dB"] + 6),
                arrowprops=dict(arrowstyle="->", lw=0.6), fontsize=8)
    ax.annotate(f"A$\\beta$ = {m['Abeta_at_25ns_dB']:.2f} dB", (25, m["Abeta_at_25ns_dB"]),
                xytext=(27, m["Abeta_at_25ns_dB"] - 12), arrowprops=dict(arrowstyle="->", lw=0.6), fontsize=8)
    ax.set_xlabel("time after input step [ns]")
    ax.set_ylabel("accuracy [dB]")
    ax.set_xlim(0, max(x.max(), 40))
    top = float(np.nanmax(A[s])) + 15
    ax.set_ylim(-5, min(140.0, max(100.0, top)))  # zero-crossing spikes reach ~180 dB (1 nV floor); clip them
    g = m.get("gap_dB", math.nan)
    if math.isfinite(g):  # mark the 20log10(1/beta_actual) gap right after the step
        x0 = 1.0
        y0 = float(np.interp(x0, xb, Ab[sb]))
        ax.annotate("", xy=(x0, y0 + g), xytext=(x0, y0), arrowprops=dict(arrowstyle="<->", lw=0.7))
        ax.text(x0 + 0.4, y0 + g / 2, f"$20\\log_{{10}}(1/\\beta_{{act}})$ = {g:.2f} dB", fontsize=8, va="center")
    ax.grid(True, lw=0.3, alpha=0.6)
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title(r"Settling accuracy, $20\log_{10}(V_{out,max}/(|V_{err}|+1\,\mathrm{nV}))$", fontsize=9)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------------- noise


def noise_metrics(raw_path, f_lo=1e4, f_hi=1e11, top=8) -> dict:
    r = Raw(raw_path)
    f = r.x
    on = np.abs(r["V(onoise)"])
    m = (f >= f_lo) & (f <= f_hi)
    vn = math.sqrt(np.trapezoid(on[m] ** 2, f[m]))
    cum = np.sqrt(np.concatenate([[0.0], np.cumsum(0.5 * (on[m][1:] ** 2 + on[m][:-1] ** 2) * np.diff(f[m]))]))
    contrib = {}
    for low, name in r.names.items():
        # device totals only: V(m1) is the device total, V(m1.id) / V(m1.fn) its components
        if low in ("frequency", "v(onoise)", "v(inoise)", "gain") or not low.startswith("v(") or "." in low:
            continue
        y = np.abs(r[name])
        if y.shape == f.shape:
            contrib[name] = math.sqrt(np.trapezoid(y[m] ** 2, f[m]))
    ranked = sorted(contrib.items(), key=lambda kv: -kv[1])[:top]
    f_band = f[m]
    corner = math.nan
    if len(f_band) > 10:
        white = np.median(on[m][(f_band > 1e6) & (f_band < 1e7)]) if ((f_band > 1e6) & (f_band < 1e7)).any() else math.nan
        lf = np.where(on[m] > math.sqrt(2) * white)[0]
        corner = float(f_band[lf[-1]]) if len(lf) and lf[-1] < len(f_band) - 1 and f_band[lf[-1]] < 1e7 else math.nan
    return {
        "Vn_amp_uVrms": vn * 1e6,
        "band_Hz": [f_lo, f_hi],
        "f_min_sim_Hz": float(f.min()),
        "f_max_sim_Hz": float(f.max()),
        "flicker_corner_Hz_est": corner,
        "top_contributors_uVrms": {k: v * 1e6 for k, v in ranked},
        "_curves": (f[m], on[m], cum),
    }


def plot_noise(m: dict, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    f, on, cum = m["_curves"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.loglog(f, on * 1e9, color="tab:blue", lw=1.2, label=r"differential output noise density $v_{onoise}$")
    ax.set_xlabel("frequency [Hz]")
    ax.set_ylabel(r"output noise density [nV/$\sqrt{\mathrm{Hz}}$]")
    ax.grid(True, which="both", lw=0.3, alpha=0.5)
    ax2 = ax.twinx()
    ax2.semilogx(f, cum * 1e6, color="tab:orange", lw=1.2, label="integrated noise (from 10 kHz)")
    ax2.set_ylabel(r"integrated noise [$\mu V_{rms}$]")
    ax2.axhline(m["Vn_amp_uVrms"], color="tab:orange", ls=":", lw=0.8)
    ax.set_xlim(1e4, 1e11)
    ax.set_title(f"Integrated amplifier noise 10 kHz to 100 GHz: {m['Vn_amp_uVrms']:.1f} $\\mu V_{{rms}}$", fontsize=9)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="center left", fontsize=8)  # the corners carry the curves
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------------- loop gain


def loop_metrics(raw_path, nodes=("sin", "sip", "vin", "vip")) -> dict:
    """Differential loop gain T = -V(sin,sip)/V(vin,vip) from design/templates/bench_loop.cir."""
    r = Raw(raw_path)
    f = r.x
    s1, s2, a1, a2 = (r[f"V({n})"] for n in nodes)
    T = -(s1 - s2) / (a1 - a2)
    mag = 20 * np.log10(np.abs(T))
    ph = np.degrees(np.unwrap(np.angle(T)))
    i = np.where((mag[:-1] >= 0) & (mag[1:] < 0))[0]
    out = {"T0_dB": float(mag[0]), "f_T0_Hz": float(f[0])}
    if len(i):
        k = i[0]
        fc = float(np.exp(np.interp(0.0, [mag[k + 1], mag[k]], [np.log(f[k + 1]), np.log(f[k])])))
        out.update({"fc_Hz": fc, "PM_deg": float(180 + np.interp(np.log(fc), np.log(f), ph))})
        out["n_unity_crossings"] = int(len(i))
    j = np.where((ph[:-1] > -180) & (ph[1:] <= -180))[0]
    if len(j):
        out["GM_dB"] = float(-mag[j[0]])
        out["f_180_Hz"] = float(f[j[0]])
    out["_curves"] = (f, mag, ph)
    return out


def plot_loop(m: dict, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    f, mag, ph = m["_curves"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 5.0), sharex=True)
    a1.semilogx(f, mag, lw=1.2)
    a1.axhline(0, color="k", lw=0.6)
    a1.set_ylabel(r"$|T|=|A\beta|$ [dB]")
    a2.semilogx(f, ph, lw=1.2, color="tab:orange")
    a2.axhline(-180, color="k", lw=0.6)
    a2.set_ylabel("phase [deg]")
    a2.set_xlabel("frequency [Hz]")
    if "fc_Hz" in m:
        for a in (a1, a2):
            a.axvline(m["fc_Hz"], color="gray", ls="--", lw=0.6)
        a1.set_title(f"T0 {m['T0_dB']:.1f} dB, fc {m['fc_Hz']/1e6:.1f} MHz, PM {m['PM_deg']:.1f} deg", fontsize=9)
    for a in (a1, a2):
        a.grid(True, which="both", lw=0.3, alpha=0.5)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------------- budget


def ktc_uV(cin: float, factor: float = KTC_FACTOR, T: float = T_K) -> float:
    return math.sqrt(factor * K_B * T / cin) * 1e6


def snr_db(vout_step: float, vn_total_uV: float) -> float:
    return 20 * math.log10((vout_step / math.sqrt(2)) / (vn_total_uV * 1e-6))


def fom(p_mw: float, tau_ns: float, snr: float) -> tuple[float, float]:
    lin = 2 * math.pi * p_mw * 1e-3 * tau_ns * 1e-9 / (10 ** (snr / 10))
    return lin, -10 * math.log10(lin)


def budget(vout: float, cin: float, vn_amp_uV: float | None = None) -> dict:
    k = ktc_uV(cin)
    v_sig = vout / math.sqrt(2)
    vn_allowed = v_sig / 10 ** (SPEC["SNR"] / 20) * 1e6
    out = {"Vsig_rms_V": v_sig, "kTC_uVrms": k, "Vn_total_allowed_uVrms": vn_allowed,
           "Vn_amp_allowed_uVrms": math.sqrt(max(vn_allowed**2 - k**2, 0.0))}
    if vn_amp_uV is not None:
        tot = math.hypot(k, vn_amp_uV)
        out.update({"Vn_total_uVrms": tot, "SNR_dB": snr_db(vout, tot)})
    return out


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("tran")
    p.add_argument("raw")
    p.add_argument("--net")
    p.add_argument("--vg", default="vip,vin")
    p.add_argument("--out", default="vop,von")
    p.add_argument("--supply", default="Vdd")
    p.add_argument("--vout-step", type=float)
    p.add_argument("--tstep", type=float)
    p.add_argument("--plot")
    p.add_argument("--json")
    p = sub.add_parser("noise")
    p.add_argument("raw")
    p.add_argument("--plot")
    p.add_argument("--json")
    p = sub.add_parser("loop")
    p.add_argument("raw")
    p.add_argument("--plot")
    p.add_argument("--json")
    p = sub.add_parser("budget")
    p.add_argument("--vout", type=float, required=True, help="differential output step [V]")
    p.add_argument("--cin", required=True, help="e.g. 3.24p")
    p.add_argument("--vn-amp", help="integrated amplifier noise, e.g. 326u")
    a = ap.parse_args(argv)
    from lt import guard  # repo/scratch-only file access (tools run auto-approved)

    for k in ("raw", "net", "plot", "json"):
        if getattr(a, k, None):
            setattr(a, k, str(guard(getattr(a, k))))
    if a.cmd == "tran":
        m = tran_metrics(a.raw, a.net, vg=tuple(a.vg.split(",")), out=tuple(a.out.split(",")),
                         supply=a.supply, vout_step=a.vout_step, tstep=a.tstep)
        if a.plot:
            plot_settling(m, Path(a.plot))
        d = _clean(m)
    elif a.cmd == "noise":
        m = noise_metrics(a.raw)
        if a.plot:
            plot_noise(m, Path(a.plot))
        d = _clean(m)
    elif a.cmd == "loop":
        m = loop_metrics(a.raw)
        if a.plot:
            plot_loop(m, Path(a.plot))
        d = _clean(m)
    else:
        d = budget(a.vout, spice_num(a.cin), spice_num(a.vn_amp) * 1e6 if a.vn_amp else None)
    if getattr(a, "json", None):
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(d, indent=1))
    print(json.dumps(d, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
