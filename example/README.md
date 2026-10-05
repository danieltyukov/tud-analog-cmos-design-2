# Passing example (grade 7.5)

A friend's submitted design for the same assignment (student 6327087, June 2026), kept as a
reference. **Do not copy it.** Use it to calibrate what a passing report looks like and
as the golden test for our tools.

| File | What |
|---|---|
| `6327087.pdf` | the 8-page report in the compulsory structure (read its D1 table, D4 explanation, short explanation) |
| `cmos2_margin0p1_visual_grid16.asc` | the LTspice schematic (written for LTspice 24; `tools/lt.py` adapts it for XVII) |

## Reproduced on this machine (LTspice XVII, `tools/evaluate.py`, 5 Oct 2026)

| Item | Report | Our tools |
|---|---|---|
| A at 25 ns | 80.81 dB | 80.81 dB |
| Aβ at 25 ns | 66.01 dB | 66.01 dB |
| T30 / T38.6 / τ | 16.397 / 19.094 / 2.697 ns | identical |
| Amplifier noise | 326.40 µV | 326.41 µV |
| kT/C (42 kT/Cin) | 231.81 µV | 231.87 µV (T = 300.15 K vs 300 K) |
| SNR | 66.01 dB | 66.01 dB |
| Power | 1.24 mW (after-step average) | 1.29 mW (our rule: max of quiescent and 25 ns window) |
| FoM | 172.78 dB | 172.60 dB |
| First ringing peak | after 25 ns | 26.6 ns |
| β actual | (reported as ~1/4, which is wrong) | 0.182 (gap 14.81 dB) |

`tools/selftest.py` re-runs this comparison; it is the toolchain's regression test.

## Architecture summary

Two-stage fully differential. Stage 1: NMOS pair, NMOS cascodes, cascoded PMOS loads, all
W = 58 µm, L = 1.8 µm. Stage 2: complementary push-pull (Wn2 = 1.9 µm, Wp2 = 21 µm, L = 0.22 µm).
Miller Cc = 720 fF with Rz = 2.8 kΩ per side, differential snubber 850 Ω + 0.78 pF across the outputs.
Continuous-time CMFB: 2 MΩ resistive output sensing, MOS diff pair against Vcmr = 0.9 V, weak
correction devices on the first-stage nodes. Bias block on Vddb with 1 Ω/1 F isolation.
Cin = 3.237 pF, output step 1.131 V differential.

What our linter flags in it: E-source probes typed as text directives (our rule forbids this), Rin/Rfb
not `noiseless` and only 10/40 MΩ (their noise inflated the amplifier noise by about 77 µV per Rin).
