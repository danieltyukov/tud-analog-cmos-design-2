---
name: report-latex
description: Builds and reviews the EE4525 8-page LaTeX report (report/main.tex) from generated results, CircuiTikZ D2/D3 schematics with simulated node voltages and branch currents, the D4/D5 plots, the D6 FoM comparison and the one-page short explanation. Use when writing, building, checking or fixing anything in report/.
---

# Report: build, fill, review

**Rules first**
- Exactly 8 pages, one item per page, in the compulsory order (`brief/spec.md` section 5). No contents page.
- Never type a simulated number. Values come from `report/generated/results.tex` (`\resSNR`, `\resPower`, ...)
  and `report/generated/opvals.tex` (`\opV{node}`, `\opI{device}`), written by
  `uv run tools/evaluate.py ... --publish` on the final `.asc`. Re-publish after any design change.
- D2/D3 are readable drawings, not simulator screenshots; the CMFB (and any sub-block) goes on the
  SAME page as a second smaller figure.
- Writing: no emojis, no em/en dashes, plain technical prose, no filler.

## Build and look

```bash
uv run tools/report.py build     # latexmk in report/ (halts on error), then the info check below
uv run tools/report.py info      # page count (must be 8), LaTeX warnings, unresolved ?? and TODO
uv run tools/report.py pages     # results/pages/p-<n>.png: Read each one and look at it
```
Unresolved values render as red `??`; `tools/check_done.py` rejects them and any `TODO` text.

## D2 / D3 schematics (`report/circuits/`)

- One drawing per block (`amp.tex`, `cmfb.tex`, ...) used twice: `\showIfalse` (D2, voltages) and
  `\showItrue` (D3, currents). Tag nodes with `\Vtag{<ltspice node>}` and devices with `\Itag{<device>}`
  (lower-case names exactly as in the netlist; `uv run tools/opvals.py design/final/amp_tran.asc --list`).
- Annotate every node and every branch. Show rails, the bias lines' sources, Cc and the CMFB links.
- Keep device names next to symbols (M1, M2, ...) and sizes in a compact table only if it fits the page.

## D4 / D5

`evaluate.py --publish` copies `results/<tag>/d4_settling.pdf` and `d5_noise.pdf` into `report/figures/`.
D4 must show A and Aβ in one figure, Aβ from 0 dB, the 25 ns line, spec lines, T30/T38.6 markers.

## D6 (page 7): FoM difference, step by step

Formula, EE4525 values (`\resPower`, `\resTau`, `\resSNR`, `\resFoMlin`, `\resFoMdB`), EE4520 values
(P 0.1119 mW, τ 497.4 ns, SNR 80.85 dB, FoM 175.20 dB; `reference/ee4520/README.md`), the ratio split into
P, τ and SNR² factors, then the physical reasons (real CMFB and stages vs ideal blocks, 1/f model, kT/C
added, speed-driven vs noise-driven design, efficiency factors). Show the arithmetic.

## Short explanation (page 8, at most one page)

Cover, in this order: every feature of the D4 plot (Aβ starts at 0 dB; A starts at
$20\log_{10}(1/\beta_{act})$; the gap and $\beta_{act}$ = `\resBetaActual` vs ideal 0.2 from input-pair $C_p$;
the slew segment; the linear segment whose slope gives τ; spikes are error zero crossings, the first at
`\resFirstPeak` ns after the step, after the deadline; the floor is the static $A_0\beta$ error); why the
architecture and the CMFB; sizing for noise (incl. 1/f: long L on loads, PMOS input) and settling; output
swing and capacitor choice; dominant noise devices (from `results/<tag>/summary.json` noise_top) and the NEF
with its definition (`\resNEF`); how it is biased (separate Vddb, mirrors, decoupling); the power window.

## Review loop

1. `uv run tools/report.py build` and `pages`, then look at every page yourself.
2. Run the `report-reviewer` agent; fix every correctness finding; rebuild.
3. `uv run tools/check_done.py`.
