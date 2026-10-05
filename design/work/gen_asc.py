#!/usr/bin/env python3
"""Generate the deliverable schematics design/final/amp_tran.asc and amp_noise.asc from design/work.

  uv run python design/work/gen_asc.py

Every element is a drawn LTspice symbol and every local connection is a drawn wire; net-label flags
are used only for sheet-spanning nets (ground, vdd, vddb, vcmr, bias lines, the CMFB control line,
and the amplifier ports vip/vin/vop/von where they cross blocks). Parameters come from the .param
lines of design/work/amp.inc and the bench files, so the drawing always matches the netlist.
Pin offsets are the LTspice XVII symbol geometry (nmos4/pmos4/res/cap/current/voltage).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / "design" / "work"
FINAL = REPO / "design" / "final"


class Sheet:
    def __init__(self):
        self.lines: list[str] = []
        self.wires: list[tuple[int, int, int, int]] = []
        self.flags: list[tuple[int, int, str]] = []
        self.texts: list[str] = []
        self.rects: list[str] = []
        self.pin_dirs: dict[tuple[int, int], tuple[int, int]] = {}   # pin point -> outward unit vector

    def pins(self, d: dict, dirs: dict) -> dict:
        for k, v in d.items():
            self.pin_dirs[v] = dirs[k]
        return d

    # ---------------------------------------------------------------- primitives
    def symbol(self, sym, ref, x, y, rot, value=None, value2=None, extra=None):
        self.lines.append(f"SYMBOL {sym} {x} {y} {rot}")
        self.lines.append(f"SYMATTR InstName {ref}")
        if value is not None:
            self.lines.append(f"SYMATTR Value {value}")
        if value2 is not None:
            self.lines.append(f"SYMATTR Value2 {value2}")
        for k, v in (extra or {}).items():
            self.lines.append(f"SYMATTR {k} {v}")

    def wire(self, *pts):
        """Polyline through points; every segment must be horizontal or vertical."""
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            assert x1 == x2 or y1 == y2, f"diagonal wire {pts}"
            if (x1, y1) != (x2, y2):
                self.wires.append((x1, y1, x2, y2))

    def flag(self, p, name):
        """Flag a point; on a device pin it sits at the end of a short drawn stub."""
        if p in self.pin_dirs:
            dx, dy = self.pin_dirs[p]
            q = (p[0] + 32 * dx, p[1] + 32 * dy)
            self.wire(p, q)
            p = q
        self.flags.append((p[0], p[1], name))

    def text(self, x, y, s, size=2, directive=False):
        self.texts.append(f"TEXT {x} {y} Left {size} {'!' if directive else ';'}{s}")

    def box(self, x1, y1, x2, y2, title):
        self.rects.append(f"RECTANGLE Normal {x2} {y2} {x1} {y1} 2")
        self.text(x1 + 16, y1 + 40, title, size=3)

    # ---------------------------------------------------------------- devices
    # Each helper places a device by its drain/source spine x and body top y and returns pin points.
    def nmos(self, ref, sx, ty, gate="left", value2=""):
        if gate == "left":
            self.symbol("nmos4", ref, sx - 48, ty, "R0", "nch", value2)
            g = (sx - 48, ty + 80)
        else:
            self.symbol("nmos4", ref, sx + 48, ty, "M0", "nch", value2)
            g = (sx + 48, ty + 80)
        gx = -1 if gate == "left" else 1
        return self.pins({"D": (sx, ty), "S": (sx, ty + 96), "B": (sx, ty + 48), "G": g},
                         {"D": (0, -1), "S": (0, 1), "B": (-gx, 0), "G": (gx, 0)})

    def pmos(self, ref, sx, ty, gate="left", value2=""):
        """Source at the top (ty), drain at the bottom (ty+96)."""
        if gate == "left":
            self.symbol("pmos4", ref, sx - 48, ty + 96, "M180", "pch", value2)
            g = (sx - 48, ty + 16)
        else:
            self.symbol("pmos4", ref, sx + 48, ty + 96, "R180", "pch", value2)
            g = (sx + 48, ty + 16)
        gx = -1 if gate == "left" else 1
        return self.pins({"S": (sx, ty), "D": (sx, ty + 96), "B": (sx, ty + 48), "G": g},
                         {"S": (0, -1), "D": (0, 1), "B": (-gx, 0), "G": (gx, 0)})

    def cap_v(self, ref, px, ty, value):
        """Vertical capacitor with pins at (px, ty) top and (px, ty+64) bottom."""
        self.symbol("cap", ref, px - 16, ty, "R0", value)
        return self.pins({"A": (px, ty), "B": (px, ty + 64)}, {"A": (0, -1), "B": (0, 1)})

    def cap_h(self, ref, lx, py, value):
        """Horizontal capacitor with pins at (lx, py) left and (lx+64, py) right."""
        self.symbol("cap", ref, lx + 64, py - 16, "R90", value)
        return {"B": (lx, py), "A": (lx + 64, py)}

    def res_v(self, ref, px, ty, value):
        """Vertical resistor with pins at (px, ty) top and (px, ty+80) bottom."""
        self.symbol("res", ref, px - 16, ty - 16, "R0", value)
        return self.pins({"A": (px, ty), "B": (px, ty + 80)}, {"A": (0, -1), "B": (0, 1)})

    def res_h(self, ref, lx, py, value):
        """Horizontal resistor with pins at (lx, py) left and (lx+80, py) right."""
        self.symbol("res", ref, lx + 96, py - 16, "R90", value)
        return {"B": (lx, py), "A": (lx + 80, py)}

    def isrc(self, ref, px, ty, value):
        """Current source, + at (px, ty) top, - at (px, ty+80) bottom (current flows + to - inside)."""
        self.symbol("current", ref, px, ty, "R0", value)
        return self.pins({"+": (px, ty), "-": (px, ty + 80)}, {"+": (0, -1), "-": (0, 1)})

    def vsrc(self, ref, px, ty, value, value2=None):
        """Voltage source, + at (px, ty) top, - at (px, ty+80) bottom."""
        self.symbol("voltage", ref, px, ty - 16, "R0", value, value2)
        return self.pins({"+": (px, ty), "-": (px, ty + 80)}, {"+": (0, -1), "-": (0, 1)})

    def split_wires(self):
        """Split segments at interior points where a flag or another wire's end lands (explicit T-junctions)."""
        pts = {(x, y) for x, y, _ in self.flags}
        for a, b, c, d in self.wires:
            pts.add((a, b)); pts.add((c, d))
        out = []
        for x1, y1, x2, y2 in self.wires:
            cuts = sorted({p for p in pts if (p != (x1, y1) and p != (x2, y2) and
                          ((x1 == x2 == p[0] and min(y1, y2) < p[1] < max(y1, y2)) or
                           (y1 == y2 == p[1] and min(x1, x2) < p[0] < max(x1, x2))))},
                          key=lambda p: abs(p[0] - x1) + abs(p[1] - y1))
            chain = [(x1, y1)] + cuts + [(x2, y2)]
            out += [(a[0], a[1], b[0], b[1]) for a, b in zip(chain, chain[1:])]
        self.wires = out

    def render(self, w=5600, h=3400):
        self.split_wires()
        out = ["Version 4", f"SHEET 1 {w} {h}"]
        out += [f"WIRE {a} {b} {c} {d}" for a, b, c, d in self.wires]
        out += [f"FLAG {x} {y} {n}" for x, y, n in self.flags]
        out += self.lines + self.rects + self.texts
        return "\n".join(out) + "\n"


