# Deliverable 1 — Table of Results (target spec)

Course: **EE4525 2025/2026 — A Residue Amplifier for a Pipeline ADC**
Due: **2026-06-28**
Process: 0.18-µm CMOS (BSIM3, 1.8 V), LTSpice

**Bold** = the green-shaded "specifications you are asked to achieve" cells in the
PDF table — rows **1–4, 8, 9, 13, 14, 17**. The Achieved column is filled during
design; the PDF's example numbers are **illustrative only** (e.g. its row-8 "81"
deliberately *violates* the < 3 mW spec to show the column is just an example, so
do not copy them). Note: the PDF table prints row 22 as $10\log_{10}$ **without**
the minus sign — the 21 Jun TA clarification adds it, so we use $-10\log_{10}$
(positive dB). See `07_lecturer_clarifications.md` §4.2.

**Achieved column legend:** **bold** = frozen Phase-1 design choice (won't change
in sim); *italic* = simulation/closure result, pending later phases, shown with a
Phase-1 *prediction* in parentheses. Predictions from `phase1_budget.m`.

| #  | Design Item                              | Unit       | Spec                | Achieved |
|----|------------------------------------------|------------|---------------------|----------|
| 1  | SNR                                      | dB         | **66**              | *TBD (≥66)* |
| 2  | $A\beta_{settle}$ (loop setting)         | dB         | **66**              | *TBD (≥66)* |
| 3  | $A_{settle}$ (amplifier settling)        | dB         | **> 78**            | *TBD (>78)* |
| 4  | $T_{settle}$ (to required accuracy)      | ns         | **25**              | **25** |
| 5  | $T_{30\,\mathrm{dB}}$                    | ns         | ---                 | *TBD* |
| 6  | $T_{38.6\,\mathrm{dB}}$                  | ns         | ---                 | *TBD* |
| 7  | $\tau = T_{38.6\,\mathrm{dB}} - T_{30\,\mathrm{dB}}$ | ns | ---            | *TBD (~3.0)* |
| 8  | Power dissipation (amplifiers only)      | mW         | **< 3**, low as poss| *TBD (0.30–1.27)* |
| 9  | $I(V_{dd})$ (amps only, no biasing)      | mA         | **< 1.7**, low as poss | *TBD (0.16–0.70)* |
| 10 | Total effective $kT/C$ noise at output   | µV$_{rms}$ | free                | **204** (hand-calc) |
| 11 | Total integrated amplifier noise         | µV$_{rms}$ | free                | *TBD (≤225)* |
| 12 | Total integrated noise (10 kHz–100 GHz)  | µV$_{rms}$ | free                | *TBD (≤319)* |
| 13 | Input step voltage                       | mV         | **$V_{out}/4$**     | **225** |
| 14 | Output step voltage                      | V          | **free** (you choose) | **0.9** (diff; ±0.45 V se) |
| 15 | $C_{in}$                                 | pF         | ---                 | **5** |
| 16 | $C_{fb}$                                 | pF         | ---                 | **1.25** |
| 17 | $C_{load}$                               | pF         | **= $C_{in}$**      | **5** |
| 18 | $C_{CM}$                                 | pF         | ---                 | *TBD (~0.5, Ph3)* |
| 19 | $R_{fb}$                                 | GΩ         | big                 | **1** ($R_{fb}/R_{in}=4$) |
| 20 | $C_{big}$                                | nF         | big                 | **1** |
| 21 | $\mathrm{FoM}_{lin} = 2\pi \cdot P \cdot \tau / \mathrm{SNR}_{lin}^2$ | J |   | *Ph-2 pre-closure **1.32e-17** (final TBD, Ph-1 pred 1.5e-18)* |
| 22 | $\mathrm{FoM}_{dB} = \mathbf{-}10\log_{10}(\mathrm{FoM}_{lin})$ (positive) | dB |          | *Ph-2 pre-closure **168.8** ⚠ <170 (final TBD, Ph-1 pred 178)* |

## Phase-2 design-verification results (2026-06-28, ideal CMFB + ideal gain-boost)

