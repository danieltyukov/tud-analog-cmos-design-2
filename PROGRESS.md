# PROGRESS (attempt 3: simple telescopic + common-source design, started 13 Oct 2026)

## Current state

Phase: DONE (P8), final verification pass complete. Final design pp06 = design/final/amp_{tran,noise}.asc (gen_asc.py from
design/work; verify_circuit equivalent, 65 components, 35 nets, 0 findings; lint 0/0). evaluate --tag final --publish on
the .asc: ALL PASS, P 0.5447 mW (I(Vdd) 0.3026 mA window, 0.2766 quiescent), SNR 66.20, Abeta 74.37, A 89.00, Ts 23.77 ns,
tau 2.500 ns, FoM 176.87 dB (TA ceiling 177), first zero crossing 26.92 ns, min sat margin 94 mV. robust PASS.
+-1 % on Cc, Rz0, Cls, Ibnp all pass (first crossing >= 25.46 ns). Params: Ibnp 6.4u, N 9, M2 11, Cc 0.77p, Rz0 1.2k,
Cls 0.68p, Cin 2.15p, Vstep 1.2, loads L 2u; cascode-gate diodes now 0.25 um (kcn 6, kcp 4, W 0.34u/0.36u).
Verified independently: KCL at all 34 nodes (< 15 pA), branch sums, I(Vdd) = stage 1 + stage 2 + CMFB, replica ratios
exact (18/9/9 units), 37 report formulas recomputed (`tools/crosscheck.py all`). D4/D5 are LTspice GUI screenshots
(`tools/ltgui.py all`), values from LTspice .meas. Report 8 pages; report/5714699.pdf = main.pdf.
Open TA point by user choice: stage 2 uses one RC level shifter (TA suggested two); see README / final message.

## Plan (tick a box only with tool evidence; add sub-steps as needed)

- [x] P0 Archive attempt 2, record TA feedback, add FoM plausibility check, selftest OK.
- [x] P1 Budget on paper (below).
- [x] P2 `design/work/amp.inc`: replica bias block + stage 1 + stage 2 + Miller Cc/Rz + CT CMFB.
      Gate: `.op` all saturated at mid and with the step applied (both polarities); loop fc and PM on target;
      output CM 0.9 V; stage-1 output CM near the replica's Vbn.
- [x] P3 CMFB checked (CM loop PM ≥ 60°, CM excursion during the step small).
- [x] P4 `evaluate.py` ALL PASS on the netlist benches, settling curve shape checked by eye (TA), τ consistent
      with the small-signal loop (1/2πfc), then `robust.py` PASS.
- [x] P5 Power descent (sweeps, `optimize.py`), keep FoM ≤ 177 dB. Then one-change experiment: the friend's
      complementary (inverter) output drive, keep it only if power drops and the curve stays clean.
- [x] P6 Draw `design/final/amp_tran.asc` and `amp_noise.asc`; `verify_circuit` equivalent; lint clean;
      `evaluate.py --publish` and `robust.py` PASS on the `.asc`.
- [x] P7 Report rewritten for the new design (D6 with kT/C-inclusive SNR for EE4520 too, explicit SNR
      computation, power = all amplifier blocks on Vdd); `report-reviewer` clean.
- [x] P8 `spec-auditor` sign-off (24 Oct: PASS, no gaps); `check_done.py` DONE; hand over the form values.

## P1 paper budget (2026-10-13)

Devices from `tools/gmid.py` (LTspice tables). Flicker (NOIMOD 1): NMOS EF 0.825 (falls slower than 1/f, keeps
integrating to the loop bandwidth), PMOS EF 1.25. Rough integral 10 kHz to 100 MHz for 60 µA, 1 mS, L 0.25 µm:
NMOS about 50 µV input-referred, PMOS about 4 µV. Hence PMOS input pair, long-L NMOS loads at low gm/ID.
NMOS fT is about 4.7x PMOS at equal gm/ID (L 0.25 µm, gm/ID 16: 7.0 vs 1.46 GHz), so the stage-2 driver is NMOS.

