#!/usr/bin/env bash
# Stop: only while autonomous mode is on (touch .claude/autorun.on BEFORE launching the agent),
# refuse to stop until tools/check_done.py passes. Sessions that started before the flag was
# created (e.g. an older session still open in this repo) are not gated.
# Escape hatch for real user decisions: "BLOCKED: <question>" in the PROGRESS.md "Current state"
# section (check_done.py then exits 0).
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
[ -f .claude/autorun.on ] || exit 0
input=$(cat)
started_before_flag=$(printf '%s' "$input" | python3 -c '
import json, os, sys, datetime
try:
    tp = json.load(sys.stdin).get("transcript_path") or ""
    flag = os.path.getmtime(".claude/autorun.on")
    with open(tp) as fh:
        for line in fh:
            ts = json.loads(line).get("timestamp")
            if ts:
                start = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                print("yes" if start < flag else "no")
                break
        else:
            print("no")
except Exception:
    print("no")
')
[ "$started_before_flag" = "yes" ] && exit 0
out=$(uv run --quiet tools/check_done.py 2>&1) && exit 0
jq -n --arg r "Not done yet according to tools/check_done.py:
$out
Continue with the next unchecked step in PROGRESS.md (log what you did first). If you genuinely need a
decision from the user, write 'BLOCKED: <question>' in the PROGRESS.md Current state section." \
  '{decision: "block", reason: $r}'
exit 0
