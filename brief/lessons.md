# Lessons from attempt 1 (failed, 3.5) and the passing example (7.5)

Read once at the start. Each line cost real time to learn. Details: `legacy-v1/attempt-1-2026-06/NOTE.md`
and `legacy-v1/attempt-1-2026-06/claude-memory/`.

## Why attempt 1 failed, and what to do instead

1. **A missed hard spec voids the design.** Settling at 25 ns was 77.2/62.7 dB (needed 78/66).
   Close every spec first, then minimise power. Never submit a near-miss.
2. **Gain-boosting is expensive here.** Two folded-cascode boosters plus their CMFBs added current
   without adding input gm, and their pole-zero doublet hurt settling. Only boost if $A_0$ cannot be
   reached otherwise; a two-stage amplifier reaches 80+ dB without boosters.
3. **Class-A slewing ate the settling budget.** 136 µA into 5 pF meant about 15 ns of the 25 ns spent
   slewing. A push-pull (class-AB) output stage decouples slew current from quiescent current; the
   passing design used exactly that. Do not retry class-AB grafted onto a gain-boosted single-stage
   core (oscillation, A0 collapse, input-CM conflicts; see `design/class-ab/class_ab_results.txt`).
4. **Over-built caps.** Cin = 5 pF with 0.9 V swing vs the friend's 3.24 pF with 1.13 V swing. kT/C
   noise scales as $1/C_{in}$ while signal power scales as $V_{out}^2$: use the largest output swing the
   output stage tolerates, then the smallest $C_{in}$ that closes SNR.
5. **Report broke the compulsory structure** (16 pages, contents page, appendices, D2/D3 over 3 pages
   each). Exactly 8 pages, one item per page (`brief/spec.md` section 5).

## What the passing design did right (and where it left power on the table)

- Two-stage: NMOS input pair with NMOS cascodes and cascoded PMOS loads (long L = 1.8 µm for gain
  and 1/f), then a complementary push-pull output stage; Miller Cc 720 fF with nulling Rz 2.8 kΩ, and a
  differential RC damper across the outputs to shape ringing so the first peak lands after 25 ns.
- Continuous-time CMFB: 2 MΩ resistive sensing, small MOS diff pair, weak correction on the
  first-stage nodes so CM correction does not disturb the differential settling.
- 0.690 mA / 1.24 mW, SNR 66.01, A 80.81, Aβ 66.01, τ 2.697 ns: no margin anywhere.
- **Free power left on the table:** Rin/Rfb were 10/40 MΩ and not `noiseless`. Their thermal noise
  was about 77 µV per Rin inside the 326 µV "amplifier" noise (FAQ allows excluding it). Removing it
  frees SNR, which allows smaller Cin, which allows less current.
- The design is knife-edge: Wn 51 µm instead of 58 µm drops Aβ(25 ns) from 66.0 to 41.7 dB. Keep a
  small margin and check the after-deadline floor, not only the value at 25 ns.
- It used E-source probes as text directives and a 1 F "Cbig". Our rules forbid elements typed as
  text; compute probes in `tools/metrics.py` instead.

## Simulation and bench gotchas (all verified)

- LTspice XVII under Wine needs an X display even in batch mode; `tools/lt.py` starts one shared Xvfb
  (`:87`). Wine stderr noise is harmless; judge by return code and output files.
- XVII rejects `.lib "path" TT` with double quotes and the LTspice-24-only `.options logopinfo`;
  `tools/lt.py` fixes both automatically. XVII logs can be UTF-16; `lt.read_text` handles it.
- Never use `-ascii` raw output (attempt 1 produced 130 to 200 MB files). Binary raw + spicelib.
- spicelib 1.6 `get_axis()` raises until a trace is read; `metrics.Raw` reads the axis by name.
- ngspice applies the model's XL/XW but LTspice ignores them: ngspice Id +5.5 %, gds +14 % at
  10u/0.36u. Size with `tools/gmid.py` (LUTs from LTspice itself) or patch XL=XW=0 for ngspice.
- Narrow devices: ID/W drops about 14 % from W = 10 µm to 1 µm (binning, narrow-width effect).
- A0/GBW/PM: read the unloaded differential $V(vop)-V(von)$ with complex subtraction, never a single
  ended node; keep $R_{fb}C_{fb}$ corner far below the frequency you read A0 at.
- A CMFB sim-aid (ideal helper) with high gain and small R latches or oscillates; real CMFB first.
- In a pseudo-differential input (no tail) the current is steeply input-CM sensitive: reproduce the
  `.op` bias in the transient bench before judging slew.
- Gain-booster tuning was non-monotone (1x 62.5 dB, 2x 77.2 dB, 2.5x 59 dB): sweep, do not guess.
- Raising output-branch current for slew backfired in the folded cascode (more cascode capacitance
  reopened the doublet). Measure, then change one knob at a time.
- Exact-time `.meas ... AT=` can be fooled by ringing zero-crossings; use the floor after 25 ns.
- Layout bug in attempt 1: a wire crossing in a crowded column merged a CMFB node with replica wiring
  and faked GBW (CM to differential leak). Keep blocks apart; `verify_circuit` flags wires through bodies.
- Deleting an ideal symbol in an `.asc` leaves its wires and flags behind; they short new parts.
  Clear the region first. LTspice connects a FLAG on a MOSFET bulk pin, but a wire must end exactly
  on the pin.

## Process lessons

- The agent repeatedly declared "done" with numbers it had not re-measured. Only
  `tools/evaluate.py` output counts, quoted verbatim.
- Write failed approaches into `PROGRESS.md` so later sessions do not retry them.
- The user reviews `.asc` files in the LTspice GUI: drawn symbols, real wires, one parameters box,
  no stale labels. Treat a messy schematic as a failed deliverable.
