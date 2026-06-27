# Process models — `log018.l`

## Use `log018.l` (with $1/f$ noise). Do **not** use `logic018 no1of.l`.

Per the TA announcement (see `analysis/07_lecturer_clarifications.md`, §1), every
EE4525 simulation **must** use the BSIM3 0.18 µm model file that **includes
flicker ($1/f$) noise**:

| File | Size | $1/f$ noise | Use it? |
|------|-----:|-------------|---------|
| **`log018.l`** | ~295 KB | **Yes** (`NOIMOD = 1`, `KF`/`AF`, `NOIA/NOIB/NOIC`) | ✅ **required** |
| `logic018 no1of.l` | ~13 KB | No ("no $1/f$") — simplified EE4520 model | ❌ forbidden |

The device model names are the same in both (`nch` / `pch`, BSIM3 geometry-binned
as `nch.1 … nch.12`, `pch.1 … pch.12`), so the only thing that changes when you
swap the `.lib` path is whether flicker noise is modelled.

## Where the file lives on this machine

`models/log018.l` here is the **pristine** lecturer-distributed file
(`md5 c0d04b2f…`). For LTspice to actually load it, a copy is installed at the two
locations LTspice reads from on this machine:

| Location | Purpose | md5 |
|----------|---------|-----|
| `models/log018.l` (this repo) | archival / portable reference | `c0d04b2f…` (pristine) |
| `~/.wine/drive_c/Program Files/LTC/LTspiceXVII/lib/cmp/log018.l` | **read by the `ltspice` MCP runner** (`XVIIx64.exe` under Wine) | `95aafed7…` (path-patched) |
| `~/Documents/LTspiceXVII/lib/cmp/log018.l` | LTspice GUI install | `95aafed7…` (path-patched) |

### Why the installed copies differ from the pristine one (the *only* change)

The lecturer's file self-includes its device sections via an **absolute Windows
path** that points at `…\LTspiceIV\…`:

```
.LIB TT
  .lib 'C:\Program Files\LTC\LTspiceIV\lib\cmp\log018.l' MOS
.ENDL TT
```

`LTspiceIV` is **not installed** on this machine (only LTspice **XVII**), so a
verbatim copy would fail the nested `.lib … MOS` include and load **no** transistor
models. The installed copies have exactly that path string patched
`LTspiceIV` → `LTspiceXVII` (20 lines). This is provable:

```bash
sed 's/LTspiceIV/LTspiceXVII/g' models/log018.l | md5sum   # -> 95aafed7…  (the installed copy)
```

All BSIM3 parameters and the $1/f$-noise data are **byte-for-byte the lecturer's** —
only the self-include path is corrected so the models resolve under LTspice XVII.

## How schematics reference it

Active EE4525 schematics include the TT corner via a SPICE directive:

```
.lib 'C:\Program Files\LTC\LTspiceXVII\lib\cmp\log018.l' TT
```

All schematics in `design/` and `simulations/` use this. The historical
`from-ee4520/` schematics are left untouched (they still reference the old
`logic018 no1of.l`); do not run project deliverables from there.

> If you add a new schematic, copy the `.lib '…\LTspiceXVII\lib\cmp\log018.l' TT`
> directive — **not** `logic018 no1of.l`.
