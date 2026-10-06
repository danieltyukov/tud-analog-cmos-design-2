# Notes on six IEEE papers for the EE4525 resit (October 2026)

Purpose: extract what is applicable to the v13 residue amplifier (CR topology, 0.2375 mW) and turn it
into at most three testable experiments. All six papers were read in full (text plus rendered figures,
tables and equations). Formulas are written as plain text in code spans.

Sources for the v13 numbers used below: `results/latest.json` (tag final), `results/final/op.json`
(device operating points), `report/generated/extra.tex` (report_extra: loop, noise split, currents),
`results/final/d5_noise.png` (noise density) and `PROGRESS.md`. No simulation was run for this note;
the only computations are hand formulas evaluated in Python (`notes_calc.py` in the session scratchpad).

## 0. Summary

| Paper | Verdict for this design |
|---|---|
| Akter et al., JSSC 2018 | Core tricks (split Cin/Cfb biasing, switches, incomplete settling) are forbidden here. Useful as the price list for level-shift capacitors: input-side level shifting with a resistor of a few MΩ would add about 310 µV of output noise. Confirms keeping the input gates DC-coupled. |
| Kim, Song, Roh, IEEE Access 2020 | Not applicable: its slew enhancement acts on current-mirror diodes and our signal path has no mirrors; its adaptive-bias auxiliary pair adds Cp and dominant flicker noise. Our small-signal FoM is already about 1.8x theirs; the gap is in slewing. |
| López-Martín et al., JSSC 2005 | The published input stages (FVF batteries, CMS, WTA) cost +50 % to +75 % static power and summing-node capacitance. The underlying adaptive-bias idea transfers for free: the NMOS tail node already acts as a max detector during the step. Basis of experiment E2. |
| Hurst et al., TCAS-I 2004 | Explains our loop: the CR stage is their Fig. 3 case (Cc into the cascode node of an input device) on both halves, so it has a RHP/LHP zero pair (about ±360 MHz) and a complex non-dominant pair (about 170 MHz), and no LHP-zero shelf. The v01 shelf was their Fig. 2 case. Mirror-gain and separate-buffer variants cost more current than they save. |
| Giustolisi, Palumbo, TCAS-I 2021 | Directly applicable as analysis (their footnote covers a two-stage Ahuja loop). In their terms v13 runs at NST 0.76 with a small-signal part near their optimum (about 0.49) and a slew term worth 6.2 ns, about 19 % of the single-pole budget. Current reuse halves ν (Gm/Io = Γ instead of Γ/2), so CR is twice as slew-prone as a single pair. |
| Yavari et al., TCAS-II 2005 | No circuit to copy. Its mechanism (stage-1 device in triode during slewing, effective SR below I1/Cc) is present in v13: the output PMOS needs about 240 µA during the slew, v1 falls to about 0.3 V and cuts off the NMOS cascode. Argues for running E1 before E2. |

Ranked experiments (details in section 4):

| Rank | Experiment | Targets | Expected power change | Risk |
|---|---|---|---|---|
| 1 | E1: move unused headroom to the NMOS input and cascode by lowering the input CM (VCMI) and re-biasing vcp, vcn, NMOS tail W; PMOS input bulk to vdd | stage-1 gain (headroom) | -3 % direct; -5 to -9 % if it buys a 1.45 to 1.5 V output step | low |
| 2 | E2: capacitively boosted NMOS tail unit (adaptive bias from the tail-node max detector) | slewing | -4 to -7 % (bound -10 %) | medium |
| 3 | E3: tiny cross-coupled PMOS pair at v1n/v1p (negative conductance) | stage-1 gain beyond E1 | -2 to -3 % direct, enables the 1.5 V step together with E1 | medium |

Correction to the current diagnosis (section 3): there is no loop-gain shelf in v13 (that was v01).
27 % of the noise above 100 MHz is close to an ideal single pole at fc = 46.6 MHz (28 %); an ideal
two-pole loop at PM 76.8° would put 17 % there, so about 10 points come from the bump of the complex
non-dominant pair (100 to 500 MHz), not from a shelf. The excess factor of 2 in α splits into the BSIM3
NOIMOD=1 thermal term (gm+gmbs+gds, x1.35), a 20 % larger noise bandwidth (that bump), flicker (8 %) and
cascodes (10 %).

## 1. Baseline numbers (v13) used in this note

Current budget (window average I(Vdd) = 132.0 µA, P = 0.2375 mW):

| Part | µA | Share | Scales with |
|---|---|---|---|
| Stage 1 (PMOS tail Mtp, reused by the NMOS pair) | 43.7 | 33 % | gm1, i.e. fc·Cc/β |
| Output stage quiescent (2 x 12.7) | 25.4 | 19 % | gm5 needed for the non-dominant pair |
| CMFB (Mct) | 5.15 | 4 % | CM loop speed |
| Slewing charge drawn from Vdd in the 25 ns window | 57.7 | 44 % | C·ΔV, fixed by Cin and Vstep |

Upper bound of the slewing charge per 25 ns at 0.7 V per output: Cload 46.5 µA, series Cfb (0.336 pF)
9.4 µA, Cc 12.4 µA, sum 68.3 µA. The measured 57.7 µA is lower because the class-AB PMOS on the
falling side drops below its quiescent current.

Stage-1 headroom (from `op.json`, input CM 0.90 V, output CM 0.903 V):

| Device | Vds magnitude (V) | Vdsat magnitude (V) | margin (V) | gm/gds |
|---|---|---|---|---|
| Mtp (PMOS tail), ntp = 1.434 V | 0.366 | 0.158 | 0.208 | 67 |
| M1p (input), nb1 = 1.262 V | 0.172 | 0.094 | 0.078 | 24 |
| Mcp1 (PMOS cascode), v1 = 0.573 V | 0.689 | 0.164 | 0.525 | 79 |
| Mcn1 (NMOS cascode), na = 0.430 V | 0.143 | 0.086 | 0.057 | 19.5 |
| M1n (input), ntn = 0.300 V | 0.130 | 0.108 | 0.022 | 12.7 |
| Mtn (NMOS tail) | 0.300 | 0.139 | 0.161 | 102 |

v1 is pinned at Vgs(Mon) = 0.573 V. Output resistance at v1: NMOS side `gm_cn·ro_cn·ro_1n ≈ 19.5 x 37 kΩ
≈ 0.73 MΩ`, PMOS side `≈ 79 x 70 kΩ ≈ 5.5 MΩ`, total ≈ 0.64 MΩ, A1 ≈ 0.685 mS x 0.64 MΩ ≈ 53 dB.
The NMOS side sets about 88 % of the stage-1 output conductance, while about 0.36 V of spare headroom
sits in the PMOS cascode and about 0.1 V in the NMOS tail margin.

Noise decomposition (amplifier noise 360.3 µV, α = v²·Cc/kT = 13.9, ideal `2γ/β` = 7.0 with
β = 0.415/(1.66+0.415+0.106) = 0.190):

| Component (both sides) | Share of amp noise power | Note |
|---|---|---|
| Input devices, thermal | 81 % | 1.61x ideal = 1.35 (NOIMOD=1 counts gm+gmbs+gds) x 1.20 (noise bandwidth) |
| Input devices, flicker | 8 % | NMOS input 71 µV vs PMOS 19 µV per device |
| Cascodes | 10 % | NMOS 63 µV, PMOS 48 µV per device |
| Everything else | 1 % | tails, output stage, CMFB |

