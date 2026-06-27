# Experiment: edit, restructure & simulate a duplicated CMOS1 schematic

**Goal:** prove the toolchain can *duplicate* a final CMOS1 (EE4520) schematic,
*edit values*, then perform **real structural surgery (components + wiring)*,
*render* before/after figures (white background), and *simulate + plot* — driving
the live `mcp__ltspice__*` tools end-to-end and fixing whatever breaks.
Source: `from-ee4520/biasing-block-hw1/Simulation_1.asc` (the biasing
current-mirror; uses `log018.l`). Date: 2026-06-27.

## Folders

| Folder | What |
|--------|------|
| `before/` | pristine duplicate (`.op`) — baseline render + sim |
| `after/`  | **value edits**: `Ibm` 200µ→400µ, `Mn` 11→22, `Vop` 1→0.9 |
| `structural/` | **circuit surgery**: a component removed + a component added + rewiring + a swept plot |

Each folder has `Simulation_1.asc` (schematic), `.svg`/`.png` (rendered figure,
**white background**), and `.log` (sim output). `structural/` also has
`Simulation_1_dcsweep.png` (the simulation plot).

## Part A — value edits (`after/`)

| Edit | Tool |
|------|------|
| `Ibm` 200 µA → 400 µA, `Mn` 11 → 22 | text `Edit` of the `.param` directive |
| `Vop` 1 → 0.9 | `mcp__ltspice__modify_component` |

`.op` result: bias scaled with the reference current as a mirror must —
Mp3 −1.50 mA → −3.00 mA, Mp1/2/4/5 −200 µA → −400 µA, Mn3 1.16 mA → 2.32 mA (all ×2).

## Part B — structural surgery (`structural/`)

Actual components and wiring changed (not just params):

1. **Removed** the ideal `Vop` voltage source (the probe that forced the cascode
   output node).
2. **Added** a real load resistor **`RL = 3k`** from the cascode output node
   (`Iop`) to ground. *First* connected by **net-name flag** (electrically valid —
   LTspice merges same-named nets — but it looked detached in the figure), then
   **relocated onto the cascode-output wire** so it is connected by a **drawn
   wire** too. Both render and simulate identically (`RL Vop 0 3k`).
3. **Changed the analysis** from `.op` to a DC sweep **`.dc Vdd 0 1.8 0.02`**.

The generated netlist confirms the wiring: **`RL Vop 0 3k`** (the new resistor
bridges the cascode-output net to ground; `Vop` is now just the net name).

**Simulation plot** (`Simulation_1_dcsweep.png`): `V(Iop)` rises with the supply
and **saturates at 1.2 V = 400 µA × 3 kΩ** — the PMOS cascode delivers its bias
current into the new load and clamps once it has headroom. Physically correct.

## Iterate-to-fix log (things that broke, and the fix)

- **`plot_simulation` returned `signals_plotted: []`** for `V(Vop)`. Cause: the
  `.raw` names the node `V(vop)` (lowercase) and signal matching was
  case-sensitive. Fix: retried with the exact name **and** made the MCP plotter's
  signal matching **case-insensitive** so `V(Vop)` / `V(VOP)` / `V(vop)` all work
  (takes effect after the next MCP reconnect).
- **Renders looked dark** in the file viewer (transparent PNG). Fix: the renderer
  now injects a **white background** into both SVG and PNG by default.

## Tools exercised (live MCP)

`read_schematic` ✓ · `run_simulation` ✓ (×3) · `modify_component` ✓ ·
`plot_simulation` ✓ (after the case fix) · `render_schematic` wrapper ✓ ·
text `Edit` for `.param`/structural geometry ✓.

See `../../LTSPICE_TOOLCHAIN.md` for the full workflow.
