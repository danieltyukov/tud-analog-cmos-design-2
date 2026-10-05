---
name: sizing
description: Hand-calculation and gm/ID sizing procedure for the EE4525 two-stage class-AB residue amplifier (budget for swing, Cin, Cc, crossover, gain, currents; device sizes from LTspice gm/ID tables; compensation and CMFB targets). Use before writing or changing amp.inc, when choosing currents or device sizes, or when a spec misses and the fix is not obvious.
---

# Sizing procedure (derive first, then simulate)

**Rules first**
- Write the budget numbers in `PROGRESS.md` before simulating; after simulating, print a
  reconciliation table (hand value vs simulated) and explain every gap above 20 %.
- Use `tools/gmid.py` (LTspice-derived tables), not textbook square law and not ngspice.
- Aβ binds, not A: plan for $A_0\beta$ ≥ 72 dB at the output extremes and Aβ(25 ns) ≥ 66.5 dB.
- Full background and references: `brief/design-strategy.md`. Specs: `brief/spec.md`.

## 1. Budget (paper)

1. Swing: pick $V_{step}$ (differential peak) 1.2 to 1.3 V for a push-pull output (outputs 0.9 ± V/2,
   keep ≥ 100 to 150 mV on output Vdsat).
2. Noise: `uv run tools/metrics.py budget --vout 1.2 --cin 1.8p` gives kT/C ($42kT/C_{in}$) and the
   allowed amplifier noise for SNR 66 dB. Plan SNR 66.3 dB. Two-stage amplifier noise ≈ $\alpha kT/C_c$
   with $\alpha \approx 18.5$ (calibrated), so pick $C_c$ for the amplifier share, $C_{in}$ for kT/C.
3. Settling: $\varepsilon = 4.7\times10^{-4}$ in 24 ns. With $p_2 \approx 4\omega_c$: $f_c \approx 40\,\mathrm{MHz}$,
   $\omega_c = \beta g_{m1}/C_c$ so $g_{m1} = 2\pi f_c C_c/\beta$ (β ≈ 0.18 after $C_p$).
4. Slew: $t_{slew} \approx (\beta V_{step}/V_{lin} - 1)/\omega_c$, $V_{lin} = 2/(g_m/I_D)$; keep below about 7 ns.
5. Output stage: $g_{m2} \geq 4\omega_c[C_{L,eff}(1 + C_1/C_c) + C_1]$, $C_{L,eff} = C_L + (1-\beta)C_{fb} + C_{par}$.
6. Gain: stage 1 60 to 70 dB (cascoded, long-L loads), stage 2 30 to 36 dB.
7. Currents: $I_{D1} = g_{m1}/(g_m/I_D)$, output quiescent from $g_{m2}$ at gm/ID 14 to 16, CMFB ≤ 10 µA.

## 2. Devices from tables

```bash
uv run tools/gmid.py table pch --L 0.25u        # pick gm/ID vs fT / gain trade
uv run tools/gmid.py size pch --L 0.25u --gmid 16 --id 70u   # W, m, Vgs, Vdsat, Cgg, fT
```
Guides: input PMOS gm/ID 16 to 18, L 0.25 to 0.36 µm (L above 0.36 µm costs β via Cgg); cascodes 12 to 14;
NMOS loads gm/ID 8 to 10, L 1 to 2 µm (gain, 1/f); output devices gm/ID 14 to 16, L 0.25 µm.
Tables are at Vds = 0.6 V and W = 1/5/20 µm (narrow devices carry less current per W). Integer m only.

## 3. Compensation and CMFB targets

- Current-buffer (cascode) Miller compensation: no RHP zero, no $R_z$ noise. If using Miller + $R_z$,
  remember $R_z$ adds thermal noise and its doublet can ring before 25 ns.
- Loop: PM 72 to 78°, no doublet below $3f_c$ (check `tools/metrics.py loop`).
- CMFB: continuous time, resistive sense 1 to 2 MΩ per side (± 30 to 50 fF), 5 to 10 µA error amp vs
  `vcmr`, acting on part of the stage-1 loads; CM loop PM ≥ 60°, CM excursion during the step < 50 mV.
- Class-AB output: NMOS gate from stage 1 directly, PMOS gate through a capacitive level shift
  (0.5 to 1 pF, DC-set through about 2 MΩ, corner below 100 kHz).

## 4. Bias block

Separate `Vddb`, EE4520-style cascode mirrors (`reference/ee4520/`, `legacy/.../design/biasing/`),
every bias line decoupled with a big cap (the value is free, "big"; 1 to 10 nF is ample).
Fixed current ratios between the bias currents (assignment p. 3).
