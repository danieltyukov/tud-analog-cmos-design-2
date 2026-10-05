#!/usr/bin/env python3
"""Robustness of the settling result to bench details the assignment does not fix.

  uv run tools/robust.py design/work/bench_tran.cir      (or the drawn .asc)

Re-runs the transient (in parallel) over: step polarity (+/-), input edge 20/50/100 ps, and
reltol 1e-3/1e-4, and reports the worst A(25ns), Abeta(25ns), floors, settling time and
first ringing peak. The example design flips from 66.0 to 64.9 dB with a 10 ps edge, so a
zero-margin design can fail at the grader. Exit 0 only if every variant passes the hard specs.
Needs `trise` and `VinStep` as .param names (bench_tran.cir template).
"""
from __future__ import annotations

import argparse
import itertools
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lt  # noqa: E402
import metrics as M  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("-j", "--jobs", type=int, default=12)
    a = ap.parse_args(argv)
    f = lt.guard(a.file)
    base = lt.netlist(f) if f.suffix.lower() == ".asc" else f
    text = lt.fix_netlist(lt.inline_includes(lt.read_text(base), base.parent))
    if not re.search(r"(?i)\btrise\s*=", text):
        print("WARN: no `trise` param; edge-rate variants will be identical")
    root = lt.REPO / "results" / "robust" / f.stem
    root.mkdir(parents=True, exist_ok=True)
    variants = list(itertools.product(["+", "-"], ["20p", "50p", "100p"], ["1e-3", "1e-4"]))

    def one(i_v):
        i, (pol, edge, rt) = i_v
        t = lt.set_params(text, {"trise": edge, **({"VinStep": "{-VoutStep/4}"} if pol == "-" else {})})
        if re.search(r"(?im)^\.options?\b.*\breltol=", t):
            t = re.sub(r"(?im)(^\.options?\b.*\breltol=)\S+", lambda m: m.group(1) + rt, t)
        else:
            t = t.replace("\n.end", f"\n.option reltol={rt}\n.end")
        d = root / f"v{i:02d}"
        d.mkdir(exist_ok=True)
        net = d / "tran.net"
        net.write_text(t)
        r = lt.run(net)
        if not r["ok"] or not r["raw"]:
            return (pol, edge, rt, None)
        m = M.tran_metrics(r["raw"], net)
        Path(r["raw"]).unlink(missing_ok=True)
        return (pol, edge, rt, m)

    lt.ensure_display()
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        res = list(ex.map(one, enumerate(variants)))
    print(f"{'pol':>3s} {'edge':>5s} {'reltol':>6s} {'A25':>7s} {'Ab25':>7s} {'Afloor':>7s} {'Abfloor':>7s} {'Ts[ns]':>7s} {'peak[ns]':>8s}")
    ok = True
    worst = {"A25": 1e9, "Ab25": 1e9, "Afl": 1e9, "Abfl": 1e9, "Ts": 0.0, "pk": 1e9}
    for pol, edge, rt, m in res:
        if m is None:
            print(f"{pol:>3s} {edge:>5s} {rt:>6s}  RUN FAILED")
            ok = False
            continue
        ts = max(m["Tsettle_A_ns"], m["Tsettle_Abeta_ns"])
        pk = min(m["first_peak_A_ns"], m["first_peak_Abeta_ns"])
        good = (m["A_at_25ns_dB"] >= 78 and m["Abeta_at_25ns_dB"] >= 66 and m["A_floor_dB"] >= 78
                and m["Abeta_floor_dB"] >= 66 and ts <= 25 and pk > 25)
        ok &= good
        for k, v in (("A25", m["A_at_25ns_dB"]), ("Ab25", m["Abeta_at_25ns_dB"]), ("Afl", m["A_floor_dB"]),
                     ("Abfl", m["Abeta_floor_dB"]), ("pk", pk)):
            worst[k] = min(worst[k], v)
        worst["Ts"] = max(worst["Ts"], ts)
        print(f"{pol:>3s} {edge:>5s} {rt:>6s} {m['A_at_25ns_dB']:7.2f} {m['Abeta_at_25ns_dB']:7.2f} {m['A_floor_dB']:7.2f} "
              f"{m['Abeta_floor_dB']:7.2f} {ts:7.2f} {pk:8.2f}{'' if good else '  FAIL'}")
    print(f"worst: A25 {worst['A25']:.2f}  Ab25 {worst['Ab25']:.2f}  Afloor {worst['Afl']:.2f}  Abfloor {worst['Abfl']:.2f}  "
          f"Ts {worst['Ts']:.2f} ns  first peak {worst['pk']:.2f} ns")
    print("robust:", "PASS" if ok else "FAIL")
    import hashlib
    import json
    import time

    (lt.REPO / "results" / "robust" / "latest.json").write_text(json.dumps({
        "file": str(f), "sha": hashlib.sha256(f.read_bytes()).hexdigest()[:12], "pass": ok, "worst": worst,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
