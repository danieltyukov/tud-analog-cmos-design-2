#!/usr/bin/env python3
"""Compact drawn boosters BA (NMOS-cascode, in NMOS box) and BB (PMOS-cascode, in PMOS box).
PMOS=M180 (src up to Vdd), NMOS=R0 (src down to gnd). Bulks via rail FLAG.
Block-spanning control nets (Vcmfb*/Vcmo*) via FLAG (like main-amp Vcn/Vbcm)."""
import sys, json
PINS={'nmos':{'D':(48,0),'G':(0,80),'S':(48,96),'B':(48,48)},
      'pmos':{'D':(48,0),'G':(0,80),'S':(48,96),'B':(48,48)},
      'res':{'A':(16,16),'B':(16,96)}}
SYM={'nmos':'nmos4','pmos':'pmos4','res':'res'}
def xf(rot,px,py): return {'R0':(px,py),'M180':(px,-py)}[rot]
class F:
    def __init__(s): s.L=[]; s.d={}
    def place(s,n,k,rot,x,y,v2=None,v=None):
        s.d[n]=(k,rot,x,y); s.L+=[f"SYMBOL {SYM[k]} {x} {y} {rot}",f"SYMATTR InstName {n}"]
        s.L+=[f"SYMATTR Value {v}"] if k=='res' else [f"SYMATTR Value {'nch' if k=='nmos' else 'pch'}",f"SYMATTR Value2 {v2}"]
    def p(s,n,pn):
        k,rot,x,y=s.d[n]; dx,dy=xf(rot,*PINS[k][pn]); return (x+dx,y+dy)
    def w(s,*pts):
        for a,b in zip(pts,pts[1:]):
            if a!=b: s.L.append(f"WIRE {a[0]} {a[1]} {b[0]} {b[1]}")
    def fl(s,p,net): s.L.append(f"FLAG {p[0]} {p[1]} {net}")
    def rect(s,a,b,c,d): s.L.append(f"RECTANGLE Normal {a} {b} {c} {d}")
    def txt(s,x,y,sz,t): s.L.append(f"TEXT {x} {y} Left {sz} ;{t}")
def s2(m,l='0.18u'): return f"l={l} w=1u m={m}"

