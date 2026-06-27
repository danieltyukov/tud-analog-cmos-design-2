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

| #  | Design Item                              | Unit       | Spec                | Achieved |
|----|------------------------------------------|------------|---------------------|----------|
| 1  | SNR                                      | dB         | **66**              |          |
| 2  | $A\beta_{settle}$ (loop setting)         | dB         | **66**              |          |
| 3  | $A_{settle}$ (amplifier settling)        | dB         | **> 78**            |          |
| 4  | $T_{settle}$ (to required accuracy)      | ns         | **25**              |          |
| 5  | $T_{30\,\mathrm{dB}}$                    | ns         | ---                 |          |
| 6  | $T_{38.6\,\mathrm{dB}}$                  | ns         | ---                 |          |
| 7  | $\tau = T_{38.6\,\mathrm{dB}} - T_{30\,\mathrm{dB}}$ | ns | ---            |          |
| 8  | Power dissipation (amplifiers only)      | mW         | **< 3**, low as poss|          |
| 9  | $I(V_{dd})$ (amps only, no biasing)      | mA         | **< 1.7**, low as poss |       |
| 10 | Total effective $kT/C$ noise at output   | µV$_{rms}$ | free                |          |
| 11 | Total integrated amplifier noise         | µV$_{rms}$ | free                |          |
| 12 | Total integrated noise (10 kHz–100 GHz)  | µV$_{rms}$ | free                |          |
| 13 | Input step voltage                       | mV         | **$V_{out}/4$**     |          |
| 14 | Output step voltage                      | V          | **free** (you choose) |        |
| 15 | $C_{in}$                                 | pF         | ---                 |          |
| 16 | $C_{fb}$                                 | pF         | ---                 |          |
| 17 | $C_{load}$                               | pF         | **= $C_{in}$**      |          |
| 18 | $C_{CM}$                                 | pF         | ---                 |          |
| 19 | $R_{fb}$                                 | GΩ         | big                 |          |
| 20 | $C_{big}$                                | nF         | big                 |          |
| 21 | $\mathrm{FoM}_{lin} = 2\pi \cdot P \cdot \tau / \mathrm{SNR}_{lin}^2$ | J |   |          |
| 22 | $\mathrm{FoM}_{dB} = \mathbf{-}10\log_{10}(\mathrm{FoM}_{lin})$ (positive) | dB |          |          |

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
