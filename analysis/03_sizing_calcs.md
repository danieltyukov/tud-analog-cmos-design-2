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

## Sizing template (fill during design)

| Device  | Role            | $(g_m/I_D)$ tgt | $I_D$ | $g_m$ | $W/L$ | $M$ | $V_{GS}$ | $V_{DS}$ | $r_o$ |
|---------|-----------------|----------------:|------:|------:|-------|-----|----------|----------|-------|
| Mn4/5   | input pair      |                 |       |       |       |     |          |          |       |
| Mn10/11 | NMOS cascode    |                 |       |       |       |     |          |          |       |
| Mp...   | PMOS source     |                 |       |       |       |     |          |          |       |
| Mp...   | PMOS cascode    |                 |       |       |       |     |          |          |       |
| Mn8     | tail            |                 |       |       |       |     |          |          |       |

Use **integer M only** (PDF + faq.txt). Tune $W$ of unit device for fine $W_{eff}$ control.
