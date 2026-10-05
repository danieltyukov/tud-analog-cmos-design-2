# 04 — Noise budget

Total output-referred differential noise must satisfy $\mathrm{SNR} \geq 66\,\mathrm{dB}$:

$$V_{n,tot}^2 = V_{n,amp}^2 + V_{n,kT/C}^2 \leq \left(\frac{V_{sig,rms,diff}}{\mathrm{SNR}_{lin}}\right)^2$$

LTSpice **does not** simulate $kT/C$ — compute it by hand and add manually (per `faq.txt`).

> The Bult SC-amplifier analysis (`08_power_prediction.md` §7) gives a **unified**
> form $\overline{V_{n,out,tot}^2}=\frac{kT}{C_{fb}}(\text{Gain}+1)(1+\mathrm{NEF}/\text{Gain})$
> that folds the term-10 sampling noise and the term-11 amplifier noise into one
> expression — a structural cross-check on the split below (prefactors stay
> topology-specific; derive your own).

## $kT/C$ contribution (sampled-and-held capacitive feedback)

For the discrete-time SC residue amplifier with feedback factor $\beta = C_{fb}/(C_{in}+C_{fb})$:

Per single-ended branch, sampled noise power referred to amplifier input:

$$V_{n,sample,in,se}^2 = \frac{kT}{C_{in}} \quad\text{(rough; refine if separate sampling cap)}$$

Amplifier-noise gain referred to output $= 1/\beta = 5$ ($= 1 + C_{in}/C_{fb}$; the **signal** gain is $C_{in}/C_{fb} = 4$ — see `01_specs_and_budget.md` §1). Differential combines two uncorrelated branches:

$$V_{n,kT/C,out,diff}^2 \approx 2 \cdot \left(\frac{1}{\beta}\right)^2 \cdot \frac{kT}{C_{in}}$$

> **Scope of the $kT/C$ term (TA clarification — `07_lecturer_clarifications.md` §4.1):**
> the reported effective $kT/C$ noise (Deliverable-1 term 10) includes **only**
> $C_{in}$, $C_{fb}$, and $C_{load}\,(=C_{in})$. If a switched-capacitor CMFB is
> used, the CMFB caps' $kT/C$ is **not** included in this term.

At $T = 300\,\mathrm{K}$, $kT = 4.14 \cdot 10^{-21}\,\mathrm{J}$:

| $C_{in}$ [pF] | $\sqrt{kT/C_{in}}$ [µV] | $V_{n,kT/C,out,diff}$ [µV$_{rms}$] |
|--------------:|------------------------:|------------------------------------:|
| 10            | 20.4                    | 144                                 |
| 20            | 14.4                    | 102                                 |
| 32            | 11.4                    | 81                                  |
| 64            | 8.05                    | 57                                  |

Target: keep $kT/C$ contribution $\lesssim 50\,\%$ of total budget so amplifier noise has equal share.

## Amplifier thermal noise (continuous, 10 kHz – 100 GHz)

Input-referred PSD of a single MOS:

$$S_{v,M} = \frac{4kT\,\gamma}{g_m}\quad [\mathrm{V}^2/\mathrm{Hz}],\qquad \gamma \approx \tfrac{2}{3}\text{ (long-}L\text{)}$$

For folded cascode the dominant noise sources are the **input pair** and the **active load tail mirrors** (Mn8 in EE4520 numbering):

$$S_{v,in,total} = \frac{8kT\,\gamma\,\big(1 + g_{m,load}/g_{m,in}\big)}{g_{m,in}}$$

Integrate against $|H(j\omega)|^2$ where $H$ is the noise-transfer to differential output:

$$V_{n,amp,out,diff}^2 \approx S_{v,in,total} \cdot \left(\frac{1}{\beta}\right)^2 \cdot \frac{\pi}{2} \cdot \mathrm{GBW}$$

(this is the classic noise-bandwidth $= \tfrac{\pi}{2} \cdot \mathrm{GBW}$ approximation for a single-pole loop).

## Flicker ($1/f$) noise — mandatory model, and sizing for the report

