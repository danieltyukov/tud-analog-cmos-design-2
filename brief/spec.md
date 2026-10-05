# EE4525 resit: specification, rules, formulas (source of truth)

Distilled from `assignment.pdf` (27 May 2026 version), `faq.txt`, `clarifications.md` and the
resit submission form. If anything here conflicts with those, the originals win; fix this file.

| | |
|---|---|
| Student | Daniel Tyukov, **5714699** |
| Deadline | **Sunday 8 November 2026, 23:59** (Amsterdam) |
| Submit | form at https://edu.nl/7turd (Google Apps Script page "EE4525-RESIT"), PDF named `5714699.pdf`, **max 2 submissions**, click Submit and wait for the confirmation page |
| Grade | set by **lowest amplifier power while meeting every spec**. Pass needs $P < 3\,\mathrm{mW}$ and FoM $> 170\,\mathrm{dB}$; best designs go below $0.3\,\mathrm{mW}$ |
| History | attempt 1: 2.04 mW but missed settling, **3.5 (fail)**. Friend: 1.24 mW, all specs met, **7.5** (`example/`) |

## 1. Fixed test circuit (do not change)

- Fully differential switched-capacitor amplifier, **amplification phase only**: a differential
  input step through $C_{in}$ into the virtual ground, $C_{fb}$ in feedback, $C_{load}$ on each output.
- $C_{in}/C_{fb} = 4$ exactly (residue gain 4). No series R with $C_{fb}$, no other change to the network.
- $C_{load} = C_{in}$. $R_{in}$, $R_{fb}$ very large with $R_{fb}/R_{in} = C_{in}/C_{fb}$, only for DC bias;
  mark them `noiseless` (FAQ) and keep $1/(2\pi R_{fb} C_{fb}) \ll 10\,\mathrm{kHz}$ (use $\mathrm{G\Omega}$).
- $\beta_{ideal} = C_{fb}/(C_{in}+C_{fb}) = 0.2$, $20\log_{10}(1/\beta) = 13.98\,\mathrm{dB}$.
- Input step (differential) $= V_{out,step}/4$. Output swing is free to choose.

## 2. Specifications (all must hold at the same design point)

| # | Spec | Value |
|---|---|---|
| S1 | SNR (amp noise 10 kHz to 100 GHz + kT/C, vs sine of peak $V_{out,step}$) | $\geq 66\,\mathrm{dB}$ |
| S2 | $A\beta$ (loop settling accuracy) at $t_{step}+25\,\mathrm{ns}$ | $\geq 66\,\mathrm{dB}$ |
| S3 | $A$ (amplifier settling accuracy) at $t_{step}+25\,\mathrm{ns}$ | $> 78\,\mathrm{dB}$ |
| S4 | stays settled after 25 ns; first significant ringing peak after 25 ns; at most 2 ringing cycles | TA rule |
| S5 | Power $= 1.8\,\mathrm{V} \times \overline{I(V_{dd})}$, amplifier only | $< 3\,\mathrm{mW}$, **minimise** |
| S6 | $\mathrm{FoM_{dB}}$ | $> 170\,\mathrm{dB}$ |

`tools/evaluate.py` adds small robustness margins (SNR +0.05 dB, A/Aβ +0.3 dB, settled by 24.8 ns)
so a re-simulation by the grader (likely LTspice 24) cannot flip a pass. Do not add more margin than
that: **over-design costs power, and power is the grade.**

## 3. Design rules

- Devices: **NMOS, PMOS, R, C only.** Ideal switches allowed for a switched-capacitor CMFB; an ideal
  voltage source allowed as the CM reference. No ideal controlled/independent sources in the amplifier
  (anything is allowed inside the bias block). Probes must not drive circuit nodes.
- **Real CMFB is mandatory** (even if the sim works without it). Real gain-boosters if boosting is used.
- **Single $V_{DD} = 1.8\,\mathrm{V}$** for every amplifier block (core, 2nd stage, CMFB, boosters).
  Bias block on a separate `Vddb` (excluded from power); decouple every bias line with a big cap.
- Model `log018.l` section `TT` (has 1/f noise). **Never** `logic018 no1of.l`.
- Integer multiplier `m` only. NMOS bulks to ground (single substrate); PMOS bulks free.
- Resistors at most a few $\mathrm{M\Omega}$ (except $R_{in}$/$R_{fb}$). Total capacitance in the main
  circuit $< 1000\,\mathrm{pF}$ (bias decoupling excluded).
- Folded cascode: input-pair currents must not exceed the cascode-branch currents.
- LTspice is the required simulator (graders may ask for the files).

## 4. Measurement definitions (implemented in `tools/metrics.py`, verified on `example/`)

- $A(t) = 20\log_{10}\dfrac{V_{out,max}}{|V(vip)-V(vin)| + 1\,\mathrm{nV}}$ with $V_{out,max} = V_{out,step}$ fixed.
- $A\beta(t) = 20\log_{10}\dfrac{V_{out,max}}{|V_{out,max} - V_{od}(t)| + 1\,\mathrm{nV}}$, so it **starts at 0 dB**
  (TA requirement). Plot $A$ and $A\beta$ **in one figure** with the 25 ns line.
