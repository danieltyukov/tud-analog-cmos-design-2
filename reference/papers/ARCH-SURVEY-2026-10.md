# Architecture survey for the EE4525 resit residue amplifier (October 2026)

Question: are the architecture choices of the v15 design (two stages; stacked complementary current-reuse input
stage with PMOS and NMOS cascodes; current-buffer compensation; quasi-floating-gate class-AB output; continuous-time
CMFB) the best available under the assignment rules, or only a local optimum of the chosen topology?

Method. Literature from IEEE Xplore (search, abstracts and full text through the TU Delft proxy; no tool reported
AUTH_REQUIRED). Six full papers were downloaded into this folder (section 9). The six papers in
`NOTES-resit-2026-10.md` (Hurst 2004, Giustolisi 2021, López-Martín 2005, Akter 2018, Kim 2020, Yavari 2005) are used
but not re-summarised. Our numbers come from `results/latest.json` (tag final) and NOTES section 7. No circuit
simulation was run for this survey. Power comparisons use a hand model calibrated on v15 (section 1.3), evaluated in
Python in the session scratchpad. Formulas are plain text in code spans.

## 0. Summary

| Class | Key papers | Verdict | Power vs v15 (0.2142 mW) |
|---|---|---|---|
| Ring amplifier (dead-zone, class-C output) | Hershberg 2012; Lim and Flynn 2015a, 2015b; Lagos 2019; Llimós Muntal 2018 | reject | honest case at best -15 % (no output quiescent), but fails the ringing rule by construction; the 0.10 to 0.13 mW "bound" needs a .noise at a dead-zone operating point, which is an artifact |
| Floating inverter / dynamic amplifier | Tang 2020, 2023; Ashwin Kumar 2022 | reject | needs precharge switches; without them it reduces to our stage 1 |
| Compensation: Miller + nulling resistor | textbook; Kamath 1974 | reject | +21 % to +48 % |
| Compensation: current buffer (Ahuja, Hurst) | Ahuja 1983; Hurst 2004 | keep (in use) | reference |
| Compensation: split-length (Saxena and Baker) | MWSCAS papers (not retrieved) | reject | current buffer with a weaker buffer gm |
| Compensation: no-capacitor feedforward | Thandri 2003 | reject | needs about 3.1 mS into the load, more than +100 % |
| Nested Miller, three stages | Eschauzier 1992; Seth and Murmann 2013; Giustolisi 2021 | reject | no gain shortfall to fix; adds a stage current |
| Output: quasi-floating-gate class AB | Ramírez-Angulo 2006 | keep (in use) | load charge within 6 % of the physical floor |
| Output: floating-battery class AB, adaptive bias, super class AB | Monticelli 1986; Hogervorst 1994; Galán 2007 | reject | +3 to +8 % control current, or single-stage swing |
| Input: current reuse in a telescopic stack | Chae and Han 2009; Lim and Flynn 2015b; Lyu and Hu 2025 | keep (in use) | 2x the Gm per µA of one pair, 4x of a folded cascode |
| Single stage (gain-boosted telescopic) | Bult and Geelen 1990 | reject | +22 % even at an unreachable full swing; 0.9 to 1.5 mW at its real swing |
| Gain boosting or E3 as an add-on | Bult and Geelen 1990 | prototype only if needed to buy swing | -4 to -8 % if a 1.45 to 1.5 V step passes |
| Switched or calibrated techniques (CLS, split ADC, incomplete settling, auto-zero, chopping) | Gregoire and Moon 2008; Akter 2018; Hershberg 2012 | excluded by the rules | not applicable |
| Switched-capacitor CMFB | FAQ | allowed, minor | about -1.5 % |

Top recommendation: no architecture change is worth prototyping as a replacement. The largest lever left is inside
the architecture: a 1.45 to 1.5 V output step (model -4 to -8 %, and the single-pair scan in PROGRESS.md measured
-7.8 % for 1.4 to 1.5 V), which has not been tried on the CR topology. Target 0.197 to 0.205 mW. Section 8 has the
ranking and the pass conditions.

## 1. Framing

### 1.1 Where the power goes (v15)

`P = 1.8 V × 119.0 µA` (window average). Quiescent 59.8 µA: stage 1 35.9, outputs 2 × 10.4, CMFB 3.1. Load charge in
the window 59.2 µA. Physical floor of the charge for a class-AB output whose rising side is fed from Vdd:
`C_L,eff·ΔV/T = 1.998 pF × 0.7 V / 25 ns = 55.9 µA`. SNR is binding (66.08 dB against the 66.05 dB gate); settling is not
(Aβ 69.31 dB, A 84.13 dB, Ts 23.20 ns, no ringing peak at all, i.e. a monotone approach).

### 1.2 Three invariants that decide most of this survey

