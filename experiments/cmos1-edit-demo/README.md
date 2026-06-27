# Experiment: edit + simulate a duplicated CMOS1 schematic

**Goal:** prove the toolchain can *duplicate* a final CMOS1 (EE4520) schematic,
*edit* it, *render* before/after figures, and *simulate* it — exercising the live
`mcp__ltspice__*` tools end-to-end. Date: 2026-06-27.

## Source

Duplicated from `from-ee4520/biasing-block-hw1/Simulation_1.asc` (the EE4520 HW1
biasing current-mirror block; references `log018.l`, active analysis `.op`).

## What changed (3 edits)

| # | Edit | How | Where |
|---|------|-----|-------|
| 1 | `Ibm` 200 µA → **400 µA** (reference current ×2) | text edit of the `.param` directive | `after/Simulation_1.asc` |
| 2 | `Mn` 11 → **22** (NMOS device multiplier ×2) | text edit of the `.param` directive | same |
| 3 | `Vop` 1 V → **0.9 V** (replica-branch output ref) | **MCP `modify_component`** | same |

## Result — `.op` simulation (both `returncode 0`)

The current-mirror bias scales with the reference current exactly as it must:

| Device | BEFORE (Ibm=200 µA) | AFTER (Ibm=400 µA) | ratio |
|--------|--------------------:|-------------------:|:-----:|
| Mp3 (mirror core) $I_d$ | −1.50 mA | −3.00 mA | ×2.0 |
| Mp1/Mp2/Mp4/Mp5 $I_d$  | −200 µA  | −400 µA  | ×2.0 |
| Mn3 $I_d$              | 1.16 mA  | 2.32 mA  | ×2.0 |

Secondary effects checked: PMOS overdrive rises with current (Mp3 $V_{gs}$
−0.85 V → −1.03 V); NMOS gate-overlap caps double (Mn device count ×2,
`Cgsov` 3.95 fF → 7.90 fF). All transistors still solve a valid operating point.

## Files

```
before/Simulation_1.asc   prior-to-edit schematic (pristine duplicate)
before/Simulation_1.svg   rendered figure (vector)
before/Simulation_1.png   rendered figure (raster)
before/Simulation_1.log   .op device operating-point table
after/Simulation_1.asc    edited schematic
after/Simulation_1.svg/.png   rendered figures (show Mn=22, Ibm=400u, Vop=0.9)
after/Simulation_1.log    .op device operating-point table
```

## Tools exercised (live MCP — all worked, nothing needed fixing)

- `mcp__ltspice__read_schematic` — parsed components/params/directives ✓
- `mcp__ltspice__run_simulation` — ran `.op` via Wine, `returncode 0` (before & after) ✓
- `mcp__ltspice__modify_component` — patched `Vop` 1→0.9 ✓
- `render_schematic` wrapper (`~/tools/ltspice-render/`) — `.asc` → SVG+PNG ✓
- text `Edit` on the `.param` directive (params are inline `TEXT`, not a `.inc`) ✓

See `../../LTSPICE_TOOLCHAIN.md` for the full workflow.
