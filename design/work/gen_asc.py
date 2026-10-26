#!/usr/bin/env python3
"""Generate the deliverable schematics design/final/amp_tran.asc and amp_noise.asc from design/work.

  uv run python design/work/gen_asc.py

Attempt 3: telescopic cascode stage 1 + push-pull common-source stage 2, Miller Cc + Rz, continuous-time
CMFB, replica bias block on Vddb. Every element is a drawn LTspice symbol and every local connection is a
drawn wire; net-label flags are used only for sheet-spanning nets (ground, vdd, vddb, vcmr, bias lines,
the CMFB control line and the amplifier ports vip/vin/vop/von where they cross blocks). Parameters come
from the .param lines of design/work/amp.inc and the bench files, so the drawing matches the netlist.
Pin offsets are the LTspice XVII symbol geometry (nmos4/pmos4/res/cap/current/voltage).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / "design" / "work"
FINAL = REPO / "design" / "final"
MARK = ((-64, 128), (4992, 2800))   # report figures: top-left and bottom-right marker points (outside everything)
# report figures: crop windows (sheet coordinates) of the blocks
CROPS = {"amp": (1880, 230, 3752, 1300), "cmfb": (3864, 230, 4920, 1110), "bias": (-8, 230, 1704, 1250)}


class Sheet:
    def __init__(self):
        self.lines: list[str] = []
        self.wires: list[tuple[int, int, int, int]] = []
        self.flags: list[tuple[int, int, str]] = []
        self.texts: list[str] = []
        self.rects: list[str] = []
        self.pin_dirs: dict[tuple[int, int], tuple[int, int]] = {}   # pin point -> outward unit vector
        self.probes: list[tuple] = []                                     # report figures only: .op data labels

    def pins(self, d: dict, dirs: dict) -> dict:
        for k, v in d.items():
            self.pin_dirs[v] = dirs[k]
        return d

    # ---------------------------------------------------------------- primitives
    def symbol(self, sym, ref, x, y, rot, value=None, value2=None):
        self.lines.append(f"SYMBOL {sym} {x} {y} {rot}")
        self.lines.append(f"SYMATTR InstName {ref}")
        if value is not None:
            self.lines.append(f"SYMATTR Value {value}")
        if value2 is not None:
            self.lines.append(f"SYMATTR Value2 {value2}")

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

    def probe(self, kind, node, expr, to=None):
        """Report figures only: an LTspice .op data label ("v" for D2, "i" for D3) at `node`, or at the end of a
        short drawn leader from `node` to `to` (the leader joins the same net, so the circuit is unchanged)."""
        path = [node] + (list(to) if isinstance(to, list) else [to] if to is not None else [])
        self.probes.append((kind, path, expr))

    def vprobe(self, node, net, to=None):
        self.probe("v", node, f"round(V({net})*1e3)*1m", to)

    def iprobe(self, node, dev, to=None):
        self.probe("i", node, f"round(abs(I{'d' if dev[0] in 'Mm' else ''}({dev}))*1e7)*100n", to)

    def text(self, x, y, s, size=2, directive=False):
        self.texts.append(f"TEXT {x} {y} Left {size} {'!' if directive else ';'}{s}")

    def box(self, x1, y1, x2, y2, title):
        self.rects.append(f"RECTANGLE Normal {x2} {y2} {x1} {y1} 2")
        self.text(x1 + 16, y1 + 40, title, size=3)

    # ---------------------------------------------------------------- devices
    # Each helper places a device by its drain/source spine x and body top y and returns pin points.
    def nmos(self, ref, sx, ty, gate="left", value2=""):
        """Drain at the top (ty), source at the bottom (ty+96)."""
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

    def render(self, w=5200, h=3400, figure=None):
        probes = [p for p in self.probes if p[0] == figure] if figure else []
        for _, path, _ in probes:       # leaders exist only in the report figures
            if len(path) > 1:
                self.wire(*path)
        self.split_wires()
        out = ["Version 4", f"SHEET 1 {w} {h}"]
        out += [f"WIRE {a} {b} {c} {d}" for a, b, c, d in self.wires]
        out += [f"FLAG {x} {y} {n}" for x, y, n in self.flags]
        lines = self.lines
        if figure:  # hide model names and R/C parameter names; the captions give the values
            lines = []
            for l in self.lines:
                lines.append(l)
                if l.startswith(("SYMBOL nmos4", "SYMBOL pmos4", "SYMBOL res", "SYMBOL cap")):
                    lines.append("WINDOW 3 0 0 Invisible 2")
                if l.startswith("SYMBOL nmos4"):
                    lines.append("WINDOW 0 56 8 Left 2")
            out += [f'DATAFLAG {path[-1][0]} {path[-1][1]} "{e}"' for _, path, e in probes]
            # corner markers: tools/ltgui.py maps sheet coordinates to screen pixels from them
            out += [f"LINE Normal {MARK[0][0]} {MARK[0][1]} {MARK[0][0] + 16} {MARK[0][1]} 2",
                    f"LINE Normal {MARK[1][0] - 16} {MARK[1][1]} {MARK[1][0]} {MARK[1][1]} 2"]
        out += lines + self.rects + self.texts
        return "\n".join(out) + "\n"


def params(path: Path) -> list[str]:
    """.param lines of a file, comments stripped."""
    out = []
    for line in path.read_text().splitlines():
        if line.strip().lower().startswith(".param"):
            out.append(line.split(";")[0].rstrip())
    return out


def mos(L, W, M):
    m = M if str(M).isdigit() else f"{{{M}}}"
    return f"l={{{L}}} w={{{W}}} m={m}"


def build(analysis: str, figure: str | None = None) -> str:
    """analysis "tran" or "noise"; figure "v" (D2 node voltages) or "i" (D3 currents) builds a report-figure copy
    of the transient sheet with LTspice .op data labels (not a deliverable)."""
    s = Sheet()

    def idev(ref, pins, gate):
        """(unused) D3 labels are branch leaders, placed per block below."""
    TOP, BOT = 224, 1600                       # block row
    # ======================================================================= Bias block (left)
    s.box(0, TOP, 1696, BOT, "Bias block: replica of the stage-1 half circuit (on Vddb, Cbig decoupling)")

    def decouple(node, rref, cref, line, x0):
        """node -> Rdec -> bias line, Cbig from the line to ground; returns the line point."""
        x, y = node
        s.wire(node, (x0, y))
        r = s.res_h(rref, x0, y, "{Rdec}")
        xc = x0 + 128
        s.wire(r["A"], (xc, y))
        c = s.cap_v(cref, xc, y + 32, "{Cbig}")
        s.wire((xc, y), c["A"])
        s.flag(c["B"], "0")
        s.flag((xc, y), line)

    # P replica: tail unit + input unit (gate at vcmr), tail gate from the input unit's drain, Ibnp sink
    x = 176
    mbp0 = s.pmos("MBP0", x, 400, "left", mos("Lt", "Wt", 1))
    mbp1 = s.pmos("MBP1", x, 560, "left", mos("Li", "Wi", 1))
    s.flag(mbp0["S"], "vddb"); s.flag(mbp0["B"], "vddb")
    s.wire(mbp0["D"], mbp1["S"])
    s.wire(mbp1["B"], (x + 32, mbp1["B"][1]), (x + 32, 528), (x, 528))   # bulk = source (bp0)
    s.flag(mbp1["G"], "vcmr")
    ibnp = s.isrc("IBNP", x, 752, "{Ibnp}")
    s.wire(mbp1["D"], ibnp["+"])
    s.flag(ibnp["-"], "0")
    s.wire(mbp0["G"], (64, mbp0["G"][1]), (64, 704), (x, 704))          # self-cascode: tail gate = vbpr
    decouple((x, 704), "RD1", "CD1", "vbp", 240)
    s.flag((x, 528), "bp0"); s.flag((x, 704), "vbpr")
    s.vprobe((x, 528), "bp0", to=(x - 64, 528)); s.vprobe((368, 704), "vbp", to=(432, 704))
    s.iprobe((x, 848), "IBNP", to=(x - 64, 848))
    s.text(x - 160, 1040, "P replica: tail unit + input unit", size=1)

    # N replica: Ibnp into NMOS cascode unit + load unit, load gate from the cascode drain (vbnr)
    x = 624
    ibnn = s.isrc("IBNN", x, 400, "{Ibnp}")
    s.flag(ibnn["+"], "vddb")
    mbn5 = s.nmos("MBN5", x, 560, "left", mos("Lcn", "Wcn", 1))
    mbn7 = s.nmos("MBN7", x, 720, "left", mos("Ll", "Wl", 1))
    s.wire(ibnn["-"], mbn5["D"])
    s.wire(mbn5["S"], mbn7["D"])
    s.flag(mbn5["G"], "vcn"); s.flag(mbn5["B"], "0")
    s.flag(mbn7["S"], "0"); s.flag(mbn7["B"], "0")
    s.wire(mbn7["G"], (512, mbn7["G"][1]), (512, 528), (x, 528))         # load gate = cascode drain
    decouple((x, 528), "RD2", "CD2", "vbn", 688)
    s.flag((x, 528), "vbnr"); s.flag((x, 688), "bn5")
    s.vprobe((816, 528), "vbn", to=(880, 528)); s.vprobe((x, 688), "bn5", to=(x + 64, 688))
    s.iprobe((x, 496), "IBNN", to=(x - 64, 496))
    s.text(x - 128, 1040, "N replica: cascode unit + load unit", size=1)

    # Vcn: diode-connected NMOS fed by Ibcn = kcn*Ibnp
    x = 1056
    ibcn = s.isrc("IBCN", x, 400, "{kcn*Ibnp}")
    s.flag(ibcn["+"], "vddb")
    mbn3 = s.nmos("MBN3", x, 560, "left", mos("Lbcn", "Wbcn", 1))
    s.wire(ibcn["-"], mbn3["D"])
    s.wire(mbn3["G"], (976, mbn3["G"][1]), (976, 528), (x, 528))
    s.flag(mbn3["S"], "0"); s.flag(mbn3["B"], "0")
    decouple((x, 528), "RD3", "CD3", "vcn", 1120)
    s.flag((x, 528), "vcnr")
    s.vprobe((1248, 528), "vcn", to=(1312, 528)); s.iprobe((x, 496), "IBCN", to=(x - 64, 496))

    # Vcp: diode-connected PMOS sinking Ibcp = kcp*Ibnp
    x = 1056
    mbp3 = s.pmos("MBP3", x, 880, "left", mos("Lbcp", "Wbcp", 1))
    s.flag(mbp3["S"], "vddb"); s.flag(mbp3["B"], "vddb")
    ibcp = s.isrc("IBCP", x, 1072, "{kcp*Ibnp}")
    s.wire(mbp3["D"], ibcp["+"])
    s.flag(ibcp["-"], "0")
    s.wire(mbp3["G"], (976, mbp3["G"][1]), (976, 1024), (x, 1024))
    decouple((x, 1024), "RD4", "CD4", "vcp", 1120)
    s.flag((x, 1024), "vcpr")
    s.vprobe((1248, 1024), "vcp", to=(1312, 1024)); s.iprobe((x, 1056), "IBCP", to=(x - 64, 1056))
    s.text(912, 1360, "cascode gates (EE4520 fig. 6: Ibcn, Ibcp)", size=1)

    # ======================================================================= Stage 1 (center)
    XA, XB, XC = 2560, 3072, 2816
    s.box(2400, TOP, 3232, BOT, "Stage 1: PMOS-input telescopic cascode")
    m0 = s.pmos("M0", XC, 400, "left", mos("Lt", "Wt", "2*N"))
    s.flag(m0["S"], "vdd"); s.flag(m0["B"], "vdd"); s.flag(m0["G"], "vbp")
    s.wire(m0["D"], (XC, 560))
    s.wire((XA, 560), (XB, 560))                                    # tail
    m1 = s.pmos("M1", XA, 624, "left", mos("Li", "Wi", "N"))
    m2 = s.pmos("M2", XB, 624, "right", mos("Li", "Wi", "N"))
    s.wire((XA, 560), m1["S"]); s.wire((XB, 560), m2["S"])
    s.wire(m1["B"], (XA + 32, m1["B"][1]), (XA + 32, 560))         # bulk = tail
    s.wire(m2["B"], (XB - 32, m2["B"][1]), (XB - 32, 560))
    s.flag(m1["G"], "vip"); s.flag(m2["G"], "vin")
    m3 = s.pmos("M3", XA, 784, "left", mos("Lcp", "Wcp", "N"))
    m4 = s.pmos("M4", XB, 784, "right", mos("Lcp", "Wcp", "N"))
    s.wire(m1["D"], m3["S"]); s.wire(m2["D"], m4["S"])             # a1p, a1n
    for m in (m3, m4):
        s.flag(m["G"], "vcp"); s.flag(m["B"], "vdd")
    m5 = s.nmos("M5", XA, 944, "left", mos("Lcn", "Wcn", "N"))
    m6 = s.nmos("M6", XB, 944, "right", mos("Lcn", "Wcn", "N"))
    s.wire(m3["D"], m5["D"]); s.wire(m4["D"], m6["D"])             # x1p, x1n
    for m in (m5, m6):
        s.flag(m["G"], "vcn"); s.flag(m["B"], "0")
    m7 = s.nmos("M7", XA, 1104, "left", mos("Ll", "Wl", "N-Ncm"))
    m8 = s.nmos("M8", XB, 1104, "right", mos("Ll", "Wl", "N-Ncm"))
    m7c = s.nmos("M7C", XA + 176, 1104, "left", mos("Ll", "Wl", "Ncm"))
    m8c = s.nmos("M8C", XB - 176, 1104, "right", mos("Ll", "Wl", "Ncm"))
    s.wire(m5["S"], m7["D"]); s.wire(m6["S"], m8["D"])             # b1p, b1n
    s.wire(m7c["D"], (XA + 176, 1072), (XA, 1072))
    s.wire(m8c["D"], (XB - 176, 1072), (XB, 1072))
    for m in (m7, m8, m7c, m8c):
        s.flag(m["S"], "0"); s.flag(m["B"], "0")
    s.flag(m7["G"], "vbn"); s.flag(m8["G"], "vbn")
    s.flag(m7c["G"], "vcmfb"); s.flag(m8c["G"], "vcmfb")
    s.text(XA + 48, 1344, "loads: N-Ncm units on vbn (replica), Ncm units on the CMFB line", size=1)
    # node-name tags on nets that are already wired (they make the report's D2/D3 values traceable)
    for pt, nm in (((XC, 560), "tail"), ((XA, 752), "a1p"), ((XB, 752), "a1n"), ((XA, 912), "x1p"),
                   ((XB, 912), "x1n"), ((XA, 1072), "b1p"), ((XB, 1072), "b1n")):
        s.flag(pt, nm)
    s.vprobe((2688, 560), "tail")
    s.vprobe((2480, 640), "vip", to=(2480, 592)); s.vprobe((3152, 640), "vin", to=(3152, 592))
    s.vprobe((XA, 752), "a1p", to=(XA - 96, 752)); s.vprobe((XB, 752), "a1n", to=(XB + 96, 752))
    s.vprobe((2480, 912), "x1p"); s.vprobe((3152, 912), "x1n")
    s.vprobe((2672, 1072), "b1p"); s.vprobe((2960, 1072), "b1n")
    s.iprobe((XC, 528), "M0", to=(XC + 64, 528))                                    # tail
    s.iprobe((XA, 736), "M1", to=(XA + 64, 736)); s.iprobe((XB, 736), "M2", to=(XB - 64, 736))   # M1 = M3 = M5
    s.iprobe((XA, 1224), "M7", to=(XA - 64, 1224)); s.iprobe((XB, 1224), "M8", to=(XB + 64, 1224))
    s.iprobe((XA + 176, 1088), "M7C", to=(XA + 144, 1088)); s.iprobe((XB - 176, 1088), "M8C", to=(XB - 144, 1088))

    # ======================================================================= Stage 2 + compensation (both sides)
    def out_stage(side):
        sgn = -1 if side == "p" else 1
        X1 = XA if side == "p" else XB
        XO = X1 + sgn * 560                       # output spine
        XL = X1 + sgn * 336                       # x1 / level-shift column
        XR = X1 + sgn * 448                       # Rb column
        k = "1" if side == "p" else "2"
        out, x1 = ("vop", "x1p") if side == "p" else ("von", "x1n")
        mn, mp = ("M9", "M11") if side == "p" else ("M10", "M12")
        gside = "right" if side == "p" else "left"
        bx1, bx2 = (XO - 112, X1 - 176) if side == "p" else (X1 + 176, XO + 112)
        s.box(bx1, TOP, bx2, BOT, f"Stage 2 ({out}) + Cc, Rz")
        mpd = s.pmos(mp, XO, 400, gside, mos("Lt", "Wt", "M2"))
        mnd = s.nmos(mn, XO, 1104, gside, "l={Ld} w={Wd*M2/20} m={Md}")
        s.flag(mpd["S"], "vdd"); s.flag(mpd["B"], "vdd"); s.flag(mnd["S"], "0"); s.flag(mnd["B"], "0")
        s.wire(mpd["D"], mnd["D"])                # output node
        s.flag((XO, 800), out)
        # level shift: Cls from x1 to the PMOS gate, Rb from the gate to vbp
        cls = s.cap_v(f"CLS{k}", XL, 560, "{Cls}")
        rb = s.res_v(f"RB{k}", XR, mpd["G"][1], "{Rb}")
        s.wire(mpd["G"], rb["A"], (XL, mpd["G"][1]), cls["A"])
        s.flag(rb["B"], "vbp")
        s.wire(cls["B"], (XL, 912), (X1, 912))   # x1 bus into stage 1
        s.wire((XL, 912), (XL, mnd["G"][1]), mnd["G"])
        # Miller compensation: x1 - Cc - Rz - output
        yc = 1024
        if side == "p":
            rz = s.res_h(f"RZ{k}", XO + 32, yc, "{Rz}")
            cc = s.cap_h(f"CC{k}", XO + 128, yc, "{Cc}")
            s.wire((XO, yc), rz["B"]); s.wire(rz["A"], cc["B"]); s.wire(cc["A"], (XL, yc))
            s.flag(rz["A"], "zp")
        else:
            cc = s.cap_h(f"CC{k}", XL + 32, yc, "{Cc}")
            rz = s.res_h(f"RZ{k}", XL + 112, yc, "{Rz}")
            s.wire((XL, yc), cc["B"]); s.wire(cc["A"], rz["B"]); s.wire(rz["A"], (XO, yc))
            s.flag(cc["A"], "zn")
        s.flag((XL, mpd["G"][1]), f"gp{k}")
        s.vprobe((XL, 480), f"gp{k}", to=(XL - sgn * 64, 480))
        s.vprobe((XO, 800), out, to=(XO - sgn * 64, 800))
        zx = (rz["A"][0] + cc["B"][0]) // 2 if side == "p" else (cc["A"][0] + rz["B"][0]) // 2
        s.vprobe((zx, yc), "zp" if side == "p" else "zn", to=(zx, yc + 64))
        s.iprobe((XO, 704), mp, to=(XO - sgn * 64, 704))

    out_stage("p")
    out_stage("n")

    # ======================================================================= CMFB (right)
    X0 = 3872
    s.box(X0, TOP, X0 + 1040, BOT, "CMFB (continuous time, on Vdd)")
    r1 = s.res_h("RCM1", X0 + 96, 480, "{Rcm}")
    r2 = s.res_h("RCM2", X0 + 96, 640, "{Rcm}")
    c1 = s.cap_h("CCM1", X0 + 96, 400, "{Ccm}")
    c2 = s.cap_h("CCM2", X0 + 96, 720, "{Ccm}")
    xs = X0 + 304                               # vcms column
    s.wire(r1["B"], (X0 + 64, 480)); s.wire(c1["B"], (X0 + 64, 400), (X0 + 64, 480))
    s.wire(r2["B"], (X0 + 64, 640)); s.wire(c2["B"], (X0 + 64, 720), (X0 + 64, 640))
    s.flag((X0 + 64, 480), "vop"); s.flag((X0 + 64, 640), "von")
    s.wire(c1["A"], (xs, 400), (xs, 720), c2["A"])
    s.wire(r1["A"], (xs, 480)); s.wire(r2["A"], (xs, 640))
    xp1, xp2 = X0 + 512, X0 + 800
    xm = (xp1 + xp2) // 2
    mc0 = s.pmos("MC0", xm, 400, "left", mos("Lt", "Wt", "Mcmt"))
    s.flag(mc0["S"], "vdd"); s.flag(mc0["B"], "vdd"); s.flag(mc0["G"], "vbp")
    s.wire(mc0["D"], (xm, 576))
    s.wire((xp1, 576), (xp2, 576))              # cmt
    mc1 = s.pmos("MC1", xp1, 640, "left", mos("Lcm", "Wcm", 1))
    mc2 = s.pmos("MC2", xp2, 640, "right", mos("Lcm", "Wcm", 1))
    s.wire((xp1, 576), mc1["S"]); s.wire((xp2, 576), mc2["S"])
    s.flag(mc1["B"], "vdd"); s.flag(mc2["B"], "vdd")
    s.wire((xs, 560), (xs + 64, 560), (xs + 64, mc1["G"][1]), mc1["G"])   # vcms -> MC1 gate
    s.flag(mc2["G"], "vcmr")
    mc3 = s.nmos("MC3", xp1, 960, "right", mos("Ll", "Wl", 1))
    mc4 = s.nmos("MC4", xp2, 960, "left", mos("Ll", "Wl", 1))
    s.wire(mc1["D"], mc3["D"]); s.wire(mc2["D"], mc4["D"])
    s.wire(mc3["G"], (xp1 + 80, mc3["G"][1]), (xp1 + 80, 896), (xp1, 896))   # diode
    s.wire(mc4["G"], (xp2 - 80, mc4["G"][1]), (xp2 - 80, 896), (xp2, 896))
    for m in (mc3, mc4):
        s.flag(m["S"], "0"); s.flag(m["B"], "0")
    s.wire((xp1, 896), (xp1 - 192, 896))
    s.flag((xp1 - 192, 896), "vcmfb")
    s.flag((xs, 560), "vcms"); s.flag((xm, 576), "cmt"); s.flag((xp2, 896), "cmd")
    s.vprobe((xs + 64, 608), "vcms", to=(xs + 128, 608)); s.vprobe((xm + 72, 576), "cmt")
    s.vprobe((xp2 - 56, 896), "cmd"); s.vprobe((xp1 - 104, 896), "vcmfb")
    s.vprobe((mc0["G"][0] - 32, mc0["G"][1]), "vbp", to=(mc0["G"][0] - 32, mc0["G"][1] - 64))
    s.vprobe((mc2["G"][0] + 32, mc2["G"][1]), "vcmr", to=(mc2["G"][0] + 32, mc2["G"][1] - 64))
    s.iprobe((xm, 528), "MC0", to=(xm + 64, 528))
    s.iprobe((xp1, 800), "MC1", to=(xp1 - 64, 800)); s.iprobe((xp2, 800), "MC2", to=(xp2 + 64, 800))

    # ======================================================================= Test bench (left, bottom)
    s.box(0, 1712, 2240, 2640, "Fixed test bench (Cin/Cfb = 4, Cload = Cin)")
    for i, (ref, val, net) in enumerate([("Vdd", "{VDD}", "vdd"), ("Vddb", "{VDD}", "vddb"), ("Vcmr", "{VCM}", "vcmr")]):
        v = s.vsrc(ref, 128 + i * 160, 1856, val)
        s.flag(v["+"], net); s.flag(v["-"], "0")
    vinp = s.vsrc("Vinp", 608, 2032, "PULSE({VCMI} {VCMI+VinStep/2} {tstep} {trise} {trise} 1 2)", "AC 0.5")
    vinn = s.vsrc("Vinn", 608, 2416, "PULSE({VCMI} {VCMI-VinStep/2} {tstep} {trise} {trise} 1 2)", "AC -0.5")
    s.flag(vinp["-"], "0"); s.flag(vinn["-"], "0")
    for k, (src, sn, out) in enumerate([(vinp, "vin", "vop"), (vinn, "vip", "von")]):
        y0 = 1904 + k * 384
        n = str(k + 1)
        cin = s.cap_h(f"Cin{n}", 800, y0, "{Cin}")
        rin = s.res_h(f"Rin{n}", 784, y0 + 96, "{Rin} noiseless")
        cfb = s.cap_h(f"Cfb{n}", 1216, y0, "{Cfb}")
        rfb = s.res_h(f"Rfb{n}", 1200, y0 + 96, "{Rfb} noiseless")
        cl = s.cap_v(f"Cload{n}", 1520, y0 + 32, "{Cload}")
        s.wire(src["+"], (src["+"][0], y0), (720, y0), cin["B"])
        s.wire((720, y0), (720, y0 + 96), rin["B"])
        s.flag((720, y0), "inp" if k == 0 else "inn")
        s.wire(cin["A"], (1008, y0), cfb["B"]); s.wire(rin["A"], (1008, y0 + 96), (1008, y0))
        s.wire(rfb["B"], (1136, y0 + 96), (1136, y0))
        s.flag((1008, y0), sn)
        s.wire(cfb["A"], (1520, y0), cl["A"]); s.wire(rfb["A"], (1360, y0 + 96), (1360, y0))
        s.flag(cl["B"], "0"); s.flag((1520, y0), out)

    # ======================================================================= directives box
    dirs = [".lib 'log018.l' TT"]  # portable: design/final/log018.l sits next to the schematics
    bench = WORK / ("bench_tran.cir" if analysis == "tran" else "bench_noise.cir")
    tran_params = params(WORK / "bench_tran.cir")
    if analysis == "noise":  # only what the noise sheet uses (the input sources need tstep, trise, VinStep)
        tran_params = [re.sub(r"\s+(Tsettle|tstop)=(\{[^}]*\}|\S+)", "", l) for l in tran_params]
    dirs += tran_params
    dirs += params(WORK / "amp.inc")
    keep = (".tran", ".option", ".meas") if analysis == "tran" else (".noise", ".meas")
    for line in bench.read_text().splitlines():
        if line.strip().lower().startswith(keep):
            dirs.append(line.strip())
    if figure:  # .op data labels need the operating point that a transient run writes; no measurements
        dirs = [".tran 0 1n 0 10p" if d.lower().startswith(".tran") else d for d in dirs
                if not d.lower().startswith(".meas")]
    y = 1808
    for d in dirs:
        s.text(2432, y, d, directive=True)
        y += 40
    s.box(2400, 1712, 4912, y + 32, "Parameters, Simulations & Measurements")
    return s.render(h=max(2700, y + 100), figure=figure)


def main():
    import sys

    if sys.argv[1:2] == ["--figures"]:  # report D2/D3 copies with .op data labels (tools/ltgui.py uses these)
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for fig, name in (("v", "amp_d2.asc"), ("i", "amp_d3.asc")):
            (out / name).write_text(build("tran", figure=fig))
            print("wrote", out / name)
        return
    FINAL.mkdir(parents=True, exist_ok=True)
    for a, name in (("tran", "amp_tran.asc"), ("noise", "amp_noise.asc")):
        (FINAL / name).write_text(build(a))
        print("wrote", FINAL / name)


if __name__ == "__main__":
    main()
