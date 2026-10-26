---
name: ee4525-class-ab-attempt
description: EE4525 Class-AB output redesign attempt — validated in principle but blocked by fundamental topology obstacles; Class-A near-miss stays recommended
metadata: 
  node_type: memory
  type: project
  originSessionId: b96563b9-0a8f-439e-8543-f06c0da7f58a
---

A Class-AB OUTPUT redesign of the residue amp (to close the 25 ns settling the Class-A
current-reuse design misses by ~1.5 ns) was attempted in `design/class-ab/folded_cascode_ab*.asc`
(forked from [[ee4525-current-reuse-phase5]]); full record in `design/class-ab/class_ab_results.txt`.

**Result (honest):** the Class-AB *differential* slew boost WORKS in principle (diff output
settled to ~1.3 mV by 20 ns, faster than baseline), but NO clean/stable/spec-preserving single-
stage realization was found after ~10 variants / 8 mechanisms. **Recommended design stays the
Class-A near-miss** (A0 106.7 / GBW 266 / PM 86.9 / SNR 66.8 / I(Vdd) 1.135 mA / FoM 170.5 dB;
settling A 77.2 / Aβ 62.7 @ 25 ns, reaches 78/66 at ~26.5 ns) — re-verified bit-identical in
`design/class-ab/`.

**The fix is targeted but blocked (the slew limiter = the falling output's NMOS sink, hard-clamped
at the 136 µA fixed source Mn5.2/Mn7.2; Voutp falls −35 mV/ns vs Voutn rises +57 mV/ns).**
Fundamental obstacles (all sim-confirmed) — these are why to NOT re-attempt the same single-stage dead-ends:
- **Gain-boosted output Rout ≈ 16.6 MΩ** → any non-cascoded assist draining at the output destroys A0 (accuracy → 32 dB).
- **Input-CM 1.2 V > output 0.9 V** (raised for the current-reuse PMOS) → a cascoded NMOS sink needs its gate <0.9 V, so it can't be driven from the input (the only stable feedforward node) without a level shifter. This is the "input-CM coupling" obstacle.
- **High-gain gain-booster loops** → any large-swing internal drive (output / Vpr / Vgnn) closes a fast loop that OSCILLATES (~385 MHz). Only gentle input-feedforward is stable — and it's too weak (±85 mV swing).
- **Ideal-CMFB sim-aid rings** on single-ended (CM-disturbing) boosts; slowing it doesn't help. CM-neutral push-pull needs N/P matching + adds bias-perturbing standby.
- **Razor-thin margin:** need vg ≤ 85 µV @ 25 ns (Aβ 66); any assist standby shifts the 1/β offset enough to erase it → true class-B needed, but the small input swing can't turn a class-B device on hard.

**Only architecture that sidesteps these:** a full TWO-STAGE Class-AB output stage (own bias rail,
own CMFB) — not pursued (separate full design + Miller Rz·Cc doublet ringing + stage-2 FoM cost;
see `analysis/11_two_stage_alternative.md`). Bench/extraction method = same as [[ee4525-ac-bench-and-sizing]];
ring-robust settling metric = MAX|vg| over 45–58 ns (the exact-25 ns .meas is fooled by oscillation zero-crossings).
