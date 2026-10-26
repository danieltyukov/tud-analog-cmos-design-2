# Design strategy for minimum power (research brief, October 2026)

> **Partly superseded (13 Oct 2026).** The TA rejected the class-AB / current-reuse direction of
> sections 3 to 4 as too complicated and its FoM (183 dB) as implausible. Attempt 3 uses the simple
> telescopic + common-source two-stage amplifier with a replica bias (`brief/ta-feedback-2026-10-12.md`).
> Sections 1, 2, 5 and 6 (what binds, noise vs swing, risks, staged procedure) still apply. The
> power table in section 3 is a model, not a target; the TA's FoM ceiling of about 176 to 177 dB
> implies roughly 0.6 to 1 mW for this course's specs.

From a first-principles power model calibrated on the friend's design (predicted 0.61 mA vs actual
0.69 to 0.72 mA) and on attempt 1 (1.26 vs 1.135 mA). **Treat every power estimate as ±25 %.**
Device numbers come from `tools/gmid.py` (LTspice tables for log018.l). Verify everything by simulation.

## 1. What actually binds

- $A = A\beta + 20\log_{10}(1/\beta_{act})$ with a gap of about 14.5 to 14.8 dB (input-pair $C_p$). So
  $A\beta \geq 66$ already forces $A \gtrsim 80.8\,\mathrm{dB}$: **the 78 dB spec never binds, Aβ does.**
- The settled floor is static: $1/(A_0\beta)$, with $A_0$ evaluated **at the final output voltage**. Need
  $A_0(\pm V_{step}/2) \gtrsim 84\,\mathrm{dB}$. The friend's output NMOS ended 15 mV from triode at the
  final output, collapsing $A_0$ to 80.8 dB: check `.op` at the settled state, both polarities.
- Error budget at 0.5 dB margin: $\varepsilon = 10^{-66.5/20} = 4.7\times10^{-4}$ = static (about
  $2.5\times10^{-4}$ at $A_0\beta = 72\,\mathrm{dB}$) + dynamic (about $2.2\times10^{-4}$), within 24 ns.
- **Single-pole settling needs about 7.7 τ; attempt 1 (τ = 3.29 ns) was infeasible by construction.**
- Two-stage with $p_2 \approx 4\omega_c$ (critically damped, loop PM about 76°): error $\propto (1+x)e^{-x}$,
  $x = 2\omega_c t$, needs $x \approx 10$, so about $6/\omega_c \leq 24\,\mathrm{ns}$: $f_c \approx 40\,\mathrm{MHz}$,
  GBW 210 to 220 MHz, measured τ about 2.4 to 2.8 ns. The error does not cross zero before 25 ns, which
  satisfies the TA ringing rule by construction.
- Slewing: with a tail-biased input, $V_{lin} = 2/(g_m/I_D)$, the input sees $\beta V_{step}$ at $0^+$,
  $t_{slew} \approx (\beta V_{step}/V_{lin} - 1)/\omega_c$. Keep slewing below about 30 % of the window.

## 2. Noise vs swing (the cheapest knob)

- Allowed total noise $v_{n,tot} \leq V_{step}/(\sqrt{2}\cdot10^{\mathrm{SNR}/20})$; kT/C $= 42kT/C_{in}$.
- Two-stage Miller amplifier noise $\approx \alpha\,kT/C_c$ with $\alpha \approx 18.5$ (calibrated on the friend,
  326 µV at $C_c = 0.72\,\mathrm{pF}$). Attempt 1's folded cascode + boosters had about 3.5x the noise
  factor, which forced $C_{in} = 5\,\mathrm{pF}$.
- All terms scale as kT/C, so $C \propto 1/V_{step}^2$, and power falls between $1/V$ and $1/V^2$ with swing.
  Use the largest swing the output stage holds with at least 100 to 150 mV saturation margin:

| Output stage | Per-side swing | $V_{step}$ (diff) |
|---|---|---|
| telescopic | ±0.3 V | 0.6 to 0.7 V |
| folded cascode | ±0.45 to 0.5 V | 0.9 to 1.0 V |
| two-stage push-pull, output devices gm/ID 14 to 16 at L 0.25 µm | ±0.6 to 0.65 V | **1.2 to 1.3 V** |

- Free noise budget the friend wasted: Rin/Rfb not `noiseless` (2 x 77 µV), $R_z$ thermal noise
  (about 60 µV each), $C_c$ too small so amplifier noise dominated kT/C.

## 3. Power floor by architecture (model, SNR 66.3 dB, Aβ 66.5 dB, 24 ns)

