# 04 — Noise budget

Total output-referred differential noise must satisfy $\mathrm{SNR} \geq 66\,\mathrm{dB}$:

$$V_{n,tot}^2 = V_{n,amp}^2 + V_{n,kT/C}^2 \leq \left(\frac{V_{sig,rms,diff}}{\mathrm{SNR}_{lin}}\right)^2$$

LTSpice **does not** simulate $kT/C$ — compute it by hand and add manually (per `faq.txt`).

## $kT/C$ contribution (sampled-and-held capacitive feedback)

For the discrete-time SC residue amplifier with feedback factor $\beta = C_{fb}/(C_{in}+C_{fb})$:

Per single-ended branch, sampled noise power referred to amplifier input:

$$V_{n,sample,in,se}^2 = \frac{kT}{C_{in}} \quad\text{(rough; refine if separate sampling cap)}$$

Closed-loop gain referred to output $\approx 1/\beta = 4$. Differential combines two uncorrelated branches:

$$V_{n,kT/C,out,diff}^2 \approx 2 \cdot \left(\frac{1}{\beta}\right)^2 \cdot \frac{kT}{C_{in}}$$

> **Scope of the $kT/C$ term (TA clarification — `07_lecturer_clarifications.md` §4.1):**
> the reported effective $kT/C$ noise (Deliverable-1 term 10) includes **only**
> $C_{in}$, $C_{fb}$, and $C_{load}\,(=C_{in})$. If a switched-capacitor CMFB is
> used, the CMFB caps' $kT/C$ is **not** included in this term.

At $T = 300\,\mathrm{K}$, $kT = 4.14 \cdot 10^{-21}\,\mathrm{J}$:

| $C_{in}$ [pF] | $\sqrt{kT/C_{in}}$ [µV] | $V_{n,kT/C,out,diff}$ [µV$_{rms}$] |
|--------------:|------------------------:|------------------------------------:|
| 10            | 20.4                    | 115                                 |
| 20            | 14.4                    | 81                                  |
| 32            | 11.4                    | 65                                  |
| 64            | 8.05                    | 46                                  |

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

## Combined budget (template)

Pick $V_{out,se} \to V_{sig,rms,diff} \to V_{n,tot,max}$, then split:

$$V_{n,kT/C,target} = \frac{V_{n,tot,max}}{\sqrt{2}} \quad\text{(50\% power split)}$$

$$V_{n,amp,target} = \frac{V_{n,tot,max}}{\sqrt{2}}$$

Solve $V_{n,kT/C,target} \to C_{in}$.
Solve $V_{n,amp,target} \to g_{m,in}$ (couples to GBW from §03).

## Acceptance checks (post-simulation)

- [ ] LTSpice `.noise` integrated 10 kHz–100 GHz on **differential output** (not single-ended)
- [ ] Add $kT/C$ analytically
- [ ] Compute $\mathrm{SNR} = 20 \log_{10}(V_{sig,rms,diff} / V_{n,tot,rms})$
- [ ] $\mathrm{SNR} \geq 66\,\mathrm{dB}$
