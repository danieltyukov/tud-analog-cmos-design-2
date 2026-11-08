#!/usr/bin/env python3
"""Extra report macros measured on the final design: loop gain, CM loop, CM excursion, linearity of the settling,
noise split, saturation with the step applied, and the design parameters.

  uv run tools/report_extra.py [--tag final]

Writes report/generated/extra.tex (macros \\xFc, \\xPM, ... and \\p... parameters, listed in the file). Sources:
  - design/work/bench_loop.cir (differential loop gain, Middlebrook series injection; `Vext` = output offset)
  - a CM-loop copy of design/work/amp.inc with the CMFB output (gates of M7C/M8C) broken by a series AC source
  - results/<tag>/summary.json and the runs of design/final/amp_tran.asc / amp_noise.asc
  - a copy of the final noise netlist with Rin and Rfb left noisy; the gm/ID tables (tools/gmid/) for the fT ratio
design/work is the netlist the drawn .asc is proven equivalent to (verify_circuit), so the numbers apply to it.
Every simulated number in the report text comes from this file or from generated/results.tex.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gmid as G  # noqa: E402
import lt  # noqa: E402
import metrics as M  # noqa: E402

REPO = lt.REPO
WORK = REPO / "design" / "work"
FINAL = REPO / "design" / "final"
OUT = REPO / "results" / "report_extra"


def loop(vext: float) -> dict:
    f = WORK / "bench_loop.cir"
    txt = lt.fix_netlist(lt.inline_includes(lt.read_text(f), f.parent))
    OUT.mkdir(parents=True, exist_ok=True)
    n = OUT / f"loop_{vext:+.2f}.net"
    n.write_text(lt.set_params(txt, {"Vext": f"{vext:.6g}"}))
    r = lt.run(n)
    if not (r["ok"] and r["raw"]):
        raise SystemExit(f"loop run failed: {r['errors']}")
    return M.loop_metrics(r["raw"])


def cm_loop() -> dict:
    """CM loop gain with the loop broken at the CMFB output (vcmfb -> gates of the CMFB load units)."""
    amp = lt.read_text(WORK / "amp.inc")
    out = []
    for line in amp.splitlines():
        t = line.split()
        if len(t) > 4 and t[0].lower().startswith("m") and t[2].lower() == "vcmfb" and t[1].lower() != "vcmfb":
            t[2] = "vcmfbx"
            line = " ".join(t)
        out.append(line)
    out.append("Vcmbrk vcmfbx vcmfb 0 AC 1")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "amp_cmloop.inc").write_text("\n".join(out) + "\n")
    bl = lt.read_text(WORK / "bench_loop.cir").replace("AC 0.5", "").replace("AC -0.5", "")
    bl = bl.replace(".include amp.inc", ".include amp_cmloop.inc").replace(".ac dec 100 1 10G", ".ac dec 100 10 10G")
    bl = "\n".join(l for l in bl.splitlines() if not l.lower().startswith(".meas"))
    n = OUT / "cmloop.cir"
    n.write_text(bl)
    r = lt.run(n)
    if not (r["ok"] and r["raw"]):
        raise SystemExit(f"CM loop run failed: {r['errors']}")
    raw = M.Raw(r["raw"])
    fr = raw.x.real
    T = -raw["V(vcmfb)"] / raw["V(vcmfbx)"]
    mag = 20 * np.log10(np.abs(T))
    i = np.where((mag[:-1] > 0) & (mag[1:] <= 0))[0][0]
    ph = math.degrees(np.angle(T[i]))
    return {"T0": float(mag[0]), "fc": float(fr[i]), "pm": 180.0 - abs(ph)}


def small_step(vstep_small: float = 0.012) -> dict:
    """tran_metrics of the final transient netlist with a 1 % output step: the purely linear response
    (tau = T38.6 - T30, and the small-signal 20 log(1/beta) gap right after the step)."""
    net = lt.read_text(FINAL / "amp_tran.net")
    net = lt.set_params(net, {"VoutStep": f"{vstep_small:.6g}"})
    OUT.mkdir(parents=True, exist_ok=True)
    n = OUT / "small_step.net"
    n.write_text(net)
    r = lt.run(n)
    if not (r["ok"] and r["raw"]):
        raise SystemExit(f"small-step run failed: {r['errors']}")
    return M.tran_metrics(r["raw"], n)


def step_op(sign: int) -> tuple[float, str]:
    """Worst saturation margin with the inputs held at their final values (output at +-Vstep/2 per side)."""
    net = lt.read_text(FINAL / "amp_tran.net")
    s = "+" if sign > 0 else "-"
    o = "-" if sign > 0 else "+"
    net = re.sub(r"(?m)^Vinp inp 0 PULSE\(.*$", f"Vinp inp 0 {{VCMI{s}VinStep/2}}", net)
    net = re.sub(r"(?m)^Vinn inn 0 PULSE\(.*$", f"Vinn inn 0 {{VCMI{o}VinStep/2}}", net)
    n = OUT / f"step_op_{'p' if sign > 0 else 'n'}.net"
    n.write_text(net)
    devs = lt.run(n, op=True)["devices"]
    worst = min((d["margin"], nm) for nm, d in devs.items() if "margin" in d and abs(d["Id"]) > 1e-8)
    out = min((d["margin"], nm) for nm, d in devs.items() if nm in ("m9", "m10", "m11", "m12"))
    return worst, out


def long_tran(t_ns: float = 2000.0) -> float:
    """Abeta at the end of a long transient of the final netlist (the error left when the Cls/Rb high-pass has relaxed)."""
    net = lt.read_text(FINAL / "amp_tran.net")
    net = re.sub(r"(?m)^\.tran .*$", f".tran 0 {t_ns:g}n 0 20p", net)
    n = OUT / "long_tran.net"
    n.write_text(net)
    r = lt.run(n)
    if not (r["ok"] and r["raw"]):
        raise SystemExit(f"long transient failed: {r['errors']}")
    raw = M.Raw(r["raw"])
    vstep = M.net_params(n)["voutstep"]
    e = vstep - (np.real(raw["V(von)"]) - np.real(raw["V(vop)"]))
    return 20 * math.log10(vstep / (abs(float(e[-1])) + 1e-9))


def tolerance(ibnp: float) -> tuple[float, str]:
    """Worst settling time when one of Cc, Rz, Cls or Ibnp is 1 % off (the margin that sets the bias, page 8)."""
    from concurrent.futures import ThreadPoolExecutor

    base = lt.set_params(lt.read_text(FINAL / "amp_tran.net"), {"Ibnp": f"{ibnp:.6g}"})
    p0 = M.net_params(FINAL / "amp_tran.net")
    nom = {"Cc": p0["cc"], "Rz0": p0["rz0"], "Cls": p0["cls"], "Ibnp": ibnp}
    OUT.mkdir(parents=True, exist_ok=True)

    def one(job):
        k, s = job
        n = OUT / f"tol_{ibnp*1e9:.0f}n_{k}{'p' if s > 0 else 'm'}.net"
        n.write_text(lt.set_params(base, {k: f"{nom[k] * (1 + 0.01 * s):.6g}"}))
        r = lt.run(n)
        if not (r["ok"] and r["raw"]):
            raise SystemExit(f"tolerance run failed: {r['errors']}")
        m = M.tran_metrics(r["raw"], n)
        Path(r["raw"]).unlink(missing_ok=True)
        return max(m["Tsettle_A_ns"], m["Tsettle_Abeta_ns"]), k

    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, [(k, s) for k in nom for s in (-1, 1)]))
    return max(res)


def noisy_rin_rfb() -> tuple[float, float]:
    """Amplifier noise and SNR of the final noise netlist with Rin and Rfb left noisy (the FAQ allows noiseless)."""
    net, n_sub = re.subn(r"(?m)^(R(?:in|fb)\d\s.*?)\s+noiseless[ \t]*\r?$", r"\1", lt.read_text(FINAL / "amp_noise.net"))
    if n_sub != 4:
        raise SystemExit(f"expected 4 noiseless resistors (Rin, Rfb per side), found {n_sub}")
    OUT.mkdir(parents=True, exist_ok=True)
    n = OUT / "noisy_rin_rfb.net"
    n.write_text(net)
    r = lt.run(n)
    if not (r["ok"] and "vn_amp" in r["meas"] and "snr_db" in r["meas"]):
        raise SystemExit(f"noisy Rin/Rfb run failed: {r['errors']}")
    return r["meas"]["vn_amp"], r["meas"]["snr_db"]


def dev_tex(name: str) -> str:
    """m7c -> M_{7C}, mbp0 -> M_{BP0}."""
    return "M_{" + name[1:].upper() + "}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="final")
    a = ap.parse_args(argv)
    s = json.loads((REPO / "results" / a.tag / "summary.json").read_text())
    tab = {r["item"]: r["achieved"] for r in s["table"]}
    x = s["extra"]
    vstep = tab[14]
    mid, ext = loop(0.0), loop(vstep)
    cm = cm_loop()
    small = small_step()
    tau_small, t30_small = small["tau_ns"], small["T30_ns"]

    # noise split from the final noise run: device groups, thermal vs flicker
    nr = M.Raw(FINAL / "amp_noise.raw")
    fq = nr.x.real
    band = (fq >= 1e4) & (fq <= 1e11)
    p2 = lambda name: float(np.trapezoid(np.abs(nr[name][band]) ** 2, fq[band])) if name.lower() in nr.names else 0.0
    on2 = p2("V(onoise)")
    groups = {"in": ("m1", "m2"), "load": ("m7", "m8", "m7c", "m8c"), "casc": ("m3", "m4", "m5", "m6"),
              "rz": ("rz1", "rz2"), "st2": ("m9", "m10", "m11", "m12"), "rb": ("rb1", "rb2"), "cmfb": ("rcm1", "rcm2", "mc0", "mc1", "mc2", "mc3", "mc4")}
    gsh = {k: sum(p2(f"V({d})") for d in v) / on2 * 100 for k, v in groups.items()}
    # the four shares page 8 lists, rounded so that they and "the rest" add up to 100 (largest remainder)
    shown = {k: gsh[k] for k in ("in", "load", "rz", "st2")}
    shown["rest"] = 100 - sum(shown.values())
    ints = {k: math.floor(v) for k, v in shown.items()}
    for k in sorted(shown, key=lambda k: shown[k] - ints[k], reverse=True)[:100 - sum(ints.values())]:
        ints[k] += 1
    fl_tot = sum(p2(n) for k, n in nr.names.items() if k.endswith(".1overf)"))
    dev_uv = lambda d: math.sqrt(p2(f"V({d})")) * 1e6
    fl_uv = lambda d: math.sqrt(p2(f"V({d}.1overf)")) * 1e6

    # operating point (quiescent) of the final drawn netlist
    r_op = lt.run(FINAL / "amp_tran.net", op=True)
    devs = r_op["devices"]
    op_raw = M.Raw(Path(r_op["net"]).with_suffix(".raw"))  # full-precision currents (the log table has 3 digits)
    qmarg, qname = min((d["margin"], n) for n, d in devs.items() if "margin" in d and abs(d["Id"]) > 1e-8)
    (smp, snp), outp = step_op(+1)
    (smn, snn), outn = step_op(-1)
    smarg, sname = min((smp, snp), (smn, snn))
    omarg, oname = min(outp, outn)
    ab_long = long_tran()
    p_bias = M.net_params(FINAL / "amp_tran.net")["ibnp"]
    tol_ts, _ = tolerance(p_bias)
    next_ib = round(p_bias * 1e6 - 0.1, 1) * 1e-6
    tol_next_ts, tol_next_dev = tolerance(next_ib)
    pp = M.net_params(FINAL / "amp_tran.net")

    # transient: CM excursion, error kick, EE4520-style tau (40 to 48.69 dB)
    r = M.Raw(FINAL / "amp_tran.raw")
    t = r.x.real
    t0 = pp["tstep"]
    vcm = (np.real(r["V(vop)"]) + np.real(r["V(von)"])) / 2
    c0 = float(np.interp(t0 - 0.1e-9, t, vcm))
    dev = vcm - c0
    k = t > t0
    i_pk = int(np.argmax(np.abs(dev[k])))
    err = vstep - (np.real(r["V(von)"]) - np.real(r["V(vop)"]))
    ab = 20 * np.log10(vstep / (np.abs(err) + 1e-9))
    t_at = lambda lev: float(t[k][np.argmax(ab[k] >= lev)])
    tau_mid = t_at(40 + 20 * math.log10(math.e)) - t_at(40.0)
    # overshoot: largest error of the opposite sign after the first zero crossing
    ov = -err[k]
    i_ov = int(np.argmax(ov))
    overshoot, t_ov = float(ov[i_ov]), float(t[k][i_ov] - t0)
    overshoot_final = float(np.max(err[-1] - err[k]))  # above the settled (static-error) value
    # zero crossings of both errors (the spikes in D4); an exact zero sample keeps the previous sign
    kz = t > t0 + 1e-9

    def crossings(e: np.ndarray) -> np.ndarray:
        s = np.sign(e[kz])
        s = s[np.maximum.accumulate(np.where(s != 0, np.arange(len(s)), 0))]
        return (t[kz][np.where(s[1:] != s[:-1])[0] + 1] - t0) * 1e9

    zc_a = crossings(np.real(r["V(vip)"]) - np.real(r["V(vin)"]))
    zc_ab = crossings(err)
    if len(zc_a) < 2 or len(zc_ab) < 2:
        raise SystemExit(f"expected two zero crossings per error, got A {zc_a} and Abeta {zc_ab}")
    if abs(zc_a[0] - x["first_peak_A_ns"]) > 0.05 or abs(zc_ab[0] - x["first_peak_Abeta_ns"]) > 0.05:
        raise SystemExit(f"first crossings {zc_a[0]:.3f}/{zc_ab[0]:.3f} ns differ from evaluate.py's first peaks")
    a_end = 20 * math.log10(vstep / (abs(float(np.real(r["V(vip)"])[-1] - np.real(r["V(vin)"])[-1])) + 1e-9))
    ab_end = float(ab[-1])
    tw = x.get("tau_windows_ns", {})
    x1 = {n: np.real(r[f"V({n})"]) for n in ("x1p", "x1n", "gp1", "gp2")}
    x1sw = max(float(np.max(np.abs(v[k] - np.interp(t0 - 0.1e-9, t, v)))) for v in (x1["x1p"], x1["x1n"]))
    gpsw = max(float(np.max(np.abs(v[k] - np.interp(t0 - 0.1e-9, t, v)))) for v in (x1["gp1"], x1["gp2"]))
    # output-stage current peak (rising side PMOS) during the step
    i11 = np.abs(np.real(r["Id(M11)"])) if "id(m11)" in r.names else None
    i12 = np.abs(np.real(r["Id(M12)"])) if "id(m12)" in r.names else None
    ipk = max(float(np.max(i[k])) for i in (i11, i12)) * 1e6 if i11 is not None else math.nan
    # actual vs ideal beta (TA, 7 Nov 2026: explain it). The full step drives the summing nodes apart and nearly
    # turns one input device off, so the gap seen at the full step differs from the small-signal one.
    w1 = (t >= t0) & (t <= t0 + 1e-9)
    vx_step = float(np.max(np.abs(np.real(r["V(vin)"])[w1] - np.real(r["V(vip)"])[w1])))
    id_off = float(np.min(np.minimum(np.abs(np.real(r["Id(M1)"])[w1]), np.abs(np.real(r["Id(M2)"])[w1]))))

    # two-pole estimate from the loop (fc, PM): dominant closed-loop pole
    wc = 2 * math.pi * mid["fc_Hz"]
    p2w = wc / math.tan(math.radians(90.0 - min(mid["PM_deg"], 89.0)))
    kk = wc * math.sqrt(1 + (wc / p2w) ** 2)
    disc = p2w * p2w - 4 * p2w * kk
    tau_2p = 1.0 / ((p2w - math.sqrt(max(disc, 0.0))) / 2)

    # Deliverable 6 at full precision (EE4520 numbers: reference/ee4520/, gain-8 network 18p / 2.25p / 18p)
    kT = M.K_B * M.T_K
    e_p, e_tau, e_snr, e_vn = 0.1119e-3, 497.4e-9, 80.85, 76.93e-6
    e_ktc = math.sqrt(2 * kT * (18e-12 / 2.25e-12 ** 2 + 1 / 2.25e-12 + 1 / 18e-12))
    e_snr_k = 20 * math.log10(0.8485 / math.hypot(e_vn, e_ktc))
    efom = lambda snr_: snr_ - 10 * math.log10(2 * math.pi * e_p * e_tau)
    d_p = -10 * math.log10(tab[8] * 1e-3 / e_p)
    d_t = -10 * math.log10(tab[7] * 1e-9 / e_tau)
    d_s = tab[1] - e_snr_k
    d_tot = d_p + d_t + d_s
    sh_now = tab[10] ** 2 / (tab[10] ** 2 + tab[11] ** 2)
    sh_ee = e_ktc ** 2 / (e_ktc ** 2 + e_vn ** 2)
    d_net, d_beta = 10 * math.log10(146 / 42), 10 * math.log10(0.2 * 9)
    d_shape = 10 * math.log10(tau_2p * 1e9 / tab[7])
    d_share = 10 * math.log10(sh_now / sh_ee)
    d_swing = 20 * math.log10(tab[14] / 1.2)
    # the remainder absorbs rounding, so the displayed parts add up exactly to the displayed total
    d_amp = round(d_tot, 2) - sum(round(v, 2) for v in (d_net, d_beta, d_shape, d_share, d_swing))
    cin, cfb = tab[15] * 1e-12, tab[16] * 1e-12
    cp = cfb / x["beta_actual"] - cin - cfb
    cp_small = cfb / small["beta_actual"] - cin - cfb  # small-signal Cp, compare with the .op Cgg of one input device

    # The FoM in the course's efficiency terms (Bult, lecture 1: tau = C_L,eff/(beta gm), gm = (gm/ID) ID, eta_cur,
    # noise share). Reference: one single-stage amplifier in this test circuit, all current in its input pair,
    # kT/C noise only: FoM_1 = 2 pi (2 VDD/(gm/ID)) (C_L,eff/(beta Cin)) 84 kT/Vstep^2, independent of Cin and I.
    # Exact identity: FoM = FoM_1(gm/ID of my pair) - 10log(I_tot/I_pair) + 10log(kT/C share) + 10log(tau_1/tau).
    i_pair, i_tot = abs(float(op_raw["Id(M0)"][0].real)), tab[9] * 1e-3
    cleff, beta0, vdd = x["C_Leff_pF"] * 1e-12, x["beta_ideal"], 1.8
    fom1 = lambda gmid: -10 * math.log10(2 * math.pi * (2 * vdd / gmid) * (cleff / (beta0 * cin)) * 84 * kT / vstep ** 2)
    gmid1 = devs["m1"]["gm_id"]
    tau_1 = cleff / (beta0 * devs["m1"]["Gm"])
    l_cur = -10 * math.log10(i_tot / i_pair)
    l_noise = 10 * math.log10(tab[10] ** 2 / tab[12] ** 2)
    g_tau = 10 * math.log10(tau_1 / (tab[7] * 1e-9))
    assert abs(fom1(gmid1) + l_cur + l_noise + g_tau - tab[22]) < 0.01, "FoM accounting does not close"
    # displayed parts add up exactly to the displayed FoM (the tau term absorbs the rounding)
    g_tau_disp = round(tab[22], 2) - sum(round(v, 2) for v in (fom1(gmid1), l_cur, l_noise))
    iq, iw = x["I_quiescent_mA"] * 1e3, x["I_settle_window_mA"] * 1e3
    m1, m9, m11 = devs["m1"], devs["m9"], devs["m11"]
    rz = pp["rz0"] * (20 / pp["m2"]) * ((pp["cc"] + 1.2 * pp["cin"]) / pp["cc"]) / 4

    # why the stage-2 driver is NMOS: fT of NMOS vs PMOS at the driver's length and gm/ID (LTspice gm/ID tables)
    def ft(typ: str) -> float:
        sl = G._slice(G.load(typ), pp["ld"], 5e-6)
        return float(np.interp(G._at_gmid(sl, m9["gm_id"]), np.arange(len(sl["ft"])), sl["ft"]))

    ft_ratio = ft("nch") / ft("pch")
    vn_noisy, snr_noisy = noisy_rin_rfb()
    macros = {
        "xFc": f"{mid['fc_Hz']/1e6:.2f}", "xPM": f"{mid['PM_deg']:.1f}", "xGM": f"{mid.get('GM_dB', math.nan):.1f}",
        "xTzero": f"{mid['T0_dB']:.1f}", "xTzeroExt": f"{ext['T0_dB']:.1f}", "xFcExt": f"{ext['fc_Hz']/1e6:.1f}",
        "xPMExt": f"{ext['PM_deg']:.1f}", "xTauWc": f"{1e3/(2*math.pi*round(mid['fc_Hz']/1e6, 2)):.2f}", "xTauTwoPole": f"{tau_2p*1e9:.2f}",
        "xCMfc": f"{cm['fc']/1e6:.1f}", "xCMpm": f"{cm['pm']:.0f}", "xCMtzero": f"{cm['T0']:.1f}",
        "xCMexc": f"{abs(dev[k][i_pk])*1e3:.1f}", "xCMexcT": f"{(t[k][i_pk]-t0)*1e9:.1f}",
        "xCMexcTf": f"{abs(float(np.interp(t0 + 25e-9, t, dev)))*1e3:.1f}", "xVcm": f"{c0:.3f}",
        "xTauSmall": f"{tau_small:.2f}", "xTthirtySmall": f"{t30_small:.1f}", "xTauMid": f"{tau_mid*1e9:.2f}", "xTauExact": f"{tab[7]:.4f}",
        "xXswing": f"{x1sw*1e3:.0f}", "xGpswing": f"{gpsw*1e3:.0f}", "xIpk": f"{ipk:.0f}",
        "xOvershoot": f"{overshoot*1e6:.0f}", "xOvershootFinal": f"{overshoot_final*1e6:.0f}", "xOvershootT": f"{t_ov*1e9:.1f}",
        "xZcBackA": f"{zc_a[1]:.1f}", "xZcBackAb": f"{zc_ab[1]:.1f}",
        "xVnNoisyR": f"{vn_noisy*1e6:.2f}", "xSNRNoisyR": f"{snr_noisy:.2f}", "xFtRatio": f"{ft_ratio:.1f}",
        "xTauWforty": f"{tw.get('40-48.6dB', math.nan):.2f}", "xTauWfifty": f"{tw.get('50-58.6dB', math.nan):.2f}",
        "xAbEnd": f"{ab_end:.1f}", "xAEnd": f"{a_end:.1f}", "xGapEnd": f"{a_end-ab_end:.1f}", "xTend": f"{(t[-1]-t0)*1e9:.0f}",
        "xAbLong": f"{ab_long:.1f}", "xOutMarg": f"{omarg*1e3:.0f}", "xOutDev": dev_tex(oname),
        "xEKTC": f"{e_ktc*1e6:.0f}", "xESNR": f"{e_snr_k:.2f}", "xEFoMspec": f"{efom(80.64):.2f}",
        "xEFoMach": f"{efom(e_snr):.2f}", "xEFoM": f"{efom(e_snr_k):.2f}", "xDP": f"{d_p:+.2f}", "xDT": f"{d_t:+.2f}",
        "xDS": f"{d_s:+.2f}", "xDTot": f"{d_tot:+.2f}", "xDNet": f"{d_net:+.2f}", "xDBeta": f"{d_beta:+.2f}",
        "xDShape": f"{d_shape:+.2f}", "xDShare": f"{d_share:+.2f}", "xDSwing": f"{d_swing:+.2f}", "xDAmp": f"{d_amp:+.2f}",
        "xShareNow": f"{100*sh_now:.0f}", "xShareEE": f"{100*sh_ee:.0f}", "xPratio": f"{tab[8]*1e-3/e_p:.2f}",
        "xTauRatio": f"{e_tau/(tab[7]*1e-9):.0f}", "xCapRatio": f"{18/tab[15]:.1f}", "xPTauOld": f"{e_p*e_tau*1e15:.1f}",
        "xStepMarg": f"{smarg*1e3:.0f}", "xStepDev": dev_tex(sname), "xQMarg": f"{qmarg*1e3:.0f}", "xQDev": dev_tex(qname),
        "xIq": f"{iq:.1f}", "xIwin": f"{iw:.1f}", "xIslew": f"{iw - iq:.1f}",
        "xNshIn": f"{ints['in']}", "xNshLoad": f"{ints['load']}", "xNshCasc": f"{gsh['casc']:.0f}",
        "xNshRz": f"{ints['rz']}", "xNshStTwo": f"{ints['st2']}", "xNshRb": f"{gsh['rb']:.1f}",
        "xNshCmfb": f"{gsh['cmfb']:.1f}",
        "xNin": f"{dev_uv('m1'):.0f}", "xNload": f"{dev_uv('m7'):.0f}", "xNrz": f"{dev_uv('rz1'):.0f}",
        "xFlickUV": f"{math.sqrt(fl_tot)*1e6:.0f}", "xFlickShare": f"{fl_tot/on2*100:.0f}",
        "xFlickIn": f"{fl_uv('m1'):.0f}", "xFlickLoad": f"{fl_uv('m7'):.0f}",
        "xIdIn": f"{m1['Id']*1e6:.1f}" if m1['Id'] > 0 else f"{-m1['Id']*1e6:.1f}", "xGmOne": f"{m1['Gm']*1e3:.3f}",
        "xGmIdIn": f"{m1['gm_id']:.1f}", "xIdTwo": f"{abs(m9['Id'])*1e6:.1f}", "xGmNine": f"{m9['Gm']*1e3:.3f}",
        "xGmEleven": f"{m11['Gm']*1e3:.3f}", "xGmIdNine": f"{m9['gm_id']:.1f}", "xGmIdEleven": f"{m11['gm_id']:.1f}",
        "xCp": f"{cp*1e15:.0f}",
        "xCpSmall": f"{cp_small*1e15:.0f}", "xBetaSmall": f"{small['beta_actual']:.4f}",
        "xGapSmall": f"{small['gap_dB']:.2f}", "xCggIn": f"{devs['m1']['Cgg']*1e15:.1f}",
        "xVxStep": f"{vx_step*1e3:.0f}", "xIdOff": f"{id_off*1e6:.1f}",
        "xTsSlack": f"{25 - tab[4]:.1f}", "xTolMargin": f"{25 - tol_ts:.1f}", "xTolNext": f"{next_ib*1e6:.1f}",
        "xTolNextMargin": f"{25 - tol_next_ts:.1f}",
        "xTolNextDev": {"Cc": "$C_c$", "Rz0": "$R_z$", "Cls": "$C_{ls}$", "Ibnp": "$I_{bnp}$"}[tol_next_dev],
        "xFoMideal": f"{fom1(25.0):.1f}", "xFoMone": f"{fom1(gmid1):.2f}", "xLcur": f"{l_cur:+.2f}",
        "xEtaCur": f"{100*i_pair/i_tot:.0f}", "xLnoise": f"{l_noise:+.2f}", "xGtau": f"{g_tau_disp:+.2f}",
        "xTauOne": f"{tau_1*1e9:.1f}",
        "pIbnp": f"{pp['ibnp']*1e6:.2f}", "pN": f"{pp['n']:.0f}", "pNcm": f"{pp['ncm']:.0f}", "pMtwo": f"{pp['m2']:.0f}",
        "pMcmt": f"{pp['mcmt']:.0f}", "pKcn": f"{pp['kcn']:.2f}", "pKcp": f"{pp['kcp']:.2f}", "pRd": f"{pp['rdec']/1e3:.0f}",
        "pCc": f"{pp['cc']*1e12:.3f}", "pRz": f"{rz/1e3:.2f}", "pCls": f"{pp['cls']*1e12:.2f}", "pRb": f"{pp['rb']/1e6:.0f}",
        "pRcm": f"{pp['rcm']/1e6:.0f}", "pCcm": f"{pp['ccm']*1e15:.0f}", "pVcmi": f"{pp.get('vcmi', 0.9):.2f}",
        "pLl": f"{pp['ll']*1e6:.1f}", "pLi": f"{pp['li']*1e6:.2f}", "pLt": f"{pp['lt']*1e6:.1f}", "pLd": f"{pp['ld']*1e6:.2f}",
    }
    lines = ["% generated by tools/report_extra.py; do not edit by hand", f"% from results/{a.tag}/summary.json"]
    lines += [f"\\newcommand{{\\{kk_}}}{{{v}}}" for kk_, v in macros.items()]
    out = REPO / "report" / "generated" / "extra.tex"
    out.write_text("\n".join(lines) + "\n")
    for kk_, v in macros.items():
        print(f"{kk_:12s} {v}")
    print("->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