(a) Noise fixes the input transconductance, not the topology. For any amplifier whose input stage is a
transconductor Gm1 (per side) inside a loop with crossover ω_c and noise-bandwidth factor k_NBW:
`v²_out ≈ 2·γ_e·kT·ω_c·k_NBW / (β²·Gm1)`. Schreier et al. (TCAS-I 2005, DOI 10.1109/TCSI.2005.853909) give the
single-stage form `2γkT/(β·C_L)` and the two-stage Miller form `2γkT/(β·Cc)`; both reduce to the expression above once
`ω_c = β·Gm1/C` is substituted. With ω_c set by the 25 ns settling, the noise budget fixes the minimum Gm1. An
architecture can only change the current per Gm1 (Γ), the excess factors γ_e and k_NBW, the ω_c it needs (slewing,
loop shape), β (input capacitance Cp) and its overheads (output stage, load charge, CMFB, boosters). Topologies whose
crossover is set by a transconductor driving the load (single stage, no-capacitor feedforward) carry a second
constraint `Gm ≥ ω_c·C_L,eff/β = 3.07 mS` per side for our load, about 5x our Gm1, and so overshoot the noise need.

(b) Swing is worth its square. The noise budget scales with Vstep², so Cin, Cc and every current that scales with
them go as 1/Vstep² (the load charge as 1/Vstep). v15 swings each output by ±0.7 V (0.2 V to 1.6 V); only a
common-source class-AB output reaches that. A cascoded output loses 0.3 to 0.5 V of swing and pays about
`(1.4/Vstep)²` in capacitance.

(c) The charge floor holds for every rule-compliant architecture. Each step moves `C_L,eff·ΔV` from Vdd into the
rising side. Moving charge from the falling output to the rising one would need an inductor or a switched charge pump.
v15 sits at 1.06x the floor.

### 1.3 Calibrated model

Two-stage: `noise = 42·kT/Cin + α·kT/Cc` with α = 13.67 at v15 (ideal `2·(2/3)/β` = 6.99, excess 1.95), α ∝ 1/β;
`I1 ∝ Cc/β` at fixed ω_c; Cp ∝ I1 (102 fF at 35.9 µA); output quiescent ∝ C_L,eff/I1 (Hurst eq. 58,
`|p2,3| ≈ sqrt(gm7·gm5/(CA·CL))` held fixed relative to ω_c, with gm7 ∝ I1); window charge
`47.2 µA·C_L,eff/C_L,eff0 + 12.0 µA·Cc/Cc0`, scaled with Vstep. Re-optimising Cin and Cc in this model gives 114.6 µA
(Cin 1.41 pF, Cc 0.48 pF) against the Optuna point's 119.0 µA (1.665 pF, 0.413 pF): the model reproduces the real
optimum to about 4 %. It is used only to rank options; differences below about 5 % are inside its error, and all
percentages below are relative to the model optimum.

Single stage (for section 6): same ω_c and settling shape as v15 (favourable to it), `Gm = ω_c·C_L,eff/β`, same Γ,
spec-definition NEF 1.13 = (2/3) × 1.35 (BSIM3 NOIMOD=1 counts gm+gmbs+gds) × 1.10 (noise bandwidth) × 1.08 (flicker)
× 1.06 (cascodes, boosters), Cp ∝ current, 0.1 pF output parasitic, 10 µA for two gain boosters, 3.1 µA CMFB.

## 2. Ring amplifiers

Papers:
- B. Hershberg, S. Weaver, K. Sobue, S. Takeuchi, K. Hamashita, U.-K. Moon, "Ring amplifiers for switched capacitor
  circuits," IEEE JSSC, vol. 47, no. 12, pp. 2928-2942, Dec. 2012. DOI 10.1109/JSSC.2012.2217865 (downloaded, read).
- Y. Lim, M. P. Flynn, "A 100 MS/s, 10.5 bit, 2.46 mW comparator-less pipeline ADC using self-biased ring amplifiers,"
  IEEE JSSC, vol. 50, no. 10, pp. 2331-2341, Oct. 2015. DOI 10.1109/JSSC.2015.2453332 (abstract; mechanism from 2015b).
- Y. Lim, M. P. Flynn, "A 1 mW 71.5 dB SNDR 50 MS/s 13 bit fully differential ring amplifier based SAR-assisted
  pipeline ADC," IEEE JSSC, vol. 50, no. 12, pp. 2901-2911, Dec. 2015. DOI 10.1109/JSSC.2015.2463094 (downloaded, read).
- J. Lagos, B. Hershberg, E. Martens, P. Wambacq, J. Craninckx, "A 1-GS/s, 12-b, single-channel pipelined ADC with
  dead-zone-degenerated ring amplifiers," IEEE JSSC, vol. 54, no. 3, pp. 646-658, Mar. 2019.
  DOI 10.1109/JSSC.2018.2889680 (abstract).
- A. ElShater et al., "A 10-mW 16-b 15-MS/s two-step SAR ADC with 95-dB DR using dual-deadzone ring amplifier,"
  IEEE JSSC, vol. 54, no. 12, pp. 3410-3420, Dec. 2019. DOI 10.1109/JSSC.2019.2943935 (abstract).
- P. Llimós Muntal, I. H. H. Jørgensen, "34.3 fJ/conv.-step 8-MHz bandwidth fourth-order pseudo-differential
  ring-amplifier-based continuous-time delta-sigma ADC in 65 nm," IEEE SSC-L, vol. 1, no. 10, pp. 198-201, Oct. 2018.
  DOI 10.1109/LSSC.2019.2910468 (downloaded, read; open access).