The simulation **must** use `log018.l`, which models flicker noise
(`NOIMOD = 1`, with `KF`/`AF`/`NOIA/NOIB/NOIC`); the old `logic018 no1of.l` had
**no** $1/f$ noise and is forbidden (see `models/README.md` and
`07_lecturer_clarifications.md` §1). With the flicker model active, the LTSpice
`.noise` integral from $10\,\mathrm{kHz}$ already captures the low-frequency
$1/f$ tail.

Input-referred flicker PSD of a MOS:

$$S_{v,1/f} = \frac{K_f}{C_{ox}\,W L}\cdot\frac{1}{f}\quad [\mathrm{V}^2/\mathrm{Hz}]$$

**Sizing knobs (graded — discuss in the report):**

- **Large gate area $W L$** on the dominant noise devices (input pair, and any
  device whose noise is referred to the input with unity-ish gain) directly
  lowers $1/f$ noise — increase $L$ and $W$ together once $g_m$ is set.
- **PMOS input devices** typically show lower $K_f$ than NMOS in this process —
  consider PMOS-input (or the $g_m$-reuse stage, `02_topology_choice.md`) if the
  $1/f$ corner eats into the budget.
- Keep the $1/f$ corner below the noise bandwidth so the thermal floor dominates
  the integrated number.

## Report items: dominant noise devices and NEF (Deliverable 9)

The short explanation must (`07_lecturer_clarifications.md` §5.8):

- **Name the devices that contribute significantly to the noise** (read off the
  LTSpice `.noise` per-device contributions — typically the input pair and the
  load/tail mirrors; cf. the thermal section above).
- **Estimate the NEF** (Noise Efficiency Factor):

$$\mathrm{NEF} = V_{n,in,rms}\sqrt{\frac{2\,I_{tot}}{\pi\,U_T\cdot 4kT\cdot \mathrm{BW}}}$$

  with $V_{n,in,rms}$ the input-referred integrated noise, $I_{tot}$ the total
  amplifier current, $U_T = kT/q$, and $\mathrm{BW}$ the noise bandwidth.

## Combined budget — FROZEN (Phase 1, 2026-06-28)

Computed + cross-checked in `phase1_budget.m` (figure
`../report/figures/phase1_noise_budget.png`). Chain:
$V_{out,se} \to V_{sig,rms,diff} \to V_{n,tot,max}$, then 50/50 split:

| Step | Value |
|---|---|
| Output swing | single-ended $\pm0.45\,\mathrm{V}$, differential $1.8\,\mathrm{V_{pp}}$ |
| $V_{sig,rms,diff}=V_{diff,amp}/\sqrt2$ | $0.636\,\mathrm{V}$ |
| $V_{n,tot,max}=V_{sig,rms}/\mathrm{SNR}_{lin}$ ($\mathrm{SNR}_{lin}=1995$) | $319\,\mu V_{rms}$ |
| $V_{n,kT/C,target}=V_{n,amp,target}=V_{n,tot,max}/\sqrt2$ (50 %) | $225\,\mu V_{rms}$ each |
| $C_{in,min}$ from $V_{n,kT/C,target}$ via $2(1/\beta)^2kT/C_{in}$ | $4.07\,\mathrm{pF}$ |
| **Frozen $C_{in}=5\,\mathrm{pF}$** ($C_{fb}=1.25$, $C_{load}=5$) | $\Rightarrow V_{n,kT/C}=204\,\mu V_{rms}$ (margin) |
| Bult unified cross-check $\sqrt{2(kT/C_{fb})(\mathrm{Gain}+1)}$ | $182\,\mu V_{rms}$ (same order) |
| Remaining amplifier-noise target $V_{n,amp}$ | $\le 225\,\mu V_{rms}$ (sets $g_{m,in}$, Phase 2) |

$$V_{n,kT/C,target} = \frac{V_{n,tot,max}}{\sqrt{2}}\quad(\text{50\% split}) \;\Rightarrow\; C_{in}=\frac{2(1/\beta)^2\,kT}{V_{n,kT/C,target}^2}$$

