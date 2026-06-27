# Report — deliverables, figures & how to extract each

The execution map for the final report: every EE4525 deliverable, what it
requires, the sim/calc that produces it, **how to generate the figure** (which
tool), and the method doc. Specs to match are in `../analysis/00_spec_table.md`;
sims are in `../analysis/09_simulation_runbook.md`; tools in
`../LTSPICE_TOOLCHAIN.md`.

> **EE4525 needs only 2 plots + 2 annotated schematics** (much leaner than
> EE4520's 8 plots): D4 settling, D5 noise, D2/D3 schematics. The AC Bode is
> internal-only here.

## Deliverable → figure/output → how to make it

| # | Deliverable (project PDF) | Output | Produced by (sim/calc) | **How to extract the figure** | Method doc |
|---|---|---|---|---|---|
| **1** | Table of results (22 rows) | the table | all sims A–E + hand calc | fill `00_spec_table.md`; copy into report + the submission form | `00`, `09` |
| **2** | Schematic + **all node voltages** | **clean** annotated schematic (PDF: *"not a simulator schematic"*) | DC op-point (sim A) | **CircuiTikZ** `circuits/<amp>.tex` → SVG, annotate node V from `read_op_point` | `09 §A`, CircuiTikZ |
| **3** | Schematic + **all branch currents** | clean annotated schematic | DC op-point (sim A) | CircuiTikZ schematic, annotate $I_d$ per branch from op-point | `09 §A` |
| **4** | **Settling accuracy vs time** | one plot: $A(t)$ **and** $A\beta(t)$, $A\beta$ **from 0 dB**, markers @ 25 ns / 78 dB / 66 dB | transient (sim D) | `plot_simulation` on the `.raw` (or MATLAB for polish) | `06`, `09 §D`, `07 §3` |
| **5** | **Output noise PSD vs freq** | PSD 10 kHz–100 GHz + **integrated** value shown | noise (sim E) | `plot_simulation` on the noise `.raw`; annotate integrated $V_{n}$ | `04`, `09 §E` |
| **6** | Design-process write-up (≤ 1 page) | text | — | content checklist below | `07 §5.8` |
| **7** | **FoM comparison vs EE4520** (step-by-step) | table + text | hand calc | EE4520 baseline **175.2 dB** (`../from-ee4520/README.md`); method `08` | `08`, `from-ee4520` |
| **8** | Submission | PDF `[StudentNumber].pdf` | — | form `https://edu.nl/3c9tf`, ≤ 2 submissions, click Submit | `07 §6` |

**Appendix (optional, EE4520-style):** the LTspice *simulator* schematics via
`render_schematic` (white-bg SVG/PNG) — internal verification / appendix, **not**
D2/D3.

## Figure-extraction quick reference (which tool for what)

- **Clean report schematics (D2, D3):** CircuiTikZ — `circuits/<name>.tex`, `make`
  → SVG, then annotate with op-point values. *Not* the LTspice render.
- **Waveform plots (D4 settling, D5 noise):** `plot_simulation(raw, signals=[…])`
  → PNG; pass explicit signals; or MATLAB (`mcp__matlab__…`) for publication polish.
- **Simulator-schematic snapshots (appendix / internal):** `render_schematic(asc,
  png=true)` → white-background SVG/PNG.
- **Computed numbers/plots (FoM, SNR, NEF):** MATLAB (`matlab -batch`).

## Deliverable-6 write-up — required content checklist (`07 §5.8`)

- [ ] **Why this architecture** (single-stage gain-boosted cascode + current-reuse) incl. **CMFB** choice — `02`
- [ ] **Sizing process** for **noise (incl. 1/f)** and **settling**; **output swing** + **capacitor sizing** — `03`, `04`, `01`
- [ ] **Dominant noise devices** + **NEF estimate** — `04` "Report items"
- [ ] **How the amplifier is biased** — `01`, bias block
- [ ] (good marks) **why our FoM differs from EE4520** woven in — `08`, D7

## Results we must match (acceptance)

From `00_spec_table.md` (hard specs, common to everyone): **SNR ≥ 66 dB**,
**$A\beta$ settle ≥ 66 dB @ 25 ns**, **$A_{settle}$ > 78 dB**, **$T_{settle}$ = 25 ns**,
**$P$ < 3 mW** (graded → minimise), **FoM > 170 dB**, $C_{load}=C_{in}$, input step
$=V_{out}/4$. All must hold at one operating point (`09` closure).

## Status

| Deliverable | Status |
|---|---|
| D1 table | ☐ values pending (Phase 1–5) |
| D2 node-V schematic | ☐ |
| D3 branch-I schematic | ☐ |
| D4 settling plot | ☐ |
| D5 noise plot | ☐ |
| D6 write-up | ☐ |
| D7 FoM comparison | ☐ (baseline 175.2 dB known) |
| D8 submission | ☐ (deadline 28 Jun 2026) |
