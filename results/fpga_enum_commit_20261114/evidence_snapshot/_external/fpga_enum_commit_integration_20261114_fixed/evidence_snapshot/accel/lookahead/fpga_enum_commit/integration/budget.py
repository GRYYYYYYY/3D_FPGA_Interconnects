"""Necessary bounds from frozen complete profiles; never FPGA predictions."""
from decimal import Decimal as D, getcontext
from pathlib import Path
import json,hashlib
getcontext().prec=40
ROOT=Path(__file__).resolve().parents[4]
R=ROOT/'results/fpga_enum_commit_20261114'
rows={}
for case,target in [('bnn_export','0.151799969444'),('lstm_s2','0.15949799988888888')]:
 p=R/'baseline/profile_a'/case/'physical_profile.json';x=json.loads(p.read_text());summary=json.loads((p.parent/'summary.json').read_text());q=x['requests_by_kind_port'];I=sum(q[4]);U=sum(q[5]);V=sum(q[6]);N=x['candidates'];W=summary['waves'];f=D(200000000)
 fixed=D(I)/32+D(N)/64;mem=D(max(a+b for a,b in zip(q[5],q[6])));variants={}
 for r,K in [(5,1),(2,1),(2,4),(2,8),(1,8)]:
  enum=D(r)*U/64-r*W;rmw=D(16)*(U+V)/(64*K);total=fixed+max(enum,rmw,mem)
  variants[f'r{r}_K{K}']={'enum_cycles':str(enum),'context_cycles':str(rmw),'physical_port_cycles':str(mem),'sum_cycles':str(total),'lower_bound_seconds':str(total/f),'exceeds_target':total>D(target)*f,'hypothetical_until_RTL_protocol_verified':True}
 rows[case]={'profile_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'I':I,'N':N,'U':U,'V':V,'W':W,'target_seconds':target,'variants':variants}
out={'scope':'necessary bounds only; new r/K assumptions must be checked against implemented protocol; no inherited old no-go','rows':rows,'assumptions':['64 II1 pair lanes; 200MHz conditional','32 physical ports fixed80ns/5ns; hotspot final port distribution from semantic touched/changed line counts','same canonical reads/writes protocol; no new spill count inferred','initialization and finalization separated from wave compute by fences','other overlapping service constraints take max, not sum','no actual frontend, scratch, event, route or tail cost included'],'fpga_seconds':None,'board_measured':False}
p=R/'joint_budget.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({c:d['variants']['r2_K8'] for c,d in rows.items()},indent=2))