Solved: $C_{in}=5\,\mathrm{pF}$ (rounded up from $4.07\,\mathrm{pF}$ for margin).
$V_{n,amp,target}=225\,\mu V_{rms}$ is the budget the **amplifier thermal + $1/f$
noise** (sized in Phase 2 via $g_{m,in}$, coupled to GBW $\approx242\,\mathrm{MHz}$
from `01` §0/§3) must come in under — verified by the `.noise` sim in Phase 5.

## Deliverable-1 terms 10 / 11 / 12 — what each number is

> **Peer-sourced clarification (course group chat — not an official TA
> announcement; verify against your own topology).** These three table rows are
> the most-confused in the course; they are **distinct**:

- **Term 11 — total integrated *amplifier* noise:** the LTSpice `.noise` result,
  `integ V(onoise)` from $10\,\mathrm{kHz}$ to $100\,\mathrm{GHz}$ on the
  **differential** output. This is $V_{n,amp,rms}$ (continuous thermal + $1/f$).
- **Term 10 — total effective $kT/C$ noise at output:** hand-computed sampled
  noise from $C_{in}$, $C_{fb}$, $C_{load}\,(=C_{in})$ only (LTSpice does not
  simulate it). This is $V_{n,kT/C,rms}$.
- **Term 12 — total integrated noise:** the **combination**,
  $V_{n,tot} = \sqrt{V_{n,amp}^2 + V_{n,kT/C}^2}$ — because the residue amp is
  **sampled**, the total handed to the next ADC stage includes *both* the
  amplification noise *and* the switching ($kT/C$) noise.

SNR uses the **total**, with $V_{sig,rms} = V_{out,max}/\sqrt{2}$ (e.g.
$1.6/\sqrt 2 = 1.131\,\mathrm{V}$). A peer's working `.meas` folds $kT/C$ in
directly:

```spice
.measure noise NOISERMS integ V(onoise) from 10k to 100G
.meas NOISE SNRlin PARAM 1.13137/sqrt(NOISERMS**2 + 10*1.380649e-23*300/Cfb)
.meas NOISE SNRdB  PARAM 20*log10(SNRlin)
```

The `10*1.380649e-23*300/Cfb` is **that design's** $kT/C$ accounting
($10\,kT/C_{fb}$) — the factor is topology-specific; derive your own from the
$kT/C$ section above (this repo's form is $2(1/\beta)^2\,kT/C_{in}$) rather than
copying the `10`. Equivalently, add the hand-computed term-10 number to the
term-11 number per the combination above.

## Phase-5 noise closure (2026-06-28) — measured, PASS

`.noise V(Voutp,Voutn)` on the closed-loop current-reuse amp
(`design/current-reuse/folded_cascode_cr_noise.asc`, `log018.l` 1/f from 10 kHz), integrated
10 kHz–100 GHz:

| term | quantity | value |
|---|---|---|
| 11 | $V_{n,amp}$ (simulated, amp + boosters) | **209.5 µV** (≤ 225 budget) |
| 10 | $V_{n,kT/C}=\sqrt{2(1/\beta)^2 kT/C_{in}}$, $C_{in}=5$ pF | **203.5 µV** (hand) |
| 12 | $V_{n,tot}=\sqrt{V_{n,amp}^2+V_{n,kT/C}^2}$ | **292 µV** |

$\mathrm{SNR}=20\log_{10}(0.636/292\,\mu\mathrm{V})=\mathbf{66.8\,dB}\ge 66$ ✓. The current-reuse
high input $g_m$ keeps the amplifier-noise share at ≈ the $kT/C$ level (the targeted 50/50 split).
Dominant noise devices: the input pair (`Mn3.2`/`Mp1.2`) and the NMOS sinks (`Mn5.2`/`Mn7.2`).
Figure `../report/figures/cr_d5_noise.png`. (The ideal sim-aid CMFB helper is noiseless → the
switched-cap CMFB noise is correctly excluded, consistent with the TA's term-10 $kT/C$ scope.)

- [x] `.noise` integrated 10 kHz–100 GHz on **differential output** → 209.5 µV
- [x] Add $kT/C$ analytically → 204 µV
- [x] $\mathrm{SNR}=66.8$ dB ≥ 66 ✓
