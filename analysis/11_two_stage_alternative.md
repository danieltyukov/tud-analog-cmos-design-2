# 11 — Two-stage alternative (considered, and why we didn't)

The two-stage architecture we **evaluated and rejected**, with the implementation
we would have used. Kept for the **report's design-process / short explanation**
(showing we weighed the alternative the TAs note "quite a few" chose) and as the
documented **Option-C fallback** (`02_topology_choice.md`).

## Context

The TA announcement (21 Jun 2026, "Settling Behavior and Ringing for two stage
design") confirms many students chose two-stage. We considered it too — here is
how we'd have built it and why we went single-stage gain-boosted instead.

## How we would have implemented it

A classic **two-stage Miller-compensated** opamp:

- **Stage 1 — gain stage:** a differential pair into a high-impedance node
  (telescopic or folded cascode, or a simple cascoded diff pair) → ~40–60 dB,
  sets the dominant pole.
- **Stage 2 — output stage:** **common-source** (CS) PMOS/NMOS → near rail-to-rail
  output swing, adds the second gain (total $>90\,\mathrm{dB}$ easily).
- **Compensation:** **Miller cap $C_c$** from stage-1 output to stage-2 output with
  a **nulling resistor $R_z$** to move the RHP zero
  ($\omega_z = 1/[C_c(1/g_{m2}-R_z)]$) out of the way. Pole-splitting:
  dominant pole $\approx 1/(R_1 g_{m2} R_2 C_c)$, non-dominant $\approx g_{m2}/C_L$.
- **GBW / PM:** $\mathrm{GBW}=g_{m1}/C_c$; size $g_{m2}$ so the 2nd pole
  $g_{m2}/C_L$ sits well above GBW (PM $\ge 60$–$70°$). For our $242\,\mathrm{MHz}$
  GBW this forces a **large $g_{m2}$** (i.e. a lot of stage-2 current).
- **CMFB:** two CM loops (one per stage) or a CMFB on the output stage — more CMFB
  than the single-stage's one loop.
- **First-cut sizing sketch:** $g_{m1}=2\pi\cdot242\,\mathrm{MHz}\cdot C_c$;
  $C_c\sim0.2$–$0.5\,C_L$; $g_{m2}$ ≈ a few × $g_{m1}$ to keep the 2nd pole high.

## Why we'd consider it (the upsides)

- **Gain is free:** $>90\,\mathrm{dB}$ with **no gain-boosting** — avoids designing
  the booster aux-amps entirely (the hardest part of the single-stage path).
- **Large output swing:** the CS output stage swings near rail-to-rail.
- Familiar, textbook topology.

## Why we rejected it (for *this* spec)

- **Settling — the deciding factor.** Two poles + Miller + the $R_z C_c$ doublet →
  **ringing** (exactly the TA's 21 Jun announcement) and a slow-settling tail.
  Hitting **0.05 % in 25 ns** is materially harder than the single-stage's clean
  first-order settle. (`06_settling_analysis.md`, `07` §2.)
- **Power = the grade.** Stage 2 burns extra current (to push $g_{m2}/C_L$ past
  $242\,\mathrm{MHz}$) and slewing $C_c$ costs current → **worse FoM**. Single-stage
  spends every µA on bandwidth. (`08_power_prediction.md`.)
- **Its advantages aren't needed here.** We already reach $>78\,\mathrm{dB}$ via
  gain-boosting, and SNR is only $66\,\mathrm{dB}$ (relaxed) so the big swing buys
  nothing.
- **Bolting it onto our design is doubly bad.** We'd pay for gain-boosting *and* a
  2nd stage + compensation/ringing, for gain we already have.

## When it *would* be our fallback

Only if the single-stage gain-boosted telescopic **can't reach 78 dB within the
$1.8\,\mathrm{V}$ headroom / swing budget** — the documented **Option-C fallback**
(`02`). Unlikely: EE4520 reached ~90 dB single-stage with boosting.

## For the report (short explanation / design process)

One paragraph: *"We evaluated a two-stage Miller-compensated opamp (gain and swing
come for free, no gain-boosting needed), but rejected it for this spec: the Miller
compensation introduces a pole-zero doublet and ringing that make 0.05 % settling
in 25 ns harder, and the second stage's bias + compensation current worsen the
power/FoM that the project grades on. Since the relaxed 66 dB SNR needs no large
swing and gain-boosting already delivers >78 dB, the single-stage gain-boosted
cascode is the lower-power, cleaner-settling choice — the TA ringing clarification
is the symptom of the two-stage path we avoided."*

Cross-refs: `02_topology_choice.md` (Option C + decision), `06_settling_analysis.md`
(ringing rule), `07_lecturer_clarifications.md` §2, `08_power_prediction.md`.
