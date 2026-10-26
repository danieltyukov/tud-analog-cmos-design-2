#!/usr/bin/env python3
"""Run a deliverable schematic in the LTspice XVII GUI (Wine) and capture LTspice's own waveform window.

The simulation runs inside the real LTspice application (`XVIIx64.exe -Run file.asc`), the traces, axes
and annotations are set with an LTspice plot-settings file (.plt, the format of Plot Settings => Save Plot
Settings), and the figure is a screenshot of LTspice's waveform viewer. Every number written on a plot is
read from the .meas lines LTspice prints in the .log of that same GUI run, and is cross-checked against
results/latest.json (tools/evaluate.py) so the report and the picture cannot disagree.

CLI (run from the repo root with `uv run`):
  uv run tools/ltgui.py d4 [--asc design/final/amp_tran.asc] [--out report/figures/d4_ltspice.png]
  uv run tools/ltgui.py d5 [--asc design/final/amp_noise.asc] [--out report/figures/d5_ltspice.png]
  uv run tools/ltgui.py all          # d4 and d5 into report/figures

Run files are kept in results/ltgui/<figure>/ (the .asc copy, log018.l, the .plt, the LTspice .log and
.raw, the raw screenshot). The user's own LTspice settings are not touched: the GUI runs with a private
.ini (`-ini plot.ini`, white plot background, larger font) on a private Xvfb display.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lt  # noqa: E402

REPO = lt.REPO
FINAL = REPO / "design" / "final"
OUTDIR = REPO / "results" / "ltgui"
FIGDIR = REPO / "report" / "figures"
XVFB_BASE = int(os.environ.get("EE4525_GUI_XVFB", "150"))

# screen and fonts: the screenshot is scaled to the text width (about 6.3 in), so the font is chosen
# for about 7 pt there
SCREEN = (2000, 1250)
FONT_PX = 30
PEN_PX = 3

# LTspice colours are 0x00BBGGRR. WaveColor0 = plot background, 1 = axes and text, 2.. = trace colours;
# a trace code is 0x80000 + colour index.
COLORS = {
    "WaveColor0": 0xFFFFFF, "WaveColor1": 0x000000, "Grid": 0xC8C8C8, "InActiveAxis": 0x808080,
    "WaveColor2": 0x0000E0,  # red    (A)
    "WaveColor3": 0xD00000,  # blue   (Abeta, onoise)
    "WaveColor4": 0x000000,  # black  (markers)
    "WaveColor5": 0x008000,  # green
    "WaveColor6": 0x808080,  # grey
    "WaveColor7": 0x0080FF,  # orange
}
RED, BLUE, BLACK, GREEN, GREY, ORANGE = 2, 3, 4, 5, 6, 7
CROP = (6, 90)  # left and top edge of the maximised waveform window on the screen


def trace(color: int, expr: str) -> str:
    return f'{{{0x80000 + color},0,"{expr}"}}'


# ----------------------------------------------------------------------------- display and processes


def start_display() -> tuple[str, subprocess.Popen]:
    """A private Xvfb (user-owned lock, see lt._display_state) sized for the figure."""
    for n in range(XVFB_BASE, XVFB_BASE + 30):
        if lt._display_state(n) != "free":
            continue
        p = subprocess.Popen(
            ["Xvfb", f":{n}", "-screen", "0", f"{SCREEN[0]}x{SCREEN[1]}x24", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
        )
        for _ in range(50):
            if lt._display_state(n) == "ours":
                return f":{n}", p
            time.sleep(0.1)
        p.kill()
    raise SystemExit(f"no free X display in :{XVFB_BASE}..:{XVFB_BASE + 29}")


def pids_on_display(display: str) -> list[int]:
    """Processes of this user whose environment has DISPLAY=<display> (our LTspice and its Wine helpers)."""
    want = f"DISPLAY={display}\0".encode()
    out = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit() or int(d.name) == os.getpid():
            continue
        try:
            if d.stat().st_uid != os.getuid():
                continue
            if want in (d / "environ").read_bytes():
                out.append(int(d.name))
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            continue
    return out


def stop(display: str, xvfb: subprocess.Popen) -> None:
    for pid in pids_on_display(display):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    xvfb.terminate()
    try:
        xvfb.wait(5)
    except subprocess.TimeoutExpired:
        xvfb.kill()


def xdo(display: str, *args: str) -> str:
    r = subprocess.run(["xdotool", *args], env={**os.environ, "DISPLAY": display},
                       capture_output=True, text=True, timeout=20)
    return r.stdout.strip()


def screenshot(display: str, path: Path) -> None:
    subprocess.run(["import", "-window", "root", str(path)], env={**os.environ, "DISPLAY": display},
                   check=True, timeout=30)


# ----------------------------------------------------------------------------- LTspice files


def write_ini(path: Path) -> None:
    """Private LTspice settings for the plot run (LTspice fills every key not listed with its default)."""
    opts = {
        "WindowSize": f"0 {SCREEN[0]} 0 {SCREEN[1]}",
        "WaveformViewerFont": 0, "WaveformViewerFontSize": FONT_PX, "WaveformViewerBoldFont": "true",
        "DataPenWidth": PEN_PX, "PenWidth": PEN_PX, "CursorThickness": 1,
        "EnableWindowTabs": "false", "DefaultTileType": "true", "AutoDeleteRawFiles": 0,
        "ShowSchematicGrid": "false", "BoldSchFont": "true", "SchFontSize": 28, "ShowTitleBox": "true",
        "LastWebUpdateTime": int(time.time()), "LastWebUpdateQuery": int(time.time()),
    }
    lines = ["[Options]"] + [f"{k}={v}" for k, v in opts.items()]
    lines += ["[Colors]"] + [f"{k}={v}" for k, v in COLORS.items()]
    path.write_bytes(("\r\n".join(lines) + "\r\n").encode("latin-1"))


def write_plt(path: Path, section: str, body: list[str]) -> None:
    """Write an LTspice plot-settings file (the layout LTspice itself saves).

    LTspice XVII reads it as ANSI (cp1252; a UTF-16 file gives "Plot setup file syntax Error"), so plot text
    can use µ, ² and ½ but not Greek letters: write "Abeta" and "tau" on the plot.
    """
    text = f"[{section}]\r\n{{\r\n   Npanes: 1\r\n   {{\r\n"
    text += "".join(f"      {b}\r\n" for b in body)
    text += "   }\r\n}\r\n"
    path.write_bytes(text.encode("cp1252"))


def asc_params(asc: Path) -> dict[str, float]:
    """Numeric .param values written on the schematic (for tstep, VoutStep, Cin)."""
    p = {}
    for line in asc.read_text(errors="replace").splitlines():
        if "!.param" not in line:
            continue
        for k, v in re.findall(r"(\w+)=([-+0-9.eE]+[a-zA-Z]*)(?=\s|$)", line.split("!", 1)[1]):
            try:
                p[k.lower()] = lt_num(v)
            except ValueError:
                pass
    return p


def lt_num(s: str) -> float:
    suf = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6, "g": 1e9}
    s = s.lower()
    for k in ("meg", "f", "p", "n", "u", "m", "k", "g"):
        if s.endswith(k) and s[: -len(k)].replace(".", "", 1).replace("e", "", 1).lstrip("+-").isdigit():
            return float(s[: -len(k)]) * suf[k]
    return float(s)


# ----------------------------------------------------------------------------- one GUI run


def gui_run(asc: Path, name: str, section: str, plt_body, crop: bool = True, actions=None, compose=None) -> dict:
    """Simulate `asc` in the LTspice GUI, then load the plot settings built from its own .log and capture.

    plt_body(meas, logtext, params) -> list of .plt body lines. actions(display, work) runs after the clean
    screenshot and returns {"allow": [window names it opened], ...}; compose(work, png, info) edits the cropped
    picture. Returns paths and the parsed .meas values.
    """
    asc = lt.guard(asc)
    work = OUTDIR / name
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    shutil.copy2(asc, work / asc.name)
    shutil.copy2(asc.parent / "log018.l", work / "log018.l")
    write_ini(work / "plot.ini")
    stem = asc.stem
    params = asc_params(asc)
    # a first .plt so LTspice opens the waveform window with the traces and enables Reload Plot Settings
    write_plt(work / f"{stem}.plt", section, plt_body({}, "", params))

    display, xvfb = start_display()
    try:
        env = {**os.environ, "DISPLAY": display, "WINEDEBUG": "-all"}
        subprocess.Popen(["wine", lt.LTSPICE_EXE, "-Run", asc.name, "-ini", "plot.ini"], cwd=work, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        log = work / f"{stem}.log"
        t0 = time.time()
        while time.time() - t0 < 180:
            if log.exists() and "elapsed time" in lt.read_text(log):
                break
            time.sleep(0.5)
        else:
            raise SystemExit(f"LTspice GUI run did not finish within 180 s ({work})")
        time.sleep(2.0)  # let the viewer finish drawing
        logtext = lt.read_text(log)
        meas, failed = lt.parse_meas(logtext)
        if failed:
            raise SystemExit(f"LTspice .meas failed in the GUI run: {failed}")
        write_plt(work / f"{stem}.plt", section, plt_body(meas, logtext, params))
        # waveform child (top tiled window): its maximise button (a double-click on the title closes it under Wine)
        xdo(display, "mousemove", str(SCREEN[0] - 39), "104", "click", "1")
        time.sleep(1.0)
        # Plot Settings => Reload Plot Settings (second item from the bottom of the menu)
        xdo(display, "key", "alt+p")
        time.sleep(0.6)
        xdo(display, "key", "Up", "Up", "Return")
        time.sleep(2.5)
        raw_png = work / "screen.png"
        screenshot(display, raw_png)
        info = actions(display, work) if actions else {}
        # any other top-level window is a message box (for example a .plt syntax error): refuse the picture
        names = [xdo(display, "getwindowname", w) for w in xdo(display, "search", "--name", "").split()]
        extra = [n for n in names if n and n != "Default IME" and not n.startswith("LTspice XVII - ")
                 and n not in info.get("allow", [])]
        if extra:
            raise SystemExit(f"LTspice showed a dialog during the plot run: {extra} (see {raw_png})")
    finally:
        stop(display, xvfb)

    out = work / f"{name}.png"
    if crop:
        crop_waveform(raw_png, out)
    else:
        shutil.copy2(raw_png, out)
    if compose:
        compose(work, out, info)
    return {"work": work, "png": out, "meas": meas, "log": logtext, "params": params}


def crop_waveform(src: Path, dst: Path) -> None:
    """Cut the maximised waveform window out of the screen: below the toolbar, above the status bar."""
    from PIL import Image

    im = Image.open(src).convert("RGB")
    w, h = im.size
    im.crop((CROP[0], CROP[1], w - 6, h - 24)).save(dst)


# ----------------------------------------------------------------------------- figures


def latest() -> dict:
    p = REPO / "results" / "latest.json"
    return json.loads(p.read_text()) if p.exists() else {}


def check_close(label: str, a: float, b: float, tol: float) -> None:
    if not (math.isfinite(a) and math.isfinite(b)) or abs(a - b) > tol:
        raise SystemExit(f"{label}: LTspice GUI run {a:.6g} vs evaluate.py {b:.6g} (tolerance {tol})")


def d4_body(meas: dict, logtext: str, p: dict) -> list[str]:
    """D4: A (red, from the virtual-ground error) and Abeta (blue, from the output error) after the step."""
    vstep, tstep = p.get("voutstep", 1.2), p.get("tstep", 10e-9)
    vs = f"{vstep:g}"
    a = f"20*log10({vs}/(abs(V(vip,vin))+1n))"
    ab = f"20*log10({vs}/(abs({vs}-V(von,vop))+1n))"
    # the axis goes below 0 dB: Abeta starts at 0 dB and first dips slightly (feedthrough through Cfb)
    tmax, ymin, ymax = 70e-9, -20, 140
    body = [
        f"traces: 2 {trace(RED, a)} {trace(BLUE, ab)}",
        f'Parametric: "time-{tstep * 1e9:g}n"',
        f"X: ('n',0,0,1e-008,{tmax:g})",
        f"Y[0]: (' ',0,{ymin},20,{ymax})",
        "Y[1]: ('_',0,1e+308,0,-1e+308)",
        f"Units: \"\" (' ',0,0,0,{ymin},20,{ymax})",
        "Log: 0 0 0",
        "GridStyle: 1",
    ]
    if not meas:
        return body
    ns = 1e-9
    t30, t386 = meas["t30_step"], meas["t38p6_step"]
    body += [
        # deadline and specifications
        f'Line: "" {BLACK} 1 ({25 * ns:g},{ymin}) ({25 * ns:g},{ymax})',
        f'Text: "" {BLACK} ({22.5 * ns:g},{ymax - 6}) ;25 ns',
        f'Text: "" {BLACK} ({5.5 * ns:g},{ymax - 6}) ;accuracy [dB]',
        f'Line: "" {RED} 2 (0,78) ({tmax:g},78)',
        f'Text: "" {RED} ({6 * ns:g},82) ;A spec 78 dB',
        f'Line: "" {BLUE} 2 (0,66) ({tmax:g},66)',
        f'Text: "" {BLUE} ({7.5 * ns:g},70) ;Abeta spec 66 dB',
        # T30dB and T38.6dB on the Abeta curve
        f'Line: "" {BLACK} 2 (0,30) ({t30:g},30)',
        f'Line: "" {BLACK} 2 ({t30:g},0) ({t30:g},30)',
        f'Line: "" {BLACK} 2 (0,38.6) ({t386:g},38.6)',
        f'Line: "" {BLACK} 2 ({t386:g},0) ({t386:g},38.6)',
        f'Text: "" {BLACK} ({t30 - 3.1 * ns:g},4) ;T30',
        f'Text: "" {BLACK} ({t386 + 2.2 * ns:g},4) ;T38.6',
        # both curves at 25 ns
        f'Circle: "" {RED} 0 ({24.2 * ns:g},{meas["a25"] - 4.5:g}) ({25.8 * ns:g},{meas["a25"] + 4.5:g})',
        f'Circle: "" {BLUE} 0 ({24.2 * ns:g},{meas["ab25"] - 4.5:g}) ({25.8 * ns:g},{meas["ab25"] + 4.5:g})',
    ]
    x = latest().get("extra", {})
    if x:  # the A - Abeta gap right after the step (tools/evaluate.py on the same LTspice data)
        gap, ideal = x["gap_dB"], -20 * math.log10(x["beta_ideal"])
        body += [
            f'Line: "" {BLACK} 0 ({0.8 * ns:g},0) ({0.8 * ns:g},{gap:.3f})',
            f'Text: "" {BLACK} ({10.5 * ns:g},-7) ;gap = 20log10(1/beta_act)',
            f'Text: "" {BLACK} ({10.5 * ns:g},-15) ;= {gap:.2f} dB (ideal {ideal:.2f} dB)',
        ]
    body += [
        # values printed by LTspice (.meas in the .log of this run); LTspice centres text on its anchor
        f'Text: "" {BLACK} ({47 * ns:g},52) ;values from LTspice .meas (this run):',
        f'Text: "" {BLACK} ({47 * ns:g},44) ;T30dB = {t30 / ns:.2f} ns, T38.6dB = {t386 / ns:.2f} ns',
        f'Text: "" {BLACK} ({47 * ns:g},36) ;tau = T38.6dB - T30dB = {meas["tau"] / ns:.3f} ns',
        f'Text: "" {BLACK} ({47 * ns:g},28) ;at 25 ns: A = {meas["a25"]:.2f} dB, Abeta = {meas["ab25"]:.2f} dB',
        f'Text: "" {BLACK} ({47 * ns:g},20) ;P = 1.8 V x avg I(Vdd) = {meas["p_mw"]:.4f} mW',
    ]
    return body


def d5_body(meas: dict, logtext: str, p: dict) -> list[str]:
    """D5: differential output noise density V(onoise), with the integrals LTspice prints."""
    body = [
        f"traces: 1 {trace(BLUE, 'V(onoise)')}",
        "X: ('G',0,10000,0,1e+011)",
        "Y[0]: ('_',0,1e-012,0,1e-006)",
        "Y[1]: ('_',0,1e+308,0,-1e+308)",
        "Units: \"V/Hz\xbd\" ('_',1,0,0,1e-012,0,1e-006)",
        "Log: 1 1 0",
        "GridStyle: 1",
    ]
    if not meas:
        return body
    uv = 1e6
    vs = p.get("voutstep", 1.2)
    body += [
        'Text: "" 4 (4e6,9e-10) ;values from LTspice .meas (this run):',
        f'Text: "" 4 (4e6,4.4e-10) ;Vn_amp = INTEG V(onoise) = {meas["vn_amp"] * uv:.2f} \xb5V rms',
        f'Text: "" 4 (4e6,2.1e-10) ;Vn_kTC = sqrt(42 kT/Cin) = {meas["vn_ktc"] * uv:.2f} \xb5V rms',
        f'Text: "" 4 (4e6,1.02e-10) ;Vn_tot = sqrt(Vn_amp\xb2 + Vn_kTC\xb2) = {meas["vn_tot"] * uv:.2f} \xb5V rms',
        f'Text: "" 4 (4e6,5e-11) ;SNR = 20 log10(({vs:g} V/sqrt2)/Vn_tot) = {meas["snr_db"]:.2f} dB',
    ]
    return body


def d5_integrate(display: str, work: Path) -> dict:
    """Ctrl-click on the trace label: LTspice integrates V(onoise) over the displayed 10 kHz to 100 GHz."""
    xdo(display, "mousemove", str(LABEL_XY[0]), str(LABEL_XY[1]))
    time.sleep(0.3)
    xdo(display, "keydown", "ctrl")
    xdo(display, "click", "1")
    xdo(display, "keyup", "ctrl")
    time.sleep(1.5)
    wid = xdo(display, "search", "--name", "^V\\(onoise\\)$").split()
    if not wid:
        raise SystemExit("LTspice did not open the integration readout for V(onoise)")
    geo = xdo(display, "getwindowgeometry", wid[0])
    pos = re.search(r"Position: (\d+),(\d+)", geo)
    size = re.search(r"Geometry: (\d+)x(\d+)", geo)
    x0, y0, w, h = int(pos[1]), int(pos[2]), int(size[1]), int(size[2])
    shot = work / "screen_integrate.png"
    screenshot(display, shot)
    return {"allow": ["V(onoise)"], "dialog": (x0, y0, w, h), "shot": shot}


def d5_inset(work: Path, png: Path, info: dict) -> None:
    """Paste LTspice's integration readout, enlarged, into the empty lower left of the plot (with a frame)."""
    from PIL import Image, ImageDraw

    x0, y0, w, h = info["dialog"]
    box = Image.open(info["shot"]).convert("RGB").crop((x0, y0, x0 + w, y0 + h))
    box = box.resize((int(w * INSET_SCALE), int(h * INSET_SCALE)), Image.LANCZOS)
    im = Image.open(png).convert("RGB")
    at = (INSET_AT[0], im.size[1] - INSET_AT[1] - box.size[1])
    im.paste(box, at)
    ImageDraw.Draw(im).rectangle((at[0] - 2, at[1] - 2, at[0] + box.size[0] + 1, at[1] + box.size[1] + 1),
                                 outline=(0, 0, 0), width=3)
    im.save(png)
    box.save(work / "integration_readout.png")


