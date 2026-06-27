# EE4525 Project plan & phasing

Today: **2026-05-09** | Due: **Sun 28 Jun 2026, 23:59** → ~7 weeks.

> TA clarifications collected in `07_lecturer_clarifications.md` (1/f-noise model,
> ringing/$\tau$ rule, Deliverable-4 plot, FoM, single supply, submission).

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

## Phase 2 — Core amplifier sizing (weeks 2–3, by 2026-05-30)

- [ ] First-cut sizing in `03_sizing_calcs.md` (g_m/I_D method)
- [ ] Open-loop AC sim in `simulations/ac/` → confirm A₀ ≥ 78 dB, GBW
- [ ] OP-point sweep → all transistors saturated, V_DS,sat margins ≥ 100 mV
- [ ] Iterate sizing until A₀, GBW, P all in spec with ideal CMFB

## Phase 3 — CMFB (week 4, by 2026-06-06)

- [ ] Build SC or CT CMFB per `05_cmfb_design.md`
- [ ] CM step response stable, GBW close to diff GBW
- [ ] Verify nothing regressed in differential AC

## Phase 4 — Gain-boosting if needed (week 5, by 2026-06-13)

- [ ] Decide go/no-go based on Phase 2 A₀
- [ ] If go: design NMOS booster first, keep PMOS ideal
- [ ] Then PMOS booster
- [ ] Watch for booster-induced doublets in settling

## Phase 5 — Noise + settling closure (week 6, by 2026-06-20)

- [ ] Differential noise sim, integrate 10 kHz–100 GHz
- [ ] Add kT/C analytically → check SNR ≥ 66 dB
- [ ] Transient settling: τ from T₃₈.₆dB − T₃₀dB
- [ ] Confirm 25 ns / 78 dB / 66 dB simultaneously
- [ ] Power optimisation pass (current scale-down where slack exists)

## Phase 6 — Report & submission (week 7, by 2026-06-28)

Deliverables (per PDF):
1. Table of results (`00_spec_table.md` finalized)
2. Schematic with all node voltages (`report/`)
3. Schematic with all branch currents (`report/`)
4. Settling accuracy vs time plot
5. Output noise PSD vs frequency + integrated value
6. ≤ 1-page design-process write-up
7. FoM comparison vs EE4520 (step-by-step) — **required** (we took EE4520; reference results in `from-ee4520/baseline-amplifier-hw2/report/`)
8. Submit via form **https://edu.nl/3c9tf** — report PDF named `[StudentNumber].pdf`, ≤ 2 submissions, **click Submit** (wait for confirmation page). Also fill the results table in the form. Issues → f.sebastiano@tudelft.nl.

> Aim for **FoM > 170 dB** ($\mathrm{FoM}_{lin} < 9.5\times10^{-18}\,\mathrm{J}$) to pass. See `07_lecturer_clarifications.md` §4–5.

## Risk log (revisit weekly)

| Risk | Mitigation |
|------|------------|
| Single-stage A₀ < 78 dB | Switch to gain-boosting (Phase 4) |
| Settling τ > 3.3 ns at affordable power | Increase I_D in input pair / shorten L cascodes |
| Noise dominated by kT/C, can't lift SNR | Increase C_in (re-sim power) |
| CMFB unstable | Slow CMFB pole, add C_cmfb hold cap |
| Power > 3 mW after meeting specs | Lower (g_m/I_D) on tails, raise (g_m/I_D) on input |
