#!/usr/bin/env python3
"""Convert the current-reuse .op bench (cr.asc copy) into a closed-loop
differential-step SETTLING bench (Deliverable 4).

Edits:
  * close the loop : Lbig 1T -> 1f (L1/L2 become shorts -> Vip=Vinpp, Vin=Vinpn)
  * split the common Cin far-end node N021 into Nfn (Vin side) / Nfp (Vip side)
    by removing the 3 vertical wires that tied them + the V6 tap
  * delete the AC-drive sources V3,V4,V5 and the common far-end ref V6
  * add two PULSE far-end sources Vsn(Nfn), Vsp(Nfp): 1.275 +/- 0.1125 step at 30 ns
    -> 0.225 V differential far-end step -> 0.9 V differential output (gain 4)
  * swap .op + AC .meas for .tran + settling .meas (A(t), Abeta(t), tau, power)
"""
import re
src = "folded_cascode_cr_tran.asc"
lines = open(src).read().split("\n")

# ---- 1. wires that form the common N021 node (remove to split) ----
DROP_WIRE = {
    "WIRE 1280 2064 1280 1760",   # N021 vertical top half
    "WIRE 1280 2368 1280 2064",   # N021 vertical bottom half
    "WIRE 1280 2064 1184 2064",   # N021 -> V6 tap
}
# ---- 2. voltage sources to delete (AC drive + common far-end ref) ----
DEL_SYM = {"V3", "V4", "V5", "V6"}

out, i = [], 0
while i < len(lines):
    ln = lines[i]
    p = ln.split()
    # drop a SYMBOL block whose InstName is in DEL_SYM
    if p[:1] == ["SYMBOL"]:
        j = i + 1
        name = None
        while j < len(lines) and (lines[j].startswith("SYMATTR") or lines[j].startswith("WINDOW")):
            m = re.match(r"SYMATTR InstName (\S+)", lines[j])
            if m:
                name = m.group(1)
            j += 1
        if name in DEL_SYM:
            i = j
            continue
    if ln in DROP_WIRE:
        i += 1
        continue
    # close the loop
    if ln.startswith("TEXT") and "Lbig=1T" in ln:
        ln = ln.replace("Lbig=1T", "Lbig=1f")
    # stiffen the sim-only DC bias so the input CM is pinned to (4*Vfar+Vout_CM)/5
    # = 1.2 V (only affects DC bias, NOT the MHz settling; this is the transient bench)
    if ln.startswith("TEXT") and "Rbig=100G Rin=100G" in ln:
        ln = ln.replace("Rin=100G", "Rin=1G")
    # NOTE: the G=12 moderate-gain CMFB helper (Rhelp=100Meg dominant pole -> stable,
    # pins out-CM ~0.9 V) is inherited from cr.asc; no override needed here.
    # swap .op for .tran
    if ln.startswith("TEXT") and re.search(r"!\.op\b", ln):
        ln = ln.replace("!.op", "!.tran 0 60n 0 0.05n")
    # drop the AC .meas directive TEXT lines + the ac sweep comment + closed-loop AC meas
    if ln.startswith("TEXT") and (".meas AC" in ln or ";ac dec" in ln
                                  or "AC MEASUREMENTS" in ln or "CLOSED-LOOP BANDWIDTH" in ln):
        i += 1
        continue
    out.append(ln)
    i += 1

# ---- 3. add far-end flags, the two PULSE sources, and settling .meas ----
add = []
# label the two split far-ends
add += ["FLAG 1280 1760 Nfn", "FLAG 1280 2368 Nfp"]
# Vsn on Nfn (Vin-side far end): steps DOWN 0.1125 at 30 ns
# LTspice 'voltage' R0 pins: +(top) at origin+(0,16), -(bot) at origin+(0,96)
add += ["SYMBOL voltage 1088 2064 R0", "SYMATTR InstName Vsn",
        "SYMATTR Value PULSE(1.275 1.1625 30n 0.05n 0.05n 1m 2m)"]
add += ["FLAG 1088 2160 0", "FLAG 1088 2080 Nfn"]
# Vsp on Nfp (Vip-side far end): steps UP 0.1125 at 30 ns
add += ["SYMBOL voltage 1344 2064 R0", "SYMATTR InstName Vsp",
        "SYMATTR Value PULSE(1.275 1.3875 30n 0.05n 0.05n 1m 2m)"]
add += ["FLAG 1344 2160 0", "FLAG 1344 2080 Nfp"]
# settling measurements (Vout_max = 0.9 V diff ; gain 4 ; vg = V(Vip)-V(Vin))
ax = "20*log10(0.9/(abs(V(Vip)-V(Vin))+1n))"
meas = [
    "TEXT 1208 -904 Left 2 !; === SETTLING (D4): A(t), Abeta(t), tau ===",
    f"TEXT 1208 -864 Left 2 !.meas TRAN offset MIN {ax} FROM 30n TO 31n",
    f"TEXT 1208 -824 Left 2 !.meas TRAN A_25ns FIND {ax} AT 55n",
    "TEXT 1208 -784 Left 2 !.meas TRAN Abeta_25ns PARAM A_25ns-offset",
    f"TEXT 1208 -744 Left 2 !.meas TRAN T30dB WHEN {ax}=30 RISE=1 TD=30.2n",
    f"TEXT 1208 -704 Left 2 !.meas TRAN T3869dB WHEN {ax}=38.69 RISE=1 TD=30.2n",
    "TEXT 1208 -664 Left 2 !.meas TRAN tau PARAM T3869dB-T30dB",
    "TEXT 1208 -624 Left 2 !.meas TRAN idd AVG I(V2) FROM 10n TO 29n",
    "TEXT 1208 -584 Left 2 !.meas TRAN power_mW PARAM abs(idd)*1.8*1000",
]
out = out + add + meas
open(src, "w").write("\n".join(out) + "\n")
nW = sum(1 for l in add if l.startswith("WIRE"))
print(f"wrote {src}: {len(out)} lines (+{len(add)} drive lines, +{len(meas)} meas)")
