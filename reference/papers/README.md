# Reference papers — relevance to the EE4525 residue amplifier

Two IEEE papers pulled (via TU Delft Xplore) to ground our architecture choice
and sizing. Both target the **same problem** as our project — a fast-settling,
low-power amplifier for a switched-capacitor / pipeline-ADC residue stage — and
the Ryu paper is in the **exact same 0.18 µm CMOS, 1.8 V** technology.

Bottom line they support: a **single-stage gain-boosted cascode** with a
**current-reuse (complementary) input** and **switched-capacitor CMFB** is the
right architecture for *fast settling at lowest power* (our grade driver), and
they tell us **how fast to make the gain-boosters** and **how to halve the input
current**. See `../analysis/02_topology_choice.md`.

---

## Paper 1 — Yang, Binkley, Li, "Modeling and Optimization of Fast-Settling-Time Gain-Boosted Cascode CMOS Amplifiers," *IEEE SoutheastCon*, 2010

**What it is:** a settling-time analysis of the gain-boosted cascode (the
small-signal model has 4 poles / 2 zeros; the gain-boosters inject **pole-zero
doublets**). It derives the optimum gain-booster GBW and phase margin for
**minimum settling time**.

**Why it matters to us:** we *will* need real gain-boosting to reach $A_0 > 78\,\mathrm{dB}$,
and the boosters' doublets are exactly what can wreck a 25 ns / 0.05 % settle.
This paper gives the design targets so they don't.

**The actionable rules (use these directly when sizing the boosters):**

- Main-amp unity GBW $\omega_u \approx g_{m1}/C_L$ (telescopic main amp — chosen
  for *better frequency response and lower power than folded cascode*).
- **Booster A** (the one *in* the signal path): $\mathrm{GBW}_A = 0.8\,\omega_u$, $\mathrm{PM}_A = 70°$.
- **Booster B** (the one *not* in the signal path): $\mathrm{GBW}_B = 0.4\,\omega_u$, $\mathrm{PM}_B = 60°$.
- Keep the cascode-source pole high: $\omega_{P4} = (g_{m2}+g_{mb2})/C_{Xa} \gtrsim 2.6\,\omega_u$.
- **Doublets:** a *low* booster PM makes the doublets complex (ringy); a *high*
  PM makes them real. The doublet mainly slows the **high-accuracy (0.01 %)**
  settling, not the 0.1 % — so since we settle to $\sim$0.05 % (66 dB), we must
  push the booster GBW/PM into the "real-doublet" regime above and place the
  doublet beyond $\omega_u$.
- Their example (0.5 µm, 3.3 V): GBW 436 MHz, gain 97.5 dB, **0.1 % settle 3.2 ns**,
  0.01 % settle 5.8 ns — i.e. the methodology delivers ns-class settling.

**Key ancestor reference (cite in the report):** K. Bult & G. Geelen, "A
fast-settling CMOS op amp for SC circuits with 90-dB DC gain," *IEEE JSSC*,
1990 — the original gain-boosting (regulated-cascode) paper.

---

## Paper 2 — Ryu, Song, Bacrania, "A 10-bit 50-MS/s Pipelined ADC With Opamp Current Reuse," *IEEE JSSC*, vol. 42(3), 2007

**What it is:** a low-power pipeline ADC in **0.18 µm CMOS at 1.8 V** whose
residue opamp **reuses its bias current** by stacking an **NMOS input pair and a
PMOS input pair in the same current branch**. Achieves 220 µW/MHz, 11 mW analog.

**Why it matters to us:** this is *the* low-power lever for our grade — the grade
is "lowest power that meets spec," and current reuse buys roughly **2× $g_m$ per
µA** (since $g_{m,\text{tot}} = g_{mN}+g_{mP}$ at one tail current) → lower current
for the required GBW and lower input-referred noise.

**Useful design points:**
- **Base topology:** a **gain-boosted telescopic** opamp with **capacitive
  (switched-capacitor) CMFB** (Fig. 9) — matches Paper 1's telescopic choice and
  gives us a concrete *real-CMFB* style (we must replace the EE4520 ideal CMFB).
- **Capacitive level shifter** (Fig. 10): lets a single **NMOS-input** boost amp
  gain-boost *both* the NMOS and PMOS cascodes. NMOS-input boosters are cheaper
  (higher $g_m$, lower power) than the PMOS-input boosters the bias would
  otherwise force → extra power saving. Boosters cascoded for **gain > 55 dB**.
- **Headroom cost:** the stacked complementary input adds **one extra $V_{DSAT}$**
  drop → small output-swing reduction. *Acceptable for us* because our SNR target
  is relaxed (66 dB) so we don't need a large swing.
