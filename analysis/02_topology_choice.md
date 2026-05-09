# 02 — Topology choice

Architecture is fully free per PDF. Three viable starting points; pick before sizing.

## Option A — Folded-cascode + transistor CMFB (no gain-boost)

**Pros:**
- Reuse hw2 schematic almost verbatim; only replace ideal CMFB.
- Single high-impedance node → single dominant pole, easy compensation (no Miller cap).
- Wide ICMR; output near rail-to-rail with cascodes sized carefully.

**Cons:**
- $A_0$ from a plain cascode at 0.18 µm is typically $50$–$70\,\mathrm{dB}$ → may **fall short of $78\,\mathrm{dB}$** without help.
- Pushing $g_m$ up to hit $194\,\mathrm{MHz}$ GBW in a single stage costs current.

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

## Recommended decision flow

1. Start in `design/core-amp/folded_cascode_baseline.asc` with the EE4520 sizing.
2. Replace ideal CMFB with a real CMFB (see `05_cmfb_design.md`). Re-simulate AC.
3. If $A_0 \geq 78\,\mathrm{dB}$ and $\tau \leq 3.3\,\mathrm{ns}$ and $P \leq 3\,\mathrm{mW}$, freeze Option A.
4. Else add gain-boosting (Option B).
5. Switch to two-stage (Option C) only if B can't close power.

## Decision

- [ ] Option A
- [ ] Option B
- [ ] Option C
- [ ] Other: _____________

Reason: _________________________________
