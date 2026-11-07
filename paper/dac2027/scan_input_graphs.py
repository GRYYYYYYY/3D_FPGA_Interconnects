"""Optional read-only recount of actual input RR XMLs; no VPR invocation.
Run from any directory. Reads large files and records SHA-256 and tag counts.
"""
from pathlib import Path
import json,hashlib,collections,re
root=Path(__file__).resolve().parents[2];out=root/'paper/dac2027/evidence/expanded_20261105';out.mkdir(parents=True,exist_ok=True)
items=[]
for name in ['alu4_s1','diffeq_s1','s38417_s1']:
 d=json.load(open(root/f'results/native_cpu_evidence_20261102/prepared/{name}/vpr_case.json'));items.append((name,d['inputs']['rr_graph']['path']))
for name in ['bnn_s1','lstm_s1','dla_like.medium_s1']:
 d=json.load(open(root/f'results/native_cpu_width120_20261104/{name}/vpr_case.json'));items.append((name,d['inputs']['rr_graph']['path']))
for r,c in [('native_paper_closure_20261105','tseng_s1'),('native_paper_closure_20261105','des_s1'),('native_flat_baseline_20261105','clma_2d'),('native_large2d_followup_20261105','bnn_2d')]:
 d=json.load(open(root/f'results/{r}/summary.json'));m=next(m for m in d['measurements'] if m.get('case',m.get('graph'))==c);cmd=m['command'];items.append((c,cmd[cmd.index('--read_rr_graph')+1]))
results=[]
for name,path in items:
 p=Path(path);tokens=[b'<node ',b'<edge ',b'type="CHANZ"'];counts=[0]*3;h=hashlib.sha256();tail=b''
 with p.open('rb') as f:
  while True:
   chunk=f.read(16*1024*1024)
   if not chunk:break
   h.update(chunk);s=tail+chunk
   for i,t in enumerate(tokens):counts[i]+=s.count(t)-tail.count(t)
   tail=s[-32:]
 row=dict(case=name,path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest(),rr_nodes=counts[0],rr_edges=counts[1],chanz_nodes=counts[2]);results.append(row)
 print(name,counts,flush=True)
 (out/'input_graph_scan.json').write_text(json.dumps(results,indent=2)+'\n')
