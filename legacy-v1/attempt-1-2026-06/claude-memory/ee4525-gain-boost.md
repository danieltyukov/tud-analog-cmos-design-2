---
name: ee4525-gain-boost
description: "EE4525 Phase-4 real gain-boosters — folded-cascode aux-amps + ref-pinned CMFB; A0 101.3 dB, I(Vdd) 1.658 mA; entry state for Phase 5"
metadata: 
  node_type: memory
  type: project
  originSessionId: 38539a02-7248-46b4-a48e-07a1b4d0c98f
---

EE4525 Phase 4 (gain-boosting) is DONE & verified (2026-06-28). The ideal VCVS boosters
(E2/E3 PMOS-side, E5/E6 NMOS-side, Aadd=100) in `design/gain-boost/folded_cascode_gb{,_ac,_tran}.asc`
were replaced by **two REAL differential folded-cascode booster aux-amps, each with a
reference-pinned CMFB** (Binkley Fig. 7). Booster A = PMOS-input fold (regulates the NMOS
cascode, in-path); Booster B = NMOS-input fold (regulates the PMOS cascode, off-path). Bias
reuses Vbp/Vbn/Vcn/Vcp. **Verified: A0 101.27 dB (≥78, genuine real-booster test, +23 dB
margin; un-boosted core 55.8 dB), GBW 262 MHz, PM 85.9°, I(Vdd) 1.658 mA / 2.985 mW
(boosters +111 µA, 42 µA headroom to 1.7 mA), all 28 booster FETs saturated, CM 0.906 V,
diff-loop stable (CM-step Δdiff≈0).** Details: `analysis/10_gain_booster_design.md`,
`design/gain-boost/phase4_results.txt`.

**Why:** the design choices below are non-obvious and caused/avoided rework.
- A **folded** (not telescopic/5-T) booster is mandatory on 1.8 V: sense node (cascode
  source) and drive node (cascode gate) are a full Vgs (~0.65 V) apart; a 5-T OTA can't span it.
- The booster CMFB **must be reference-pinned** (diff-pair vs Vcn/Vcp), NOT self-biased: a
  self-biased CMFB lands the gate CM wherever the pull device sources the branch current →
  for Booster B that landed Vpr=566 mV (vs Vcp 873), pulling the PMOS-cascode source down and
  **ballooning the main-amp branch current 177→256 µA → I(Vdd) 1.768 mA (ceiling BREACH)**.
  Pinning gate CM to Vcn/Vcp restores the cascode sources to ~ideal and the amp to 1.66 mA.
- Booster UGF (~0.5 GHz) is faster than the Binkley 0.8ωu/0.4ωu targets — fine/conservative:
  it pushes the pole-zero **doublet beyond ωu**, no slow settling tail (clean single-pole AC).

**How to apply (Phase 5 entry + gotchas):**
- Phase-5 starts from `design/gain-boost/folded_cascode_gb.asc`. Keep the real boosters + SC-CMFB;
  add current-reuse (complementary NMOS+PMOS input → telescopic). Power ceiling is razor-thin
  (97.5 %); current-reuse halves the input branch and restores margin (also mandatory for FoM).
- Read A0/GBW/PM from the UNLOADED `V(voutp)-V(voutn)` via `design/gain-boost/extract_gb.py`
  (β=1/5), NOT the loaded `Voutp2` (~42 dB artifact). See [[ee4525-ac-bench-and-sizing]].
- **A0-sign bench artifact:** the single-copy `.op/.tran` benches and the dual-copy `_ac` bench
  use OPPOSITE AC-drive phases, so `V(voutp)-V(voutn)` reads 0° vs 180° for the SAME amp. Don't
  compare the A0 *sign* across benches — only within one; the magnitude (101.3 dB) is the result.
- **Drawing real blocks over an ideal one:** deleting ideal VCVS symbols leaves their connecting
  WIRES/FLAGs in place — those collide with the new drawn wires and short nodes. Must clear the old
  test-block region first (see `design/gain-boost/integrate_boosters.py`). Also, LTspice connects a
  **FLAG** on a 4-terminal MOSFET bulk pin but NOT a **wire** from it, so bulks (0/Vdd) are flagged,
  not wired. See [[schematics-must-be-complete]] and [[ltspice-wine-gotchas]].
- **`mcp__ltspice__write_schematic` DOES place + auto-wire nmos4/pmos4/res/voltage** from a `nets`
  map (+ optional `layout` coords) — the Phase-3 "router unreliable" caveat was about SWITCHES (S)
  and VCVS (E) ONLY. For future transistor blocks, prefer it: build each booster as a clean STANDALONE
  .asc, netlist-diff vs the locked design, then transplant its SYMBOL/WIRE/FLAG lines (offset) into the
  main sheet. (Phase 4 used a hand generator `gen_boosters.py` — same result, more effort.)
- **The .asc bar is drawn/readable/honest, NOT publication-perfect** — dense label overlap on a 28-FET
  block is fine. The polished report figure is **CircuiTikZ** (`circuits/cmfb_sc.tex` style), a Phase-6 item.
