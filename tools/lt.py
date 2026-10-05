#!/usr/bin/env python3
"""LTspice XVII (Wine) batch runner: run, parse .meas / .op, parallel param sweeps.

CLI (run from the repo root with `uv run`):
  uv run tools/lt.py run  FILE.asc|.net|.cir [--op] [--json OUT] [--keep-raw]
  uv run tools/lt.py op   FILE                 # device table: Id, Vds, Vdsat, margin, gm/Id, Cgg
  uv run tools/lt.py sweep FILE --set Wn=50u,58u --set Cc=600f,720f [-j 16] [--csv OUT]
  uv run tools/lt.py netlist FILE.asc          # .asc -> .net only

Output is compact by design: never print raw waveforms into the agent context.
Library use: `from lt import run, sweep, op_table` (tools/ is on sys.path when run as script).
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LTSPICE_EXE = os.environ.get(
    "LTSPICE_EXE",
    str(Path.home() / ".wine/drive_c/Program Files/LTC/LTspiceXVII/XVIIx64.exe"),
)
XVII_LIB = r"C:\Program Files\LTC\LTspiceXVII\lib\cmp\log018.l"
DISPLAY_NUM = os.environ.get("EE4525_XVFB", "87")
REPO = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------------- display


def ensure_display() -> str:
    """Return a usable X display for Wine. Starts one shared Xvfb (:87) if needed.

    LTspice under Wine silently writes no output without a display, even in -b mode.
    One persistent Xvfb lets many parallel runs share it (8 runs in about 6 s).
    """
    if os.environ.get("EE4525_DISPLAY"):
        return os.environ["EE4525_DISPLAY"]
    lock = Path(f"/tmp/.X{DISPLAY_NUM}-lock")
    if lock.exists():
        try:
            pid = int(lock.read_text().strip())
            os.kill(pid, 0)
            return f":{DISPLAY_NUM}"
        except (ValueError, ProcessLookupError, PermissionError):
            lock.unlink(missing_ok=True)
    subprocess.Popen(
        ["Xvfb", f":{DISPLAY_NUM}", "-screen", "0", "1024x768x24", "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(50):
        if lock.exists():
            break
        time.sleep(0.1)
    return f":{DISPLAY_NUM}"


def _wine(args: list[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess:
    env = {**os.environ, "DISPLAY": ensure_display(), "WINEDEBUG": "-all"}
    return subprocess.run(
        ["wine", LTSPICE_EXE, *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def winpath(p: Path) -> str:
    return "Z:" + str(p.resolve()).replace("/", "\\")


# ----------------------------------------------------------------------------- netlists


def read_text(p: Path) -> str:
    """Read an LTspice text file that may be UTF-16 (XVII error logs) or ASCII."""
    b = p.read_bytes()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff") or (len(b) > 4 and b[1:2] == b"\x00" and b[3:4] == b"\x00"):
        return b.decode("utf-16", errors="replace")
    return b.decode("latin-1", errors="replace")


def fix_netlist(text: str) -> str:
    """Make a netlist run on this machine's LTspice XVII.

    - LTspice 24 (ADI) model path -> XVII path; double-quoted .lib path -> single quotes
      (XVII mis-parses `.lib "path" TT`).
    - drop LTspice-24-only `.options logopinfo`.
    """
    out = []
    for line in text.splitlines():
        low = line.lower()
        if low.startswith(".lib") and "log018" in low:
            m = re.match(r'(?i)\.lib\s+["\']?(.*?log018\.l)["\']?\s+(\w+)\s*$', line.strip())
            if m:
                line = f".lib '{XVII_LIB}' {m.group(2)}"
        if low.startswith((".option", ".options")) and "logopinfo" in low:
            line = re.sub(r"(?i)\s*logopinfo", "", line)
            if line.strip().lower() in (".option", ".options"):
                continue
        out.append(line)
    return "\n".join(out) + "\n"


def inline_includes(text: str, base: Path) -> str:
    """Replace `.include`/`.inc` of local files by their content (sweep copies live elsewhere)."""
    out = []
    for line in text.splitlines():
        m = re.match(r"(?i)^\.inc(?:lude)?\s+[\"']?([^\"']+?)[\"']?\s*$", line.strip())
        if m and (base / m.group(1)).exists():
            inc = base / m.group(1)
            out.append(f"* ---- begin {m.group(1)} ----")
            out.append(inline_includes(read_text(inc), inc.parent).rstrip("\n"))
            out.append(f"* ---- end {m.group(1)} ----")
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def netlist(asc: Path, timeout: float = 60) -> Path:
    asc = asc.resolve()
    proc = _wine(["-netlist", winpath(asc)], asc.parent, timeout)
    net = asc.with_suffix(".net")
    if not net.exists():
        raise RuntimeError(f"netlist failed for {asc}: rc={proc.returncode} {proc.stderr[-400:]}")
    net.write_text(fix_netlist(read_text(net)))
    return net


# ----------------------------------------------------------------------------- parsing

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def parse_meas(log: str) -> tuple[dict[str, float], list[str]]:
    """Parse LTspice .meas lines from a log.

    Formats handled:
      name: expr=VALUE                       (PARAM, AVG, MAX, INTEG ...)
      name: expr=VALUE FROM a TO b
      name: expr=VALUE at T                  (FIND ... AT -> VALUE)
      name: expr=LEVEL AT T                  (WHEN -> T, uppercase AT)
      name=VALUE
    Failed measurements are returned in the second list.
    """
    meas: dict[str, float] = {}
    failed: list[str] = []
    for raw in log.splitlines():
        line = raw.strip()
        m = re.match(r"^Measurement\s+\"?(\w+)\"?\s+FAIL", line, re.I)
        if m:
            failed.append(m.group(1).lower())
            continue
        m = re.match(r"^(\w+):\s.*=(" + _NUM + r")\s+AT\s+(" + _NUM + r")\s*$", line)
        if m:  # WHEN: value is the time
            meas[m.group(1).lower()] = float(m.group(3))
            continue
        m = re.match(r"^(\w+):\s.*?=(" + _NUM + r")(?:\s|$)", line)
        if m:
            meas[m.group(1).lower()] = float(m.group(2))
            continue
        m = re.match(r"^(\w+)=(" + _NUM + r")\s*$", line)
        if m:
            meas[m.group(1).lower()] = float(m.group(2))
    return meas, failed


def op_table(log: str) -> dict[str, dict]:
    """Parse the 'Semiconductor Device Operating Points' table (needs a .op run)."""
    dev: dict[str, dict] = {}
    for block in re.split(r"\nName:", log)[1:]:
        lines = block.splitlines()
        names = lines[0].split()
        cols: dict[str, dict] = {n: {} for n in names}
        for ln in lines[1:]:
            m = re.match(r"\s*([A-Za-z]+):?\s+(.*)", ln)
            if not m or not ln.strip():
                if not ln.strip():
                    break
                continue
            key, vals = m.group(1), m.group(2).split()
            for n, v in zip(names, vals):
                if key == "Model":
                    cols[n]["Model"] = v
                else:
                    try:
                        cols[n][key] = float(v)
                    except ValueError:
                        pass
        dev.update(cols)
    for n, d in dev.items():
        if "Id" in d and "Vds" in d and "Vdsat" in d:
            d["margin"] = abs(d["Vds"]) - abs(d["Vdsat"])
            d["gm_id"] = d.get("Gm", 0.0) / abs(d["Id"]) if d["Id"] else 0.0
            d["Cgg"] = d.get("dQgdVgb", float("nan"))
            d["type"] = "p" if str(d.get("Model", "")).lower().startswith("p") else "n"
    return dev


def log_issues(log: str) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    for line in log.splitlines():
        s = line.strip()
        low = s.lower()
        if any(k in low for k in ("fatal", "error:", "singular matrix", "timestep too small", "convergence failed")):
            errs.append(s)
        elif low.startswith("warning"):
            warns.append(s)
    return errs, warns


# ----------------------------------------------------------------------------- run


def run(path: str | Path, timeout: float = 300, op: bool = False, keep_raw: bool = True) -> dict:
    """Run an .asc/.net/.cir in LTspice XVII batch mode. Returns a compact result dict."""
    path = Path(path).resolve()
    t0 = time.time()
    if path.suffix.lower() == ".asc":
        net = netlist(path)
    else:
        net = path
        net.write_text(fix_netlist(read_text(net)))
    if op:
        net = make_op_netlist(net)
    for ext in (".log", ".raw", ".op.raw"):
        net.with_suffix(ext).unlink(missing_ok=True)
    try:
        proc = _wine(["-b", winpath(net)], net.parent, timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        rc = -1
    logp = net.with_suffix(".log")
    log = read_text(logp) if logp.exists() else ""
    meas, failed = parse_meas(log)
    errs, warns = log_issues(log)
    raw = net.with_suffix(".raw")
    res = {
        "file": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path),
        "net": str(net),
        "ok": rc == 0 and bool(log) and not errs,
        "rc": rc,
        "elapsed_s": round(time.time() - t0, 2),
        "meas": meas,
        "meas_failed": failed,
        "errors": errs[:10],
        "warnings": warns[:10],
        "raw": str(raw) if raw.exists() else None,
        "log": str(logp) if logp.exists() else None,
    }
    if op or "Semiconductor Device Operating Points" in log:
        res["devices"] = op_table(log)
    if not keep_raw and raw.exists():
        raw.unlink()
        res["raw"] = None
    return res


def make_op_netlist(net: Path) -> Path:
    """Copy of a netlist with all analyses replaced by `.op` (prints the device table)."""
    lines = []
    for line in read_text(net).splitlines():
        low = line.strip().lower()
        if low.startswith((".tran", ".ac", ".noise", ".dc", ".meas", ".measure", ".four", ".step")):
            continue
        if low == ".end":
            lines.append(".op")
        lines.append(line)
    out = net.with_name(net.stem + "_op.net")
    out.write_text("\n".join(lines) + "\n")
    return out


# ----------------------------------------------------------------------------- sweeps


def set_params(text: str, values: dict[str, str]) -> str:
    """Override `.param NAME=...` assignments in place; append any not found."""
    remaining = dict(values)
    out = []
    for line in text.splitlines():
        if line.strip().lower().startswith(".param"):
            for name, val in values.items():
                pat = re.compile(r"(?i)(\b" + re.escape(name) + r"\s*=\s*)(\{[^}]*\}|\S+)")
                if pat.search(line):
                    line = pat.sub(lambda m: m.group(1) + str(val), line, count=1)
                    remaining.pop(name, None)
        out.append(line)
    if remaining:
        extra = [f".param {k}={v}" for k, v in remaining.items()]
        idx = next((i for i, l in enumerate(out) if l.strip().lower() == ".end"), len(out))
        out[idx:idx] = extra
    return "\n".join(out) + "\n"


def sweep(path: str | Path, grid: dict[str, list[str]], jobs: int = 12, tag: str | None = None,
          keep_raw: bool = False, timeout: float = 300) -> list[dict]:
    """Cartesian sweep of .param overrides, run in parallel. Each point gets its own folder."""
    path = Path(path).resolve()
    base = netlist(path) if path.suffix.lower() == ".asc" else path
    text = fix_netlist(inline_includes(read_text(base), base.parent))
    tag = tag or f"{path.stem}_{time.strftime('%H%M%S')}"
    root = REPO / "results" / "sweeps" / tag
    root.mkdir(parents=True, exist_ok=True)
    keys = list(grid)
    points = [dict(zip(keys, combo)) for combo in itertools.product(*(grid[k] for k in keys))]

    def one(i_pt):
        i, pt = i_pt
        d = root / f"p{i:04d}"
        d.mkdir(exist_ok=True)
        net = d / f"{path.stem}.net"
        net.write_text(set_params(text, pt))
        r = run(net, timeout=timeout, keep_raw=keep_raw)
        return {"point": pt, **r}

    ensure_display()
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        results = list(ex.map(one, enumerate(points)))
    return results


# ----------------------------------------------------------------------------- printing


def fmt(v: float) -> str:
    if v == 0 or not isinstance(v, (int, float)):
        return str(v)
    a = abs(v)
    return f"{v:.4g}" if 1e-3 <= a < 1e5 else f"{v:.4e}"


def print_op(devs: dict[str, dict], warn_mv: float = 50.0) -> None:
    rows = sorted((n, d) for n, d in devs.items() if "margin" in d)
    print(f"{'device':16s} {'model':7s} {'Id[uA]':>9s} {'Vgs':>7s} {'Vds':>7s} {'Vdsat':>7s} "
          f"{'marg[mV]':>8s} {'gm/Id':>6s} {'gm[mS]':>7s} {'Cgg[fF]':>8s}")
    for n, d in rows:
        flag = ""
        if abs(d["Id"]) < 1e-8:
            flag = "  OFF"
        elif d["margin"] < 0:
            flag = "  TRIODE"
        elif d["margin"] * 1e3 < warn_mv:
            flag = "  low-margin"
        print(f"{n:16s} {str(d.get('Model', '')):7s} {d['Id']*1e6:9.2f} {d.get('Vgs', 0):7.3f} {d['Vds']:7.3f} "
              f"{d['Vdsat']:7.3f} {d['margin']*1e3:8.1f} {d['gm_id']:6.1f} {d.get('Gm', 0)*1e3:7.3f} "
              f"{d['Cgg']*1e15:8.1f}{flag}")
    bad = [n for n, d in rows if d["margin"] < 0 and abs(d["Id"]) > 1e-8]
    print(f"\n{len(rows)} MOSFETs; {len(bad)} not saturated" + (f": {', '.join(bad)}" if bad else ""))


def print_run(r: dict, show_meas: bool = True) -> None:
    status = "OK" if r["ok"] else "FAILED"
    print(f"[{status}] {r['file']}  rc={r['rc']}  {r['elapsed_s']} s")
    for e in r["errors"]:
        print("  ERROR:", e)
    for w in r["warnings"][:5]:
        print("  warn:", w)
    if r["meas_failed"]:
        print("  meas FAILED:", ", ".join(r["meas_failed"]))
    if show_meas and r["meas"]:
        width = max(len(k) for k in r["meas"])
        for k, v in r["meas"].items():
            print(f"  {k:{width}s} = {fmt(v)}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("file")
    p.add_argument("--op", action="store_true", help="replace analyses with .op and print device table")
    p.add_argument("--json", help="write full result JSON here")
    p.add_argument("--keep-raw", action="store_true", default=True)
    p = sub.add_parser("op")
    p.add_argument("file")
    p.add_argument("--warn-mv", type=float, default=50.0)
    p = sub.add_parser("netlist")
    p.add_argument("file")
    p = sub.add_parser("sweep")
    p.add_argument("file")
    p.add_argument("--set", action="append", required=True, help="NAME=v1,v2,...")
    p.add_argument("-j", "--jobs", type=int, default=12)
    p.add_argument("--csv", help="CSV output path (default results/sweeps/<tag>.csv)")
    p.add_argument("--tag")
    p.add_argument("--keep-raw", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "netlist":
        print(netlist(Path(a.file)))
        return 0
    if a.cmd == "run":
        r = run(a.file, op=a.op)
        print_run(r)
        if a.op and r.get("devices"):
            print()
            print_op(r["devices"])
        if a.json:
            Path(a.json).parent.mkdir(parents=True, exist_ok=True)
            Path(a.json).write_text(json.dumps(r, indent=1, default=str))
        return 0 if r["ok"] else 1
    if a.cmd == "op":
        r = run(a.file, op=True)
        print_run(r, show_meas=False)
        if r.get("devices"):
            print_op(r["devices"], a.warn_mv)
        return 0 if r["ok"] else 1
    if a.cmd == "sweep":
        grid = {}
        for s in a.set:
            k, v = s.split("=", 1)
            grid[k] = [x.strip() for x in v.split(",")]
        res = sweep(a.file, grid, jobs=a.jobs, tag=a.tag, keep_raw=a.keep_raw)
        keys = list(grid)
        mkeys = sorted({k for r in res for k in r["meas"]})
        out = Path(a.csv) if a.csv else REPO / "results" / "sweeps" / f"{a.tag or Path(a.file).stem}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(keys + ["ok"] + mkeys)
            for r in res:
                w.writerow([r["point"][k] for k in keys] + [r["ok"]] + [r["meas"].get(k, "") for k in mkeys])
        print(f"{len(res)} points -> {out}")
        show = mkeys[:8]
        print("  ".join(f"{k:>10s}" for k in keys + show))
        for r in res:
            vals = [r["point"][k] for k in keys] + [fmt(r["meas"].get(k, float("nan"))) for k in show]
            print("  ".join(f"{str(v):>10s}" for v in vals) + ("" if r["ok"] else "  FAILED"))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
