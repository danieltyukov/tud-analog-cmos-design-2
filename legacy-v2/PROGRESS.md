# PROGRESS (resit attempt, started 5 Oct 2026)

## Current state

Phase: DONE (P8). Final design v18 (CR topology: stacked complementary input, current-buffer compensation,
class-AB QFG output, CT CMFB; Ib 9.0u, tsc 0.686, ko 0.505, knr 0.60, VCMI 0.8107, Vstep 1.478 V, Cin 1.43p,
Cc 0.389p, Cls 0.63p, Won 1.46u, Rin 125Meg). Drawn design/final/amp_{tran,noise}.asc (gen_asc.py; verify_circuit
equivalent, 62 components, 0 findings; lint 0/0). evaluate --tag final --publish on the .asc: ALL PASS, P 0.1918 mW
(I(Vdd) 0.10654 mA), SNR 66.08, Abeta 69.34, A 84.27, Ts 22.29 ns, tau 1.641 ns, FoM 183.12 dB, output CM 0.899 V.
robust PASS (worst Abeta 69.32); ko and Cc +-1 % all pass; every FET saturated with the step applied (both
polarities, worst 27 mV); loop T0 81.0 dB, fc 39.8 MHz, PM 78.4 deg. Report 8 pages (copy report/5714699.pdf).
Form values: results/latest.json (tag final). Archives: design/work/archive_v13, archive_v14, archive_v15.

## Plan (tick a box only with tool evidence; add sub-steps as needed)

- [x] P0 Harness: tools verified on `example/` (selftest OK), benches validated, report skeleton builds (8 pages).
- [x] P1 Budget on paper (spec-auditor PASS): $V_{step}$, $C_{in}$, $C_c$, $f_c$, $A_0$, currents per branch, noise split
      (`metrics.py budget`, `gmid.py`). Architecture A from `brief/design-strategy.md` unless the budget says otherwise.
      Gate: paper SNR ≥ 66.3 dB, settling budget closes in 24 ns, total current target written down.
- [x] P2 Bias block (on `Vddb`, EE4520 style, decoupled) + stage 1 + stage 2 + compensation in
      `design/work/amp.inc`, temporarily with the simplest real CMFB that works.
      Gate: `.op` all saturated at mid and at both output extremes; loop fc and PM on target.
- [x] P3 Real CMFB designed and checked (CM loop PM ≥ 60°, CM excursion during the step < 50 mV).
- [x] P4 Full `evaluate.py` PASS on the netlist benches, then `robust.py` PASS.
- [x] P5 Power descent (sweeps, `optimize.py`); re-check P4 gates at the final point. Log the power trajectory.
- [x] P6 Draw `design/final/amp_tran.asc` and `amp_noise.asc` (`draw-asc` skill); `verify_circuit` equivalent
      to the netlist; `asc_lint` clean; `evaluate.py --publish` and `robust.py` PASS on the `.asc`.
- [x] P7 Report: D2/D3 CircuiTikZ with `\Vtag`/`\Itag`, D6 and short explanation; 8 pages; `report-reviewer` clean.
- [x] P8 `spec-auditor` sign-off; `check_done.py` DONE; hand the user the form values from `results/latest.json`.

## P1 paper budget (2026-10-05)

Architecture A, refined: two-stage, PMOS-input telescopic stage 1 (PMOS + NMOS cascodes, long-L NMOS
loads), **current-buffer (Ahuja) compensation**: $C_c$ from each output to the source of the NMOS cascode
(node A), class-AB output (NMOS gate from $v_1$, PMOS gate through $C_{ls}$ with $R_b$ to a bias line),
continuous-time CMFB (2 MΩ ∥ $C_{CM}$ sense, PMOS diff pair vs vcmr, mirror into 25 % of the stage-1 loads).

- Swing: $V_{step}$ = 1.2 V diff (outputs 0.30 to 1.50 V). Later try 1.3 V.
- Noise: $C_{in} = C_L$ = 2.2 pF, $C_{fb}$ = 0.55 pF, kT/C = 281 µV (42 kT/Cin). Allowed total at 66.3 dB: 411 µV.
  α calibration: the friend's 326 µV at $C_c$ = 0.72 pF minus Rin/Rfb (2 × 77 µV) and Rz (2 × 60 µV) noise,
  both absent here, leaves 295 µV, so α = 15.2 (18.5 was the raw value). First-principles check:
  $2\gamma(1+g_{mL}/g_{m1})/\beta$ = 2(2/3)(1.5)/0.19 = 10.5 plus 1/f, cascode, stage 2. With $C_c$ = 0.75 pF:
  amp 290 µV, total 404 µV, **paper SNR 66.45 dB** (α = 18.5 would give 65.9 dB; then raise $C_c$ to 0.95 pF).
- Settling: ε = 4.84e-4 at 24.8 ns. Static: $A_0$(HF, gm2 = gmn+gmp) ≈ 100 dB, $A_0\beta$ ≈ 86 dB, 5e-5.
  Slew ≈ $(\beta V_{step}/V_{lin} - 1)/\omega_c$ = (0.23/0.125 − 1)/ω_c ≈ 3.3 ns. Linear from 0.6 of the error,
  critically damped $(1+x)e^{-x}$ = 7.2e-4 needs x = 9.6, i.e. 19.1 ns at $f_c$ = 40 MHz. Total 22.4 ns < 24.8 ns. **Closes.**
- $g_{m1} = \omega_c C_c/\beta$ = 2π·40 MHz·0.75 pF/0.193 = 0.98 mS per input device.
- Current-buffer loop: $T = \frac{\beta g_{m1}}{sC_c}\frac{1+sC_c/g_{mc}}{1 + s\frac{C_1(C_L+C_c)}{g_{m2}C_c} + s^2\frac{C_1C_L}{g_{mc}g_{m2}}}$,
  $\omega_n^2 = g_{mc}g_{m2}/(C_1C_L)$, $\zeta = \frac{C_L+C_c}{2C_c}\sqrt{\frac{g_{mc}C_1}{g_{m2}C_L}}$. With $g_{mc}$ 0.8 mS, $C_1$ 0.1 pF,
  $C_L$ 2.7 pF, $g_{m2}$ 0.6 mS: $\omega_n$ = 5.3 ω_c, ζ ≈ 0.5, LHP zero at 4.3 ω_c. So $g_{m2}$ needs only about 0.6 mS
  (Miller would need about 2.5 mS).
