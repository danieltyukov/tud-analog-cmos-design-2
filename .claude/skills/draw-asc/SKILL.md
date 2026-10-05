---
name: draw-asc
description: Draws or edits the deliverable LTspice .asc schematics for EE4525 with the ltspice-asc MCP (edit_schematic, verify_circuit) so they are clean, fully wired, rule-compliant and provably equivalent to the verified netlist. Use when creating or changing any .asc, or when a schematic must be checked or rendered.
---

# Drawing the deliverable .asc

**Rules first (user's hard rules, the user opens these in the LTspice GUI)**
1. Every element is a drawn symbol. Never a SPICE element typed as a text directive (no E/B probes).
2. Pins are joined by drawn wires. Net-label flags only for sheet-spanning nets: `0`, `vdd`, `vddb`,
   `vcmr`, bias lines, `vop`/`von`/`vip`/`vin` where they cross blocks. Never a field of floating
   symbols tagged with the same local net.
3. All directives (`.lib`, `.param`, `.tran`/`.noise`, `.meas`, `.option`) inside ONE titled box
   "Parameters, Simulations & Measurements".
4. Each block (Bias, Stage 1, Stage 2, Compensation, CMFB, Test bench) in its own titled rectangle,
   same title size, no overlaps, nothing outside its box (enlarge the box instead).
5. No stale symbols, labels, params or `.meas`. 6. Re-verify after every change.

## Procedure

1. Start only from a netlist that passes `tools/evaluate.py` (`design/work/`). That netlist (with
   `amp.inc` inlined: `uv run python -c "import sys; sys.path.insert(0,'tools'); import lt, pathlib as p; f=p.Path('design/work/bench_tran.cir'); print(lt.inline_includes(f.read_text(), f.parent))" > design/final/reference_tran.cir`)
   is the equivalence reference.
2. Plan the layout on paper: block columns left to right (bias, stage 1, stage 2 + compensation,
   CMFB, test bench), 16-unit grid, 200+ units of clearance between blocks, directives box at the bottom.
3. Build with `mcp__ltspice-asc__edit_schematic`:
   - new sheet: `base: "blank"`; later edits: `base: "existing"` plus `expected_sha256` from the last result.
   - `add_component` (`symbol`: `nmos4`, `pmos4`, `res`, `cap`, `voltage`, `current`, `sw`; `value`;
     `attributes: {"Value2": "l={L1} w={W1} m={M1}"}`), then `return_views: ["pin_legend"]` to read pins.
   - Pins are `REF.PIN`: MOSFET `M1.D/G/S/B`, R/C `R1.A/B`, sources `V1.+/-`.
     (nmos4 at R0 from origin (x,y): D (x+48,y), G (x,y+80), S (x+48,y+96), B (x+48,y+48).)
   - `wire_pins` refuses diagonals: give `waypoints` so every segment is horizontal or vertical,
     and route around symbol bodies.
   - `add_net_label` with `pin` for ground (`0`) and the sheet-spanning nets only.
   - `add_directive` for each directive line, placed inside the parameters box area.
   - Titled rectangles are not an MCP op: append `RECTANGLE Normal x1 y1 x2 y2 2` and
     `TEXT x y Left 3 ;Block title` lines to the `.asc` with Edit afterwards (same size for all titles).
4. Verify with `mcp__ltspice-asc__verify_circuit`:
   `checks: ["symbols","export","layout","quality","compare"]`,
   `compare: {"reference": "design/final/reference_tran.cir"}`, `render: {"format": "png"}`.
   Require `comparison.equivalent == true` and zero layout/quality findings (overlaps, wires through
   bodies, floating pins, label-only nets). Look at the rendered PNG (path in `render.path`).
5. `uv run tools/asc_lint.py design/final/amp_tran.asc` clean, then
   `uv run tools/evaluate.py --tran design/final/amp_tran.asc --noise design/final/amp_noise.asc --tag final --publish`
   and `uv run tools/robust.py design/final/amp_tran.asc`. Numbers must match the netlist run.
6. The noise schematic is the transient one with the analysis directives swapped; keep both files in sync.

## Gotchas

- `ltspice-asc` writes scratch to `.ltspice-mcp/` in the repo (gitignored).
- Deleting a symbol leaves its wires and flags; clean them (`remove_wire`, `remove_net_label`) or they short new parts.
- A wire must end exactly on a pin; LTspice connects a flag on a MOSFET bulk pin but not a wire passing by.
- Crowded columns caused a fake CM-to-differential leak in attempt 1: keep blocks apart.
- `ltspice` (user MCP) `render_schematic` gives an alternative SVG/PNG render for a second look.
