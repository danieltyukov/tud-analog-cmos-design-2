# Process model `log018.l`

`log018.l` is the BSIM3 0.18 µm model file distributed with the course, unchanged
(md5 `c0d04b2f…`). It models flicker noise (`NOIMOD = 1`, `KF`/`AF`, `NOIA`/`NOIB`/`NOIC`), which
the assignment requires. The simplified EE4520 file `logic018 no1of.l` has no flicker noise and
must not be used here. Device names are `nch` and `pch`, geometry-binned as `nch.1` to `nch.12`
and `pch.1` to `pch.12`.

`design/final/log018.l` is the same file, byte for byte, placed next to the schematics, which
load it with `.lib 'log018.l' TT`.

## Installing it for LTspice

The file includes its own device sections through an absolute Windows path:

```
.LIB TT
  .lib 'C:\Program Files\LTC\LTspiceIV\lib\cmp\log018.l' MOS
.ENDL TT
```

So LTspice only finds the transistor models when a copy of the file is at that location. With a
different LTspice version, either create that folder and put the file there, or replace
`LTspiceIV` in the file with the installed version's folder name (20 lines):

```bash
sed 's/LTspiceIV/LTspiceXVII/g' models/log018.l > log018_xvii.l
```

The model parameters are not touched by this. `tools/lt.py` points every run at the copy
installed under `C:\Program Files\LTC\LTspiceXVII\lib\cmp\`.