- Devices (gmid tables, L in µm): input PMOS L 0.25 gm/ID 16 (W ≈ 53, Cgg ≈ 100 fF, Vdsat 94 mV); PMOS cascode
  L 0.36 gm/ID 10; NMOS cascode L 0.36 gm/ID 14 (gm 0.8 mS); NMOS loads L 2 gm/ID 8 (Vdsat 0.24, gm_L/gm1 = 0.5);
  tail PMOS L 0.5 gm/ID 10; output NMOS L 0.36 gm/ID 10 (Vgs 0.64 = $v_1$), output PMOS L 0.25 gm/ID 13.
  Headroom: $v_1$ = 0.64, node A ≈ 0.35 (load margin ≈ 0.1 V, cascode margin ≈ 0.18 V); tail node 1.43 V.
- **Current target:** tail 122 µA + output 2 × 28 µA + CMFB 6 µA = 184 µA quiescent. Class-AB slew charge drawn
  from Vdd by the rising output, $(C_L + C_{fb} + C_c)\cdot V_{step}/2$ = 2.1 pC, averages 84 µA over the 25 ns window,
  so the reported (window) current ≈ 270 µA, **P ≈ 0.49 mW**. Floor of this charge term ∝ $1/V_{step}$.

## Session log (append one line per experiment: date, change, key numbers, verdict)

- 2026-10-05 harness: selftest reproduces example (A 80.81, Aβ 66.01, τ 2.697 ns, Vn 326.4 µV).
  Example amp in our bench (50 ps edge, 100 MΩ noiseless Rin/Rfb): Aβ 65.7 dB, i.e. its pass was bench-dependent.

- 2026-10-05 TOOL FIX `tools/optimize.py` `violations()`: a design with no ringing peak (first peak = inf) gave
  25 − inf = −inf, which the non-finite guard mapped to a +100 violation, so the optimizer rejected the best
  (monotonic) designs. evaluate.py already treats inf as "after 25 ns". Now −inf maps to −100 (satisfied);
  NaN/+inf stay violations. Thresholds unchanged. selftest OK after the change.
- 2026-10-05 v01 (first amp.inc: PMOS-in telescopic, Cc 0.75p into NMOS-cascode source, class-AB out, CT CMFB;
  Cin 2.2p, Vstep 1.2): .op all sat (min margin 107 mV), Iq 185 µA. Loop fc 39.8 MHz, PM 96° (zero gm_c/Cc ≈ 177 MHz
  makes a −13 dB shelf to 700 MHz). evaluate: P 0.428 mW, SNR 65.74 (Vn 336 µV, shelf adds ≈ 220 µV above 100 MHz),
  Aβ25 45.7, τ 4.56 ns, settles 36 ns. Slew ≈ 10 ns: rising side v1 falls until the NMOS cascode cuts off, slew ≈ I_load/Cc.
- v02: floating C1d = 100f between v1n/v1p (damping cap at the stage-1 outputs): loop PM 76.5°, Vn 300 µV (shelf gone),
  SNR 66.30, Aβ25 85.8, settles 16.9 ns, but FAIL first ringing peak 17.7 ns (tiny overshoot, error crosses zero).
- Sweeps (Mt × C1d × ko): behaviour flips abruptly between monotonic-but-slow and early zero crossing. Small-signal
  (1 mV) step shows the same 4 ns single-pole tail, so it is linear: with the cascode zero at ≈ p2 the closed loop is
  a pole near ω_c, not a critically damped pair. Larger C1d (> 70f) gives early ringing (peak 12 to 15 ns).
- Mt 10 collapsed (fixed NMOS loads 2 × 47 µA > tail): `kn` now tracks `Mt` (`kn = knr·Mt`).
- g5: Mt 14, C1d 60f, ko 1.1: every check passes in grid (P 0.439 mW, SNR 66.30, Aβ25 73.7, Ts 21.0, no peak),
  but C1d 70f at the same Mt rings at 13.8 ns: sensitive.

- Swing scan (single-pair design): Vstep 1.3/1.4/1.5 V with Cin, Cc ∝ 1/V²: passes at 0.394 / 0.348 / 0.321 mW.
  DC loop gain at the settled extremes (loop bench `Vext`): 86.6 dB mid, 80.8 (1.3 V), 77.5 (1.4 V), 70.5 (1.5 V).
  Chose 1.4 V (Cin 1.616p, Cc 0.55p). Single-pair design archived in `design/work/archive_singlepair/` (Mt 10, C1d ≈ 58f,
  0.348 mW, window C1d 53 to 63f).
- **Topology change: stacked complementary input (CR).** PMOS pair on a top tail and NMOS pair (L 1 µm) on a bottom
  tail, both gates on the summing node, both drains cascoded onto v1: same gm and slew rate for half the current, no
  load-noise term. First try slow because the output NMOS was made weak (W 1.05u L 0.5u) to raise v1; restored
  Won 2u/0.36u. CR at Mt 6, C1d 0: all PASS, 0.285 mW (grid). Noise: inputs 85 %, cascodes 14 %; 230 of 375 µV lies
  above 100 MHz (residual loop shelf).
- CM loop (CR): Middlebrook break at the CMFB tail gate: |T_cm| 28.5 dB, crossover 10.2 MHz, 84° from −180°. H(0) is
  positive because an internal CM loop (output CM → Rfb/Rin → summing-node CM → tail gds → v1) is positive with gain > 1;
  Nyquist: one CCW encirclement = one RHP open-loop pole, closed loop stable (transient confirms). CM excursion 28 mV.
