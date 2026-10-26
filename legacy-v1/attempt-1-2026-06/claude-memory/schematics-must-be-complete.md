---
name: schematics-must-be-complete
description: "User requires every LTspice .asc to be a COMPLETE, honest, GOOD-LOOKING schematic — all parts drawn as symbols (never SPICE text-directive elements), connected by drawn WIRES not net-label flags, all .param/.model/.meas consolidated INSIDE the Parameters/Sims box, blocks laid out like the template (no overlaps, circuitry stays inside its boundary box, consistent title fonts), no deleted-component gaps, no stale labels/params"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8c207938-735c-4c08-9f30-17cb2d1c363d
---

When the Phase-3 agent built the real SC-CMFB, it added the switched-cap network
(`.model SWCM`, `Cs1/Cs2`, `S1p–S4n`, `Vcmr`, `Ehelp/Rhelp`, clocks) as **SPICE
text-directive lines** and **deleted the ideal `E1` VCVS symbol** — leaving a visible
gap and a now-stale "Ideal CMFB Unloaded" label. The user opened the `.asc`, saw the
gap + stale label, and reacted strongly: "THIS MUST NEVER HAPPEN — it MUST ALWAYS
CONTAIN ALL THE COMPONENTS."

**Why:** the `.asc` is read by a human (and a grader) and forked by later phases; a
schematic with a missing-symbol gap, a label that describes a part that was removed,
or a sub-network that exists only as text reads as broken/incomplete and is below the
quality bar for D2/D3 (schematic + node-voltage / branch-current deliverables). It
also makes the file confusing to extend in Phases 4–5.

A second round was needed: the agent redrew the parts as real symbols but (a) connected
them with **net-label FLAGs instead of drawn WIRES** (so it still looked like a field of
disconnected floating symbols each tagged `ap`/`bp`/`phi1`…), and (b) dropped the new
`.param Ccm/Cchold/Rhelp` + `.model SWCM` in a **floating text block OUTSIDE** the
"Parameters, Simulations & Measurements" boundary box. The user rejected both.

**How to apply (now a project CLAUDE.md rule — 5 points):** when replacing an ideal block
with a real one (CMFB done, gain-boosters Phase 4, current-reuse Phase 5):
(1) draw every element as a **real symbol**, never a SPICE text-directive element;
(2) **connect pins with drawn `WIRE` segments** — net-label `FLAG`s only for nets that span
the sheet (rails, clocks, far-apart shared I/O), NEVER as a substitute for wiring a local
cluster (no field of flag-tagged floating symbols);
(3) put **all** `.param`/`.model`/`.lib`/`.op`/`.ac`/`.tran`/`.meas` **inside the single
"Parameters, Simulations & Measurements" boundary box** (consolidated, old lines removed,
new lines added in-box) — never a floating directive block elsewhere;
(4) **lay it out cleanly** — match the existing titled blocks' style, NO overlapping
symbols/wires/text, keep all circuitry **inside its boundary rectangle** (enlarge the box if
the block grows — never let parts spill outside), and use the **same title font size/style** as
the other block titles (title fits in its box);
(5) **remove/relabel** the old block's label, delete leftover symbols (no orphan gaps), and
**prune stale `.param`/`.meas`** (e.g. the `Voutp2` artifact measurements);
(6) after any redraw, re-run `.op`/`.ac`/`.tran` and confirm the verified numbers still
match (CMFB baseline: CM 0.900 V, I(Vdd) 1.547 mA, A0 93.8–93.9 dB, GBW 264 MHz, PM 89°).
The clean report figure still comes from CircuiTikZ ([[circuit-sim-tooling]]), but the `.asc`
itself must also be complete and honest. Relates to [[ee4525-ac-bench-and-sizing]],
[[ee4525-sc-cmfb]].
