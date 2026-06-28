# 09 — Simulation runbook (every sim to run, what each produces)

The consolidated list of **all** simulations needed to execute the project, the
`.meas` each carries, the numbers/figures it produces, and which deliverable it
feeds. Run everything with the **`log018.l` (1/f) model** (`models/README.md`) via
the `ltspice` MCP; tools per `../LTSPICE_TOOLCHAIN.md`. Figures land per
`../report/README.md`.

> **Differential everywhere.** All gain / noise / settling are on the
> **differential** output `V(voutp,voutn)`. Noise must be the differential
> output noise (a common mistake — `faq.txt`, project PDF "common mistakes").

> **β to update.** The baseline `.meas` carry the **EE4520** feedback factor
> (`Abeta = A/9`, `=9`). EE4525 uses $C_{in}{:}C_{fb}=4{:}1 \Rightarrow \beta=C_{fb}/(C_{in}+C_{fb})=1/5$
> (`01_specs_and_budget.md` §1), so replace every hard-coded `9` with **5** (e.g.
> `Abeta = A/5`, `=5`).

## Map: sim → deliverable

| Sim | Testbench (`.asc`) | Analysis | Feeds |
|---|---|---|---|
| **A. DC op-point** | core (`design/core-amp/…`) with `.op` | bias, regions | **D1** (τ inputs), **D2** node V, **D3** branch I, $\eta_{cur}$ (`08`) |
| **B. AC (open-loop, internal)** | `design/cmfb/folded_cascode_cmfb_ac.asc` (`.ac dec 1000 1 100G`) | $A_0$, GBW, PM, GM | **D1** (gain), design verify (*not a required figure*) |
| **C. AC loaded (replica)** | `design/cmfb/folded_cascode_cmfb_ac.asc` | realistic $A$, $A\beta$, BW, PM | **D1**, settling cross-check |
| **D. Transient settling** | `simulations/transient/…` (Phase-2 legacy; real bench Phase 5) | accuracy $A(t)$/$A\beta(t)$, $\tau$ | **D1** (rows 4–7), **D4** plot |
| **E. Noise** | `simulations/noise/…` (Phase-2 legacy; real bench Phase 5) | integrated $V_{n,amp}$, SNR | **D1** (rows 11–12), **D5** plot |

> **Phase-2 legacy benches.** The `simulations/{ac,transient,noise}/*_baseline.asc` files are
> Phase-2 (ideal-CMFB) leftovers, kept for reference only and **marked on-sheet** — do not use
> them for Phase-3+ results. The current AC/op benches are the real-SC-CMFB, verified
> `design/cmfb/folded_cascode_cmfb{,_ac}.asc`; the **real-CMFB noise and settling-transient
> benches are built in Phase 5** on the Phase-4 booster circuit (rows D/E still point at the
> legacy `.asc` until then). The `V(Voutp2,Voutn2)` artifact warning in §C below still applies
> (the current AC bench carries the same loaded replica).

---

## A. DC operating point — `.op`

- **Run:** `run_simulation` on the core → `read_op_point`.
- **Produces:** every node voltage (**D2**), every branch current (**D3**), and the
  region check — **all transistors saturated**, $V_{DS,sat}$ margin $\gtrsim
  100\,\mathrm{mV}$ (`03_sizing_calcs.md`).
- **Acceptance:** all devices in saturation; **`I(Mn4)+I(Mn5) ≥ I(Mn8)`** (folded-cascode
  current rule, `03` / project PDF). Also gives $I(V_{dd})$ → **D1 rows 8–9** power
  (bias on a separate `Vddb` so its current is excluded).

## B. AC open-loop (internal design check) — `.ac dec 1000 1 100G`

- **`.meas`** (from the baseline schematic): `A_DC = mag(V(Voutp,Voutn))@10`;
  `A_DC_dB = 20log10(A_DC)`; `Abeta_DC`; `BW_cl_open when mag(Aβ)=1`; `tau_cl_open
  = 1/(2π·BW)`; `PM = 180 + ph@BW`; `GM`.
- **Produces:** $A_0$ (**must be ≥ 78 dB**, D1 row 3), GBW, phase margin, gain
  margin, $\tau$ cross-check.
