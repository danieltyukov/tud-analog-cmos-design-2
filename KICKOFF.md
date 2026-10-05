# Starting the resit agent

Everything the agent needs is in this repo: `CLAUDE.md` (instructions), `PROGRESS.md` (state),
`brief/` (spec, lessons, strategy), `tools/` (simulation, measurement, checks), `.claude/` (skills,
agents, hooks), `.mcp.json` (the `ltspice-asc` schematic server).

## 1. Launch

```bash
cd ~/workspace/tud/tud-analog-cmos-design-2
touch .claude/autorun.on        # optional: Stop hook keeps the agent working until tools/check_done.py passes
claude --permission-mode auto   # or plain `claude`; approve the project MCP server `ltspice-asc` once
```

Remove `.claude/autorun.on` (or press Esc) to let it stop. The agent stops on its own when it writes
`BLOCKED: <question>` into PROGRESS.md, which is how it asks you for a decision.

## 2. First prompt (paste as is)

```
Start the EE4525 resit. Follow CLAUDE.md exactly: read PROGRESS.md, run uv run tools/selftest.py, then read brief/spec.md, brief/lessons.md, brief/design-strategy.md and example/README.md once. Work through the plan in PROGRESS.md from P1 to P8 without waiting for me: budget on paper, netlist design in design/work with the benches, gates in order, power descent, then the drawn .asc in design/final, then the 8-page report. Use the skills (sizing, ltspice-loop, draw-asc, report-latex), run the spec-auditor agent before ticking each phase and the report-reviewer agent before calling the report done. The goal is every check PASS at the lowest power you can reach, target 0.6 mW or less. Log every experiment and dead end in PROGRESS.md. Do not commit, push or submit anything. Finish when uv run tools/check_done.py prints DONE, then give me the 22 form values from results/latest.json.
```

## 3. Alternatives for long unattended runs

- **ralph-loop plugin** (fresh prompt each iteration, survives long runs; use it instead of `autorun.on`,
  not together):
  `/ralph-loop:ralph-loop "<the prompt above>" --max-iterations 40 --completion-promise "EE4525 DONE"`
  and add to the prompt: "Output <promise>EE4525 DONE</promise> only when tools/check_done.py prints DONE."
  Cancel with `/ralph-loop:cancel-ralph`.
- **`/goal`** (built in): `/goal uv run tools/check_done.py prints DONE`.
- **Fresh context per phase**: `/clear` between phases is safe; the SessionStart hook re-injects
  PROGRESS.md and the latest results.

## 4. What to check while it runs

- `PROGRESS.md`: current state, log, failed approaches.
- `results/history.csv`: every evaluation (power, SNR, settling, pass/fail) in order.
- `results/<tag>/d4_settling.png`, `d5_noise.png`: latest plots.
- `report/main.pdf`: the report as it fills in.

## 5. Submission (you, not the agent)

Form: https://edu.nl/7turd, deadline **Sun 8 Nov 2026 23:59**, at most 2 submissions. Upload
`report/main.pdf` renamed `5714699.pdf` and copy the 22 values from `results/latest.json` (same numbers
as the D1 table). Click Submit and wait for the confirmation page.
