# LTspice / SPICE toolchain — full-capacity workflow (this project)

Rules for driving the circuit-design toolchain end-to-end: **design →
verification → simulation → figure extraction (plots *and* circuits) →
iteration**. Every stage below has a tool that was **verified working on this
machine on 2026-06-26** (evidence in the "Verified" column). Read this before
SPICE work; it complements the machine-level `~/tools/*/OPERATING_RULES.md`.

## Engines — which to reach for

| MCP server | Engine | Use it for |
|---|---|---|
| **`ltspice`** | LTspice XVII (Wine) | the project `.asc` files: run sims, read bias, **plot waveforms**, **render schematic figures**, patch values |
| **`spicelib`** | ngspice (native) | from-scratch **netlist** design, fast parametric sweeps, numeric cross-checks |
| **`matlab`** | MATLAB R2025b | **post-processing**: noise integration, SNR / FoM / settling-$\tau$ math, $g_m/I_D$ tables, report-quality plots from extracted data |

> The project is **LTspice-driven** (`.asc` coursework + `log018.l`). Symbolic
> hand-derivations (gain, $\beta$, noise budget, settling $\tau$) live in
> `analysis/01_specs_and_budget.md` and `analysis/04_noise_budget.md`; MATLAB
> turns the extracted simulation data into the reported numbers and figures.
> **SLiCAP is not used in this project.**

## Capability matrix — every stage is covered

| # | Workflow stage | Tool (MCP / command) | Verified |
|---|----------------|----------------------|----------|
| 1 | Spec / budget / $\beta$ / noise derivations | by hand → `analysis/01_*`, `analysis/04_*` | ✅ docs |
| 2 | From-scratch netlist + sweeps | `spicelib` → `run_ac_analysis`/`run_transient`/`run_dc_op`/`run_sweep` (ngspice) | ✅ RC `fc≈999 Hz` |
| 3 | Run `.asc` simulation (AC/tran/DC/noise/`.step`) | `ltspice` → `run_simulation` | ✅ loaded-AC `rc=0` |
| 4 | Verify DC operating point / bias region | `ltspice` → `read_op_point` | ✅ |
| 5 | Inspect / parse schematic | `ltspice` → `read_schematic`, `list_schematics` | ✅ |
| 6 | **Extract plot figure** (waveforms → PNG) | `ltspice` → `plot_simulation` | ✅ PNG produced |
| 7 | **Extract circuit figure** (`.asc` → SVG/PNG) | `ltspice` → `render_schematic` *(new)* / wrapper | ✅ SVG+PNG |
| 8 | Iterate: patch a component value | `ltspice` → `modify_component`, `write_parameters` | ✅ |
| 9 | Author a new `.asc` programmatically | `ltspice` → `write_schematic` (router unreliable — prefer netlist) | ⚠ partial |
| 10 | Publication schematic (hand-drawn) | CircuiTikZ `circuits/*.tex` → SVG (`make`) | ✅ existing |
| 11 | **Post-process data** → noise integral, SNR, FoM, $\tau$ | `matlab` → `evaluate_matlab_code` / `run_matlab_file` | ✅ FoM 175.4 dB |
| 12 | Report-quality plots from extracted data | `matlab` (or matplotlib via `plot_simulation`) | ✅ |

## The new piece: schematic-figure extraction (`.asc` → SVG/PNG)

LTspice has **no** headless schematic-image export, and the SPICE MCPs only
plotted *waveforms*. That left a gap for "extract a figure of the circuit"
(report **Deliverable 2** node-voltage schematic, **Deliverable 3**
branch-current schematic). Filled with the PyPI **`ltspice-to-svg`** renderer,
which parses the `.asc` + `.asy` symbols and emits a faithful vector schematic.

It is exposed two ways:

**A. As an MCP tool (preferred, after the `ltspice` MCP reconnects):**

```
mcp__ltspice__render_schematic(path=".../folded_cascode_baseline.asc", png=true, width=2400, out_dir=".../report")
```
Returns `{svg, png, symbol_lib, parse}`. *(Added to the server this session; it
appears after the MCP server restarts/reconnects — until then use the wrapper.)*

**B. As a wrapper script (works right now, via Bash):**

```bash
~/tools/ltspice-render/.venv/bin/python ~/tools/ltspice-render/render_schematic.py \
    design/core-amp/folded_cascode_baseline.asc --out-dir <dir> --png --width 2400
```