- Robust optimizer (scratch `ropt.py`: Optuna, optimize.py constraints, plus settling must also pass at ko × 0.93 and
  × 1.07): round 1, 200 trials over Mt, ko, Cls, fcc, C1d, Cc, Cin, Wcn. Best robust 0.246 mW; cluster at Mt 5,
  ko 0.87, Cc 0.43p, Cin 1.69p (e.g. #123: 0.2556 mW, worst Aβ 73 dB, Ts 20.9 ns, SNR 66.11).
- DC gain of CR is headroom-limited: v1 = Vgs(Mon) ≈ 0.6 V leaves ≈ 0.15 V on M1n and Mcn1 (gm/gds 25 and 21 there,
  vs 260/90 at Vds 0.6 V), A1 = 60.8 dB; longer L in stage 1 does not help. Accepted (worth ≈ 3 % power).
- `design/work/gen_asc.py` generates `design/final/amp_tran.asc`/`amp_noise.asc` from the netlist (drawn symbols, wires,
  stub-flags for rails/bias/ports only, titled boxes, one directives box). verify_circuit: equivalent, 0 findings.

- Round 2 (adds Ib, Wctl, VoutStep): unproductive, stopped. Scaling Ib also moves the cascode-bias diode voltages,
  so many trials were dead circuits (Aβ 0.1 dB). Do not optimise Ib together with fixed cascode-bias diode sizes.
- Picked round-1 #199, rounded (Cc 0.443p, Cls 0.52p, fcc 0.61, C1d 2.5f, Cin 1.66p, Wcn 8.5u); sensitivity Cc ±3 %,
  C1d ×0.5/×2, Cls ±10 %: all pass. C1d 0 passes but loses 1.6 dB/0.9 ns, kept. ko < 0.68 rings (peak ≈ 19 ns).
- v10 (ko 0.78, Wop 6u): evaluate ALL PASS, P 0.2495 mW, robust PASS. But CM excursion 69.5 mV peak at 3.5 ns.
  Doubling the CMFB mirror ratio (Wc3 0.5u, knr 0.53) did not reduce the peak (67.9 mV, it is a 3 ns slewing transient)
  and cost DM settling (Aβ 66.3). Root cause: pull-down (NMOS) stronger than pull-up (PMOS) during slewing.
- **v11 (final point): Wop 6u → 12u (same quiescent current), ko 0.72.** evaluate ALL PASS: P 0.2499 mW,
  SNR 66.21, Aβ 70.71, A 85.79, Ts 21.74 ns, τ 1.54 ns, FoM 182.37 dB, no ringing peak, min sat margin 37 mV.
  CM excursion 48.4 mV peak at 3.3 ns, 6.6 mV at 25 ns. CM loop 12.6 MHz, 82° from −180°. DM loop fc 49.8 MHz,
  PM 77.3°, GM 19.4 dB, T0 75.1 dB mid / 68.2 dB at ±0.7 V outputs (all FETs saturated there; worst 30.6 mV on
  mcn2/mcn1 per spec-auditor; my earlier 36 mV was measured on the v10 geometry).
  ko 0.65 to 0.86 all pass (0.60 rings). Ib 9.0u fails settling (Aβ 65.8): 9.6u kept (settling is steep in current).

- P6: regenerated design/final/amp_tran.asc + amp_noise.asc from v11 (gen_asc.py). verify_circuit equivalent to
  reference_tran.cir, 0 findings (both sheets); asc_lint 0 errors/0 warnings (8.61 pF main C, 50 nF decoupling).
  evaluate --tag final --publish on the .asc: ALL PASS, identical to the netlist (P 0.2499 mW). robust on .asc PASS.
  Internal nets carry one name label each (ntp, nb1/2, v1n/p, na1/2, ntn, gp1/2, vcms, ncs, ncm2, inp, inn) on
  already-wired nets, so opvals/D2 node names are traceable; no connection is made by these labels.
- NEW TOOL `tools/report_extra.py` (report plumbing only, no thresholds): re-measures loop gain (mid and ±VoutStep),
  CM loop, CM excursion, noise and power split from the final design, writes report/generated/extra.tex so the
  explanation page quotes no hand-typed numbers.
- EE4520 baseline: its report used SNR_lin = 10764.5 (the 80.64 dB spec) in the FoM; with its achieved 80.85 dB the
  same P and τ give 175.41 dB instead of 175.20 dB. D6 shows both and uses the consistent value for the steps.

- TOOL CHANGE `tools/evaluate.py` publish(): rows 8 (Power) and 9 (I(Vdd)) now print 4 decimals instead of 2
  ("0.25" was too coarse for the D1 table, which must match the form). Formatting only, no threshold touched.
  selftest OK after the change.
- spec-auditor (P1 to P5): P1 to P4 PASS. P5 GAP: Ib 9.2u passes evaluate (0.2437 mW, Aβ 67.65, Ts 24.0) and
  robust; 9.0u fails partly because vcn/vcp shift with Ib (m1n margin collapses), not only speed.

- **v12 = FINAL: Ib 9.6u → 9.2u (auditor P5 finding).** Grid: ko 0.68/0.72/0.76 all pass at Ib 9.2u. Netlist
  evaluate v12 ALL PASS. Regenerated .asc (verify_circuit equivalent, 0 findings; lint clean), evaluate --tag final
  --publish on the .asc: ALL PASS, P 0.2437 mW, I(Vdd) 0.1354 mA, SNR 66.19, Aβ 67.65, A 82.51, Ts 24.01 ns,
  τ 1.85 ns, FoM 181.67 dB, min sat margin 27 mV. robust on .asc PASS (worst Aβ 67.58, Ts 24.04 ns).
  report_extra: fc 47.9 MHz, PM 77.8°, CM loop 12.3 MHz/82°, CM excursion 46.1 mV, Iq 79.1 µA, window 135.4 µA.

- Schematic hygiene: block titles shortened (they ran past their boxes) and top boxes raised so titles clear the
  vdd stubs. Re-verified (equivalent, 0 findings), lint clean, evaluate --tag final --publish ALL PASS (P 0.2437 mW,
  unchanged), robust PASS, report rebuilt (8 pages).

- report-reviewer (first pass): estimated 8 to 9; correctness findings fixed:
  (1) D6 physics: for kT/C-limited designs C ∝ SNR_lin², so the FoM is SNR-neutral (my "FoM ∝ 1/SNR" was wrong);
  (2) EE4520's 80.85 dB excluded kT/C: like-for-like baseline computed in LaTeX from its network (gain 8,
  18/2.25/18 pF): +183 µV, SNR 72.60 dB, FoM 167.17 dB, difference +14.50 dB; contributions separated (β 2.34 dB,
  swing 1.34 dB, τ definition 2.54 dB, circuit 8.28 dB); (3) τ = 1.85 ns lies in the fast post-slew segment,
  1/(2πfc) = 3.32 ns governs the tail; (4) β wording per TA note; (5) gap grows 14.41 → 14.86 (25 ns) → 15.2 dB:
  verified mechanism, input-device drains swing 25× (NMOS) / 8× (PMOS) v_gd at 1 kHz in the loop bench (< 0.5× above
  1 MHz), so Cgd is Miller-multiplied in the slow tail; (6) sizing details (gm/ID 15.6, gm1 0.700 mS, fc = β gm1/2πCc
  = 47.9 MHz, noise split, 1/f share 9 %, EF values); (8) bias "same L" claim limited to tails/output mirrors;
  (9) CMFB current only (bias excluded). Cosmetics: labels off wires, bias names v_bp.., numeric k values, FoM spec
  cells, page numbers (title = page 1), D4 plot (no t=0 spike, y-range fitted, 1/β gap marked).
