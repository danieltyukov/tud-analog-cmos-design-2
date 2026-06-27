# 07 — Lecturer / TA clarifications (EE4525 2025–2026)

Verbatim-faithful transcription of the project announcements posted by the
TAs, re-organised by topic and cross-linked to the analysis files they affect.
Where an announcement changes a number or a rule already written elsewhere in
`analysis/`, that file has been updated and points back here.

> **Submission deadline: Sunday, 28 June 2026, 23:59.** See §6.

---

## 1. SPICE model files — **must include $1/f$ noise**

> "For the simulations in your project, please make sure to use the SPICE model
> files that include $(1/f)$ noise (attached). **Do not** use the simplified
> model files previously used in EE4520, as those do not include $(1/f)$ noise.
> In your report, you may also briefly discuss how you sized your amplifier to
> reduce the impact of $(1/f)$ noise, since this is also one aspect considered in
> the grading." — *Attachment:* `log018.l`

**What this means for this repo:**

- The official model is **`log018.l`** (BSIM3, 0.18 µm, `NOIMOD = 1`, with
  `KF`/`AF` and `NOIA/NOIB/NOIC` flicker-noise parameters). It is committed at
  `models/log018.l` and installed into LTspice — see `models/README.md`.
- The forbidden "simplified EE4520" file is **`logic018 no1of.l`** (literally
  *"no $1/f$"*). All active schematics in `design/` and `simulations/` have been
  switched from `logic018 no1of.l` → `log018.l`. Do **not** revert this.
- Sizing for low $1/f$ noise (large gate area $W L$ on the dominant devices,
  PMOS-input where it helps, etc.) must be **discussed in the report** — it is
  graded. See `04_noise_budget.md`.

Related: `04_noise_budget.md`, `models/README.md`.

---

## 2. Settling / ringing and a *fair* time-constant $\tau$ (two-stage architectures)

> "Since quite a few of you have chosen a two-stage amplifier architecture, you
> may observe ringing in the transient settling behavior. For a fair calculation
> of the time constant $\tau$, please make sure that the first significant peak of
> the settling/ringing response — which typically corresponds to the main-loop
> transient response near the dominant pole — appears **after 25 ns**, i.e., the
> required amplifier settling time. Please note that up to **two cycles of
> ringing are acceptable**, as long as the output still satisfies the required
> settling accuracy."

**What this means:**

- $\tau$ is only "fair" if the loop is **not** ringing faster than the spec: the
  first significant peak of $A\beta(t)$ must land at $t > 25\,\mathrm{ns}$.
- Up to **2 cycles** of ringing are tolerated **provided** the accuracy spec
  ($A\beta \geq 66\,\mathrm{dB}$, $A_{settle} \geq 78\,\mathrm{dB}$ at
  $25\,\mathrm{ns}$) is still met.
- The example settling plot shows $A$ (green) and $A\beta$ (blue) both rising,
  with the first ringing peak marked at the $25\,\mathrm{ns}$ line.

Related: `06_settling_analysis.md`.

---

## 3. Deliverable 4 — plotting $A$ and $A\beta$ together, starting from 0 dB

> "Please make sure that you plot both $A\beta$ and $A$ **in the same figure**.
> In addition, the $A\beta$ plot should **start exactly from 0 dB**. … Note that,
> depending on your design choices, the actual feedback factor $\beta$ may differ
> from the ideal feedback factor (typically **higher**; if **lower**, something is
> wrong in your formula/design). This difference mainly comes from the parasitics
> introduced by the input pair of your amplifier. You should also explain this
> effect in your report."

**What this means:**

- One figure, two curves: $A(t)$ (amplifier settling accuracy) and $A\beta(t)$
  (loop settling accuracy). The example shows $A$ reaching $78\,\mathrm{dB}$ and
  $A\beta$ reaching $66\,\mathrm{dB}$, with the $1/\beta$ gap marked.
- The $A\beta$ curve **must start at exactly 0 dB** at $t = 0$ ("START from 0!!").
- **Actual vs. ideal $\beta$:** the realised $\beta$ is usually a bit **higher**
  than the ideal $C_{fb}/(C_{in}+C_{fb})$ because the input-pair parasitic
  capacitance $C_{gs}$/$C_{gd}$ adds to the divider. If your extracted $\beta$
  comes out **lower** than ideal, your formula or design has a bug. Explain this
  in the report.

Related: `06_settling_analysis.md`, `01_specs_and_budget.md` (§1, $\beta$).

---

## 4. Deliverable 1 — table-of-results clarifications

### 4.1 Term 10 — effective $kT/C$ noise scope