Check of the input-device numbers: predicted per device with `8kT/3·(gm+gmbs+gds)/gm1²·(1/β)²·(π/2)fc`
is 147 µV (m1n) and 150 µV (m1p); measured thermal parts (flicker removed) are 161 and 164 µV, so the
remaining factor is a noise bandwidth 1.19 to 1.21 times the two-pole ideal `(π/2)·fc`.
The log018 model is BSIM3v3.2 with `NOIMOD = 1` (SPICE2 thermal noise `8kT(gm+gds+gmbs)/3`); the
gmbs/gm ratios are 0.25 (m1n) and 0.34 (m1p), which is where the x1.35 comes from.

Slew decomposition (Giustolisi model, section 2.5): ε = 4.84e-4 (|ln ε| = 7.63), GBW = 2π·46.6 MHz,
per side Gm = gmn + gmp = 0.685 mS, Io = 43.7 µA (full tail steered), Y = 0.7 V per output:
`ν = Io/(β·Gm) = 0.335 V`, `Y/ν = 2.09`, slew term `Y/ν - 1 + ln(Y/ν) = 1.82`, i.e. 6.2 ns.

Loop (report_extra): fc 46.6 MHz, PM 76.8°, GM 19.6 dB, T0 72.3 dB at mid and 65.9 dB at ±0.7 V outputs,
Aβ at the end of the run 71.6 dB (static error about 2.6e-4, i.e. 54 % of the 4.84e-4 budget),
CM loop 12.0 MHz / 82°, CM excursion 49.8 mV at 3.2 ns, Cp 106 fF.

## 2. Paper notes

Each paper: A = technique, equations, reported numbers, mechanism; B = applicability to v13.

### 2.1 Akter, Sehgal, van der Goes, Makinwa, Bult, IEEE JSSC 2018

M. S. Akter et al., "A 66-dB SNDR pipelined split-ADC in 40-nm CMOS using a class-AB residue amplifier,"
IEEE J. Solid-State Circuits, vol. 53, no. 10, pp. 2939-2950, Oct. 2018. DOI 10.1109/JSSC.2018.2859415.

**A. Technique.** Single-stage push-pull residue amplifier: per half circuit one NMOS and one PMOS
common-source device with grounded sources (an inverter), drains tied to the output, no tail. Both
devices give gain at one bias current (gm reuse), there is no slew limit and the input pair is linear by
the square law. The two gates need different DC levels. Instead of extra switched level-shift capacitors
CLS, the sampling capacitor CS and the feedback capacitor CF are each split in two halves: one half of
each goes to the NMOS gate and one to the PMOS gate, and switches store VBN and VBP on them during a
short reset phase. The amplifier is pseudo-differential; CM signals are stopped by floating the sampling
network CM during sampling. Incomplete settling: CS/CF = 4 is used for a gain of 2 so the target is
reached at tA/τ of about 1 to 2; the gain error is detected digitally (split ADC) and corrected by
trimming the amplifier bias current (9-bit current DAC, 80 nA LSB, ±25 % range).

Key equations:
- `Geff(tA) = [Aβ/(1+Aβ)]·(CS/CF)·(1 - exp(-tA/τ))` (1)
- `Pamp ∝ (CL/tA)·(tA/τ)·(1 + 2/(1 - exp(-tA/τ)))` (2)
- `Pn = (1 + CS/CF)·γkT/CL·(1 - exp(-2tA/τ)) + kT/CL·exp(-2tA/τ)` (3)
- with explicit level shifters: `Pnoise = (kT/CS)(CS/CF)² + kT/CF + γ(kT/CL)/β + 2(kT/CLS)(1/(2β))²` (5)
- attenuation `α = 1 - VG/VX = (CP + CGS)/(CLS + CP + CGS)` (6), `β = CF/(CS + CF + 2CX)` (7),
  `CX = CLS(CP + CGS)/(CLS + CP + CGS) + CP` (8)
- split mismatch gain error `εge = (m/2)²·CS/(CS + CF)` (10)
- grounded-source pair `IDIFF = βn·VI·(VBN - Vth)` (17), linear, versus the tail pair (15)

Reported: 40 nm CMOS, 1 V, 12-bit pipelined split ADC (nine 1.5-bit stages plus 5-bit flash), 53 MS/s,
1.5 Vpp,diff full scale, SNDR 66 dB and SFDR 77.3 dB near Nyquist, 9 mW total (2.8 mW analog, 6.2 mW
clock), residue amplifiers 0.83 mW, calibration converges in 12,000 cycles, INL -0.7/+0.6 LSB,
DNL -0.24/+0.14 LSB, 0.76 mm², Schreier FoM 160.7 dB (165.8 dB on analog power only). Fig. 2: with CLS
(CP = 5 % of CLS) at least 63 % more power is needed for the same bandwidth and noise. Removing CLS is
worth about 1.6x, incomplete settling about 4x.

Mechanism: no tail (no slewing, gm reuse), no CLS (no extra kT/C, no attenuation, no β loss), lower
bandwidth through incomplete settling.

**B. Applicability.**
- Cannot carry over: splitting Cin/Cfb (feedback network fixed), switches and clock phases (only an
  SC-CMFB may switch, single-phase test), incomplete settling (the Aβ floor after 25 ns is checked, so the
  settled value must be within 4.84e-4), pseudo-differential operation (our real CMFB acts through the
  tail; without a tail there is no CM rejection).
- Input-gate level shift with a resistor instead of switches (the only legal way to give the NMOS and
  PMOS input gates different DC levels): a bias resistor Rb of 3 MΩ with 0.55 pF at the gate has its
  corner at 96 kHz, so 93 % of kT/C (84 µV rms at the gate) lies inside the 10 kHz to 100 GHz band. It
  drives half of the input gm, is multiplied by 1/β and adds per side, giving about 310 µV at the
  differential output, comparable to the whole 360 µV amplifier budget. Even 2 pF still gives 150 µV;
  only a GΩ resistor would be quiet enough (44 µV), which the "a few MΩ" rule forbids. Akter's own
  Fig. 2 adds +63 % power for CLS at the virtual ground. Conclusion: keep both input gates on the
  summing node (as now).
- What carries over: (1) the push-pull gm-reuse principle, already present in the CR stage and the
  class-AB output; (2) the CLS cost model, applied to our output stage: Cls = 0.52 pF drives the 39 fF
  gate of Mop, transmission `Cls/(Cls + Cgg) ≈ 0.93`, and the series combination (about 36 fF) is about
  half of the v1 node capacitance CA (about 66 fF). Our Cls is not at the virtual ground, so β is not
  affected; its cost is through CA (sets the non-dominant pair, see Hurst) and the 7 % attenuation. Its
  Rb noise is suppressed by the stage-1 gain. (3) The linearity result is not relevant (no THD spec).
- Net effect on power: none directly. It supports the present architecture and rules out input-side
  class-AB with level shifters.

### 2.2 Kim, Song, Roh, IEEE Access 2020

