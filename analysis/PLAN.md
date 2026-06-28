# EE4525 Project plan & phasing

Today: **2026-05-09** | Due: **Sun 28 Jun 2026, 23:59** → ~7 weeks.

> TA clarifications collected in `07_lecturer_clarifications.md` (1/f-noise model,
> ringing/$\tau$ rule, Deliverable-4 plot, FoM, single supply, submission).
>
> Top-down power/FoM prediction (Bult efficiency method, $P_{system}$ floor,
> $F_{circuit}$, the clean FoM identity) in `08_power_prediction.md` — use it to
> sanity-check power and FoM before *and* after sizing.
>
> **Architecture settled:** single-stage gain-boosted cascode + current-reuse
> input + real SC-CMFB — see `02_topology_choice.md` (decision + block-by-block
> build plan EE4520 → EE4525).
>
> **Execution refs:** all sims + their `.meas` → `09_simulation_runbook.md`;
> every deliverable figure + how to extract it → `../report/README.md`.

## Phase 0 — Setup (done)

- [x] Pull EE4520 reusable artefacts → `from-ee4520/` (index + Deliverable-6 baseline: `from-ee4520/README.md`)
- [x] Scaffold `design/`, `simulations/`, `analysis/`, `models/`, `report/`
- [x] Init git
- [x] Drop in baseline schematics + 0.18 µm model
- [x] Switch active schematics to the **$1/f$-noise** model `log018.l` (off `logic018 no1of.l`) — `models/README.md`
- [x] Transcribe TA clarifications → `07_lecturer_clarifications.md`

## Phase 1 — Specs & budget (week 1, by 2026-05-16) — DONE 2026-06-28

All numbers computed + cross-checked in `phase1_budget.m` (→ `phase1_results.txt`,
figures `../report/figures/phase1_*.png`). Frozen table in `01` §0.

- [x] Fill `analysis/00_spec_table.md` design-time column (frozen choices + predictions)
- [x] Pick V_out swing (single-ended $\pm0.45\,\mathrm{V}$, diff $1.8\,\mathrm{V_{pp}}$, $\eta_{vol}=0.5$) → noise budget finalised in `04`
- [x] Solve C_in from kT/C share → **C_in = 5 pF, C_fb = 1.25 pF, C_load = 5 pF** (kT/C = 204 µV, margin)
- [x] Solve g_m,in from GBW → **g_m ≈ 10 mS**, input current 0.42–0.67 mA (reuse) → first-cut bias
- [x] Topology decision in `02_topology_choice.md` (already settled: GB-cascode + current-reuse + SC-CMFB)
- [x] $P_{system}$ floor = **0.169 mW**; first-cut $F_{circuit}=76$, **P ≈ 0.30 mW (TD) / 1.27 mW (BU)**, **FoM ≈ 178 dB** — all pass (`08` §5)

**Phase-2 entry conditions met:** caps frozen, $g_m$/current first-cut set,
GBW ($242\,\mathrm{MHz}$) and $\tau$ ($3.0\,\mathrm{ns}$) targets known. Next: size
the folded-cascode core (`03`) to $A_0\ge78\,\mathrm{dB}$ at this GBW with ideal CMFB.

## Phase 2 — Core amplifier sizing (weeks 2–3, by 2026-05-30) — DONE 2026-06-28

Sized folded-cascode core (`design/core-amp/folded_cascode_baseline.asc`) with ideal
CMFB + ideal gain-boost. Results frozen in `03_sizing_calcs.md` and `00_spec_table.md`
(Phase-2 section). Achieved: **A₀ 93.9 dB · GBW 264 MHz · PM 89° · τ 3.01 ns ·
gₘ,ᵢₙ 12.2 mS · I(Vdd) 1.55 mA / 2.78 mW · branch rule 773 µA ≥ 597 µA · all 17 FETs
saturated**. Method log + the AC measurement gotcha (loaded `voutp2` node ≠ clean
open-loop; use unloaded `V(voutp)−V(voutn)` post-processed in Python) captured below.

