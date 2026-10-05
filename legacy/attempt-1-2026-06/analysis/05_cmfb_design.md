# 05 — Common-mode feedback

EE4520 used an **ideal** CMFB. EE4525 forbids ideal CMFB — you must build one from real components. Two acceptable styles per PDF + `faq.txt`:

> **Decision (settled — `02_topology_choice.md`):** real **switched-capacitor
> CMFB** (Option 1, Ryu 2007 style), replacing the ideal `E1` block in the core.
> CT-CMFB (Option 2) kept as the alternative. The **AC testbench still uses an
> ideal DC-CMFB-with-large-R helper** to set the operating point (allowed,
> `faq.txt`) even though the working CMFB is switched-capacitor.

## Option 1 — Switched-capacitor CMFB (faq-allowed, ideal switches OK) — **BUILT (Phase 3)**

The realized SC-CMFB (`design/cmfb/`) — see `../circuits/cmfb_sc.svg`:

![SC-CMFB schematic](../circuits/cmfb_sc.svg)

```
            φ1                  φ2
   V_out+ ──/ ─── C_CM ─── /────┐
                                 │── V_bcm (control) → gates of Mn5,Mn7 (output-CM sinks)
   V_out- ──/ ─── C_CM ─── /────┘   + continuous C_C from each V_out to V_bcm (hold/sense)
            φ1                  φ2
```

The control node is **`Vbcm`** — the gate of the output-stage bottom NMOS current
sinks `Mn5.2`/`Mn7.2`. The ideal CMFB set `Vbcm = V_CM,out − 0.9 + Vbn`; the real
SC-CMFB reproduces exactly this, with `Vbcm = Vbn = 0.624 V` when `V_CM,out = 0.9 V`.

**Two-cap structure (the key to fast + DC-accurate, ~0 current):**

- **Continuous sense/hold caps $C_C$** (= `C7`, `C8`, **1.25 pF** each): always connected
  `Voutp/Voutn → Vbcm`. Because `Vbcm` is a high-impedance gate, the cap-coupled CM
  charge is *held*, so this path provides CM feedback from DC up to the loop bandwidth
  — this is what makes the CM loop **fast** (≈ diff GBW) and what *holds* the level
  between refreshes. For a differential signal the two $C_C$ inject equal-and-opposite
  charge → `Vbcm` doesn't move → the CMFB is invisible to the differential path.
- **Switched sampling caps $C_{CM}$** (= `Cs1`, `Cs2`, **0.5 pF** each, row 18): on
  $\phi_1$ each is charged between $V_{cmr}=0.9$ V and $V_{bn}=0.624$ V (stored
  $0.276$ V); on $\phi_2$ it is placed `Vout → Vbcm` in parallel with $C_C$, which
  **refreshes the DC operating point** of `Vbcm` each cycle (per-cycle charge-transfer
  fraction $C_{CM}/(C_{CM}+C_C)\approx0.17$ → CM converges in ≈ 5–6 clock cycles).

**Switches:** 8 ideal voltage-controlled switches, `.model SWCM SW(Ron=10 Roff=1e9
Vt=0.9 Vh=0)` (ideal switches allowed for SC-CMFB, `faq.txt`). **Clock:** non-overlapping
two-phase at **20 MHz** ($\phi_1$ sample/reset, $\phi_2$ amplify). $V_{cmr}=0.9$ V is
an ideal reference (bias class), the bias plate ties to the existing `Vbn`.

**Static current added: 0** — clocks draw 0 A, the only DC element is the weak helper
(≈ 0.5 pA through 100 MΩ). $I(V_{dd})$ stays **1.547 mA** (= Phase-2). Power ceiling held.

**Pros:** noiseless at DC, no resistive loading of output, ~0 static current.
**Cons:** needs a clock; cannot be `.ac`-simulated (sampled loop) → use the weak DC
helper below for the OP-point and differential-AC runs (`faq.txt`).

### The weak ideal-DC helper (OP/AC only)

