# EE4525 resit: residue amplifier at minimum power (agent instructions)

**Mission.** Design from scratch a fully differential switched-capacitor residue amplifier
(0.18 µm CMOS, `log018.l`, 1.8 V, LTspice) that meets every spec in `brief/spec.md` at the
**lowest possible power**, then write the 8-page report. Deadline **Sun 8 Nov 2026 23:59**.
**Power is the grade.** Attempt 1 failed (3.5: missed settling at 2.04 mW). A friend passed with
7.5 at 1.24 mW. Target: every check PASS at **≤ 0.6 mW**, stretch ≤ 0.45 mW (`brief/design-strategy.md`).

## Start of every session (in this order)

1. Read `PROGRESS.md` (current state, plan, last log entries, failed approaches).
2. `uv run tools/selftest.py` (10 s). If it fails, fix the toolchain before anything else.
3. Do the next unchecked step of the plan in `PROGRESS.md`.

First session only, also read: `brief/spec.md`, `brief/lessons.md`, `brief/design-strategy.md`,
`example/README.md`. Do not browse `legacy/` unless a lesson points there. Never `Read` `.raw` files.

## Tools (run from the repo root; outputs are compact by design)

| Command | Purpose |
|---|---|
| `uv run tools/selftest.py` | toolchain regression vs the passing example |
| `uv run tools/lt.py run F [--op]` / `op F` | run LTspice XVII headless; `.meas` table; device op table (Id, Vds, Vdsat, margin, gm/ID, Cgg) |
| `uv run tools/lt.py sweep F --set K=a,b --set J=c,d -j 16` | parallel `.param` sweep (8 runs in about 6 s) |
| `uv run tools/gmid.py table nch --L 0.36u` / `size pch --L 0.25u --gmid 16 --id 70u` | gm/ID sizing from LTspice tables (`build` regenerates) |
| `uv run tools/metrics.py budget --vout 1.2 --cin 1.8p` | kT/C, allowed amplifier noise for SNR 66 dB |
| `uv run tools/metrics.py loop RAW --plot X.pdf` | loop gain T0, fc, PM, GM from `bench_loop.cir` |
| `uv run tools/evaluate.py --tran T --noise N --tag vNN` | **the judge**: 22-row table, PASS/FAIL, hints, history |
| `uv run tools/robust.py T` | settling under edge rate / polarity / reltol variants |
| `uv run tools/optimize.py --tran T --noise N --space S.json --study s1` | Optuna power minimisation with spec constraints |
| `uv run tools/asc_lint.py F.asc` | rules + schematic hygiene |
| `uv run tools/opvals.py F` | node voltages / branch currents as LaTeX macros for D2/D3 |
| `uv run tools/check_done.py` | definition of done for the whole task |

MCP: `ltspice-asc` (project) `edit_schematic` + `verify_circuit` (equivalence vs a netlist, overlaps,
wires through bodies, label-only nets, renders); `ltspice` (user) `render_schematic`, `plot_simulation`;
`matlab` for extra math. Skills: `ltspice-loop`, `draw-asc`, `report-latex`, `sizing`.
Agents: `spec-auditor` (before claiming any milestone), `report-reviewer` (before declaring the report done).

## Workflow

1. **Budget on paper** (swing, Cin, Cc, fc, A0, currents) with `metrics.py budget` + `gmid.py`; log it.
2. **Netlist first.** Work in `design/work/` from `design/templates/` (`bench_tran.cir`,
   `bench_noise.cir`, `bench_loop.cir` include one `amp.inc`). Iterate with `lt.py`, sweeps, loop bench.
3. **Gates in order:** `.op` (every FET saturated, CM on target, both step polarities) → loop
   (fc, PM, A0β) → `evaluate.py` (all PASS) → `robust.py`.
4. **Power descent** with sweeps / `optimize.py` until the first margin hits its floor.
5. **Draw the final `.asc`** in `design/final/` with `ltspice-asc` (`draw-asc` skill), prove it
   equivalent to the netlist with `verify_circuit`, then `evaluate.py --publish` and `robust.py` **on the `.asc`**.
6. **Report** (`report-latex` skill), then `report-reviewer` and `spec-auditor`, then `check_done.py`.

## Hard rules

- **Evidence only.** Every spec number you state comes from `tools/evaluate.py` (quote its line). Never
  claim PASS from `.meas` quick-looks, memory or estimates. Never type simulated numbers into the report.
- **Do not move the goalposts:** never edit `brief/spec.md` specs, `tools/selftest.py` golden values, or the
  thresholds/margins in `tools/evaluate.py`, `robust.py`, `check_done.py` to make a design pass.
- **One change at a time**, then measure. Log every experiment (change, numbers, verdict) in `PROGRESS.md`;
  record dead ends under "Failed approaches" so later sessions do not retry them.
- **Assignment rules** (`brief/spec.md` section 3): NMOS/PMOS/R/C only, real CMFB, single 1.8 V supply
  for all amplifier blocks, bias block on `Vddb`, integer `m`, NMOS bulk to ground, `log018.l` TT only.
- **Schematic hygiene (user rule, every `.asc`):** (1) every element is a drawn symbol, never a SPICE
  text line (no E/B probes typed as directives); (2) pins joined by drawn wires, net-label flags only for
  sheet-spanning nets (rails, vcmr, outputs, bias lines); (3) all directives inside one titled
  "Parameters, Simulations & Measurements" box; (4) titled block rectangles, no overlaps, nothing outside
  its box; (5) no stale symbols, labels, params or `.meas`; (6) re-verify after every change.
- **Report:** exactly 8 pages in the compulsory order (`brief/spec.md` section 5). No contents page, no appendices.
- **Git:** never commit or push unless the user asks.
- **Writing:** no emojis, no em/en dashes, plain direct prose. LaTeX math (`$...$`) in markdown here.
- **Context hygiene:** never print waveforms or whole logs; use the tools' summaries. Keep `PROGRESS.md`
  "Current state" short and current (it is re-injected after compaction).
- Blocked on a decision only the user can make: write `BLOCKED: <question>` in the PROGRESS.md
  "Current state" and stop. Do not submit anything; the user submits the form.

## Layout

`brief/` assignment, spec, clarifications, lessons, strategy (read-only sources) · `design/templates/`
benches · `design/work/` iteration · `design/final/` drawn deliverable `.asc` · `tools/` Python tooling
(uv project) · `results/` generated (gitignored) · `report/` LaTeX · `example/` passing reference ·
`reference/ee4520/` prior course (D6 baseline, bias block) · `models/` `log018.l` · `legacy/` attempt 1 (frozen).
