# 08 — Power prediction & efficiency budget (Bult method)

Top-down companion to the bottom-up sizing files. Files `03`/`04`/`06` go
*forward* (pick caps from noise → pick $g_m$ from GBW → check settling → read off
power). This file goes *backward*: from the spec alone it computes a **power
floor** $P_{system}$ and an **efficiency multiplier** $F_{circuit}$, so you know
the power a "perfect" implementation of this spec would burn **before** sizing a
single transistor — and exactly which knobs to turn to approach it.

> **Source:** EE4525 lecture *"Predicting Analog Power Dissipation"* (Klaas Bult
> discrete-time-amplifier efficiency & noise method). The lecture builds one
> chain: $\text{settling spec} \to g_m \to I_d \to (\text{noise sets } C_L) \to
> P_{supply}$. Every non-ideality enters as an **efficiency factor**
> ($\eta_{gm}, \eta_{cur}, \eta_{vol}, \mathrm{NEF}, F_{supply}$).

Related: `00_spec_table.md` (rows 8–9 power, 21–22 FoM), `01_specs_and_budget.md`
(§3 settling, §4 noise, §5 power feel), `04_noise_budget.md` (NEF, SC noise),
`06_settling_analysis.md` ($\tau$), `07_lecturer_clarifications.md` §4.2 (FoM).

---

## 1. The design chain

$$\underbrace{N_{settle}, A_{req}, C_L}_{\text{settling}} \;\to\; g_m
\;\to\; I_d \;\xleftarrow{\;C_L\;} \underbrace{\mathrm{SNR},\,\mathrm{NEF},\,V_{dd},\,\eta_{vol}}_{\text{noise sets }C_L}
\;\to\; I_{supply} \;\to\; P_{supply}$$

- **Settling → $g_m$:** single-pole settling to accuracy $DR$ after the
  amplification half-period needs $N_{settle} = \ln(DR) = (T_{clk}/2)/\tau_{cl}$
  time constants, giving $g_m = 2\,N_{settle}\,F_{clk}\,A_{req}\,C_L$.
- **$g_m$ → $I_d$:** the generic transconductance $g_m = 2 I_d / V_{gt}$ holds in
  all inversion regions ($V_{gt} = V_{gs}-V_{th}$ in SI; $V_{gt} = 2nkT/q$ in deep
  WI). So $I_d = g_m \cdot V_{gt}/2$.
- **Noise → $C_L$:** integrated output noise is $kT\,A_{req}/C_L$ (the $kT/C$
  result), so meeting the SNR budget sets a **minimum** $C_L$.
- **$I_d$ → $P_{supply}$:** current efficiency $\eta_{cur} = I_{device}/I_{supply}$
  and $P_{supply} = I_{supply} V_{dd}$.

---

## 2. $P_{system}$ — the implementation-independent floor ⭐

$$\boxed{P_{system} = 32\,kT\,F_{clk}\,A_{req}^2\,DR^2}$$

Determined by **system specs only** — no circuit choice can beat it; real circuits
only make it worse. For this project:

| Quantity | Value | Source |
|---|---|---|
| $kT$ (300 K) | $4.142\times10^{-21}\,\mathrm{J}$ | — |
| $F_{clk}$ | $20\,\mathrm{MHz}$ | $T_{settle}=T_{clk}/2=25\,\mathrm{ns}$, 20 MS/s ÷ 50 % duty |
| $A_{req}=C_{in}/C_{fb}$ | $4$ | residue gain $2^2$ (`01` §1) |
| $DR=\mathrm{SNR}$ | $66\,\mathrm{dB}\Rightarrow 1995$ | `00` row 1 |

$$P_{system} = 32\,kT\,(20\,\mathrm{MHz})(4)^2(1995)^2 \approx \mathbf{0.169\,mW}$$

> **Why $DR=66\,\mathrm{dB}$ does double duty here.** In Bult's framework $DR$
> appears *twice*: as the **settling accuracy** (→ $N_{settle}=\ln DR$) and as the
> **noise dynamic range** (→ $C_L$). This project happens to set *both* the loop
> settling accuracy $A\beta$ and the SNR target to $66\,\mathrm{dB}$, so a single
> $DR=1995$ feeds both. $N_{settle}=\ln(1995)=7.60$, hence
> $\tau_{cl}=T_{settle}/N_{settle}=25/7.60=3.29\,\mathrm{ns}$ — identical to
> `01_specs_and_budget.md` §3.

---

## 3. $F_{supply}$ — the supply lever

$$F_{supply} = \frac{V_{dd}}{nkT/q} = \frac{1.8\,\mathrm{V}}{41.4\,\mathrm{mV}} \approx 43.5
\qquad (n\approx1.6,\;\; nkT/q \approx 41.4\,\mathrm{mV at }300\,\mathrm{K})$$

