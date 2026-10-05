# design/

| Folder | What |
|---|---|
| `templates/` | fixed test benches (`bench_tran.cir`, `bench_noise.cir`, `bench_loop.cir`) and the `amp.inc` skeleton. Validated on 5 Oct 2026 by dropping the example amplifier in. |
| `work/` | netlist iteration (copy the templates here). One `amp.inc` shared by all benches. |
| `final/` | the drawn deliverable schematics `amp_tran.asc`, `amp_noise.asc` and `reference_tran.cir` (the netlist they are proven equivalent to). Only these are evaluated for the report. |

Bench contract: amplifier inputs `vip vin`, outputs `vop von`, amplifier supply `vdd` (source `Vdd`,
graded power), bias supply `vddb`, CM reference `vcmr` (0.9 V), ground `0`. Parameters `Cin`, `VoutStep`,
`tstep`, `Tsettle`, `trise` are read by the tools. Input step 50 ps edges; Rin/Rfb 100 MΩ/400 MΩ
`noiseless`; `reltol=1e-4`.
