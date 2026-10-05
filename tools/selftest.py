#!/usr/bin/env python3
"""Toolchain regression test: re-measure the passing example and compare to its report.

  uv run tools/selftest.py        # about 15 s; exit 0 = LTspice, parsing and metrics all healthy

Run it at the start of a session (or after touching tools/) before trusting any number.
"""
from __future__ import annotations

import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lt  # noqa: E402
import metrics as M  # noqa: E402

GOLD = {"A": 80.81, "Abeta": 66.01, "tau": 2.697, "T30": 16.397, "Vn_amp": 326.40, "SNR": 66.01}


def main() -> int:
    d = lt.REPO / "results" / "selftest"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    asc = d / "example_tran.asc"
    shutil.copy2(lt.REPO / "example" / "cmos2_margin0p1_visual_grid16.asc", asc)
    rt = lt.run(asc)
    assert rt["ok"], rt["errors"]
    net = Path(rt["net"])
    noise_lines = []
    for l in net.read_text().splitlines():
        s = l.strip().lower()
        if s.startswith((".tran", ".meas tran")):
            continue
        if s.startswith((";.noise", ";.meas noise")):
            l = l.lstrip(";")
        noise_lines.append(l)
    nn = d / "example_noise.net"
    nn.write_text("\n".join(noise_lines) + "\n")
    rn = lt.run(nn)
    assert rn["ok"], rn["errors"]
    tm = M.tran_metrics(rt["raw"], net)
    nm = M.noise_metrics(rn["raw"])
    p = M.net_params(net)
    snr = M.snr_db(tm["VoutStep_V"], math.hypot(M.ktc_uV(p["cin"], T=300.0), nm["Vn_amp_uVrms"]))
    got = {"A": tm["A_at_25ns_dB"], "Abeta": tm["Abeta_at_25ns_dB"], "tau": tm["tau_ns"], "T30": tm["T30_ns"],
           "Vn_amp": nm["Vn_amp_uVrms"], "SNR": snr}
    ok = True
    for k, ref in GOLD.items():
        good = abs(got[k] - ref) <= max(0.02, 0.002 * abs(ref))
        ok &= good
        print(f"[{'PASS' if good else 'FAIL'}] {k:7s} expected {ref:9.3f}  got {got[k]:9.3f}")
    ok &= tm["checks"]["first_peak_after_25ns"]
    print(f"[{'PASS' if tm['checks']['first_peak_after_25ns'] else 'FAIL'}] first ringing peak after 25 ns "
          f"({min(tm['first_peak_A_ns'], tm['first_peak_Abeta_ns']):.2f} ns)")
    print("selftest", "OK" if ok else "FAILED", f"(LTspice runs {rt['elapsed_s']} s + {rn['elapsed_s']} s)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