Core sized in `design/core-amp/folded_cascode_baseline.asc`, verified on the loaded
AC bench `simulations/ac/loaded_ac_baseline.asc` ($C_L=5\,\mathrm{pF}$) and `.op`.
Full sizing table + method in `03_sizing_calcs.md`. **These are Phase-2 numbers with
the ideal CMFB/boost still in place and NMOS-only input (no current-reuse yet)** —
real CMFB is Phase 3, real boosters Phase 4, current-reuse power optimisation Phase 5.

| Metric | Spec / target | Phase-2 achieved | Note |
|---|---|---|---|
| $A_0$ (open-loop diff gain) | $\ge 78$ dB | **93.9 dB** | with **ideal** boost — "confirmed achievable"; real-booster 78 dB test is Phase 4 |
| Amplifier GBW $=f_u/\beta$ | $\approx 242$ MHz | **264 MHz** | $g_{m,in}=12.2\,\mathrm{mS}$, $C_{L,eff}\approx7.3\,\mathrm{pF}$ |
| Loop crossover $f_u$ ($|A|\beta=1$) | $\ge 48.4$ MHz | **52.9 MHz** | → $\tau_{cl}=1/2\pi f_u$ |
| $\tau_{cl}$ | 3.0 ns (< 3.29 ceiling) | **3.01 ns** | row 7 design-verify (transient confirm in Phase 5) |
| Phase margin | $\ge 60°$ | **89°** | single dominant pole; non-dominant poles $\gg f_u$ |
| $g_{m,in}$ | $\approx 10$ mS | **12.2 mS** | input pair $g_m/I_D=20.4$, $I_D=597\,\mu\mathrm{A}$/side |
| All transistors saturated | yes, $V_{DS,sat}\gtrsim100$ mV | **yes** (min 52 mV) | wide-swing/tail devices 52–85 mV (intrinsic, all in sat.) |
| Branch rule $I_{top}\ge I_{in}$ | required | **773 µA ≥ 597 µA** (37 % fold margin) | folded-cascode "common mistake" check |
| $I(V_{dd})$ (amps only) — **row 9** | $<1.7$ mA | **1.55 mA** | NMOS-only; drops in Phase 5 (current-reuse) |
| Power (amps only) — **row 8** | $<3$ mW | **2.78 mW** | $=I(V_{dd})\cdot1.8$; Phase-5 target $\to0.3$ mW |

Figures: open-loop Bode `../report/figures/phase2_openloop_bode.png`; sized core
schematic `../report/figures/folded_cascode_baseline.{svg,png}`.

### FoM reality check — the metric that grades this project (PRE-CLOSURE)

With the Phase-2 power and the AC-derived settling proxy:

$$\mathrm{FoM}_{lin} = \frac{2\pi\,P\,\tau}{\mathrm{SNR}_{lin}^2}
 = \frac{2\pi\,(2.78\,\mathrm{mW})(3.01\,\mathrm{ns})}{1995^2}
 = 1.32\times10^{-17}\,\mathrm{J}
 \;\Rightarrow\; \mathrm{FoM}_{dB} = -10\log_{10}(\cdot) = \mathbf{168.8\,dB}.$$

($\tau = 1/2\pi f_u = 3.01\,\mathrm{ns}$ from $f_u=52.9\,\mathrm{MHz}$; $\mathrm{SNR}_{lin}=1995$ at $66\,\mathrm{dB}$.)

- **(a) 168.8 dB is BELOW the 170 dB pass line** and below the **EE4520 baseline (175.2 dB)** we must beat in Deliverable 6.
- **(b) This is NOT a Phase-2 exit criterion.** FoM is a Phase-5/6 *closure* metric: it needs the **final** power, the **transient-measured** $\tau$ ($T_{38.6}-T_{30}$, not the AC proxy), and the **integrated noise / SNR**. The 168.8 dB here is a pre-closure indicator computed from the Phase-2 (NMOS-only, ideal-block) power only.
- **(c) The lever to clear 170 dB is current-reuse (Phase 5).** FoM $\propto P$, so the dominant knob is power. The Phase-2 amp burns 2.78 mW NMOS-only; the complementary current-reuse input (≈2× $g_m/\mu\mathrm{A}$) is the planned path from 2.78 mW toward the 0.30 mW top-down floor → FoM toward ~178 dB. **Current-reuse is now MANDATORY, not optional.**