J. Kim, S. Song, J. Roh, "A high slew-rate enhancement class-AB operational transconductance amplifier
(OTA) for switched-capacitor (SC) applications," IEEE Access, vol. 8, pp. 226167-226175, 2020.
DOI 10.1109/ACCESS.2020.3044608.

**A. Technique.** Single-stage symmetrical (current-mirror) class-AB OTA. The main pair M1/M2 and an
auxiliary pair M3/M4 share the tail M39. The auxiliary pair feeds diodes M11/M12 that drive the
cross-coupled current sources M9/M10, which inject extra current into the mirror diodes M13/M14 only
when the differential input is large (adaptive bias, after Roh 2006). The diode currents are mirrored
(M33/M34) to cascoded output branches. New part: slew-rate-enhancement transistors M15 to M18 in series
with the sources of the mirror diodes, held in triode by VBCM. At rest their Vds is about 2 mV, at large
current up to 320 mV, which raises the diode gate voltage and so the mirrored output current (a
nonlinear source degeneration that raises the mirror gain at high current). A current-reference CMFB
(replica of M7/M13/M17) sets VBCM so that the branch ratios hold over PVT.

Key equations: `Av = Gm·Rout`; `Gm = (3/2)gm1,2(A/B) + (3/2)gm3,4(C/D)(A/B) = (3/2)(It/VOD)(A/B)(B+2C)/(B+C+D)`;
`Rout = Ro1 ∥ Ro2 ∥ Ro3` with each `Ro = gm·ro·ro`; `FoMS = GBW·CL/P`, `FoML = SR·CL/P`.

Reported (OTA by simulation, 0.18 µm, 1.8 V, CL 8 pF): DC gain 67.5 to 68 dB, PM 48.2°, UGBW 172.5 MHz,
SR 212.5 V/µs (conventional class-AB 52.9 V/µs), 0.1 % settling 4.2 ns (conventional 21 ns), 1.18 mW
(conventional 1.22 mW), FoMS 1169 MHz·pF/mW, FoML 1440 (V/µs)·pF/mW, 0.036 mm². Corners: UGBW 131 to
214 MHz, PM 43.6° to 55.3°. Flicker shares: auxiliary pair M3/M4 27.6 % each, M11/M12 14.6 % each, main
pair 4.7 % each. Measured third-order CIFF SC delta-sigma (12.8 MHz, OSR 256, 25 kHz, chopped first
integrator): SNR 90.7 dB, SNDR 90.1 dB, DR 92.1 dB, 1.9 mW total.

Mechanism: low quiescent current in the output branches and large dynamic current only while slewing.

**B. Applicability.**
- Our signal path has no current mirrors: stage 1 drives the cascodes directly and stage 2 is driven
  directly from v1 (NMOS) or through Cls (PMOS). The SRE degeneration and the mirror-ratio boost have
  nothing to act on. Our output stage already has no fixed current limit (it delivers the about 240 µA
  peak needed during the slew).
- The adaptive-bias auxiliary pair takes tail current, adds gate capacitance at the summing node
  (Cp up, β down) and by their own Fig. 10 dominates flicker noise (55 % from M3/M4). Both hurt a
  noise-limited design.
- Their design style (PM 48°) would fail our "no ringing peak before 25 ns" rule.
- Benchmark: v13 has an open-loop unity-gain frequency of about fc/β = 46.6/0.19 ≈ 245 MHz into about
  2.0 pF (Cload plus series Cfb) at 0.2375 mW, so FoMS ≈ 2000, about 1.8x theirs; FoML ≈ 100 V/µs x
  2.0 pF / 0.2375 mW ≈ 840, below their 1440. Our gap is in slewing, not small-signal efficiency, which is
  consistent with section 2.5.
- Only transferable idea: a device that is nearly idle at rest and conducts only during large signals.
  E2 applies it at the NMOS tail.
- Net: not applicable as published.

### 2.3 López-Martín, Baswa, Ramírez-Angulo, Carvajal, IEEE JSSC 2005

A. J. López-Martín et al., "Low-voltage super class AB CMOS OTA cells with very high slew rate and power
efficiency," IEEE J. Solid-State Circuits, vol. 40, no. 5, pp. 1068-1077, May 2005.
DOI 10.1109/JSSC.2005.845977.

**A. Technique.** Two ideas combined in a simple current-mirror OTA.
1. Adaptive biasing of the input pair, so the pair current is not capped by its quiescent IB. Three
   versions: (a) cross-coupled floating batteries built from flipped voltage followers (FVF): each input
   transistor's source is driven from the opposite input, so the signal hits gate and source and
   `i_d ≈ 2·gm·v_id`; (b) a CM-sensing level shifter on the common source; (c) a winner-take-all (max)
   circuit on the common source, so the common source follows the higher input.
2. Local CMFB (LCMFB) in the active load: the diode loads M6/M7 get their common gate Z from their drains
   X/Y through matched resistors R1, R2. For differential signals Z is an AC ground, so the load is R
   instead of 1/gm (DC gain and GBW rise by about gm5,8·R). For large signals the swing at X or Y directly
   overdrives the output device, the output current grows as Id² (as Vid⁴ with a class-AB input), and no
   replica current is wasted (current efficiency near 1).

Key equations: `GBW = k·gm1,2·gm5,8·RX,Y/(2π·CL)` (1);
`PM ≈ 90° - arctan[k·gm1,2·gm5,8·(R ∥ ro6,7 ∥ ro1,2)²·CGS5,8/CL]` (2);
`Iout ≈ ±(β5,8/2)·(√(2Icm/β6,7) + R·|Id|/2)²` (7);
FVF input `I1 = (β1,2/2)·(√(2IB/β1,2) + Vid)²` (8);
`Iout ≈ ±(β5,8/2)·(√(β1,2/(2β6,7))·|Vid| + R·β1,2·Vid²/4)²` (10);
minimum supply `|VTH| + 3|VDS,sat|` (1.3 V for 0.7 V / 0.2 V); exponential boost in weak inversion (14);
class-A reference `SR = B·IBIAS/CL`, `I_Q = SR·CL·(1 + 1/B)`.

Reported (measured, 0.5 µm, ±1 V, IB = 10 µA, R = 10 kΩ, CL about 80 pF): class-A OTA SR 0.35/-0.4 V/µs,
1 % settling 3.1/3.6 µs, GBW 200 kHz, gain 30 dB, noise 223 µVrms (1 MHz band), 80 µW. FVF version
Fig. 3(a): SR 100/-78 V/µs, settling 29/57 ns, GBW 725 kHz, gain 43 dB, noise 230 µVrms, 120 µW. WTA
version Fig. 3(b): 92/-76 V/µs, 66/62 ns, 410 kHz, 120 µW. CMS version Fig. 3(d): 42/-80 V/µs, 140 µW.
Up to 280x slew rate and 3.6x GBW at the same pair quiescent current.

Mechanism: slewing current scales with Vid² (exponentially in weak inversion) instead of being capped at
IB; LCMFB removes replica-current waste and raises the load impedance for differential signals.

**B. Applicability.**
- Input stages as published: every version adds bias branches (their static power +50 % to +75 % over
  the class-A OTA at equal pair current), adds devices whose noise is in series with the input, and puts
  extra gate capacitance on the summing node (FVF follower gates sit on the opposite input), so Cp up
  and β down. In our stack the NMOS pair has no room for a level shifter (ntn = 0.30 V). Even for the
  PMOS half alone, two FVFs at about 11 µA each cost +22 µA (+17 % of P), more than the at most -10 %
  that removing all slewing could return (section 2.5). Rejected.
