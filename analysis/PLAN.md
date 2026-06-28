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
> **Verdict:** with a pure SC-CMFB (~0) and **lean boosters (≤~150 µA total)**,
> post-Phase-4 I(Vdd) ≈ **1.55 + 0.15 ≈ 1.7 mA — right at the ceiling**; a generous
> booster bias **breaches** 1.7 mA / 3 mW *before* Phase-5 current-reuse. The margin is
> razor-thin (~9 %). **Actions:** (1) bias the boosters minimally (Binkley min-current
> sizing); (2) re-measure I(Vdd) after *each* block drop-in; (3) if it breaches, pull
> **current-reuse forward** (it halves input-branch current — the dominant term) rather
> than waiting for Phase 5. Current-reuse is in any case now mandatory for FoM (`00`).

- [ ] Build **real SC-CMFB** (settled) per `05_cmfb_design.md` — replaces ideal `E1`
- [ ] CM step response stable, GBW close to diff GBW
- [ ] Verify nothing regressed in differential AC
- [ ] **Re-check I(Vdd) ≤ 1.7 mA after CMFB drop-in** (power-ceiling watch above)

## Phase 4 — Gain-boosting (committed; week 5, by 2026-06-13)

Part of the settled architecture (need 78 dB single-stage) — see `02_topology_choice.md` build plan and **`10_gain_booster_design.md`** (Binkley Fig. 7 template + Ryu improvement, with the figure).

- [ ] Design **real NMOS-cascode booster** first, keep PMOS ideal (Binkley: $0.8\,\omega_u$/70°)
- [ ] Then **real PMOS-cascode booster** (off-path one $0.4\,\omega_u$/60°; cascode-source pole $\ge 2.6\,\omega_u$)
- [ ] Watch booster-induced doublets in settling (keep the doublet beyond $\omega_u$)

## Phase 5 — Noise + settling closure (week 6, by 2026-06-20)

- [ ] Differential noise sim, integrate 10 kHz–100 GHz
- [ ] Add kT/C analytically → check SNR ≥ 66 dB
- [ ] Transient settling: τ from T₃₈.₆dB − T₃₀dB
- [ ] Confirm 25 ns / 78 dB / 66 dB simultaneously
- [ ] **Migrate input to current-reuse** (complementary NMOS + PMOS) for ~2× $g_m/\mu$A — the main power lever (`02_topology_choice.md`, Ryu 2007)
- [ ] Power optimisation pass (current scale-down where slack exists) — guide the pass with the four live FoM knobs ($\eta_{gm},\mathrm{NEF},\eta_{cur},\eta_{vol}$) in `08_power_prediction.md` §6
- [ ] **Candidate knob (from Ph-2):** raise input-pair $g_m/I_D$ from **20.4 → ~24** (weaker inversion) at the same $g_{m,in}=12.2\,\mathrm{mS}$ → $I_{tail}$ 1.20 mA → 1.02 mA, saving **~0.18 mA / ~0.32 mW**. *Gate:* the wider input device drops $f_T$ (Ph-2 $f_T\approx3.7\,\mathrm{GHz}=14\times\mathrm{GBW}$); at $g_m/I_D=24$ verify $f_T$ stays $\gtrsim10\times\mathrm{GBW}$ (~2.6 GHz) and PM/settling don't degrade. Complementary to (not a substitute for) current-reuse.

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
| **Power ceiling breached in Phase 3–4 (LIVE).** Core already at 1.55 mA / 2.78 mW (93 % of ceiling); boosters add ~60–250 µA | Pure SC-CMFB (~0 µA); lean Binkley-min booster bias; re-measure I(Vdd) per block; pull current-reuse forward if breached (`PLAN` Phase-3 entry note) |
| **FoM 168.8 dB < 170 pass line (LIVE).** Pre-closure at Phase-2 power | Current-reuse now **mandatory** (FoM ∝ P): 2.78 mW → ~0.3 mW target lifts FoM → ~178 dB (`00` FoM block) |
| Single-stage A₀ < 78 dB | Switch to gain-boosting (Phase 4); un-boosted ~50–55 dB, boost must add ≥25 dB (in reach) |
| Settling τ > 3.3 ns at affordable power | Increase I_D in input pair / shorten L cascodes (Ph-2: 3.01 ns met at 12.2 mS) |
| Noise dominated by kT/C, can't lift SNR | Increase C_in (re-sim power) |
| CMFB unstable | Slow CMFB pole, add C_cmfb hold cap |
| Power > 3 mW after meeting specs | Lower (g_m/I_D) on tails, raise (g_m/I_D) on input |