- [x] First-cut sizing in `03_sizing_calcs.md` (g_m/I_D method) — input pair g_m/I_D=20.4 (weak-mod inv. for low Vgs → tail headroom + low power); cascodes/sources 10–11; tail 11
- [x] Open-loop AC sim in `simulations/ac/` → **A₀ = 93.9 dB** (≥78 with ideal boost), **GBW = 264 MHz** (≈242 target), **PM = 89°** (≥60)
- [x] OP-point sweep → **all transistors saturated**; V_DS,sat margins: signal/cascode devices ≥ 520 mV, wide-swing-sink/tail/source devices 52–85 mV (*intrinsic* to a 1.8 V wide-swing folded cascode — verified density-independent; all remain in saturation)
- [x] Iterate sizing until A₀, GBW, P all in spec with ideal CMFB — **all pass simultaneously** (P = 2.78 mW < 3 mW, I(Vdd) = 1.55 mA < 1.7 mA)

**Phase-3 entry conditions met:** core frozen with ideal blocks; ready to drop in the
real SC-CMFB (replaces ideal `E1`) and re-verify differential AC.

## Phase 3 — CMFB (week 4, by 2026-06-06)

> **⚠ Power-ceiling watch (entry note, from Phase-2 closure).** The core already
> draws **I(Vdd) = 1.55 mA / 2.78 mW = 93 % of the 3 mW ceiling** — only **~0.15 mA /
> 0.22 mW** of headroom before the 1.7 mA / 3 mW hard limit, and Phases 3–4 *add*
> supply current:
> - **Phase 3 real SC-CMFB:** switched-capacitor → **~0 mA static** (clocked
>   charge-transfer, no continuous DC bias path). Negligible adder. *(A continuous-time
>   error-amp variant would instead cost ~20–50 µA — avoid it for this reason.)*
> - **Phase 4 two gain-booster aux-amps (single $V_{dd}$ rail):** each is a small
>   diff-amp driving a low-cap cascode gate; bandwidth-, not power-bound. Lean bias
>   ≈ 30–75 µA tail each → **~60–150 µA total**; if cascoded for ≥40 dB / higher speed,
>   up to ~250 µA.
>
> **✅ Phase-3 measured (2026-06-28):** the real SC-CMFB drew **0 mA static** (clocks
> 0 A, helper ~0.5 pA) → **I(Vdd) = 1.547 mA, unchanged** from Phase-2. The SC choice
> paid off exactly as predicted; ~0.15 mA headroom remains for Phase-4 boosters.
>
> **Verdict:** with a pure SC-CMFB (~0) and **lean boosters (≤~150 µA total)**,
> post-Phase-4 I(Vdd) ≈ **1.55 + 0.15 ≈ 1.7 mA — right at the ceiling**; a generous
> booster bias **breaches** 1.7 mA / 3 mW *before* Phase-5 current-reuse. The margin is
> razor-thin (~9 %). **Actions:** (1) bias the boosters minimally (Binkley min-current
> sizing); (2) re-measure I(Vdd) after *each* block drop-in; (3) if it breaches, pull
> **current-reuse forward** (it halves input-branch current — the dominant term) rather
> than waiting for Phase 5. Current-reuse is in any case now mandatory for FoM (`00`).

## Phase 3 — CMFB — DONE 2026-06-28

Replaced ideal `E1` with a **real switched-capacitor CMFB** (`design/cmfb/`,
`05_cmfb_design.md`, results `design/cmfb/phase3_results.txt`). $C_{CM}=0.5$ pF
switched + $C_C=1.25$ pF hold/sense per side, control node `Vbcm`, 20 MHz
non-overlapping clock, ideal switches, weak ideal-DC helper (100 MΩ) for OP/AC.

- [x] Build **real SC-CMFB** (settled) per `05_cmfb_design.md` — replaces ideal `E1`
- [x] CM step response **stable** (overshoot +0.26 mV, no ringing); CM-loop $\tau_{cm}=4.15$ ns ($f_{cm}\approx38$ MHz) ≈ diff $f_u$=52.9 MHz → CM tracks during the 25 ns settle
- [x] Differential AC **unregressed**: A₀ 93.81 dB · GBW 264 MHz · PM 89° (Δ ≈ 0 vs Phase 2)
- [x] **I(Vdd) = 1.547 mA after CMFB drop-in** ✓ (== Phase-2; SC-CMFB adds 0 mA static; clocks draw 0 A)

## Phase 4 — Gain-boosting (committed; week 5, by 2026-06-13)

Part of the settled architecture (need 78 dB single-stage) — see `02_topology_choice.md` build plan and **`10_gain_booster_design.md`** (Binkley Fig. 7 template + Ryu improvement, with the figure).

