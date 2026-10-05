#!/usr/bin/env python3
"""Definition of done for the whole task (fast: reads results, does not simulate).

  uv run tools/check_done.py          # exit 0 = done (or BLOCKED declared in PROGRESS.md)

Done means ALL of:
  1. results/latest.json: all_pass, evaluated on drawn .asc files in design/final/, and their
     current sha256 matches the evaluated one (no stale numbers).
  2. results/robust/latest.json: PASS on the same final tran .asc (same sha).
  3. report/generated/results.tex comes from the same evaluation tag.
  4. report/main.pdf exists, is newer than results/latest.json, has exactly 8 pages, and its text
     contains no unresolved "??" placeholders and no TODO text.
  5. PROGRESS.md was updated after the last evaluation.
Stop-hook escape: a line starting with `BLOCKED:` in the PROGRESS.md "Current state" section
(only for a decision that genuinely needs the user).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def main() -> int:
    todo: list[str] = []
    prog = REPO / "PROGRESS.md"
    state = prog.read_text().split("## Session log")[0] if prog.exists() else ""
    if re.search(r"(?m)^BLOCKED:", state):
        print("BLOCKED declared in PROGRESS.md; stopping is allowed.")
        return 0

    latest = REPO / "results" / "latest.json"
    s = json.loads(latest.read_text()) if latest.exists() else None
    if not s:
        todo.append("no results/latest.json: run tools/evaluate.py on design/final/*.asc")
    else:
        if not s.get("all_pass"):
            fails = [k for k, v in s["checks"].items() if not v]
            todo.append(f"latest evaluation `{s['tag']}` fails: {', '.join(fails)}")
        files = s.get("files", {})
        for f, h in files.items():
            p = Path(f)
            if p.suffix.lower() != ".asc" or "design/final" not in str(p):
                todo.append(f"final evaluation must use the drawn design/final/*.asc, got {p.name}")
            elif not p.exists() or sha(p) != h:
                todo.append(f"{p.name} changed since evaluation `{s['tag']}`: re-run tools/evaluate.py")
        rob = REPO / "results" / "robust" / "latest.json"
        r = json.loads(rob.read_text()) if rob.exists() else None
        tran = next((Path(f) for f in files if "tran" in Path(f).name.lower()), None)
        if not r or not r.get("pass"):
            todo.append("tools/robust.py has not passed on the final transient .asc")
        elif tran and (Path(r["file"]) != tran or (tran.exists() and sha(tran) != r["sha"])):
            todo.append("robust.py result is not for the current final transient .asc")
        gen = REPO / "report" / "generated" / "results.tex"
        if not gen.exists() or f"% tag {s['tag']} " not in gen.read_text():
            todo.append("report/generated/results.tex is not from the latest evaluation (evaluate.py --publish)")
        pdf = REPO / "report" / "main.pdf"
        if not pdf.exists():
            todo.append("report/main.pdf missing (build with latexmk in report/)")
        else:
            if pdf.stat().st_mtime < latest.stat().st_mtime:
                todo.append("report/main.pdf is older than results/latest.json: rebuild")
            info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
            m = re.search(r"Pages:\s+(\d+)", info)
            if not m or int(m.group(1)) != 8:
                todo.append(f"report has {m.group(1) if m else '?'} pages; the compulsory structure is exactly 8")
            txt = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
            if "??" in txt:
                todo.append("report contains unresolved ?? (missing \\opV/\\opI/\\res values or references)")
            if re.search(r"\bTODO\b", txt):
                todo.append("report still contains TODO text")
        if prog.exists() and prog.stat().st_mtime < latest.stat().st_mtime:
            todo.append("PROGRESS.md not updated since the last evaluation")

    if todo:
        print("NOT DONE:")
        for t in todo:
            print(" -", t)
        return 1
    print("DONE: final design evaluated, robust, report built (8 pages), progress logged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