Notes:
- Auto-discovers the symbol library (`~/.wine/.../LTspiceXVII/lib/sym`, falls
  back to `~/Documents/...`); **custom `.asy` next to the `.asc` are merged in**.
- **SVG** for LaTeX/GitHub; **PNG** (`--png --width`) for slides/Word.
- Output goes to `--out-dir` (default: next to the `.asc`). To avoid littering
  `design/`, render report figures into `report/` or a scratch dir.
- The renderer + its venv live in `~/tools/ltspice-render/` (isolated deps:
  `ltspice-to-svg`, `cairosvg`).

## MATLAB (post-processing & report math)

MATLAB R2025b is installed and licensed; the official MathWorks MCP server is
registered (`mcp__matlab__*`, available after reconnect). Use it for the
**numbers and final figures**, not for SPICE:

- Integrate the LTSpice `.noise` output PSD over $10\,\mathrm{kHz}$–$100\,\mathrm{GHz}$,
  **add the hand-computed $kT/C$**, and form $\mathrm{SNR}$.
- Compute the FoM ($2\pi P\tau/\mathrm{SNR_{lin}}^2$, then $-10\log_{10}$) and the
  settling $\tau = T_{38.6\mathrm{dB}}-T_{30\mathrm{dB}}$ from transient data.
- $g_m/I_D$ design tables, capacitor-sizing sweeps, and publication plots.

Tools (next session): `evaluate_matlab_code` (run a code string),
`run_matlab_file` (run a `.m`), `detect_matlab_toolboxes`, `check_matlab_code`.
Right now, via Bash: `matlab -sd <dir> -batch "scriptname"` (script-file form is
robust; inline multi-line `-batch` strings get mangled by the shell). Verified:
reproduces the EE4520 baseline FoM (175.4 dB) and the EE4525 $\tau\le3.29$ ns /
$354\,\mu V$ budget from `analysis/01`.

## End-to-end loop (concrete, this project)

1. **Size by hand first** — work the gain / $\beta$ / noise / settling numbers in
   `analysis/01_*` and `analysis/04_*` before committing W/L.
2. **Iterate values fast** — a netlist through `spicelib` (ngspice) sweeps.
3. **Simulate the real `.asc`** — `ltspice run_simulation` on
   `simulations/{ac,noise,transient}/*.asc` (uses `log018.l`, see below).
4. **Verify bias** — `read_op_point` → all transistors saturated, $V_{DS,sat}$ margins.
5. **Extract the plot** — `plot_simulation(raw_path, signals=[...])` (pass the
   **specific** signals; the schematic exposes ~200 nodes/branches — plotting
   all is noise).
6. **Extract the circuit figure** — `render_schematic` for the report schematic.
7. **Post-process** — `matlab` to integrate noise, add $kT/C$, compute SNR/FoM/$\tau$.
8. **Iterate** — `modify_component` / `write_parameters`, re-run, re-plot.

## Gotchas (toolchain-specific)

- **Model:** every `.asc` must use `log018.l` (with $1/f$ noise), **not**
  `logic018 no1of.l`. See `models/README.md`.
- **Wine display + stderr:** LTspice needs an X display even for `-b` (the MCP
  wraps `xvfb-run`); the `wine: Read access denied … Z:\` stderr is harmless —
  judge by `returncode==0` + output files.
- **`plot_simulation`:** pass explicit `signals=[...]`; default plots everything.
- **`render_schematic`:** writes `<stem>.svg` next to the `.asc` unless `out_dir`
  is given — the wrapper relocates it; the MCP tool honours `out_dir`.

## Where the tooling lives

| Path | What |
|---|---|
| `~/tools/ltspice-mcp/` | LTspice MCP (+ `OPERATING_RULES.md`); now includes `render_schematic` |
| `~/tools/spicelib-mcp/` | ngspice MCP |
| `~/tools/ltspice-render/` | **new** — `.asc`→SVG/PNG renderer venv + `render_schematic.py` wrapper |
| `~/tools/matlab-mcp-server/` | **new** — official MathWorks MATLAB MCP binary (R2025b, headless) |

*Sources for the renderer choice: [ltspice-to-svg (PyPI)](https://pypi.org/project/ltspice-to-svg/) ·
[lt2circuitikz](https://github.com/ckuhlmann/lt2circuitikz) (alt: `.asc`→CircuiTikZ) ·
[xuio/ltspice-mcp](https://github.com/xuio/ltspice-mcp) (macOS-only, not usable here).*
