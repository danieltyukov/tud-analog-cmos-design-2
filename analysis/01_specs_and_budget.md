# 01 — Spec translation & top-level budget

Goal: turn the PDF requirements into design-time numbers (gain, $\beta$, settling $\tau$, noise, power) before sizing transistors.

## 0. Phase-1 FROZEN values (2026-06-28) ⭐

All numbers below are computed + cross-checked in **`phase1_budget.m`** (run it to
regenerate; results in `phase1_results.txt`, figures in
`../report/figures/phase1_*.png`). These are **frozen** inputs to Phase 2 sizing —
the architecture and $C_{in}{:}C_{fb}=4{:}1$ ratio were already settled (§1, `02`).

| Quantity | Frozen value | Source / note |
|---|---|---|
| $V_{dd}$, output CM | $1.8\,\mathrm{V}$, $0.9\,\mathrm{V}$ | single rail (`07` §5.1), mid-rail |
| Output swing (single-ended) | $\pm 0.45\,\mathrm{V}$ ($0.45$–$1.35\,\mathrm{V}$) | the one Phase-1 DOF; telescopic-headroom-safe, Ryu-backed |
| Output swing (differential) | $1.8\,\mathrm{V_{pp}}$ ($V_{out,step}=0.9\,\mathrm{V}$) | $=2\times$ se; row 14 |
| Input step (row 13) | $V_{out}/4 = 0.225\,\mathrm{V}$ | residue gain $=4$ |
| $V_{sig,rms,diff}$ | $0.636\,\mathrm{V}$ | $=V_{diff,amp}/\sqrt2$ |
| $\eta_{vol}=V_{sig,pp,se}/V_{dd}$ | $0.50$ | (`08` first-cut used optimistic $0.7$) |
| $V_{n,tot}$ ceiling | $319\,\mu V_{rms}$ | $=V_{sig,rms}/\mathrm{SNR}_{lin}$, $\mathrm{SNR}_{lin}=1995$ |
| Noise split (50/50) | $225\,\mu V_{rms}$ each | kT/C share + amplifier share |
| **$C_{in}$** | **$5\,\mathrm{pF}$** | $\ge C_{in,min}=4.07\,\mathrm{pF}$; gives $kT/C=204\,\mu V$ (margin) |
| **$C_{fb}$** | **$1.25\,\mathrm{pF}$** | $=C_{in}/4$ |
| **$C_{load}$** | **$5\,\mathrm{pF}$** | $=C_{in}$ (row 17) |
| $\tau_{cl}$ ceiling / design | $3.29 / 3.0\,\mathrm{ns}$ | $N_{settle}=\ln(1995)=7.60$; 3.0 ns leaves slew/parasitic margin |
| loop $f_u$ / amp GBW | $48.4 / 242\,\mathrm{MHz}$ **(floor)** | $\mathrm{GBW}=f_u/\beta$; 242 is the floor at $\tau=3.29$ ceiling — **design point** is $\tau=3.0\Rightarrow f_u=53.1,\ \mathrm{GBW}\approx265$ MHz (Ph-2 achieved 264) |
| $g_{m,in}$ first-cut | $\approx 10\,\mathrm{mS}$ → **12.2 mS** (Ph-2) | $=2\pi\,\mathrm{GBW}\,C_{L,eff}$; Ph-1 used estimated $C_{L,eff}=6\,\mathrm{pF}$, **sim-realised $C_{L,eff}=7.34\,\mathrm{pF}$** ⇒ $\tau=3.0$ ns needs $g_m=12.2$ mS (settling-bound; 10 mS → $\tau\approx3.7$ ns, fails) |
| Input-stage current | $0.42$–$0.67\,\mathrm{mA}$ (reuse) | $g_m/I_D=15$–$24$; $0.83$–$1.33\,\mathrm{mA}$ without reuse |
| $P_{system}$ floor | $0.169\,\mathrm{mW}$ | implementation-independent (`08` §2) |
| Predicted $P$ (top-down / bottom-up) | $0.30 / 1.27\,\mathrm{mW}$ | both $<3\,\mathrm{mW}$; optimise toward floor in Phase 5 |
| Predicted FoM (floor / TD / BU) | $180.6 / 178.2 / 172.2\,\mathrm{dB}$ | all $>170\,\mathrm{dB}$ pass |

