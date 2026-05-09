# 05 — Common-mode feedback

EE4520 used an **ideal** CMFB. EE4525 forbids ideal CMFB — you must build one from real components. Two acceptable styles per PDF + `faq.txt`:

## Option 1 — Switched-capacitor CMFB (faq-allowed, ideal switches OK)

```
            φ1                  φ2
   V_out+ ──/ ─── C_cmfb ─── /────┐
                                   │── V_cmfb,ctrl → bias of M_tail or load
   V_out- ──/ ─── C_cmfb ─── /────┘
            φ1                  φ2
```

- $C_{cmfb}$ capacitors sample $(V_{out,+} - V_{cm,ref})$ and $(V_{out,-} - V_{cm,ref})$ on $\phi_1$.
- On $\phi_2$ they share charge with a hold capacitor → produces $V_{cmfb,ctrl}$ set to $(V_{out,+} + V_{out,-})/2 - V_{cm,ref}$.
- Drives the tail current source or the PMOS load gate to push CM back to $V_{cm,ref}$.

**Pros:** noiseless at DC, no resistive loading of output, easy to bias.
**Cons:** needs a clock; for **AC simulations** add a parallel ideal-DC CMFB with large resistors so the OP point is set (see `faq.txt`).

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

## Required CMFB performance

- Loop bandwidth: comparable to or higher than the differential settling pole (otherwise CM kicks during step), so target a CMFB GBW of **same order as differential GBW** ($\sim 200\,\mathrm{MHz}$).
- DC loop gain: $\geq 30\,\mathrm{dB}$ to suppress CM error.
- Phase margin: $\geq 60°$ (independent CMFB loop stability).

## To do

- [ ] Pick CMFB style (SC or CT)
- [ ] Add the AC-only ideal CMFB with large $R$ for OP-point in AC sims (per `faq.txt`)
- [ ] Verify CM step response: CM should settle without ringing
- [ ] Sweep $C_{cmfb} / R_{cmfb}$ to confirm CMFB pole > differential pole

> **TODO** When the SC- or CT-CMFB is drawn, replace the ASCII sketches above with proper CircuiTikZ (`circuits/cmfb_sc.tex` or `circuits/cmfb_ct.tex`).