> "For the 10th term, the total effective $kT/C$ noise at the output should only
> include the noise contribution from **$C_{in}$, $C_{fb}$, and $C_{load}$ ($= C_{in}$)**.
> Therefore, if you use a switched-capacitor CMFB, you do **not** need to report
> the noise contribution from the common-mode feedback circuit in this part."

→ Hand-computed $kT/C$ uses only $C_{in}$, $C_{fb}$, $C_{load}$. The
switched-cap CMFB caps are **excluded** from the term-10 number.
Related: `04_noise_budget.md`.

### 4.2 Terms 21 & 22 — Figure of Merit

> "For the **21st term**, *Power $\tau$* means *Power multiplied by $\tau$*, namely
> Power $\times \tau$. In this case, it is equivalent to Power $\times T_{8.6\,\mathrm{dB}}$.
> For the **22nd term**, please do not forget the **negative sign** in the formula,
> which is needed to make the final value positive."

| # | Quantity | Formula (as written in the announcement) | Unit |
|---|----------|------------------------------------------|------|
| 21 | $\mathrm{FoM_{lin}}$ | $\displaystyle 2\pi \cdot \mathrm{Power} \cdot T_{8.6\,\mathrm{dB}} \, / \, \mathrm{SNR_{lin}}^2$ | J |
| 22 | $\mathrm{FoM_{dB}}$  | $\displaystyle -10\log_{10}(\mathrm{FoM_{lin}})$  *(positive number)* | dB |

> **What "$T_{8.6\,\mathrm{dB}}$" means (resolved via the EE4520 precedent):** it is
> **not** a typo. "$T_{8.6\,\mathrm{dB}}$" is shorthand for the time of **one $e$-fold
> of settling**, i.e. $\tau$ — because one $e$-fold $= 20\log_{10}(e) = 8.686\,\mathrm{dB}$,
> so the "$8.6\,\mathrm{dB}$" subscript *is* the e-fold. Here that e-fold is
> $\tau = T_{38.6\,\mathrm{dB}} - T_{30\,\mathrm{dB}}$ (the two thresholds differ by
> $8.6\,\mathrm{dB}$). The EE4520 deliverable used the **identical** label with
> $\tau = T_{48.69\,\mathrm{dB}} - T_{40\,\mathrm{dB}}$ (difference $8.69\,\mathrm{dB}$);
> see `from-ee4520/README.md` and `…/baseline-amplifier-hw2/report/`. So row 21 is
> $\mathrm{FoM_{lin}} = 2\pi \cdot P \cdot \tau / \mathrm{SNR_{lin}}^2$ with this $\tau$.

### 4.3 Term 22 sign

The leading minus sign turns $\log_{10}$ of a sub-unity (tiny, $<10^{-17}$ J)
$\mathrm{FoM_{lin}}$ into a **positive** dB number. Report $\mathrm{FoM_{dB}}$ as a
positive value.

Related: `00_spec_table.md` (rows 10, 21, 22). For a closed-form reading of this
FoM — $\mathrm{FoM}_{lin}=16\pi\,kT\,A_{req}^2\,\mathrm{NEF}/(\eta_{gm}\eta_{cur}\eta_{vol}^2 F_{supply})$,
i.e. which four knobs actually move it — see `08_power_prediction.md` §6.

---

## 5. General design rules & report content

### 5.1 Supply voltage — single rail everywhere

> "All amplifier components should use the same supply voltage, **$V_{DD} = 1.8\,\mathrm{V}$**.
> This **also includes the CMFB circuit**. You are **NOT** allowed to use different
> supply voltages for different circuit blocks, such as the gain booster, second
> stage, CMFB circuit, or other amplifier components."

→ One $1.8\,\mathrm{V}$ rail for the entire amplifier (core, boosters, second
stage, CMFB). No boosted/separate rails. Related: `01_specs_and_budget.md`,
`05_cmfb_design.md`.

### 5.2 Don't over-design

> "Please avoid over-designing your amplifier. For both **SNR** and **settling
> speed**, it is better to **meet** the required specifications, then optimize your
> design for **low power consumption**."

→ Hit $\mathrm{SNR} = 66\,\mathrm{dB}$ and $T_{settle} = 25\,\mathrm{ns}$ with a
little margin, then push current **down**. Power is the optimisation target.
Related: `PLAN.md` (Phase 5), `01_specs_and_budget.md` (§5).

### 5.3 $g_m$-reuse input stage allowed

> "Depending on your design choice, some of you may use a $g_m$-reused architecture
> for the input stage. In this case, the biasing points of the NMOS and PMOS input
> devices may be different. Such a difference is acceptable and allowed. It is also
> **encouraged** in this project if it helps improve the overall performance."

→ NMOS/PMOS input devices may sit at different bias points in a $g_m$-reuse
(current-reuse) input stage. Encouraged where it helps SNR/power.
Related: `02_topology_choice.md`.