- TOOL CHANGE `tools/metrics.py` plot_settling(): plotting only (start after the input edge, fitted y-range, gap
  arrow). TOOL CHANGE `tools/report_extra.py`: adds flicker share, Miller ratios, op gm/gm-ID, design-param macros.
  selftest OK after both.

- report-reviewer second pass (est. 8.5 to 9.5): fixed D6 decomposition (test-network terms: kT/C noise gain 146 vs
  42 kT/Cin 5.41 dB, ideal β 2.55 dB, C_L,eff/Cin −0.33 dB; swing 1.34 dB; τ definition from the fitted small-signal
  tail τ (16 to 24 ns) instead of 1/(2πfc); remainder = circuit efficiency); Aβ now plotted from t_step (0 dB) and
  the wrong-way feedthrough dip explained; cascode/Miller wording; A0β balanced vs extremes; D4 labels (25 ns, spec
  lines), D5 legend moved; column label, rms font, exact τ for Pτ, larger sub-figure fonts.
  report_extra adds xTauTail, xKick, xAbDip, xTauExact. metrics.py plotting only. The spec-auditor's exploratory
  evaluate runs (c_h_*.cir) overwrote results/latest.json and the robust record; restored below on the final .asc.

- spec-auditor final sign-off (P5 to P8): PASS. Remaining power it found: Ib 9.0u/ko 0.64 0.2375 mW (CM 49.8 mV,
  under the 50 mV P3 gate). Grid confirmed (ko 0.60 to 0.66 pass; 0.60 has CM 52.4 mV; 0.69 too slow; ringing edge
  at Ib 9.0u between ko 0.52 and 0.56 per auditor). Adopted: **v13 FINAL Ib 9.0u, ko 0.64**. Netlist v13 ALL PASS;
  .asc regenerated, equivalent, lint clean; evaluate --tag final --publish ALL PASS P 0.2375 mW; robust PASS.
  Also fixed: noise sheet no longer carries unused Tsettle/tstop (hygiene rule 5); publish prints T30/T38.6/τ with
  3 decimals so D1 arithmetic closes (TOOL CHANGE evaluate.py publish format, selftest OK).
  Power trajectory: 0.428 (v01) → 0.348 (single pair, 1.4 V) → 0.285 (CR) → 0.2499 (v11) → 0.2437 (v12) → 0.2375 mW.

- Portability: the .asc used an absolute LTspice XVII model path. Now `.lib 'log018.l' TT` with
  design/final/log018.l next to the sheets; that copy is the lecturer's file with its 20 internal
  self-includes (absolute LTspice IV path) made relative, model parameters unchanged (diff: include lines only).
  XVII needs the single quotes (unquoted, it read "log018.l TT" as the file name). Proven by running LTspice
  directly (no tool path rewriting) on a relocated uniquely named copy and on the final sheets in a fresh folder:
  A25 81.5866, Ab25 66.7564, P 0.2375 mW, Vn_amp 360.3 µV. Re-verified (equivalent, lint clean), evaluate --tag final
  --publish ALL PASS (0.2375 mW), robust PASS, report rebuilt, report/5714699.pdf refreshed. README rewritten.
- Housekeeping: a watcher loop of mine (`while pgrep -f "ropt.py cr_r1"`) never ended because pgrep matched its
  own command line; killed. Lesson: use `pgrep -f "[r]opt.py"` style patterns.

- Report prose rewritten with the humanizer skill (D1 notes, D6 text, short explanation): first-person student voice,
  shorter sentences, no enumerated lists or stacked parentheticals; every macro, number and verified claim unchanged.
  FoM proportionality moved to a displayed equation (removed an overfull line). 8 pages, no ??, check_done DONE.

