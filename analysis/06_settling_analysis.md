# 06 — Settling analysis (deliverable 4 + $\tau$ extraction)

## Definition (from project PDF)

$$\mathrm{Accuracy}_{dB} = 20 \log_{10}\!\left(\frac{V_{out,max}}{|V(\text{virtualground})| + 1\,\mathrm{nV}}\right)$$

Where $V_{out,max}$ is a **fixed** number (the target output settled value), NOT $V_{out}(t)$. The $1\,\mathrm{nV}$ avoids $\log(0)$.

## Time constant from two settling points

$$\tau = T_{38.6\,\mathrm{dB}} - T_{30\,\mathrm{dB}}$$

($38.6\,\mathrm{dB} \approx 1/85$, $30\,\mathrm{dB} = 1/31.6$ — the difference is one $e$-fold of an exponential.)

## Ringing & a *fair* $\tau$ (two-stage architectures)

TA clarification (`07_lecturer_clarifications.md` §2): a two-stage amplifier may
**ring** during settling. For the $\tau$ extraction to be fair:

- The **first significant peak** of the settling/ringing response — the main-loop
  transient near the dominant pole — must appear **after $25\,\mathrm{ns}$**, i.e.
  past the required settling time. (Don't let the loop ring faster than spec.)
- **Up to two cycles** of ringing are acceptable **provided** the output still
  meets the required settling accuracy ($A\beta \geq 66\,\mathrm{dB}$ and
  $A_{settle} \geq 78\,\mathrm{dB}$ at $25\,\mathrm{ns}$).

## Spec compliance

| Time   | Required accuracy            |
|--------|------------------------------|
| 25 ns  | $A\beta \geq 66\,\mathrm{dB}$ |
|        | $A_{settle} \geq 78\,\mathrm{dB}$ |

Both must be true at $t = 25\,\mathrm{ns}$. The amplifier curve $A(t)$ sits $20\log_{10}(C_{in}/C_{fb}) = 12\,\mathrm{dB}$ above the loop curve $A\beta(t)$ — the plot labels this gap "$1/\beta$", but it is the **closed-loop gain** $C_{in}/C_{fb}=4$ (the true loop $\beta = 1/5$; see `01_specs_and_budget.md` §1).

## Simulation setup

Reuse `simulations/transient/transient_baseline.asc` (from EE4520 hw2). Edit:

1. Step-voltage source amplitude → $V_{in,step} = V_{out,target} / 4$ (since the closed-loop gain $C_{in}/C_{fb} = 4$).
2. $C_{load}$ on each output → equal to $C_{in}$ from §04.
3. Replace ideal CMFB with the CMFB chosen in §05.
4. Add a measure block. The accuracy can be thresholded **inline** (no separate
   behavioural source needed) — a peer's working LTSpice block, generalised:

```spice
* --- τ from two settling thresholds (one e-fold apart) ---
* AccuracydB(t) here = A(t), the raw amplifier accuracy at the summing node.
* Subtract OFFSET (the measured t=0 value, ≈ 1/β in dB) to reference it to Aβ.
.meas TRAN T30dB   WHEN (20*log10(Vout_max/(abs(V(virtualground))+1n)))-OFFSET=30    RISE=1
.meas TRAN T3869dB WHEN (20*log10(Vout_max/(abs(V(virtualground))+1n)))-OFFSET=38.69 RISE=1
.meas TRAN tau     PARAM='T3869dB-T30dB'

* --- ringing-robust settling time: rise 66 dB above the curve's own min, LAST crossing ---
.meas TRAN vdbaMin MIN  V(vdba) FROM 0 TO 5n
.meas TRAN Tsettle TRIG V(in)=0.1 RISE=1 TARG V(vdba)=66+vdbaMin RISE=LAST

* --- average power over a LATE steady-state window (not from t=0); mind the sign ---
.meas TRAN avg_pow AVG (-1.8*I(Vdd)) FROM 100n TO 190n
.meas TRAN idd_avg AVG I(Vdd)        FROM 100n TO 190n
```

`Vout_max` is the fixed target output (a peer used $1.6\,\mathrm{V}$); `OFFSET`
is the measured $t=0$ value of the raw expression (a peer's netlist used
`13.6534471512`). The two thresholds are **30** and **38.69 dB** — they differ by
$8.69\,\mathrm{dB} = 20\log_{10}e$, i.e. exactly one $e$-fold, so $\tau =
T_{38.69} - T_{30}$ is one time constant (`38.69` is the precise e-fold; the
$38.6$ used in the section above is a rounding of the same thing). `RISE=LAST`
makes `Tsettle` immune to ringing (takes the last threshold crossing).

## Deliverable plot (4)

TA requirements (`07_lecturer_clarifications.md` §3): **both curves in the same
figure**, and the **$A\beta$ curve must start at exactly 0 dB** at $t = 0$.

Two curves on one axis:
- $A(t)$ = amplifier accuracy (purple in PDF example)
- $A\beta(t)$ = loop accuracy (yellow) — **starts from 0 dB**

Vertical lines at $25\,\mathrm{ns}$; horizontal lines at $78\,\mathrm{dB}$ and $66\,\mathrm{dB}$. Mark the $1/\beta$ gaps.

> **Actual vs. ideal $\beta$:** the extracted $\beta$ is normally a little **higher**
> than ideal (input-pair parasitics add to the divider); if it comes out **lower**,
> something is wrong. Explain this in the report (`01_specs_and_budget.md` §1).

### Making $A\beta$ start at exactly 0 dB — the offset trick

> **Peer-sourced (course group chat — not an official TA announcement). This is
> the step people most often get wrong.** Verify the numbers against your design.

The accuracy expression measured at the summing node behaves as the **amplifier**
curve $A(t)$. To get the **loop** curve $A\beta(t)$ that "starts at exactly 0 dB",
don't just assume $1/\beta = 12\,\mathrm{dB}$ — **measure your actual offset and
subtract it**:

1. At $t = 0$ the raw expression evaluates to a small non-zero value set by the
   input capacitive divider plus input-pair parasitics — typically
   $\approx 12\text{–}16\,\mathrm{dB}$, a little **above** the ideal
   $1/\beta = 12\,\mathrm{dB}$. A peer's working netlist measured
   $13.6534471512\,\mathrm{dB}$.
2. Subtract that constant inside the expression (the `OFFSET` in the `.meas`
   block above). Now $A\beta(t)$ starts at $0\,\mathrm{dB}$ and
   $A(t) = A\beta(t) + \text{OFFSET}$ sits the offset above it.
3. **Spec mapping (resolves the recurring "66 vs 78" confusion):** the *raw*
   curve $A(t)$ must exceed $\mathbf{78\,\mathrm{dB}}$ at $25\,\mathrm{ns}$; the
   *offset* curve $A\beta(t)$ must exceed $\mathbf{66\,\mathrm{dB}}$. They differ
   by exactly the offset you measured.

### Measuring $A\beta$ open-loop (the AC / loop-gain plot)

Break the loop on the open-loop ("CMOS I") schematic by inserting a
**$1\,\mathrm{TH}$ (terahenry) inductor** between the amplifier input and the
feedback network: a $1\,\mathrm{TH}$ inductor is a short at DC (bias point
preserved) and an open at AC (loop broken). Then $\mathrm{mag}(V(ab))$ is
$A\beta$, and the loop unity-gain crossover is:

```spice
.meas AC Freq_0dB FIND frequency WHEN mag(v(ab))=1 FALL=1
```

### Gotcha — the accuracy curve is non-monotonic

After settling, the accuracy curve **peaks then droops** (in the shared example:
peak $\approx 125\,\mathrm{dB}$ near $60\,\mathrm{ns}$, drifting back to
$\approx 110\,\mathrm{dB}$ by $90\,\mathrm{ns}$) because of slow leakage / CM
drift through $R_{fb}$. **Read the spec at the $25\,\mathrm{ns}$ line** and use
`RISE=1` (first crossing) in the `.meas`; ignore the post-settle droop.

## To do

- [ ] Build behavioural source for `accuracy_dB`
- [ ] Confirm $V_{out,max}$ definition matches PDF (fixed, not $V(t)$)
- [ ] Tune sizing in `03_sizing_calcs.md` until $T_{settle} \leq 25\,\mathrm{ns}$ at $78\,\mathrm{dB}$ / $66\,\mathrm{dB}$
- [ ] Capture $\tau$ from `.meas`, log into deliverable table (#7)
