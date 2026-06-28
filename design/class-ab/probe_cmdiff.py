import numpy as np
from spicelib import RawRead
raw=RawRead("scratch_ab.raw"); TSTEP=30e-9
t=np.abs(np.asarray(raw.get_axis()))
names={n.lower():n for n in raw.get_trace_names()}
def tr(n): return np.real(np.asarray(raw.get_trace(names[n.lower()]).get_wave()))
vop,von=tr("V(voutp)"),tr("V(voutn)")
vg=tr("V(vip)")-tr("V(vin)")
cm=(vop+von)/2; diffout=von-vop
print("window(ns)  |vg|env(uV)  CMrange(mV)  diffOUT range(mV around final)")
finalo=diffout[-1]
for w0 in range(12,58,4):
    m=(t>=TSTEP+w0*1e-9)&(t<TSTEP+(w0+4)*1e-9)
    if m.any():
        vgmx=np.max(np.abs(vg[m]))*1e6
        cmr=(cm[m].max()-cm[m].min())*1e3
        cmmean=cm[m].mean()
        dor=(diffout[m].max()-diffout[m].min())*1e3
        print(f"  {w0:3d}-{w0+4:3d}   {vgmx:9.1f}   CMmean={cmmean:.4f} range={cmr:6.2f}   dOUTrange={dor:6.2f}")
