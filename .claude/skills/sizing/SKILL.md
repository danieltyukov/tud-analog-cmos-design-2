---
name: sizing
description: Hand-calculation and gm/ID sizing procedure for the EE4525 two-stage residue amplifier (attempt 3: PMOS-input telescopic stage 1, common-source stage 2 with AC-coupled PMOS, Miller Cc + Rz, CT CMFB, replica bias): budget for swing, Cin, Cc, crossover, gain, currents; device sizes from LTspice gm/ID tables; compensation and CMFB targets. Use before writing or changing amp.inc, when choosing currents or device sizes, or when a spec misses and the fix is not obvious.
---

# Sizing procedure (derive first, then simulate)

**Rules first**
- Write the budget numbers in `PROGRESS.md` before simulating; after simulating, print a
  reconciliation table (hand value vs simulated) and explain every gap above 20 %.
- Use `tools/gmid.py` (LTspice-derived tables), not textbook square law and not ngspice.
- Aβ binds, not A: plan for $A_0\beta$ ≥ 72 dB at the output extremes and Aβ(25 ns) ≥ 66.5 dB.
- TA rules (`brief/ta-feedback-2026-10-12.md`): simple architecture, replica bias, FoM ≤ 177 dB,
  ordinary two-stage settling curve (check τ against a 1 % small-step run).
- Background: `brief/design-strategy.md` (sections 1, 2, 5, 6). Specs: `brief/spec.md`.

## 1. Budget (paper)

1. Swing: $V_{step}$ (differential peak) about 1.2 V: outputs 0.9 ± 0.6 V, keep ≥ 100 mV on the NMOS driver
   Vdsat and the PMOS source Vsd at the extremes.
2. Noise: `uv run tools/metrics.py budget --vout 1.2 --cin 2p` gives kT/C ($42kT/C_{in}$) and the allowed
   amplifier noise. Plan SNR 66.2 dB. Amplifier noise ≈ $\alpha kT/C_c$, α about 15 to 17 here
   (input pair ≈ half, NMOS loads ≈ a third, $R_z$ ≈ 8 %).
3. Settling: with $R_z$ placing its zero near $p_2$, the closed-loop poles sit above $\omega_c$
   (measured τ ≈ 0.55/ω_c). $\omega_c = \beta g_{m1}/C_c$, β ≈ 0.195 after $C_p$.
4. Slew: stage 1 pushes its tail into $C_c$; the AC-coupled PMOS lets the rising output draw more than its
   quiescent current. A pure class-A stage 2 is slew-limited at $I_2/(C_{L,eff}+C_c)$ (> 1 mW to pass).
5. Gain: stage 1 ≈ 60 to 66 dB (cascoded, long-L loads), stage 2 ≈ 25 to 30 dB.
6. Currents: everything is a multiple of $I_{bnp}$: tail $2N I_{bnp}$, stage 2 $M_2 I_{bnp}$ per side,
   CMFB $M_{cmt} I_{bnp}$.

## 2. Devices from tables

```bash
uv run tools/gmid.py table pch --L 0.18u
uv run tools/gmid.py size pch --L 0.18u --gmid 16 --id 60u   # W, m, Vgs, Vdsat, Cgg, fT
```
Guides: input PMOS gm/ID 16 to 17 at L 0.18 µm (low Cgg for β); cascodes gm/ID 12; NMOS loads gm/ID 9 to 10 at
L 2 µm (NMOS flicker EF 0.825 integrates into the loop bandwidth: L is the lever); NMOS driver gm/ID about 10 at
L 0.25 µm so its Vgs equals the load Vgs (the stage-1 output then sits at the replica's vbn). Integer m only.

## 3. Compensation and CMFB targets

- Miller $C_c$ from $x_1$ to the output with $R_z$ in series; $R_z$ tracks $(1/g_{m2})(C_c + C_{L,eff})/C_c$
  (see `amp.inc`). Aβ(25 ns) is a sharp function of $R_z$: sweep it whenever currents change.
- The first error zero crossing must stay after 25 ns with margin (≥ 27 ns nominal); check ±1 % on $C_c$, $R_z$.
- CMFB: continuous time, 2 MΩ ∥ 50 fF sense, PMOS pair vs `vcmr`, diode into 1 of N load units per side;
  CM loop PM ≥ 60° (injection at the CMFB output), CM excursion during the step < 50 mV.

## 4. Bias block

Replica of one stage-1 half on `Vddb`: tail unit + input unit (gate at vcmr) set vbp (tail gate taken from the
input unit's drain), cascode unit + load unit set vbn (load gate from the cascode drain); vcn, vcp from diodes
fed by fixed multiples of $I_{bnp}$ (EE4520 fig. 6). Each line through $R_d$ to a big decoupling cap.
Balance the cascode gates so loads and input pair both keep ≥ 100 mV margin.
