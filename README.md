# EE4525 2025-2026 resit: a residue amplifier for a pipeline ADC

Fully differential switched-capacitor residue amplifier (gain 4) in 0.18 µm CMOS (`log018.l`, 1.8 V),
designed and verified in LTspice. Specs: SNR ≥ 66 dB, Aβ ≥ 66 dB and A > 78 dB at 25 ns, FoM > 170 dB;
**the grade is set by the lowest power that meets them all** (< 3 mW to pass). Resit deadline
**Sun 8 Nov 2026, 23:59**.

| Attempt | Result |
|---|---|
| 1 (June 2026, `legacy-v1/attempt-1-2026-06/`) | 2.04 mW, settling missed at 25 ns, **3.5 (fail)** |
| reference (`example/`, a friend's design) | 1.24 mW, all specs met, 7.5 |
| 2 (Oct 2026, `legacy-v2/`, not submitted) | class-AB current-reuse design, 0.19 mW; dropped after the TA meeting of 12 Oct 2026: too complicated, FoM 183 dB implausible (course maximum about 176 to 177 dB), unusual settling curve, bias not a replica (`brief/ta-feedback-2026-10-12.md`) |
| **3 (this design)** | **0.5295 mW, all specs met, FoM 176.95 dB** (report and form values ready, not yet submitted) |

## Final result

Measured by `tools/evaluate.py` on the drawn schematics `design/final/amp_tran.asc` and `amp_noise.asc`
(LTspice XVII); all checks pass, including the TA plausibility check FoM ≤ 177 dB. `tools/robust.py` passes
(step polarity, 20/50/100 ps edges, reltol).

| Quantity | Value |
|---|---|
| Power (1.8 V × average I(Vdd) over the 25 ns after the step; Vdd feeds stage 1, stage 2 and the CMFB) | 0.5295 mW (0.2942 mA) |
| SNR (amplifier noise 10 kHz to 100 GHz plus 42 kT/Cin for both halves) | 66.19 dB |
| Aβ / A at 25 ns | 72.88 dB / 87.44 dB |
| Settling time, τ = T38.6dB − T30dB | 24.08 ns, 2.527 ns |
| FoM | 2.020e-18 J, 176.95 dB |
| Output step (differential), Cin = Cload, Cfb | 1.2 V, 2.15 pF, 0.5375 pF |

The complete 22-row table is page 2 of the report; the same values are in `results/latest.json`
(generated, not tracked) and in `report/generated/results.tex`.

## Design

The simple two-stage structure the TA recommended, no gain boosting:

- **Stage 1:** PMOS-input telescopic cascode (PMOS input pair, PMOS and NMOS cascodes, NMOS loads with L = 2 µm).
  PMOS input because in `log018.l` PMOS flicker noise falls as 1/f^1.25 and NMOS flicker only as 1/f^0.825.
- **Stage 2:** common source. The NMOS driver takes the stage-1 output directly; the PMOS current source gets the
  same signal through a 0.68 pF capacitor while its DC gate voltage comes from the replica bias line through
  2 MΩ, so both devices amplify and the rising output is not limited to the quiescent current. A pure class-A
  version needed more than 1 mW (kept in `design/work/classA/`).
- **Compensation:** Miller Cc with a nulling resistor Rz that moves the zero onto the second pole.
- **CMFB:** continuous time. 2 MΩ ∥ 50 fF output-CM sense, PMOS pair against vcmr, diode mirror into one of the
  nine NMOS load units per side.
- **Bias:** replica of one stage-1 half on Vddb (excluded from power). A tail unit plus an input unit set vbp, a
  cascode unit plus a load unit set vbn; every amplifier transistor is an integer number of these units, so the
  amplifier copies the replica's current density (the replica nodes match the amplifier nodes within about 1 mV).
  vcn and vcp come from wide-swing diodes of the cascode type and length fed by fixed multiples of the same
  current (EE4520 fig. 6). Every line is
  decoupled with 1 kΩ and 10 nF.

The settling is linear: a 1 % output step gives about the same τ (2.60 ns) as the full step (2.53 ns), the first zero crossing
of the error is at 26.5 ns, and the loop has fc 33.75 MHz with 79.9° phase margin. The bias (Ibnp 6.2 µA) is the
lowest at which the design still settles 0.3 ns before 25 ns with any one of Cc, Rz, Cls or Ibnp 1 % off. The design history (budget,
experiments, optimiser runs, dead ends) is in `PROGRESS.md`.

## Rerunning the simulations

**Plain LTspice (as a TA would):** open `design/final/amp_tran.asc` (transient) or `design/final/amp_noise.asc`
(noise) with `design/final/log018.l` in the same folder. The schematics load the model with a relative path
(`.lib 'log018.l' TT`). That copy is the lecturer's file with its internal self-includes made relative; every
model parameter is unchanged (`models/log018.l` is the pristine original). The `.meas` lines print `A25`, `Ab25`,
`P_mW`, `T30_step`, `T38p6_step` and `tau` (transient) and `Vn_amp`, `Vn_kTC`, `Vn_tot`, `SNR_dB` (noise) in the log
(View => SPICE Error Log). To see the D4 curves in the waveform viewer, add the traces
`20*log10(1.2/(abs(V(vip,vin))+1n))` (A) and `20*log10(1.2/(abs(1.2-V(von,vop))+1n))` (Aβ); the step is at 10 ns.

**With the tools (this machine, LTspice XVII under Wine):**

```bash
uv run tools/selftest.py                      # toolchain regression on the passing example
uv run tools/evaluate.py --tran design/final/amp_tran.asc --noise design/final/amp_noise.asc --tag final --publish
uv run tools/robust.py design/final/amp_tran.asc
uv run tools/ltgui.py all                     # D4/D5: runs the .asc in the LTspice GUI, screenshots its plots
uv run tools/report_extra.py && uv run tools/report.py build
uv run tools/crosscheck.py all                # KCL at every node, branch sums, every report formula
uv run tools/check_done.py                    # definition of done
```

The drawn schematics are generated from the netlist by `design/work/gen_asc.py` and proven equivalent to
`design/final/reference_tran.cir` with the `ltspice-asc` MCP `verify_circuit`.

## Report and submission

`report/5714699.pdf` is the submission copy of `report/main.pdf`: 8 pages in the compulsory order (title, D1 table,
D2 node voltages, D3 branch currents, D4 settling, D5 noise, D6 FoM comparison with EE4520, short explanation).
Every number in it is generated from simulation (`report/generated/*.tex`); the D4 and D5 figures are screenshots of
the LTspice XVII waveform viewer after running the deliverable schematics in the LTspice GUI. Submit through the form
(https://edu.nl/7turd, at most 2 submissions) with the 22 values from the D1 table.

## How this repo is set up

The resit was run by a Claude Code agent with a purpose-built harness (`KICKOFF.md`).

| Path | What |
|---|---|
| `CLAUDE.md` | agent instructions: mission, start ritual, tools, workflow, hard rules |
| `PROGRESS.md` | state, plan with gates, experiment log, failed approaches |
| `brief/` | assignment PDF, FAQ, TA clarifications and TA feedback, distilled `spec.md`, `lessons.md`, `design-strategy.md` |
| `tools/` | Python (uv) tooling around LTspice XVII: runner, metrics, judge, robustness, optimizer, gm/ID, lint, report macros |
| `design/final/` | drawn deliverable schematics, portable model copy, equivalence reference netlist |
| `design/work/` | netlist benches (`amp.inc` shared by tran, noise and loop benches), schematic generator, optimiser space, class-A variant |
| `report/` | 8-page LaTeX report, CircuiTikZ D2/D3 drawings, generated values and figures |
| `.claude/` | project settings (permissions, hooks), skills, subagents |
| `.mcp.json` | `ltspice-asc` MCP server for drawing and verifying `.asc` schematics |
| `reference/` | EE4520 artefacts (FoM baseline for Deliverable 6, bias block) and papers |
| `models/` | pristine `log018.l` (with 1/f noise, mandatory) |
| `legacy-v1/` | attempt 1 (June 2026), frozen |
| `legacy-v2/` | attempt 2 (class-AB resit design, October 2026), frozen: sources, report, evidence, experiment log |
