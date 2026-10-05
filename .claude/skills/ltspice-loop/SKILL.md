---
name: ltspice-loop
description: Runs and measures EE4525 LTspice simulations (op, loop gain, transient, noise, sweeps, optimizer, robustness) with the repo tools and interprets the numbers. Use for any simulation, sizing iteration, "does it pass", power reduction, or when a number needs to be measured.
---

# LTspice simulate-measure-iterate loop

**Rules first**
- Only `tools/evaluate.py` output decides PASS/FAIL. `.meas` lines are quick looks.
- Never print waveforms, whole logs, or `Read` a `.raw`. Use the tools' summaries and plots.
- Change one knob at a time; log change + numbers + verdict in `PROGRESS.md`.
- Every bench in `design/work/` includes the same `amp.inc` so tran, noise and loop see one amplifier.
- Do not use `db()`/`ph()` of complex expressions in `.meas` (XVII applies dB twice). Use `tools/metrics.py loop`.

## Setup a working copy

```bash
mkdir -p design/work && cp design/templates/*.cir design/templates/amp.inc design/work/
```
Set `Cin`, `VoutStep` identically in `bench_tran.cir`, `bench_noise.cir`, `bench_loop.cir` (or move
shared params into `amp.inc` and delete them from the benches). Node contract: `vip vin` inputs,
`vop von` outputs, `vdd` amp supply (source `Vdd` = graded power), `vddb` bias supply, `vcmr` 0.9 V.

## The gates, in order

1. **Operating point:** `uv run tools/lt.py op design/work/bench_tran.cir`. Every FET saturated
   (margin column), output CM 0.9 V, currents as budgeted. Repeat with the step applied
   (`.param` override of `VCMI`, or a DC copy with the inputs at their final values) to see the
   output extremes: margins ≥ 50 to 100 mV there too, or A0 collapses at the final value.
2. **Loop gain:** `uv run tools/lt.py run design/work/bench_loop.cir` then
   `uv run tools/metrics.py loop design/work/bench_loop.raw --plot results/loop.pdf`.
   Targets (two-stage, `brief/design-strategy.md`): fc about 40 MHz, PM 72 to 78°, T0 ≥ 66+15+3 dB.
3. **Full evaluation:** `uv run tools/evaluate.py --tran design/work/bench_tran.cir --noise design/work/bench_noise.cir --tag vNN`.
   Read the FAIL lines and the hints. Plots land in `results/vNN/` (look at `d4_settling.png`).
4. **Robustness:** `uv run tools/robust.py design/work/bench_tran.cir` must PASS before power descent ends.

## Moving numbers

| Symptom | Usual lever |
|---|---|
| Aβ floor (static) short | raise $A_0$ at the output extremes: longer L in stage 1, output devices out of triode, less swing |
| Aβ(25 ns) short, floor fine | more fc (gm1/Cc) or less slewing (tail current, class-AB drive); check PM is not too high |
| first ringing peak before 25 ns | PM too low: move $p_2$ up (gm2), more Cc, or nulling/cascode-compensation tuning |
| SNR short | bigger Cc (two-stage noise ≈ αkT/Cc), bigger Cin, more swing, longer L on 1/f-dominant devices |
| SNR far above 66.3 | shrink Cin / Cc or cut input current: you are paying power for nothing |
| power high, all specs with margin | sweep currents down 3 to 5 % per step |

## Sweeps and optimizer

```bash
uv run tools/lt.py sweep design/work/bench_tran.cir --set Ib1=60u,70u,80u --set Cc=0.8p,0.9p,1p -j 16 --tag cc_ib
uv run tools/optimize.py --tran design/work/bench_tran.cir --noise design/work/bench_noise.cir \
    --space design/work/space.json --study s1 --trials 150 -j 8
```
Sweep CSVs go to `results/sweeps/`. The optimizer tunes `.param` knobs (`"int"` for multipliers),
minimises power under every spec constraint, resumes from `results/opt/<study>.db`, and writes
`results/opt/<study>_best.json`. Use it only when the topology already passes; it tunes, it does not design.

## Gotchas (verified)

- LTspice XVII via Wine needs a display: `tools/lt.py` manages one shared Xvfb (`:87`).
- `.lib` path must be single-quoted for XVII; `lt.py` fixes LTspice-24 paths and `.options logopinfo`.
- `.op` with `.tran` prints no device table: use `lt.py op` (it swaps in `.op`).
- ngspice disagrees with LTspice on this model (XL/XW): size with `tools/gmid.py`, verify in LTspice.
- The bench uses 50 ps edges and 100 MΩ noiseless Rin/Rfb on purpose; the example design only passed
  with its own bench details. Margins are not optional.
- Loop bench: series voltage injection; the 1 TH / 1 TF break mis-solves the `.op` in LTspice.
