# Project-local conventions for tud-analog-cmos-design-2

These rules **override** the parent `/home/danieltyukov/workspace/tud/CLAUDE.md` for this
directory only.

## Circuit simulation toolchain

The full verified design→verify→simulate→extract→iterate workflow (which MCP for
what, the `.asc`→SVG/PNG schematic renderer, gotchas) is in
[`LTSPICE_TOOLCHAIN.md`](LTSPICE_TOOLCHAIN.md). This project uses **`ltspice`**
(Wine) + **`spicelib`** (ngspice) for simulation and **`matlab`** (R2025b) for
post-processing/report math — **not** SLiCAP. Always use the `log018.l` model
(with $1/f$ noise), never `logic018 no1of.l` (`models/README.md`).

## Math notation

Use **LaTeX math** in all markdown files in this project (NOT the parent's Unicode rule).

- Inline: `$\beta = C_{fb}/(C_{in}+C_{fb})$`
- Display: `$$\tau \leq \frac{T_{settle}}{\ln(10^{A\beta/20})}$$`
- GitHub renders both natively via MathJax — no plugin needed.
- Use `\mathrm{dB}`, `\mathrm{ns}` etc. for units; never italic.
- Use `\,` for thin space between number and unit: `$25\,\mathrm{ns}$`.

## Circuit diagrams

Use **CircuiTikZ** source compiled to SVG.

1. Source goes in `circuits/<name>.tex`, one circuit per file.
2. Each `.tex` includes the shared preamble: `\input{header.tex}` (relative).
3. Run `make` in `circuits/` to compile every changed `.tex` to a sibling `.svg`.
4. Reference from markdown:

   ```markdown
   ![Biasing block](../circuits/biasing_block.svg)
   ```

5. `circuits/build/`, `*.aux`, `*.log`, `*.pdf` are gitignored. Commit only `.tex` + `.svg`.

## Why this stack

- **CircuiTikZ** is the academic standard for analog/MOS schematics; output is publication
  grade and the source is plain text (clean diffs).
- **SVG** embeds in any markdown viewer (GitHub, VS Code preview, pandoc) and stays crisp at
  any zoom.
- **LaTeX math** in markdown works on GitHub natively (MathJax) and in every modern previewer.

## Build dependencies (already present on this machine)

`pdflatex` (TeXLive 2023) · `circuitikz.sty` · `pdftocairo` (poppler) · `inkscape` (fallback)

## Editing workflow

1. Edit `circuits/foo.tex`.
2. `cd circuits && make` (only rebuilds changed files).
3. Reference `../circuits/foo.svg` from any `.md` in `analysis/` or `report/`.
4. Commit `foo.tex` and `foo.svg` together.
