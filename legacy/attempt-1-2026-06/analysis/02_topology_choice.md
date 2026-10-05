# 02 — Topology choice

Architecture is fully free per PDF. Three viable starting points; pick before sizing.

## Option A — Folded-cascode + transistor CMFB (no gain-boost)

**Pros:**
- Reuse hw2 schematic almost verbatim; only replace ideal CMFB.
- Single high-impedance node → single dominant pole, easy compensation (no Miller cap).
- Wide ICMR; output near rail-to-rail with cascodes sized carefully.

**Cons:**
- $A_0$ from a plain cascode at 0.18 µm is typically $50$–$70\,\mathrm{dB}$ → may **fall short of $78\,\mathrm{dB}$** without help.
- Pushing $g_m$ up to hit $242\,\mathrm{MHz}$ GBW in a single stage costs current.

**When to pick:** if you can show $A_0 \geq 78\,\mathrm{dB}$ by sizing alone (long $L$, moderate $g_m / I_D$).

## Option B — Folded-cascode + gain-boosting (NMOS + PMOS auxiliary amps)

**Pros:**
- $A_0$ multiplied by aux-amp gain: easily $> 100\,\mathrm{dB}$.
- Same single dominant pole, settling stays first-order.

**Cons:**
- Three amplifiers to design (main + two boosters). Each booster must be faster than the slow pole at the cascode source it boosts → tight bandwidth-doublet balance.
- Per PDF: design NMOS-side and PMOS-side boosters separately; keep the other ideal while iterating.

**When to pick:** if Option A misses $A_0$ and you have time budget for two more amps.

## Option C — Two-stage Miller-compensated

**Pros:**
- $A_0$ trivially $> 90\,\mathrm{dB}$.
- Larger output swing.

**Cons:**
- Two poles → Miller compensation eats slew speed; settling at $25\,\mathrm{ns}$ to $-66\,\mathrm{dB}$ is **harder** than single-stage with proper $\omega_u$.
- $C_c$ shows up in noise and power.

**When to pick:** if you can't make a single-stage hit GBW within power, or if output swing is the limiter.

> Full write-up of *how we'd build it and why we rejected it* (for the report's
> short explanation) → `11_two_stage_alternative.md`.

## Recommended decision flow

1. Start in `design/core-amp/folded_cascode_baseline.asc` with the EE4520 sizing.
2. Replace ideal CMFB with a real CMFB (see `05_cmfb_design.md`). Re-simulate AC.
3. If $A_0 \geq 78\,\mathrm{dB}$ and $\tau \leq 3.3\,\mathrm{ns}$ and $P \leq 3\,\mathrm{mW}$, freeze Option A.
4. Else add gain-boosting (Option B).
5. Switch to two-stage (Option C) only if B can't close power.

## Literature support (`../reserach-papers/`)

Two papers (annotated in `../reserach-papers/README.md`) back a **single-stage
gain-boosted cascode** over two-stage for this fast-settle / low-power spec:

- **Binkley 2010** — gain-boosted (telescopic) cascode beats multi-stage for
  high-gain + wide-BW + low-power SC; gives booster sizing for min settling
  (A: $0.8\,\omega_u$/70°, B: $0.4\,\omega_u$/60°, cascode pole $\ge 2.6\,\omega_u$).
- **Ryu 2007** (same 0.18 µm / 1.8 V) — **current-reuse** complementary input
  ($g_m = g_{mN}+g_{mP}$ at one tail current) → the low-power lever for the grade;
  gain-boosted telescopic + SC-CMFB.

→ Leaning **Option A/B (single-stage) + current-reuse input + real SC-CMFB**;
two-stage (Option C) kept only as a fallback.

## Decision (settled — 2026-06-27)

**Chosen: single-stage gain-boosted cascode (Option B) + current-reuse
complementary input + real switched-capacitor CMFB** — **folded** baseline
evolving to a **telescopic** stack when current-reuse is added (the two are
coupled, see Build plan). Two-stage (Option C) is a documented fallback only.

- [ ] Option A — plain cascode (fallback if gain-boost proves unnecessary)
- [x] **Option B — gain-boosted cascode** (committed), with:
  - [x] **current-reuse (complementary NMOS + PMOS) input** — the low-power lever (Ryu 2007)
  - [x] **real switched-capacitor CMFB** (replaces the ideal CMFB)