- Y. Lyu, Y. Hu, "A 2.30 NEF split-steering amplifier for switched-capacitor circuits with -14.2-dB CM-CM gain and
  100-V/µs slew rate," IEEE JSSC, vol. 60, no. 2, pp. 638-650, Feb. 2025. DOI 10.1109/JSSC.2024.3440266 (read in part).

Mechanism. A ring oscillator of three inverters, split before the last stage, with an offset ("dead zone") embedded so
that near balance both output devices are cut off or in deep subthreshold. For a large error the output device is
driven rail to rail and charges the load like a switched current source (slew-based charging, no quiescent current).
Near the target the overdrive on the output devices shrinks every half period, the output pole moves towards DC, and
the loop locks (Hershberg section III, "progressive overdrive reduction"). Accuracy at lock is the input-referred dead
zone, about `V_DZ/A1` (Hershberg eq. 1). In the "weak zone" the output still conducts and the circuit is a three-stage
opamp with very high gain. Hershberg embeds the dead zone with switched capacitors and stores the stage-1 offset on
C_AZ. Lim and Flynn replace this with a resistor R_B in the second stage (offset from the second-stage crowbar current,
no switches, no external bias) and high-Vt output devices. Their fully differential version uses a single differential
first stage with PMOS and NMOS input pairs on top and bottom tails (current reuse: the same stage as our stage 1),
inverter-like second and third stages, a triode CMFB on stage 1 during auto-zero plus an SC CMFB on the outputs, and a
4 pF auto-zero capacitor; simulated small-signal gain above 80 dB for 0.1 to 1.1 V output at 1.2 V.

Reported numbers:
- Hershberg, 0.18 µm: 10.5-bit pipeline, 61.5 dB SNDR at 30 MS/s, 2.6 mW total, about 90 µW per pseudo-differential
  ringamp stage, 800 fF differential input capacitance. 15-bit split-CLS pipeline: 76.8 dB SNDR, 95.4 dB SFDR at
  20 MS/s, 5.1 mW (the fine accuracy comes from CLS with a conventional opamp, not from the ringamp alone).
- Lim and Flynn 2015a, 65 nm: 56.6 dB SNDR at 100 MS/s, 2.46 mW. 2015b, 65 nm, 1.2 V: 70.9 dB SNDR at Nyquist, 1 mW
  total of which 366 µW ringamp (residue gain 32), Schreier FoM 174.9 dB, no calibration.
- Lagos, 28 nm: 56.6 dB SNDR at 1 GS/s, 24.8 mW. ElShater, 0.18 µm: 91 dB SNDR at 15 MS/s, 10 mW.
- Llimós Muntal, 65 nm, 1.1 V: two continuous-time ringamps without periodic reset, stabilised by a 100 fF output load
  (50.9 µW) or by current-starving stages 1 and 2 (27.4 µW, needs trimming); ADC 50.6 dB SNDR in 8 MHz. Their Fig. 4
  text: after an input step "the RAs leave the dead-zone and start oscillating with a decreasingly smaller amplitude
  until they lock into the dead-zone again."
- Energy per amplification, rough: Hershberg about 90 µW / 30 MHz ≈ 3 pJ at 61.5 dB with a smaller load; v15
  0.2142 mW × 25 ns = 5.4 pJ at 66 dB, gain 4, C_L,eff 2 pF. Same order; no factor-of-several advantage at this node.

Applicability, question by question:
1. Without reset or offset-cancellation switches: possible. Rule: "Ideal switches allowed for a switched-capacitor
   CMFB" (spec section 3), so no other switches. The R_B dead zone is resistor-only and legal (kΩ, well below "a few
   MΩ"). Offset storage only fights mismatch, which a TT, mismatch-free simulation does not have; the DC point would be
   set by Rin/Rfb as now. Llimós Muntal shows ringamps stabilising without any reset.