- **Settling-bandwidth rule of thumb (their Eq. 5):** to settle to $\tfrac{1}{2}$ LSB
  of an $N$-bit residue, $\mathrm{BW} = \dfrac{N\ln 2}{\pi T}$ — the same
  $\tau$-vs-accuracy relation we use for the 25 ns budget.
- Input common-mode is set by the stack ($V_{INC} = V_{DS,\text{tail}} + V_{GS,\text{in}}$),
  and NMOS-input is favoured for the noise-critical (high-gain) path.

**Caveat — what does *not* transfer:** Ryu switches the two pairs between clock
phases to *share* one opamp across a sampling and an amplifying stage
(opamp-sharing). **Our project does not share opamps** — we have a single
amplification phase. So we take only the **current-reuse principle**: run **both
pairs simultaneously** as a complementary (inverter-style) input that sums $g_m$
at one bias current. The phase-multiplexing / summing-node-reset machinery is not
needed here.

---

## How they combine into our plan

1. **Architecture:** single-stage **gain-boosted telescopic (or folded) cascode**,
   **current-reuse complementary input**, **SC-CMFB**. (Folded first to de-risk —
   reuses EE4520 — then telescopic/current-reuse to push power down.)
2. **Size the main amp** for $\omega_u = g_m/C_L$ to hit GBW $\approx 194\,\mathrm{MHz}$ /
   $\tau \le 3.3\,\mathrm{ns}$ (the 25 ns settle).
3. **Size the gain-boosters per Paper 1:** A at $0.8\,\omega_u$/70°, B at $0.4\,\omega_u$/60°,
   cascode-source pole $\ge 2.6\,\omega_u$ — verify the doublet doesn't leave a
   slow tail at 66 dB.
4. **Halve the input current per Paper 2** with the complementary input; watch the
   $1.8\,\mathrm{V}$ headroom (current-reuse + cascodes), spending the swing slack
   that the relaxed 66 dB SNR gives us.
5. **CMFB:** real SC-CMFB (Paper 2 style), replacing the EE4520 ideal block.

These also serve as **citations for Deliverable 9** (architecture justification,
sizing-for-settling, gain-booster design, low-power technique).

---

## Resit papers (October 2026), analysed in `NOTES-resit-2026-10.md`

- `IEEE-8443396-A-66-dB-SNDR-Pipelined-Split-ADC-in-40-nm-CMOS-Using-a-Class-AB-Residue.pdf`: Akter et al., IEEE JSSC 2018, doi:10.1109/JSSC.2018.2859415. Class-AB push-pull residue amplifier with split-capacitor biasing and incomplete settling (40 nm, 1 V); not transferable here, but it prices level-shift capacitors.
- `IEEE-9293306-A-High-Slew-Rate-Enhancement-Class-AB-Operational-Transconductance-Amplifier-OTA.pdf`: Kim, Song, Roh, IEEE Access 2020, doi:10.1109/ACCESS.2020.3044608. 0.18 µm class-AB OTA with triode slew-rate-enhancement devices in the mirror diodes; not applicable (no mirrors in our signal path).
- `IEEE-1425714-Low-Voltage-Super-class-AB-CMOS-OTA-cells-with-very-high-slew-rate-and-power.pdf`: López-Martín et al., IEEE JSSC 2005, doi:10.1109/JSSC.2005.845977. Super class-AB OTAs (adaptive-biased input pair plus local CMFB); its adaptive-bias principle is the basis of experiment E2.
- `IEEE-1266829-Miller-Compensation-Using-Current-Buffers-in-Fully-Differential-CMOS-Two-Stage.pdf`: Hurst et al., IEEE TCAS-I 2004, doi:10.1109/TCSI.2003.820254. Pole and zero formulas for four current-buffer compensation variants; our CR stage is their Fig. 3 case.
- `IEEE-9307219-Design-of-Three-Stage-OTA-Based-on-Settling-Time-Requirements-Including-Large.pdf`: Giustolisi, Palumbo, IEEE TCAS-I 2021, doi:10.1109/TCSI.2020.3044454. Settling-time design with slew and separation factors; shows slewing costs about 19 % of our settling budget.
- `IEEE-1406209-An-accurate-analysis-of-slew-rate-for-two-stage-CMOS-opamps.pdf`: Yavari, Maghari, Shoaei, IEEE TCAS-II 2005, doi:10.1109/TCSII.2004.842058. Large-signal slew-rate model for two-stage Miller opamps when a stage-1 device enters triode.
