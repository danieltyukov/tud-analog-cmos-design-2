---
name: circuit-sim-tooling
description: SPICE simulation is wired into Claude Code via two user-scope MCPs (LTspice + ngspice)
metadata: 
  node_type: memory
  type: project
  originSessionId: 6f789942-9dd7-4766-b7a8-2cae1298661d
---

Two SPICE engines are available as user-scope MCP servers (every project):

- **`ltspice`** (`~/tools/ltspice-mcp/`, run via `run.sh` = xvfb + venv) — LTspice XVII over
  Wine. Tools: list/read/run/read_op_point/read_waveforms/plot_simulation/modify_component/
  write_parameters/write_schematic + **`render_schematic`** (NEW — `.asc`→SVG/PNG circuit figure).
- **`spicelib`** (`~/tools/spicelib-mcp/`, `SPICE_SIMULATOR=ngspice`) — native ngspice for
  from-scratch **design** via netlists. Tools: run_ac_analysis/run_transient/run_dc_op/run_sweep.
- **`matlab`** (NEW, `~/tools/matlab-mcp-server/` official MathWorks binary, R2025b, headless,
  user-scope) — post-processing/report math: noise integration, SNR/FoM/τ, gm/ID, plots. Tools:
  evaluate_matlab_code/run_matlab_file/detect_matlab_toolboxes/check_matlab_code. Now via Bash:
  `matlab -sd <dir> -batch "scriptname"` (script-file form; inline multi-line strings mangle).

NEW (2026-06-26) tools (`render_schematic`, `matlab` MCP) appear only after the MCP **reconnects**;
until then use the Bash wrappers. `.asc`→SVG/PNG renderer: `~/tools/ltspice-render/` (own venv,
`ltspice-to-svg`+`cairosvg`). **This project (EE4525) does NOT use SLiCAP** — ltspice+spicelib+matlab
only; full workflow in `LTSPICE_TOOLCHAIN.md`. Operating rules: `~/tools/ltspice-mcp/OPERATING_RULES.md`.
Slash commands `/analyze-circuit`, `/design-circuit`. See [[ltspice-wine-gotchas]].