A switched-cap loop is a sampled system → it cannot be linearised for `.ac`, and at
DC its caps give `Vbcm` no defined operating point. So a **weak parallel ideal-DC
CMFB** is kept: a behavioural source senses the **true** output CM and drives `Vbcm`
*through* a large series resistor — `Bhelp Vh 0 V=V(vcmavg)-0.9+V(Vbn)` (where
`vcmavg` is the large-`R1,R2` output average) and `Rhelp Vh Vbcm 100Meg`. Because
`Vbcm` draws no DC current, `Rhelp` drops 0 V → the **DC bias is set exactly** (output
CM = **0.900 V**, `Vbcm = Vbn`), but the helper's correction bandwidth is
$1/(2\pi R_{help}C_{Vbcm})\approx 0.6$ kHz $\ll$ signal band. It defines the
`.op`/`.ac` bias point only; **all in-band CM correction
is done by the real SC network** (verified in transient).

## Option 2 — Continuous-time CMFB (resistive average + diff-pair sense)

```
   V_out+ ── R ──┐
                  ├── V_avg ── + diff pair ── error → bias
   V_out- ── R ──┘                     − ref V_cm
```

- $R$ must be a few MΩ (faq) to avoid loading output.
- Noise of $R$ should generally be included (verify with TA — may be OK to set noiseless if used only as sense element).

**Pros:** one analog block; simple.
**Cons:** extra current branch, $R$-noise, $R$-loading at high freq.

## Required CMFB performance — vs. achieved (Phase 3)

| Requirement | Target | Achieved (SC-CMFB) |
|---|---|---|
| CM-loop bandwidth (track CM during settle) | same order as diff loop | $\tau_{cm}=4.15\,\mathrm{ns}$, $f_{cm}\approx38\,\mathrm{MHz}$ ≈ diff $f_u=52.9\,\mathrm{MHz}$ ✓ |
| Stability (CM step) | no ringing, PM ≥ 60° | settles, overshoot **+0.26 mV**, no oscillation ✓ |
| Output CM accuracy | 0.9 V | **900.4 mV** (helper trims residual to 0.9 V) ✓ |
| Static current added | ~0 (power ceiling) | **0 mA** (clocks 0 A); $I(V_{dd})=1.547$ mA unchanged ✓ |
| Differential A0/GBW/PM unregressed | = Phase 2 | 93.81 dB / 264 MHz / 89° (Δ ≈ 0) ✓ |

> Note: a pure SC-CMFB cannot be `.ac`-analysed (sampled loop), so CM-loop bandwidth
> and stability are characterised in **transient** (the CM-step test), not by an `.ac`
> loop-gain Bode. The continuous $C_C$ path makes the small-signal CM loop effectively
> continuous-time, hence the ~4 ns response comparable to the differential settling.

## Done (Phase 3, 2026-06-28)

- [x] Pick CMFB style → **switched-capacitor** (Option 1), control node `Vbcm`
- [x] Size caps: $C_{CM}=0.5$ pF (switched) + $C_C=1.25$ pF hold/sense each side
- [x] Add the weak ideal-DC helper (behavioural `Bhelp` true-CM sense + `Rhelp=100\,\mathrm{M\Omega}`) for OP/AC (`faq.txt`)
- [x] Drew the whole SC-CMFB as **real component symbols** (switches/caps/sources/`Bhelp`/`Rhelp`), no SPICE text-directive elements, honest box labels, pruned the artifact `Voutp2` `.meas` (CLAUDE.md schematic hygiene)
- [x] OP-point: all 17 FETs saturated, output CM = 0.9 V, $I(V_{dd})=1.547$ mA
- [x] CM step response stable (no ringing), CM-loop BW ≈ diff GBW (`folded_cascode_cmfb_tran.asc`)
- [x] Differential AC unregressed vs Phase 2 (`folded_cascode_cmfb_ac.asc`, Python extraction)
- [x] CircuiTikZ schematic drawn → `../circuits/cmfb_sc.svg`

Full numbers + run log: `../design/cmfb/phase3_results.txt`.
