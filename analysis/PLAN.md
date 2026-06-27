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

## Phase 1 — Specs & budget (week 1, by 2026-05-16)

- [ ] Fill `analysis/00_spec_table.md` target column
- [ ] Pick V_out swing → finalise noise budget in `04_noise_budget.md`
- [ ] Solve C_in from kT/C share → freeze C_in, C_fb, C_load
- [ ] Solve g_m,in from GBW → freeze first-cut bias current
- [ ] Topology decision in `02_topology_choice.md`
- [ ] Compute $P_{system}$ floor + first-cut $F_{circuit}$/FoM in `08_power_prediction.md` (target check before sizing)

## Phase 2 — Core amplifier sizing (weeks 2–3, by 2026-05-30)

- [ ] First-cut sizing in `03_sizing_calcs.md` (g_m/I_D method)
- [ ] Open-loop AC sim in `simulations/ac/` → confirm A₀ ≥ 78 dB, GBW
- [ ] OP-point sweep → all transistors saturated, V_DS,sat margins ≥ 100 mV
- [ ] Iterate sizing until A₀, GBW, P all in spec with ideal CMFB

## Phase 3 — CMFB (week 4, by 2026-06-06)

- [ ] Build **real SC-CMFB** (settled) per `05_cmfb_design.md` — replaces ideal `E1`
- [ ] CM step response stable, GBW close to diff GBW
- [ ] Verify nothing regressed in differential AC

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
| Single-stage A₀ < 78 dB | Switch to gain-boosting (Phase 4) |
| Settling τ > 3.3 ns at affordable power | Increase I_D in input pair / shorten L cascodes |
| Noise dominated by kT/C, can't lift SNR | Increase C_in (re-sim power) |
| CMFB unstable | Slow CMFB pole, add C_cmfb hold cap |
| Power > 3 mW after meeting specs | Lower (g_m/I_D) on tails, raise (g_m/I_D) on input |