LABEL_XY = (1096, 112)   # the V(onoise) trace label on the screen (2000 x 1250)
INSET_SCALE = 2.8
INSET_AT = (300, 88)     # inset position: from the left edge and above the bottom edge of the cropped plot


def make_d4(asc: Path, out: Path) -> dict:
    r = gui_run(asc, "d4", "Transient Analysis", d4_body)
    m, L = r["meas"], latest().get("table")
    if L:
        row = {x["item"]: x["achieved"] for x in L}
        check_close("A at 25 ns", m["a25"], row[3], 0.02)
        check_close("A-beta at 25 ns", m["ab25"], row[2], 0.02)
        check_close("T30dB [ns]", m["t30_step"] * 1e9, row[5], 0.002)
        check_close("T38.6dB [ns]", m["t38p6_step"] * 1e9, row[6], 0.002)
        check_close("tau [ns]", m["tau"] * 1e9, row[7], 0.002)
        check_close("power [mW]", m["p_mw"], row[8], 0.0005)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(r["png"], out)
    return r


def make_d5(asc: Path, out: Path) -> dict:
    r = gui_run(asc, "d5", "Noise Spectral Density - (V/Hz\xbd or A/Hz\xbd)", d5_body,
                actions=d5_integrate, compose=d5_inset)
    L = latest().get("table")
    if L:
        row = {x["item"]: x["achieved"] for x in L}
        m = r["meas"]
        check_close("amplifier noise [uV]", m["vn_amp"] * 1e6, row[11], 0.02)
        check_close("kT/C noise [uV]", m["vn_ktc"] * 1e6, row[10], 0.02)
        check_close("total noise [uV]", m["vn_tot"] * 1e6, row[12], 0.02)
        check_close("SNR [dB]", m["snr_db"], row[1], 0.005)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(r["png"], out)
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["d4", "d5", "all"])
    ap.add_argument("--asc", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    todo = ["d4", "d5"] if a.what == "all" else [a.what]
    for w in todo:
        if w == "d4":
            r = make_d4(a.asc or FINAL / "amp_tran.asc", a.out or FIGDIR / "d4_ltspice.png")
            m = r["meas"]
            print(f"d4: A25 {m['a25']:.2f} dB  Ab25 {m['ab25']:.2f} dB  T30 {m['t30_step'] * 1e9:.3f} ns  "
                  f"T38.6 {m['t38p6_step'] * 1e9:.3f} ns  tau {m['tau'] * 1e9:.3f} ns  P {m['p_mw']:.4f} mW  -> {r['png']}")
        else:
            r = make_d5(a.asc or FINAL / "amp_noise.asc", a.out or FIGDIR / "d5_ltspice.png")
            m = r["meas"]
            print(f"d5: Vn_amp {m['vn_amp'] * 1e6:.2f} uV  kT/C {m['vn_ktc'] * 1e6:.2f} uV  "
                  f"total {m['vn_tot'] * 1e6:.2f} uV  SNR {m['snr_db']:.2f} dB  -> {r['png']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
