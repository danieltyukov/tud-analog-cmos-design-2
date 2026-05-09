# 06 — Settling analysis (deliverable 4 + $\tau$ extraction)

## Definition (from project PDF)

$$\mathrm{Accuracy}_{dB} = 20 \log_{10}\!\left(\frac{V_{out,max}}{|V(\text{virtualground})| + 1\,\mathrm{nV}}\right)$$

Where $V_{out,max}$ is a **fixed** number (the target output settled value), NOT $V_{out}(t)$. The $1\,\mathrm{nV}$ avoids $\log(0)$.

## Time constant from two settling points

$$\tau = T_{38.6\,\mathrm{dB}} - T_{30\,\mathrm{dB}}$$

($38.6\,\mathrm{dB} \approx 1/85$, $30\,\mathrm{dB} = 1/31.6$ — the difference is one $e$-fold of an exponential.)

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

Two curves on one axis:
- $A(t)$ = amplifier accuracy (purple in PDF example)
- $A\beta(t)$ = loop accuracy (yellow)

Vertical lines at $25\,\mathrm{ns}$; horizontal lines at $78\,\mathrm{dB}$ and $66\,\mathrm{dB}$. Mark the $1/\beta$ gaps.

## To do

- [ ] Build behavioural source for `accuracy_dB`
- [ ] Confirm $V_{out,max}$ definition matches PDF (fixed, not $V(t)$)
- [ ] Tune sizing in `03_sizing_calcs.md` until $T_{settle} \leq 25\,\mathrm{ns}$ at $78\,\mathrm{dB}$ / $66\,\mathrm{dB}$
- [ ] Capture $\tau$ from `.meas`, log into deliverable table (#7)
