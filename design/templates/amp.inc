* EE4525 amplifier netlist fragment (included flat by bench_tran.cir and bench_noise.cir).
* External nets: vip vin (inputs)  vop von (outputs)  vdd (amp supply)  vddb (bias supply)
*                vcmr (0.9 V CM reference)  0 (ground)
* Rules (brief/spec.md section 3): NMOS/PMOS/R/C only; real CMFB; every amplifier block on vdd;
* bias block on vddb with big decoupling caps; integer m; NMOS bulk = 0; R <= a few Meg.
* Put sizing knobs in .param lines here (one source of truth for both benches).
*
* .param L1=0.5u W1=20u M1=2 ...
*
* ---- bias block (on vddb) ----
*
* ---- stage 1 ----
*
* ---- stage 2 / output ----
*
* ---- compensation ----
*
* ---- CMFB ----