- **Note:** this Bode is **not** a required EE4525 figure — it's our internal
  proof of $A_0$/stability. (EE4520 reported it; EE4525 does not.)

## C. AC loaded (replica) — realistic loading

- Same `.meas` but on `V(Voutp2,Voutn2)` with the **replica amplifier** providing
  realistic output loading (the replica mimics the next-stage load). The loaded
  $A$/BW is what actually governs settling.
- **⚠ The `V(Voutp2,Voutn2)` `.meas` is UNRELIABLE — do NOT trust it for
  $A_0$/GBW/PM.** Phase 2 found this loaded node reads ~42 dB (or ~132 dB with
  wrapped phase) at the `at=10` point — a replica/probe artifact, not the real gain.
  Extract $A_0$/GBW/PM instead from the **unloaded** `V(Voutp)−V(Voutn)` by complex
  subtraction in Python ($\beta=1/5$), as done in Phase 2 (also saved to project
  memory). Use the loaded bench only for the *loading effect* (settling cross-check),
  never for the headline gain numbers.
- **Produces:** loaded $A_0$, $A\beta$, BW, PM (via the Python post-processor on the
  unloaded nodes — not the raw `Voutp2` `.meas`).

## D. Transient settling — step response (**Deliverable 4**)

- **Setup:** differential input step `= V_out/4` (closed-loop gain $C_{in}/C_{fb}=4$); behavioural source
  computes settling accuracy $\mathrm{Acc}_{dB}(t)=20\log_{10}(V_{out,max}/(|V(\text{vg})|+1\mathrm{n}))$
  (`06_settling_analysis.md`).
- **`.meas`:** `T30dB when V(vsettledb)=30`; `T386dB when V(vsettledb)=38.6`;
  `tau = T386dB − T30dB` (one $e$-fold = 8.6 dB, `07` §4.2).
- **Produces:** $A(t)$ and $A\beta(t)$ accuracy curves → **D4 plot** (both in one
  figure, $A\beta$ from 0 dB, markers at 25 ns / 78 dB / 66 dB); $T_{settle}$,
  $T_{30}$, $T_{38.6}$, $\tau$ → **D1 rows 4–7**.
- **Acceptance:** at $t=25\,\mathrm{ns}$, $A\beta \ge 66\,\mathrm{dB}$ **and**
  $A \ge 78\,\mathrm{dB}$; first ringing peak **after** 25 ns, ≤ 2 cycles (`07` §2).

## E. Noise — `.noise` differential output (**Deliverable 5**)

- **Setup:** `.noise V(onoise_diff) Vin dec … 10k 100G`, differential output,
  **`log018.l`** so the 1/f tail is captured from 10 kHz.
- **`.meas`:** `NOISERMS integ V(onoise) from 10k to 100G` → $V_{n,amp}$ (**D1 row
  11**). Then **add $kT/C$ by hand** (term 10, from $C_{in}/C_{fb}/C_{load}$ only,
  `04` / `07` §4.1) → $V_{n,tot}$ (**D1 row 12**) →
  $\mathrm{SNR}=20\log_{10}(V_{sig,rms}/V_{n,tot})$ (**must be ≥ 66 dB**, D1 row 1).
- **Produces:** output-noise PSD vs frequency → **D5 plot** (10 kHz–100 GHz, show
  integrated value); the per-device noise breakdown → **dominant noise devices +
  NEF** for D6 (`04` "Report items").

---

## Run order & closure

1. **A (op)** → confirm bias/saturation before anything else.
2. **B/C (AC)** → confirm $A_0 \ge 78\,\mathrm{dB}$, stable, GBW on target.
3. **D (transient)** → confirm 25 ns settling to 78/66 dB; extract $\tau$.
4. **E (noise)** → integrate, add $kT/C$, confirm SNR ≥ 66 dB.
5. Compute **power** ($I(V_{dd})\cdot1.8$) and **FoM** (`00` rows 21–22); compare to
   the `08` prediction; minimise power (Phase 5).

**All four spec lines must hold simultaneously at the same operating point:**
$A_0\!\ge\!78$, $A\beta\!\ge\!66$ @ 25 ns, SNR $\ge\!66$, $P$ minimised. Re-run A–E
after every sizing change. Figures → `../report/README.md`.