- The principle transfers for free: the common source of a differential pair is already a max (NMOS)
  or min (PMOS) detector. During our 0.27 V differential input step the NMOS tail node ntn rises by about
  `|vid|/2 - n·UT·ln2 ≈ 0.133 - 0.025 ≈ 0.11 V`, while in the linear tail of the settling it moves only
  `vid²/(8·n·UT)` (0.35 mV at 10 mV). Coupling that rise through a capacitor to the gate of part of the
  NMOS tail gives class-AB-like tail current with no added quiescent current and no change to the
  small-signal differential circuit (ntn is a differential AC ground). This is E2.
- LCMFB: our stage 1 has no diode loads, so the gain mechanism does not map one-to-one. A resistive
  local CM sense on v1n/v1p driving the CMFB tail unit is DC compatible (v1 CM 0.57 V is close to the
  tail unit Vgs 0.567 V) but only helps if v1 is decoupled from Vgs(Mon) by AC-coupling the NMOS output
  gate, which then needs a new output CM loop through a slow Rb·C path (about 0.5 MHz). High risk, and
  its gain benefit is what E1 gets for free, so not proposed.
- Net: worse as published; the adaptive-bias principle is the basis of E2.

### 2.4 Hurst, Lewis, Keane, Aram, Dyer, IEEE TCAS-I 2004

P. J. Hurst et al., "Miller compensation using current buffers in fully differential CMOS two-stage
operational amplifiers," IEEE Trans. Circuits Syst. I, vol. 51, no. 2, pp. 275-285, Feb. 2004.
DOI 10.1109/TCSI.2003.820254.

**A. Technique.** Four ways to put a current buffer in series with Cc in a fully differential two-stage
opamp, analysed with finite buffer gm and output resistance: Fig. 1 a separate common-gate stage with its
own bias (Ahuja), Fig. 2 Cc into the cascode node of a cascoded first-stage load, Fig. 3 Cc into the
cascode node of a cascoded input pair (or folded cascode), Fig. 4 a differential current mirror with gain
m (cross-coupled to keep the feedback negative), plus mirror variants that cut the CM gain.

Key equations (node A = stage-1 output, node B = buffer input, gm5 = stage-2 gm, gm7 = buffer gm):
- Figs. 1, 2, 4 (m = 1): one LHP zero `z ≈ -gm7/(CB + Cc)` (1, 27); `p1 ≈ -1/(gm5·RL·RoA·Cc)` (2, 28);
  `p2 ≈ -gm5·Cc/((CL + Cc)·CA)` (3, 30); `p3 ≈ -gm7/((CL ∥ Cc) + CB)` (31); p2, p3 real and widely spaced
  only if `gm7 ≫ 4·gm5·Cc·[(CL ∥ Cc) + CB]/[(CL + Cc)·CA]`.
- Fig. 3: the input current enters node B where Cc also connects, so feedforward remains and the zeros
  are `≈ ±√(gm7·gm5/(CA·Cc))` (one RHP, one LHP) (56, 57); when complex `|p2| = |p3| ≈ √(gm7·gm5/(CA·CL))` (58).
- Fig. 4 with mirror gain m and capacitor Cc/m: `z ≈ -gm11/(m·CB + Cc)`, `p2 ≈ -gm5·Cc/((CL + Cc/m)·CA)` (68),
  `p3 ≈ -gm11/([(CL ∥ Cc/m) + CB]·m)` (69); dominant pole unchanged; the CM current gain of the
  differential mirror is unity, so for CM only Cc/m is effective.

Reported: analysis only, checked against HSPICE pole-zero runs; no silicon.

Mechanism: blocking the Cc feedforward removes the RHP zero; disconnecting Cc from the stage-2 input
raises p2 by about Cc/CA relative to plain Miller, so a smaller gm5 (output current) gives the same PM.

**B. Applicability.**
- Classification: the CR stage is the Fig. 3 case on both halves (Cc1/Cc2 into na, the drain of the
  input NMOS; Cc3/Cc4 into nb, the drain of the input PMOS). A current-reuse stage has no passive load,
  so Fig. 2 is not available. The single-pair v01 was the Fig. 2 case (Cc into the NMOS cascode over a
  long-L load): its LHP zero `gm_c/(CB + Cc)` sat below p2 and made the loop gain flat at about
  `β·gm1/gm_c` between them. That was the v01 noise shelf. CR has no such zero.
- v13 numbers (gm5 ≈ gm_on + 0.93·gm_op ≈ 0.40 mS, gm7 ≈ 0.38 mS, CA ≈ 66 fF, CL ≈ 2.0 pF including
  series Cfb, Cc 0.443 pF, CB ≈ 30 fF): zero pair at about ±360 MHz (7.7 fc), |p2,3| ≈ 170 MHz (3.6 fc),
  real-pole condition needs gm7 ≫ 1.7 mS (we have 0.38 mS), so the inner pair is complex. Measured PM
  76.8° and GM 19.6 dB fit a complex but well damped pair. The high-frequency asymptote of A is
  `-gm1/(s·(CL + CB·(1 + CL/Cc)))`, 13.8 dB below the Miller line: this is the -20 dB/decade tail above
  about 2 GHz in D5 and it carries under 1 % of the noise.
- Fig. 1 (separate buffer): extra bias per side only to free gm7; the RHP zero at 7.7 fc is not limiting.
  No.
- Fig. 4 (mirror gain m): the physical Cc/m would cut the Cc part of the slewing charge (12.4 µA) by
  (1 - 1/m), but the mirrors are class-A and must be biased for the slewing current through Cc: about
  `2·(1 + m)·I1/m ≥ 2·I1` extra (> 40 µA) against < 12 µA saved. No.
- Design use: (58) says the inner pair frequency scales as `√(gm7·gm5/(CA·CL))`. To lower the output
  quiescent current (gm5) at a fixed inner-pair frequency, raise gm7 (cascode gm, free in current) or
  lower CA. The PMOS cascode runs at gm/ID 10.3 (0.226 mS) against 17.2 for the NMOS cascode. The running
  r3 optimizer already spans Wcp 5 to 15 µm; if its optimum sits on the 15 µm bound, extend the range to
  about 25 µm. In CA, 36 of the 66 fF is the Cls to Cgg(Mop) series path; Cgg(Mon) is only 5.4 fF.
