#!/usr/bin/env python3
"""Phase-4 gain-boost differential-AC extraction.

Reads A0 / GBW / loop-crossover f_u / PM from the UNLOADED main-amp nodes
V(Voutp)-V(Voutn) by complex subtraction (the loaded replica node Voutp2 reads a
~42 dB artifact and must NOT be used -- analysis/09 sec C, project memory).
beta = Cfb/(Cin+Cfb) = 1/5.

Usage:
  ~/tools/spicelib-mcp/.venv/bin/python design/gain-boost/extract_gb.py [raw_path]
Default raw_path = design/gain-boost/folded_cascode_gb_ac.raw
"""
import sys, numpy as np
from spicelib import RawRead

BETA = 1.0 / 5.0
BASE = "/home/danieltyukov/workspace/tud/tud-analog-cmos-design-2"


def trace(raw, name):
    names = raw.get_trace_names()
    lut = {n.lower(): n for n in names}
    return np.asarray(raw.get_trace(lut[name.lower()]).get_wave())


def extract(path, label="gb AC"):
    raw = RawRead(path)
    f = np.abs(np.asarray(raw.get_axis()))
    vp = trace(raw, "V(voutp)")
    vn = trace(raw, "V(voutn)")
    A = vp - vn
    magA_dB = 20 * np.log10(np.abs(A))
    phA = np.unwrap(np.angle(A)) * 180 / np.pi
    ph_dc = phA[0]
    A0_dB = magA_dB[0]

    def cross(level_dB):
        d = magA_dB - level_dB
        idx = np.where((d[:-1] > 0) & (d[1:] <= 0))[0]
        if len(idx) == 0:
            return np.nan, np.nan
        i = idx[0]
        lf0, lf1 = np.log10(f[i]), np.log10(f[i + 1])
        frac = d[i] / (d[i] - d[i + 1])
        lf = lf0 + frac * (lf1 - lf0)
        ph = phA[i] + frac * (phA[i + 1] - phA[i])
        return 10 ** lf, ph

    GBW, _ = cross(0.0)
    f_u, ph_fu = cross(20 * np.log10(5.0))   # |A|=5 -> |A.beta|=1
    PM = 180.0 + (ph_fu - ph_dc)

    # CM->diff leak sanity (should be ~0 for a symmetric design)
    cm = np.abs((vp + vn) / 2.0)
    leak = np.max(cm / (np.abs(A) + 1e-30))

    print(f"=== {label} ===")
    print(f"  file        : {path}")
    print(f"  A0          : {A0_dB:7.2f} dB    (phase_dc {ph_dc:6.1f} deg)")
    print(f"  GBW (|A|=1) : {GBW/1e6:7.2f} MHz")
    print(f"  f_u (|Ab|=1): {f_u/1e6:7.2f} MHz  -> amp GBW = f_u/beta = {f_u*5/1e6:7.2f} MHz")
    print(f"  PM  @ f_u   : {PM:7.2f} deg")
    print(f"  CM->diff leak (max): {leak:.2e}")
    return dict(A0=A0_dB, GBW=GBW, fu=f_u, PM=PM, leak=leak)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else f"{BASE}/design/gain-boost/folded_cascode_gb_ac.raw"
    extract(path)
