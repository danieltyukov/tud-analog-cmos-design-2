#!/usr/bin/env python3
"""Phase-3 transient CM-step analysis for the real SC-CMFB.

Reads the CM-step transient, computes the output common mode
CM(t) = (V(Voutp)+V(Voutn))/2 and the differential V(Voutp)-V(Voutn),
quantifies the CM recovery (dip, settling, residual, loop time constant),
and saves a report figure.

Run:  ~/tools/spicelib-mcp/.venv/bin/python design/cmfb/analyze_cm_step.py
"""
import numpy as np
from spicelib import RawRead
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = "/home/danieltyukov/workspace/tud/tud-analog-cmos-design-2"
RAW  = f"{BASE}/design/cmfb/folded_cascode_cmfb_tran.raw"
FIG  = f"{BASE}/report/figures/phase3_cm_step.png"
VCM_REF = 0.9
T_ON, T_OFF = 600e-9, 800e-9     # disturbance edges (s)

raw = RawRead(RAW)
names = {n.lower(): n for n in raw.get_trace_names()}
t  = np.asarray(raw.get_axis())
def g(n): return np.asarray(raw.get_trace(names[n.lower()]).get_wave())
vp, vn, vbcm = g("V(voutp)"), g("V(voutn)"), g("V(vbcm)")
cm   = 0.5*(vp+vn)
diff = vp-vn

def at(tt):                       # sample value just before time tt
    i = np.searchsorted(t, tt)-1
    return cm[i]

# --- steady CM windows (avoid clock-edge ripple by averaging over a window) ---
def win_mean(t0, t1, arr=cm):
    m = (t >= t0) & (t <= t1)
    return arr[m].mean(), arr[m].std()

cm_pre,   cm_pre_sd   = win_mean(540e-9, 598e-9)    # before disturbance (well settled)
cm_dist,  cm_dist_sd  = win_mean(760e-9, 798e-9)    # settled during disturbance
cm_post,  cm_post_sd  = win_mean(950e-9, 999e-9)    # after disturbance removed

# --- CM-loop response time constant on the step-ON edge -------------------
# (continuous C7/C8 path: time for CM to traverse 1-1/e of the way from the
#  pre-disturbance level to the settled-during-disturbance level)
target = cm_dist
seg = (t >= T_ON) & (t <= T_ON+40e-9)
ts, ys = t[seg]-T_ON, cm[seg]
total = cm_pre - target
thresh = cm_pre - (1-1/np.e)*total                 # 1/e of the way there
hit = np.where(ys <= thresh)[0]
tau_cm = ts[hit[0]] if len(hit) else np.nan
f_cm = 1/(2*np.pi*tau_cm) if tau_cm and not np.isnan(tau_cm) else np.nan
cm_dip = ys.min()

# --- ringing / overshoot check on the step-OFF recovery edge --------------
m_off = (t >= T_OFF) & (t <= T_OFF+60e-9)
cm_off = cm[m_off]
overshoot = cm_off.max() - cm_post

# --- initial SC settling (startup) ----------------------------------------
m_set = (t >= 50e-9) & (t <= 560e-9)
# time after t=0 for CM to come within 1 mV of its pre-disturbance settled value
err = np.abs(cm - cm_pre)
within = np.where((t > 30e-9) & (err <= 1e-3))[0]
t_settle = t[within[0]] if len(within) else np.nan

print("=== Phase-3 CM-step transient (real SC-CMFB) ===")
print(f"  CM settled (pre-disturb)    : {cm_pre*1e3:8.3f} mV  (ripple sd {cm_pre_sd*1e3:.3f} mV, ref 900)")
print(f"  initial SC settle to <1 mV  : {t_settle*1e9:8.1f} ns  (~{t_settle/50e-9:.1f} clock cycles)")
print(f"  CM dip at +50uA step-on     : {cm_dip*1e3:8.3f} mV  (drop {(cm_pre-cm_dip)*1e3:.2f} mV)")
print(f"  CM-loop response tau_cm     : {tau_cm*1e9:8.3f} ns   -> f_cm ~= {f_cm/1e6:.1f} MHz  (diff loop f_u=52.9 MHz)")
print(f"  CM settled during +50uA     : {cm_dist*1e3:8.3f} mV  -> closed-loop CM Z = {abs(cm_dist-cm_pre)/50e-6:.0f} ohm (=1/gm_cmfb)")
print(f"  CM after disturbance off    : {cm_post*1e3:8.3f} mV  -> returns to {cm_post*1e3:.2f} mV")
print(f"  overshoot on recovery edge  : {overshoot*1e3:+.3f} mV  (ringing check: stable if small)")
print(f"  max |diff| (Voutp-Voutn)    : {np.abs(diff).max()*1e3:8.3f} mV  (should stay ~0)")
print(f"  Vbcm range                  : {vbcm.min()*1e3:.2f} .. {vbcm.max()*1e3:.2f} mV")

# ---------------- figure ----------------
fig, ax = plt.subplots(3, 1, figsize=(9, 8.2), sharex=True)
tns = t*1e9

ax[0].axvspan(T_ON*1e9, T_OFF*1e9, color="0.92", label="+50 µA CM disturbance")
ax[0].axhline(900, color="r", lw=0.8, ls="--", label="$V_{cm,ref}=0.9$ V")
ax[0].plot(tns, cm*1e3, color="C0", lw=1.0)
ax[0].set_ylabel("Output CM\n$(V_{o+}+V_{o-})/2$  [mV]")
ax[0].set_title("Phase-3 SC-CMFB — common-mode step response (20 MHz clock)")
ax[0].legend(loc="upper right", fontsize=8); ax[0].grid(alpha=0.3)
ax[0].set_ylim(min(cm_dip*1e3-5, 880), 905)

ax[1].axvspan(T_ON*1e9, T_OFF*1e9, color="0.92")
ax[1].plot(tns, diff*1e3, color="C3", lw=1.0)
ax[1].set_ylabel("Differential\n$V_{o+}-V_{o-}$  [mV]")
ax[1].set_ylim(-1, 1)
ax[1].text(0.02, 0.85, "differential stays at 0 (CMFB orthogonal to diff mode)",
           transform=ax[1].transAxes, fontsize=8, color="0.3")
ax[1].grid(alpha=0.3)

ax[2].axvspan(T_ON*1e9, T_OFF*1e9, color="0.92")
ax[2].plot(tns, vbcm*1e3, color="C2", lw=1.0)
ax[2].set_ylabel("CMFB control\n$V_{bcm}$  [mV]")
ax[2].set_xlabel("time [ns]"); ax[2].grid(alpha=0.3)
ax[2].set_xlim(0, 1000)

fig.tight_layout()
fig.savefig(FIG, dpi=130)
print(f"\nsaved figure -> {FIG}")