2. With a real CMFB: possible (Lim and Flynn 2015b; our CT CMFB would also fit).
3. "First significant ringing peak after 25 ns, at most 2 ringing cycles" (spec S4; clarification: "the first
   significant peak of the settling/ringing response ... appears after 25 ns"): fails by construction. After the slew
   the ringamp overshoots by `V_OS = t_d·I/C_L` (Hershberg eq. 2). With the 240 µA slew current our output already
   delivers, C_L ≈ 2 pF and a loop delay of 0.2 to 0.5 ns, `V_OS` = 24 to 60 mV per output against an error band of
   0.34 mV per output (Aβ ≥ 66.3 dB means 0.68 mV differential). Hershberg: practical designs "stabilize in only one or
   two periods of oscillation", so there is at least one large peak within a few ns. Removing it requires the output
   current to fall smoothly as the error shrinks, which is linear settling with a biased output, i.e. what v15 does.
4. A meaningful .noise result at the DC operating point: no. Spec section 4: "Amplifier noise: .noise V(vop,von) ...
   integrate over 10 kHz to 100 GHz". At a dead-zone operating point the output devices are cut off or in deep
   subthreshold, so the loop crossover at the op point is set by a leakage-level gm3. By invariant (a) the integrated
   noise scales with that crossover, so it can be orders of magnitude below the noise during settling, and it moves by
   orders of magnitude depending on where in the dead zone the op lands (Hershberg Fig. 6, dead zone against weak zone).
   The number would be legal on paper but an artifact, and output devices near cutoff may also fail the evaluate.py
   saturation check.
   Accuracy alone is reachable: A > 78.3 dB needs |vid| < 0.17 mV differential; with A1 ≈ 300 (our cascoded
   current-reuse stage) the dead zone may be about 40 to 50 mV at the second-stage input.

Power estimate. Honest case (only the 20.8 µA output quiescent removed, same noise physics): model -15 %, about
0.182 mW, but it needs S4 and an honest op point at the same time, which points 3 and 4 say cannot both hold. Artifact
bound (amplifier noise counted as about 0, Cin from kT/C alone = 0.715 pF, load charge ∝ Cin, stage 1 20 to 36 µA,
second-stage crowbar 5 µA): 0.10 to 0.13 mW. That is not a number to submit.

Verdict: reject. Our class-AB QFG output already captures the ringamp's main benefit (slew-based charging, about
240 µA peaks from 10.4 µA quiescent); what is left (the quiescent current) cannot be removed without breaking S4 or the
meaning of the noise number. This refines `brief/design-strategy.md`: the switched offset storage is avoidable (R_B dead
zone), the ringing is not.

## 3. Floating inverter and dynamic amplifiers

Papers:
- X. Tang et al., "A 13.5-ENOB, 107-µW noise-shaping SAR ADC with PVT-robust closed-loop dynamic amplifier," IEEE JSSC,
  vol. 55, no. 12, pp. 3248-3259, Dec. 2020. DOI 10.1109/JSSC.2020.3020194 (downloaded, read).
- X. Tang et al., "A bandwidth-adaptive pipelined SAR ADC with three-stage cascoded floating inverter amplifier,"
  IEEE JSSC, vol. 58, no. 9, pp. 2564-2574, Sep. 2023. DOI 10.1109/JSSC.2023.3268719 (abstract).
- R. S. Ashwin Kumar, N. Krishnapura, P. Banerjee, "Analysis and design of a discrete-time delta-sigma modulator using a
  cascoded floating-inverter-based dynamic amplifier," IEEE JSSC, vol. 57, no. 11, pp. 3384-3395, Nov. 2022.
  DOI 10.1109/JSSC.2022.3171790 (abstract).

Mechanism. An inverter pair (CMOS input, current reuse) is powered from a reservoir capacitor C_RES that is precharged to
VDD during reset and floats during amplification. Because C_RES floats, the CM output current is forced to zero (no
CMFB needed) and the PMOS and NMOS currents are equal. The current decays as C_RES discharges, so bandwidth and noise
bandwidth shrink during settling (self-quenching), and there is no static current.

Reported numbers (Tang 2020): 40 nm; two-stage FIA (first stage 0.8 V, second 1.1 V, C_RES2 = 3.5 pF), open-loop gain
18 + 15.5 = 33 dB; initial UGB about 500 MHz with PM 35° rising to about 80° as the currents decay; no Miller capacitor;
noise `kT/(β·C_T)·Gm2·Ro1` (their eq. 5), more than 2x lower rms as Gm2·Ro1 drops 8x; closed-loop gain 0.96 instead of 1
from the finite gain; ADC 83.8 dB SNDR in 625 kHz, 107 µW (sampling switch and integrators 41 µW), FoM_S 181.5 dB.
Ashwin Kumar 2022: cascoded FIA above 50 dB DC gain. Tang 2023: three-stage cascoded FIA in a 75.7 dB, 40 MS/s
pipelined SAR, 821 µW.

Applicability. The reservoir must be precharged by switches every cycle, which the rules forbid outside an SC CMFB.
Without switches C_RES sits on VDD at DC and the circuit becomes either a tailless pseudo-differential inverter (bias
current set by VDD - Vtn - |Vtp| with both gates near 0.86 V: strong inversion, gm/ID about 5 instead of 19, no CM
control) or, when fed through current sources, exactly our stage 1 (Lyu and Hu Fig. 1(a); the Lim and Flynn first
stage). The time-varying bandwidth is the same artifact problem as the ringamp under a DC-op .noise, and 33 to 50 dB of
gain is about 30 dB short of the A0 of about 80 dB we need at the output extremes. Static leftover: a capacitor between
the two tail nodes (ntp to ntn) would give an FIA-like transient boost of both pairs during the step and zero
high-frequency CM current. The slew part is what E2 tested (no change in Aβ or settling, +0.4 to +0.9 µW); only a small
CM-excursion benefit could remain (ko -0.04, about -1 to -2 %).

Verdict: reject.

## 4. Compensation

Papers:
- B. K. Ahuja, "An improved frequency compensation technique for CMOS operational amplifiers," IEEE JSSC, vol. 18,
  no. 6, pp. 629-633, Dec. 1983. DOI 10.1109/JSSC.1983.1052012 (abstract).
