# Attempt 1 (May to June 2026): FAILED, final grade 3.5

Frozen archive of the first EE4525 attempt. Submitted 28 June 2026 as
`report/5714699.pdf`, graded **3.5 / 10 (not accomplished)**. Kept for reference
only. **Do not build on these files**; the resit attempt starts from scratch in the
repo root. Paths inside these docs refer to the old layout (repo root), not
`legacy/attempt-1-2026-06/`.

## What was submitted

Single-stage gain-boosted folded cascode, complementary current-reuse input
(NMOS + PMOS pairs on one branch), real switched-capacitor CMFB, two real
folded-cascode gain-boosters, Class-A output.

| Item | Spec | Achieved |
|---|---|---|
| SNR | 66 dB | 66.8 dB |
| A settle at 25 ns | > 78 dB | **77.2 dB (FAIL)** |
| Aβ settle at 25 ns | 66 dB | **62.7 dB (FAIL)** |
| T settle | 25 ns | about 26.5 ns (FAIL) |
| τ | | 3.29 ns |
| Power / I(Vdd) | < 3 mW | 2.04 mW / 1.135 mA |
| Cin / Cfb / Cload | | 5 / 1.25 / 5 pF |
| Output step (diff) | | 0.9 V |
| FoM | > 170 dB | 170.5 dB |

## Why it most likely failed (post-mortem)

1. **A hard spec was missed.** Settling at 25 ns was 0.8 dB (A) and 3.3 dB (Aβ)
   short. The brief says the grade is for the power achieved *while meeting all
   specifications*; a design that does not settle is not a valid design. Framing
   it as an "honest near-miss" did not rescue it.
2. **Power was high anyway.** 2.04 mW is 1.6x the passing friend (1.24 mW, grade
   7.5) and about 7x the "best designs" (< 0.3 mW). Gain-boosters, their two CMFBs
   and the cascode branches burned current that added no input gm.
3. **Architecture fought the spec.** Class-A output slewing (136 µA into 5 pF,
   about 15 ns of the 25 ns budget spent slewing) plus a gain-booster pole-zero
   doublet. Raising current reopened the doublet; Class-AB variants on the
   single-stage core oscillated or broke A0 (see `design/class-ab/class_ab_results.txt`).
4. **Report did not follow the compulsory structure.** 16 pages with a contents
   page, D2 and D3 spread over 3 pages each, appendices. The brief prescribes 8
   pages, one item per page, fixed order.
5. **Over-built caps / swing choice.** Cin = 5 pF with only 0.9 V differential
   swing. The friend used 1.13 V swing and Cin = 3.24 pF: less load, same SNR.
6. kT/C used a conservative 50 kT/Cin factor; the Cin+Cfb+Cload derivation gives
   42 kT/Cin differential (what the passing report used).

## What is still worth reading

| Path | Why |
|---|---|
| `claude-memory/` | snapshot of the agent memory from attempt 1 (bench gotchas, CMFB/booster lessons) |
| `design/biasing/biasing_block.asc` | EE4520-style wide-swing bias block on separate Vddb (reusable idea) |
| `design/cmfb/` + `analysis/05_cmfb_design.md` | a working real SC-CMFB with drawn, wired switches |
| `analysis/04_noise_budget.md`, `08_power_prediction.md` | budget method (beware the 50 kT/C factor) |
| `design/class-ab/class_ab_results.txt` | dead ends: do not retry Class-AB on a gain-boosted single-stage core |
| `circuits/*.tex` | CircuiTikZ figure sources (style reference for D2/D3) |
| `report/report.tex` | LaTeX skeleton (too long; the new skeleton is in `../../report/`) |

The distilled lessons for the resit are in `../../brief/lessons.md`.

## Old to new path map

| Old (attempt 1) | Now |
|---|---|
| `analysis/`, `design/`, `simulations/`, `circuits/`, `report/`, `experiments/` | here |
| `LTSPICE_TOOLCHAIN.md`, `README.md`, `CLAUDE.md` | here (`CLAUDE.md` renamed `PROJECT_RULES_attempt1.md` so it is not auto-loaded) |
| `from-ee4520/` | `reference/ee4520/` |
| `reserach-papers/` | `reference/papers/` |
| `Project EE4525 2025-2026_updated.pdf`, `faq.txt` | `brief/assignment.pdf`, `brief/faq.txt` |

Large `.raw` simulation outputs (about 630 MB, gitignored, regenerable) were moved
here too; delete them freely to reclaim disk space.