- 2026-10-06 LITERATURE (IEEE Xplore MCP, institutional sign-in): six full papers downloaded to reference/papers/
  (Akter JSSC 2018 class-AB RA; Kim IEEE Access 2020 SRE class-AB OTA; Lopez-Martin JSSC 2005 super class-AB;
  Hurst TCAS-I 2004 current-buffer Miller; Giustolisi TCAS-I 2021 settling design; Yavari TCAS-II 2005 slew rate).
  Notes and applicability in reference/papers/NOTES-resit-2026-10.md. Verdict: split-capacitor biasing, SRE mirrors
  and super class-AB inputs do not carry over (forbidden switches/split network, or net extra charge in the 25 ns
  window, or headroom). Corrected diagnosis: v13 has no loop-gain shelf; alpha 13.9 vs 7.0 = BSIM3 noimod thermal
  (gm+gmbs+gds) x1.35, noise bandwidth x1.2, flicker 8 %, cascodes 10 %. Proposed experiments: (1) lower input CM to
  move PMOS-side headroom to the NMOS input/cascode, (2) capacitor-boosted NMOS tail unit, (3) cross-coupled gain pair.
- Round 3b robust optimizer (13 knobs incl. Lin, Wcp, Won, Wop, Wctl, stage-1 current scale tsc; CM-excursion gate
  as a constraint; ko +-4 %): 134/250 feasible, best #148 0.2277 mW (evaluate: ALL PASS, SNR 66.08, Abeta 67.32,
  Ts 24.36 ns, min margin 33 mV). Pattern: tsc 0.94, ko 0.59, Wctl 2.05u, Lin 0.85u, Wop 15u, C1d -> 0.
- Experiment 1 (input CM): on #148, VCMI 0.9 -> 0.85 with kcp 0.65: Abeta25 68.1 -> 72.3 dB, Ts 24.0 -> 22.4 ns,
  same power and SNR (FAQ: common mode is free; in a real MDAC the summing-node CM is set during sampling).
  VCMI 0.8 needs Wtn 6u (Wtn 4u collapses: NMOS tail in triode). Round 4 launched to convert the margin to power
  (15 knobs incl. VCMI, Wtn, kcp; C1d removed).

- Experiment 2 (capacitor-boosted NMOS tail unit Mtb: gate AC-coupled to ntn by Ctb, DC via Rtb 3Meg to vbn, fixed
  tail current unchanged): Ctb 0/0.1/0.2/0.4p all give Abeta25 71.7 dB, Ts 22.6 ns, power +0.4 to +0.9 uW. No effect,
  killed (design/work/cr4e2 kept as record).

- Record restore: candidate evaluations (cand148/cand248 on scratch benches) overwrote results/latest.json; re-ran
  evaluate --publish and robust on the unchanged final .asc (v13) while round 4 runs. gen_asc.py now supports the
  stage-1 current scale (W={Wt*tsc}) and an optional C1d; output for v13 byte-identical.

- Round 4 robust optimizer (15 knobs incl. VCMI, Wtn, kcp, C1d removed; CM-excursion gate; ko +-4 %): best #281,
  rounded and ko re-centred at 0.55 so ko +-7 % passes. Promoted as v14 (Ib 9.0u, tsc 0.81, ko 0.55, VCMI 0.86,
  Cin 1.67p, Cc 0.418p, Cls 0.76p, fcc 0.70). Drawn .asc regenerated (verify_circuit equivalent, 62 components,
  0 findings; lint clean). evaluate --tag final --publish on the .asc: ALL PASS, P 0.2160 mW (I(Vdd) 0.1200 mA),
  SNR 66.09, Abeta 69.51, A 84.28, Ts 23.33 ns, tau 1.740 ns, FoM 182.36 dB; robust PASS (worst Abeta 69.48).
  Min saturation margin 22 -> 48 mV, CM excursion 49.8 -> 22.0 mV. Power -9 % vs v13. Report: C1d removed from the
  D2/D3 drawing and text, input CM sentence added on page 8.
- v14 output CM check: report_extra gives xVcm 0.941 V (v13: 0.903 V). The optimizer never constrained the static
  output CM, and a high CM buys Abeta (knr 0.75 leaves the CMFB pair 41 mV off balance). Sweep knr on
  design/work/cmfix: 0.60/0.64/0.68/0.75 -> Vcm 0.886/0.901/0.915/0.941 V, Abeta25 68.9/68.9/69.0/69.5, power
  unchanged. knr 0.64 (v14b): evaluate ALL PASS, P 0.2160 mW, SNR 66.09, Abeta 68.93, Ts 23.60 ns, tau 1.749 ns;
  robust PASS; ko 0.5115 / 0.5885 both ALL PASS (Ts 20.95 / 24.61 ns). ko sweep down: Abeta floor 74 dB at
  ko 0.44 to 0.49 (power 0.2131 to 0.2144 mW), collapse below 0.40. Round 5 launched (static |Vcm - 0.9| <= 10 mV
  as a constraint, knr free, ko +-7 %, ranges widened where v14 sat on an edge; design/work/cmfix/space_r5.json).
- Record restore (again): the v14b candidate runs overwrote results/latest.json; re-published the unchanged v14
  .asc (tag final: ALL PASS, 0.2160 mW, Ts 23.33 ns), robust PASS, report rebuilt. design/final is still v14
  (knr 0.75, Vcm 0.941 V) until round 5 picks the CM-centred replacement.
- Round 5 (results/ropt/cr_r5, 320 trials, 16 knobs incl. knr; static CM gate; ko +-7 %): 8 robust-feasible,
  SNR binds (41 trials fail on SNR alone at 0.206 to 0.210 mW). Best #275 0.2140 mW (SNR 66.08, worst Abeta 66.9).
  Rounded as v15 (design/work/r5): Lin 1.07u, Wtn 7.5u, Wcp 11.7u, Wcn 8u, Won 1.22u, Wop 12.75u, Wctl 1.85u,
  Cc 0.413p, Cls 0.53p, fcc 0.72, tsc 0.82, ko 0.52, kcp 0.52, Cin 1.665p; knr 0.63 gave Vcm 0.8954 V, trimmed
  to 0.64 -> 0.8989 V. Netlist: ALL PASS 0.2142 mW, SNR 66.08, Abeta 69.31, Ts 23.20 ns, min margin 52 mV;
  robust PASS; ko 0.4836 / 0.5564 ALL PASS (Ts 18.44 / 24.55 ns); loop T0 79.8 dB, fc 43.5 MHz, PM 76.9 deg,
  GM 19.3 dB. Promoted to design/work (v14 in archive_v14), .asc regenerated, verify_circuit equivalent
  (62 components, 0 findings), lint clean. evaluate --tag final --publish on the .asc: ALL PASS, 0.2142 mW
  (I(Vdd) 0.1190 mA), FoM 182.73 dB; robust PASS. report_extra: CM loop 15.5 MHz / 77 deg, CM excursion 21.8 mV,
  output CM 0.899 V, CMFB pair 1.56 / 1.53 uA. Report rebuilt (8 pages). Power -9.8 % vs v13 (0.2375 mW).
  Diminishing returns: round 5 gained 0.9 % over the CM-centred v14b; SNR (66.08 vs 66.05) binds everywhere.