- P. J. Hurst et al., TCAS-I 2004, DOI 10.1109/TCSI.2003.820254 (in this folder; NOTES 2.4).
- V. Saxena, R. J. Baker, split-length and indirect compensation (MWSCAS 2008 and 2010): not found by this search; the
  technique is assessed from its circuit only, no numbers used.
- B. K. Thandri, J. Silva-Martínez, "A robust feedforward compensation scheme for multistage operational
  transconductance amplifiers with no Miller capacitors," IEEE JSSC, vol. 38, no. 2, pp. 237-243, Feb. 2003.
  DOI 10.1109/JSSC.2002.807410 (downloaded, read).
- R. G. H. Eschauzier, L. P. T. Kerklaan, J. H. Huijsing, "A 100-MHz 100-dB operational amplifier with multipath nested
  Miller compensation structure," IEEE JSSC, vol. 27, no. 12, pp. 1709-1717, Dec. 1992. DOI 10.1109/4.173096 (abstract).
- S. Seth, B. Murmann, "Settling time and noise optimization of a three-stage operational transconductance amplifier,"
  IEEE TCAS-I, vol. 60, no. 5, pp. 1168-1174, May 2013. DOI 10.1109/TCSI.2013.2244325 (read).
- G. Giustolisi, G. Palumbo, TCAS-I 2021, DOI 10.1109/TCSI.2020.3044454 (in this folder; NOTES 2.5).
- B. Y. Kamath, R. G. Meyer, P. R. Gray, "Relationship between frequency response and settling time of operational
  amplifiers," IEEE JSSC, vol. 9, no. 6, pp. 347-352, Dec. 1974. DOI 10.1109/JSSC.1974.1050527 (read in part).

Settling physics that decides the comparison. Error band: 66.3 dB, ε = 4.84e-4, 0.68 mV differential, in 25 ns.
Kamath et al.: a doublet (pole and zero near ω_z, spacing Δω) adds a slow term of relative size about Δω/ω_c with time
constant 1/ω_z; "doublets which produce only minor changes in circuit frequency response can produce major changes in
settling time." Allowing it 30 % of ε at 25 ns, with ω_c = 2π × 46.6 MHz:

| Doublet frequency | Allowed Δω/ω_c | Allowed pole-zero mismatch |
|---|---|---|
| ω_c/3 | 1.7e-3 | 0.5 % |
| ω_c/2 | 5.6e-3 | 1.1 % |
| ω_c | 0.22 | about 20 % |
| 2·ω_c or higher | no constraint | no constraint |

So any scheme that leaves a doublet below ω_c whose zero follows a large-signal quantity (the class-AB gm5 changes by
more than 10x during the step) is out for 66 dB in 25 ns.

Miller with nulling resistor. `p2 ≈ gm5/(CL + CA + CA·CL/Cc) = gm5/2.36 pF`. Placing p2 at the 171 MHz of our inner
pair needs gm5 = 2.54 mS against 0.40 mS (6.4x). With Rz set so that the LHP zero cancels p2, p2 can drop to about
1.5·ω_c (gm5 about 3x), but the zero tracks gm5 only at the op point, giving exactly the moving doublet of the table.
Model: +21 % (3x) to +48 % (6.4x). Reject.

Current buffer (Ahuja; Hurst Fig. 3 on both halves; ours). The inner pair rises by about Cc/CA (about 6x) at the same
gm5, there is no RHP zero, and the loop is third order, which is where Giustolisi's three-pole minimum (NST 0.38 to
0.40) lives; v13 sat at NST0 ≈ 0.49 against a practical 0.42 to 0.45 (NOTES 2.5). Costs: cascode noise injection
(about 10 % of the noise power) and a complex inner pair that adds about 20 % noise bandwidth. A real inner pair needs
`gm7 ≫ 1.7 mS` (Hurst) against 0.38 mS; a separate buffer (Hurst Fig. 1) at gm/ID 20 would need about 85 µA per side.
The model values those two noise excesses at -4 % and -7 %; no topology removes them for less than that. Keep.

Split-length (Saxena and Baker). Cc goes to the internal node of a split-length device, whose upper segment acts as a
low-gain current buffer. Hurst's analysis applies with a smaller gm7, so the inner pair drops (`∝ sqrt(gm7)`) and gm5
must rise. Its advantage, no cascode bias line, is free here anyway (bias block on Vddb is not counted). Reject.

No-capacitor feedforward (Thandri). LHP zeros from a feedforward stage cancel the first-stage pole; above the zero the
amplifier is `gm_ff/(s·C_L)`, so `ω_c = β·gm_ff/C_L,eff` and gm_ff = 3.07 mS per side for our load. Reported (0.5 µm,
1.25 V): simulated 94 dB, UGF 300 MHz, PM 74° into 8 pF; measured about 90 dB and 1 % settling in 15 ns with 12 pF (8 ns
of it slewing); post-layout 0.1 % in about 20 ns. Their target is 1 %, not 0.05 %, and their zero is deliberately placed
on the closed-loop dominant pole,
the one location where mismatch is tolerated. At gm/ID about 15 a 3 mS feedforward stage alone needs about 200 µA per
side. Reject.