A supply taller than $nkT/q$ makes the real power **better** by $F_{supply}^{-1}$.
The single-rail $1.8\,\mathrm{V}$ constraint (`07` §5.1) fixes this at $43.5$ — we
cannot push it further, so the *only* remaining freedom is $F_{circuit}$.

A loose best-case estimate is $P_{system}/F_{supply} = 0.169\,\mathrm{mW}/43.5
\approx 3.9\,\mu\mathrm{W}$, but $F_{circuit}\!\ge\!1$ always (see below), so treat
this as a floor, not a target.

---

## 4. $F_{circuit}$ — the circuit Figure-of-Merit, and the 6 knobs ⭐⭐

$$\boxed{P_{supply} = P_{system}\cdot\frac{F_{circuit}}{F_{supply}}},\qquad
F_{circuit} = \tfrac12\,\eta_{gm}^{-1}\,\frac{N_{settle}\,\mathrm{NEF}}{\eta_{cur}\,\eta_{vol}^2}$$

$F_{circuit}$ isolates *exactly what to improve* for a fixed spec. The six factors
and how **this project's** chosen levers move each one:

| Factor | Expression | Directive | This project's lever |
|---|---|---|---|
| $\eta_{gm}$ | $\dfrac{2nkT}{qV_{gt}}$ | bias **weak/moderate inversion** ($V_{gt}$ small) | input pair at $g_m/I_D \approx 12$–$18$ (`03`); $\eta_{gm}\to1$ as $V_{gt}\to 2nkT/q$ |
| $N_{settle}$ | $\dfrac{T_{clk}}{2\tau_o}=\ln DR$ | **less settling** (accuracy-limited) | fixed at $7.60$ by the $66\,\mathrm{dB}$ accuracy — *not* a free knob here |
| $\mathrm{NEF}$ | $\dfrac{\text{main}+\text{extra}}{\text{main}}$ | **avoid current-source / resistive loads** | SC-CMFB (noiseless at DC), cascode loads, large $WL$ for $1/f$ (`04`) |
| $\eta_{cur}$ | $\dfrac{I_{device}}{I_{supply}}$ | **current re-use, avoid current-mirrors** | complementary (NMOS+PMOS) **current-reuse input** — Ryu 2007 (`../reserach-papers/`) |
| $\eta_{vol}$ | $\dfrac{V_{sig,pp}}{V_{dd}}$ | **maximise signal swing** | output CM at $0.9\,\mathrm{V}$ (mid-rail), relaxed $66\,\mathrm{dB}$ SNR buys swing slack |
| $F_{supply}$ | $\dfrac{V_{dd}}{nkT/q}$ | **highest $V_{dd}$** | pinned at $1.8\,\mathrm{V}$ single rail (`07` §5.1) |

> Two knobs are **locked** by the spec/rules ($N_{settle}=7.60$, $F_{supply}=43.5$).
> The grade is won on the other four: **$\eta_{gm}$ (WI bias), NEF (clean loads),
> $\eta_{cur}$ (current reuse), $\eta_{vol}$ (swing)** — precisely the levers the
> two reference papers target.

---

## 5. Predicted amplifier power (pre-sizing estimate)

With first-cut efficiency guesses for the target architecture (single-stage
gain-boosted cascode + current-reuse input + SC-CMFB) — **refine after sizing:**

| $\eta_{gm}$ | NEF | $\eta_{cur}$ | $\eta_{vol}^2$ | $\Rightarrow F_{circuit}$ | $\Rightarrow P_{supply}$ |
|---:|---:|---:|---:|---:|---:|
| $0.6$ | $1.5$ | $0.5$ | $0.49$ | $38.8$ | $\approx 0.15\,\mathrm{mW}$ |

$$P_{supply} = 0.169\,\mathrm{mW}\cdot\frac{38.8}{43.5} \approx \mathbf{0.15\,mW}$$

Comfortably under the $3\,\mathrm{mW}$ ceiling and consistent with the "best
designs drop below $0.3\,\mathrm{mW}$" note in `01` §5. This is the number to beat
when the real sizing lands; track the achieved $P$ against it in `00` row 8.

---

## 6. The clean FoM identity ⭐⭐⭐ — what actually moves your grade

Feed the master relation into the graded FoM
($\mathrm{FoM}_{lin}=2\pi\,P\,\tau/\mathrm{SNR}_{lin}^2$, `00` rows 21–22 / `07`
§4.2). Using $P=P_{system}F_{circuit}/F_{supply}$,
$\tau=T_{settle}/N_{settle}=1/(2F_{clk}N_{settle})$, and
$P_{system}=32kT\,F_{clk}A_{req}^2\,\mathrm{SNR}^2$, the **$\mathrm{SNR}^2$,
$F_{clk}$, and $N_{settle}$ all cancel:**

