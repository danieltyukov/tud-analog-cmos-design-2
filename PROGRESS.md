# PROGRESS (resit attempt, started 5 Oct 2026)

## Current state

Phase: P0 (setup done by the harness session; no design work yet).
Best passing design: none. Best power so far: n/a.
Next action: P1, read the brief files, then write the paper budget.

## Plan (tick a box only with tool evidence; add sub-steps as needed)

- [x] P0 Harness: tools verified on `example/` (selftest OK), benches validated, report skeleton builds (8 pages).
- [ ] P1 Budget on paper: $V_{step}$, $C_{in}$, $C_c$, $f_c$, $A_0$, currents per branch, noise split
      (`metrics.py budget`, `gmid.py`). Architecture A from `brief/design-strategy.md` unless the budget says otherwise.
      Gate: paper SNR ≥ 66.3 dB, settling budget closes in 24 ns, total current target written down.
- [ ] P2 Bias block (on `Vddb`, EE4520 style, decoupled) + stage 1 + stage 2 + compensation in
      `design/work/amp.inc`, temporarily with the simplest real CMFB that works.
      Gate: `.op` all saturated at mid and at both output extremes; loop fc and PM on target.
- [ ] P3 Real CMFB designed and checked (CM loop PM ≥ 60°, CM excursion during the step < 50 mV).
- [ ] P4 Full `evaluate.py` PASS on the netlist benches, then `robust.py` PASS.
- [ ] P5 Power descent (sweeps, `optimize.py`); re-check P4 gates at the final point. Log the power trajectory.
- [ ] P6 Draw `design/final/amp_tran.asc` and `amp_noise.asc` (`draw-asc` skill); `verify_circuit` equivalent
      to the netlist; `asc_lint` clean; `evaluate.py --publish` and `robust.py` PASS on the `.asc`.
- [ ] P7 Report: D2/D3 CircuiTikZ with `\Vtag`/`\Itag`, D6 and short explanation; 8 pages; `report-reviewer` clean.
- [ ] P8 `spec-auditor` sign-off; `check_done.py` DONE; hand the user the form values from `results/latest.json`.

## Session log (append one line per experiment: date, change, key numbers, verdict)

- 2026-10-05 harness: selftest reproduces example (A 80.81, Aβ 66.01, τ 2.697 ns, Vn 326.4 µV).
  Example amp in our bench (50 ps edge, 100 MΩ noiseless Rin/Rfb): Aβ 65.7 dB, i.e. its pass was bench-dependent.

## Failed approaches (do not retry without a new reason)

- Attempt 1 (June 2026): single-stage gain-boosted folded cascode + current reuse + SC-CMFB: 2.04 mW and
  settling short (77.2/62.7 dB at 25 ns). Single-pole settling needs about 7.7 τ; infeasible by construction.
- Attempt 1: class-AB output grafted onto the gain-boosted single-stage core: oscillation, A0 collapse,
  input-CM conflicts (`legacy/attempt-1-2026-06/design/class-ab/class_ab_results.txt`).
- Loop bench with 1 TH / 1 TF break: LTspice lands the `.op` in a wrong state. Use the series-injection bench.
