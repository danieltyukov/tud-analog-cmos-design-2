* EE4525 amplifier: two-stage, PMOS-input telescopic stage 1, current-buffer (cascode) compensation,
* class-AB output (NMOS gate direct, PMOS gate through a capacitive level shift), continuous-time CMFB.
* External nets: vip vin (inputs)  vop von (outputs)  vdd (amp supply)  vddb (bias supply)
*                vcmr (0.9 V CM reference)  0 (ground)
* Side a: M1 (gate vin) -> v1n -> drives von.  Side b: M2 (gate vip) -> v1p -> drives vop.
*
* ---- sizing knobs (one source of truth for every bench) ----
.param Ib=9.6u                                 ; bias unit current (all bias currents are fixed multiples)
.param Lin=0.25u Win=8.8u Min=6                ; input PMOS pair
.param Lt=0.5u Wt=5u Mt=10                     ; tail PMOS (unit mirrors the bias diode Mbp)
.param Lcp=0.36u Wcp=7u Mcp=3                  ; PMOS cascodes
.param Lcn=0.36u Wcn=9.5u Mcn=1                ; NMOS cascodes
.param Lld=2u Wld=3.2u Mld=3 Mlc=1             ; NMOS loads: Mld units on vbn, Mlc units on the CMFB line
.param Lon=0.36u Won=2u Mon=1                  ; output NMOS
.param Lop=0.25u Wop=6u Mop=2                  ; output PMOS (unit mirrors Mbo)
.param Cc=0.55p Cls=0.5p Rb=3Meg C1d=60f       ; compensation, level-shift cap, level-shift bias resistor, v1 damping cap (floating)
.param fcc=1 Rcm=2Meg Ccm=50f                        ; CMFB sense
.param Lcm=0.5u Wcm=4u Wctl=3u Wc3=0.64u       ; CMFB pair, CMFB tail width, CMFB diode width (L=Lld)
.param knr=0.1277 kn={knr*Mt} ko=1.1 kcn=0.5 kcp=0.5   ; bias current ratios (x Ib); fixed loads track the tail
.param Wbcn=0.4u Lbcn=4u Wbcp=0.87u Lbcp=4u       ; cascode-bias diodes
.param Cbig=10n
*
* ---- bias block (on vddb; ideal reference currents allowed here) ----
Ibp  vbp 0 {Ib}
Mbp  vbp vbp vddb vddb pch L={Lt} W={Wt} m=1
Ibn  vddb vbn {kn*Ib}
Mbn  vbn vbn 0 0 nch L={Lld} W={Wld} m=1
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
* ---- stage 1 ----
Mt   ntail vbp vdd vdd pch L={Lt} W={Wt} m={Mt}
M1   nb1 vin ntail ntail pch L={Lin} W={Win} m={Min}
M2   nb2 vip ntail ntail pch L={Lin} W={Win} m={Min}
Mcp1 v1n vcp nb1 vdd pch L={Lcp} W={Wcp} m={Mcp}
Mcp2 v1p vcp nb2 vdd pch L={Lcp} W={Wcp} m={Mcp}
Mcn1 v1n vcn na1 0 nch L={Lcn} W={Wcn} m={Mcn}
Mcn2 v1p vcn na2 0 nch L={Lcn} W={Wcn} m={Mcn}
Mld1 na1 vbn 0 0 nch L={Lld} W={Wld} m={Mld}
Mld2 na2 vbn 0 0 nch L={Lld} W={Wld} m={Mld}
Mlc1 na1 vcmfb 0 0 nch L={Lld} W={Wld} m={Mlc}
Mlc2 na2 vcmfb 0 0 nch L={Lld} W={Wld} m={Mlc}
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
* ---- compensation (current buffers: output -> NMOS cascode source, fraction fcc; rest -> PMOS cascode source) ----
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
Mc3  vcmfb vcmfb 0 0 nch L={Lld} W={Wc3} m=1
Mc4  ncm2 ncm2 0 0 nch L={Lld} W={Wc3} m=1
