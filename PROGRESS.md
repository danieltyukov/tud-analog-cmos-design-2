# PROGRESS (resit attempt, started 5 Oct 2026)

## Current state

Phase: DONE (P8). Final design v13 (CR topology: stacked complementary input, current-buffer compensation,
class-AB output, CT CMFB; Ib 9.0u, ko 0.64, Vstep 1.4 V, Cin 1.66p). Drawn design/final/amp_{tran,noise}.asc
(gen_asc.py; verify_circuit equivalent, 0 findings; lint clean). evaluate --tag final --publish on the .asc:
ALL PASS, P 0.2375 mW (I(Vdd) 0.1320 mA), SNR 66.21, Aβ 66.76, A 81.59, Ts 24.48 ns, τ 1.792 ns, FoM 181.9 dB.
robust PASS on the .asc (worst Aβ 66.69, Ts 24.52 ns). Report 8 pages, reviewed twice; spec-auditor PASS.
Form values: results/latest.json (tag final).

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

## Failed approaches (do not retry without a new reason)

- Optimising the global bias unit Ib with fixed cascode-bias diodes: shifts vcn/vcp, devices leave saturation.
- Stronger CMFB (mirror ratio 8) to cut the 3 ns CM spike: no effect on the spike, slows DM settling.

- Attempt 1 (June 2026): single-stage gain-boosted folded cascode + current reuse + SC-CMFB: 2.04 mW and
  settling short (77.2/62.7 dB at 25 ns). Single-pole settling needs about 7.7 τ; infeasible by construction.
- Attempt 1: class-AB output grafted onto the gain-boosted single-stage core: oscillation, A0 collapse,
  input-CM conflicts (`legacy/attempt-1-2026-06/design/class-ab/class_ab_results.txt`).
- Loop bench with 1 TH / 1 TF break: LTspice lands the `.op` in a wrong state. Use the series-injection bench.