> **Reconciling the two power estimates.** Top-down (Bult, `08`) assumes the
> efficiency knobs are *realised* ($\eta_{cur}=0.5$ etc.) → $0.30\,\mathrm{mW}$.
> Bottom-up uses the rigorous loop $g_m=C_{L,eff}/(\beta\tau)=10\,\mathrm{mS}$ at
> moderate WI → $1.27\,\mathrm{mW}$. The honest first-cut sits between; **Phase 5
> power optimisation** (deeper WI, current reuse, clean loads, swing) drives it
> toward the top-down number. Both pass the $3\,\mathrm{mW}$ ceiling with room.

## 1. Closed-loop gain $G_{cl}$ and feedback factor $\beta$

**Final decision (2026-06-28): $C_{in} : C_{fb} = 4 : 1$.** Driven by the defining
spec — the **residue (closed-loop) gain** is $2^n = 4$ ($n = 2$ bits/stage), and
for this charge-transfer SC amplifier that gain *is* the capacitor ratio:

$$G_{cl} = \frac{V_{out}}{V_{in}} = \frac{C_{in}}{C_{fb}} = 4 \qquad(\text{input step} = V_{out}/4,\ \text{row 13}).$$

The **feedback factor** (the capacitive divider — sets loop stability + noise gain) is then

$$\beta = \frac{C_{fb}}{C_{in}+C_{fb}} = \frac{1}{5}\qquad\Rightarrow\qquad \frac{1}{\beta} = 1 + \frac{C_{in}}{C_{fb}} = 5\ \ (=\text{amplifier-noise gain}).$$

> **Two distinct "gains" — do not conflate them:**
> - **Signal gain $G_{cl} = C_{in}/C_{fb} = 4$** — sets $V_{out}/V_{in}$, the input
>   step ($V_{out}/4$), and the **Deliverable-4 plot "$1/\beta$" gap**
>   ($20\log_{10}4 = 12\,\mathrm{dB}$, so $A_{settle} = A\beta_{settle} + 12 = 78\,\mathrm{dB}$).
>   The plot labels that gap "$1/\beta$" loosely — it is really $G_{cl}$.
> - **Feedback factor $\beta = 1/5$** — the true loop $\beta$; the **noise gain**
>   ($1/\beta = 5$) and the loop time-constant (§3) use this.
>
> **Why 4:1, not 3:1 (resolved):** residue gain $= C_{in}/C_{fb} = 4$ is the
> unambiguous defining requirement (input step $= V_{out}/4$), and matches EE4520
> (gain $= C_{in}/C_{fb}$; its $A$–$A\beta$ gap was $20\log_{10}(C_{in}/C_{fb})$).
> The earlier "$3:1$" came from mis-reading the 12 dB gap as
> $20\log_{10}((C_{in}+C_{fb})/C_{fb})$. `08`'s $(\text{Gain}+1)$ noise factor
> already uses $1/\beta = 5$.

> **Ideal vs. actual $\beta$ (TA clarification — `07_lecturer_clarifications.md` §3):**
> the *realised* $\beta$ extracted from simulation is usually slightly **higher**
> than the ideal $C_{fb}/(C_{in}+C_{fb})$, because the input-pair parasitics
> ($C_{gs}$, $C_{gd}$) add to the capacitive divider at the virtual-ground node.
> If your extracted $\beta$ comes out **lower** than ideal, the formula or design
> has a bug. This effect must be **explained in the report**, and the Deliverable-4
> plot shows $A$ and $A\beta$ together with $A\beta$ starting from exactly 0 dB.

## 2. Required open-loop DC gain $A_0$

The amplifier curve sits $20\log_{10}G_{cl} = 20\log_{10}4 = 12\,\mathrm{dB}$ above the loop curve, so for $A\beta_{settle} = 66\,\mathrm{dB}$:

