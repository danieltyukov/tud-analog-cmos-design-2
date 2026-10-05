#!/usr/bin/env python3
"""Phase-3 differential-AC extraction.

Reads A0 / GBW / loop-crossover f_u / PM from the UNLOADED main-amp nodes
V(Voutp)-V(Voutn) by complex subtraction (the loaded replica node Voutp2 reads a
~42 dB artifact and must NOT be used -- see analysis/09 section C and project memory).
beta = Cfb/(Cin+Cfb) = 1/5.

Run with the spicelib venv:
  ~/tools/spicelib-mcp/.venv/bin/python design/cmfb/extract_ac.py
"""
import sys, numpy as np
from spicelib import RawRead

BETA = 1.0 / 5.0

def trace(raw, name):
    """Case-insensitive trace fetch -> complex wave."""
    names = raw.get_trace_names()
    lut = {n.lower(): n for n in names}
    return np.asarray(raw.get_trace(lut[name.lower()]).get_wave())

def extract(path, label):
    raw = RawRead(path)
    f = np.abs(np.asarray(raw.get_axis()))          # frequency axis (Hz)
    vp = trace(raw, "V(voutp)")
    vn = trace(raw, "V(voutn)")
    A = vp - vn                                      # open-loop differential gain (1 V diff drive)
    magA = np.abs(A)
    magA_dB = 20*np.log10(magA)
    phA = np.unwrap(np.angle(A)) * 180/np.pi         # degrees, unwrapped
    ph_dc = phA[0]

    A0_dB = magA_dB[0]                               # at f = 1 Hz

    def cross(level_dB):
        """First downward crossing of magA_dB through level_dB; log-freq interp."""
        d = magA_dB - level_dB
        idx = np.where((d[:-1] > 0) & (d[1:] <= 0))[0]
        if len(idx) == 0:
            return np.nan, np.nan
        i = idx[0]
        # interpolate in log10(f)
        lf0, lf1 = np.log10(f[i]), np.log10(f[i+1])
        frac = d[i] / (d[i] - d[i+1])
        lf = lf0 + frac*(lf1-lf0)
        # interpolate phase too
        ph = phA[i] + frac*(phA[i+1]-phA[i])
        return 10**lf, ph

    GBW, ph_gbw = cross(0.0)                         # |A| = 1
    f_u, ph_fu  = cross(20*np.log10(5.0))            # |A| = 5  ->  |A*beta| = 1 (loop crossover)
    PM = 180.0 + (ph_fu - ph_dc)                     # excess phase relative to DC

    print(f"=== {label} ===")
    print(f"  file              : {path}")
    print(f"  A0  (DC diff gain): {A0_dB:7.2f} dB   (phase_dc = {ph_dc:6.1f} deg)")
    print(f"  GBW (|A|=1)       : {GBW/1e6:7.2f} MHz")
    print(f"  f_u (|A*beta|=1)  : {f_u/1e6:7.2f} MHz   -> amp GBW = f_u/beta = {f_u*5/1e6:7.2f} MHz")
    print(f"  PM  @ f_u         : {PM:7.2f} deg")
    return dict(A0=A0_dB, GBW=GBW, fu=f_u, PM=PM)

if __name__ == "__main__":
    base = "/home/danieltyukov/workspace/tud/tud-analog-cmos-design-2"
    r_ideal = extract(f"{base}/simulations/ac/loaded_ac_baseline.raw", "Phase-2 ideal CMFB (baseline)")
    print()
    r_sc    = extract(f"{base}/design/cmfb/folded_cascode_cmfb_ac.raw", "Phase-3 real SC-CMFB")
    print()
    print("=== regression check (SC-CMFB vs ideal) ===")
    print(f"  dA0  = {r_sc['A0']-r_ideal['A0']:+.2f} dB")
    print(f"  dGBW = {(r_sc['GBW']-r_ideal['GBW'])/1e6:+.2f} MHz "
          f"({100*(r_sc['GBW']/r_ideal['GBW']-1):+.1f} %)")
    print(f"  dPM  = {r_sc['PM']-r_ideal['PM']:+.2f} deg")