### 5.4 FoM requirement (pass threshold)

> "To pass this project, we strongly recommend that your design achieves a **FoM
> higher than 170 dB**. … the FoM should be reported as a **positive value in dB**,
> which corresponds to a **linear FoM lower than $9.5\times10^{-18}$ J**. All related
> calculations must be performed correctly (e.g. SNR) and clearly presented."

→ Target $\mathrm{FoM_{dB}} > 170\,\mathrm{dB}$ ⇔ $\mathrm{FoM_{lin}} < 9.5\times10^{-18}\,\mathrm{J}$.
Related: `00_spec_table.md` (rows 21–22).

### 5.5 CMFB is mandatory

> "A **CMFB circuit is necessary**. Although some structures may appear to work even
> without CMFB in simulation, a CMFB circuit makes the design more robust against
> process variations in manufacturing."

→ A real CMFB must be present even if the sim "works" without it.
Related: `05_cmfb_design.md`.

### 5.6 Biasing-circuit power excluded

> "You can ignore the power consumed by the biasing circuit in your power
> calculation."

(Consistent with `faq.txt`.) Related: `00_spec_table.md` (rows 8–9).

### 5.7 Deliverable 6 — EE4520 FoM comparison (**required for us**)

We took EE4520, so **Deliverable 6 is in scope** and must be completed: a
step-by-step FoM comparison of this EE4525 amplifier against the EE4520 design.
The EE4520 reference deliverables and results are already in this repo under
`from-ee4520/` (see `from-ee4520/baseline-amplifier-hw2/report/`).
**All deliverables 1–8 are required.**

### 5.8 Short explanation (report page 8) — required content

> "In your short explanation, please at least address the following points:"
> - Explain **why the proposed architecture was selected**, including the CMFB
>   implementation.
> - Describe the **sizing process** used to meet the requirements, **especially for
>   noise, including $1/f$ noise, and settling**. Also mention your choice of
>   **output swing** and **capacitor sizing**.
> - Mention **which devices contribute significantly to the noise** and provide an
>   **estimation of the NEF** (Noise Efficiency Factor).
> - Describe **how the amplifier is biased**.

Related: `04_noise_budget.md` (NEF, dominant noise devices), `02_topology_choice.md`,
`05_cmfb_design.md`.

---

## 6. Submission process

> "The report submission process is the same as in EE4520. Submit both your
> project report and the table of results using the online form:
> **https://edu.nl/3c9tf**"

- Review the earlier **"Clarifications Regarding the Project Report"** announcement
  and make sure the final submission follows all stated requirements.
- Report must be **PDF only**; file name **`[Your Student Number].pdf`**.
- **Maximum two submissions** per student.
- **Click the Submit button** at the bottom — submission is successful only when
  the confirmation page ("Final project successfully submitted for student …")
  appears.
- The form requires: student number, first + last name, uploaded PDF, and the
  results table filled in the same way as in the report. Filling all fields is the
  student's responsibility (no automatic checking). Submission date/time is recorded.
- **Deadline: Sunday, 28 June 2026, 23:59.**
- Issues / questions → **f.sebastiano@tudelft.nl**; TAs **A.Gupta-6@tudelft.nl**
  (Avish Gupta) and **Zenghui.Li@tudelft.nl** (Zenghui Li).

### 6.1 Compulsory report structure (project PDF p. 11)

**One page per item, fixed order:** (1) **Title** — Name + Student Number +
"EE4525 2026"; (2) **D1** Table of Results; (3) **D2** node-voltage schematic;
(4) **D3** branch-current schematic; (5) **D4** settling plot; (6) **D5** noise
plot; (7) **D6** = the **FoM comparison** EE4520 ↔ EE4525 (this is the "skip if you
didn't take EE4520" item — *we did take it, so it's required*); (8) **Short
Explanation** (≤ 1 page) — must **explain every aspect of the D4 settling plot**
plus the §5.8 bullets.

> D2/D3 need **clean, readable** schematics (*"not a simulator schematic"*) — and
> **separate sheets for the gain-boosters and CMFB**, each with the node voltages
> / branch currents indicated. Full figure-extraction map → `../report/README.md`.

---

*Source: course announcements ("Dear EE4525ers, …") from the TAs, transcribed
into this repo on 2026-06-26. Figures referenced (example settling plot,
example Deliverable-4 plot, FoM table) are the TAs' "EXAMPLE ONLY" illustrations.*

*Project description in the repo is the **27 May 2026 updated** version
(`Project EE4525 2025-2026_updated.pdf`). The only change vs. the earlier version
was to the Short-Explanation bullets — add "including the CMFB implementation" and
"choice of output swing and capacitor sizing" — both already reflected in §5.8.*