# ---------------- BA : NMOS-cascode booster, PMOS input, fold DOWN ----------------
def BA():
    f=F(); VDD=648; GND=1336
    # output branch1 Vnl col 1696 ; branch2 Vnr col 2040
    f.place('Ms1_a','pmos','M180',1696,744,s2(1,'0.5u')); f.place('Mc1_a','nmos','R0',1696,984,s2(2,'0.3u')); f.place('Mb1_a','nmos','R0',1696,1160,s2(1))
    f.place('Ms2_a','pmos','M180',2040,744,s2(1,'0.5u')); f.place('Mc2_a','nmos','R0',2040,984,s2(2,'0.3u')); f.place('Mb2_a','nmos','R0',2040,1160,s2(1))
    f.place('Mta_a','pmos','M180',1868,744,s2(3))
    f.place('MiA_a','pmos','M180',1788,872,s2(2)); f.place('MiB_a','pmos','M180',1948,872,s2(2))
    f.place('Mcmp1_a','pmos','M180',2216,744,s2(1)); f.place('Mcmp2_a','pmos','M180',2336,744,s2(1))
    f.place('Mcm1_a','nmos','R0',2216,984,s2(1)); f.place('Mcm2_a','nmos','R0',2336,984,s2(1)); f.place('Mcmt_a','nmos','R0',2276,1160,s2(1))
    f.place('Rcm1a','res','R0',1680,1120,v='100Meg'); f.place('Rcm2a','res','R0',2136,1120,v='100Meg')
    f.w((1640,VDD),(2440,VDD)); f.fl((1640,VDD),'Vdd')
    f.w((1640,GND),(2440,GND)); f.fl((1640,GND),'0')
    pm=['Ms1_a','Ms2_a','Mta_a','Mcmp1_a','Mcmp2_a','MiA_a','MiB_a']; nm=['Mb1_a','Mb2_a','Mcmt_a','Mc1_a','Mc2_a','Mcm1_a','Mcm2_a']
    for n in pm: f.fl(f.p(n,'B'),'Vdd')
    for n in nm: f.fl(f.p(n,'B'),'0')
    for n in ['Mb1_a','Mb2_a','Mcmt_a']: sp=f.p(n,'S'); f.w(sp,(sp[0],GND))
    # Vnl/Vnr
    f.w(f.p('Ms1_a','D'),f.p('Mc1_a','D')); f.fl(f.p('Ms1_a','D'),'Vnl')
    f.w(f.p('Ms2_a','D'),f.p('Mc2_a','D')); f.fl(f.p('Ms2_a','D'),'Vnr')
    # S_a trunk y=824 (between PMOS row bottom 744 and input top 776)... use 800
    Ty=800; f.w((f.p('MiA_a','S')[0],Ty),(f.p('MiB_a','S')[0],Ty))
    f.w(f.p('MiA_a','S'),(f.p('MiA_a','S')[0],Ty)); f.w(f.p('MiB_a','S'),(f.p('MiB_a','S')[0],Ty))
    f.w(f.p('Mta_a','D'),(f.p('Mta_a','D')[0],Ty))
    # F1: Mc1.S - Mb1.D ; MiA.D down to y=1080 then to Mc1.S
    Fy=1080
    f.w(f.p('Mc1_a','S'),f.p('Mb1_a','D')); f.w(f.p('MiA_a','D'),(f.p('MiA_a','D')[0],Fy),(f.p('Mc1_a','S')[0],Fy))
    f.w(f.p('Mc2_a','S'),f.p('Mb2_a','D')); f.w(f.p('MiB_a','D'),(f.p('MiB_a','D')[0],Fy),(f.p('Mc2_a','S')[0],Fy))
    # Tca
    f.w(f.p('Mcm1_a','S'),f.p('Mcm2_a','S')); f.w((f.p('Mcmt_a','D')[0],f.p('Mcm1_a','S')[1]),f.p('Mcmt_a','D'))
    # ndAa
    f.w(f.p('Mcmp1_a','D'),f.p('Mcm1_a','D'))
    f.w(f.p('Mcmp1_a','G'),(2200,664),(2200,800),(f.p('Mcmp1_a','D')[0],800))
    f.w(f.p('Mcmp2_a','G'),(f.p('Mcmp2_a','G')[0],704),(f.p('Mcmp1_a','D')[0],704),(f.p('Mcmp1_a','D')[0],744))
    # Vcmfba / Vcmoa FLAGs
    f.fl(f.p('Ms1_a','G'),'Vcmfba'); f.fl(f.p('Ms2_a','G'),'Vcmfba')
    f.w(f.p('Mcmp2_a','D'),f.p('Mcm2_a','D')); f.fl(f.p('Mcm2_a','D'),'Vcmfba')
    f.fl(f.p('Mcm1_a','G'),'Vcmoa')
    f.fl(f.p('Rcm1a','A'),'Vnl'); f.fl(f.p('Rcm1a','B'),'Vcmoa'); f.fl(f.p('Rcm2a','A'),'Vnr'); f.fl(f.p('Rcm2a','B'),'Vcmoa')
    f.fl(f.p('Mta_a','G'),'Vbp'); f.fl(f.p('MiA_a','G'),'Vgnp'); f.fl(f.p('MiB_a','G'),'Vgnn')
    for n in ['Mc1_a','Mc2_a','Mcm2_a']: f.fl(f.p(n,'G'),'Vcn')
    for n in ['Mb1_a','Mb2_a','Mcmt_a']: f.fl(f.p(n,'G'),'Vbn')
    f.rect(2436,1360,1656,628); f.txt(1664,612,2,'NMOS-Cascode Booster (real)')
    return f

