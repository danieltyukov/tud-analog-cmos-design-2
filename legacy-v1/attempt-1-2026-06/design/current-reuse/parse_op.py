#!/usr/bin/env python3
"""Parse an LTspice .op device table (from the batch .log) and print a compact
summary of the key main-amp devices: Id, Vds, Vdsat, sat-margin, Gm, gm/Id.
Also sums the main-amp supply current (2x top PMOS Mp1.2/Mp3.2 + booster Vdd draw)
as a quick I(Vdd) estimate. Usage: parse_op.py [log_path]"""
import sys, re

LOG = sys.argv[1] if len(sys.argv) > 1 else "folded_cascode_cr.log"
txt = open(LOG, errors="ignore").read()

# Build {device: {param: value}}
dev = {}
blocks = re.split(r"\nName:", txt)
for b in blocks[1:]:
    lines = b.splitlines()
    names = lines[0].split()
    cols = {n: {} for n in names}
    for ln in lines[1:]:
        m = re.match(r"\s*([A-Za-z]+):\s+(.*)", ln)
        if not m:
            continue
        key = m.group(1)
        vals = m.group(2).split()
        if key in ("Model",):
            continue
        for n, v in zip(names, vals):
            try:
                cols[n][key] = float(v)
            except ValueError:
                pass
    dev.update(cols)

def row(name):
    d = dev.get(name.lower()) or dev.get(name)
    if not d:
        return f"  {name:9s}  (not found)"
    Id = d.get("Id", 0.0); Vds = d.get("Vds", 0.0); Vdsat = d.get("Vdsat", 0.0)
    Gm = d.get("Gm", 0.0)
    margin = abs(Vds) - abs(Vdsat)
    gmid = Gm/abs(Id) if Id else 0.0
    flag = " <-- SUBTHRESH/OFF" if abs(Id) < 1e-7 else ("  <<< NOT SAT" if margin < 0 else "")
    return (f"  {name:9s} Id={Id*1e6:8.2f}uA Vds={Vds:+6.3f} Vdsat={Vdsat:+6.3f} "
            f"margin={margin*1e3:6.1f}mV Gm={Gm*1e3:6.2f}mS gm/Id={gmid:5.1f}{flag}")

KEY = ["Mp1.2","Mp3.2","Mn3.2","Mn4.2","Mp2.2","Mp4.2",
       "Mn5.2","Mn6.2","Mn7.2","Mn8.2","Mn1.2","Mn2.2"]
print(f"=== {LOG} : main-amp core ===")
for k in KEY:
    print(row(k))

# transconductance summary
def g(n): return dev.get(n.lower(),{}).get("Gm",0.0)
def i(n): return dev.get(n.lower(),{}).get("Id",0.0)
gmn = g("mn3.2"); gmp = g("mp1.2")
print(f"\n  g_m,n(Mn3.2)={gmn*1e3:.2f}mS  g_m,p(Mp1.2)={gmp*1e3:.2f}mS  "
      f"g_m,total={(gmn+gmp)*1e3:.2f}mS")
Ipin = abs(i("mp1.2")); Inin = abs(i("mn3.2"))
print(f"  I_pin(Mp1.2)={Ipin*1e6:.1f}uA  I_nin(Mn3.2)={Inin*1e6:.1f}uA  "
      f"I_cas={ (Ipin-Inin)*1e6:.1f}uA")

# booster Vdd draw: PMOS devices whose source is Vdd (top sources + pull-ups)
# BA: Mta_a(tail,pmos) + Ms1_a/Ms2_a(pull-up pmos) + Mcmp1_a/Mcmp2_a(cmfb mirror pmos)
# BB: Mbb1_b/Mbb2_b(top src pmos) + Mcmp1_b/Mcmp2_b(cmfb pmos)
ba = abs(i("mta_a")) + abs(i("ms1_a")) + abs(i("ms2_a")) + abs(i("mcmp1_a")) + abs(i("mcmp2_a"))
bb = abs(i("mbb1_b")) + abs(i("mbb2_b")) + abs(i("mcmp1_b")) + abs(i("mcmp2_b"))
core = 2*Ipin
print(f"\n  core supply (2*I_pin) = {core*1e6:.1f}uA")
print(f"  booster A Vdd draw ~ {ba*1e6:.1f}uA   booster B Vdd draw ~ {bb*1e6:.1f}uA")
print(f"  EST total I(Vdd) ~ {(core+ba+bb)*1e6:.1f}uA  ->  P ~ {(core+ba+bb)*1.8*1e3:.3f} mW")