- report-reviewer on v15 (estimate 8.5 to 9.5, no correctness blockers). Fixed: SNR formula written out on p2;
  beta stated as 1/beta_act 5.24 > 5 (TA wording); stale hand-typed L = 1 um replaced by macro \pLin (1.07);
  input CM text now says sources at 0.86 V, summing nodes at \opV{vin}; input-CM physics corrected (NMOS pair gains
  Vds, PMOS pair gives some up; margins 52 / 90 mV from lt.py op); paper noise and settling budget added on p8;
  FoM with the tail tau and the +7.53 dB headline vs the EE4520 report added on p7; fc hand estimate marked;
  Cc, fcc, Cls, Rb values in the D2 caption; gp and ntn labels moved off wires; CM-loop margin number dropped
  (Middlebrook voltage break at the Mc3 diode node is not a low-impedance point) in favour of the transient CM
  numbers. Format-only tool changes: tools/evaluate.py publish fmt item 16 (Cfb) 4g -> 5g so 0.41625 shows
  Cin/Cfb = 4 exactly; tools/report_extra.py pKn 3 digits, new pLin/pLip macros. No threshold touched.
- Helper benches design/work/amp_cmloop.inc and bench_cmloop.cir were stale (Ib 9.6u, VCMI 0.9); re-synced to
  v15 from the report_extra copies (runs rc=0).
- spec-auditor on v15: PASS (reproduced every number on the .asc, 0 unsaturated with the step applied at DC,
  CMFB tracks vcmr 0.80 to 1.00 V within 1 mV, FAQ allows a free input CM, no threshold changes). Its note: the
  Abeta slack (69.3 dB) is what pays for the self-imposed ko +-7 % guard; dropping the guard is worth at most
  2.7 % (ko 0.48, Ib 8.6u: 0.2084 mW, fails at ko -7 %). Decision: keep the guard, stop the power descent here
  (round 5 gained 0.9 %, guard-free headroom 2.7 %). Final re-published after the audit runs (tag final
  01:08:24, ALL PASS, 0.2142 mW), robust PASS, report rebuilt, report/5714699.pdf re-copied (identical).
- DECISION REVERSED (user review 2026-10-06: "if the goal is 66 and we get 69"): the ko +-7 % guard is extra margin
  beyond evaluate.py's (Abeta +0.3 dB, Ts 24.8 ns) and brief/spec.md says not to add more: over-design costs power.
  Round 6 (results/ropt/cr_r6, design/work/r6/space_r6.json, 360 trials, seed v15): no ko perturbation (PF empty),
  keeps all evaluate.py constraints, the CM-excursion gate (< 50 mV) and the static CM gate (|Vcm - 0.9| <= 10 mV);
  ranges widened downward for tsc, ko, Won, Wop, Wctl. Final candidate must still pass robust.py.
