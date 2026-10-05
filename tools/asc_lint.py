#!/usr/bin/env python3
"""Lint an LTspice .asc (or .net/.cir) against the EE4525 rules and the schematic-hygiene rules.

  uv run tools/asc_lint.py design/amp_tran.asc [--no-netlist]

Exit 0 = no ERRORs (WARNs allowed). Checks:
  hygiene   : circuit elements typed as text directives (forbidden), log018.l present,
              forbidden `logic018 no1of`, integer m=, LTspice-24-only options
  electrical: NMOS bulk must be ground; integer M; R > 10 Meg only for Rin/Rfb (FAQ);
              Rin/Rfb should be `noiseless`; Rfb/Rin == Cin/Cfb; Cload == Cin;
              main-circuit capacitance < 1000 pF (caps >= 1 nF counted as bias decoupling);
              controlled sources (E/F/G/H/B) must be pure probes (output drives nothing);
              no DC supply above 1.8 V.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics import net_params, spice_num  # noqa: E402

ALLOWED_DOT = (".lib", ".include", ".inc", ".model", ".param", ".op", ".ac", ".tran", ".noise", ".dc",
               ".meas", ".measure", ".option", ".options", ".save", ".step", ".temp", ".func", ".ic",
               ".nodeset", ".global", ".backanno", ".end", ".four", ".probe", ".savebias", ".loadbias")


def lint_asc_text(text: str) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    directives = []
    for line in text.splitlines():
        if line.startswith("TEXT") and " !" in line:
            body = line.split(" !", 1)[1]
            directives.extend(body.split("\\n"))
    if not any("log018.l" in d.lower() for d in directives if d.strip().lower().startswith(".lib")):
        errs.append("no `.lib ... log018.l TT` directive (the 1/f-noise model is mandatory)")
    for d in directives:
        s = d.strip()
        low = s.lower()
        if "no1of" in low and not low.startswith(";"):
            errs.append(f"forbidden model `logic018 no1of.l`: {s[:80]}")
        if not s or s.startswith(("*", ";", "+")):
            continue
        if s.startswith("."):
            if not low.startswith(ALLOWED_DOT):
                warns.append(f"unusual dot-command in directives: {s[:80]}")
            if "logopinfo" in low:
                warns.append("`.options logopinfo` is LTspice-24-only (XVII rejects it)")
            continue
        if re.match(r"^[A-Za-z]\w*\s+\S+\s+\S+", s):
            errs.append(f"circuit element typed as a SPICE text directive (must be a drawn symbol): {s[:80]}")
    for m in re.finditer(r"SYMATTR Value2 .*?\bm=([^\s]+)", text):
        v = m.group(1)
        try:
            if abs(spice_num(v) - round(spice_num(v))) > 1e-9:
                errs.append(f"non-integer multiplier m={v} (FAQ: integer M only)")
        except ValueError:
            pass  # {param}: checked on the netlist
    return errs, warns


def lint_netlist(net: Path) -> tuple[list[str], list[str], list[str]]:
    errs, warns, info = [], [], []
    p = net_params(net)
    lines = [l.strip() for l in net.read_text(errors="replace").splitlines()]
    elems = [l for l in lines if l and l[0].isalpha() and not l.startswith(".")]
    nodes_use: dict[str, int] = {}
    parsed = []
    for l in elems:
        tok = l.split()
        name = tok[0]
        kind = name[0].upper()
        nn = {"M": 4, "R": 2, "C": 2, "V": 2, "I": 2, "E": 4, "G": 4, "F": 2, "H": 2, "B": 2, "S": 4, "D": 2}.get(kind, 2)
        nodes = [t.lower() for t in tok[1:1 + nn]]
        parsed.append((name, kind, nodes, tok, l))
        for n in nodes:
            nodes_use[n] = nodes_use.get(n, 0) + 1

    def val(tok_list, idx):
        v = tok_list[idx] if len(tok_list) > idx else ""
        v = v.strip("{}")
        try:
            return spice_num(v)
        except ValueError:
            return p.get(v.lower())

    cap_main = 0.0
    cap_dec = 0.0
    for name, kind, nodes, tok, l in parsed:
        low = l.lower()
        if kind == "M":
            model = tok[5].lower() if len(tok) > 5 else ""
            if model.startswith("n") and nodes[3] != "0":
                errs.append(f"{name}: NMOS bulk on `{nodes[3]}` (must be ground, single substrate)")
            mm = re.search(r"\bm=\{?([^\s}]+)\}?", low)
            if mm:
                mv = p.get(mm.group(1)) if not re.match(r"^[\d.]", mm.group(1)) else spice_num(mm.group(1))
                if mv is not None and abs(mv - round(mv)) > 1e-9:
                    errs.append(f"{name}: non-integer m={mv}")
        elif kind == "R":
            r = val(tok, 3)
            is_fb = name.lower().startswith(("rin", "rfb"))
            if r is not None and r > 10e6 and not is_fb:
                warns.append(f"{name} = {r:.3g} ohm > 10 Meg (FAQ: only Rin/Rfb may be ~GOhm)")
            if is_fb and "noiseless" not in low:
                warns.append(f"{name}: add `noiseless` (FAQ: Rin/Rfb noise is excluded from the amplifier noise)")
        elif kind == "C":
            c = val(tok, 3)
            if c is None:
                continue
            if c >= 1e-9:
                cap_dec += c
            else:
                cap_main += c
        elif kind in "EFGHB":
            outs = nodes[:2]
            drives = [n for n in outs if n != "0" and nodes_use.get(n, 0) > 1]
            if drives:
                errs.append(f"{name}: controlled/behavioural source drives circuit node(s) {drives} "
                            "(only allowed as a pure measurement probe or inside the bias block)")
            else:
                info.append(f"{name}: pure probe (ok, but prefer computing it in tools/metrics.py)")
        elif kind == "V":
            dc = re.search(r"(?i)\b(?:dc\s+)?(\{[^}]+\}|[-+]?[\d.]+(?:e[-+]?\d+)?[a-z]*)\b", " ".join(tok[3:4]))
            v = val(tok, 3) if dc else None
            if v is not None and (v > 1.8 + 1e-6 or v < -1e-6):
                errs.append(f"{name}: DC value {v} V outside 0..1.8 V (single 1.8 V supply rule)")
    info.append(f"main-circuit capacitance {cap_main*1e12:.2f} pF (limit 1000 pF); decoupling {cap_dec*1e9:.3g} nF")
    if cap_main > 1e-9:
        errs.append(f"main-circuit capacitance {cap_main*1e12:.1f} pF > 1000 pF")
    cin, cfb, cl = p.get("cin"), p.get("cfb"), p.get("cload")
    if cin and cl and abs(cl / cin - 1) > 1e-6:
        errs.append(f"Cload ({cl:.4g}) != Cin ({cin:.4g})")
    if cin and cfb and abs(cin / cfb - 4) > 1e-6:
        errs.append(f"Cin/Cfb = {cin/cfb:.4g}, must be 4 (feedback network may not be modified)")
    rin, rfb = p.get("rin"), p.get("rfb")
    if rin and rfb and cin and cfb and abs((rfb / rin) / (cin / cfb) - 1) > 1e-6:
        errs.append(f"Rfb/Rin = {rfb/rin:.4g} must equal Cin/Cfb = {cin/cfb:.4g}")
    if rfb and cfb and 1 / (2 * 3.14159 * rfb * cfb) > 1e3:
        warns.append(f"Rfb*Cfb corner {1/(2*3.14159*rfb*cfb):.3g} Hz > 1 kHz: Rfb noise/leakage leaks into the 10 kHz+ band; use GOhm")
    vs, vb = p.get("voutstep"), p.get("vinstep")
    if vs and vb and abs(vb / vs - 0.25) > 1e-6:
        errs.append(f"VinStep/VoutStep = {vb/vs:.4g}, must be 1/4")
    return errs, warns, info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--no-netlist", action="store_true", help="skip LTspice netlisting (text checks only)")
    a = ap.parse_args(argv)
    f = Path(a.file)
    errs, warns, info = [], [], []
    if f.suffix.lower() == ".asc":
        e, w = lint_asc_text(f.read_text(errors="replace"))
        errs += e
        warns += w
        if not a.no_netlist:
            from lt import netlist

            e, w, i = lint_netlist(netlist(f))
            errs += e
            warns += w
            info += i
    else:
        e, w, i = lint_netlist(f)
        errs += e
        warns += w
        info += i
    for x in errs:
        print("ERROR:", x)
    for x in warns:
        print("WARN: ", x)
    for x in info:
        print("info: ", x)
    print(f"{f.name}: {len(errs)} error(s), {len(warns)} warning(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