| Architecture | $V_{step}$ | $C_{in}$ | I(Vdd) | P |
|---|---|---|---|---|
| single-stage telescopic + boosters | 0.6 to 0.7 V | 4 to 6.5 pF | 1.1 to 1.7 mA | 2.0 to 3.0 mW |
| folded cascode, current reuse, boosted (attempt 1) | 0.9 to 1.0 V | 3 to 4 pF | 1.0 to 1.3 mA | 1.9 to 2.3 mW |
| two-stage, class-A output | 1.2 to 1.3 V | 1.6 to 1.9 pF | 0.65 to 0.75 mA | 1.2 to 1.35 mW |
| **two-stage, class-AB output, tail-biased PMOS input** | 1.2 to 1.3 V | 1.5 to 1.8 pF | **0.30 to 0.35 mA** | **0.55 to 0.62 mW** |
| + current-reuse input with tails | 1.2 to 1.3 V | 1.3 to 1.5 pF | 0.28 to 0.31 mA | 0.50 to 0.56 mW |
| class-AB output + tail-less stacked (inverter-like) input | 1.2 to 1.3 V | 1.3 to 1.5 pF | 0.17 to 0.20 mA | 0.31 to 0.36 mW |

Single-stage designs have a floor near 1.9 mW here: do not use them. Current reuse with tails buys
little (doubling gm/I halves $V_{lin}$ and lengthens slewing); it pays only if the input is also class-AB.

## 4. Recommended architecture

**A (primary, robust): two-stage Miller, PMOS-input telescopic stage 1, class-AB push-pull output,
no gain boosting.**
- Stage 1: PMOS pair (gm/ID 16 to 18, L 0.25 to 0.36 µm; keep L at or below 0.36 µm or $C_{gg}$ cuts β),
  PMOS cascodes, NMOS cascoded loads with long L (1 to 2 µm, gm/ID 8 to 10) for gain and low 1/f.
  About 60 to 70 dB. Stage 2 about 30 to 36 dB. If $A_0$ is short, lengthen L (free in power).
- Class-AB drive: stage 1 drives the NMOS output gate directly; the PMOS output gate through a
  capacitive level shift (0.5 to 1 pF, DC-biased through about 2 MΩ, corner below 100 kHz) [Ryu 2007].
  Alternative: Monticelli / Hogervorst floating class-AB control (needs a folded stage 1: extra branch).
- Compensation: current-buffer (cascode) Miller [Ahuja 1983; Hurst 2004]: no RHP zero, no $R_z$ noise,
  higher $p_2$. Place $p_2 \approx 4 f_c$. No output snubber (it loads the output).
- CMFB: continuous time. 1 to 2 MΩ resistive sensing per side with 30 to 50 fF in parallel, a 5 to 10 µA
  diff pair against the 0.9 V reference, acting on 20 to 30 % of the stage-1 loads. CM crossover about
  0.3 to 0.5 $f_c$, PM above 60°. Keep the output CM excursion during the step below about 50 mV.
  Avoid SC-CMFB here: its caps load the outputs and it needs multi-cycle simulation.

Starting point (model): $V_{step} = 1.2\,\mathrm{V}$ (outputs 0.30 to 1.50 V), $V_{in,step} = 300\,\mathrm{mV}$,
$C_{in} = C_L = 1.8\,\mathrm{pF}$, $C_{fb} = 0.45\,\mathrm{pF}$, $C_c \approx 0.9$ to $1.0\,\mathrm{pF}$ per side,
kT/C 311 µV, amplifier noise at most 265 µV, $g_{m1} \approx 1.2\,\mathrm{mS}$ per input device
($I_D \approx 70\,\mathrm{\mu A}$, tail about 140 µA), $g_{m2} = g_{mn}+g_{mp} \approx 2.8$ to $3.0\,\mathrm{mS}$ per side
at about 90 to 100 µA quiescent, CMFB at most 10 µA. Total about 0.34 mA (0.6 mW), FoM about 176 dB.
Aggressive: 0.25 mA (0.45 mW).

**B (stretch, only after A passes): class-AB current-reuse input** (stacked NMOS+PMOS pairs with
capacitively level-shifted gates [Ryu 2007], or a flipped-voltage-follower / adaptive-bias input
[López-Martín 2005]). Model 0.31 to 0.45 mW. Risk: tail-less inputs are very CM and supply
sensitive (attempt 1: 20 mV input-CM error moved I(Vdd) by 180 µA); the CMFB must also set the
input-stage current; validate at ±50 mV CM offset.

Not recommended: single-stage anything; ring amplifiers (need switched offset storage; ringing
collides with the TA rule).

## 5. Main risks and how to catch them

