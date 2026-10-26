#!/usr/bin/env python3
"""Extract settling metrics from the cr transient .raw.
A(t)  = 20*log10(Vout_max/(|vg|+1n)),  vg = V(vip)-V(vin),  Vout_max=0.9 (diff)
Abeta(t) = A(t) - OFFSET  (OFFSET = A at the step instant)
Spec: A(25ns)>=78 dB  AND  Abeta(25ns)>=66 dB ; tau = T38.69 - T30 (one e-fold).
Step is applied at TSTEP (default 30 ns) -> 25 ns point = TSTEP+25 ns."""
import sys, numpy as np
from spicelib import RawRead

path = sys.argv[1] if len(sys.argv) > 1 else "folded_cascode_cr_tran.raw"
TSTEP = float(sys.argv[2]) if len(sys.argv) > 2 else 30e-9
VMAX = 0.9
raw = RawRead(path)
t = np.abs(np.asarray(raw.get_axis()))
lut = {n.lower(): n for n in raw.get_trace_names()}
def tr(n): return np.real(np.asarray(raw.get_trace(lut[n.lower()]).get_wave()))
vip, vin = tr("V(vip)"), tr("V(vin)")
vop, von = tr("V(voutp)"), tr("V(voutn)")
vg = vip - vin
vod = von - vop                       # differential output
A = 20*np.log10(VMAX/(np.abs(vg)+1e-9))

def at(tt):
    i = np.searchsorted(t, tt)
    i = min(i, len(t)-1)
    return A[i], vg[i], vod[i]

# offset = min accuracy in [TSTEP, TSTEP+1ns] (peak vg right after step)
m = (t >= TSTEP) & (t <= TSTEP+1e-9)
offset = A[m].min() if m.any() else float('nan')
A25, vg25, vod25 = at(TSTEP+25e-9)
Abeta25 = A25 - offset

# threshold crossings after step (rising)
def cross(level):
    for i in range(1, len(t)):
        if t[i] > TSTEP+0.1e-9 and A[i-1] < level <= A[i]:
            f = (level-A[i-1])/(A[i]-A[i-1])
            return t[i-1] + f*(t[i]-t[i-1])
    return float('nan')
T30 = cross(30); T3869 = cross(38.69)
tau = (T3869-T30) if (T30==T30 and T3869==T3869) else float('nan')

# slew estimate: max |dVod/dt| just after step
i0 = np.searchsorted(t, TSTEP)
i1 = np.searchsorted(t, TSTEP+8e-9)
dvdt = np.diff(vod[i0:i1])/np.diff(t[i0:i1])
SR = np.max(np.abs(dvdt)) if len(dvdt) else float('nan')

print(f"=== settling: {path}  (step @ {TSTEP*1e9:.0f} ns) ===")
print(f"  pre-step  vg={vg[i0-2]*1e3:+.3f} mV  Voutp/n CM={(vop[i0-2]+von[i0-2])/2:.3f} V  Vod={vod[i0-2]*1e3:+.2f} mV")
print(f"  OFFSET (A at step)      = {offset:6.2f} dB   (1/beta ~ 14 dB)")
print(f"  A(25ns)    [need >=78]  = {A25:6.2f} dB   vg={vg25*1e6:8.1f} uV  Vod={vod25:.4f} V")
print(f"  Abeta(25ns)[need >=66]  = {Abeta25:6.2f} dB")
print(f"  T30dB={T30*1e9 if T30==T30 else float('nan'):.3f} ns  T38.69dB={T3869*1e9 if T3869==T3869 else float('nan'):.3f} ns  (after step: "
      f"{(T30-TSTEP)*1e9 if T30==T30 else float('nan'):.2f}/{(T3869-TSTEP)*1e9 if T3869==T3869 else float('nan'):.2f} ns)")
print(f"  tau = T38.69-T30        = {tau*1e9 if tau==tau else float('nan'):.3f} ns")
print(f"  peak slew |dVod/dt|     = {SR/1e6:.1f} V/us   (Vod final ~ {vod[-1]:.3f} V)")
PASS = (A25>=78) and (Abeta25>=66)
print(f"  --> settling {'PASS' if PASS else 'FAIL'}  (A25>=78 & Abeta25>=66 @ 25 ns)")