- Swing: $V_{step}$ = 1.2 V diff (outputs 0.3 to 1.5 V). Driver Vdsat 0.14 V at 0.3 V, PMOS source Vsd 0.3 V.
- Noise: $C_{in} = C_L$ = 2.0 pF, $C_{fb}$ = 0.5 pF, kT/C 295 µV; allowed total 415 µV at 66.2 dB, so amplifier
  ≤ 292 µV. Model $v_n^2 \approx 2kT\gamma(1+g_{mL}/g_{m1})/(\beta C_c)$ ≈ 14 kT/Cc, about 16 kT/Cc with 1/f and
  stage 2: $C_c$ = 0.8 pF per side.
- β: input Cgg ≈ 60 fF (PMOS L 0.18 µm, gm/ID 16, 1.07 mS), β_act ≈ 0.5/2.58 = 0.194.
- Settling: needs an overdamped two-pole response (no zero crossing before 25 ns), p2 ≥ 4 ωc or p2 cancelled
  by the Rz zero. Closed-loop τ ≈ 0.72/ωc for p2 = 5 ωc. Target ωc = 2.6e8 rad/s (fc 41 MHz), τ ≈ 2.8 ns.
- $g_{m1} = \omega_c C_c/\beta$ = 1.07 mS: PMOS L 0.18 µm gm/ID 16, 67 µA per side, tail 134 µA.
- Class-A slewing: the rising output gets at most I2. Linear phase starts at a per-side error
  $e = I_2\tau/(C_2 + C_c)$; with I2 170 µA, $C_2 = C_L + (1-\beta)C_{fb} + C_{par}$ ≈ 2.55 pF: e ≈ 0.14 V, diff 0.28 V.
  Slew from 1.2 to 0.28 V diff at about 220 V/µs combined: 4.2 ns; linear ln(0.28/5.8e-4) = 6.2 τ = 17.3 ns.
  Total ≈ 21.5 ns < 24.8 ns.