Nested Miller and three stages. Three stages replace cascodes when the intrinsic gain is low (Seth and Murmann: 90 nm,
stage gains of about 8; 0.1 % in 2.5 ns, 240 µV, 5.2 mW at 1 V). Eschauzier's MNMC is a bipolar 100 dB, 100 MHz design. We have
no gain shortfall at mid scale (T0 about 72 dB) and the three-pole settling shape is already available from the
current-buffer two-stage. A third stage adds a stage current and another complex pair. Reject.

Verdict: keep the current-buffer compensation.

## 5. Output stages

Papers:
- J. Ramírez-Angulo, R. G. Carvajal, J. A. Galán, A. López-Martín, "A free but efficient low-voltage class-AB two-stage
  operational amplifier," IEEE TCAS-II, vol. 53, no. 7, pp. 568-571, Jul. 2006. DOI 10.1109/TCSII.2006.875320
  (downloaded, read).
- R. Hogervorst, J. P. Tero, R. G. H. Eschauzier, J. H. Huijsing, "A compact power-efficient 3 V CMOS rail-to-rail
  input/output operational amplifier for VLSI cell libraries," IEEE JSSC, vol. 29, no. 12, pp. 1505-1513, Dec. 1994.
  DOI 10.1109/4.340424 (abstract); D. M. Monticelli, IEEE JSSC, vol. 21, no. 6, 1986 (cited by Ramírez-Angulo).
- J. Galán et al., "Super class-AB OTAs with adaptive biasing and dynamic output current scaling," IEEE TCAS-I, vol. 54,
  no. 3, pp. 449-457, Mar. 2007. DOI 10.1109/TCSI.2006.887639 (abstract). López-Martín 2005, Kim 2020, Yavari 2005: NOTES.

Requirement: during the slew each output must source about `(CL + Cc)/Cc · I1 ≈ 240 µA` (NOTES 2.6) and then settle
linearly with gm5 about 0.4 mS at quiescent.

- Class A: quiescent current at least the peak, at least 240 µA per side. Reject (+400 %).
- Floating-battery class AB (Monticelli; Hogervorst translinear control): accurate quiescent control, at the price of a
  control branch of a few µA per side (+2 to +5 µA per side, +3 to +8 %) and an extra node at the stage-2 input.
  Ramírez-Angulo: such control circuits reduce the effective boost factor because their current adds to the static
  current. Not needed in a TT-only simulation, where the QFG quiescent current is set by design.
- Quasi-floating gate (ours). A small capacitor plus a very large resistor make a floating battery with no extra static
  current. Reported (measured, 0.5 µm, single 2 V supply): slew 0.41 V/µs (class A) to 20 V/µs, a boost of about 50;
  UGF 6 to 11 MHz at the same 45 dB gain, because both output devices conduct and the output pole doubles. In v15: Cls about 0.5 pF,
  Rb 3 MΩ (corner about 100 kHz; Rb noise is referred to the input through the stage-1 gain), transmission about 0.93.
  The window charge is 59.2 µA against the 55.9 µA floor.
- Adaptive bias and super class AB (López-Martín 2005, Galán 2007, Kim 2020): single-stage OTAs whose gains are in
  slewing and in mirror-ratio boosting. Our signal path has no mirrors, slewing is not binding (E2), and a single stage
  loses the swing (section 6). Reject.

Is QFG the most efficient here? Yes for static overhead (zero) and charge (1.06x the floor). What remains is the
20.8 µA of quiescent current that sets gm5 for the inner pair at the op point. By Hurst eq. 58 it trades against gm7,
which costs no current: halving gm5 at a fixed inner pair needs 2x gm7 (for example the PMOS cascode from gm/ID 10.3 to
about 17, NOTES 2.4). Model: -7 %. This is sizing inside the topology, not an architecture change.

## 6. Input stage and number of stages

Papers:
- Y. Chae, G. Han, "Low voltage, low power, inverter-based switched-capacitor delta-sigma modulator," IEEE JSSC,
  vol. 44, no. 2, pp. 458-472, Feb. 2009. DOI 10.1109/JSSC.2008.2010973 (abstract).
- K. Bult, G. J. G. M. Geelen, "A fast-settling CMOS op amp for SC circuits with 90-dB DC gain," IEEE JSSC, vol. 25,
  no. 6, pp. 1379-1384, Dec. 1990. DOI 10.1109/4.62165 (abstract).
- Lim and Flynn 2015b (first stage), Lyu and Hu 2025 (Fig. 1 classification), Akter 2018 (NOTES 2.1).

