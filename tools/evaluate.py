#!/usr/bin/env python3
"""One-command evaluation of a design against every EE4525 spec (the definition of done).

  uv run tools/evaluate.py --tran design/amp_tran.asc --noise design/amp_noise.asc [--tag v07] [--publish]

Runs lint -> transient -> noise -> .op (all in LTspice XVII), computes the 22-row
Deliverable-1 table, prints PASS/FAIL with margins and over-design hints, and writes:
  results/<tag>/summary.json   full numbers + checks + file hashes
  results/<tag>/d4_settling.{pdf,png}, d5_noise.{pdf,png}
  results/latest.json          copy of the newest summary
  results/history.csv          one appended line per evaluation (best-so-far tracking)
With --publish (final candidate only) it also writes report/generated/results.tex,
report/generated/opvals.tex and copies the D4/D5 figures to report/figures/.
Exit code 0 only if every spec and rule check passes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asc_lint  # noqa: E402
import lt  # noqa: E402
import metrics as M  # noqa: E402

REPO = lt.REPO
# Margins the design must keep (robust to re-simulation noise; see brief/spec.md section 4)
MARGIN = {"SNR": 0.05, "A": 0.3, "Abeta": 0.3, "Tsettle_ns": 0.2}
EE4520 = {"P_mW": 0.1119, "tau_ns": 497.4, "SNR_dB": 80.85, "FoM_dB": 175.20}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:12]


def evaluate(tran: Path, noise: Path, tag: str, plots: bool = True) -> dict:
    out = REPO / "results" / tag
    out.mkdir(parents=True, exist_ok=True)
    lint_errs: list[str] = []
    for f in (tran, noise):
        if f.suffix.lower() == ".asc":
            e, _ = asc_lint.lint_asc_text(f.read_text(errors="replace"))
            lint_errs += [f"{f.name}: {x}" for x in e]

    rt = lt.run(tran)
    if not rt["ok"] or not rt["raw"]:
        raise SystemExit(f"transient run failed: {rt['errors']}")
    net_t = Path(rt["net"])
    e, _, _ = asc_lint.lint_netlist(net_t)
    lint_errs += [f"{net_t.name}: {x}" for x in e]
    tm = M.tran_metrics(rt["raw"], net_t)
    if plots:
        M.plot_settling(tm, out / "d4_settling.pdf")

    rn = lt.run(noise)
    if not rn["ok"] or not rn["raw"]:
        raise SystemExit(f"noise run failed: {rn['errors']}")
    nm = M.noise_metrics(rn["raw"])
    if plots:
        M.plot_noise(nm, out / "d5_noise.pdf")

    ro = lt.run(net_t, op=True)
    devs = ro.get("devices", {})
    mos = {n: d for n, d in devs.items() if "margin" in d}
    not_sat = sorted(n for n, d in mos.items() if d["margin"] < 0 and abs(d["Id"]) > 1e-8)
    min_margin = min((d["margin"] for d in mos.values() if abs(d["Id"]) > 1e-8), default=math.nan)

    p = M.net_params(net_t)
    cin, cfb, cl = p.get("cin"), p.get("cfb"), p.get("cload")
    vout = tm["VoutStep_V"]
    ktc = M.ktc_uV(cin)
    vn_amp = nm["Vn_amp_uVrms"]
    vn_tot = math.hypot(ktc, vn_amp)
    snr = M.snr_db(vout, vn_tot)
    P = tm.get("P_report_mW", math.nan)
    fom_lin, fom_db = M.fom(P, tm["tau_ns"], snr)
    beta = cfb / (cin + cfb)
    c_leff = cl + (1 - beta) * cfb
    kT = M.K_B * M.T_K
    nef_diff = (vn_amp * 1e-6) ** 2 / (2 * kT / (beta * c_leff))
    ts = max(tm["Tsettle_A_ns"], tm["Tsettle_Abeta_ns"])

    table = [
        (1, "SNR", "dB", "66", snr),
        (2, "Abeta settle (loop settling)", "dB", "66", tm["Abeta_at_25ns_dB"]),
        (3, "A settle (amplifier settling)", "dB", ">78", tm["A_at_25ns_dB"]),
        (4, "T settle (to required accuracy)", "ns", "25", ts),
        (5, "T30dB", "ns", "-", tm["T30_ns"]),
        (6, "T38.6dB", "ns", "-", tm["T38p6_ns"]),
        (7, "tau = T38.6dB - T30dB", "ns", "-", tm["tau_ns"]),
        (8, "Power dissipation (amplifiers only)", "mW", "<3, min", P),
        (9, "I(Vdd) (amplifiers only)", "mA", "<1.7, min", tm.get("I_report_mA", math.nan)),
        (10, "Total effective kT/C noise at output", "uVrms", "free", ktc),
        (11, "Total integrated amplifier noise", "uVrms", "free", vn_amp),
        (12, "Total integrated noise (10kHz-100GHz)", "uVrms", "free", vn_tot),
        (13, "Input step voltage (diff)", "mV", "Vout/4", vout / 4 * 1e3),
        (14, "Output step voltage (diff)", "V", "free", vout),
        (15, "Cin", "pF", "-", cin * 1e12),
        (16, "Cfb", "pF", "-", cfb * 1e12),
        (17, "Cload", "pF", "=Cin", cl * 1e12),
        (18, "CCM", "pF", "-", p.get("ccm", math.nan) * 1e12 if p.get("ccm") else math.nan),
        (19, "Rbig (Rfb)", "GOhm", "big", p.get("rfb", math.nan) / 1e9),
        (20, "Cbig", "nF", "big", (p.get("cbig") or p.get("cbias") or math.nan) * 1e9),
        (21, "FoM_lin = 2 pi P tau / SNR_lin^2", "J", "-", fom_lin),
        (22, "FoM_dB = -10 log10(FoM_lin)", "dB", ">170", fom_db),
    ]
    checks = {
        "SNR >= 66 dB (+margin)": snr >= 66 + MARGIN["SNR"],
        "Abeta(25ns) >= 66 dB (+margin)": tm["Abeta_at_25ns_dB"] >= 66 + MARGIN["Abeta"],
        "A(25ns) >= 78 dB (+margin)": tm["A_at_25ns_dB"] >= 78 + MARGIN["A"],
        "Abeta floor after 25ns >= 66 dB": tm["Abeta_floor_dB"] >= 66,
        "A floor after 25ns >= 78 dB": tm["A_floor_dB"] >= 78,
        "settled before 25 ns (-margin)": ts <= 25 - MARGIN["Tsettle_ns"],
        "first ringing peak after 25 ns": tm["checks"]["first_peak_after_25ns"],
        "sim runs >= 30 ns past deadline": tm["checks"]["sim_long_enough"],
        "Power < 3 mW": P < 3.0,
        "FoM_dB > 170": fom_db > 170,
        "all MOSFETs saturated": not not_sat,
        "lint: no errors": not lint_errs,
        "beta_actual <= beta_ideal (physics sanity)": tm["beta_actual"] <= beta * 1.01,
    }
    hints = []
    if snr > 66.6:
        hints.append(f"SNR {snr:.2f} dB is {snr-66:.2f} dB over spec: shrink Cin or swing headroom, or cut input-pair current")
    if tm["Abeta_at_25ns_dB"] > 68:
        hints.append(f"Abeta(25ns) {tm['Abeta_at_25ns_dB']:.1f} dB: settling has slack, cut bias current")
    if ts < 22:
        hints.append(f"settles at {ts:.1f} ns: {25-ts:.1f} ns of slack, cut bias current")
    summary = {
        "tag": tag,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "files": {str(tran): sha(tran), str(noise): sha(noise)},
        "all_pass": all(checks.values()),
        "checks": checks,
        "table": [{"item": i, "name": n, "unit": u, "spec": s, "achieved": v} for i, n, u, s, v in table],
        "extra": {
            "beta_ideal": beta, "beta_actual": tm["beta_actual"], "gap_dB": tm["gap_dB"],
            "Abeta_shift_at_25ns_dB": tm["Abeta_shift_at_25ns_dB"],
            "A_floor_dB": tm["A_floor_dB"], "Abeta_floor_dB": tm["Abeta_floor_dB"],
            "first_peak_A_ns": tm["first_peak_A_ns"], "first_peak_Abeta_ns": tm["first_peak_Abeta_ns"],
            "slew_max_V_per_us": tm["slew_max_V_per_us"], "I_quiescent_mA": tm.get("I_quiescent_mA"),
            "I_settle_window_mA": tm.get("I_settle_window_mA"), "NEF_diff": nef_diff, "C_Leff_pF": c_leff * 1e12,
            "min_sat_margin_mV": min_margin * 1e3, "not_saturated": not_sat, "n_mosfets": len(mos),
            "noise_top_uVrms": nm["top_contributors_uVrms"], "flicker_corner_Hz_est": nm["flicker_corner_Hz_est"],
            "lint_errors": lint_errs, "EE4520": EE4520,
        },
        "hints": hints,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    (out / "op.json").write_text(json.dumps(devs, indent=1, default=str))
    (REPO / "results" / "latest.json").write_text(json.dumps(summary, indent=1, default=str))
    hist = REPO / "results" / "history.csv"
    new = not hist.exists()
    with hist.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["time", "tag", "all_pass", "P_mW", "SNR_dB", "A25_dB", "Abeta25_dB", "Tsettle_ns",
                        "tau_ns", "FoM_dB", "first_peak_ns", "tran_sha", "noise_sha"])
        w.writerow([summary["time"], tag, summary["all_pass"], f"{P:.4f}", f"{snr:.3f}",
                    f"{tm['A_at_25ns_dB']:.3f}", f"{tm['Abeta_at_25ns_dB']:.3f}", f"{ts:.3f}", f"{tm['tau_ns']:.4f}",
                    f"{fom_db:.3f}", f"{min(tm['first_peak_A_ns'], tm['first_peak_Abeta_ns']):.2f}",
                    sha(tran), sha(noise)])
    return summary


def publish(summary: dict, tran_net: Path) -> None:
    gen = REPO / "report" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    names = {1: "SNR", 2: "Abeta", 3: "A", 4: "Tsettle", 5: "Tthirty", 6: "Tthirtyeight", 7: "Tau", 8: "Power",
             9: "Idd", 10: "KTC", 11: "VnAmp", 12: "VnTot", 13: "Vin", 14: "Vout", 15: "Cin", 16: "Cfb",
             17: "Cload", 18: "CCM", 19: "Rbig", 20: "Cbig", 21: "FoMlin", 22: "FoMdB"}
    fmt = {5: "{:.3f}", 6: "{:.3f}", 7: "{:.3f}", 8: "{:.4f}", 9: "{:.4f}", 13: "{:.2f}", 14: "{:.4f}", 15: "{:.4g}", 16: "{:.4g}", 17: "{:.4g}", 18: "{:.4g}", 19: "{:.3g}",
           20: "{:.3g}", 21: None}
    lines = ["% generated by tools/evaluate.py --publish; do not edit by hand",
             f"% tag {summary['tag']} at {summary['time']}"]
    for row in summary["table"]:
        v = row["achieved"]
        i = row["item"]
        if isinstance(v, float) and math.isnan(v):
            s = "--"
        elif i == 21:
            m, e = f"{v:.3e}".split("e")
            s = f"{m}\\times10^{{{int(e)}}}"
        else:
            s = (fmt.get(i) or "{:.2f}").format(v)
        lines.append(f"\\newcommand{{\\res{names[i]}}}{{{s}}}")
    x = summary["extra"]
    for k, v in (("BetaIdeal", x["beta_ideal"]), ("BetaActual", x["beta_actual"]), ("GapdB", x["gap_dB"]),
                 ("NEF", x["NEF_diff"]), ("FirstPeak", min(x["first_peak_A_ns"], x["first_peak_Abeta_ns"])),
                 ("Slew", x["slew_max_V_per_us"]), ("CLeff", x["C_Leff_pF"]),
                 ("FoMEEtwenty", x["EE4520"]["FoM_dB"])):
        lines.append(f"\\newcommand{{\\res{k}}}{{{v:.4g}}}")
    (gen / "results.tex").write_text("\n".join(lines) + "\n")
    out = REPO / "results" / summary["tag"]
    figs = REPO / "report" / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    for f in ("d4_settling.pdf", "d4_settling.png", "d5_noise.pdf", "d5_noise.png"):
        if (out / f).exists():
            shutil.copy2(out / f, figs / f)
    import opvals

    opvals.write_opvals(tran_net, gen / "opvals.tex")


def print_summary(s: dict) -> None:
    print(f"== {s['tag']}  {s['time']}  {'ALL PASS' if s['all_pass'] else 'NOT DONE'} ==")
    for r in s["table"]:
        v = r["achieved"]
        vs = f"{v:.4e}" if r["item"] == 21 else (f"{v:.4f}" if isinstance(v, float) else str(v))
        print(f"{r['item']:>2} {r['name']:40s} {r['unit']:6s} {r['spec']:>9s} {vs:>12s}")
    print("checks:")
    for k, ok in s["checks"].items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {k}")
    x = s["extra"]
    print(f"beta ideal {x['beta_ideal']:.4f} / actual {x['beta_actual']:.4f} (gap {x['gap_dB']:.2f} dB); "
          f"first peaks A {x['first_peak_A_ns']:.2f} ns, Abeta {x['first_peak_Abeta_ns']:.2f} ns; "
          f"floors A {x['A_floor_dB']:.2f} / Abeta {x['Abeta_floor_dB']:.2f} dB")
    print(f"I quiescent {x['I_quiescent_mA']:.4f} mA, settle-window {x['I_settle_window_mA']:.4f} mA; "
          f"NEF(diff) {x['NEF_diff']:.2f}; min sat margin {x['min_sat_margin_mV']:.0f} mV over {x['n_mosfets']} FETs")
    top = list(x["noise_top_uVrms"].items())[:4]
    print("noise top: " + ", ".join(f"{k} {v:.0f}uV" for k, v in top))
    for e in x["lint_errors"]:
        print("  lint:", e)
    for h in s["hints"]:
        print("  hint:", h)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tran", required=True)
    ap.add_argument("--noise", required=True)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--publish", action="store_true", help="write report/generated/*.tex and report figures")
    a = ap.parse_args(argv)
    tag = a.tag or time.strftime("run_%m%d_%H%M%S")
    s = evaluate(lt.guard(a.tran), lt.guard(a.noise), tag, plots=not a.no_plots)
    print_summary(s)
    if a.publish:
        net = lt.guard(a.tran)
        net = net.with_suffix(".net") if net.suffix.lower() == ".asc" else net
        publish(s, net)
        print("published -> report/generated/{results,opvals}.tex, report/figures/d4_*, d5_*")
    return 0 if s["all_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
