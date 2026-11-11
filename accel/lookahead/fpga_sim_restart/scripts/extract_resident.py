#!/usr/bin/env python3
"""Extract existing resident timers, preserving provenance and cold/native scope."""
import pathlib,json,re
root=pathlib.Path(__file__).resolve().parents[4];out=root/'results/fpga_sim_restart_20261111T231000Z'
rows=[]
for rel in ['results/lookahead_r6_2_20261109T191213Z/evidence_snapshot/holdout_results.json','results/lookahead_r6_2_20261109T191213Z/evidence_snapshot/targeted_optimization_results.json']:
 j=json.loads((root/rel).read_text())
 def walk(x,path):
  if isinstance(x,dict):
   for k,v in x.items():walk(v,path+[k])
  elif isinstance(x,list):
   for i,v in enumerate(x):walk(v,path+[i])
  elif isinstance(x,str) and x.startswith('LA_LIVE ') and 'resident_s=' in x:
   fields=dict(re.findall(r'(\w+)=([^ ]+)',x));rows.append(dict(source=rel,json_path=path,fields=fields,scope='native resident timer, internal control included; initial H2D/final D2H excluded',reuse_limit='cold native run; NOT the requested three-process warm resident cohort'))
 walk(j,[])
(out/'resident_existing.json').write_text(json.dumps(rows,indent=2)+'\n')
print(len(rows),'existing resident intervals located, retained without relabeling E1')