Current reuse. Both pairs share one current, so `Gm per side = Γ·I_T`, against `Γ·I_T/2` for one pair and at most
`Γ·I_T/4` for a folded cascode, whose fold branches must carry at least the input current (spec: "input-pair currents
must not exceed the cascode-branch currents"). Chae and Han: inverter-based SC delta-sigma modulators, 81 dB SNDR in
20 kHz at 36 µW from 0.7 V; a 0.7 V supply in 0.18 µm puts the inverters near or below threshold (my inference, the
abstract does not say). At 1.8 V a tailless inverter would sit in strong inversion. Lyu and Hu call our stage type (a): "its biasing point can be well
controlled, and the common-mode feedback (CMFB) can be feasibly realized by controlling either Vbp or Vbn", at the
cost of two Vgs plus two
Vdsat of headroom and a bias-limited slew rate. The "limited output range" of inverter amplifiers they list does not
apply: our stage-1 output only drives the output-stage gates and swings tens of mV.

Tailless and level-shifted inputs (Akter; the split-steering amplifier of Lyu and Hu, NEF 2.30, which reuses Cs and Cf
halves as level shifters and needs DMCN switches): forbidden ("Cin/Cfb = 4 exactly ... no other change to the
network"; switches) or noisy (resistor-biased level shift, about 310 µV extra, NOTES 2.1).

Telescopic against folded. The six-device stack works because v1 hardly moves; folding would buy swing we do not need
at v1 for 4x the current per Gm. Keep telescopic.

NEF. The spec NEF (`v² = NEF·2kT/(β·C_L,eff)`) is 6.6 for v15 and about 1.1 for a single stage, which makes the two-stage
look 6x worse. That is a normalisation effect: the two-stage noise is set by Cc, not C_L,eff. At equal ω_c the fair
metric is noise power times current, and by invariant (a) it depends only on Γ, γ_e, k_NBW, β and the overheads. Report
the NEF as the spec asks, but do not rank stage counts with it.

Single stage (gain-boosted telescopic current reuse, Bult-Geelen style). Bult and Geelen: 1.6 µm, 5 V, 90 dB DC gain,
116 MHz UGF into 16 pF, settling better than 0.03 % with β = 1/3, boosters +15 % power. Model (section 1.3):

| Single-stage case | Cin | β | Total current | P |
|---|---|---|---|---|
| hypothetical 1.4 V step (unreachable) | 0.91 pF | 0.150 | 146 µA | 0.262 mW (+22 %) |
| ±0.35 V per output (0.70 V step) | 3.67 pF | 0.153 | 505 µA | 0.91 mW |
| ±0.265 V per output (0.53 V step), the realistic stack range of about 0.57 to 1.10 V at input CM 0.86 V | 6.41 pF | 0.154 | 861 µA | 1.55 mW |
| folded-cascode single stage, 1.1 to 1.4 V step | 1.0 to 1.6 pF | | 490 to 770 µA | 0.88 to 1.38 mW |

Even with the impossible full swing the single stage loses, because its 3 mS input pair adds about 0.38 pF of Cp
(β 0.150 instead of 0.191). Attempt 1 (single-stage gain-boosted folded cascode, 2.04 mW, settling short) is the
measured confirmation. Reject.

Gain boosting as an add-on to stage 1. Legal ("Real gain-boosters if boosting is used", same 1.8 V supply). Its only use
here is A0 at the output extremes, i.e. buying swing (invariant (b)). A booster on the NMOS cascode alone (88 % of the
stage-1 output conductance, NOTES 1) would cost about 2 to 4 µA, and by the doublet table its unity-gain frequency must
sit above about 2·ω_c or match within about 1 % below it. The cheaper first try is E3 (cross-coupled PMOS pair, about
1 µA). Only worth building if the swing experiment in section 8 needs it.

## 7. Techniques that beat these but need switches or calibration

| Technique | What it buys (source) | Why excluded |
|---|---|---|
| Correlated level shifting | rail-to-rail swing and a finite-gain error reduced by roughly the loop gain again; 30 dB loop gain gives more than 60 dB (Gregoire and Moon, IEEE JSSC 43(12), 2008, DOI 10.1109/JSSC.2008.2006312: 0.18 µm, 12-bit 20 MS/s pipeline, 10.5 ENOB, 0.9 V) | a level-shift capacitor switched into the feedback path after an estimation phase: switches outside the CMFB and a changed network ("no other change to the network") |
| Split-CLS with a ringamp | ringamp charges coarsely, an opamp finishes (Hershberg 2012: 76.8 dB at 5.1 mW) | same, plus the ringamp issues of section 2 |
| Incomplete settling with gain trimmed by bias current | about 4x power (Akter 2018) | the Aβ floor after 25 ns is checked; a single-step testbench has no calibration loop |
| Split-ADC or background calibration | gain error corrected digitally (Akter 2018) | no digital calibration in this assignment |
| Auto-zero, CDS, offset storage | offset and low-frequency gain error cancelled (ringamp C_AZ; 4 pF C_AZ in Lim and Flynn 2015b) | switches |
| Dynamic amplifiers, FIA, duty-cycled bias | no static current, decaying noise bandwidth (Tang 2020, 2023) | precharge switches; and the power metric averages the 25 ns window, so duty-cycling outside it gains nothing |
| Split Cin/Cfb as level shifters | tailless class-AB input with no extra kT/C (Akter 2018; Lyu and Hu 2025) | fixed network; switches |
| Chopping | flicker removed (Tang 2020) | clocks; our flicker share is only 8 % anyway |
| Charge recycling between the outputs | part of the 55.9 µA floor | needs switches or inductors |
| Amplifier current fed from the bias block | moves current off the measured supply | "Single VDD = 1.8 V for every amplifier block"; the bias block only provides decoupled bias voltages |
| Switched-capacitor CMFB | removes the 3.1 µA CT CMFB current | allowed: FAQ "you are allowed to use a switched-capacitor CMFB using capacitors and ideal switches"; run clock cycles before the step and use a DC CMFB for AC runs. Net about -1.5 % after the extra load charge of the CM capacitors (about 28 µA/pF × C_cm, 1.4 µA at 50 fF); the CM excursion must stay below 50 mV |

## 8. Ranked recommendation

Bottom line. The v15 architecture sits in the efficient corner of the design space for these rules. Every alternative
class surveyed either breaks a rule (switches, calibration, network changes), fails S4 by construction (ringamps), or
costs more in the calibrated model (single stage +22 % even with an unreachable swing, Miller +21 to +48 %,
feedforward more than +100 %, folded cascode 4x the current per Gm). No architecture change is worth prototyping as a
replacement in the remaining month.

To beat 0.2142 mW, any replacement would need a window current below 119 µA at SNR ≥ 66.05 dB, measured with .noise at
an operating point whose loop bandwidth is representative of the settling, and the first significant peak after 25 ns.
By the invariants of section 1.2 that needs either more output swing than ±0.7 V or a noise excess α below 13.7 at no
extra current. No surveyed topology provides either more cheaply than the present one.

What is worth the month, inside the architecture, ranked by expected saving per unit of risk (model estimates, about
±5 % absolute, applied to 0.2142 mW):

1. Output step 1.45 V, then 1.5 V, with Cin and Cc scaled by `(1.4/Vstep)²` and the power descent re-run. Model -4 %
   (1.45 V) and -8 % (1.5 V); the single-pair design measured -7.8 % for 1.4 to 1.5 V (PROGRESS.md swing scan: 0.348
   to 0.321 mW). Not yet tried on the CR topology, which now has A(25 ns) 84.1 dB, 5.8 dB above the gate. Pass
   conditions: evaluate.py ALL PASS, in particular A ≥ 78.3 dB and Aβ ≥ 66.3 dB at ±0.725 or ±0.75 V outputs, every
   MOSFET saturated at both extremes (the output devices then sit 0.15 V from a rail), and robust.py PASS. Target:
   ≤ 0.205 mW (1.45 V) or ≤ 0.197 mW (1.5 V). If the static loop gain at the extremes is what fails (the single-pair
   design fell from 77.5 dB to 70.5 dB between 1.4 and 1.5 V), add E3 first (about 1 µA), then a real NMOS-cascode
   booster (about 2 to 4 µA, unity-gain frequency at least 2·ω_c). Kill if the add-on costs more than 3 µA or shows a
   slow tail after 25 ns.
2. Lower output quiescent current at a constant inner pair: raise gm7 (wider PMOS cascode, extend the Wcp range beyond
   15 µm as NOTES 2.4 suggests), then let the optimiser lower Won, Wop and ko. Pass: same PM, GM and settling with at
   least 30 % less output quiescent current. Model -7 %, target ≤ 0.20 mW; about 0.183 mW together with item 1.
3. Switched-capacitor CMFB in place of the CT CMFB: about -1.5 %, only if items 1 and 2 are done and time remains.

Ringamp-type output: do not prototype. If it is tried anyway, set a two-day go/no-go: evaluate.py ALL PASS including the
first-peak check, the op-point loop crossover within 2x of the settling-phase crossover (otherwise the SNR number is an
artifact), and P ≤ 0.19 mW. I expect the first two conditions not to hold together.

## 9. Files downloaded for this survey (all through the TU Delft proxy)

- `IEEE-6373760-Ring-Amplifiers-for-Switched-Capacitor-Circuits.pdf` (Hershberg 2012)
- `IEEE-7236937-A-1-mW-71.5-dB-SNDR-50-MSs-13-bit-Fully-Differential-Ring-Amplifier-Based-SAR-Assisted-Pipeline-ADC.pdf`
  (Lim and Flynn 2015b)
- `IEEE-8686174-Pseudo-Differential-Ring-Amplifier-Based-Continuous-Time-Delta-Sigma-ADC-in-65-nm.pdf` (Llimós Muntal 2018)
- `IEEE-9190038-A-13.5-ENOB-107-uW-Noise-Shaping-SAR-ADC-With-PVT-Robust-Closed-Loop-Dynamic-Amplifier.pdf` (Tang 2020)
- `IEEE-1658191-A-Free-But-Efficient-Low-Voltage-Class-AB-Two-Stage-Operational-Amplifier.pdf` (Ramírez-Angulo 2006)
- `IEEE-1175504-A-Robust-Feedforward-Compensation-Scheme-for-Multistage-OTAs-With-No-Miller-Capacitors.pdf` (Thandri 2003)

Read in full or in part without downloading: Lyu and Hu 2025, Seth and Murmann 2013, Kamath, Meyer and Gray 1974.
Abstracts only: Lim and Flynn 2015a, Lagos 2019, ElShater 2019, Tang 2023, Ashwin Kumar 2022, Chae and Han 2009,
Bult and Geelen 1990, Ahuja 1983, Gregoire and Moon 2008, Galán 2007, Hogervorst 1994, Eschauzier 1992.