- Cascode noise in current-buffer compensation (derived here, consistent with Hurst's remark that
  current buffers add input noise): Cc at the cascode source stops the cascode noise from being
  degenerated above fc. The cascode noise reaches the output with a roughly flat density
  `4kTγ·C'²/(gm_c·Cc²)` from about fc up to about `gm_c/C'` (C' = CB plus the Cc part on that node).
  For the NMOS cascode this estimates about 12 % of the NMOS-half input noise over a 300 MHz flat band;
  measured 6.8 %. Same order, so the 10 % cascode share is structural to Ahuja compensation.
- Net: confirms the topology and gives the formulas for reasoning about ko, Wcp, Cls and C1d; no new
  circuit to add.

### 2.5 Giustolisi, Palumbo, IEEE TCAS-I 2021

G. Giustolisi, G. Palumbo, "Design of three-stage OTA based on settling-time requirements including
large and small signal behavior," IEEE Trans. Circuits Syst. I, vol. 68, no. 3, pp. 998-1011, Mar. 2021.
DOI 10.1109/TCSI.2020.3044454.

**A. Technique.** A settling-time-driven design method that includes slewing. Time is normalised to the
loop GBW; the normalised settling time NST compares the settling time with that of a linear single-pole
loop with the same GBW. Slewing is modelled by a saturating transconductor (limit Io) in front of the
dominant integrator. Two-pole loops are described by the separation factor `K = ωs/GBW ≈ tan(PM)`,
three-pole loops by an external factor `Ke = GBWi/GBW` and an internal factor `Ki = ωs/GBWi`. With zeros,
"global" separation factors from the closed-loop coefficients give about the same NST as the pure-pole
case. The GBW follows from ts, ε, β, Γ = gm/ID and the output step; Cc1 follows from the noise-set Gm1.
Slewing must happen in the first stage, otherwise the loop is positive during slewing and overshoots
(fix with class-AB or slew enhancers in later stages). Footnote 5: the method applies to a two-stage
opamp with Ahuja compensation (third-order loop), which is our case.

Key equations:
- `NST = ts·GBW/|ln ε|` (8); `ν = Io/(β·Gm) = SR/GBW` (11)
- single pole with slew: `NST = 1` if `Y/ν < 1`, else `NST = 1 + (Y/ν - 1 + ln(Y/ν))/|ln ε|` (12)
- two-pole minimum NST / K (Table I): ε 1 %: 0.55 / 2.73; 0.5 %: 0.53 / 2.96; 0.2 %: 0.51 / 3.19; 0.1 %: 0.50 / 3.32
- global two-pole factor `K̂ = α1²/α2 = (1 + b1·GBW)²/(a1·GBW)` (21)
- three-pole `Ke = 1/(a1·GBW)`, `Ki = a1²/a2` (26); closed loop `α1 = 1/GBW`, `α2 = 1/(Ke·GBW²)`, `α3 = 1/(Ke²·Ki·GBW³)` (29)
- three-pole minimum NST / Ke / Ki (Table II): 1 %: 0.43 / 2.55 / 1.78; 0.5 %: 0.40 / 2.55 / 2.00;
  0.2 %: 0.39 / 2.60 / 2.18; 0.1 %: 0.38 / 2.63 / 2.40
- with zeros `K̂e = [1/(a1·GBW)]·(1 + b1·GBW)²/(1 + b2·GBW/a1)`, `K̂i = (a1²/a2)·(1 + b2·GBW/a1)²/(1 + b1·GBW)` (34)
- slew added to any loop: `NST ≈ NST0 + (Y/ν - 1 + ln(Y/ν))/|ln ε|` (23), errors below about 20 %
- standard pair `Gm/Io = Γ/2` (38); design `GBW = [|ln ε| + βΓ·VDD/2 - 1 + ln(βΓ·VDD/2)]/ts` (39);
  `Sn = 2·4kT·(2/3)·(1 + c)/Gm1` (40); `Cc1 = β·Gm1/GBW` (42); `GBW = β·Gm1/(Cc1·(1 + η))` (45)
- rule of thumb: Ke and Ki 10 to 20 % above Table II, because the minima sit on discontinuities where the
  first overshoot just touches the error band.

Reported: 65 nm, 1 V, reversed-nested-Miller three-stage with feedforward stage and a slew enhancer
(low-threshold device that is off at rest), SC integrator with Cs = Cf = Cout = 0.4 pF, β = 0.5,
CL = 0.6 pF, ε = 0.5 %, 20 ns available. Gm1 = 320 µA/V (Γ = 16), required GBW 55 MHz, designed 66 MHz,
Cc1 385 fF, Cc2 247 fF, Gm2 = Gm3 = Gmf = 664 µA/V; simulated GBW 57.5 MHz, PM 65°; 0.5 % settling
7.8 / 9.8 ns for ±100 mV (NST 0.52 / 0.66) and 16.0 / 17.0 ns for ±800 mV (NST 1.07 / 1.14); 400-run
Monte Carlo. Power is not reported. Two-pole check: K = 2.96, PM 72.2°, NST 0.53.

Mechanism: set GBW and separation factors for minimum settling time including slew, rather than for a
large phase margin.

**B. Applicability (directly usable as analysis).**
- v13 in their terms: `ν = 1/(β·Γ) = 0.335 V` because current reuse gives `Gm/Io = Γ` per side (0.685 mS
  from a 43.7 µA tail), not Γ/2. `Y/ν = 2.09`, slew term 1.82, single-pole reference
  `ts = (7.63 + 1.82)/GBW = 32.3 ns`; measured 24.48 ns, so NST = 0.76.
- Splitting with (23), and using the dynamic budget left after the static error (about 2.2e-4,
  |ln| = 8.42): NST0 ≈ 0.49. Table II minima are 0.38 to 0.40 at the discontinuity, about 0.42 to 0.45
  with the 10 to 20 % back-off. So the optimizer has already found a near-optimal small-signal shape; the
  slew term (6.2 ns, about 19 % of the single-pole budget) is the largest remaining settling loss.
- Key consequence: at the same Γ a single standard pair would have `Y/ν = 1.04` and almost no slewing.
  Current reuse halves the stage-1 current for a given Gm but doubles Y/ν. A tail boost that only acts
  while slewing recovers this (E2). From (12): boost x1.3 gives ts -7.9 %, x1.6 gives -13.2 %, x2 gives
  -18.4 %, upper bound -19.3 %.
- Power conversion: the currents that scale with fc at fixed noise (stage 1 43.7 µA and output quiescent
  25.4 µA, which tracks fc when the inner-pair frequency is held) are about 53 % of the 132 µA window
  current; the 57.7 µA load charge does not scale. So `ΔP/P ≈ 0.53·Δts/ts`: -4 % (x1.3), -7 % (x1.6),
  -10 % (bound).
- Our rule "no ringing peak before 25 ns" is compatible with their minima: at the minimum the output
  enters the band first and crosses the final value later, so the zero crossing is after ts. It must land
  after 25 ns and the overshoot must stay below ε (floor check). Use their 10 to 20 % back-off.
- "Slew in the first stage" holds for v13 (class-AB output).
- Suggested analysis without new circuitry: fit the loop-bench T(s) to their third-order form (31),
  compute K̂e and K̂i with (34) and compare with Table II. This shows how much small-signal reshaping is
  left (estimated at most 10 to 15 % of the linear part) and can narrow the optimizer ranges.

### 2.6 Yavari, Maghari, Shoaei, IEEE TCAS-II 2005

M. Yavari, N. Maghari, O. Shoaei, "An accurate analysis of slew rate for two-stage CMOS opamps,"
IEEE Trans. Circuits Syst. II, vol. 52, no. 3, pp. 164-167, Mar. 2005. DOI 10.1109/TCSII.2004.842058.

**A. Technique.** A time-domain large-signal model of slewing in a two-stage Miller OTA (with nulling
resistor Rc) for the power-efficient case where the second-stage current I2 is too small:
`I2 > (Cc + CL)/Cc · I1` (3) is violated. Then the first-stage mirror load (M4) enters triode, the output
device (M5) cuts off, and the current in Cc is no longer I1. Solving the node equations gives the
effective SR for the NMOS-input negative edge and the PMOS-input positive edge.

Key equations:
- textbook `SR = min(I1/Cc, I2/(Cc + CL))` (16); Wang-Harjani `SR± = (I1/Cc)/(1 + 2a(a - b)/(ΔV·(a + b)))` (1, 2)
- `SR- = -I2/(Cc + CL)·(1 + γ2/ΔV)^-1` (15), with
  `γ2 = I2·Cc²·(1 + Rc·kp4)/(kp4·(Cc + CL)²) - Cc/(Cc + CL)·(|Vtp| + √(2·I2/βp5))`, `kp4 = √(2·I1·βp4)`
- `SR+ = I2/(Cc + CL)·(1 + γ3/ΔV)^-1` (24), with
  `γ3 = Cc/(Cc + CL)·(Vtn + √(2·I2/βn5)) - I2·Cc²·(1 + Rc·kn4)/(kn4·(Cc + CL)²)`

Reported: 0.25 µm BSIM3v3, VDD 3 V, I1 = 1 mA, Cc = CL = 5 pF, Rc 400 / 320 Ω, ΔV ±1 V, I2 swept 0.5 to
2.5 mA: SR from about 40 to about 200 V/µs; the textbook model overestimates by about 20 to 25 % where (3)
is violated; the new model matches HSPICE until I2 is large.

Mechanism: a design whose second stage is below the class-A slew requirement slews slower than the
textbook formula, and the effective SR depends on ΔV and on how far internal nodes swing.

**B. Applicability.**
- Our output stage is class-AB, so the I2/(Cc + CL) limit does not apply directly. The same physics moves
  one level up: during the slew the output PMOS must source `(CL + Cc)/Cc · I1 ≈ 5.5 x 43.7 ≈ 240 µA`
  (19x its 12.7 µA quiescent current). Its gate (through Cls, 0.93 transmission) must fall by roughly
  0.25 to 0.3 V, so v1 drops from 0.57 V to about 0.3 V, below na (0.43 V): the NMOS cascode cuts off and
  M1n leaves saturation. This is the Yavari situation (stage-1 device in triode during the slew) and
  matches the v01 log entry "v1 falls until the NMOS cascode cuts off". Effect: effective SR below I1/Cc
  and a recovery of na and v1 back into saturation at the end of the slew.
- Use: plot V(v1n) and V(na1, ntn) during the first 8 ns to see how long Mcn1 and M1n are out of
  saturation. The knobs that shrink the v1 swing (Wop, Cls) are already in the r3 space. For E2, a larger
  slew current needs a larger output current and hence a larger v1 swing, so E1 (more NMOS headroom)
  should come first.
- Net: no circuit to copy; a correction to the slew estimate and an ordering argument (E1 before E2).

## 3. Corrections to the current diagnosis

1. **No noise shelf in v13.** For a closed loop with fc = 46.6 MHz, the share of noise above 100 MHz is
   27.8 % for a pure single pole and 16.7 % for an ideal two-pole loop with PM 76.8° (both have noise
   bandwidth `(π/2)·fc`). The measured 27 % is therefore not a shelf. D5 shows no flat region: the
   density is about 37 nV/√Hz in band, about 21 nV/√Hz at 100 MHz and 10 nV/√Hz at 200 MHz (the ideal
   two-pole curve gives 17 and 6.9, so +1.8 dB and +3.2 dB), then falls steeply, and above about 2 GHz
   follows the Hurst Fig. 3 feedforward asymptote at -20 dB/decade (under 1 % of the noise). The excess
   is a 20 % larger noise bandwidth, located mostly between 100 and 500 MHz, i.e. the bump of the complex
   non-dominant pair at about 170 MHz. The v01 shelf (LHP zero gm_c/(CB + Cc), Hurst Fig. 2) disappeared
   with the CR topology.
2. **Where α = 13.9 comes from** (ideal 7.0): `7.0 x 1.35 (NOIMOD=1 gmbs and gds) x 1.20 (noise
   bandwidth) = 11.3` for input thermal noise, plus 1.2 flicker, plus 1.35 cascodes, plus 0.05 other. The
   gmbs term is a model property: it applies to the PMOS inputs even with bulk tied to source (gmbs/gm =
   0.34 at Vsb = 0). Tying the PMOS input bulk to vdd (Vsb ≈ 0.37 V) lowers gmbs/gm to about 0.28 and
   trims the amplifier noise by about 1.8 % (part of E1).
3. **What noise improvements are worth.** With the v13 split (amplifier-noise-side current
   `sqrt(a·B) ≈` kT/C-side current `sqrt(b·A)`, i.e. Cc and Cin already near the Lagrange optimum), a
   relative cut r in amplifier noise power returns `P'/P ≈ ((√r + 1)/2)²` on the 127 µA that scales:
   r = 0.95 gives -2.5 %, r = 0.90 gives -5 %, r = 0.83 (noise bandwidth back to ideal) gives -8 %. The
   bandwidth excess is the price of the settling-optimal inner pair, which the optimizer already trades
   against SNR, so no structural noise experiment is proposed beyond the bulk tie in E1.
4. **Slewing.** About 6 ns of the 24.5 ns (Giustolisi term 1.82 of 9.45 normalised units). Stage-1 tail
   limited, aggravated by current reuse (Gm/Io = Γ) and by M1n/Mcn1 leaving saturation while v1 swings
   (Yavari mechanism).
5. **Stage-1 gain.** Set by the NMOS side (0.73 MΩ of the 0.64 MΩ total) because M1n and Mcn1 have
   0.13 and 0.14 V, while 0.36 V of spare headroom sits in the PMOS cascode and 0.16 V of margin in the
   NMOS tail. The input common mode is free per the FAQ ("You are free to choose the common-mode"), and
   the benches already expose it as `.param VCMI`.

## 4. Experiments (ranked by expected saving over risk)

General: one change at a time, log each in PROGRESS.md, judge with `evaluate.py` and `robust.py`.
The r3 optimizer space already holds tsc, ko, Cls, fcc, C1d, Cc, Cin, Wcn, Lin, Wcp, Won, Wop and Wctl, so
none of the three experiments below duplicates it: VCMI, kcp, kcn, Wtn, the PMOS input bulk, the boosted
tail unit and the cross-coupled pair are all outside it. After each experiment that works, add its new
parameters to the optimizer space and redo the power descent.

### E1 (rank 1): move headroom to the NMOS input and cascode (input CM plus bias)

Target: stage-1 gain (A1 about 53 to 55 dB, limited by M1n at 0.13 V and Mcn1 at 0.14 V).
Basis: FAQ (input CM free); Hurst and López-Martín headroom accounting; Akter (why not level-shift the
input gates instead); Yavari (more M1n headroom also helps the slew recovery).

Mechanism: the summing-node DC is `(Vout,cm + 4·VCMI)/5` (Rin 100 MΩ, Rfb 400 MΩ). Lowering VCMI lowers
ntn (= Vsum - Vgs(M1n)) while na stays set by vcn, so M1n gets the NMOS tail's spare margin. ntp falls by
the same amount, so vcp must come down to keep M1p in saturation; the PMOS cascode has 0.36 V to give.

Changes, in order (each measured before the next):
- E1a, bench only: `VCMI` 0.90 to 0.85, 0.80, 0.75 in bench_tran/noise/loop (scan first with
  `lt.py sweep ... --set VCMI=0.9,0.85,0.8,0.75`). At 0.80: Vsum ≈ 0.82 V, ntn ≈ 0.22 V.
- E1b, amp.inc: `kcp` 0.5 to about 0.6 to 0.7 (scan), lowering vcp by about 0.05 to 0.1 V so that
  |Vds(M1p)| ≥ 0.2 V and |Vds(Mcp1)| ≥ 0.4 V.
- E1c, amp.inc: `Wtn` 4u to 6u (Mbn uses Wtn too, so the tail current is unchanged; tail Vdsat about
  0.14 to about 0.11 V), then VCMI 0.75 (Vsum ≈ 0.78 V, ntn ≈ 0.18 V, tail margin about 0.07 V).
- E1d, amp.inc: `kcn` 0.6 to 0.5 (vcn about -0.05 V, na about 0.38 V) to split the gained headroom:
  targets |Vds(M1n)| ≈ 0.18 to 0.20 V and |Vds(Mcn1)| ≈ 0.18 to 0.19 V.
- E1e, amp.inc: bulk of M1p and M2p from ntp to vdd (FAQ: PMOS bulk free). Cuts the NOIMOD=1 gmbs noise
  term of the PMOS inputs (about -1.8 % amplifier noise) and raises |Vth| by about 0.06 V, which lifts ntp
  back up and relaxes E1b.

Starting point to try in one go after the scans: VCMI 0.78, kcp 0.65, Wtn 6u, kcn 0.5, PMOS input bulk
on vdd.

Measure: `lt.py op` margins and gm/gds of m1n, mcn1, m1p, mcp1, mtn; loop T0 at mid and ±0.7 V (expect
65.9 dB at the extremes to rise to about 72 to 75 dB; NMOS-side output resistance from 0.73 MΩ to about
2 to 3 MΩ, A1 +6 to +9 dB); Aβ at the end of the run (71.6 dB now, expect about 78 dB); A25 margin;
SNR; CM loop (`bench_cmloop`) and CM excursion, because a smaller NMOS-tail margin raises tail gds and
with it the existing positive internal CM loop.

Payoff: (1) the smaller static error frees about 0.54 of |ln ε| (dynamic budget 2.2e-4 to 3.8e-4), ts
-5 %, power about -3 % after an Ib/tsc descent; (2) the larger A25 margin may allow a larger output step
with Cin and Cc scaled as `(1.4/V)²`: 1.45 V is worth about -4.5 %, 1.5 V about -8.6 % (estimates include
the extra slew from the larger step). The step is gated by A25 ≥ 78.3 dB at ±0.725 or ±0.75 V outputs.

Kill criteria: T0 at ±0.7 V rises by less than 4 dB after E1d; any device below 25 mV saturation margin
at mid or at the extremes (watch ntn during the step); CM loop PM below 60° or CM excursion above
50 mV that ko cannot fix; SNR loss above 0.05 dB not recovered by E1e.

Report impact: the input sources' DC level in amp_tran.asc and amp_noise.asc (gen_asc.py) and one
sentence in the biasing paragraph ("input CM 0.78 V, output CM 0.90 V, both free per the FAQ").

### E2 (rank 2): capacitively boosted NMOS tail unit (adaptive bias from the tail-node max detector)

Target: slewing (about 6 ns, 19 % of the single-pole budget). Basis: López-Martín adaptive biasing and
WTA principle; Kim and Giustolisi "device idle at rest, active only in large signal"; Giustolisi (12)
for the expected gain; Yavari for the limits.

Mechanism: during the step ntn rises by about 0.11 V (max of the two NMOS gates minus Vgs at full tail
current); in the linear phase it stays within about 1 mV. A tail unit whose gate is AC-coupled to ntn
and DC-biased from vbn carries its normal current at rest and roughly 15 to 30 µA extra during the slew
(self-limited, because more tail current lowers ntn again). Side a (vin up, von rising) is driven by the
NMOS pair, side b (vop falling) by the PMOS pair, so this boost speeds the rising output, which is the
slower one today (CM excursion comes from the stronger pull-down). The extra M1n current is drawn through
Cc from the rising output, whose charge `fcc·Cc·ΔV` is fixed and already inside the 57.7 µA, so the
window charge should barely change; the quiescent current is unchanged (one tail unit is re-used).
ntn is a differential AC ground, so fc, PM and noise of the differential loop should not move at all.

Netlist change (amp.inc):
```
.param Mtn=2 Mtb=1 Ctb=0.2p Rtb=3Meg
.param kn={knr*Mt/(Mtn+Mtb)}          ; was knr*Mt/Mtn: keeps the total NMOS tail bias current unchanged
                                      ; (in design/work/cr/amp.inc keep the tsc factor: knr*Mt*tsc/(Mtn+Mtb))
Mtn  ntn vbn 0   0 nch L={Ltn} W={Wtn} m={Mtn}
Mtb  ntn gtb 0   0 nch L={Ltn} W={Wtn} m={Mtb}   ; boost unit, an ordinary tail unit at rest
Ctb  ntn gtb {Ctb}                              ; couples the tail-node rise to its gate
Rtb  gtb vbn {Rtb}                              ; DC bias; Rtb*(Ctb+Cgg) ≈ 0.7 us >> 25 ns
```
Mtc (CMFB unit) stays as is. Cgg per tail unit is about 24 fF, so Ctb = 0.2 pF gives about 0.9 coupling.
Rtb noise and Mtb noise are common-mode (rejected differentially). Sweep Ctb {0.05, 0.1, 0.2, 0.4} pF and
Mtb {1, 2} (Mtn = 3 - Mtb). Total added capacitance at most 0.4 pF per amplifier.

Measure at fixed Ib first: T30dB (13.91 ns now; expect about 11 to 12 ns), Ts, Aβ25, A25, window and
quiescent I(Vdd) (window must not rise by more than about 1 µA), CM excursion (expect it to shrink; if it
flips sign, reduce Ctb), CM loop with the new parts (`bench_cmloop`: the coupled unit adds a fast,
positive input-CM to tail-current path of about 0.27 mS x 0.19 above 0.25 MHz, against the CMFB's about
0.17 mS/V), DM loop fc/PM (must be unchanged; a change means the netlist is wrong). Also plot V(na1, ntn)
in the first 8 ns: if M1n is in triode during the slew the boost cannot flow, then do E1 first.
Then convert the slack with Ib/tsc descent.

Expected: from (12), a 1.3x to 1.6x slew current cuts ts by 8 to 13 %, i.e. -4 to -7 % power after
descent; bound -10 %. Possible extra: if the CM excursion drops, ko can go from 0.64 to about 0.60
(PROGRESS: 0.60 failed only the 50 mV CM gate), a further -1 to -2 %.

Kill criteria: T30dB improves by less than 1.0 ns with Mtb = 2 and Ctb ≥ 0.2 pF; CM loop PM below 60°;
a ringing peak before 25 ns that persists for ko from 0.60 to 0.76; window current up by more than 2 µA
at fixed Ib. Do not add the PMOS mirror image (Mtp unit coupled from ntp) unless the CM excursion turns
positive: its boost current comes from Vdd into the falling side and costs up to `(1 - fcc)·Cc·ΔV`
= 0.12 pC, about +5 µA window.

### E3 (rank 3): cross-coupled PMOS pair at v1 (negative conductance)

Target: stage-1 gain beyond E1, mainly to make a 1.5 V output step pass A25. Not taken from the six
papers; it is the standard negative-conductance gain enhancement. The closest paper principle is
López-Martín's LCMFB (remove the differential load conductance while keeping the CM defined). Listed
because the papers' own headroom remedies (level shifters, split capacitors) fail here.

Mechanism: for differential signals a cross-coupled pair is a conductance -gm_x at each v1 node, for CM it
is +gm_x. With gm_x about 0.6 to 0.7 of the v1 conductance, the stage-1 output resistance triples. The
v1 conductance seen on the settling time scale is about 1.6 µS from the stage-1 cascodes plus about
0.3 µS from Rb through Cls (above about 0.1 MHz), so gm_x ≈ 1.1 µS stays below it at all frequencies.
Strong inversion is used so gm_x hardly changes with the ±20 to 40 mV v1 swing at the output extremes.
The grade uses TT only, so the cancellation ratio is deterministic, but keep a 1.5x margin anyway.

Netlist change (amp.inc):
```
.param Wx=0.22u Lx=9u
Mx1 v1n v1p vdd vdd pch L={Lx} W={Wx} m=1   ; about 0.45 uA each at |Vov| ≈ 0.78 V, gm_x ≈ 1.1 uS
Mx2 v1p v1n vdd vdd pch L={Lx} W={Wx} m=1
```
Added supply current about 0.9 µA (+0.7 %); the CMFB moves the same amount to the NMOS tail. Device
noise referred to the input is about gm_x/gm1 ≈ 0.2 % of the input pair's, negligible. At fc the v1 node
is dominated by ωCA ≈ 19 µS, so the loop shape near fc is unchanged.

Measure: sweep Lx {20, 14, 9, 6} µm; find the Lx where the circuit becomes bistable and run at a gm_x
no larger than 2/3 of that value. Bistability test: two `.op` runs with `.nodeset V(v1n)=0.62 V(v1p)=0.52`
and the reverse must give the same solution. Then loop T0 at mid and ±0.7 V (expect +6 to +10 dB on the
stage-1 part), Aβ at the end of the run, A25, settling shape, CM loop (CM gain at v1 drops by a few dB),
`robust.py`.

Expected: on its own about the same static-error benefit as E1 (-2 to -3 %); together with E1 enough A25
margin to try the 1.5 V step (about -8.6 % estimated, section E1).

Kill criteria: T0 at ±0.7 V up by less than 4 dB at the 2/3-of-latch point; any bistability or
hysteresis in a slow differential DC sweep (loop bench with Vext); non-monotonic settling that ko or C1d
cannot remove; A25 not improved.

Combined outlook: if E1, E2 and E3 each deliver their central estimate and the 1.5 V step passes, the
target is roughly 0.20 to 0.21 mW. Each estimate carries about ±50 % uncertainty.

## 5. Rejected ideas and the number that rejects them

| Idea | Source | Why not |
|---|---|---|
| Split Cin/Cfb to bias NMOS and PMOS input gates separately | Akter | Feedback network fixed; needs switches and clock phases |
| Input-gate level shift with Cls plus a few-MΩ bias resistor | Akter (CLS variant) | About 310 µV extra output noise (3 MΩ, 0.55 pF); Akter's Fig. 2: +63 % power |
| Incomplete settling with gain trimmed by bias current | Akter | Aβ floor after 25 ns is checked; the settled value must be within 4.84e-4 |
| Grounded-source (tail-less) pseudo-differential input | Akter | No CM rejection; Vgs would be the 0.9 V input CM, current not controllable without level shift |
| SRE triode devices in mirror diodes; auxiliary adaptive-bias pair | Kim | No mirrors in our signal path; aux pair adds Cp and 55 % of their flicker noise |
| FVF / CMS / WTA class-AB input stage | López-Martín | +50 to +75 % static power in their own data; NMOS half has no headroom (ntn 0.30 V); extra summing-node capacitance |
| AC-coupled NMOS output gate plus LCMFB on v1 | López-Martín | Needs a new output CM loop through a slow Rb·C path (about 0.5 MHz); E1 gets the same headroom cheaply |
| Separate common-gate current buffer (Fig. 1) | Hurst | Extra bias current to fix a RHP zero that sits at 7.7 fc and does not limit |
| Current mirror with gain m in series with Cc (Fig. 4) | Hurst | Saves at most 12.4 µA of slewing charge, costs at least 2·I1 (> 40 µA) of mirror bias |
| Internal positive capacitive feedback to cancel the static gain error | (Akter's gain-correction idea) | Changes the closed-loop gain through a second feedback path; violates the fixed-network rule |
| Larger NMOS input area against flicker (8 % share) | general | Cp rises; with L 1.5 µm flicker -4.6 % but β -3.8 %, net about -1 % |
| Re-tuning separation factors toward Table II minima | Giustolisi | Already near: NST0 ≈ 0.49 vs 0.42 to 0.45 practical minimum; the optimizer covers ko, Cls, C1d, fcc, Wcn, Wcp |

## 6. Open measurements that would sharpen these estimates

- Fit T(s) from `bench_loop` to the third-order form and compute K̂e, K̂i (Giustolisi (34)).
- Transient plots of V(v1n), V(na1, ntn) and V(ntn) during 0 to 8 ns after the step (Yavari mechanism,
  size of the ntn rise for E2).
- Noise contributions per device split into below and above 100 MHz, to confirm that the 20 % excess
  noise bandwidth sits in the 100 to 500 MHz bump.

## 7. Outcome of the experiments (6 Oct 2026)

| Experiment | Result | Verdict |
|---|---|---|
| E1: input common mode 0.9 V to 0.86 V | Abeta(25 ns) +4 dB at equal power and SNR, min saturation margin 22 to 48 mV, CM excursion 49.8 to 22 mV | kept; round 4 turned the margin into power: 0.2375 to 0.2160 mW |
| E2: capacitor-boosted NMOS tail unit | no change in Abeta or settling, +0.4 to +0.9 µW | rejected |
| E3: cross-coupled PMOS gain pair | not tried (bistability risk at the output extremes, adds Cp) | open |
| Static output CM constraint (found in review: v14 sat at 0.941 V) | knr re-centred; round 5 with abs(Vcm - 0.9) <= 10 mV and ko +-7 % | v15: 0.2142 mW, output CM 0.899 V |

Where the remaining power goes (v15): 119.0 µA window average = 59.8 µA quiescent (stage 1 35.9 µA, outputs
2 x 10.4 µA, CMFB 3.1 µA) + 59.2 µA of load charge. The load charge is close to the physical minimum for a
class-AB output, one side of C_L,eff (about 2.0 pF) lifted by 0.7 V in 25 ns (about 56 µA). SNR is the binding
constraint in every optimiser round (66.08 dB against the 66.05 dB gate), so further savings need lower noise per
ampere, not faster settling.
