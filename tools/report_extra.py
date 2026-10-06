#!/usr/bin/env python3
"""Extra report macros measured on the final design: loop gain, CM loop, CM excursion, noise and power split.

  uv run tools/report_extra.py [--tag final]

Writes report/generated/extra.tex (macros \\xFc, \\xPM, ... listed in the file). Sources:
  - design/work/bench_loop.cir (differential loop gain, Middlebrook series injection; `Vext` = output offset)
  - a CM-loop copy of design/work/amp.inc with the CMFB-controlled gate broken by a series AC source
  - results/<tag>/summary.json and the transient raw of design/final/amp_tran.asc (CM excursion)
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
import lt  # noqa: E402
import metrics as M  # noqa: E402

REPO = lt.REPO
WORK = REPO / "design" / "work"


def loop(vext: float) -> dict:
    f = WORK / "bench_loop.cir"
    txt = lt.fix_netlist(lt.inline_includes(lt.read_text(f), f.parent))
    d = REPO / "results" / "report_extra"
    d.mkdir(parents=True, exist_ok=True)
    n = d / f"loop_{vext:+.2f}.net"
    n.write_text(lt.set_params(txt, {"Vext": f"{vext:.6g}"}))
    r = lt.run(n)
    if not (r["ok"] and r["raw"]):
        raise SystemExit(f"loop run failed: {r['errors']}")
    out = M.loop_metrics(r["raw"])
    out["raw"] = r["raw"]
    return out


def miller(raw_path: str, fx: float = 1e3) -> tuple[float, float]:
    """|v(na)/v_gd| and |v(nb)/v_gd| (differential) at frequency fx from the loop-bench raw."""
    r = M.Raw(raw_path)
    f = r.x.real
    i = int(np.argmin(np.abs(f - fx)))
    d = lambda a, b: r[f"V({a})"][i] - r[f"V({b})"][i]
    vg = d("vin", "vip")
    return float(abs(d("na1", "na2") / vg)), float(abs(d("nb1", "nb2") / vg))


def cm_loop() -> dict:
    amp = lt.read_text(WORK / "amp.inc")
    out = []
    for line in amp.splitlines():
        t = line.split()
        if len(t) > 4 and t[0].lower().startswith("m") and t[2].lower() == "vcmfb" and t[1].lower() != "vcmfb":
            t[2] = "vcmfbx"
            line = " ".join(t)
        out.append(line)
    out.append("Vcmbrk vcmfbx vcmfb 0 AC 1")
    d = REPO / "results" / "report_extra"
    (d / "amp_cmloop.inc").write_text("\n".join(out) + "\n")
    bl = lt.read_text(WORK / "bench_loop.cir").replace("AC 0.5", "").replace("AC -0.5", "")
    bl = bl.replace(".include amp.inc", ".include amp_cmloop.inc").replace(".ac dec 100 1 10G", ".ac dec 100 10 10G")
    bl = "\n".join(l for l in bl.splitlines() if not l.lower().startswith(".meas"))
    n = d / "cmloop.cir"
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
    # T(0) is negative real (see report: an internal positive CM path makes the broken-loop gain negative);
    # the margin is the angular distance of T(j*fc) from the -180 degree axis.
    return {"T0": float(mag[0]), "fc": float(fr[i]), "margin": 180.0 - abs(ph)}


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
    mill_na, mill_nb = miller(mid["raw"])
    # flicker (1/f) part of the amplifier noise from the final noise run
    nr = M.Raw(REPO / "design" / "final" / "amp_noise.raw")
    fq = nr.x
    band = (fq >= 1e4) & (fq <= 1e11)
    fl = {k: float(np.trapezoid(np.abs(nr[v][band]) ** 2, fq[band])) for k, v in nr.names.items() if k.endswith(".1overf)")}
    fl_tot = sum(fl.values())
    on2 = float(np.trapezoid(np.abs(nr["V(onoise)"][band]) ** 2, fq[band]))
    # operating point of the input devices
    devs = lt.run(REPO / "design" / "final" / "amp_tran.net", op=True)["devices"]
    pp = M.net_params(REPO / "design" / "final" / "amp_tran.net")
    traw = REPO / "design" / "final" / "amp_tran.raw"
    r = M.Raw(traw)
    t = r.x
    p = M.net_params(REPO / "design" / "final" / "amp_tran.net")
    t0 = p["tstep"]
    vcm = (np.real(r["V(vop)"]) + np.real(r["V(von)"])) / 2
    c0 = float(np.interp(t0 - 0.1e-9, t, vcm))
    dev = np.abs(vcm - c0)
    k = t > t0
    i_pk = int(np.argmax(dev[k]))
    vo = np.real(r["V(von)"]) - np.real(r["V(vop)"])
    vg = np.real(r["V(vip)"]) - np.real(r["V(vin)"])
    ab_end = 20 * math.log10(vstep / (abs(vstep - abs(vo[-1])) + 1e-9))
    err = vstep - vo  # signed: > vstep while the output is pushed the wrong way by feedthrough
    # local time constant of the small-signal tail: fit ln of the decaying part (error minus its final, static value)
    # over [t_step+16 ns, t_step+24 ns]
    w = (t > t0 + 16e-9) & (t < t0 + 24e-9)
    tau_tail = -1.0 / np.polyfit(t[w], np.log(np.abs(err[w] - err[-1])), 1)[0]
    # wrong-way feedthrough kick right after the step (output error above the full step) and the Abeta dip
    e0 = (t > t0) & (t < t0 + 2e-9)
    kick = float(np.max(err[e0]) - vstep)
    ab_dip = float(20 * math.log10(vstep / np.max(np.abs(err[e0]))))
    a_end = 20 * math.log10(vstep / (abs(vg[-1]) + 1e-9))
    # Abeta curve features: EE4520-style tau (40 to 48.69 dB), slow component after the knee (e-fold 25 to 45 ns)
    k2 = t > t0
    ab = 20 * np.log10(vstep / (np.abs(err) + 1e-9))
    t_at = lambda lev: float(t[k2][np.argmax(ab[k2] >= lev)])
    tau_mid = t_at(40 + 20 * math.log10(math.e)) - t_at(40.0)
    e25, e45 = (float(np.interp(t0 + x, t, np.abs(err))) for x in (25e-9, 45e-9))
    ab45 = 20 * math.log10(vstep / e45)
    # decaying part of the error after the knee: error minus its final (static) value, 25 to 45 ns
    d25, d45 = (float(np.interp(t0 + x, t, err)) - float(err[-1]) for x in (25e-9, 45e-9))
    tau_slow = 20e-9 / math.log(abs(d25) / abs(d45))
    gap_end = a_end - ab_end
    # two-pole closed loop with the measured fc and PM: dominant pole factor r (s = -r * wc)
    # T(s) = K / (s (1 + s/p2)) with |T(j wc)| = 1 and the measured PM: p2 = wc / tan(90 - PM), K = wc sqrt(1 + (wc/p2)^2)
    wc = 2 * math.pi * mid["fc_Hz"]
    p2 = wc / math.tan(math.radians(90.0 - mid["PM_deg"]))
    kk = wc * math.sqrt(1 + (wc / p2) ** 2)
    tau_2p = 1.0 / ((p2 - math.sqrt(max(p2 * p2 - 4 * p2 * kk, 0.0))) / 2)
    # operating point with the step applied (inputs at their final values): saturation at the output extremes
    net = lt.read_text(REPO / "design" / "final" / "amp_tran.net")
    net = re.sub(r"(?m)^Vinp inp 0 PULSE\(.*$", "Vinp inp 0 {VCMI+VinStep/2}", net)
    net = re.sub(r"(?m)^Vinn inn 0 PULSE\(.*$", "Vinn inn 0 {VCMI-VinStep/2}", net)
    sn = REPO / "results" / "report_extra" / "step_op.net"
    sn.write_text(net)
    sdev = lt.run(sn, op=True)["devices"]
    smarg, sname = min((d["margin"], n) for n, d in sdev.items() if "margin" in d and abs(d["Id"]) > 1e-8)
    qmarg, qname = min((d["margin"], n) for n, d in devs.items() if "margin" in d and abs(d["Id"]) > 1e-8)
    noise = {k.lower(): v for k, v in x["noise_top_uVrms"].items()}
    vn = tab[11]
    share = sum(noise.get(f"v({d})", 0.0) ** 2 for d in ("m1n", "m2n", "m1p", "m2p")) / vn ** 2 * 100
    cin, cfb = tab[15] * 1e-12, tab[16] * 1e-12
    cp = cfb / x["beta_actual"] - cin - cfb
    iq, iw = x["I_quiescent_mA"] * 1e3, x["I_settle_window_mA"] * 1e3
    macros = {
        "xFc": f"{mid['fc_Hz']/1e6:.1f}", "xPM": f"{mid['PM_deg']:.1f}", "xGM": f"{mid['GM_dB']:.1f}",
        "xTzero": f"{mid['T0_dB']:.1f}", "xTzeroExt": f"{ext['T0_dB']:.1f}",
        "xCMfc": f"{cm['fc']/1e6:.1f}", "xCMpm": f"{cm['margin']:.0f}", "xCMtzero": f"{cm['T0']:.1f}",
        "xCMexc": f"{dev[k][i_pk]*1e3:.1f}", "xCMexcT": f"{(t[k][i_pk]-t0)*1e9:.1f}",
        "xCMexcTf": f"{float(np.interp(t0 + 25e-9, t, dev))*1e3:.1f}", "xVcm": f"{c0:.3f}",
        "xAbEnd": f"{ab_end:.1f}", "xTauTail": f"{tau_tail*1e9:.2f}", "xKick": f"{kick*1e3:.0f}",
        "xAbDip": f"{ab_dip:.2f}", "xTauMid": f"{tau_mid*1e9:.2f}", "xTauSlow": f"{tau_slow*1e9:.0f}",
        "xAbFortyFive": f"{ab45:.1f}", "xTauTwoPole": f"{tau_2p*1e9:.2f}", "xStepMarg": f"{smarg*1e3:.0f}",
        "xStepDev": sname.upper()[:1] + "_{" + sname[1:] + "}", "xQMarg": f"{qmarg*1e3:.0f}",
        "xQDev": qname.upper()[:1] + "_{" + qname[1:] + "}", "xGapEnd": f"{gap_end:.1f}", "xTauExact": f"{tab[7]:.4f}", "xAEnd": f"{a_end:.1f}", "xTend": f"{(t[-1]-t0)*1e9:.0f}",
        "xIq": f"{iq:.1f}", "xIwin": f"{iw:.1f}", "xIslew": f"{iw - iq:.1f}",
        "xNinN": f"{noise.get('v(m1n)', math.nan):.0f}", "xNinP": f"{noise.get('v(m1p)', math.nan):.0f}",
        "xNcasN": f"{noise.get('v(mcn1)', math.nan):.0f}", "xNcasP": f"{noise.get('v(mcp1)', math.nan):.0f}",
        "xNinShare": f"{share:.0f}",
        "xFlickUV": f"{math.sqrt(fl_tot)*1e6:.0f}", "xFlickShare": f"{fl_tot/on2*100:.0f}",
        "xFlickN": f"{math.sqrt(fl.get('v(m1n.1overf)', 0.0))*1e6:.0f}",
        "xFlickP": f"{math.sqrt(fl.get('v(m1p.1overf)', 0.0))*1e6:.0f}",
        "xMillNa": f"{mill_na:.0f}", "xMillNb": f"{mill_nb:.0f}",
        "xIdIn": f"{devs['m1n']['Id']*1e6:.1f}", "xGmN": f"{devs['m1n']['Gm']*1e3:.3f}",
        "xGmP": f"{devs['m1p']['Gm']*1e3:.3f}", "xGmIdN": f"{devs['m1n']['gm_id']:.1f}",
        "xGmIdP": f"{devs['m1p']['gm_id']:.1f}",
        "xGmOne": f"{(devs['m1n']['Gm'] + devs['m1p']['Gm'])*1e3:.3f}",
        "pIb": f"{pp['ib']*1e6:.1f}", "pMt": f"{pp['mt']:.0f}", "pKo": f"{pp['ko']:.3f}", "pKn": f"{pp['kn']:.3f}",
        "pKcn": f"{pp['kcn']:.2f}", "pKcp": f"{pp['kcp']:.3f}", "pCc": f"{pp['cc']*1e12:.3f}",
        "pCls": f"{pp['cls']*1e12:.2f}", "pConed": f"{pp.get('c1d', 0.0)*1e15:.1f}", "pVcmi": f"{pp.get('vcmi', 0.9):.3f}",
        "pTsc": f"{pp.get('tsc', 1.0):.3f}", "pLin": f"{pp['lin']*1e6:.3f}", "pLip": f"{pp['lip']*1e6:.2f}", "pFcc": f"{pp['fcc']:.3f}",
        "pRb": f"{pp['rb']/1e6:.0f}", "pRcm": f"{pp['rcm']/1e6:.0f}", "pCcm": f"{pp['ccm']*1e15:.0f}", "xCp": f"{cp*1e15:.0f}", "xFlicker": f"{x['flicker_corner_Hz_est']/1e3:.0f}",
    }
    lines = ["% generated by tools/report_extra.py; do not edit by hand", f"% from results/{a.tag}/summary.json"]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in macros.items()]
    out = REPO / "report" / "generated" / "extra.tex"
    out.write_text("\n".join(lines) + "\n")
    for k, v in macros.items():
        print(f"{k:12s} {v}")
    print("->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
