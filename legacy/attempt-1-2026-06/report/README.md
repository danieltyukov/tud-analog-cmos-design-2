# Report — structure, deliverables, figures & how to extract each

The execution map for the final report. Specs to match → `../analysis/00_spec_table.md`;
sims → `../analysis/09_simulation_runbook.md`; tools → `../LTSPICE_TOOLCHAIN.md`.

> **Report skeleton: `report.tex`** — the LaTeX report (article class), already in the
> **compulsory EE4525 structure**, adapted from the EE4520 template
> `../from-ee4520/HW2_EE4520_5714699/main.tex`. It compiles as-is (figure
> placeholders). Fill the **Achieved** column and drop figures into `figures/`
> (swap each commented `\includegraphics` line in for its placeholder). Build:
> `pdflatex report.tex` (twice, for the ToC).

> **EE4525 needs only 2 plots + 2 annotated schematics** (D4 settling, D5 noise;
> D2/D3 schematics). Submit **PDF named `[StudentNumber].pdf`**, ≤ 2 submissions,
> via `https://edu.nl/3c9tf` — **deadline Sun 28 Jun 2026, 23:59**.

## Compulsory report structure (project PDF, p. 11 — "COMPULSARY REPORT STRUCTURE")

**One page per item, in this exact order:**

| Page | Item | Content |
|---|---|---|
| 1 | **Title** | Name + Student Number + "EE4525 2026" |
| 2 | **Deliverable 1** | Table of Results (the 22-row table) |
| 3 | **Deliverable 2** | Schematic with **all node voltages** |
| 4 | **Deliverable 3** | Schematic with **all branch currents** |
| 5 | **Deliverable 4** | Plot of settling behaviour |
| 6 | **Deliverable 5** | Plot of noise density (showing integrated noise) |
| 7 | **Deliverable 6** | **Explanation of the FoM difference EE4520 ↔ EE4525** |
| 8 | **Short Explanation** | ≤ 1 page — **explain every aspect of the D4 settling plot** + the 4 bullets below |

> **Numbering note:** the compulsory structure (p. 11) and the TA clarification use
> **Deliverable 6 = the FoM comparison** (the "skip if you didn't take EE4520" item;
> *we took it → required*). The design write-up is the separate **"Short
> Explanation"** on page 8 — **not** numbered as a deliverable. (The p. 5 list
> numbers them loosely as 6 = write-up, 7 = FoM; follow the **p. 11** structure.)

## Deliverable → figure/output → how to make it

| Page item | Output | Produced by | **How to extract** | Method doc |
|---|---|---|---|---|
| **D1** table | 22-row table | all sims + hand calc | fill `00_spec_table.md` → copy into report + submission form | `00`, `09` |
| **D2** node voltages | **clean, readable** schematic(s) — *separate* sheets for **gain-boosters** and **CMFB** too — with node V on every node (PDF: *"not a simulator schematic"*) | DC op-point (sim A) | **CircuiTikZ** `circuits/<…>.tex` → SVG, annotate V from `read_op_point` | `09 §A` |
| **D3** branch currents | same, but **branch currents** per branch (boosters + CMFB on separate sheets) | DC op-point (sim A) | CircuiTikZ schematic + $I_d$ per branch | `09 §A` |
| **D4** settling | one plot: $A(t)$ **and** $A\beta(t)$, $A\beta$ **from 0 dB**, markers @ 25 ns / 78 dB / 66 dB; use $\mathrm{Acc}_{dB}=20\log_{10}(V_{out,max}/(|V(\text{vg})|+1\mathrm{n}))$, $V_{out,max}$ **fixed** | transient (sim D) | `plot_simulation` (or MATLAB) | `06`, `09 §D`, `07 §3` |
| **D5** noise | output-noise PSD **10 kHz–100 GHz** + **integrated** value shown | noise (sim E) | `plot_simulation` on noise `.raw`; annotate integrated $V_n$ | `04`, `09 §E` |
| **D6** FoM comparison | step-by-step EE4520 ↔ EE4525 | hand calc | EE4520 baseline **175.2 dB** (`../from-ee4520/README.md`); method `08` | `08`, `from-ee4520` |
| **Short Explanation** | ≤ 1 page text | — | content checklist below | `07 §5.8`, `08` |

**Appendix (optional):** the LTspice *simulator* schematics via `render_schematic`
(white-bg) — internal verification, **not** D2/D3.

## Figure-extraction quick reference (which tool for what)

- **Clean report schematics (D2, D3):** CircuiTikZ (`circuits/*.tex`, `make` → SVG),
  annotated with op-point values — **separate readable sheets** for core,
  gain-boosters, and CMFB. *Not* the LTspice render.
- **Waveform plots (D4, D5):** `plot_simulation(raw, signals=[…])` → PNG (explicit
  signals), or MATLAB for polish.
- **Appendix sim schematics:** `render_schematic(asc, png=true)`.
- **Computed numbers (FoM, SNR, NEF):** MATLAB.

## Short Explanation (page 8) — required content (`07 §5.8`, PDF p. 11)

- [ ] **Explain every aspect of the D4 settling plot** (the $A(t)$/$A\beta(t)$ shape, the $1/\beta$ gap, why it meets 78/66 dB at 25 ns)
- [ ] **Why this architecture** (single-stage gain-boosted cascode + current-reuse) incl. **CMFB** choice — `02`
- [ ] **Sizing process** for **noise (incl. 1/f)** and **settling**; **output swing** + **capacitor sizing** — `03`, `04`, `01`
- [ ] **Dominant noise devices** + **NEF estimate** — `04`
- [ ] **How the amplifier is biased** — `01`, bias block
- [ ] (good marks) the **actual-vs-ideal β** effect (`07 §3`) and the **two-stage alternative we rejected** (`11_two_stage_alternative.md`)

## Results we must match (hard specs, common to all — `00_spec_table.md`)

**SNR ≥ 66 dB**, **$A\beta$ settle ≥ 66 dB @ 25 ns**, **$A_{settle}$ > 78 dB**,
**$T_{settle}$ = 25 ns**, **$P$ < 3 mW** (graded → minimise, best < 0.3 mW),
**FoM > 170 dB** (linear < $9.5\times10^{-18}$ J), $C_{load}=C_{in}$, input step
$=V_{out}/4$. All hold at one operating point (`09` closure).

## Status

| Page item | Status |
|---|---|
| D1 table | ☐ values pending (Phase 1–5) |
| D2 node-V schematic(s) | ☐ |
| D3 branch-I schematic(s) | ☐ |
| D4 settling plot | ☐ |
| D5 noise plot | ☐ |
| D6 FoM comparison | ☐ (baseline 175.2 dB known) |
| Short Explanation | ☐ |
| Submission | ☐ (deadline 28 Jun 2026, 23:59) |
