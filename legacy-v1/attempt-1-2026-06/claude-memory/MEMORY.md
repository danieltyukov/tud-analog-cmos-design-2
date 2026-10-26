# Memory index

- [No auto-commit](git-no-autocommit.md) — never `git commit` unless the user explicitly asks; save files only
- [Schematics must be complete](schematics-must-be-complete.md) — `.asc` must use REAL drawn components (never SPICE text-directive elements), no deleted-symbol gaps, no stale labels/params/.meas; now a project CLAUDE.md rule

- [Circuit sim tooling](circuit-sim-tooling.md) — MCPs: ltspice (Wine, +render_schematic), spicelib (ngspice), matlab (R2025b); no SLiCAP here; see LTSPICE_TOOLCHAIN.md
- [LTspice Wine gotchas](ltspice-wine-gotchas.md) — display required, harmless stderr, paths, stepped .raw
- [EE4525 AC bench + sizing](ee4525-ac-bench-and-sizing.md) — read A0/GBW/PM from unloaded V(voutp)-V(voutn) (NOT voutp2); mirror-ratio M sizing; wide-swing margins intrinsic; baseline.asc can't .ac
- [EE4525 SC-CMFB (Phase 3)](ee4525-sc-cmfb.md) — real switched-cap CMFB at Vbcm (C_C 1.25p + C_CM 0.5p + weak 100MΩ helper); LTspice directive-element graft trick; I(Vdd) unchanged 1.547mA
- [EE4525 gain-boost (Phase 4)](ee4525-gain-boost.md) — real folded-cascode boosters + ref-pinned CMFB (self-biased → ceiling breach); A0 101.3dB / I(Vdd) 1.658mA; A0-sign bench artifact; clear ideal-block region before drawing; write_schematic OK for nmos4/pmos4/res
- [EE4525 current-reuse (Phase 5)](ee4525-current-reuse-phase5.md) — top-PMOS→PMOS input (g_m,N+g_m,P), I(Vdd) 1.135mA/−32%, SNR 66.8, FoM 170.5 PASS; settling near-miss (slew+booster-doublet, 78/66 at ~26.5ns); CM-sensitivity + bench-CMFB-stability + booster-2×-sweet-spot gotchas
- [EE4525 Class-AB attempt](ee4525-class-ab-attempt.md) — Class-AB output redesign (design/class-ab/) validated in principle but blocked by fundamental obstacles (16.6MΩ Rout, 1.2V input-CM vs cascoded sink, booster-loop osc, CMFB-aid ring); Class-A near-miss stays recommended — don't re-attempt the single-stage dead-ends
