# 03 — Transistor sizing calculations

Use the $g_m / I_D$ methodology (typical at 0.18 µm). Pick $(g_m/I_D)$ per device based on the role:

| Role                    | $(g_m/I_D)$ typical [V$^{-1}$] | Region                             |
|-------------------------|-------------------------------:|------------------------------------|
| Input pair (noise+gain) | 12–18                          | weak-to-moderate inversion         |
| Cascode devices         | 8–12                           | moderate inversion                 |
| Tail / mirror sources   | 6–10                           | strong inversion (headroom + matching) |

## Core formulas (saturation, square-law approximation — refine with $g_m/I_D$ LUT later)

$$g_m = \sqrt{2\,\mu\,C_{ox}\,(W/L)\,I_D}$$

$$g_{ds} \approx I_D \cdot \lambda \quad\Longrightarrow\quad A_{intrinsic} = \frac{g_m}{g_{ds}}$$

For a folded cascode the output resistance is the parallel of the NMOS and PMOS cascode legs:

$$R_{out} \approx \big(g_{m,\mathrm{Mcas_n}} \cdot r_{o,\mathrm{Mcas_n}} \cdot r_{o,\mathrm{Mn}}\big)\,\big\|\,\big(g_{m,\mathrm{Mcas_p}} \cdot r_{o,\mathrm{Mcas_p}} \cdot r_{o,\mathrm{Mp}}\big)$$

$$A_0 = g_{m,in} \cdot R_{out}$$

## GBW and dominant pole

$C_{load,total} \approx C_{load} + C_{fb}(1-\beta) + \text{parasitics} \approx C_{in}$ (PDF requires $C_{load} = C_{in}$).

$$\mathrm{GBW} \approx \frac{g_{m,in}}{2\pi \cdot C_{load,eff}}$$

Required GBW from §01 ≈ **242 MHz** ($=f_u/\beta$, $\beta = 1/5$) → fixes $g_{m,in}$.

$$g_{m,in,required} = 2\pi \cdot 242 \cdot 10^6 \cdot C_{load,eff}$$

Plug in $C_{in}$ (decided in §04 from noise budget) to get the absolute $g_{m,in}$ number, then divide by chosen $(g_m/I_D)_{in}$ to get $I_{D,in}$.

## Branch-current rule (PDF "common mistakes")

For folded cascode (Fig. 8 in project PDF):

$$I_{Mn4} + I_{Mn5} \;\geq\; I_{Mn10} + I_{Mn11} \;(= I_{Mn8})$$

Otherwise the differential pair starves the PMOS cascodes when input swings.

## Phase-2 sized core — RESULT (2026-06-28) ⭐

Sized in `design/core-amp/folded_cascode_baseline.asc` (folded cascode, **ideal**
CMFB `E1` + **ideal** gain-boost `E2–E7`, `Aadd=100`), verified by `.op`
(`read_op_point` + device table) and the AC bench
`simulations/ac/loaded_ac_baseline.asc` (loaded $C_L=5\,\mathrm{pF}$). All devices
share the unit cell $W/L = 1\,\mu\mathrm{m}/0.18\,\mu\mathrm{m}$; size set by the
integer multiplier $M$.

**Frozen `.param` (both core + AC bench):**
`W=1u L=0.18u Mp=75 Mn=22 Rn=5.8 Rp=7.5` · `Cin=5p Cfb={Cin/4} Cload={Cin} Ibm=350u` ·
`Mn34=380 Mn12=76 Mn56=11 Mn78=11 Mp13=165 Mp24=38`. (`Mp`/`Mn` = bias-reference
multipliers that set the current-source inversion level; `Ibm`/`Rn`/`Rp` set the bias
branch currents; the opamp branch currents are mirror ratios $I=I_{bm}\,M_{\text{branch}}/M_{\text{ref}}$.)

| Device (×2)   | Role          | $W/L$       | $M$ | $I_D$    | $g_m$     | $g_m/I_D$ | $V_{DS}$  | $V_{DS,sat}$ | margin | $r_o$ |
|---------------|---------------|-------------|----:|----------|-----------|----------:|-----------|--------------|-------:|-------|
| Mn3.2 / Mn4.2 | NMOS input    | 1u/0.18u    | 380 | 597 µA   | 12.2 mS   | 20.4      | 1.21 V    | 53 mV        | 1157 mV| 3.94 kΩ |
| Mp1.2 / Mp3.2 | PMOS source   | 1u/0.18u    | 165 | 773 µA   | 7.84 mS   | 10.1      | −233 mV   | 148 mV       | 85 mV  | 1.77 kΩ |
| Mp2.2 / Mp4.2 | PMOS cascode  | 1u/0.18u    |  38 | 177 µA   | 1.95 mS   | 11.0      | −667 mV   | 143 mV       | 524 mV | 21.8 kΩ |
| Mn5.2 / Mn6.2 | NMOS cascode  | 1u/0.18u    |  11 | 177 µA   | 1.97 mS   | 11.1      | 179 mV\*  | 113 mV       | 66 mV  | 4.74 kΩ |
| Mn7.2 / Mn8.2 | NMOS sink     | 1u/0.18u    |  11 | 177 µA   | 1.97 mS   | 11.1      | 179 mV\*  | 113 mV       | 66 mV  | 4.74 kΩ |
| Mn1.2         | NMOS tail src | 1u/0.18u    |  76 | 1.19 mA  | 13.2 mS   | 11.1      | 164 mV    | 112 mV       | 52 mV  | 0.60 kΩ |
| Mn2.2         | NMOS tail casc| 1u/0.18u    |  76 | 1.19 mA  | 13.6 mS   | 11.4      | 193 mV    | 112 mV       | 81 mV  | 0.78 kΩ |

