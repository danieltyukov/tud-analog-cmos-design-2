#!/usr/bin/env bash
# SessionStart (startup|resume|clear|compact): re-inject the current state so a fresh or
# compacted context knows where the work stands. Plain stdout is added to Claude's context.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
echo "== EE4525 resit: session brief (from PROGRESS.md and results/latest.json) =="
if [ -f PROGRESS.md ]; then
  awk '/^## Current state/{f=1} /^## Plan/{f=0} f' PROGRESS.md
  echo "Last log entries:"
  awk '/^## Session log/{f=1;next} /^## Failed approaches/{f=0} f && /^- /' PROGRESS.md | tail -5
fi
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("results/latest.json")
if p.exists():
    s = json.loads(p.read_text())
    t = {r["item"]: r["achieved"] for r in s["table"]}
    fails = [k for k, v in s["checks"].items() if not v]
    print(f"Latest evaluation {s['tag']} ({s['time']}): {'ALL PASS' if s['all_pass'] else 'NOT DONE'}; "
          f"P={t[8]:.3f} mW SNR={t[1]:.2f} Abeta25={t[2]:.2f} A25={t[3]:.2f} FoM={t[22]:.2f}")
    if fails:
        print("  failing: " + "; ".join(fails))
else:
    print("No evaluation yet (results/latest.json missing).")
PY
[ -f .claude/autorun.on ] && echo "Autorun is ON: the Stop hook blocks stopping until tools/check_done.py passes."
echo "Ritual: read PROGRESS.md fully, run 'uv run tools/selftest.py', then continue the next unchecked plan step."
exit 0