$$A_0 \geq 66 + 12 = 78\,\mathrm{dB}\quad\text{(matches the PDF }A_{settle} > 78\text{ spec).}$$

(For the loop to reach $66\,\mathrm{dB}$ static accuracy with $\beta = 1/5$, the DC loop gain $A_0\beta \ge 10^{66/20}$ wants $A_0 \gtrsim 80\,\mathrm{dB}$ — design with that margin.)

## 3. Required settling time-constant $\tau$

The closed-loop step response decays as $e^{-t/\tau_{cl}}$. Reaching $A\beta = 66\,\mathrm{dB}$ of accuracy means relative error $\varepsilon \leq 10^{-66/20} \approx 5 \cdot 10^{-4}$.

$$e^{-25\,\mathrm{ns}\,/\,\tau_{cl}} \leq 10^{-66/20}$$

$$\tau_{cl} \leq \frac{25\,\mathrm{ns}}{\ln(10^{66/20})} = \frac{25}{7.60} \approx 3.29\,\mathrm{ns}$$

(The PDF example shows $\tau = 2.5\,\mathrm{ns}$, leaving a small margin.)

The loop unity-gain bandwidth must therefore satisfy:

$$\omega_u \geq \frac{1}{\tau_{cl}} \approx 304\,\mathrm{Mrad/s} \quad\Longrightarrow\quad f_u \geq 48.4\,\mathrm{MHz}$$

And the **amplifier** GBW (open-loop) is:

$$\mathrm{GBW} \approx \frac{f_u}{\beta} = 5 \cdot 48.4 \approx 242\,\mathrm{MHz}\qquad(\beta = 1/5)$$

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

> **Single supply rail (TA clarification — `07_lecturer_clarifications.md` §5.1):**
> the **entire** amplifier — core, gain boosters, second stage, **and the CMFB
> circuit** — runs from the **same** $V_{DD} = 1.8\,\mathrm{V}$. Separate/boosted
> rails per block are **not allowed**.
>
> **Don't over-design (§5.2):** meet $\mathrm{SNR} = 66\,\mathrm{dB}$ and
> $T_{settle} = 25\,\mathrm{ns}$ with margin, then optimise for **low power** —
> power is the figure to minimise, not gain or speed headroom.

## 6. Reused vs. new building blocks

| Block | Source | Status |
|---|---|---|
| Biasing block (3-current cascode mirror) | EE4520 hw1 → `design/biasing/biasing_block.asc` | reuse, decouple bias lines with $C_{big}$ |
| Process model `log018.l` (BSIM3, **with $1/f$ noise**) | lecturer-provided → `models/log018.l` | **required**; active schematics switched off the no-$1/f$ `logic018 no1of.l` — see `models/README.md` |
| Folded-cascode core (skeleton) | EE4520 hw2 → `design/core-amp/folded_cascode_baseline.asc` | adapt — replace ideal CMFB / ideal gain-boost |
| CMFB | EE4520 used **ideal** | **must redesign** in transistors |
| Gain-boosters (NMOS, PMOS) | EE4520 used **ideal** | **must redesign** if used |

## To do before sizing — DONE (Phase 1, see §0)

- [x] Pick $V_{out,se}$ → $\pm 0.45\,\mathrm{V}$ around $0.9\,\mathrm{V}$ CM (§0)
- [x] Compute $V_{sig,rms,diff}=0.636\,\mathrm{V}$ and the noise budget ($319\,\mu V$ ceiling, 50/50 split)
- [x] Choose $C_{in}/C_{fb}=5/1.25\,\mathrm{pF}$ satisfying ratio $4{:}1$ and noise budget
- [x] Cross-check $C_{load}=C_{in}=5\,\mathrm{pF}$; $g_{m,in}\approx10\,\mathrm{mS}$ gives $\tau_{cl}=3\,\mathrm{ns}<3.29\,\mathrm{ns}$ at GBW $242\,\mathrm{MHz}$
