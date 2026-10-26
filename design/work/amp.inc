* EE4525 attempt 3: telescopic cascode stage 1 + push-pull common-source stage 2 (PMOS gate AC-coupled).
* External nets: vip vin (inputs)  vop von (outputs)  vdd (amp supply)  vddb (bias supply)
*                vcmr (0.9 V CM reference)  0 (ground)
* Stage-1 devices (except the PMOS cascodes), the stage-2 PMOS sources and the CMFB tail and diodes are integer
* multiples (m) of units that also appear in the bias-block replica (tail, input, NMOS cascode, load), so vbp and
* vbn come from scaled copies of the devices they bias (TA: replica bias). vcn, vcp: EE4520-style diodes.
*
* ---- unit devices (W per finger, L) ----
.param Lt=0.5u  Wt=4.3u           ; PMOS tail / current-source unit (stage-1 tail, stage-2 load, CMFB tail)
.param Li=0.18u Wi=5u             ; PMOS input unit
.param Lcp=0.25u Wcp=3u           ; PMOS cascode unit
.param Lcn=0.25u Wcn=0.8u         ; NMOS cascode unit
.param Ll=2u    Wl=2.8u           ; NMOS load unit
.param Ld=0.25u Wd=8.5u           ; NMOS stage-2 driver width at M2=20 (scaled with M2: same gm/ID)
* ---- multipliers: N units per stage-1 half, stage-2 current = M2 tail units, CMFB ----
.param N=9 Ncm=1 M2=11 Mcmt=2 Md=1
* ---- bias block: one master current, fixed ratios (assignment: fixed Ibcn/Ibnp, Ibcp/Ibnp) ----
.param Ibnp=6.4u kcn=6 kcp=4 Wbcn=0.34u Lbcn={Lcn} Wbcp=0.36u Lbcp={Lcp} Rdec=1k Cbig=10n
* ---- compensation and CMFB ----
* Rz tracks the p2-cancelling value (1/gm2)(Cc+CLeff)/Cc, normalised to Rz0*2 at M2 10, Cc 0.8p, Cin 2p
.param Cc=0.77p Rz0=1.2k Rz={Rz0*(20/M2)*((Cc+1.2*Cin)/Cc)/4} Cls=0.68p Rb=2Meg Rcm=2Meg Ccm=50f Lcm=0.36u Wcm=8u

* ===== bias block (on vddb, excluded from power) =====
* P replica: tail unit + input unit (gate at the input CM), tail gate from the input unit's drain
MBP0 bp0 vbpr vddb vddb pch l={Lt} w={Wt} m=1
MBP1 vbpr vcmr bp0 bp0 pch l={Li} w={Wi} m=1
IBNP vbpr 0 {Ibnp}
* N replica: Ibnp into NMOS cascode unit + load unit, load gate from the cascode drain (stage-1 output level)
IBNN vddb vbnr {Ibnp}
MBN5 vbnr vcn bn5 0 nch l={Lcn} w={Wcn} m=1
MBN7 bn5 vbnr 0 0 nch l={Ll} w={Wl} m=1
* cascode gate voltages: wide-swing diodes of the cascode type and length (EE4520 fig. 6: Ibcn, Ibcp)
IBCN vddb vcnr {kcn*Ibnp}
MBN3 vcnr vcnr 0 0 nch l={Lbcn} w={Wbcn} m=1
MBP3 vcpr vcpr vddb vddb pch l={Lbcp} w={Wbcp} m=1
IBCP vcpr 0 {kcp*Ibnp}
* decoupling of every bias line
RD1 vbpr vbp {Rdec}
CD1 vbp 0 {Cbig}
RD2 vbnr vbn {Rdec}
CD2 vbn 0 {Cbig}
RD3 vcnr vcn {Rdec}
CD3 vcn 0 {Cbig}
RD4 vcpr vcp {Rdec}
CD4 vcp 0 {Cbig}

* ===== stage 1: PMOS-input telescopic cascode =====
M0 tail vbp vdd vdd pch l={Lt} w={Wt} m={2*N}
M1 a1p vip tail tail pch l={Li} w={Wi} m={N}
M2 a1n vin tail tail pch l={Li} w={Wi} m={N}
M3 x1p vcp a1p vdd pch l={Lcp} w={Wcp} m={N}
M4 x1n vcp a1n vdd pch l={Lcp} w={Wcp} m={N}
M5 x1p vcn b1p 0 nch l={Lcn} w={Wcn} m={N}
M6 x1n vcn b1n 0 nch l={Lcn} w={Wcn} m={N}
M7 b1p vbn 0 0 nch l={Ll} w={Wl} m={N-Ncm}
M8 b1n vbn 0 0 nch l={Ll} w={Wl} m={N-Ncm}
M7C b1p vcmfb 0 0 nch l={Ll} w={Wl} m={Ncm}
M8C b1n vcmfb 0 0 nch l={Ll} w={Wl} m={Ncm}

* ===== stage 2: NMOS common source, PMOS current-source load =====
M9 vop x1p 0 0 nch l={Ld} w={Wd*M2/20} m={Md}
M10 von x1n 0 0 nch l={Ld} w={Wd*M2/20} m={Md}
M11 vop gp1 vdd vdd pch l={Lt} w={Wt} m={M2}
M12 von gp2 vdd vdd pch l={Lt} w={Wt} m={M2}
CLS1 x1p gp1 {Cls}
RB1 gp1 vbp {Rb}
CLS2 x1n gp2 {Cls}
RB2 gp2 vbp {Rb}

* ===== Miller compensation with nulling resistor =====
CC1 x1p zp {Cc}
RZ1 zp vop {Rz}
CC2 x1n zn {Cc}
RZ2 zn von {Rz}

* ===== CMFB: resistive sense, PMOS pair against vcmr, mirror into Ncm load units per side =====
RCM1 vop vcms {Rcm}
CCM1 vop vcms {Ccm}
RCM2 von vcms {Rcm}
CCM2 von vcms {Ccm}
MC0 cmt vbp vdd vdd pch l={Lt} w={Wt} m={Mcmt}
MC1 vcmfb vcms cmt vdd pch l={Lcm} w={Wcm} m=1
MC2 cmd vcmr cmt vdd pch l={Lcm} w={Wcm} m=1
MC3 vcmfb vcmfb 0 0 nch l={Ll} w={Wl} m=1
MC4 cmd cmd 0 0 nch l={Ll} w={Wl} m=1
