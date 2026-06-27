# 10 — Gain-booster design (real circuits to replace the ideal blocks)

Reference + plan for the two **real gain-boosting amplifiers** we must draw in
Phase 4 (the EE4520 `Ideal Gain-Boosting PMOS/NMOS` VCVS boxes — `E2/E3`, `E5/E6`
— are forbidden in EE4525). Template = Binkley Fig. 7; improvement = Ryu's
capacitive level shifter.

## Binkley's Fig. 7 — the real-booster template

![Binkley et al. (IEEE SoutheastCon 2010), Fig. 7 — gain-boosting amplifiers A and B](../reserach-papers/figures/binkley_fig7_gain_boosters.png)

*Figure: Yang, Binkley & Li, "Modeling and Optimization of Fast-Settling-Time
Gain-Boosted Cascode CMOS Amplifiers," IEEE SoutheastCon 2010, Fig. 7 — cropped
for study reference; see `binkley_fig7_…pdf`.*

Each booster is a **single-stage folded-cascode differential amplifier with its
own CMFB**:

| | **Amplifier A** (right) | **Amplifier B** (left) |
|---|---|---|
| Input stage | **PMOS** input pair `M6` (tail `I6` *above*) | **NMOS** input pair `M11` (tail *below*) |
| Senses / regulates | the **NMOS** cascode (low-side node `v_Xa`, `G_La`) | the **PMOS** cascode (high-side node) |
| Devices | `M6`–`M10`, bias `I6/I9` | `M11`–`M15`, bias `I11/I13` |
| CMFB | own CMFB block | own CMFB block |
| Role | **in the signal path** (booster A) | **not in signal path** (booster B) |

Why each input type: a **PMOS-input** booster sits comfortably at a **low**
common-mode (the NMOS-cascode source), an **NMOS-input** booster at a **high** CM
(the PMOS-cascode source). Both are themselves cascoded for high gain (Binkley's
case study: boosters give the main amp ~97.5 dB).

## How it maps onto our core (EE4520 numbering)

| EE4520 ideal box | Real booster (Binkley type) | Regulates | Input type |
|---|---|---|---|
| `Ideal Gain-Boost NMOS` (`E5/E6`) | **Booster A** | NMOS cascode `Mn6/Mn8` (low node) | **PMOS** input |
| `Ideal Gain-Boost PMOS` (`E2/E3`) | **Booster B** | PMOS cascode `Mp2/Mp4` (high node) | **NMOS** input |

Each replaces an ideal VCVS (`Aadd=100`) with this ~6–8-device folded-cascode amp
**plus its own CM stabilization** — see `02_topology_choice.md` build plan.

## Sizing & speed rules (Binkley, for **minimum settling**)

With $\omega_u \approx g_{m1}/C_L$ the main-amp unity GBW:

- **Booster A (in signal path):** $\mathrm{GBW}_A = 0.8\,\omega_u$, $\mathrm{PM}_A = 70°$.
- **Booster B (not in path):** $\mathrm{GBW}_B = 0.4\,\omega_u$, $\mathrm{PM}_B = 60°$.
- Keep the cascode-source pole high: $\omega_{P4} = (g_{m,cas}+g_{mb,cas})/C_{X} \gtrsim 2.6\,\omega_u$.
- **Doublets:** the boosters inject pole-zero doublets. *Low* booster PM → complex
  (ringy) doublets; *high* PM → real. The doublet slows the **high-accuracy**
  settling, so push GBW/PM into the real-doublet regime and keep the doublet
  **beyond $\omega_u$** — critical for our 0.05 % (66 dB) settle in 25 ns.

## The improvement for our power grade (Ryu)

Binkley uses **two separate** boosters, and the **PMOS-input** one (booster A) is
the costlier. **Ryu's capacitive level shifter** lets a **single cheap
NMOS-input booster regulate *both* cascodes** → less current and area. Adopt
Fig. 7's *topology*, but layer Ryu's level-shift trick to avoid paying for two
full boosters. (See `../reserach-papers/README.md`, Paper 2.)

## Constraints for *our* implementation (vs. Binkley)

- **Process / supply:** Binkley is **0.5 µm / 3.3 V**; we are **0.18 µm / 1.8 V**
  → much **tighter headroom**. Keep each booster's stack low; all boosters share
  the **single 1.8 V rail** (`07` §5.1) — no boosted supply.
- **Each booster needs CM stabilization** (its own small CMFB or a CM-stable
  pseudo-diff structure), as Fig. 7 shows.
- **Bias:** the boosters need their own bias currents/voltages → part of the
  **extended bias block** (`02` build plan).
- **Build order (Phase 4):** NMOS-cascode booster (A, PMOS-input) first with the
  other kept ideal, then the PMOS-cascode booster (B), per Binkley's advice and
  the PDF.

## Status

- [ ] Draw Booster A (PMOS-input folded cascode + CMFB) → netlist → standalone sim → drop into core
- [ ] Draw Booster B (NMOS-input) likewise
- [ ] Evaluate Ryu capacitive-level-shift single-booster variant for power
- [ ] Verify $0.8\,\omega_u$/70° and $0.4\,\omega_u$/60°, doublet beyond $\omega_u$, 1.8 V headroom

Cross-refs: `02_topology_choice.md` (build plan), `06_settling_analysis.md`
(doublets/settling), `08_power_prediction.md` (NEF/power), `05_cmfb_design.md`
(CMFB style), `../reserach-papers/README.md` (Binkley + Ryu).