- The gap between the curves right after the step is $20\log_{10}(1/\beta_{act})$. Input-pair parasitic
  capacitance at the summing node gives $\beta_{act} = C_{fb}/(C_{in}+C_{fb}+C_p) < \beta_{ideal}$, a gap
  above 13.98 dB (the friend's design: 14.81 dB, $\beta_{act} = 0.182$). The TA note says the actual
  $\beta$ is "typically higher, if lower something is wrong"; read that as the $1/\beta$ gap being
  higher, explain the $C_p$ mechanism explicitly, and report both numbers. Explain this in the report.
- $\tau = T_{38.6\,\mathrm{dB}} - T_{30\,\mathrm{dB}}$ on the $A\beta$ curve (one e-fold $= 8.69\,\mathrm{dB}$).
- Settling time = last instant either curve is below its spec; "floor" = worst value after 25 ns.
- Power: average $I(V_{dd})$; the tool reports $\max(I_{quiescent}, \overline{I}_{[t_{step},\,t_{step}+25\,\mathrm{ns}]})$.
  State the window in the report.
- Amplifier noise: `.noise V(vop,von) <src> dec 100 10k 100G`, integrate $v_{onoise}^2$ over 10 kHz to 100 GHz.
- kT/C at the output (Cin, Cfb, Cload only; TA clarification), per side
  $\frac{kT C_{in}}{C_{fb}^2} + \frac{kT}{C_{fb}} + \frac{kT}{C_{load}} = (16+4+1)\frac{kT}{C_{in}}$, differential
  $v_{n,kTC}^2 = 42\,kT/C_{in}$ ($T = 300.15\,\mathrm{K}$). Attempt 1 used $50\,kT/C_{in}$ (over-conservative).
- $\mathrm{SNR} = 20\log_{10}\dfrac{V_{out,step}/\sqrt{2}}{\sqrt{v_{n,amp}^2 + v_{n,kTC}^2}}$ ($V_{out,step}$ = differential peak).
- $\mathrm{FoM_{lin}} = 2\pi P \tau / \mathrm{SNR_{lin}}^2$ with $\mathrm{SNR_{lin}}^2 = 10^{\mathrm{SNR_{dB}}/10}$;
  $\mathrm{FoM_{dB}} = -10\log_{10}\mathrm{FoM_{lin}}$ (positive). $> 170\,\mathrm{dB}$ means $< 9.5\times10^{-18}\,\mathrm{J}$.
- NEF (report an estimate and state the formula): $v_{n,amp}^2 = \mathrm{NEF}\cdot 2kT/(\beta C_{L,eff})$,
  $C_{L,eff} = C_{load} + (1-\beta)C_{fb}$ (the factor 2 is the differential output). The friend used the
  same form without the 2 (got 20; ours gives 10 for the same design).
- EE4520 baseline for Deliverable 6 (`reference/ee4520/`): $P = 0.1119\,\mathrm{mW}$, $\tau = 497.4\,\mathrm{ns}$,
  SNR 80.85 dB, $\mathrm{FoM} = 175.20\,\mathrm{dB}$.

## 5. Report: compulsory structure (8 pages, one item per page, this order)

| Page | Content |
|---|---|
| 1 | Title: name, student number, "EE4525 2026" |
| 2 | D1 table of results: all 22 rows (layout of assignment p. 6) |
| 3 | D2 schematic with **all node voltages** (drawn, not a simulator screenshot); CMFB and boosters on separate readable sheets |
| 4 | D3 schematic with **all branch currents** (same style) |
| 5 | D4 settling plot: $A$ and $A\beta$ in one figure, $A\beta$ from 0 dB, 25 ns marker |
| 6 | D5 output-noise density 10 kHz to 100 GHz with the integrated value shown |
| 7 | D6 step-by-step FoM difference EE4520 vs EE4525 |
| 8 | Short explanation, at most 1 page: every feature of the D4 plot; why this architecture (incl. CMFB); sizing for noise (incl. 1/f) and settling, output swing and capacitor choice; dominant noise devices and NEF; how it is biased; actual vs ideal $\beta$ |

If D2/D3 need separate sheets for CMFB/boosters, keep each deliverable to one page (several small
figures on the page) rather than spilling over. No contents page, no appendices.

## 6. Submission form fields (fill exactly as in the D1 table)

Student number, first name, last name, PDF upload, then Achieved for: SNR [dB], Abetasettle [dB],
Asettle [dB], Tsettle [ns], T30dB [ns], T38.6dB [ns], tau [ns], Power dissipation [mW], I(Vdd) [mA],
Total effective kT/C-noise at output [uVrms], Total integrated amplifier noise [uVrms], Total
integrated noise [uVrms], Input step voltage [mV], Output step voltage [V], Cin [pF], Cfb [pF],
Cload [pF], CCM [pF], Rbig [GOhm], Cbig [nF], FoM_lin [J], FoM_dB [dB].
`results/latest.json` holds every value; the human submits (never the agent).