# ---------------- BB : PMOS-cascode booster, NMOS input, fold UP ----------------
def BB():
    f=F(); VDD=648; GND=1336
    # output branch Vpr col 840: Mbb(top PMOS src) / Mcb(PMOS casc) / Msb(NMOS pulldown)
    f.place('Mbb1_b','pmos','M180',840,744,s2(3)); f.place('Mcb1_b','pmos','M180',840,944,s2(2,'0.3u')); f.place('Msb1_b','nmos','R0',840,1160,s2(1,'0.5u'))
    f.place('Mbb2_b','pmos','M180',1184,744,s2(3)); f.place('Mcb2_b','pmos','M180',1184,944,s2(2,'0.3u')); f.place('Msb2_b','nmos','R0',1184,1160,s2(1,'0.5u'))
    f.place('Mtb_b','nmos','R0',1012,1160,s2(1))
    f.place('MiP1_b','nmos','R0',932,1000,s2(2)); f.place('MiP2_b','nmos','R0',1092,1000,s2(2))
    f.place('Mcmp1_b','pmos','M180',1360,744,s2(1)); f.place('Mcmp2_b','pmos','M180',1480,744,s2(1))
    f.place('Mcm1_b','nmos','R0',1360,984,s2(1)); f.place('Mcm2_b','nmos','R0',1480,984,s2(1)); f.place('Mcmt_b','nmos','R0',1420,1160,s2(1))
    f.place('Rcmb1','res','R0',808,1120,v='100Meg'); f.place('Rcmb2','res','R0',1280,1120,v='100Meg')
    f.w((784,VDD),(1584,VDD)); f.fl((784,VDD),'Vdd')
    f.w((784,GND),(1584,GND)); f.fl((784,GND),'0')
    pm=['Mbb1_b','Mbb2_b','Mcmp1_b','Mcmp2_b']; nm=['Msb1_b','Msb2_b','Mtb_b','MiP1_b','MiP2_b','Mcm1_b','Mcm2_b','Mcmt_b']
    pmc=['Mcb1_b','Mcb2_b']  # PMOS cascode bulk Vdd
    for n in pm+pmc: f.fl(f.p(n,'B'),'Vdd')
    for n in nm: f.fl(f.p(n,'B'),'0')
    for n in ['Mbb1_b','Mbb2_b','Mcmp1_b','Mcmp2_b']: sp=f.p(n,'S'); f.w(sp,(sp[0],VDD))
    for n in ['Msb1_b','Msb2_b','Mtb_b','Mcmt_b']: sp=f.p(n,'S'); f.w(sp,(sp[0],GND))
    # Vpr/Vpl (output between Mcb.D and Msb.D)
    f.w(f.p('Mcb1_b','D'),f.p('Msb1_b','D')); f.fl(f.p('Msb1_b','D'),'Vpr')
    f.w(f.p('Mcb2_b','D'),f.p('Msb2_b','D')); f.fl(f.p('Msb2_b','D'),'Vpl')
    # Sb trunk between tail-drain(1160) and input-source(1096): y=1130
    Sy=1130; f.w((f.p('MiP1_b','S')[0],Sy),(f.p('MiP2_b','S')[0],Sy))
    f.w(f.p('MiP1_b','S'),(f.p('MiP1_b','S')[0],Sy)); f.w(f.p('MiP2_b','S'),(f.p('MiP2_b','S')[0],Sy))
    f.w(f.p('Mtb_b','D'),(f.p('Mtb_b','D')[0],Sy))
    # Fb1: Mbb.D - Mcb.S ; MiP1.D up to Fb level then to Mcb.S
    f.w(f.p('Mbb1_b','D'),f.p('Mcb1_b','S')); Fy=800
    f.w(f.p('MiP1_b','D'),(f.p('MiP1_b','D')[0],Fy),(f.p('Mcb1_b','S')[0],Fy))
    f.w(f.p('Mbb2_b','D'),f.p('Mcb2_b','S'))
    f.w(f.p('MiP2_b','D'),(f.p('MiP2_b','D')[0],Fy),(f.p('Mcb2_b','S')[0],Fy))
    # Tcb (NMOS sources of CMFB pair to Mcmt drain)
    f.w(f.p('Mcm1_b','S'),f.p('Mcm2_b','S')); f.w((f.p('Mcmt_b','D')[0],f.p('Mcm1_b','S')[1]),f.p('Mcmt_b','D'))
    # ndAb
    f.w(f.p('Mcmp1_b','D'),f.p('Mcm1_b','D'))
    f.w(f.p('Mcmp1_b','G'),(1344,664),(1344,800),(f.p('Mcmp1_b','D')[0],800))
    f.w(f.p('Mcmp2_b','G'),(f.p('Mcmp2_b','G')[0],704),(f.p('Mcmp1_b','D')[0],704),(f.p('Mcmp1_b','D')[0],744))
    # Vcmfbb / Vcmob FLAGs
    f.fl(f.p('Msb1_b','G'),'Vcmfbb'); f.fl(f.p('Msb2_b','G'),'Vcmfbb')
    f.w(f.p('Mcmp2_b','D'),f.p('Mcm2_b','D')); f.fl(f.p('Mcm2_b','D'),'Vcmfbb')
    f.fl(f.p('Mcm1_b','G'),'Vcmob')
    f.fl(f.p('Rcmb1','A'),'Vpr'); f.fl(f.p('Rcmb1','B'),'Vcmob'); f.fl(f.p('Rcmb2','A'),'Vpl'); f.fl(f.p('Rcmb2','B'),'Vcmob')
    f.fl(f.p('Mtb_b','G'),'Vbn'); f.fl(f.p('MiP1_b','G'),'Vgpn'); f.fl(f.p('MiP2_b','G'),'Vgpp')
    for n in ['Mbb1_b','Mbb2_b']: f.fl(f.p(n,'G'),'Vbp')
    for n in ['Mcb1_b','Mcb2_b']: f.fl(f.p(n,'G'),'Vcp')
    f.fl(f.p('Mcm2_b','G'),'Vcp')
    f.fl(f.p('Mcmt_b','G'),'Vbn')
    f.rect(1580,1360,800,628); f.txt(808,612,2,'PMOS-Cascode Booster (real)')
    return f

ba=BA(); bb=BB()
out={'BA':'\n'.join(ba.L),'BB':'\n'.join(bb.L)}
json.dump(out,open(sys.argv[1],'w'))
print(f"BA: {len(ba.d)} dev, {sum(1 for l in ba.L if l[:4]=='WIRE')} wires")
print(f"BB: {len(bb.d)} dev, {sum(1 for l in bb.L if l[:4]=='WIRE')} wires")
