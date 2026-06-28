#!/usr/bin/env python3
"""Clear the old ideal-booster region from a cmfb-derived .asc and insert drawn BA/BB.
Usage: integrate.py <src.asc> <dst.asc> <frags.json> <unloaded_only:0|1>
For the _ac file (unloaded_only handling): only the UNLOADED copy's E2-E7 + their region
are cleared; the loaded replica (E8-E13) stays ideal."""
import sys, json, re
src,dst,fragf=sys.argv[1],sys.argv[2],sys.argv[3]
dual=len(sys.argv)>4 and sys.argv[4]=='1'
frags=json.load(open(fragf))
lines=open(src).read().split('\n')

# region of the two ideal-booster test boxes (unloaded copy)
def inbox(x,y): return 792<=x<=2536 and 632<=y<=1400
# symbols to delete (ideal boosters of the unloaded copy)
DEL_SYM={'E2','E3','E4','E5','E6','E7'}
# test-box rectangles + labels to drop
DROP_RECT={('1664','1392','800','640'),('2528','1392','1664','640')}
DROP_TEXT_SUB=['Ideal Gain-Boosting PMOS','Ideal Gain-Boosting NMOS',
               'Vsp & Vsn are used for ration']

out=[]; i=0
while i<len(lines):
    ln=lines[i]; p=ln.split()
    # drop ideal-booster symbol blocks (SYMBOL e/e2 ... InstName E2.. + attrs)
    if p[:1]==['SYMBOL'] and i+1<len(lines):
        # look ahead for InstName
        j=i+1; name=None
        while j<len(lines) and lines[j].startswith('SYMATTR'):
            m=re.match(r'SYMATTR InstName (\S+)',lines[j])
            if m: name=m.group(1)
            j+=1
        if name in DEL_SYM:
            i=j; continue
    if p[:1]==['WIRE']:
        x1,y1,x2,y2=map(int,p[1:5])
        if inbox(x1,y1) and inbox(x2,y2): i+=1; continue
    if p[:1]==['FLAG']:
        x,y=int(p[1]),int(p[2])
        if inbox(x,y): i+=1; continue
    if p[:1]==['DATAFLAG']:
        x,y=int(p[1]),int(p[2])
        if inbox(x,y): i+=1; continue
    if p[:2]==['RECTANGLE','Normal'] and tuple(p[2:6]) in DROP_RECT:
        i+=1; continue
    if p[:1]==['TEXT'] and any(s in ln for s in DROP_TEXT_SUB):
        i+=1; continue
    # prune stale Aadd from the param line (keep Cfb/Rfb/Cload)
    if (not dual) and 'Aadd=100 Cfb=' in ln:
        ln=ln.replace('Aadd=100 ','')
    out.append(ln); i+=1

# insert drawn boosters before the final ';end-of-content' (append near end, before last blank)
frag_lines=(frags['BA']+'\n'+frags['BB']).split('\n')
# place after the last RECTANGLE line (keeps them grouped with drawing area)
out=out+frag_lines
open(dst,'w').write('\n'.join(out)+'\n')
print(f"wrote {dst}: {len(out)} lines (added {len(frag_lines)} booster lines)")
