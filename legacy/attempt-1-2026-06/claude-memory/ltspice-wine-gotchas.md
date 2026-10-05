---
name: ltspice-wine-gotchas
description: Non-obvious rules for running LTspice via Wine on Ubuntu (avoid repeating mistakes)
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6f789942-9dd7-4766-b7a8-2cae1298661d
---

Operating LTspice on this Ubuntu box (Wine):

- **A display is mandatory even for `-b` batch** — with no `DISPLAY` the sim silently writes no
  `.raw`. The `ltspice` MCP runs under `xvfb-run` so it's headless-safe.
- **Wine stderr noise is harmless**: `wine: Read access denied for device "\\??\\Z:\\"` and
  `err:menubuilder:Process_Link ... .lnk` always appear. Judge success by `returncode==0` +
  output files, never by stderr.
- LTspice exe: `~/.wine/drive_c/Program Files/LTC/LTspiceXVII/XVIIx64.exe` (default in runner;
  `~/LTspice64.exe` is just the installer).
- AC analysis writes **no** `.op.raw`. `.step` runs produce stepped/complex `.raw` (parser now
  splits into `n_steps`/`steps[]`).
- `write_schematic` auto-router is unreliable (disconnected pins) → design via netlist/ngspice;
  if a real `.asc` is needed, hand-author geometry (pin offsets in OPERATING_RULES.md).
- **Model libs must live in the Wine-prefix `lib/cmp/`** (`~/.wine/drive_c/Program Files/LTC/LTspiceXVII/lib/cmp/`) —
  that's what the runner's `XVIIx64.exe` reads for `C:\Program Files\LTC\LTspiceXVII\...`. The
  GUI's `~/Documents/LTspiceXVII/lib/cmp/` is a *separate* tree; a file there alone won't be found.
- **The Delft `log018.l` self-includes an absolute `...\LTspiceIV\...` path** that doesn't exist
  here → verbatim copy loads **no** transistor models. Patch `sed s/LTspiceIV/LTspiceXVII/g`
  before placing (the working install copy is exactly the pristine file so-patched). For EE4525
  use `log018.l` (has 1/f noise, `NOIMOD=1`); **never** `logic018 no1of.l` (no 1/f). Verified: a
  sim then logs `Ignoring BSIM parameter XL/XW/ACM...` = models loaded OK.

**Why:** these cost real debugging time the first pass. **How to apply:** before any LTspice
sim work, recall these; don't re-diagnose the stderr noise or the missing-display failure.
Part of [[circuit-sim-tooling]].
