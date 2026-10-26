#!/usr/bin/env python3
"""Scale the gain-booster device multipliers (m=) by a factor to raise their
transconductance/bandwidth -> push the booster pole-zero DOUBLET beyond w_u so
the high-accuracy (78 dB / 25 ns) settling tail decays in time (Binkley rule).
Operates on the booster devices only (InstName ending _a or _b), NOT the main
amp (.2) or bias devices. Usage: scale_boosters.py <file.asc> <factor>"""
import sys, re
f = sys.argv[1]
k = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
lines = open(f).read().split("\n")
out = []
i = 0
nchg = 0
while i < len(lines):
    ln = lines[i]
    if ln.startswith("SYMBOL"):
        # gather the block to find InstName + Value2
        blk = [ln]; j = i + 1
        name = None
        while j < len(lines) and (lines[j].startswith("SYMATTR") or lines[j].startswith("WINDOW")):
            blk.append(lines[j])
            m = re.match(r"SYMATTR InstName (\S+)", lines[j])
            if m: name = m.group(1)
            j += 1
        is_booster = bool(name) and (name.endswith("_a") or name.endswith("_b"))
        if is_booster:
            for bi, bl in enumerate(blk):
                mm = re.search(r"(Value2 .*m=)(\d+)", bl)
                if mm:
                    newm = max(1, round(int(mm.group(2)) * k))
                    blk[bi] = bl[:mm.start(2)] + str(newm) + bl[mm.end(2):]
                    nchg += 1
        out.extend(blk)
        i = j
        continue
    out.append(ln)
    i += 1
open(f, "w").write("\n".join(out))
print(f"scaled {nchg} booster device m-values by {k} in {f}")
