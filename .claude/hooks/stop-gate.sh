#!/usr/bin/env bash
# Stop: only while autonomous mode is on (touch .claude/autorun.on), refuse to stop until
# tools/check_done.py passes. Escape hatch for real user decisions: "BLOCKED: <question>" in
# the PROGRESS.md "Current state" section (check_done.py then exits 0).
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
[ -f .claude/autorun.on ] || exit 0
out=$(uv run --quiet tools/check_done.py 2>&1) && exit 0
jq -n --arg r "Not done yet according to tools/check_done.py:
$out
Continue with the next unchecked step in PROGRESS.md (log what you did first). If you genuinely need a
decision from the user, write 'BLOCKED: <question>' in the PROGRESS.md Current state section." \
  '{decision: "block", reason: $r}'
exit 0
