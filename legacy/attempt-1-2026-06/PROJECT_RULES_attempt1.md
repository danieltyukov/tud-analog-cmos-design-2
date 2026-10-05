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

## LTspice `.asc` schematic hygiene (MANDATORY — applies to every phase/agent)

The `.asc` is read by a human and a grader and is forked by later phases. It must
**always be a complete, honest schematic of exactly what was simulated** — never a
course-template file with bolt-on text and leftover labels.

1. **Real drawn components, NOT text-directive elements.** Every circuit *element*
   — transistor, R, C, switch, source, VCVS — must be a **drawn symbol**. Do **NOT**
   add circuit elements as SPICE netlist text lines (e.g. `S1p ap Voutp phi2 0 SWCM`,
   `Cs1 ap bp {Ccm}`, `Ehelp …`, `Vphi1 …`). This holds for every phase: SC-CMFB
   switches/caps/clocks (Phase 3), gain-boosters (Phase 4), current-reuse devices
   (Phase 5). *Text directives are allowed ONLY for non-element items:* `.lib`,
   `.include`, `.model`, `.param`, `.op`, `.ac`, `.tran`, `.meas`, `.option`.

2. **Connect components with drawn WIRES, not net-label flags.** Pins that connect must
   be joined by actual `WIRE` segments so the schematic *looks* connected. Net-label
   `FLAG`s are allowed **only** for nets that genuinely span the sheet (supply rails,
   clock lines, shared far-apart I/O like `Voutp`/`Vbcm`) — **never** as a substitute
   for wiring up a local cluster of parts. A field of floating symbols each tagged with
   a net name (e.g. three switches + a cap all labelled `ap` with no wire between them)
   is **not acceptable** — draw the wire.

3. **All directives live INSIDE the one "Parameters, Simulations & Measurements" box.**
   Every `.param`/`.model`/`.lib`/`.op`/`.ac`/`.tran`/`.meas`/`.option` goes inside that
   single titled boundary box, consolidated — **not** in a floating block elsewhere on
   the sheet. When you add new params/models (e.g. `Ccm`, `Cchold`, `Rhelp`,
   `.model SWCM`), put them *in the box* alongside the existing ones; when something is
   superseded, **remove the old line from the box**.

4. **Lay it out cleanly — match the existing blocks, no overlaps, stay inside the box.**
   Mirror the course template's style: each functional block sits inside its own titled
   rectangle (Biasing, Decoupling, etc.). Newly drawn circuitry must **(a)** NOT overlap
   any other symbol, wire, or text — give parts room; **(b)** stay **inside** its
   designated boundary rectangle — if the block grows, **enlarge the rectangle** rather
   than letting symbols/wires spill outside it; **(c)** use the **same title font size
   and style** as the other block titles, with the title fitting inside its box. Match
   the spacing/alignment of the existing blocks so the sheet reads consistently. Before
   finishing, scan the render for overlaps and out-of-box elements and fix them.

5. **Keep it updated — no stale anything.** When you replace an ideal block with a
   real one: **delete the old symbols** (no orphan gaps where a part was removed),
   **relabel the block** to what it now is (never an "Ideal CMFB" caption over a real
   SC-CMFB), and **prune stale `.param`/`.meas`** that no longer apply (e.g. artifact
   `Voutp2` measurements, superseded sizing). The file must show the *current* values
   and *current* topology so the reader can see exactly what was calculated — never
   leftover parameters or simulations from the course template.

6. **Verify after every change.** Re-run the sim and `render_schematic` (white bg) and
   confirm the verified numbers still hold. The clean report figure is still CircuiTikZ
   (below), but the `.asc` itself must also be complete and current.

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