- Stage 2: NMOS driver L 0.25 µm, gm/ID 10 (Vgs 0.634 V, same as the load's Vgs so the stage-1 output CM sits
  at the replica's Vbn), I2 170 µA, gm2 1.7 mS. p2 ≈ gm2/(C2 + C1 + C1C2/Cc) ≈ 6.2e8 rad/s = 2.4 ωc, so Rz
  cancels it: $R_z = (1/g_{m2})(C_2 + C_1 + C_c)/C_c$ ≈ 2.5 kΩ, p3 = 1/(Rz C1) ≈ 30 ωc.
- Gain: stage 1 ≈ 66 dB (P side gm·ro·ro limits), stage 2 ≈ 30 dB: A0 ≈ 96 dB, A0β ≈ 82 dB mid-swing.
- Bias (replica, EE4520 fig. 6 with the input device added): P replica = tail unit (gate Vbp) + input unit
  (gate vcmr), Vbp taken from the input unit's drain (self-cascode), Ibnp sinks it. N replica = Ibnp into
  NMOS cascode unit (gate Vcn) + load unit (gate tied to the top, Vbn). Vcn, Vcp from diodes with Ibcn, Ibcp.
  Fixed ratios Ibcn/Ibnp, Ibcp/Ibnp. Amplifier devices are integer multiples (m) of the replica units, N = 8.
- CMFB: 2 x 2 MΩ ∥ 50 fF sense, PMOS pair (tail = 2 tail units, 2 Ibnp), sense-side drain into an NMOS
  load-unit diode, mirrored into 1 to 2 load units per side (rest on Vbn). G_cm ≈ 60 to 120 µS, ω_cm ≈ 0.3 to 0.5 ωc.
- **Current target:** tail 134 + 2 x 170 + CMFB 17 = 491 µA, P ≈ 0.88 mW, FoM ≈ 174.4 dB (τ 2.8 ns, SNR 66.2).

## Session log (append one line per experiment: date, change, key numbers, verdict)

- 2026-10-13 archive: `legacy/` renamed `legacy-v1/` (git mv), attempt 2 copied to `legacy-v2/` (sources,
  report, evidence; old `results/` moved there, gitignored). `design/final`, `design/work`, `results/` start empty.
- 2026-10-13 TOOL CHANGE `tools/metrics.py`: τ per Aβ window (30, 40, 50 dB starts) as a diagnostic.
  On the example: 2.70 / 2.27 / 1.77 ns (accelerates into its first zero crossing); on attempt 2: 1.64 / 1.28 /
  1.29 ns. A window-ratio check would fail the passing example and pass attempt 2, so it is printed only.
  Attempt 2's real anomaly: 15 ns creep to 30 dB, then 30 dB in 5 ns, and τ 1.64 ns vs 1/(2π fc) = 4.0 ns.
- 2026-10-13 TOOL CHANGE `tools/evaluate.py`: new check "FoM_dB ≤ 177 (TA plausibility)". Stricter only.
  selftest OK after both changes.

- 2026-10-13 v01 class A (N 8, M2 20, Cc 0.8p, Rz 2.5k, Cin 2p, Vstep 1.2): .op all saturated after Vcn up
  (Wbcn 0.25u) and CMFB pair widened (Wcm 8u; 2u gave a 52 mV CM offset). x1 = 0.634 V = driver Vgs (replica works).
  Loop: T0 77 dB, fc 39.2 MHz, PM 92 deg, single pole to 1 GHz (Rz cancels p2). evaluate: P 0.912 mW, SNR 65.71,
  Abeta25 60.75, overshoot zero crossings at 14.9 and 32 ns. Rising output slew-limited at I2/(C2+Cc) = 50 V/us,
  x1n winds down to 0.33 V; after slewing the error decays with tau 4.5 ns = 1/(2 pi fc): Rz cancellation leaves
  a single closed-loop pole at wc (the budget assumed an overdamped pair, 0.72/wc).
- Noise split v01 (uV, thermal/flicker): input pair 153/31 each, NMOS loads (L 1u) 111/73 each, Rz 72 each,
  stage 2 about 78 total. Loads at L 2u (same W/L): flicker 73 -> about 37.
- Sweeps (class A): bigger Ccm (200f, 400f) and stronger CMFB (Ncm 3) made Abeta25 worse (CM correction leaks
  into DM through the asymmetric output halves); keep Ccm 50f, Ncm 1.
- pp01: variant PP = PMOS current-source gate AC-coupled to x1 (Cls 0.5p, Rb 2Meg to vbp), NMOS gate direct, M2 10
  (89 uA per side, gm2 = gmn + 0.75 gmp): P 0.628 mW, textbook first-order curve (tau windows 4.0/4.2/4.5 ns =
  1/wc), Abeta25 49 (too slow). Rz0 sweep: smaller Rz gives a near-critically-damped pair, faster.
- pp03 (PP, loads L 2u W 2.8u, Rz0 1.0k = Rz 2k, Cc 0.8p): evaluate **ALL PASS**: P 0.6273 mW, SNR 66.18,
  Abeta25 74.28, A25 88.98, Ts 23.05 ns, tau 2.428 ns, FoM 176.37 dB, first peak 27.7 ns, tau windows
  2.43/2.19/1.99 ns. robust PASS (worst Abeta 74.23). Rz0 0.9k: zero crossing at 20.1 ns (FAIL), FoM 177.2.
- a03 class A (loads L 2u, M2 24, Rz0 1.2k): P 1.040 mW, SNR 66.12, Abeta25 83.1 but zero crossings at 19.0 and
  23.5 ns (FAIL); curve = 12 ns slew creep then a steep rise, the shape the TA objected to. Class A needs more than
  about 1.1 mW to settle cleanly because the rising side only gets I2.
- 2026-10-13 user decision: push-pull CS (class A needs > 1.1 mW and shows the slew-creep curve).
- pp03 checks: loop T0 77.6 dB (72.1 dB at both settled extremes), fc 36 MHz, PM 80 deg. CM loop (injection at the
  CMFB output, bench_cmloop.cir): fc 8.7 MHz, PM 81.5 deg. Output CM excursion during the step -17.8/+4.1 mV.
  2 us transient: error flat at 204 uV (static floor) from 35 ns on, so the Cls/Rb high-pass (about 120 kHz) adds
  no slow tail. 12 mV small-step tau 2.54 ns vs 2.43 ns large step: settling is linear (closed-loop poles above
  wc because of p2 and the Rz zero), unlike attempt 2.
- TOOL CHANGE `tools/optimize.py`: FoM <= 177 constraint (TA), --extra-snr/--extra-ab margins, --seed-params,
  unique temp dir per trial (two workers had picked up the same enqueued trial and deleted each other's files),
  a crashing trial is now an infeasible point instead of ending the study. Evaluation thresholds unchanged.
- Studies d1/d2 (wide space): 0 feasible in 110/34 trials; Abeta is a sharp function of Rz relative to p2.
  Rz now tracks the cancelling value: Rz = Rz0 (20/M2)(Cc + 1.2 Cin)/(4 Cc); best Rz0 then flat vs Ibnp.
- Bias rebalance: Lbcn 1u -> 1.4u (Vcn +90 mV), Lbcp 1u -> 1.3u (Vcp -140 mV): load margin 52 -> 123 mV, input
  pair 112 -> 223 mV at Ibnp 8.4u; below 6.8u the old bias put the loads in triode (Abeta cliff).
- pp04 (Ibnp 7.6u, Rz0 1.05k): ALL PASS, P 0.5736 mW, SNR 66.16, Abeta25 72.22, A25 86.83, Ts 23.91, tau 2.515,
  FoM 176.58, first peak 28.7 ns.
- Study d3 (seeded pp04, 260 trials, 58+ feasible): converges at about 0.529 mW with FoM 176.85 to 177.0 (TA
  ceiling binds) and N, M2 at their upper and Ibnp at its lower bound. Many winners had the first zero crossing
  at 25.5 to 26 ns. Chose with robustness filters (first crossing >= 27 ns, Ts <= 24.3, Abeta >= 68, FoM <= 176.8).
- pp05 (rounded: Ibnp 6.4u, N 9, M2 11, Cc 0.77p, Rz0 1.2k, Cls 0.68p, Cin 2.15p, Vstep 1.2): ALL PASS, P 0.5446,
  SNR 66.19, Abeta25 73.43, Ts 23.86, tau 2.510, FoM 176.85, first crossing 27.2 ns; robust PASS.
  Sensitivity: +-1 % on Cc, Rz0, Cls, Ibnp all keep Abeta >= 68.8 and first crossing >= 25.65 ns; -2 % Cc or
  -1 %/-1 % Cc and Rz move the crossing to 24.5 to 24.6 ns. Cc window for the full spec 0.757 to 0.781 pF, nominal
  0.77 near its center. Bias rebalanced (Lbcn 1.4u, Lbcp 1.3u) before the descent.
- Final (.asc): identical numbers. Extras (report_extra.py): loop fc 34.7 MHz, PM 80.1 deg, T0 81.1 dB (76.4 dB at
  the settled extreme); CM loop fc 7.6 MHz, 82 deg; CM excursion 18.4 mV; 1 % step tau 2.60 ns (linear);
  replica nodes bp0/bn5 1.434/0.275 V equal to tail/b1p. Noise power: input pair 51 %, loads 36 %, Rz 8 %,
  stage 2 5 %, flicker 7 %.
- TOOL CHANGE `tools/report_extra.py` rewritten for the attempt-3 circuit (macros for the new text).
- spec-auditor (13 Oct): PASS. Reproduced every number, element-by-element equivalence, all rules, saturation with
  the step in both polarities (output devices >= 156 mV), selftest OK, no loosened thresholds. Noted Ibnp 6.0u also
  passes (0.5142 mW, Ts 24.61 ns, first crossing 26.79 ns, FoM 176.98): kept 6.4u for ringing/FoM margin.
- report-reviewer (13 Oct, estimate 7 to 8): fixed. "Straight lines" was wrong: the response is linear but slightly
  underdamped (tau windows 2.510/2.20/1.87 ns; 1 % step 2.60/2.38/2.17), heading for the zero crossing at 27.2 ns;
  dominant closed-loop pole from the loop 3.48 ns, FoM with it 175.43 dB, now stated. Overshoot 12 uV above ideal,
  149 uV above the final value. Floors quoted as plotted (78.9 dB, 79.0 dB after 2 us). D6 now carries the kT/C
  share term (47 % vs 85 %, -2.59 dB); amplifier remainder +4.89 dB. Bias text no longer overclaims (vcn/vcp are
  the fig. 6 diodes). Stage-2 deviation from class A stated with gm/ID 11.1/10.9. zp/zn voltages added.
- TOOL CHANGE `tools/report_extra.py`: overshoot, window tau, dominant-pole FoM, small-step T30, floors, 2 us run,
  output-device margins with the step applied.
- Report re-check (13 Oct): fixed the last items: overshoot attributed to the loop zeros (PM 80 deg means nearly
  real poles), D6 gained a settling-shape term (+1.42 dB, 2.51 vs 3.48 ns; amplifier remainder +3.47 dB), zp/zn
  labels moved, Cload in the D2 caption. TOOL CHANGE `tools/opvals.py`: drain currents from the .op raw (full
  precision) at 4 significant figures, so D3 sums close visibly (M0 115.2 = 2 x 57.60 uA); the TA checked KCL sums.
- 2026-10-13 verification pass (user request): KCL script over the .op raw (all four terminal currents): worst node
  residual 15 pA; all branch sums exact; I(Vdd) 276.616 uA = 115.200 + 148.786 + 12.631. Formula script: 37 checks.
  Fixes: D6 had a double-counted tau-window term (removed; the settling-shape term alone converts to the dominant pole)
  and rounding (D6 now computed in report_extra at full precision; parts add up exactly); D3 currents now 4 s.f. so
  KCL is visible; CM loop wording (broken-loop gain; the test circuit returns beta of the output CM to the input pair,
  a positive path through the tail's output resistance that the CMFB dominates: phase -180 at DC, 82 deg margin).
- Bias: cascode-gate diodes changed from L 1.4/1.3 um to the cascode length 0.25 um (wide-swing bias, kcn 6, kcp 4,
  W 0.34u/0.36u), same vcn/vcp within 0.5 mV. Re-evaluated (pp06): ALL PASS, P 0.5447, Abeta 74.37, first crossing 26.92.
- 2026-10-24 (user request: plots straight from LTspice, end-to-end check). Deadline confirmed on Brightspace:
  Sun 8 Nov 2026 23:59, form https://edu.nl/7turd, file 5714699.pdf, at most 2 submissions.
  Benches gained LTspice-side measurements (no circuit change): tran `.meas` T30, T38p6 (WHEN Abeta = 30 / 38.6 dB,
  RISE=1), T30_step, T38p6_step, tau; noise `.meas` Vn_kTC (42kT/Cin), Vn_tot, SNR_dB. gen_asc.py regenerated both
  `.asc` (only the directives box grew); verify_circuit equivalent (65 components, 35 nets, 0 findings), lint 0/0.
  LTspice prints T30 15.163 ns, T38.6 17.664 ns, tau 2.5003 ns, P 0.5447 mW, SNR 66.197 dB.
  NEW TOOL `tools/ltgui.py`: runs the deliverable `.asc` in the LTspice XVII GUI (Wine, private Xvfb, private
  `-ini`), loads a generated `.plt` (traces, `Parametric: "time-10n"` axis, Line/Text annotations; LTspice reads `.plt`
  as cp1252 only, so no Greek on the plot) and screenshots the waveform window: report/figures/d4_ltspice.png and
  d5_ltspice.png. Values on the plots are the `.meas` lines of that same GUI run, cross-checked against latest.json.
  The report's D4/D5 now use these LTspice screenshots (the matplotlib figures are no longer included).
  TOOL CHANGE `tools/evaluate.py`: item 11 (amplifier noise) is now LTspice's own `.meas INTEG` (303.131 uV, what a TA
  sees in the log) instead of numpy's trapezoid on the raw data (303.137 uV); the trapezoid stays as a cross-check
  (abort if they differ by > 0.1 %). Total noise 415.75 -> 415.74 uV; SNR 66.20, FoM 176.87 unchanged. selftest OK.
  NEW TOOL `tools/crosscheck.py` (kcl, formulas): KCL at 34 nodes (worst 14.6 pA), 12 branch sums exact, I(Vdd) split
  exact, replica copies exact (M11 +5.7 % from Vsd, CMFB devices -1.3/+1.8 % from the CM correction, x1 13.9 mV from
  vbnr because the CMFB sets it: page 8 wording softened to "held by the CMFB near the replica's vbn"); 37 formula
  checks, 0 problems. evaluate --publish and robust on the .asc: ALL PASS, robust PASS.
- 2026-10-24 independent reviews. spec-auditor: PASS, signs off (every number reproduced; no rule broken; no
  threshold moved; Ibnp 6.0u would give 0.5143 mW but FoM 177.007 fails the TA ceiling, so 6.4u stays).
  report-reviewer (estimate 8 to 9): no wrong numbers; fixed its items: D4 y axis from -20 dB (Abeta visibly starts
  at 0 dB; it first dips 0.34 dB below for 0.7 ns: feedthrough through Cfb), gap 20log(1/beta_act) 14.18 vs ideal
  13.98 dB marked, circles at 25 ns; D5 inset with LTspice's own Ctrl-click integration (303.13 uV over 10 kHz to
  100 GHz, assignment fig. 10); page 8 D4 paragraph reordered by plot feature (start/gap, slewing, linear part with
  1/(2 pi fc) = 4.58 ns vs dominant pole 3.47 ns vs window tau, spikes A 26.92 / Abeta 27.15 ns, floor), class-AB
  single level shifter argued directly, wording ("noise power", "ended at 1.2 V"); D3 caption lists every no-DC
  branch; bias drawing larger, labels moved off wires, b_n5 named. TOOL CHANGE `tools/evaluate.py --publish`: new
  macros resFirstPeakA, resFirstPeakAbeta, resFlickCornerMHz (output only). selftest OK, crosscheck OK.
- 2026-10-24 prose pass (user request, humanizer skill): D1 notes, D2/D3/D4/D5 captions, D6 and page 8 rewritten in
  shorter plain sentences (no italic run-in labels, fewer stacked parentheses, same macros, still 8 pages). Local AI-text
  detectors on the PDF prose (scratch venv, nothing uploaded): word-weighted P(AI) before/after: chatgpt-detector-roberta
  0.002/0.002, fakespot roberta 0.027/0.012 (max 0.50/0.11), OpenAI roberta detector 0.136/0.008 (max 0.86/0.13).
  crosscheck formulas 37/0 after the edit.
- 2026-10-24 report-reviewer re-check: items 1 to 13 fixed, estimate 8 to 9 (8.5). Last fixes: Fig. 3 v_bp label back at
  the Cbig node (P-side Rd shortened, right column moved right), bias note split in two lines, CMFB figures wider
  (0.46/0.52 linewidth), D4 gap arrow removed, D4 caption explains the red line at t = 0. crosscheck formulas 37/0.
- 2026-10-25 (user: one design, one FoM; is the TA's 177 dB ceiling real?). The TA's figure is empirical (best
  course designs over 5 to 10 years: about 176, at most 177 dB). The course's own efficiency analysis (Bult lecture 1,
  tud-notes: tau = A_req C_L/gm, gm/ID, eta_cur, NEF) gives for one single-stage amplifier in this test circuit with
  kT/C noise only: FoM_1 = 2 pi (2 VDD/(gm/ID)) (C_L,eff/(beta Cin)) 84 kT/Vstep^2, 178.8 dB at gm/ID 25 and 1.2 V,
  so 177 is a sound plausibility line at this swing (attempt 2's 183 dB beat even this ideal reference). Report: the
  hypothetical "FoM with the dominant-pole tau" (175.44) removed; page 8 now gives the one FoM as an exact sum:
  177.06 (reference at gm/ID 16.7) - 4.19 (38 % of current in the pair) - 3.29 (amplifier noise) + 7.29 (tau 2.500 vs
  13.4 ns single stage) = 176.87 dB. TOOL CHANGE report_extra.py (macros xFoMideal..xTauOne, M0 current from the op
  raw at full precision; xFoMdom dropped), crosscheck.py (6 new checks, 42/0). Page 8 tightened to stay 8 pages.

## Failed approaches (do not retry without a new reason)

- Attempt 3 class-A stage 2 (current-source PMOS on vbp): rising output slew-limited at I2/(C2+Cc); 1.04 mW
  still rang before 25 ns after a 12 ns slew creep (design/work/classA/).

- Attempt 2 (Oct 2026, `legacy-v2/`): class-AB output with one RC level shifter, stacked complementary input,
  current-buffer compensation. Passed every numeric check at 0.19 mW but the TA rejected it: FoM 183 dB is
  implausible, the settling curve is not ordinary two-stage settling, MN2 near cutoff, bias not a replica.
- Attempt 1 (June 2026, `legacy-v1/`): single-stage gain-boosted folded cascode + current reuse + SC-CMFB:
  2.04 mW and settling short (77.2/62.7 dB at 25 ns). Single-pole settling needs about 7.7 τ.
- Loop bench with 1 TH / 1 TF break: LTspice lands the `.op` in a wrong state. Use the series-injection bench.