- Round 6 stopped at about 240 trials: 14 feasible, best 0.2093 mW (#118/#238; Abeta 71.1, SNR 66.13: slack left).
  Cheaper trials fail on SNR (71), settling/ringing (about 58) and the static CM gate (55): the CM window is only
  +-0.03 wide in knr, so TPE wastes trials on it. Round 7 (scratch ropt7.py, results/ropt/cr_r7,
  design/work/r6/space_r7.json, 400 trials): knr removed from the search and auto-centred per trial (Newton step
  on the measured output CM, slope 0.365 V/unit, |Vcm - 0.9| <= 4 mV), seeded with the 4 best round-6 points and v15.
- Round 7 result: 400 trials, 123 feasible (auto-CM works), converged 0.2030 to 0.2036 mW. All top points have
  SNR 66.06 to 66.11 while Abeta spans 66.6 to 70.5 dB at equal power: SNR (Cin) now sets the power, not settling.
  Won (0.93u) and Wop (10.1u) sit on their lower bounds. #374 materialised as design/work/x374: evaluate ALL PASS,
  0.2032 mW, SNR 66.06, Abeta 69.43, Ts 23.22 ns, Iq 51.8 uA, window 112.9 uA, min margin 40 mV.
- Output swing (fixed at 1.4 V since P1) on x374 with Cin and Cc scaled by (1.4/V)^2: 1.35 V fails (floor 60.5 dB);
  1.45/1.5/1.55/1.6 V: 0.1996/0.1962/0.1928/0.1891 mW, Abeta floors 74 to 76 dB, A floors about 90 dB, SNR held,
  but the error crosses zero at 17.5/16.1/15.2/14.7 ns (counts as a ringing peak before 25 ns, FAIL). Round 8
  (results/ropt/cr_r8, design/work/r8/space_r8.json, 450 trials): VoutStep 1.40 to 1.62 as a knob, Cin 1.2 to 1.9p,
  Cc 0.26 to 0.45p, output-device bounds widened, auto-CM kept, seeded with x374 and the four swing points.
- The swing crossing is real underdamping: at 1.6 V the output error goes +17 mV (14 ns) -> -17 mV (16 ns) -> +0.24 mV
  (25 ns); scaling Cc with Cin raised fc without moving p2. Record restore: experiment runs overwrote
  results/latest.json; re-published the unchanged v15 .asc (tag final, ALL PASS 0.2142 mW), robust PASS, report rebuilt.
- ARCHITECTURE SURVEY (user request: do not stay confined to the chosen topology): reference/papers/ARCH-SURVEY-2026-10.md,
  six more IEEE papers downloaded (Hershberg 2012 ringamp, Lim and Flynn 2015 FD ringamp, Llimos Muntal 2018 CT ringamp,
  Tang 2020 FIA, Ramirez-Angulo 2006 QFG class-AB, Thandri 2003 NCFF). Verdicts under our rules: keep current-reuse
  telescopic input, current-buffer compensation, QFG class-AB output; reject ringamps (24 to 60 mV post-slew overshoot
  vs 0.34 mV error band breaks the ringing rule; .noise at a dead-zone op point is an artifact), FIA (needs precharge
  switches), Miller+Rz (+21 to +48 %), NCFF (> +100 %), nested/three-stage, class-A, single-stage gain-boosted;
  CLS/split-ADC/incomplete settling/chopping excluded by the rules. Ranked in-architecture levers: (1) larger output
  step with Cin, Cc scaled (round 8 running), (2) less output quiescent with stronger cascodes, (3) SC CMFB (-1.5 %).
- Round 8 stopped at about 365 trials: 179 feasible but none below the 1.4 V seed (0.2032 mW); TPE retreated to
  V < 1.45 because every V >= 1.5 trial rang. Manual damping probe at 1.5 V (xsw1.5): Cc 0.34p rings (16 ns),
  0.37p ALL PASS 0.1963 mW (SNR 66.25, Abeta 68.57, Ts 23.73 ns, tau 1.410 ns), 0.40p too slow (Abeta 56.8),
  0.43p 49.5: a narrow Cc window. 1.55 V: Cc 0.3626p no peak, Abeta 68.28, 0.1930 mW, SNR 66.34. 1.6 V still rings
  at Cc 0.34p. Round 9 (results/ropt/cr_r9, design/work/r8/space_r9.json, 450 trials): V 1.48 to 1.64,
  Cc 0.33 to 0.40p, Cin 1.25 to 1.62p, other knobs narrowed around x374, seeded with the passing 1.5/1.55 V points.
- Record restore (scratch evaluations overwrote latest.json): re-published v15 .asc (tag final), robust PASS, rebuilt.
  Scratch evaluations now go through a wrapper that restores results/latest.json with its mtime.
- Round 9 stopped at about 185 trials: 54 feasible, best #129 0.1868 mW at Vstep 1.623 V, Cin 1.265p, Cc 0.3765p
  (full evaluate on the netlist: ALL PASS, SNR 66.51, Abeta 71.23, A 86.51, Ts 21.69 ns, tau 1.892 ns, Iq 54.2 uA,
  window 103.8 uA, min margin 27 mV). Pinned at bounds: Cin, Lin, Wcp, VCMI low; Cls, Wcn, Wtn high. Round 10
  (scratch ropt10.py = ropt7 + min saturation margin >= 25 mV at the op point as a constraint; results/ropt/cr_r10,
  design/work/r10/space_r10.json): V 1.56 to 1.72, Cin 0.95 to 1.40p, the pinned bounds widened, seeded with the
  top 5 of round 9.
- Round 10: 450 trials, 153 feasible, converged 0.1818 to 0.1824 mW (no bound pinned). #350 rounded as
  design/work/v16 (Vstep 1.62 V, Cin 1.21p, Cc 0.36p after a damping trim: 0.356p gives a tiny target crossing at
  21.4 ns, 0.364p is at the settling edge, 0.368p fails). Netlist: ALL PASS 0.1818 mW, SNR 66.30, Abeta 69.77,
  A 84.97, Ts 21.65 ns, tau 1.806 ns, FoM 183.16 dB, min margin 37 mV (quiescent), robust PASS.
  REJECTED: with the step applied (DC op, both polarities) the low-side output NMOS is in triode (Vds 91 mV,
  margin -118 mV), and also in the reconstructed t = 25 ns state (Cls held by sources: margin -80 mV); the
  high-side output PMOS keeps only 18 to 22 mV. Breaks the project gate (every FET saturated, both step
  polarities) and the report claim. Round 11 (scratch ropt11.py: + min margin >= 15 mV in the step-applied DC
  op; results/ropt/cr_r11, design/work/r11/space_r11.json, 500 trials): V 1.40 to 1.62, Won up to 2.4u,
  Wop up to 18u, seeded with v15, x374, v16 and a 1.5 V midpoint.
- Round 11 stopped at about 200 trials: TPE stayed at 1.40 to 1.45 V (best = x374 seed, 0.2032 mW, step margin 40 mV);
  only 29 trials above 1.45 V. Round 12 (V forced to 1.45 to 1.60, Won 1.2 to 3.0u, seeded with v16 variants with a wide
  output NMOS): best #68 0.1888 mW at 1.488 V (Won 1.72u, Cin 1.395p, Cc 0.391p), ALL PASS, step-applied DC margins
  mcn 18.6 mV, mon 32 mV both polarities. Next cluster 0.1950 to 0.1966 mW at 1.47 V. #68 rounded = design/work/v17:
  ALL PASS 0.1888 mW, Abeta 66.94, Ts 24.23 ns, but a knife edge: Cc +1 % fails (64.5 dB), ko -3 % rings, ko +3 %
  too slow; swing +-0.5 % passes. Rule adopted: nominal + ko and Cc each at +-2 % must pass (much tighter than the
  dropped ko +-7 % guard). Round 13 (scratch ropt13.py, multi-knob PERT=ko,Cc, PF=0.98,1.02; results/ropt/cr_r13,
  space_r12, seeded with the round-12 top 10).
- Round 13 (+-2 %): 0 of 77 robust-feasible; e.g. r12 #323 (nominal Abeta 73.3) gets a tiny pre-25 ns target crossing at
  ko or Cc -2 % (Abeta 80 dB, but a zero crossing at 18 to 19 ns = ringing peak). High-swing optima sit next to critical
  damping. Numerical sensitivity of v17: method=gear vs trap Abeta 66.9425 vs 66.9425 dB, reltol 1e-3 66.9388 dB
  (the bench pins .option method=trap reltol=1e-4, carried into the .asc). Round 14: +-1 % on ko and Cc
  (results/ropt/cr_r14), about 100x the numerical spread.
- Round 14: 400 trials, 67 feasible; best #341 0.1915 mW (worst Abeta over +-1 % 67.83). Rounded = design/work/v18;
  rounding moved it to the underdamped edge (Cc -1 % crossed), Cc re-centred 0.387p -> 0.389p: nominal ALL PASS
  0.1918 mW, SNR 66.08, Abeta 69.35, Ts 22.29 ns; Cc and ko +-1 % all pass (Abeta 67.07 to 72.02, no crossing);
  step-applied DC op both polarities all saturated (worst mon 27.0 mV, mcn 28.6 mV); robust PASS; loop T0 81.0 dB,
  fc 39.8 MHz, PM 78.4 deg, GM 20.4 dB. Rfb*Cfb corner 1.11 kHz tripped a lint warning: Rin 100 -> 125Meg (Rfb 0.5 GOhm,
  corner 890 Hz; noiseless; Abeta 69.35 -> 69.34). PROMOTED as v18 (v15 archived in design/work/archive_v15):
  .asc regenerated (only .param lines differ), verify_circuit equivalent (62 components, 0 findings), lint 0/0,
  evaluate --tag final --publish on the .asc ALL PASS 0.1918 mW (I(Vdd) 0.1065 mA, FoM 183.12 dB), robust PASS.
  report_extra: CM excursion 33.2 mV (9.1 mV at 25 ns), output CM 0.899 V, tau tail 1.80 ns. Power -10.5 % vs v15,
  -19 % vs v13. Report: swing paragraph rewritten (swing as a sizing variable, limited by output-NMOS saturation
  with the step applied), +-1 % damping statement added, macro precision 3 digits (tools/report_extra.py, format only).
- spec-auditor on v18: design PASS (all claims reproduced; step-applied and reconstructed t = 25 ns states fully
  saturated, worst 27 / 33 mV; +-1 % corners pass; the Abeta slack pays for the window, spending it frees about 0.7 %
  and fails the corners). Report FAIL on two stale passages. report-reviewer (8.5 to 9.5): same two plus settling
  explanation errors. Diagnostics for the slow component (local e-fold 22.5 ns from 25 to 45 ns): 0.4 V step 14 ns
  (stays, so not large-signal), fcc 0.5 9.8 ns, fcc 0.9 rings, Cls x3 10.5 ns: a pole-zero doublet of the split
  current-buffer compensation and the AC-coupled output PMOS. Loop fc at the output extremes unchanged (39.1 to
  39.8 MHz), so the fast 40 to 48.69 dB stretch (tau 1.29 ns < two-pole 2.85 ns) is large-signal recovery: I(Vdd)
  falls through its quiescent value (54.9 -> 50.9 uA) in that stretch. Fixes: Rin/Rfb from \resRbig (p2); I(Vdd)
  printed with 5 decimals (tools/evaluate.py publish fmt item 9, format only); D6 tau term with the EE4520 definition
  on the same curve (xTauMid 1.29 ns: official tau costs 1.05 dB, circuit share 7.56 dB); p8 slew-rate budget
  (2 I_D/C_c), fast-stretch and doublet description, damping window wording, input-CM trade-off (PMOS pair now
  tightest, m1p 40 mV), beta note, NOIMOD 1/f clause, gm/ID both types, NEF ~6.1, n_tn label moved. New
  report_extra macros (generated): xTauMid, xTauSlow, xAbFortyFive, xTauTwoPole, xStepMarg, xStepDev. Report 8 pages.
- report-reviewer re-review (9 to 9.5): fixed the remaining items. Input-CM effect stated correctly (NMOS input pair and
  PMOS tail gain Vds, PMOS input pair and NMOS tail lose it; quiescent worst M1p 40 mV via \xQMarg/\xQDev); A-Abeta gap
  growth explained (Miller-multiplied Cgd, \xMillNa/\xMillNb; end gap \xGapEnd 16.0 dB); settling budget closes on its
  own terms (post-slew 4.2 e-folds in 10.0 ns; small-signal two-pole tau 2.75 ns exact (K from |T(j wc)| = 1) is slower,
  class-AB recovery closes it); slow part described as static floor plus a decaying doublet part (floor-subtracted
  e-fold about 7 ns, \xTauSlow now fitted on err - err_final); slew stated as a peak rate; D6 "about half"; output CM
  0.899 in the swing; page 8 tightened (parskip 2pt on page 8, shorter stage-1, damping, biasing sentences). Report 8
  pages, submission copy identical, no en/em dashes in the PDF text.

## Failed approaches (do not retry without a new reason)

- Optimising the global bias unit Ib with fixed cascode-bias diodes: shifts vcn/vcp, devices leave saturation.
- Capacitor-boosted NMOS tail unit (adaptive tail): no settling gain in this topology.
- Stronger CMFB (mirror ratio 8) to cut the 3 ns CM spike: no effect on the spike, slows DM settling.

- Attempt 1 (June 2026): single-stage gain-boosted folded cascode + current reuse + SC-CMFB: 2.04 mW and
  settling short (77.2/62.7 dB at 25 ns). Single-pole settling needs about 7.7 τ; infeasible by construction.
- Attempt 1: class-AB output grafted onto the gain-boosted single-stage core: oscillation, A0 collapse,
  input-CM conflicts (`legacy/attempt-1-2026-06/design/class-ab/class_ab_results.txt`).
- Loop bench with 1 TH / 1 TF break: LTspice lands the `.op` in a wrong state. Use the series-injection bench.
