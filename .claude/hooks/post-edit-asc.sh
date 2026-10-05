#!/usr/bin/env bash
# PostToolUse: lint any .asc touched by Edit/Write or the LTspice MCPs (text checks only, fast).
# On rule violations, feed the findings back to Claude as a block reason.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
f=$(jq -r '.tool_input.file_path // .tool_input.path // .tool_input.target // .tool_input.schematic_path // empty')
case "$f" in *.asc) ;; *) exit 0 ;; esac
[ -f "$f" ] || exit 0
out=$(uv run --quiet tools/asc_lint.py --no-netlist "$f" 2>&1) && exit 0
jq -n --arg r "asc_lint found rule/hygiene violations in $f (fix before continuing):
$out" '{decision: "block", reason: $r}'
exit 0