> **Base schematic: fork from `design/cmfb/folded_cascode_cmfb.asc`** (the Phase-3
> real-CMFB version) — **NOT** `design/core-amp/folded_cascode_baseline.asc` (ideal CMFB).
> Keep the real SC-CMFB **and** the NMOS-only input; replace ONLY the ideal gain-boost
> `E2–E7` (`Aadd=100`) with real cascode boosters. Expect $A_0$ to **drop** from 93.8 dB
> toward the real-booster value — that drop *is* the genuine $\ge 78\,\mathrm{dB}$ test
> (`00` Phase-2 note). Read A₀/GBW/PM from the unloaded `V(Voutp)−V(Voutn)` + Python,
> never the `Voutp2` `.meas` (`09` §C). Keep total booster bias $\le\sim150\,\mu$A (ceiling).

- [x] Design **real NMOS-cascode booster** (PMOS-input fold + ref-pinned CMFB), PMOS kept ideal first → verified
- [x] Then **real PMOS-cascode booster** (NMOS-input fold + ref-pinned CMFB); both real → **$A_0$ 101.3 dB**
- [x] Watched booster doublet: UGF ~0.5 GHz (>0.8$\omega_u$ target) pushes the doublet **beyond $\omega_u$**; clean single-pole AC (PM 85.9°) + monotone CM-step recovery → no slow tail

## Phase 4 — Gain-boosting — DONE 2026-06-28

Replaced ideal VCVS boosters (`E2/E3` PMOS, `E5/E6` NMOS, `Aadd=100`) with **two REAL
differential folded-cascode booster aux-amps + reference-pinned CMFB** (`design/gain-boost/`,
`10_gain_booster_design.md`, `00_spec_table.md` Phase-4 block, results
`design/gain-boost/phase4_results.txt`). Booster A = PMOS-input (in-path NMOS cascode);
Booster B = NMOS-input (off-path PMOS cascode). Real SC-CMFB + NMOS-only input unchanged.

- [x] **$A_0 = 101.27$ dB** (≥78 ✓, +23 dB margin) — the genuine real-booster test; un-boosted core 55.8 dB → boosters add +45.5 dB
- [x] GBW 261.9 MHz (≈264), PM 85.9° (≥60) — differential response not degraded
- [x] **$I(V_{dd}) = 1.658$ mA / 2.985 mW** (<1.7 mA / 3 mW ✓) — boosters add +111 µA, lean Binkley-min bias
- [x] All 28 booster FETs saturated; cascode sources held ~ideal (172 / 1553 mV); CMFB unregressed (CM 0.906 V, CM-step stable, Δdiff≈0)
- [x] Drawn as REAL component symbols (`pmos4/nmos4/res` + wires), ideal VCVS deleted, blocks relabelled, rendered to `report/figures/folded_cascode_gb.svg`

## Phase 5 — Noise + settling closure — DONE 2026-06-28 (one honest near-miss)

Files: `design/current-reuse/folded_cascode_cr{,_ac,_tran,_noise}.asc`, `phase5_results.txt`;
results in `00_spec_table.md` Phase-5 block. **FoM 170.5 dB (PASS)**; only the 25 ns settling
falls ~3 dB short (reaches 78/66 dB at ~26.5 ns).

- [x] **Migrate input to current-reuse** (complementary NMOS + PMOS): top PMOS `Mp1.2/Mp3.2`
  re-wired as a PMOS input pair (gate `Vip/Vin`) → $g_m=g_{mN}+g_{mP}=12.45$ mS on one branch.
  PMOS in moderate inversion ($V_{sg}=0.6$, input CM = 1.2 V). **A₀ 106.7 dB · GBW 272 MHz · PM 88.0°.**
- [x] Power optimisation: **I(Vdd) 1.658 → 1.135 mA, P 2.985 → 2.04 mW (−32 %)** — the current-reuse
  is the lever (input branch ≈halved). $g_m/I_D$-knob (20.4→24) **not needed** — FoM already > 170.
- [x] Differential noise sim, integrate 10 kHz–100 GHz → $V_{n,amp}=209.5\,\mu$V; +kT/C 204 µV →
  $V_{n,tot}=292\,\mu$V → **SNR 66.8 dB ≥ 66 ✓**.
- [x] Transient settling bench (closed-loop diff step, real SC-CMFB CM verified separately):
  $\tau=T_{38.6}-T_{30}=3.29$ ns → **FoM 170.5 dB > 170 ✓**.