def params(path: Path) -> list[str]:
    """.param lines of a file, comments stripped."""
    out = []
    for line in path.read_text().splitlines():
        if line.strip().lower().startswith(".param"):
            out.append(line.split(";")[0].rstrip())
    return out


def mos2(L, W, M):
    m = M if M.isdigit() else f"{{{M}}}"
    return f"l={{{L}}} w={{{W}}} m={m}"


def build(analysis: str) -> str:
    s = Sheet()
    # ======================================================================= Stage 1 (center)
    XA, XB, XC = 2240, 2752, 2496
    s.box(2080, 224, 2912, 1600, "Stage 1 (complementary input)")
    mtp = s.pmos("Mtp", XC, 400, "left", mos2("Lt", "Wt", "Mt"))
    s.flag(mtp["S"], "vdd"); s.flag(mtp["B"], "vdd"); s.flag(mtp["G"], "vbp")
    s.wire(mtp["D"], (XC, 560))
    s.wire((XA, 560), (XB, 560))                                   # ntp
    m1p = s.pmos("M1p", XA, 624, "left", mos2("Lip", "Wip", "Mip"))
    m2p = s.pmos("M2p", XB, 624, "right", mos2("Lip", "Wip", "Mip"))
    s.wire((XA, 560), m1p["S"]); s.wire((XB, 560), m2p["S"])
    s.wire(m1p["B"], (XA + 32, m1p["B"][1]), (XA + 32, 560))       # bulk = source (ntp)
    s.wire(m2p["B"], (XB - 32, m2p["B"][1]), (XB - 32, 560))
    mcp1 = s.pmos("Mcp1", XA, 784, "left", mos2("Lcp", "Wcp", "Mcp"))
    mcp2 = s.pmos("Mcp2", XB, 784, "right", mos2("Lcp", "Wcp", "Mcp"))
    s.wire(m1p["D"], mcp1["S"]); s.wire(m2p["D"], mcp2["S"])        # nb1, nb2
    for m in (mcp1, mcp2):
        s.flag(m["G"], "vcp"); s.flag(m["B"], "vdd")
    mcn1 = s.nmos("Mcn1", XA, 976, "left", mos2("Lcn", "Wcn", "Mcn"))
    mcn2 = s.nmos("Mcn2", XB, 976, "right", mos2("Lcn", "Wcn", "Mcn"))
    s.wire(mcp1["D"], mcn1["D"]); s.wire(mcp2["D"], mcn2["D"])      # v1n, v1p
    for m in (mcn1, mcn2):
        s.flag(m["G"], "vcn"); s.flag(m["B"], "0")
    m1n = s.nmos("M1n", XA, 1136, "left", mos2("Lin", "Win", "Min"))
    m2n = s.nmos("M2n", XB, 1136, "right", mos2("Lin", "Win", "Min"))
    s.wire(mcn1["S"], m1n["D"]); s.wire(mcn2["S"], m2n["D"])        # na1, na2
    s.flag(m1n["B"], "0"); s.flag(m2n["B"], "0")
    s.wire(m1n["S"], (XA, 1296), (XB, 1296), m2n["S"])               # ntn
    mtn = s.nmos("Mtn", XC - 96, 1360, "left", mos2("Ltn", "Wtn", "Mtn"))
    mtc = s.nmos("Mtc", XC + 96, 1360, "right", mos2("Ltn", "Wtn", "Mtc"))
    s.wire(mtn["D"], (XC - 96, 1296)); s.wire(mtc["D"], (XC + 96, 1296))
    for m in (mtn, mtc):
        s.flag(m["S"], "0"); s.flag(m["B"], "0")
    s.flag(mtn["G"], "vbn"); s.flag(mtc["G"], "vcmfb")
    # inputs: one vertical per side joins the PMOS and NMOS input gates
    xin_a, xin_b = XA - 128, XB + 128
    s.wire(m1p["G"], (xin_a, m1p["G"][1]), (xin_a, m1n["G"][1]), m1n["G"])
    s.wire(m2p["G"], (xin_b, m2p["G"][1]), (xin_b, m2n["G"][1]), m2n["G"])
    s.flag((xin_a, 928 + 96), "vin"); s.flag((xin_b, 928 + 96), "vip")
    # node-name tags (nets already wired; the names make the report's D2/D3 values traceable)
    for pt, nm in (((XC, 560), "ntp"), ((XA, 752), "nb1"), ((XB, 752), "nb2"), ((XA, 1104), "na1"),
                   ((XB, 1104), "na2"), ((XC, 1296), "ntn")):
        s.flag(pt, nm)
    # C1d across the two stage-1 outputs
    c1d = s.cap_h("C1d", XC - 32, 928, "{C1d}")
    s.wire((XA, 928), c1d["B"]); s.wire(c1d["A"], (XB, 928))

    # ======================================================================= Stage 2 + compensation, side a (left)
    def out_stage(side):
        sgn = -1 if side == "a" else 1
        X1 = XA if side == "a" else XB
        XO = X1 + sgn * 560                       # output spine
        XL = X1 + sgn * 336                       # v1 / level-shift column
        XR = X1 + sgn * 448                       # Rb column
        k = "1" if side == "a" else "2"
        out, v1 = ("von", "v1n") if side == "a" else ("vop", "v1p")
        gside = "right" if side == "a" else "left"
        bx1, bx2 = (XO - 112, X1 - 176) if side == "a" else (X1 + 176, XO + 112)
        s.box(bx1, 224, bx2, 1600, f"Stage 2{'A' if side == 'a' else 'B'} + comp.")
        mop = s.pmos(f"Mop{k}", XO, 400, gside, mos2("Lop", "Wop", "Mop"))
        mon = s.nmos(f"Mon{k}", XO, 1136, gside, mos2("Lon", "Won", "Mon"))
        s.flag(mop["S"], "vdd"); s.flag(mop["B"], "vdd"); s.flag(mon["S"], "0"); s.flag(mon["B"], "0")
        s.wire(mop["D"], mon["D"])                # output node
        s.flag((XO, 816), out)
        # level shift: Cls from v1 to gate, Rb from gate to vbo
        cls = s.cap_v(f"Cls{k}", XL, 560, "{Cls}")
        rb = s.res_v(f"Rb{k}", XR, mop["G"][1], "{Rb}")
        s.wire(mop["G"], rb["A"], (XL, mop["G"][1]), cls["A"])
        s.flag(rb["B"], "vbo")
        s.wire(cls["B"], (XL, 928), (X1, 928))     # v1 bus
        s.wire((XL, 928), (XL, mon["G"][1]), mon["G"])
        s.flag((XL, 928), v1); s.flag((XL, mop["G"][1]), f"gp{k}")
        # compensation caps: output -> PMOS-cascode source (nb) and -> NMOS-cascode source (na)
        ylo, yhi = 752, 1104
        lx = XO + 96 if side == "a" else XO - 160
        for name, yy in ((f"Cc{3 if k == '1' else 4}", ylo), (f"Cc{k}", yhi)):
            c = s.cap_h(name, lx, yy, "{(1-fcc)*Cc}" if yy == ylo else "{fcc*Cc}")
            near, far = (c["B"], c["A"]) if side == "a" else (c["A"], c["B"])
            s.wire(near, (XO, yy)); s.wire(far, (X1, yy))

    out_stage("a")
    out_stage("b")

    # ======================================================================= CMFB (right)
    X0 = 3600
    s.box(X0, 224, X0 + 1040, 1600, "CMFB (continuous time)")
    r1 = s.res_h("Rcm1", X0 + 96, 480, "{Rcm}")
    r2 = s.res_h("Rcm2", X0 + 96, 640, "{Rcm}")
    c1 = s.cap_h("Ccm1", X0 + 96, 400, "{Ccm}")
    c2 = s.cap_h("Ccm2", X0 + 96, 720, "{Ccm}")
    xs = X0 + 304                               # vcms column
    s.wire(r1["B"], (X0 + 64, 480)); s.wire(c1["B"], (X0 + 64, 400), (X0 + 64, 480))
    s.wire(r2["B"], (X0 + 64, 640)); s.wire(c2["B"], (X0 + 64, 720), (X0 + 64, 640))
    s.flag((X0 + 64, 480), "vop"); s.flag((X0 + 64, 640), "von")
    s.wire(c1["A"], (xs, 400), (xs, 720), c2["A"])
    s.wire(r1["A"], (xs, 480)); s.wire(r2["A"], (xs, 640))
    xp1, xp2 = X0 + 512, X0 + 800
    mct = s.pmos("Mct", (xp1 + xp2) // 2, 400, "left", mos2("Lt", "Wctl", "1"))
    s.flag(mct["S"], "vdd"); s.flag(mct["B"], "vdd"); s.flag(mct["G"], "vbp")
    s.wire(mct["D"], ((xp1 + xp2) // 2, 576))
    s.wire((xp1, 576), (xp2, 576))              # ncs
    mc1 = s.pmos("Mc1", xp1, 640, "left", mos2("Lcm", "Wcm", "1"))
    mc2 = s.pmos("Mc2", xp2, 640, "right", mos2("Lcm", "Wcm", "1"))
    s.wire((xp1, 576), mc1["S"]); s.wire((xp2, 576), mc2["S"])
    s.wire(mc1["B"], (xp1 + 32, mc1["B"][1]), (xp1 + 32, 576))
    s.wire(mc2["B"], (xp2 - 32, mc2["B"][1]), (xp2 - 32, 576))
    s.wire((xs, 560), (xs + 64, 560), (xs + 64, mc1["G"][1]), mc1["G"])   # vcms -> Mc1 gate
    s.flag(mc2["G"], "vcmr")
    mc3 = s.nmos("Mc3", xp1, 960, "right", mos2("Ltn", "Wc3", "1"))
    mc4 = s.nmos("Mc4", xp2, 960, "left", mos2("Ltn", "Wc3", "1"))
    s.wire(mc1["D"], mc3["D"]); s.wire(mc2["D"], mc4["D"])
    s.wire(mc3["G"], (xp1 + 80, mc3["G"][1]), (xp1 + 80, 896), (xp1, 896))   # diode
    s.wire(mc4["G"], (xp2 - 80, mc4["G"][1]), (xp2 - 80, 896), (xp2, 896))
    for m in (mc3, mc4):
        s.flag(m["S"], "0"); s.flag(m["B"], "0")
    s.wire((xp1, 896), (xp1 - 192, 896))
    s.flag((xp1 - 192, 896), "vcmfb")
    s.flag((xs, 560), "vcms"); s.flag(((xp1 + xp2) // 2, 576), "ncs"); s.flag((xp2, 896), "ncm2")

    # ======================================================================= Bias block (left, top)
    s.box(0, 224, 1120, 1600, "Bias block (on Vddb, decoupled by Cbig)")
    cols = [("p", "Ibp", "{Ib}", "Mbp", ("Lt", "Wt"), "vbp", "Cb1"),
            ("n", "Ibn", "{kn*Ib}", "Mbn", ("Ltn", "Wtn"), "vbn", "Cb2"),
            ("p", "Ibo", "{ko*Ib}", "Mbo", ("Lop", "Wop"), "vbo", "Cb3"),
            ("n", "Ibcn", "{kcn*Ib}", "Mbcn", ("Lbcn", "Wbcn"), "vcn", "Cb4"),
            ("p", "Ibcp", "{kcp*Ib}", "Mbcp", ("Lbcp", "Wbcp"), "vcp", "Cb5")]
    for i, (typ, iref, ival, mref, (L, W), line, cref) in enumerate(cols):
        x = 112 + i * 208
        if typ == "p":
            m = s.pmos(mref, x, 432, "left", f"l={{{L}}} w={{{W}}} m=1")
            s.flag(m["S"], "vddb"); s.flag(m["B"], "vddb")
            src = s.isrc(iref, x, 784, ival)
            s.wire(m["D"], src["+"]); s.flag(src["-"], "0")
            s.wire(m["G"], (m["G"][0], 576), (x, 576))                  # diode: gate to drain
            node = (x, 640)
        else:
            src = s.isrc(iref, x, 432, ival)
            s.flag(src["+"], "vddb")
            m = s.nmos(mref, x, 752, "left", f"l={{{L}}} w={{{W}}} m=1")
            s.wire(src["-"], m["D"])
            s.flag(m["S"], "0"); s.flag(m["B"], "0")
            s.wire(m["G"], (m["G"][0], 704), (x, 704))
            node = (x, 640)
        cb = s.cap_v(cref, x + 96, 1040, "{Cbig}")
        s.wire(node, (x + 96, node[1]), cb["A"])
        s.flag(cb["B"], "0")
        s.flag((x + 96, node[1]), line)

    # ======================================================================= Test bench (left, bottom)
    s.box(0, 1712, 2240, 2640, "Fixed test bench (Cin/Cfb = 4, Cload = Cin)")
    for i, (ref, val, net) in enumerate([("Vdd", "{VDD}", "vdd"), ("Vddb", "{VDD}", "vddb"), ("Vcmr", "{VCM}", "vcmr")]):
        v = s.vsrc(ref, 128 + i * 160, 1856, val)
        s.flag(v["+"], net); s.flag(v["-"], "0")
    vinp = s.vsrc("Vinp", 608, 2032, "PULSE({VCMI} {VCMI+VinStep/2} {tstep} {trise} {trise} 1 2)", "AC 0.5")
    vinn = s.vsrc("Vinn", 608, 2416, "PULSE({VCMI} {VCMI-VinStep/2} {tstep} {trise} {trise} 1 2)", "AC -0.5")
    s.flag(vinp["-"], "0"); s.flag(vinn["-"], "0")
    for k, (src, sn, fb, out) in enumerate([(vinp, "vin", "Cfb1", "vop"), (vinn, "vip", "Cfb2", "von")]):
        y0 = 1904 + k * 384
        n = str(k + 1)
        cin = s.cap_h(f"Cin{n}", 800, y0, "{Cin}")
        rin = s.res_h(f"Rin{n}", 784, y0 + 96, "{Rin} noiseless")
        cfb = s.cap_h(f"Cfb{n}", 1216, y0, "{Cfb}")
        rfb = s.res_h(f"Rfb{n}", 1200, y0 + 96, "{Rfb} noiseless")
        cl = s.cap_v(f"Cload{n}", 1520, y0 + 32, "{Cload}")
        # input node
        s.wire(src["+"], (src["+"][0], y0), (720, y0), cin["B"])
        s.wire((720, y0), (720, y0 + 96), rin["B"])
        s.flag((720, y0), "inp" if k == 0 else "inn")
        # summing node
        s.wire(cin["A"], (1008, y0), cfb["B"]); s.wire(rin["A"], (1008, y0 + 96), (1008, y0))
        s.wire(rfb["B"], (1136, y0 + 96), (1136, y0))
        s.flag((1008, y0), sn)
        # output node
        s.wire(cfb["A"], (1520, y0), cl["A"]); s.wire(rfb["A"], (1360, y0 + 96), (1360, y0))
        s.flag(cl["B"], "0"); s.flag((1520, y0), out)

    # ======================================================================= directives box
    dirs = [".lib 'log018.l' TT"]  # portable: design/final/log018.l (relative self-includes) sits next to the schematics
    bench = WORK / ("bench_tran.cir" if analysis == "tran" else "bench_noise.cir")
    tran_params = params(WORK / "bench_tran.cir")
    if analysis == "noise":  # only what the noise sheet uses (the input sources need tstep, trise, VinStep)
        tran_params = [re.sub(r"\s+(Tsettle|tstop)=(\{[^}]*\}|\S+)", "", l) for l in tran_params]
    dirs += tran_params
    dirs += params(WORK / "amp.inc")
    if analysis == "tran":
        for line in bench.read_text().splitlines():
            if line.strip().lower().startswith((".tran", ".option", ".meas")):
                dirs.append(line.strip())
    else:
        for line in bench.read_text().splitlines():
            if line.strip().lower().startswith((".noise", ".meas")):
                dirs.append(line.strip())
    y = 1808
    for d in dirs:
        s.text(2432, y, d, directive=True)
        y += 40
    s.box(2400, 1712, 4640, y + 32, "Parameters, Simulations & Measurements")
    return s.render(h=max(2700, y + 100))


def main():
    FINAL.mkdir(parents=True, exist_ok=True)
    for a, name in (("tran", "amp_tran.asc"), ("noise", "amp_noise.asc")):
        (FINAL / name).write_text(build(a))
        print("wrote", FINAL / name)


if __name__ == "__main__":
    main()
