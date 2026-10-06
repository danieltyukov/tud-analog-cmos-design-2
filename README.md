# EE4525 2025-2026 resit: a residue amplifier for a pipeline ADC

Fully differential switched-capacitor residue amplifier (gain 4) in 0.18 µm CMOS (`log018.l`, 1.8 V),
designed and verified in LTspice. Specs: SNR ≥ 66 dB, Aβ ≥ 66 dB and A > 78 dB at 25 ns, FoM > 170 dB;
**the grade is set by the lowest power that meets them all** (< 3 mW to pass, best designs < 0.3 mW).
Resit deadline **Sun 8 Nov 2026, 23:59**.

| Attempt | Result |
|---|---|
| 1 (June 2026, `legacy/attempt-1-2026-06/`) | 2.04 mW, settling missed at 25 ns, **3.5 (fail)** |
| reference (`example/`, a friend's design) | 1.24 mW, all specs met, 7.5 |
| **resit (this repo)** | **0.1918 mW, all specs met** (report and form values ready, not yet submitted) |

## Final result

Measured by `tools/evaluate.py` on the drawn schematics `design/final/amp_tran.asc` and `amp_noise.asc`
(LTspice XVII), all checks pass; `tools/robust.py` passes (step polarity, 20/50/100 ps edges, reltol).

| Quantity | Value |
|---|---|
| Power (1.8 V × I(Vdd), max of quiescent and 25 ns window average) | 0.1918 mW (0.10654 mA) |
| SNR (amplifier noise 10 kHz to 100 GHz plus 42 kT/Cin) | 66.08 dB |
| Aβ / A at 25 ns | 69.34 dB / 84.27 dB |
| Settling time, τ = T38.6dB − T30dB | 22.29 ns, 1.641 ns |
| FoM | 4.878e-19 J, 183.12 dB |
| Output step (differential), Cin = Cload, Cfb | 1.478 V, 1.43 pF, 0.3575 pF |
| Common mode: input, output | 0.811 V, 0.899 V |

The complete 22-row table is page 2 of the report; the same values are in `results/latest.json`
(generated, not tracked) and in `report/generated/results.tex`.

## Design

Two-stage amplifier, no gain boosting:

- **Stage 1:** stacked complementary input pair (PMOS pair on a top tail, NMOS pair on a bottom tail,
  both gates on the summing node) with PMOS and NMOS cascodes. One current produces both transconductances,
  which halves the stage-1 current for the needed gm and removes load-device noise.
- **Compensation:** current buffers. Cc is split between the NMOS-cascode and PMOS-cascode sources, so there
  is no right-half-plane zero and no nulling resistor.
- **Stage 2:** class-AB push-pull. The NMOS is driven directly, the PMOS through a level-shift capacitor whose
  DC is set by a 3 MΩ resistor from a bias line, so the slewing current is not limited by quiescent current.
- **CMFB:** continuous time. 2 MΩ ∥ 50 fF output-CM sense, PMOS pair against vcmr, diode mirror into part of the
  NMOS tail.
- **Bias:** separate block on Vddb (excluded from power), reference currents as fixed multiples of one unit,
  every line decoupled with 10 nF.
- **Input common mode 0.811 V** (the FAQ leaves it free): below the output CM, which moves spare headroom from the
  PMOS input pair to the NMOS input pair.
- **Output step 1.478 V:** at a fixed SNR, Cin scales as 1/V², so the load charge falls as 1/V. The step is the
  largest at which every transistor stays saturated with the step applied, in both polarities.

The design history (budget, experiments, dead ends, power trajectory 0.43 to 0.1918 mW) is in `PROGRESS.md`.
A literature pass over IEEE Xplore (class-AB residue amplifiers, slew-rate enhancement, current-buffer
compensation, settling-driven design) is summarised in `reference/papers/NOTES-resit-2026-10.md`; it led to the
lower input common mode and the later optimisation rounds (0.2375 to 0.1918 mW). An architecture-level survey
(ring amplifiers, floating-inverter amplifiers, compensation and output-stage alternatives against the assignment
rules) is in `reference/papers/ARCH-SURVEY-2026-10.md`.

## Rerunning the simulations

**Plain LTspice (as a TA would):** open `design/final/amp_tran.asc` (transient) or `design/final/amp_noise.asc`
(noise) with `design/final/log018.l` in the same folder. The schematics load the model with a relative path
(`.lib 'log018.l' TT`). That copy is the lecturer's file with its internal self-includes made relative; every
model parameter is unchanged (`models/log018.l` is the pristine original). Both sheets were run unmodified in a
fresh folder and reproduce the numbers above. The `.meas` lines print `A25`, `Ab25` and `P_mW` (transient) and
`Vn_amp` (noise) in the log. To see the D4 curve in the waveform viewer, plot
`20*log10(1.4/(abs(1.4-V(von,vop))+1n))`.

**With the tools (this machine, LTspice XVII under Wine):**

```bash
uv run tools/selftest.py                      # toolchain regression on the passing example
uv run tools/evaluate.py --tran design/final/amp_tran.asc --noise design/final/amp_noise.asc --tag final --publish
uv run tools/robust.py design/final/amp_tran.asc
uv run tools/report_extra.py && uv run tools/report.py build
uv run tools/check_done.py                    # definition of done
```

The drawn schematics are generated from the netlist by `design/work/gen_asc.py` and proven equivalent to
`design/final/reference_tran.cir` with the `ltspice-asc` MCP `verify_circuit`.

## Report and submission

`report/5714699.pdf` is the submission copy of `report/main.pdf`: 8 pages in the compulsory order (title, D1 table,
D2 node voltages, D3 branch currents, D4 settling, D5 noise, D6 FoM comparison with EE4520, short explanation).
Every number in it is generated from simulation (`report/generated/*.tex`). Submit through the form
(https://edu.nl/7turd, at most 2 submissions) with the 22 values from the D1 table.

## How this repo is set up

The resit was run by a Claude Code agent with a purpose-built harness (`KICKOFF.md`).

| Path | What |
|---|---|
| `CLAUDE.md` | agent instructions: mission, start ritual, tools, workflow, hard rules |
| `PROGRESS.md` | state, plan with gates, experiment log, failed approaches |
| `brief/` | assignment PDF, FAQ, TA clarifications, distilled `spec.md`, `lessons.md`, `design-strategy.md` |
| `tools/` | Python (uv) tooling around LTspice XVII: runner, metrics, judge, robustness, optimizer, gm/ID, lint, report macros |
| `design/final/` | drawn deliverable schematics, portable model copy, equivalence reference netlist |
| `design/work/` | netlist benches (`amp.inc` shared by tran, noise and loop benches), schematic generator, archived earlier versions (`archive_*`) and optimiser rounds |
| `report/` | 8-page LaTeX report, CircuiTikZ D2/D3 drawings, generated values and figures |
| `.claude/` | project settings (permissions, hooks), skills, subagents |
| `.mcp.json` | `ltspice-asc` MCP server for drawing and verifying `.asc` schematics |
| `reference/` | EE4520 artefacts (FoM baseline for Deliverable 6, bias block) and papers |
| `models/` | pristine `log018.l` (with 1/f noise, mandatory) |
| `legacy/` | attempt 1, frozen |
