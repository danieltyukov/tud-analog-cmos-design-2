* EE4525 amplifier, variant CR: stacked complementary input (PMOS pair on a top tail, NMOS pair on a
* bottom tail, both gates on the summing node, current reused), telescopic cascodes onto v1,
* current-buffer compensation, class-AB output (NMOS gate direct, PMOS gate via level-shift cap), CT CMFB
* acting on part of the NMOS tail.
* External nets: vip vin (inputs)  vop von (outputs)  vdd  vddb  vcmr  0
* Side a: inputs vin -> v1n -> von.  Side b: vip -> v1p -> vop.
*
.param Ib=9.6u
.param Lip=0.25u Wip=7u Mip=3                  ; input PMOS
.param Lin=1u Win=8.3u Min=2                   ; input NMOS
.param Lt=0.5u Wt=5u Mt=5                      ; top PMOS tail (unit mirrors Mbp)
.param Ltn=1u Wtn=4u Mtn=3 Mtc=1               ; bottom NMOS tail: Mtn units on vbn, Mtc units on the CMFB line
.param Lcp=0.36u Wcp=8.5u Mcp=1                ; PMOS cascodes
.param Lcn=0.36u Wcn=8.5u Mcn=1                 ; NMOS cascodes
.param Lon=0.36u Won=2u Mon=1                  ; output NMOS
.param Lop=0.25u Wop=12u Mop=2                  ; output PMOS (unit mirrors Mbo)
.param Cc=0.443p Cls=0.52p Rb=3Meg C1d=2.5f fcc=0.61
.param Rcm=2Meg Ccm=50f
.param Lcm=0.5u Wcm=4u Wctl=3u Wc3=1u
.param knr=0.75 kn={knr*Mt/Mtn} ko=0.72 kcn=0.6 kcp=0.5
.param Wbcn=0.4u Lbcn=4u Wbcp=1u Lbcp=4u
.param Cbig=10n
*
* ---- bias block (vddb) ----
Ibp  vbp 0 {Ib}
Mbp  vbp vbp vddb vddb pch L={Lt} W={Wt} m=1
Ibn  vddb vbn {kn*Ib}
Mbn  vbn vbn 0 0 nch L={Ltn} W={Wtn} m=1
Ibo  vbo 0 {ko*Ib}
Mbo  vbo vbo vddb vddb pch L={Lop} W={Wop} m=1
Ibcn vddb vcn {kcn*Ib}
Mbcn vcn vcn 0 0 nch L={Lbcn} W={Wbcn} m=1
Ibcp vcp 0 {kcp*Ib}
Mbcp vcp vcp vddb vddb pch L={Lbcp} W={Wbcp} m=1
Cb1 vbp 0 {Cbig}
Cb2 vbn 0 {Cbig}
Cb3 vbo 0 {Cbig}
Cb4 vcn 0 {Cbig}
Cb5 vcp 0 {Cbig}
*
* ---- stage 1: complementary stacked input ----
Mtp  ntp vbp vdd vdd pch L={Lt} W={Wt} m={Mt}
M1p  nb1 vin ntp ntp pch L={Lip} W={Wip} m={Mip}
M2p  nb2 vip ntp ntp pch L={Lip} W={Wip} m={Mip}
Mcp1 v1n vcp nb1 vdd pch L={Lcp} W={Wcp} m={Mcp}
Mcp2 v1p vcp nb2 vdd pch L={Lcp} W={Wcp} m={Mcp}
Mcn1 v1n vcn na1 0 nch L={Lcn} W={Wcn} m={Mcn}
Mcn2 v1p vcn na2 0 nch L={Lcn} W={Wcn} m={Mcn}
M1n  na1 vin ntn 0 nch L={Lin} W={Win} m={Min}
M2n  na2 vip ntn 0 nch L={Lin} W={Win} m={Min}
Mtn  ntn vbn 0 0 nch L={Ltn} W={Wtn} m={Mtn}
Mtc ntn vcmfbx 0 0 nch L={Ltn} W={Wtn} m={Mtc}
*
* ---- stage 2 (class-AB) ----
Mon1 von v1n 0 0 nch L={Lon} W={Won} m={Mon}
Mop1 von gp1 vdd vdd pch L={Lop} W={Wop} m={Mop}
Cls1 v1n gp1 {Cls}
Rb1  gp1 vbo {Rb}
Mon2 vop v1p 0 0 nch L={Lon} W={Won} m={Mon}
Mop2 vop gp2 vdd vdd pch L={Lop} W={Wop} m={Mop}
Cls2 v1p gp2 {Cls}
Rb2  gp2 vbo {Rb}
*
* ---- compensation ----
Cc1 von na1 {fcc*Cc}
Cc2 vop na2 {fcc*Cc}
Cc3 von nb1 {(1-fcc)*Cc}
Cc4 vop nb2 {(1-fcc)*Cc}
C1d v1n v1p {C1d}
*
* ---- CMFB ----
Rcm1 vop vcms {Rcm}
Rcm2 von vcms {Rcm}
Ccm1 vop vcms {Ccm}
Ccm2 von vcms {Ccm}
Mct  ncs vbp vdd vdd pch L={Lt} W={Wctl} m=1
Mc1  vcmfb vcms ncs ncs pch L={Lcm} W={Wcm} m=1
Mc2  ncm2 vcmr ncs ncs pch L={Lcm} W={Wcm} m=1
Mc3  vcmfb vcmfb 0 0 nch L={Ltn} W={Wc3} m=1
Mc4  ncm2 ncm2 0 0 nch L={Ltn} W={Wc3} m=1
Vcmbrk vcmfbx vcmfb 0 AC 1