$$\boxed{\;\mathrm{FoM}_{lin} = \frac{16\pi\,kT\,A_{req}^2\,\mathrm{NEF}}
{\eta_{gm}\,\eta_{cur}\,\eta_{vol}^2\,F_{supply}}\;}$$

This is the most useful single result for the project. It says the graded FoM
depends **only** on: the residue gain $A_{req}=4$ (fixed), the supply lever
$F_{supply}=43.5$ (fixed), and **four circuit efficiencies** —
$\mathrm{NEF},\eta_{gm},\eta_{cur},\eta_{vol}$. It does **not** depend on SNR,
clock rate, or settling time. So:

- Chasing extra SNR or extra speed **does not improve the FoM** — it only spends
  power (matches the "don't over-design" rule, `07` §5.2).
- The FoM is won purely by **clean loads (low NEF), WI bias (high $\eta_{gm}$),
  current reuse (high $\eta_{cur}$), and full swing (high $\eta_{vol}$).**

Plugging the §5 estimates: $\mathrm{FoM}_{lin}\approx7.8\times10^{-19}\,\mathrm{J}
\Rightarrow \mathrm{FoM}_{dB}=-10\log_{10}(\mathrm{FoM}_{lin})\approx
\mathbf{181\,dB}$ — above the $>170\,\mathrm{dB}$ pass target (`07` §5.4) and in
line with the EE4520 baseline of $175.2\,\mathrm{dB}$ (`../from-ee4520/README.md`).

> **Factor-of-2 caveat.** The lecture's "project working forms" (summary slide)
> carry an extra factor of $2$ versus the $F_{circuit}$-chain above, from the
> single-device-vs-differential $g_m$ convention ($g_{m,diff}=\tfrac12 g_{m,device}$).
> Pin down *your* convention when you plug raw simulator currents in — the same
> caution `04` makes about its topology-specific $kT/C$ prefactor.

---

## 7. SC-amplifier noise refinement (feeds `04`)

The lecture's discrete-time SC analysis gives a **unified** output-noise
expression that folds sampling ($kT/C$) and amplifier noise into one form. With
SC gain $\text{Gain}=C_{in}/C_{fb}=4$ ($=A_{req}$, the residue gain; the feedback
factor $\beta=C_{fb}/(C_{in}+C_{fb})$ gives $1/\beta=1+\text{Gain}=5$, the noise
gain) and $C_L=C_{in}=\text{Gain}\cdot C_{fb}$:

$$\overline{V_{n,out,tot}^2} = \underbrace{\frac{kT}{C_{fb}}(\text{Gain}+1)}_{\text{sampling }(kT/C)}
\Bigl(1 + \frac{\mathrm{NEF}}{\text{Gain}}\Bigr)$$

The **left term is sampling noise** (Deliverable-1 term 10 — includes only
$C_{in},C_{fb},C_{load}$, per `07` §4.1), the **right factor $1+\mathrm{NEF}/\text{Gain}$
is the amplifier's contribution** (term 11), and the product is the **total**
(term 12). Key takeaways for `04`:

- **NEF scales the amplifier-noise share directly**, hence $C_L$, hence power
  ($C_L=8kT\,\mathrm{NEF}\,DR^2 A_{req}/(V_{dd}^2\eta_{vol}^2)$). Every avoidable
  noise source you remove (current-source loads, resistive CMFB) buys back $C_L$
  and current — the same reason NEF is the hardest factor to estimate and the one
  most worth fighting.
- The higher the SC gain, the **smaller** the relative amplifier-noise penalty
  ($\mathrm{NEF}/\text{Gain}$) — but our Gain is fixed at $3$ by the residue ratio.
- The exact prefactor is **topology-specific** — `04` adopts
  $2(1/\beta)^2\,kT/C_{in}$ for the differential sampled term; this lecture form is
  a cross-check on the *structure*, not a competing number. Derive your own
  prefactor (as `04` already warns about the peer's $10\,kT/C_{fb}$).

---

## 8. How to close this file (after sizing)

- [ ] Read back $V_{gt}$ (or $g_m/I_D$) of the input pair → compute actual
      $\eta_{gm}$.
- [ ] From the `.noise` per-device contributions (`04`) → estimate actual NEF.
- [ ] From branch currents (Deliverable 3) → actual $\eta_{cur}=I_{device}/I_{supply}$.
- [ ] From the chosen output swing → actual $\eta_{vol}=V_{sig,pp}/V_{dd}$.
- [ ] Recompute $F_{circuit}$, predicted $P_{supply}$, and the FoM identity;
      compare to the **simulated** $P$ (`00` row 8) and **measured** FoM
      (`00` rows 21–22). Discrepancy = a non-ideality the efficiency model
      missed — name it in the Deliverable-9 write-up (`07` §5.8).
