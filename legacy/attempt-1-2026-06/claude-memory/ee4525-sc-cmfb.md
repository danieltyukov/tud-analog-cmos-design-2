---
name: ee4525-sc-cmfb
description: "EE4525 Phase-3 real switched-capacitor CMFB — topology, verified results (CM 0.900V, GBW 264.4MHz), and the FAR-RIGHT wired layout; warns that a cramped-column layout faked GBW=260.4 via a wire-crossing CM->diff leak"
metadata: 
  node_type: memory
  type: reference
  originSessionId: bb4fecd9-8007-463d-929c-12a9ff9da5e0
---

Phase 3 swapped the ideal CMFB (`E1` VCVS) for a **real switched-capacitor CMFB**
in `design/cmfb/` (committed). Control node = **`Vbcm`** = gate of the output-CM
sink NMOS `Mn5.2`/`Mn7.2`. Ideal CMFB enforced `Vbcm = CM_out − 0.9 + Vbn`, so
`Vbcm = Vbn = 0.624 V` when output CM = 0.9 V — the real one reproduces this.

**Topology (two-cap canonical SC-CMFB):**
- `C_C` = `C7,C8` = **1.25 pF** each, *continuous* `Voutp/Voutn → Vbcm`. Because
  Vbcm is a high-Z gate, cap-coupled CM charge is *held* → this is the FAST CM loop
  (≈ diff GBW) AND the hold cap. It's invisible to differential (equal-opposite charge).
- `C_CM` = `Cs1,Cs2` = **0.5 pF** each, *switched* (row 18). φ1: charge between
  `Vcmr`(0.9) and `Vbn`(0.624); φ2: place `Vout→Vbcm` (∥ C_C) to refresh DC. Per-cycle
  transfer ≈ Ccm/(Ccm+C_C) ≈ 0.17 → CM settles in ~5–6 clock cycles (faq: "run several").
- 8 ideal switches `.model SWCM SW(Ron=10 Roff=1e9 Vt=0.9 Vh=0)`; 20 MHz non-overlap clock.
- **Weak DC helper (OP/AC only):** `Bhelp Vh 0 V=V(vcmavg)-0.9+V(Vbn)` + `Rhelp Vh Vbcm 100Meg`,
  where `vcmavg` = the large-R `R1,R2` output average (true-CM sense). `bv` symbol. Drives
  Vbcm *through* 100 MΩ → ~0.6 kHz BW (DC-only), sets bias point exactly (CM=0.900 V).
  Static current added by whole CMFB = **0** (clocks 0 A; helper ~pA).
  ⚠ Do NOT use a plain VCVS `Ehelp N002 Vbcm/Vh N003 Vbn` here: its control inputs are the
  *constants* N003,Vbn, so with `Rhelp` inserted it senses N002 only via the weak R1,R2 pull
  and regulates the .op CM **loosely to 0.914 V**. The behavioural true-CM-sense `Bhelp` gives
  the correct 0.900 V. (Verified: Ehelp→914 mV, Bhelp→900 mV, same Rhelp.)

**✅ REDRAWN as real symbols + WIRED (2026-06-28) — directive graft is gone.** The whole CMFB is
DRAWN (`sw`,`cap`,`voltage`,`bv` Bhelp,`res`,`current` Idist) and joined by real **WIRE**
segments — NOT net-label flags. Per CLAUDE.md hygiene pt 2, FLAGs are used ONLY for the
sheet-spanning nets `Voutp/Voutn/Vbcm/Vbn` (+ ground, + `vcmavg` because the Bhelp expression
references it by name); the local nets `ap/bp/an/bn/phi1/phi2/vcmr/Vh` are WIRED (auto-named in
the netlist — electrically identical). Layout that wires cleanly: switches staggered so the
ap-bus (S1.A,S2.A,Cs.A collinear) and bp-bus (Cs.B,S3.A,S4.A collinear) are clean horizontals;
clock fan-out via per-phase trunks to sources stacked at distinct y on the right (distinct y
avoids paralleled-source errors); NC- grounded with coincident `FLAG 0`; route clock/vcmr
risers in clear x-lanes BETWEEN switches, never through a switch's NC- pin (that shorts the
net to gnd). All `.param Ccm`/`.model SWCM` moved INSIDE the params box (hygiene pt 4); artifact
`Voutp2` `.meas` chain pruned; core annotation "Ideal CMFB"→"SC-CMFB (Vbcm)"; `Vcm` removed.
Done in all three `folded_cascode_cmfb{,_ac,_tran}.asc`. **PLACEMENT (revised): the whole wired
block sits in the CLEAR FAR-RIGHT area (x>4512, right of the opamp core) in all 3 files, NOT the
left column.** Why: in the cramped left column the `.ac` bench (which also holds the loaded replica
+ feedback in that same x-column) had an unintended WIRE CROSSING merging a CMFB internal node with
replica wiring → a CM→diff leak (output |CM|≈0.019 for a diff drive) that made `.ac` read
**GBW=260.4 MHz — a LAYOUT ARTIFACT, not physics**. A symmetric SC-CMFB injects equal/opposite C_C
charge for a diff signal so Vbcm can't move → diff GBW must equal the ideal-CMFB case. Far-right
(clear of all other wiring) → CM→diff leak ~1e-13 and the **correct GBW=264.4 MHz**. ⚠ ALWAYS
verify CM→diff leak ~0; never trust a GBW from a layout whose wires share a column with other
circuitry. Box rectangles are sized to contain the RENDERED net-name/instance labels (they overhang
pin points ~65 px; tran source values are long `PULSE()` strings needing ~500 px extra right margin),
NOT the bare pin bbox — else the border clips the labels (the generator is scratchpad
`remediate3.py`, run with `<file> <op|ac|tran> 1180 4900`). Pin-offset table: sw A(0,16) B(0,96)
NC+(-48,80) NC-(-48,32); cap A(16,0) B(16,64); res A(16,16) B(16,96); voltage/bv +(0,16) -(0,96);
current +(0,0) -(0,80); e/e2 +(0,16) -(0,96) P/N at x-48. Verify wiring by netlist topology-diff
(treat auto-renamed locals as internal) + sim: CM 0.900 V, I(Vdd) 1.547 mA, A0 93.9 dB,
GBW 264 MHz, PM 89°, CM-step stable (+0.23 mV). **Phases 4/5 must draw + WIRE new circuitry,
keep all directives in the params box, flags only for sheet-spanning nets.**
[[schematics-must-be-complete]]

**Verified (returncode 0, log018.l):** OP all 17 FETs sat, CM 0.900 V, I(Vdd) 1.547 mA
(== Phase-2, ceiling held). Diff AC 93.81 dB / 264 MHz / 89° — unregressed. CM-step
transient stable (overshoot +0.26 mV), returns to 0.9 V, CM-loop τ 4.15 ns
(f_cm≈38 MHz ≈ diff f_u 52.9 MHz → tracks in 25 ns). Full log: `design/cmfb/phase3_results.txt`.
Extraction: `design/cmfb/extract_ac.py`, `analyze_cm_step.py` (spicelib venv). See
[[ee4525-ac-bench-and-sizing]], [[circuit-sim-tooling]].
