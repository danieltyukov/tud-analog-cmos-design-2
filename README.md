# EE4525 2025–2026 — A Residue Amplifier for a Pipeline ADC

Design of a fully-differential switched-capacitor residue amplifier in 0.18 µm
CMOS, 1.8 V. **Due: Sun 28 Jun 2026, 23:59.** Specs (common to all): SNR ≥ 66 dB,
$A_{settle}$ > 78 dB, $A\beta$ settle ≥ 66 dB in **25 ns**, **lowest power = the
grade** (< 3 mW to pass, best < 0.3 mW), FoM > 170 dB.

**Architecture (settled):** single-stage **gain-boosted cascode** + **current-reuse**
complementary input + **real switched-capacitor CMFB** — see `analysis/02`.

## How the docs fit together (the execution flow)

```
spec/rules ─► design derivations ─► sizing ─► simulate ─► extract figures ─► report
   00,07         01,02,04,08          03      09 runbook     report/         report/
```

### Where everything is

| Area | File(s) | Purpose |
|---|---|---|
| **Plan / steps** | `analysis/PLAN.md` | phased schedule (Phase 0–6), risk log |
| **Spec & results to match** | `analysis/00_spec_table.md` | the 22-row Deliverable-1 table (specs + achieved) |
| | `analysis/07_lecturer_clarifications.md` | all TA clarifications (1/f model, ringing, FoM, single rail, submission) |
| **Design derivations** | `analysis/01_specs_and_budget.md` | β, $A_0$, τ, noise budget, power feel |
| | `analysis/02_topology_choice.md` | **architecture decision + EE4520→EE4525 build plan** |
| | `analysis/03_sizing_calcs.md` | $g_m/I_D$ sizing method + template |
| | `analysis/04_noise_budget.md` | thermal + 1/f + kT/C, NEF, terms 10/11/12 |
| | `analysis/05_cmfb_design.md` | CMFB (real SC-CMFB chosen) |
| | `analysis/06_settling_analysis.md` | τ, settling accuracy, D4 plot rules |
| | `analysis/08_power_prediction.md` | top-down power/FoM floor (Bult method) + the 4 grade knobs |
| **Simulations** | `analysis/09_simulation_runbook.md` | **every sim to run, its `.meas`, what it produces** |
| **Report & figures** | `report/README.md` | **every deliverable → figure → how to extract it** |
| **Tooling** | `LTSPICE_TOOLCHAIN.md` | LTspice/ngspice/MATLAB MCPs, schematic renderer, gotchas |
| **Model** | `models/README.md` | `log018.l` (1/f) — required; not `logic018 no1of.l` |
| **Literature** | `reserach-papers/README.md` | Binkley (booster sizing) + Ryu (current-reuse) design rules |
| **Prior course** | `from-ee4520/README.md` | reused EE4520 artefacts + the Deliverable-7 baseline (FoM 175.2 dB) |
| **Working schematics** | `design/`, `simulations/` | core + biasing + AC/transient/noise testbenches |
| **Experiments** | `experiments/` | toolchain/edit sandboxes |

## Current state

**Phases 1–4 done** (`PLAN.md`). Phase 1 specs/budget frozen; Phase 2 folded-cascode
core sized (ideal CMFB + ideal gain-boost); Phase 3 swapped in a **real switched-capacitor
CMFB** (`design/cmfb/`, `analysis/05`); Phase 4 swapped in **two real folded-cascode
gain-boosters + reference-pinned CMFB** (`design/gain-boost/`, `analysis/10`) — the genuine
78 dB test: **A₀ 101.3 dB · GBW 262 MHz · PM 85.9° · I(Vdd) 1.658 mA / 2.985 mW** (real
boosters add +111 µA, all 28 booster FETs saturated, CMFB unregressed). Next: Phase 5
current-reuse + noise/settling closure, Phase 6 report. The β/gain question is **resolved**:
$C_{in}{:}C_{fb} = 4{:}1$ (residue gain $= C_{in}/C_{fb} = 4$; loop
$\beta = C_{fb}/(C_{in}+C_{fb}) = 1/5$, noise gain 5) — see `analysis/01` §1.

## To execute (short version)

1. `PLAN.md` Phase 1 — freeze swing, $C_{in}/C_{fb}/C_{load}$, first-cut $g_m$/current.
2. Phases 2–5 — size core, drop in real CMFB → real boosters → current-reuse; run sims (`09`) after each change.
3. Phase 6 — extract figures + fill the table (`report/README.md`), write up, submit.