- [~] Confirm 25 ns / 78 dB / 66 dB simultaneously — **NEAR-MISS**: A 77.2 / Aβ 62.7 dB at 25 ns;
  full 78/66 at ~26.5 ns. The output is **slew-limited** ($I_{cas}/C_L=27$ V/µs, ~15 ns slew) +
  a residual **gain-booster doublet** (managed by 2× booster bias; lever sweep showed $I_{cas}$↑ and
  $C$↓ both *worsen* it via cascode cap). Full closure → Class-AB output / decoupled sink-cascode
  sizing (documented in `phase5_results.txt` §5, not taken). Reported honestly, not faked.

## Phase 6 — Report & submission (week 7, by 2026-06-28)

**Compulsory page-by-page structure** (PDF p. 11; figure extraction → `../report/README.md`):
1. Title (Name + Student Number + EE4525 2026); **D1** Table of results (`00_spec_table.md`)
2. **D2** Schematic + all node voltages — separate readable sheets for gain-boosters + CMFB
3. **D3** Schematic + all branch currents (same)
4. **D4** Settling plot — $A(t)$ & $A\beta(t)$, $A\beta$ from 0 dB
5. **D5** Noise PSD 10 kHz–100 GHz + integrated value
6. **D6** FoM comparison EE4520 ↔ EE4525 — **required** (we took EE4520; baseline 175.2 dB in `from-ee4520/`)
7. **Short Explanation** (≤ 1 p): explain every aspect of the D4 plot + architecture / sizing (noise incl 1/f + settling) / dominant-noise devices + NEF / biasing
8. **Submit** via **https://edu.nl/3c9tf** — PDF `[StudentNumber].pdf`, ≤ 2 submissions, **click Submit** (confirmation page). Issues → f.sebastiano@tudelft.nl (TAs: A.Gupta-6@, Zenghui.Li@tudelft.nl).

> Aim for **FoM > 170 dB** ($\mathrm{FoM}_{lin} < 9.5\times10^{-18}\,\mathrm{J}$) to pass. See `07_lecturer_clarifications.md` §4–5.

## Risk log (revisit weekly)

| Risk | Mitigation |
|------|------------|
| **Power ceiling (LIVE, razor-thin).** Core 1.55 mA; boosters add current | SC-CMFB 0 µA (Ph-3) + **lean ref-pinned boosters +111 µA (Ph-4 measured) → 1.658 mA / 2.985 mW, still < 1.7 mA / 3 mW** but only 42 µA headroom. Current-reuse (Ph-5) halves the input branch → restores margin (mandatory for FoM anyway). *Lesson:* a **self-biased** booster CMFB mis-lands the cascode-gate CM and balloons the main-amp current to 1.768 mA (breach) — **ref-pinned CMFB** is required, see `10`. |
| **CMFB unstable / kicks CM during settle** (was a Phase-3 risk) | **RESOLVED Phase 3:** SC-CMFB stable (overshoot +0.26 mV), CM-loop $\tau$=4.15 ns ≈ diff settling; continuous $C_C$ path keeps CM loop ~ diff GBW |
| **FoM 168.5 dB < 170 pass line.** Pre-closure at Phase-4 power | ✅ **RESOLVED Phase 5:** current-reuse cut power 2.985 → **2.04 mW**; closure FoM (measured τ 3.29 ns, SNR 66.8) = **170.5 dB > 170 PASS** (`00` Ph-5 block). Did not reach the ~0.3 mW floor (slew binds, below). |
| Single-stage A₀ < 78 dB | ✅ **RESOLVED Phase 4:** real boosters lift un-boosted 55.8 dB → **101.3 dB** (+45.5 dB); 78 dB held with 23 dB margin |
| **25 ns settling slew-limited (LIVE, Phase-5 finding).** Class-A folded output slews at $I_{cas}/C_L$=27 V/µs; ~15 ns of the 25 ns budget is slew + a residual gain-booster doublet → A 77.2 / Aβ 62.7 dB at 25 ns (full 78/66 at ~26.5 ns) | Boosters set to 2× bias (doublet beyond $\omega_u$); $I_{cas}$↑ and $C$↓ both *worsen* it (added cascode cap re-opens the doublet). **Not fully closed** — needs Class-AB output or decoupled sink/cascode sizing (`phase5_results.txt` §4–5). FoM/SNR/power still pass. |
| Noise dominated by kT/C, can't lift SNR | Increase C_in (re-sim power) |
| CMFB unstable | ✅ resolved Phase 3 (SC-CMFB, stable; see row above) |
| Power > 3 mW after meeting specs | Lower (g_m/I_D) on tails, raise (g_m/I_D) on input |
