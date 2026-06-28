#!/usr/bin/env python3
"""Probe per-node slew of Voutp/Voutn around the step (TSTEP=30ns)."""
import sys, numpy as np
from spicelib import RawRead
path = sys.argv[1] if len(sys.argv)>1 else "folded_cascode_ab_tran.raw"
TSTEP=30e-9
raw=RawRead(path)
t=np.abs(np.asarray(raw.get_axis()))
lut={n.lower():n for n in raw.get_trace_names()}
def tr(n): return np.real(np.asarray(raw.get_trace(lut[n.lower()]).get_wave()))
vop,von=tr("V(voutp)"),tr("V(voutn)")
vip,vin=tr("V(vip)"),tr("V(vin)")
vg=vip-vin
# pre-step values
i0=np.searchsorted(t,TSTEP-0.2e-9)
print(f"pre-step: Voutp={vop[i0]:.4f} Voutn={von[i0]:.4f} CM={(vop[i0]+von[i0])/2:.4f} vg={vg[i0]*1e3:+.3f}mV")
# final values
print(f"final   : Voutp={vop[-1]:.4f} Voutn={von[-1]:.4f}")
# peak slew each node in [TSTEP, TSTEP+12ns]
def peakslew(v,lbl):
    a=np.searchsorted(t,TSTEP); b=np.searchsorted(t,TSTEP+12e-9)
    dv=np.diff(v[a:b]); dt=np.diff(t[a:b])
    sr=dv/dt
    imax=np.argmax(np.abs(sr))
    print(f"  {lbl}: peak dV/dt={sr[imax]/1e6:+.1f} V/us at t-step={ (t[a+imax]-TSTEP)*1e9:.2f}ns")
    return sr[imax]
print("slew (first 12ns after step):")
peakslew(vop,"Voutp(falls)")
peakslew(von,"Voutn(rises)")
# trajectory samples every 1ns after step
print("traj  t-step  Voutp   Voutn    vg(mV)")
for dt_ns in [0,1,2,3,4,5,6,8,10,15,20,25]:
    i=np.searchsorted(t,TSTEP+dt_ns*1e-9); i=min(i,len(t)-1)
    print(f"   {dt_ns:5.0f}ns  {vop[i]:.4f}  {von[i]:.4f}  {vg[i]*1e3:+8.3f}")
