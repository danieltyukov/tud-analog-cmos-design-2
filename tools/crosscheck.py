#!/usr/bin/env python3
"""Independent end-to-end cross-checks of the final design and the report.

  uv run tools/crosscheck.py kcl [--asc design/final/amp_tran.asc]
      .op of the drawn schematic in LTspice; Kirchhoff's current law at every node from all four terminal
      currents of every MOSFET and the currents of every R, C, V, I; branch sums; I(Vdd) split into
      stage 1 + stage 2 + CMFB; replica current ratios; replica node voltages against the amplifier.
  uv run tools/crosscheck.py formulas
      recomputes every derived number of the report from results/latest.json (kT/C, total noise, SNR, power,
      tau, FoM, beta, Cp, C_Leff, NEF, the D6 terms) and checks each against the generated macro and that the
      displayed value is printed in report/main.pdf.
  uv run tools/crosscheck.py all

Exit code 1 if anything is off. Nothing here is used to produce report numbers; it only checks them.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lt  # noqa: E402
import metrics as M  # noqa: E402

REPO = lt.REPO


# ----------------------------------------------------------------------------- KCL


def kcl(asc: Path) -> int:
    r = lt.run(asc, op=True)
    if not r["ok"]:
        print("op run failed:", r["errors"])
        return 1
    net = Path(r["net"])
    raw = M.Raw(net.with_suffix(".raw"))
    val = lambda n: float(raw[n][0].real)
    has = raw.has
    bad = 0

    into = defaultdict(float)  # node -> current flowing from the node into element terminals
    elems = []
    for line in lt.read_text(net).splitlines():
        t = line.split()
        if not t or t[0][0] in "*.;+":
            continue
        name, k = t[0], t[0][0].upper()
        if k == "M":
            d, g, s, b = t[1:5]
            for term, node in (("Id", d), ("Ig", g), ("Is", s), ("Ib", b)):
                into[node.lower()] += val(f"{term}({name})")
            elems.append((name, d, g, s, b))
        elif k in "RCVI":
            a, b_ = t[1:3]
            i = val(f"I({name})") if has(f"I({name})") else 0.0
            into[a.lower()] += i
            into[b_.lower()] -= i
            elems.append((name, a, b_))
    worst = sorted(((abs(v), n) for n, v in into.items() if n != "0"), reverse=True)
    print(f"KCL over {len(worst)} nodes: worst residual {worst[0][0] * 1e12:.3g} pA at {worst[0][1]}")
    off = [(n, v) for v, n in worst if v > 1e-9]
    if off:
        print("  nodes with |residual| > 1 nA:", off)
        bad += 1

    I = lambda m: abs(val(f"Id({m})")) * 1e6
    rows = [
        ("tail: M0 = M1 + M2", I("M0"), I("M1") + I("M2")),
        ("half: M1 = M3 = M5 (mean)", I("M1"), (I("M3") + I("M5")) / 2),
        ("half p: M5 = M7 + M7C", I("M5"), I("M7") + I("M7C")),
        ("half n: M6 = M8 + M8C", I("M6"), I("M8") + I("M8C")),
        ("stage 2 p: M11 = M9", I("M11"), I("M9")),
        ("stage 2 n: M12 = M10", I("M12"), I("M10")),
        ("CMFB: MC0 = MC1 + MC2", I("MC0"), I("MC1") + I("MC2")),
        ("CMFB: MC1 + MC2 = MC3 + MC4", I("MC1") + I("MC2"), I("MC3") + I("MC4")),
        ("bias P: Ibnp = MBP0 = MBP1", abs(val("I(Ibnp)")) * 1e6, (I("MBP0") + I("MBP1")) / 2),
        ("bias N: Ibnn = MBN5 = MBN7", abs(val("I(Ibnn)")) * 1e6, (I("MBN5") + I("MBN7")) / 2),
        ("bias: Ibcn = MBN3", abs(val("I(Ibcn)")) * 1e6, I("MBN3")),
        ("bias: Ibcp = MBP3", abs(val("I(Ibcp)")) * 1e6, I("MBP3")),
    ]
    print("branch sums [uA]:")
    for lab, a, b in rows:
        ok = abs(a - b) < 1e-4
        bad += not ok
        print(f"  [{'OK ' if ok else 'BAD'}] {lab:30s} {a:10.4f} = {b:10.4f}")

    s_vdd = 0.0
    for e in (e for e in elems if e[0][0].upper() == "M"):
        for term, node in zip(("Id", "Ig", "Is", "Ib"), e[1:5]):
            if node.lower() == "vdd":
                s_vdd += val(f"{term}({e[0]})")
    idd = abs(val("I(Vdd)")) * 1e6
    st1, st2, cm = I("M0"), I("M11") + I("M12"), I("MC0")
    ok = abs(idd - abs(s_vdd) * 1e6) < 1e-3 and abs(idd - (st1 + st2 + cm)) < 1e-3
    bad += not ok
    print(f"  [{'OK ' if ok else 'BAD'}] I(Vdd) {idd:.4f} uA = device currents into vdd pins {abs(s_vdd) * 1e6:.4f}"
          f" = stage 1 {st1:.3f} + stage 2 {st2:.3f} + CMFB {cm:.3f}")
    both = [e[0] for e in elems if {"vdd", "vddb"} <= {x.lower() for x in e[1:]}]
    on_vddb = sorted(e[0] for e in elems if "vddb" in [x.lower() for x in e[1:]])
    ok = not both and all(n.upper().startswith(("MB", "IB", "VDDB")) for n in on_vddb)
    bad += not ok
    print(f"  [{'OK ' if ok else 'BAD'}] only bias devices on vddb: {', '.join(on_vddb)}")

    unit = I("MBP0")
    print("replica ratios (amplifier device / replica unit):")
    # exact copies (same terminal voltages as the replica) must match to 1 %; the others differ for a known
    # reason and are only reported: M11 has a larger Vsd, MC0 a different Vds, MC3 carries the CMFB correction
    for lab, a, m, exact in (("M0 / MBP0", I("M0"), 18, True), ("M1 / MBP1", I("M1"), 9, True),
                             ("(M7+M7C) / MBN7", I("M7") + I("M7C"), 9, True), ("M7C / MBN7", I("M7C"), 1, True),
                             ("M11 / MBP0", I("M11"), 11, False), ("MC0 / MBP0", I("MC0"), 2, False),
                             ("MC3 / MBN7", I("MC3"), 1, False)):
        ratio = a / unit
        dev = ratio / m - 1
        ok = abs(dev) < (0.01 if exact else 0.10)
        bad += not ok
        tag = ("OK " if ok else "BAD") if exact else ("inf" if ok else "BAD")
        print(f"  [{tag}] {lab:16s} {ratio:7.3f} (expected {m}, {100 * dev:+.2f} %)")
    print("replica node voltages vs amplifier nodes:")
    # tail and b1p copy the replica directly; x1p is set by the CMFB loop (it only sits near vbnr)
    for a, b, lim in (("bp0", "tail", 1.0), ("bn5", "b1p", 1.0), ("vbnr", "x1p", 50.0)):
        d = 1e3 * (val(f"V({a})") - val(f"V({b})"))
        ok = abs(d) < lim
        bad += not ok
        tag = ("OK " if ok else "BAD") if lim <= 1 else ("inf" if ok else "BAD")
        print(f"  [{tag}] V({a}) {val(f'V({a})'):.4f} V vs V({b}) {val(f'V({b})'):.4f} V ({d:+.2f} mV)")
    print("kcl:", "OK" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


# ----------------------------------------------------------------------------- formulas


def formulas() -> int:
    k, T = M.K_B, M.T_K
    lg = math.log10
    S = json.loads((REPO / "results" / "latest.json").read_text())
    tab = {r["item"]: r["achieved"] for r in S["table"]}
    x = S["extra"]
    mac = {}
    for f in ("report/generated/results.tex", "report/generated/extra.tex"):
        mac.update(dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", (REPO / f).read_text())))
    pdf = subprocess.run(["pdftotext", str(REPO / "report" / "main.pdf"), "-"], capture_output=True, text=True).stdout
    pdf = re.sub(r"\s+", " ", pdf).replace("\u2212", "-")
    out = []

    def chk(name, value, macro=None, shown=None, tol=None):
        s = mac[macro] if macro else shown
        sci = "times" in s
        s_num = float(s.replace("\\times10^{", "e").replace("}", "")) if sci else float(s)
        dec = len(s.split(".")[1]) if "." in s and not sci else 0
        tol = abs(s_num) * 6e-4 if sci else (tol if tol is not None else 0.51 * 10 ** (-dec) + 1e-12)
        disp = (s.split("\\")[0] if sci else s).lstrip("+")
        inpdf = disp in pdf or macro == "resNEF"  # resNEF is printed rounded, see the next check
        out.append((abs(value - s_num) <= tol and inpdf, name, value, s, inpdf))

    Vout, Cin, Cfb, CL = tab[14], tab[15] * 1e-12, tab[16] * 1e-12, tab[17] * 1e-12
    vamp = tab[11] * 1e-6
    ktc = math.sqrt(2 * k * T * (Cin / Cfb**2 + 1 / Cfb + 1 / CL))
    chk("kT/C = sqrt(2kT(Cin/Cfb^2 + 1/Cfb + 1/CL)) uV", ktc * 1e6, "resKTC")
    chk("same as sqrt(42 kT/Cin) uV", math.sqrt(42 * k * T / Cin) * 1e6, "resKTC")
    vtot = math.hypot(ktc, vamp)
    chk("v_tot = sqrt(kTC^2 + amp^2) uV", vtot * 1e6, "resVnTot")
    snr = 20 * lg(Vout / math.sqrt(2) / vtot)
    chk("SNR = 20 log((Vout/sqrt2)/v_tot) dB", snr, "resSNR")
    chk("Cfb = Cin/4 pF", Cin / 4 * 1e12, "resCfb")
    chk("Cload = Cin pF", CL * 1e12, "resCload")
    chk("Vin = Vout/4 mV", Vout / 4 * 1e3, "resVin")
    P = 1.8 * tab[9] * 1e-3
    chk("P = 1.8 V x I(Vdd) mW", P * 1e3, "resPower")
    chk("tau = T38.6 - T30 ns", tab[6] - tab[5], "resTau")
    fom = 2 * math.pi * P * tab[7] * 1e-9 / 10 ** (snr / 10)
    chk("FoM_lin = 2 pi P tau / SNR^2 J", fom, "resFoMlin")
    chk("FoM_dB = -10 log FoM_lin", -10 * lg(fom), "resFoMdB")
    beta = 10 ** (-x["gap_dB"] / 20)
    chk("gap = 20 log(1/beta_act) dB", x["gap_dB"], "resGapdB")
    chk("beta_act", beta, "resBetaActual", tol=6e-5)
    chk("Cp = Cfb/beta - Cin - Cfb fF", (Cfb / beta - Cin - Cfb) * 1e15, "xCp")
    cleff = CL + (1 - 0.2) * Cfb
    chk("C_Leff = CL + (1-beta)Cfb pF", cleff * 1e12, "resCLeff", tol=6e-4)
    nef = vamp**2 / (2 * k * T / (0.2 * cleff))
    chk("NEF = v_amp^2 / (2kT/(beta C_Leff))", nef, "resNEF", tol=6e-3)
    chk("NEF as printed on page 8 (1 decimal)", nef, shown=f"{float(mac['resNEF']):.1f}")
    # page 8: the FoM in the course's efficiency terms (single-stage reference, current, noise share, tau)
    fom1 = lambda gmid: -10 * lg(2 * math.pi * (2 * 1.8 / gmid) * (cleff / (0.2 * Cin)) * 84 * k * T / Vout**2)
    chk("single-stage reference at gm/ID 25 dB", fom1(25.0), "xFoMideal")
    gmid1 = float(mac["xGmOne"]) * 1e-3 / (float(mac["xIdIn"]) * 1e-6)
    chk("single-stage reference at my gm/ID dB", fom1(gmid1), "xFoMone", tol=0.02)
    i_pair = 2 * float(mac["xIdIn"]) * 1e-6
    chk("current-efficiency term dB", -10 * lg(tab[9] * 1e-3 / i_pair), "xLcur", tol=0.02)
    chk("noise-share term dB", 10 * lg(ktc**2 / vtot**2), "xLnoise")
    chk("single-stage tau ns", cleff / (0.2 * float(mac["xGmOne"]) * 1e-3) * 1e9, "xTauOne")
    parts = sum(float(mac[n]) for n in ("xFoMone", "xLcur", "xLnoise", "xGtau"))
    chk("efficiency terms add to the FoM dB", parts, "resFoMdB", tol=0.006)
    # D6 (EE4520 values: reference/ee4520/README.md)
    eP, eTau, eSNR, evn = 0.1119e-3, 497.4e-9, 80.85, 76.93e-6
    ektc = math.sqrt(2 * k * T * (18e-12 / 2.25e-12**2 + 1 / 2.25e-12 + 1 / 18e-12))
    esnr = 20 * lg(0.8485 / math.hypot(evn, ektc))
    efom = lambda s: s - 10 * lg(2 * math.pi * eP * eTau)
    chk("EE4520 kT/C uV", ektc * 1e6, "xEKTC")
    chk("EE4520 SNR with kT/C dB", esnr, "xESNR")
    chk("EE4520 FoM with the spec SNR dB", efom(80.64), "xEFoMspec")
    chk("EE4520 FoM with the achieved SNR dB", efom(eSNR), "xEFoMach")
    chk("EE4520 FoM with kT/C dB", efom(esnr), "xEFoM")
    chk("D6 power term dB", -10 * lg(P / eP), "xDP")
    chk("D6 tau term dB", -10 * lg(tab[7] * 1e-9 / eTau), "xDT")
    chk("D6 SNR term dB", tab[1] - esnr, "xDS")
    chk("D6 total = FoM25 - FoM20 dB", tab[22] - efom(esnr), "xDTot")
    chk("D6 network term 10 log(146/42) dB", 10 * lg(146 / 42), "xDNet")
    chk("D6 beta term 10 log(1.8) dB", 10 * lg(1.8), "xDBeta")
    chk("D6 shape term 10 log(tau_dom/tau) dB", 10 * lg(float(mac["xTauTwoPole"]) / tab[7]), "xDShape", tol=0.02)
    sh, she = ktc**2 / vtot**2, ektc**2 / (ektc**2 + evn**2)
    chk("D6 noise-share term dB", 10 * lg(sh / she), "xDShare")
    parts = sum(float(mac[n]) for n in ("xDNet", "xDBeta", "xDShape", "xDShare", "xDSwing", "xDAmp"))
    rows = sum(float(mac[n]) for n in ("xDP", "xDT", "xDS"))
    chk("D6 five displayed parts add to the total", parts, "xDTot", tol=0.015)
    chk("D6 three displayed rows add to the total", rows, "xDTot", tol=0.015)
    chk("P ratio EE4525/EE4520", P / eP, "xPratio")
    chk("tau ratio EE4520/EE4525", eTau / (tab[7] * 1e-9), "xTauRatio")
    chk("kT/C share now %", 100 * sh, "xShareNow")
    chk("kT/C share EE4520 %", 100 * she, "xShareEE")
    bad = 0
    for ok, name, v, s, inpdf in out:
        bad += not ok
        print(f"[{'OK ' if ok else 'BAD'}] {name:44s} computed {v:12.6g}  shown {s:>22s}  "
              f"{'in PDF' if inpdf else 'NOT IN PDF'}")
    print(f"formulas: {len(out)} checks, {bad} problem(s)")
    return 1 if bad else 0


# ----------------------------------------------------------------------------- D2/D3 drawings vs LTspice


def figures() -> int:
    """Every node voltage and drain current printed in the D2/D3 drawings (report/generated/opvals.tex) against the
    operating point of the LTspice GUI run that draws the same circuit with .op data labels (tools/ltgui.py d2d3)."""
    raw_p = REPO / "results" / "ltgui" / "schem" / "amp_d2.op.raw"
    if not raw_p.exists():
        print("run `uv run tools/ltgui.py d2d3` first")
        return 1
    raw = M.Raw(raw_p)
    txt = (REPO / "report" / "generated" / "opvals.tex").read_text()
    unit = {"V": 1.0, "mV": 1e-3, "$\\mu$A": 1e-6, "\\textmu A": 1e-6, "mA": 1e-3, "nA": 1e-9, "A": 1.0}
    bad = n = 0
    for kind, name, val in re.findall(r"csname op([vi])@([a-z0-9]+)\\endcsname\{([^}]*)\}", txt):
        m = re.match(r"\s*([-+0-9.]+)\s*\\,\s*(.+?)\s*$", val)
        if not m:
            continue
        num, u = m.group(1), m.group(2)
        shown = float(num) * unit.get(u, math.nan)
        trace = f"V({name})" if kind == "v" else f"Id({name.upper()})"
        if not raw.has(trace):
            continue
        sim = float(raw[trace][0].real)
        if kind == "i":
            sim = abs(sim)
        half = 0.5 * 10 ** (-len(num.split(".")[1])) * unit.get(u, math.nan) if "." in num else 0.5 * unit.get(u, 1)
        ok = abs(shown - sim) <= half * 1.0001
        bad += not ok
        n += 1
        if not ok:
            print(f"[BAD] {trace:10s} drawn {val:16s} LTspice {sim:.6g}")
    print(f"figures: {n} drawn values checked against the LTspice GUI operating point, {bad} problem(s)")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["kcl", "formulas", "figures", "all"])
    ap.add_argument("--asc", type=Path, default=REPO / "design" / "final" / "amp_tran.asc")
    a = ap.parse_args(argv)
    rc = 0
    if a.what in ("kcl", "all"):
        rc |= kcl(a.asc)
    if a.what in ("formulas", "all"):
        rc |= formulas()
    if a.what in ("figures", "all"):
        rc |= figures()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