- [ ] Option C — two-stage (fallback only, if single-stage can't make 78 dB at power)

**Reason:** the spec is fast-settle ($25\,\mathrm{ns}$) / modest gain ($78\,\mathrm{dB}$) /
relaxed SNR ($66\,\mathrm{dB}$) / **lowest power = the grade**. Single-stage = one
output pole → cleanest fast settling per µA; gain-boosting reaches $78\,\mathrm{dB}$
without adding a pole; current-reuse ~doubles $g_m/\mu\mathrm{A}$ for the power
grade. Two-stage's strengths (huge gain, large swing) aren't needed here and its
compensation hurts settling + power. Literature-backed (Binkley 2010, Ryu 2007)
and reuses the EE4520 core → lowest risk.

## Build plan — what we draw vs. reuse (EE4520 → EE4525)

The EE4520 sheet already has the blocks we replace drawn as **behavioral
placeholders** (`E`-source boxes: `Ideal CMFB`, `Ideal Gain-Boosting PMOS/NMOS`).
So the architecture work is mostly **swapping those boxes for real transistor
sub-circuits** — the cascode core, bias block and testbenches stay.

### New transistor drawings (the circuit work)

| EE4520 (have) | EE4525 (draw) | ~New devices | Required? |
|---|---|---|---|
| Ideal CMFB (`E1` VCVS) | **Real SC-CMFB** (sense caps + ideal switches → tail/load gate); CT-CMFB alt | ~4 sw + 2–4 caps, or ~6–8 FET | **Yes** |
| Ideal gain-boost PMOS (`E2/E3`) | **Real PMOS-cascode booster** (NMOS-input diff-amp regulating `Mp2/Mp4`) | ~6–8 | **Yes** |
| Ideal gain-boost NMOS (`E5/E6`) | **Real NMOS-cascode booster** (PMOS-input / level-shifted diff-amp regulating `Mn6/Mn8`) | ~6–8 | **Yes** |
| NMOS-only input (`Mn3/Mn4`) | **+ complementary PMOS input, current-reuse** ($g_m=g_{mN}+g_{mP}$) — **restructures folded → telescopic stack** (see below) | ~+4–6 | **Power step (last)** |
| Bias block (6 bias V) | **Extended bias** for the boosters + CMFB + P-input tail | a few branches | **Yes** |

### Reused with retune only (no new topology)

- The **cascode core** (`Mp1–Mp4`, `Mn1–Mn8`, mirrors) — same skeleton, resized for the new GBW / current.
- The **3 testbenches** (loaded-AC, transient, noise) + **feedback net** (`Cin/Cfb/Rin/Rfb`) + `Cload` + the **replica** — same structure, retuned values, `.meas` $\beta$ updated.
- The AC testbench keeps an **ideal DC-CMFB-with-large-R** helper (allowed, `faq.txt`) to set the OP point in AC even when the real CMFB is switched-capacitor.

### Sequence (de-risk → optimise)

1. Retune the **folded-cascode core with the ideal blocks** to the EE4525 spec (Phase 2) — find the current 25 ns actually demands.
2. Drop in the **real SC-CMFB** (Phase 3).
3. Drop in the **real gain-boosters**, NMOS first then PMOS, Binkley-sized ($0.8\,\omega_u$/70°, $0.4\,\omega_u$/60°, cascode-source pole $\ge 2.6\,\omega_u$) (Phase 4).
4. **Restructure the input to current-reuse** and minimise power (Phase 5 power pass) — highest payoff, highest risk → last.

### Folded (start) → telescopic (endpoint) — why current-reuse decides this

Folded-vs-telescopic is **not an independent choice** — the current-reuse decision forces it:

- Current-reuse only works if the NMOS **and** PMOS input pairs are **stacked in
  series** to *share* one bias current. A **folded** structure pushes the input
  current out into a separate branch → no sharing → no current-reuse. So
  **current-reuse ⟹ a telescopic (vertical) input stack** — exactly Ryu's
  "gain-boosted **telescopic** with current reuse."
- Telescopic is also the **more power-efficient** main amp (one current path →
  more $g_m/\mu\mathrm{A}$, lower noise, fewer parasitic poles). Binkley and Ryu
  both chose it for that reason.

So the topology evolves *with* the sequence above:

- **Steps 1–3 — folded:** keep the EE4520 **folded** cascode while de-risking
  (easier to bias, more headroom, reuses the baseline).
- **Step 4 — telescopic:** the current-reuse migration **restructures the core
  into a telescopic stack**. Folded → telescopic happens *as part of* adding
  current-reuse, **not** as a separate step.

**Gate (the only real risk):** telescopic stacks more devices between the rails
(+ the complementary pair + its tail) → **tighter output swing on 1.8 V**.
Acceptable here because SNR is only $66\,\mathrm{dB}$ (swing slack) and the input
CM is a *sampled* value we choose (telescopic ICMR limit doesn't bite). **Ryu is
the existence proof** (0.18 µm / 1.8 V, current-reuse telescopic, 1 Vpp). If the
$1.8\,\mathrm{V}$ headroom can't fit our swing during sizing, **stay folded** and
pay the extra current.

Each block: draw as a netlist → simulate standalone → drop into the core → re-verify (render + AC / transient / noise). Cross-refs: `05_cmfb_design.md` (CMFB), `10_gain_booster_design.md` (real boosters — Binkley Fig. 7 template + figure), `03_sizing_calcs.md` (core + boosters), `08_power_prediction.md` (FoM target), `../reserach-papers/README.md` (Binkley / Ryu design rules).
