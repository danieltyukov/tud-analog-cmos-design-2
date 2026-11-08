# TA feedback, email of Sat 7 Nov 2026 (Zenghui Li, cc Fabio Sebastiano)

Reply to the four questions of 26 Oct 2026 (follow-up sent 3 Nov). The questions, then the answers:

1. One RC level shifter on the PMOS gate only (NMOS gate DC coupled, CMFB holds it near the replica bias):
   is one enough, or should it be two (meeting of 12 Oct, item 8)?
   **Answer: "as long as the specs met, 1 level shift is good to go."** Closes the open TA point.
2. Actual beta 0.195 < ideal 0.2 because the input pair adds about 64 fF at the summing node, so the gap is
   14.18 dB instead of 13.98 dB. Expected?
   **Answer: "indeed, this is exactly what we expect from your design, pls explain it in your report, which
   help your grade."** Done 8 Nov: page 8 paragraph "Actual vs ideal beta".
3. Rin and Rfb noiseless (FAQ allows it; with their noise SNR 66.10 dB, still passing). Keep the noiseless
   numbers in the table?
   **Answer: "sure".**
4. Power = 1.8 V x I(Vdd) averaged over the 25 ns after the step (0.53 mW; quiescent alone 0.48 mW). Right window?
   **Answer: "Seems fine."**

On the report sent 26 Oct: "Did a quick look of your report, seems ok to go!"
