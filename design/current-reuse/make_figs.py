#!/usr/bin/env python3
"""Phase-5 closure: compute SNR/FoM and render the D4 (settling) and D5 (noise PSD)
report figures from the locked current-reuse benches."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from spicelib import RawRead

BASE = "/home/danieltyukov/workspace/tud/tud-analog-cmos-design-2"
FIG = f"{BASE}/report/figures"

# ---------- constants ----------
kT = 4.142e-21; Cin = 5e-12; beta = 1/5.0
VsigRMS = 0.636                       # diff signal rms (1.8 Vpp diff / 2sqrt2)
P = 2.043e-3; tau = 3.289e-9          # locked design: P=I(Vdd)*1.8, tau=T38.69-T30

# ---------- D5 noise ----------
rn = RawRead(f"{BASE}/design/current-reuse/folded_cascode_cr_noise.raw")
f = np.abs(np.asarray(rn.get_axis()))
lut = {n.lower(): n for n in rn.get_trace_names()}
onoise = np.abs(np.asarray(rn.get_trace(lut["v(onoise)"]).get_wave()))   # V/sqrt(Hz)
Vnamp = np.sqrt(np.sum(0.5*(onoise[1:]**2+onoise[:-1]**2)*np.diff(f)))                                   # integrated Vrms
VnkTC = np.sqrt(2*(1/beta)**2*kT/Cin)
Vntot = np.sqrt(Vnamp**2 + VnkTC**2)
SNRlin = VsigRMS/Vntot; SNRdB = 20*np.log10(SNRlin)
FoMlin = 2*np.pi*P*tau/SNRlin**2; FoMdB = -10*np.log10(FoMlin)

print(f"  Vn,amp (term11, sim 10k-100G) = {Vnamp*1e6:6.1f} uV")
print(f"  Vn,kT/C(term10, hand 2(1/b)^2 kT/Cin) = {VnkTC*1e6:6.1f} uV")
print(f"  Vn,tot (term12) = {Vntot*1e6:6.1f} uV")
print(f"  SNR = {SNRdB:.2f} dB   (Vsig,rms={VsigRMS} V)")
print(f"  P={P*1e3:.3f} mW  tau={tau*1e9:.3f} ns  -> FoM_lin={FoMlin:.3e} J  FoM_dB={FoMdB:.2f} dB")

fig, ax = plt.subplots(figsize=(7, 4.3))
ax.loglog(f, onoise*1e9, lw=1.3, color="C0")
ax.set_xlabel("Frequency [Hz]"); ax.set_ylabel(r"Output noise [nV/$\sqrt{\mathrm{Hz}}$]")
ax.set_title(f"D5 — Differential output noise PSD (current-reuse residue amp)\n"
             f"integrated $V_{{n,amp}}$={Vnamp*1e6:.1f} µV (10 kHz–100 GHz), "
             f"+kT/C {VnkTC*1e6:.0f} µV → $V_{{n,tot}}$={Vntot*1e6:.0f} µV, SNR={SNRdB:.1f} dB")
ax.axvline(1e4, color="0.6", ls="--", lw=0.8); ax.axvline(1e11, color="0.6", ls="--", lw=0.8)
ax.grid(True, which="both", alpha=0.3)
fig.tight_layout(); fig.savefig(f"{FIG}/cr_d5_noise.png", dpi=140, bbox_inches="tight"); print(f"  wrote {FIG}/cr_d5_noise.png")

# ---------- D4 settling ----------
rt = RawRead(f"{BASE}/design/current-reuse/folded_cascode_cr_tran.raw")
t = np.abs(np.asarray(rt.get_axis()))
lut = {n.lower(): n for n in rt.get_trace_names()}
def tr(n): return np.real(np.asarray(rt.get_trace(lut[n.lower()]).get_wave()))
TSTEP = 30e-9
vg = tr("v(vip)") - tr("v(vin)")
A = 20*np.log10(0.9/(np.abs(vg)+1e-9))
m = (t >= TSTEP) & (t <= TSTEP+1e-9); OFF = A[m].min()
Ab = A - OFF
tn = (t - TSTEP)*1e9
sel = tn >= -1
fig, ax = plt.subplots(figsize=(7.2, 4.5))
ax.plot(tn[sel], A[sel], lw=1.4, color="C3", label=r"$A(t)$  amplifier accuracy")
ax.plot(tn[sel], Ab[sel], lw=1.4, color="C1", label=r"$A\beta(t)$  loop accuracy (from 0 dB)")
ax.axvline(25, color="0.4", ls="--", lw=1.0); ax.axhline(78, color="C3", ls=":", lw=0.9)
ax.axhline(66, color="C1", ls=":", lw=0.9)
ax.annotate("25 ns", (25, 5), fontsize=9); ax.annotate("78 dB", (0, 79), color="C3", fontsize=9)
ax.annotate("66 dB", (0, 67), color="C1", fontsize=9)
def at(tt):
    # linear interpolation to the exact time (consistent with the .meas extraction)
    return np.interp(TSTEP+tt*1e-9, t, A), np.interp(TSTEP+tt*1e-9, t, Ab)
A25, Ab25 = at(25)
ax.set_xlim(-1, 35); ax.set_ylim(0, 100)
ax.set_xlabel("time after amplify-phase step [ns]"); ax.set_ylabel("settling accuracy [dB]")
ax.set_title(f"D4 — Settling: A(25ns)={A25:.1f} dB, Aβ(25ns)={Ab25:.1f} dB  "
             f"(offset 1/β={OFF:.1f} dB; reaches 78/66 at ~26.5 ns)")
ax.legend(loc="lower right", fontsize=9); ax.grid(True, alpha=0.3)
fig.tight_layout(); fig.savefig(f"{FIG}/cr_d4_settling.png", dpi=140, bbox_inches="tight"); print(f"  wrote {FIG}/cr_d4_settling.png")