> **On track for the real 78 dB (Phase 4).** With the ideal boost the single-stage
> reads 93.9 dB; the *un-boosted* folded cascode here is $\sim$50–55 dB
> ($g_{m,in}r_{o,casc}$ with $r_{o}$ in the kΩ range, short $L=0.18\,\mu$m). The
> gain-boost must therefore supply $\gtrsim25$ dB of extra loop gain to clear 78 dB —
> well within a single-stage NMOS/PMOS cascode booster's reach (Binkley target
> $\ge 40$ dB), so **78 dB is on track**.

## Deliverable-1 clarifications (TA announcements — see `07_lecturer_clarifications.md`)

- **Row 10 ($kT/C$ noise):** the total effective $kT/C$ noise at the output includes
  **only** $C_{in}$, $C_{fb}$, and $C_{load}\,(=C_{in})$. With a switched-capacitor
  CMFB, the CMFB caps' $kT/C$ is **not** reported in this term.
- **Rows 11–12 (amplifier vs. total noise):** row 11 is the LTSpice `.noise`
  integral (amplifier noise only); row 12 is the **total**,
  $\sqrt{V_{n,amp}^2 + V_{n,kT/C}^2}$ (amplifier noise **plus** the row-10 $kT/C$),
  since the residue amp is sampled. See `04_noise_budget.md` (terms 10/11/12).
- **Row 21 ($\mathrm{FoM}_{lin}$):** "Power $\tau$" $=$ Power $\times\,\tau$. The
  announcement's $T_{8.6\,\mathrm{dB}}$ is shorthand for **one $e$-fold of settling**
  ($20\log_{10}e = 8.686\,\mathrm{dB}$), i.e. $\tau = T_{38.6\,\mathrm{dB}} - T_{30\,\mathrm{dB}}$
  (rows 5–7). Confirmed by the EE4520 precedent (`from-ee4520/README.md`).
- **Row 22 ($\mathrm{FoM}_{dB}$):** keep the **negative sign** so the result is a
  **positive** dB value.
- **Pass target:** aim for $\mathrm{FoM}_{dB} > 170\,\mathrm{dB}$, i.e.
  $\mathrm{FoM}_{lin} < 9.5\times10^{-18}\,\mathrm{J}$.
- **Power (rows 8–9):** biasing-circuit power is excluded.

## Pipeline-ADC context (from PDF)

- 12-bit pipeline ADC, 2 bits resolved per stage → residue gain $2^2 = 4$.
- Required gain accuracy (12 − 2 = 10 bits residual): $0.5 \cdot 2^{-10} \equiv -66\,\mathrm{dB}$.
- Sampling rate **20 MS/s**, 50 % duty cycle → **25 ns** for amplification phase.
- Architecture is fully-differential switched-capacitor amplifier with **real CMFB** and (optionally) **real gain-boosters**. **No ideal sources** allowed except in the bias block.

## Top-level circuit (Fig. 1 of project PDF)

![Closed-loop SC residue amplifier — feedback network](../circuits/feedback_network.svg)

## Key constraints (from PDF + faq.txt)

- BJT / JFET forbidden. Only NMOS / PMOS / R / C.
- Total non-bias capacitance $\leq 1000\,\mathrm{pF}$. $R \leq$ a few MΩ ($\leq$ GΩ only for $R_{in}$ / $R_{fb}$).
- $R_{in}$ / $R_{fb}$ are **simulation-only biasing** resistors with **$R_{fb}/R_{in} = C_{in}/C_{fb}$** (so the DC operating-point gain equals the high-frequency cap gain — PDF p. 1).
- All NMOS bulk → GND. PMOS bulk free ($V_{dd}$ or own source).
- $M$ (parallel-device count) must be integer.
- $C_{load}$ must equal $C_{in}$.
- $kT/C$ noise is hand-computed and added to LTSpice noise output before SNR.
