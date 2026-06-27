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

Both must be true at $t = 25\,\mathrm{ns}$. The amplifier curve $A(t)$ sits $1/\beta = 12\,\mathrm{dB}$ above the loop curve $A\beta(t)$.

## Simulation setup

Reuse `simulations/transient/transient_baseline.asc` (from EE4520 hw2). Edit:

1. Step-voltage source amplitude → $V_{in,step} = V_{out,target} / 4$ (since $1/\beta = 4$).
2. $C_{load}$ on each output → equal to $C_{in}$ from §04.
3. Replace ideal CMFB with the CMFB chosen in §05.
4. Add a measure block:

```spice
.meas TRAN T30dB  WHEN V(vsettledb)=30
.meas TRAN T386dB WHEN V(vsettledb)=38.6
.meas TRAN tau    PARAM='T386dB-T30dB'
```

Where `vsettledb` is a behavioural source computing the accuracy expression above.

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

## To do

- [ ] Build behavioural source for `accuracy_dB`
- [ ] Confirm $V_{out,max}$ definition matches PDF (fixed, not $V(t)$)
- [ ] Tune sizing in `03_sizing_calcs.md` until $T_{settle} \leq 25\,\mathrm{ns}$ at $78\,\mathrm{dB}$ / $66\,\mathrm{dB}$
- [ ] Capture $\tau$ from `.meas`, log into deliverable table (#7)