| Risk | Check |
|---|---|
| ringing peak before 25 ns (an $R_z$ doublet can cause it) | `evaluate.py` first-peak check, `robust.py` |
| CMFB disturbing differential settling (class-AB currents are CM-asymmetric) | output CM excursion during the step < 50 mV |
| 1/f noise: NMOS KF 4e-29, AF 0.83, EF 0.825; PMOS KF 6.1e-28, AF 1.05, EF 1.25 | per-device `.noise` contributions; integrate 10 kHz to 1 MHz separately. NMOS loads need L at or above 2 µm and low gm/ID |
| β loss from input $C_{gg}$ (131 fF at L 0.25 µm, 265 fF at 0.36 µm, about 500 fF at 0.5 µm for 1.2 mS) | `beta_actual` in `evaluate.py`; keep it above 0.175 |
| headroom at the extremes | `.op` at the settled state for both polarities, margins ≥ 100 mV |
| power window ambiguity (class-AB draws extra current while slewing) | report the window; `evaluate.py` uses max(quiescent, 25 ns window) |

## 6. Staged procedure (each stage has a gate)

0. `uv run tools/selftest.py` passes.
1. Budget: pick $V_{step}$, $C_{in}$, $C_c$, $f_c$, $A_0$ (with `tools/metrics.py budget`). Gate: paper SNR ≥ 66.3 dB using α = 18.5.
2. Size from tables: `tools/gmid.py size/table`. Input PMOS gm/ID 16 to 18; loads 8 to 10 (L 1 to 2 µm);
   cascodes 12 to 14; output devices 14 to 16 (L 0.25 µm). Gate: margins ≥ 100 mV, $\beta_{act}$ ≥ 0.175 on paper.
3. Loop AC (`design/templates/bench_loop.cir`, real CMFB in place). Gate: $f_c$ within ±10 %, PM 72 to 78°,
   no peaking or doublet below $3f_c$, $A_0$ ≥ 90 dB at mid-swing, CM loop PM ≥ 60°.
4. `.op` at the final state, both polarities (`tools/lt.py op`). Gate: margins ≥ 100 mV, $A_0$ ≥ 84 dB at $\pm V_{step}/2$.
5. Transient + noise (`tools/evaluate.py`). Gate: every check PASS.
6. Power descent: step bias currents down 3 to 5 % at a time (`lt.py sweep`, then `optimize.py`), re-placing
   $p_2$ each time; stop when the first margin reaches its floor. Then raise $C_c$, lower $C_{in}$, raise
   $V_{step}$ while $A_0$ at the extremes holds.
7. `tools/robust.py` passes on the final drawn `.asc`.

Margins (cost about 5 % power, a missed spec costs the grade): SNR +0.2 to 0.3 dB, Aβ floor +0.3 to
0.5 dB, settled by 24.0 to 24.5 ns, A floor ≥ 79 dB, saturation margin ≥ 50 mV at the extremes.

## 7. Grading model (one data point, low confidence)

grade ≈ 6 + 4·log10(3 mW / P): 7.5 at 1.24 mW (friend), 8.8 at 0.6 mW, 9.3 at 0.45 mW, 10 at 0.3 mW.
Attempt 1 would have scored about 6.7 had it met spec; missing a spec dominates everything.

## References

1. Bult & Geelen, JSSC 25(6) 1990, https://doi.org/10.1109/4.62165 (gain boosting, doublets)
2. Yang & Allstot, TCAS 37(3) 1990, https://doi.org/10.1109/31.52726 (fast-settling op amps)
3. Monticelli, JSSC 21(6) 1986, https://doi.org/10.1109/JSSC.1986.1052645 (class-AB control)
4. Hogervorst et al., JSSC 29(12) 1994, https://doi.org/10.1109/4.340424 (two-stage class-AB)
5. Ahuja, JSSC 18(6) 1983, https://doi.org/10.1109/JSSC.1983.1052012 (current-buffer compensation)
6. Hurst et al., TCAS-I 51(2) 2004, https://doi.org/10.1109/TCSI.2003.820254 (fully differential, cascode compensation)
7. Ryu, Song, Bacrania, JSSC 42(3) 2007, https://doi.org/10.1109/JSSC.2006.891718 (current reuse, 0.18 µm; PDF in `reference/papers/`)
8. López-Martín et al., JSSC 40(5) 2005, https://doi.org/10.1109/JSSC.2005.845977 (super class-AB OTA)
9. Schreier et al., TCAS-I 52(11) 2005, https://doi.org/10.1109/TCSI.2005.853909 (SC thermal noise)
10. Silveira, Flandre, Jespers, JSSC 31(9) 1996, https://doi.org/10.1109/4.535416; Jespers & Murmann, *Systematic Design of Analog CMOS Circuits*, 2017 (gm/ID)
11. Bult, ESSCIRC 2000, https://ieeexplore.ieee.org/document/1471230 (power vs dynamic range)

Textbooks: Carusone, Johns & Martin 2nd ed. (two-stage compensation, SC settling); Razavi 2nd ed. ch. 10 to 11.
Uncertain: ±25 % model accuracy, the grade mapping, the class-AB-input floor (not simulated), hand 1/f
estimates, the TA's β wording.
