# EE4525 2025-2026 resit: a residue amplifier for a pipeline ADC

Fully differential switched-capacitor residue amplifier (gain 4) in 0.18 µm CMOS, 1.8 V, LTspice.
Specs: SNR ≥ 66 dB, Aβ ≥ 66 dB and A > 78 dB at 25 ns, FoM > 170 dB; **the grade is set by the lowest
power that meets them all** (< 3 mW to pass, best designs < 0.3 mW). Resit deadline **Sun 8 Nov 2026, 23:59**.

| Attempt | Result |
|---|---|
| 1 (June 2026, `legacy/attempt-1-2026-06/`) | 2.04 mW, settling missed at 25 ns, **3.5 (fail)** |
| reference (`example/`, a friend's design) | 1.24 mW, all specs met, 7.5 |
| resit (this repo) | in progress; see `PROGRESS.md` |

## How this repo is set up

The resit is run by a Claude Code agent with a purpose-built harness. To start it, follow `KICKOFF.md`.

| Path | What |
|---|---|
| `CLAUDE.md` | agent instructions: mission, start ritual, tools, workflow, hard rules |
| `PROGRESS.md` | live state, plan with gates, experiment log, failed approaches |
| `brief/` | assignment PDF, FAQ, TA clarifications, distilled `spec.md`, `lessons.md`, `design-strategy.md` |
| `tools/` | Python (uv) tooling around LTspice XVII: runner, metrics, judge, robustness, optimizer, gm/ID, lint, report macros |
| `design/` | bench templates, netlist work area, final drawn `.asc` |
| `report/` | 8-page LaTeX report in the compulsory structure, values generated from simulation |
| `.claude/` | project settings (permissions, hooks), skills, subagents |
| `.mcp.json` | `ltspice-asc` MCP server for drawing and verifying `.asc` schematics |
| `reference/` | EE4520 artefacts (FoM baseline for Deliverable 6, bias block) and papers |
| `models/` | `log018.l` (with 1/f noise, mandatory) |

Toolchain check: `uv run tools/selftest.py` re-measures the passing example and must match its report.