\* **Wide-swing bias:** within each cascode/sink pair, the bottom device of a leg
sits at $V_{DS}\approx0.18\,\mathrm{V}$ (margin 66 mV) and its partner at
$V_{DS}\approx0.72\,\mathrm{V}$ (margin $\approx620\,\mathrm{mV}$); the 0.18 V value
is the binding one. This is the intended wide-swing split (cascode source held near
the sink's $V_{DS,sat}$) that buys the output swing for the $\pm0.45\,\mathrm{V}$ spec.

**Verified performance (ideal CMFB + ideal gain-boost in place):**

| Quantity | Target | Achieved | Where |
|---|---|---|---|
| $A_0$ (open-loop, diff) | $\ge 78$ dB (here $\sim$90 expected) | **93.9 dB** | AC bench, $A=V_{outp}-V_{outn}$ |
| GBW (amplifier, $=f_u/\beta$) | $\approx 242$ MHz | **264 MHz** | AC bench |
| loop crossover $f_u$ ($|A|=1/\beta=5$) | $\ge 48.4$ MHz | **52.9 MHz** | AC bench |
| $\tau_{cl}=1/2\pi f_u$ | $3.0$ ns ($<3.29$ ceiling) | **3.01 ns** | AC bench |
| Phase margin | $\ge 60°$ | **89°** | AC bench |
| $g_{m,in}$ | $\approx 10$ mS | **12.2 mS** | core `.op` |
| all devices saturated | yes | **yes** (min margin 52 mV, tail) | core `.op` |
| branch rule $I_{top}\ge I_{in}$ | yes | **773 µA ≥ 597 µA** (37 % fold) | core `.op` |
| $I(V_{dd})$ (amps only) | $<1.7$ mA | **1.55 mA** | core `.op`, `I(V2)` |
| Power | $<3$ mW | **2.78 mW** | $=I(V_{dd})\cdot1.8$ |

> **Saturation-margin note.** All 17 transistors are in saturation. The signal-/gain-
> defining devices (input pair, both cascodes) keep $\ge 520\,\mathrm{mV}$ margin. The
> current-source / tail / wide-swing-sink devices sit at 52–85 mV — *intrinsic* to a
> wide-swing folded cascode on a 1.8 V rail (verified: lowering current-source density
> does **not** improve them, since the wide-swing reference tracks $V_{DS,sat}$). These
> are fixed-$V_{DS}$ CM/bias devices, not in the signal swing path. A0 reads ~94 dB only
> because the ideal boost is in place — the genuine 78 dB-from-real-boosters test is
> Phase 4.

### Target-vs-achieved reconciliation (no unexplained overshoot)

- **GBW 264 MHz vs "242 MHz".** 242 MHz is the **floor**, not the target: it is
  $\mathrm{GBW}=f_u/\beta$ at the settling-time *ceiling* $\tau=3.29\,\mathrm{ns}$
  ($f_u=1/2\pi\tau=48.4\,\mathrm{MHz}$). The **design point** is $\tau=3.0\,\mathrm{ns}$,
  which needs $f_u=53.1\,\mathrm{MHz}\Rightarrow\mathrm{GBW}=265\,\mathrm{MHz}$. The
  achieved **264 MHz** sits exactly on the design point — not fat.
- **$g_{m,in}$ 12.2 mS vs "10 mS".** Phase-1's 10 mS assumed an *estimated*
  $C_{L,eff}=6\,\mathrm{pF}$. The realised value from sim is
  $C_{L,eff}=g_{m,in}/2\pi\,\mathrm{GBW}=12.2\,\mathrm{mS}/(2\pi\cdot264\,\mathrm{MHz})
  =\mathbf{7.34\,pF}$ ($C_L=5\,\mathrm{pF}$ + feedback $C_{fb}(1-\beta)$ + cascode/parasitic
  loading). At 7.34 pF, $\tau=3.0\,\mathrm{ns}$ **requires** $g_m=12.2\,\mathrm{mS}$;
  using 10 mS gives $\mathrm{GBW}=217\,\mathrm{MHz},\ f_u=43.4\,\mathrm{MHz},\
  \tau=3.7\,\mathrm{ns}>3.29$ → **fails the 25 ns / 66 dB settle**. So $g_{m,in}=12.2\,\mathrm{mS}$
  is **settling-bound, not over-sized**. (Phase-1 $C_{L,eff}$ estimate corrected $6\to7.34\,\mathrm{pF}$ in `01` §0.)

### FoM pre-closure indicator (the grading metric)

$$\mathrm{FoM}_{lin}=\frac{2\pi P\tau}{\mathrm{SNR}_{lin}^2}
=\frac{2\pi(2.78\,\mathrm{mW})(3.01\,\mathrm{ns})}{1995^2}=1.32\times10^{-17}\,\mathrm{J}
\;\Rightarrow\;\mathrm{FoM}_{dB}=\mathbf{168.8\,dB}.$$

**Below** the 170 dB pass line and the EE4520 baseline (175.2 dB). This is a
**pre-closure** number (Phase-2 power + AC-proxy $\tau$ only) — FoM is a Phase-5/6
closure metric needing final power, transient $\tau$, and SNR. FoM $\propto P$, so
**current-reuse (Phase 5) is now mandatory** to drive 2.78 mW → ~0.3 mW and clear
170 dB (details in `00_spec_table.md`).

Use **integer M only** (PDF + faq.txt). Tune $W$ of the unit device for fine
$W_{\text{eff}}$ control. Figures: open-loop Bode `../report/figures/phase2_openloop_bode.png`,
sized schematic `../report/figures/folded_cascode_baseline.{svg,png}`.
