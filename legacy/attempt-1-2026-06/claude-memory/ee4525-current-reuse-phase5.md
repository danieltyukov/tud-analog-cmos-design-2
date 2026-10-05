---
name: ee4525-current-reuse-phase5
description: EE4525 Phase-5 current-reuse migration + settling/noise/FoM closure — results and the hard-won bench/design gotchas
metadata: 
  node_type: memory
  type: project
  originSessionId: 0c7a2f9b-b9db-4ce7-83d7-07cbaca0a7f3
---

EE4525 Phase 5 DONE (2026-06-28), canonical = `design/current-reuse/folded_cascode_cr{,_ac,_tran,_noise}.asc`, record `phase5_results.txt`. The NMOS-only input was made **complementary current-reuse**: the two top PMOS current sources `Mp1.2/Mp3.2` were re-wired (gate `Vbp`→`Vip`/`Vin`) into a PMOS INPUT pair sharing the fold nodes with NMOS `Mn3.2/Mn4.2` → g_m=g_mN+g_mP on one branch. PMOS in moderate inversion (Vsg=0.6, **input CM raised to 1.2 V**; far-end ref 1.275 V). Just 2 gate re-wires — no new symbols.

**Verified at the locked point** (2× booster bias): A0 106.7 dB · GBW 266 MHz · PM 86.9° · **I(Vdd) 1.135 mA / 2.04 mW (−32% vs Ph-4)** · Vn,amp 209.5 µV → SNR **66.8 dB** · τ 3.29 ns → **FoM 170.5 dB (>170 PASS)**.

**Honest near-miss:** the 25 ns settling lands A 77.2 / Aβ 62.7 dB at 25 ns (reaches 78/66 at ~26.5 ns). Binding = **Class-A slew** (I_cas/C_L=27 V/µs, ~15 ns slew) + a residual **gain-booster doublet**.

Hard-won gotchas (cost many iterations — see [[ee4525-ac-bench-and-sizing]], [[ee4525-gain-boost]]):
- **Pseudo-diff PMOS input current is steeply CM-sensitive** (no tail): a 20 mV input-CM error shifts I(Vdd) ~180 µA. In the settling bench you MUST reproduce the .op bias (vg 1.2 V, out-CM 0.9 V, idd 1.036 mA) BEFORE judging slew, else slew looks worse than it is.
- **Settling-bench CMFB:** continuous ideal helper needs `Rhelp=100Meg` (dominant pole) + moderate gain (G≈12) for stability — G high with small Rhelp LATCHES/oscillates (idd→8–17 mA). Stiffen `Rin`→1G so the resistive divider pins the DC bias to (4·Vfar+Vout_CM)/5. Real SC-CMFB CM-stability is verified separately (Ph-3 CM-step bench), so an ideal continuous CMFB is an acceptable sim-aid for the *differential* D4/D5 benches.
- **Booster-doublet tuning is non-monotone:** 1×→62.5 dB, **2×→77.2 dB (best)**, 2.5×→59 dB (overshoots/rings). Use `scale_boosters.py`.
- **Raising I_cas for slew BACK-FIRES:** bigger output devices add cascode cap that re-opens the doublet (I_cas 136→280 µA dropped A@25ns to 55–66 dB). Reducing C also lowers PM. So lean I_cas + 2× boosters + C=5p is optimal. Full closure → Class-AB output or decoupled sink/cascode sizing (not taken).
- LTspice `voltage` R0 pins at origin+(0,16)/(0,96); a FLAG must sit exactly on the pin or it floats (NC_xx warning).
