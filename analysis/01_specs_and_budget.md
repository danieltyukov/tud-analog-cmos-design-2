# 01 — Spec translation & top-level budget

Goal: turn the PDF requirements into design-time numbers (gain, $\beta$, settling $\tau$, noise, power) before sizing transistors.

## 1. Feedback factor $\beta$

$$\beta = \frac{C_{fb}}{C_{in} + C_{fb}}$$

The residue gain is $2^n = 4$ ($n = 2$ bits/stage), and at low frequency the closed-loop gain $\approx 1/\beta$. So:

$$\frac{1}{\beta} = 4 \quad\Longrightarrow\quad \frac{C_{in}}{C_{fb}} = 3 \quad\Longrightarrow\quad \beta = 0.25$$

This sets the *ratio* $C_{in} : C_{fb} = 3 : 1$. Absolute values come from the noise budget (§4).

## 2. Required open-loop DC gain $A_0$

For the loop setting $A\beta = 66\,\mathrm{dB}$ and $\beta = 0.25$ ($1/\beta = 12\,\mathrm{dB}$):

$$A_0 \geq 66\,\mathrm{dB} + 12\,\mathrm{dB} = 78\,\mathrm{dB} \quad\text{(matches PDF spec)}$$

## 3. Required settling time-constant $\tau$

The closed-loop step response decays as $e^{-t/\tau_{cl}}$. Reaching $A\beta = 66\,\mathrm{dB}$ of accuracy means relative error $\varepsilon \leq 10^{-66/20} \approx 5 \cdot 10^{-4}$.

$$e^{-25\,\mathrm{ns}\,/\,\tau_{cl}} \leq 10^{-66/20}$$

$$\tau_{cl} \leq \frac{25\,\mathrm{ns}}{\ln(10^{66/20})} = \frac{25}{7.60} \approx 3.29\,\mathrm{ns}$$

(The PDF example shows $\tau = 2.5\,\mathrm{ns}$, leaving a small margin.)

The loop unity-gain bandwidth must therefore satisfy:

$$\omega_u \geq \frac{1}{\tau_{cl}} \approx 304\,\mathrm{Mrad/s} \quad\Longrightarrow\quad f_u \geq 48.4\,\mathrm{MHz}$$

And the **amplifier** GBW (open-loop) is:

$$\mathrm{GBW} \approx \frac{\omega_u}{\beta} = 4 \cdot 48.4 \approx 194\,\mathrm{MHz}$$

## 4. Noise budget (output-referred, differential)

Choose output single-ended swing $V_{out,se}$. Differential peak-peak $= 2\,V_{out,se}$. RMS of full-swing diff sinusoid:

$$V_{sig,rms,diff} = \frac{2\,V_{out,se}}{2\sqrt{2}} = \frac{V_{out,se}}{\sqrt{2}}$$

For $\mathrm{SNR} = 66\,\mathrm{dB}$ ($\mathrm{SNR}_{lin} = 10^{66/20} \approx 1995$):

$$V_{n,tot,rms} \leq \frac{V_{sig,rms,diff}}{\mathrm{SNR}_{lin}}$$

Example ($V_{out,se} = 1.0\,\mathrm{V}$): $V_{sig,rms,diff} = 0.707\,\mathrm{V} \Rightarrow V_{n,tot} \leq \mathbf{354\,\mu V_{rms}}$ total.

This budget splits into:

$$V_{n,tot}^2 = V_{n,amp}^2(\text{integrated 10 kHz–100 GHz}) + V_{n,kT/C}^2$$

Where the **$kT/C$ term** for sampling at the input (per side, single-ended-equivalent referred to output via gain $\approx 1/\beta$):

$$V_{n,kT/C,\text{in,se}}^2 = \frac{kT}{C_{in}} \quad\text{(rough; refine if separate sampling cap)}$$

$$V_{n,kT/C,\text{out,diff}}^2 \approx 2 \cdot \left(\frac{1}{\beta}\right)^2 \cdot \frac{kT}{C_{in}}$$

→ Larger $C_{in}$ lowers $kT/C$ noise but loads the amplifier and hurts speed/power. Solve for $C_{in}$ such that $kT/C$ consumes $< \tfrac{1}{2}$ of total noise budget, then size amplifier transistor noise to meet the remaining half.

## 5. Power-budget feel

Hard ceiling $P_{max} = 3\,\mathrm{mW}$ at $V_{dd} = 1.8\,\mathrm{V} \Rightarrow I_{dd,max} = 1.67\,\mathrm{mA}$.
Best designs drop below $0.3\,\mathrm{mW}$. Use this as the optimization target after the spec is met.

## 6. Reused vs. new building blocks

| Block | Source | Status |
|---|---|---|
| Biasing block (3-current cascode mirror) | EE4520 hw1 → `design/biasing/biasing_block.asc` | reuse, decouple bias lines with $C_{big}$ |
| Process model `log018.l` | EE4520 → `models/log018.l` | reuse |
| Folded-cascode core (skeleton) | EE4520 hw2 → `design/core-amp/folded_cascode_baseline.asc` | adapt — replace ideal CMFB / ideal gain-boost |
| CMFB | EE4520 used **ideal** | **must redesign** in transistors |
| Gain-boosters (NMOS, PMOS) | EE4520 used **ideal** | **must redesign** if used |

## To do before sizing

- [ ] Pick $V_{out,se}$ (e.g., $\pm 0.9\,\mathrm{V}$ around $0.9\,\mathrm{V}$ CM)
- [ ] Compute $V_{sig,rms,diff}$ and the noise budget
- [ ] Choose initial $C_{in} / C_{fb}$ satisfying ratio $3{:}1$ and noise budget
- [ ] Cross-check $C_{load} = C_{in}$ fits in the loaded GBW spec
