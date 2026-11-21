# EE4520 artefacts (Analog CMOS Design I)

Everything in here is carried over **verbatim** from the prior project
`tud-analog-cmos-design-1` (student 5714699, design #27). It is the starting
point EE4525 builds on, and the **baseline for Deliverable 6** (FoM comparison).
Do not edit these files: they are a frozen reference. New EE4525 work lives in
`design/`, `tools/` and `report/`.

## Directory map

| Path | What it is | Origin in `tud-analog-cmos-design-1` |
|------|-----------|--------------------------------------|
| `ee4520_design_overview.png` | One-page visual map of the **whole** EE4520 design (biasing, decoupling, ideal CMFB loaded/unloaded, ideal gain-boost PMOS/NMOS, feedback test bench) | `image-1.png` (README hero) |
| `biasing-block-hw1/` | HW1 biasing block: cascode current mirror, $R_n$/$R_p$ sweeps, op-points | `hw1/` |
| `baseline-amplifier-hw2/` | HW2 folded-cascode amplifier: AC (loaded+unloaded), noise, transient sims + full report | `hw2/` |
| `baseline-amplifier-hw2/report/` | The EE4520 report (`report.md`), Deliverable-1 table, all 8 deliverable plots, appendix schematics | `hw2/report/` |
| `models/log018.l` | Process model (pristine; same file as `../models/log018.l`) | `log018.l` |
| `pdfs/` | EE4520 lecture intro, LTspice tutorial, HW1/HW2 assignments + submissions | root + `hw1/` + `hw2/` |

> Not carried over: `discrete_time_…_loaded_ac_sim.raw` (a gitignored binary sim
> output — the `.asc`/`.op.raw`/`.log` are here and it regenerates on a run).
> The EE4520 `README.md` held only the overview image, now
> `ee4520_design_overview.png`.

## EE4520 final result — the Deliverable-6 baseline

From `baseline-amplifier-hw2/report/deliverable_1_table_of_results.md`:

| Quantity | EE4520 achieved |
|----------|-----------------|
| SNR | 80.85 dB |
| $A_{settle}$ | 63.32 dB |
| $T_{settle}$ | 2800 ns |
| $\tau_{cl}$ (transient) | 497.4 ns |
| Power (amp only) | 0.1119 mW |
| $I(V_{dd})$ | 0.0622 mA |
| Integrated output noise | 76.93 µV$_{rms}$ |
| $C_{in}$ / $C_{fb}$ / $C_{load}$ / $C_{CM}$ | 18 / 2.25 / 18 / 2.25 pF |
| $\mathrm{FoM_{lin}}$ | $3.02\times10^{-18}$ J |
| **$\mathrm{FoM_{dB}}$** | **175.20 dB** |

Design knobs: ScaleA = 0.25, Ibm = 350 µA, input pair Mn34 = 200 (weak inversion),
W = 1 µm, L = 0.18 µm, Mp = 60, Mn = 11.

> **FoM notation:** the EE4520 table writes $\mathrm{FoM_{lin}} = 2\pi\,P\,T_{8.6\,\mathrm{dB}}/\mathrm{SNR_{lin}}^2$
> and computes $T_{8.6\,\mathrm{dB}} \equiv \tau = T_{48.69\,\mathrm{dB}} - T_{40\,\mathrm{dB}}$
> (one $e$-fold $= 8.69\,\mathrm{dB}$). This is the **same** "$T_{8.6\,\mathrm{dB}}$"
> shorthand the EE4525 announcement uses — see `legacy-v1/attempt-1-2026-06/analysis/07_lecturer_clarifications.md` §4.2.

## What changed EE4520 → EE4525 (why this is a redesign, not a copy)

| Spec | EE4520 (#27) | EE4525 | Implication |
|------|-------------|--------|-------------|
| SNR | 80.64 dB | **66 dB** | noise budget *relaxed* |
| $A_{settle}$ | 63 dB | **≥ 78 dB** | need *more gain* |
| $T_{settle}$ | 2800 ns | **25 ns** | **~112× faster** — speed-driven |
| FoM target | ≥ 174 dB | > 170 dB | similar |
| Process model | `logic018 no1of.l` (**no 1/f**) | **`log018.l`** (with 1/f) | must re-sim with flicker noise |
| CMFB | **ideal** | **real transistor** CMFB required | new block |
| Gain-boost | **ideal** | real, if used | new block(s) |

EE4520 was **noise-limited** (huge caps, weak-inversion input pair, tiny current).
EE4525 is **settling-speed-limited** (25 ns), so expect much higher $g_m$/current,
smaller time constants, and the ideal CMFB/boosters replaced by real circuits.
See `legacy-v1/attempt-1-2026-06/analysis/02_topology_choice.md` and `legacy-v1/attempt-1-2026-06/analysis/PLAN.md`.
