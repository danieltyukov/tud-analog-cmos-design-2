---
name: ee4525-ac-bench-and-sizing
description: "EE4525 folded-cascode — how to correctly read A0/GBW/PM from the AC benches, and the mirror-ratio sizing structure"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4947e27c-6dc0-4c3b-8d65-dd0daa96a725
---

EE4525 residue amp (`design/core-amp/folded_cascode_baseline.asc` + `simulations/ac/loaded_ac_baseline.asc`).

**AC measurement gotcha (cost several iterations in Phase 2):**
- The loaded bench's `.meas A_DC find mag(V(Voutp2,Voutn2)) at=10` is **unreliable** — the `voutp2/voutn2` node is NOT a clean open-loop gain (reads ~132 dB with wrapped phase; it's a loop-shaped/injection artifact), and `at=10` Hz lands in a region where the two outputs are nearly common-mode so their difference is garbage.
- **Correct method:** post-process the *unloaded* differential gain `A(f)=V(voutp)−V(voutn)` (complex subtraction) from the `.raw`. Script: `scratchpad/ac_metrics.py` (uses `~/tools/spicelib-mcp/.venv/bin/python` + `spicelib.RawRead`; β=1/5). Gives clean A0 (LF plateau), dominant pole, GBW (|A|=1), f_u (|A|=1/β=5), PM=180+∠A(f_u). Bode figure: `scratchpad/bode_plot.py`.
- LTspice `.meas` prints magnitude with a spurious "dB" suffix on a *linear* value — don't trust the label.
- **`Rin`/`Rfb` must stay LARGE for the `at=10` A0 read to be valid.** They're sim-only bias R with `Rfb/Rin = Cin/Cfb = 4`; canonical sim values `Rin=100G`, `Rfb=400G`. The DC-feedback RC corner `1/(2π·Rfb·Cfb) ≈ 0.3 Hz` must sit ≪ the A0 `.meas … at=10` (10 Hz) so capacitive feedback dominates and A0 reads the true ~94 dB, **not** the resistive ~12 dB (`= Rfb/Rin`). A `≤1 GΩ` value pushes the corner to ~127 Hz (> 10 Hz) → corrupt A0. Verified: running the OP file's unloaded bench as `.ac`, `a_dc: mag(v(voutp,voutn)) at 10 = 93.89 dB`. `00_spec_table.md` rows 19/20 document this; `Cbig=1n` is the canonical decoupling value (ideal rail → cosmetic) and is now set in **every EE4525 `.asc`** — the 3 Phase-3 files plus the Phase-2 baseline (`design/core-amp/folded_cascode_baseline.asc`) and its `simulations/{ac,transient,noise}/*_baseline.asc` benches (all re-verified unchanged: baseline loaded-AC A0=93.93 dB, GBW=264 MHz, CM=0.900 V, I(Vdd)=1.547 mA). Only the `from-ee4520/` prior-course archive intentionally keeps the old `Cbig=1000n`.
- The OP device table (gm, Vdsat, region) only prints in the `.op` run `.log`; parse with `scratchpad/parse_op.py`. AC runs don't print it.
- Toggling files: core runs `.op` (line `!.op`); bench runs `.ac` (`!.ac dec 1000 1 100G`). The bench also contains an unloaded replica `V(voutp)/V(voutn)` → use that for clean AC.
- **`folded_cascode_baseline.asc` CANNOT run `.ac`** — enabling its `ac` directive → `Fatal Error: Ac: Missing node(s)` (pre-existing, not CMFB-related). For any differential-AC run, copy `simulations/ac/loaded_ac_baseline.asc` (which works) and graft changes there; that's what `design/cmfb/folded_cascode_cmfb_ac.asc` does. See [[ee4525-sc-cmfb]].

**Mirror-ratio sizing structure (all devices W=1u L=0.18u, integer M):**
- Branch current = `Ibm·M_branch/M_ref`. `Mp`/`Mn` are bias-ref multipliers (set current-source inversion level/Vdsat); `Ibm=350u`, `Rn`/`Rp` set bias branch currents.
- Fold-node KCL: `Mp13 = (Mp/Mn)·(Mn12/2 + Mn78)` (I_top = I_tail/2 + I_out) — must hold or output CM rails.
- Input pair gm/Id is set **independently** by `Mn34` (its current comes from the tail `Mn12`, not a direct mirror).
- In weak inversion gm∝Id, so raise gm mainly via tail current (`Mn12`), widen `Mn34` together to hold gm/Id (≈20) and keep input Vgs low for tail headroom.
- Wide-swing tail/sink/source devices sit at 52–85 mV Vds,sat margin — **intrinsic** on 1.8 V, density-independent (the wide-swing reference tracks Vdsat); all stay saturated. Don't chase 100 mV there.

Phase-2 frozen result: A0=93.9 dB, GBW=264 MHz, PM=89°, τ=3.01 ns, gm,in=12.2 mS, I(Vdd)=1.55 mA/2.78 mW (with ideal CMFB+boost). See [[circuit-sim-tooling]].
