#!/usr/bin/env python3
"""Build, render and check the report (fixed paths, so it can run auto-approved).

  uv run tools/report.py build            # latexmk in report/ -> report/main.pdf
  uv run tools/report.py pages [--dpi 80]  # page PNGs -> results/pages/p-<n>.png (then Read them)
  uv run tools/report.py info             # page count, LaTeX warnings, unresolved ?? and TODO
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPORT = REPO / "report"
PDF = REPORT / "main.pdf"
PAGES = REPO / "results" / "pages"


def build() -> int:
    r = subprocess.run(["latexmk", "main.tex"], cwd=REPORT, capture_output=True, text=True)
    log = REPORT / "build" / "main.log"
    if r.returncode != 0:
        tail = log.read_text(errors="replace").splitlines()[-30:] if log.exists() else r.stdout.splitlines()[-30:]
        print("BUILD FAILED\n" + "\n".join(l for l in tail if l.strip()))
        return 1
    print(f"built {PDF.relative_to(REPO)}")
    return info()


def pages(dpi: int) -> int:
    if not PDF.exists():
        print("report/main.pdf missing: run `uv run tools/report.py build`")
        return 1
    shutil.rmtree(PAGES, ignore_errors=True)
    PAGES.mkdir(parents=True)
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(PDF), str(PAGES / "p")], check=True)
    for p in sorted(PAGES.glob("*.png")):
        print(p.relative_to(REPO))
    return 0


def info() -> int:
    if not PDF.exists():
        print("report/main.pdf missing")
        return 1
    meta = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True).stdout
    n = int(re.search(r"Pages:\s+(\d+)", meta).group(1))
    txt = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True, text=True).stdout
    log = REPORT / "build" / "main.log"
    warns = []
    if log.exists():
        warns = [l.strip() for l in log.read_text(errors="replace").splitlines()
                 if re.search(r"Overfull|Underfull \\hbox \(badness 10000|undefined|LaTeX Warning", l)]
    ok = n == 8 and "??" not in txt and not re.search(r"\bTODO\b", txt)
    print(f"pages: {n} (must be 8)")
    n_todo = len(re.findall(r"\bTODO\b", txt))
    print(f"unresolved ??: {txt.count('??')}   TODO: {n_todo}")
    for w in warns[:12]:
        print("  latex:", w)
    print("report:", "OK" if ok else "NOT READY")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    p = sub.add_parser("pages")
    p.add_argument("--dpi", type=int, default=80)
    sub.add_parser("info")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        return build()
    if a.cmd == "pages":
        return pages(max(30, min(a.dpi, 200)))
    return info()


if __name__ == "__main__":
    sys.exit(main())
