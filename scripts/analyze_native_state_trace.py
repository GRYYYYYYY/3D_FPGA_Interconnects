"""Compare canonical BB/partition/order traces, not global thread schedules."""
import json
from collections import defaultdict,Counter
from pathlib import Path
from prepare import write_json,sha256
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_state_trace_20261102'
def trace(path):
 rows=[tuple(map(int,l.split())) for l in path.read_text().splitlines()];assert all(len(r)==16 for r in rows)
 assert sorted(r[0] for r in rows)==list(range(len(rows)))
 rows.sort();by=defaultdict(list)
 for r in rows:by[r[1]].append(r)
 assert set(by)==set(range(1,6))
 result={}
 for it,rr in by.items():
  snap={r[3]:r for r in rr if r[2]==0};plans=defaultdict(list)
  for r in rr:
   if r[2]==1:plans[r[4]].append((r[5],r[3]))
  for k in plans:plans[k]=[net for idx,net in sorted(plans[k])]
  starts=[r for r in rr if r[2]==2];ends=[r for r in rr if r[2]==3]
  assert len(starts)==len(ends)==sum(map(len,plans.values()))==len(snap)
  invalid=[r for r in snap.values() if not (r[6]>=r[12] and r[7]<=r[13] and r[8]>=r[14] and r[9]<=r[15])]
  old=[r for r in rr if r[2]==5];new=[r for r in rr if r[2]==6];assert len(old)==len(new)
  moves=[]
  for a,b in zip(old,new):
   assert a[3]==b[3];moves.append(dict(net=a[3],old=a[4],new=b[4]))
  result[it]=dict(snapshot=snap,plans=dict(plans),stale=invalid,notifications=[r[3] for r in rr if r[2]==4],dynamic=[r[3] for r in rr if r[2]==7],moves=moves,flags={r[3]:r[5] for r in ends},execution_starts=[r[3] for r in starts])
 return result

def compare(a,b):
 out=[]
 for it in range(1,6):
  x,y=a[it],b[it];nets=sorted(set(x['snapshot'])|set(y['snapshot']))
  boxes=[n for n in nets if x['snapshot'].get(n,())[6:12]!=y['snapshot'].get(n,())[6:12]]
  owners=[n for n in nets if x['snapshot'][n][4]!=y['snapshot'][n][4]]
  partitions=sorted(set(x['plans'])|set(y['plans']));orders=[n for n in partitions if x['plans'].get(n)!=y['plans'].get(n)]
  details=[]
  for n in orders[:3]:
   aa=x['plans'].get(n,[]);bb=y['plans'].get(n,[]);idx=next((i for i,(u,v) in enumerate(zip(aa,bb)) if u!=v),min(len(aa),len(bb)))
   details.append(dict(partition=n,first_order_index=idx,left=aa[max(0,idx-2):idx+4],right=bb[max(0,idx-2):idx+4]))
  out.append(dict(iteration=it,bb_differences=len(boxes),bb_examples=boxes[:8],owner_differences=len(owners),owner_examples=owners[:8],order_partitions=len(orders),order_examples=details,notification_order_equal=x['notifications']==y['notifications'],notification_set_equal=set(x['notifications'])==set(y['notifications']),dynamic_set_equal=set(x['dynamic'])==set(y['dynamic']),reroute_flags_equal=x['flags']==y['flags'],global_start_order_equal=x['execution_starts']==y['execution_starts']))
 return out

def main():
 audit=json.loads((OUT/'evidence_verification.json').read_text());assert audit['status']=='passed'
 s=json.loads((OUT/'runs/serial/summary.json').read_text());assert s['status']=='completed' and len(s['measurements'])==24
 p=json.loads((OUT/'plan.json').read_text());expected=[(c['id'],q['repeat_start'],v) for c in p['lanes']['serial']['cases'] for q in c['phases'] for v in q['intended_execution_order']];rows=s['measurements'];assert [(r['case'],r['repeat'],r['variant']) for r in rows]==expected
 captures={};summaries=[]
 for r in rows:
  assert r['cpu_budget']['cpu_set']==list(range(32,40)) and r['cache_mode']=='reuse'
  want={'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1',**p['variants'][r['variant']]['env']};assert r['candidate_environment']==want
  path=Path(r['directory'])/'state_trace.tsv'
  if r['variant'].startswith('on_'):
   t=trace(path);captures[r['case'],r['repeat'],r['variant']]=t
   per=[]
   for it,x in t.items():
    per.append(dict(iteration=it,nets=len(x['snapshot']),stale_count=len(x['stale']),stale_examples=[dict(net=z[3],partition=z[4],bb=z[6:12],partition_bb=z[12:16]) for z in x['stale'][:8]],notifications=len(x['notifications']),dynamic=len(x['dynamic']),partition_moves=sum(m['old']!=m['new'] for m in x['moves']),same_partition_reinsertions=sum(m['old']==m['new'] for m in x['moves'])))
   summaries.append(dict(key=r['key'],case=r['case'],repeat=r['repeat'],variant=r['variant'],trace_path=str(path),trace_sha256=sha256(path),iterations=per))
  else:assert not path.exists()
 diffs=[]
 for case in sorted({r['case'] for r in rows}):
  for rep in range(2):diffs.append(dict(case=case,repeat=rep,comparison='none_vs_both',iterations=compare(captures[case,rep,'on_none'],captures[case,rep,'on_both'])))
  for mode in ['none','both']:diffs.append(dict(case=case,comparison=mode+'_repeat0_vs_repeat1',iterations=compare(captures[case,0,'on_'+mode],captures[case,1,'on_'+mode])))
 look={(r['case'],r['repeat'],r['variant']):r for r in rows};perturb=[]
 for case in sorted({r['case'] for r in rows}):
  for rep in range(2):
   for mode in ['none','both']:
    a,b,c=[look[case,rep,prefix+'_'+mode] for prefix in ['state','off','on']]
    perturb.append(dict(case=case,repeat=rep,mode=mode,iterations=[r['iterations'] for r in [a,b,c]],critical_path_ns=[r['critical_path_ns'] for r in [a,b,c]],wirelength=[r['wirelength'] for r in [a,b,c]],old_vs_off_route_equal=a.get('route_body_sha256')==b.get('route_body_sha256'),off_vs_on_route_equal=b.get('route_body_sha256')==c.get('route_body_sha256')))
 data=dict(status='complete',samples=24,legal=sum(r['success'] for r in rows),trace_summaries=summaries,comparisons=diffs,perturbation=perturb,scope='All runs diagnostic, only first5 iterations. Global event order is observed call linearization, not a deterministic total routing order. Snapshot containment uses original2D partition predicate; no predecessor race proof.',default_changed=False)
 write_json(OUT/'analysis.json',data);write_json(OUT/'acceptance.json',dict(status='complete',samples=24,legal=data['legal'],trace_files=8,evidence_audit='passed',env_cpu_order_trace_structure_audit='passed',performance_claim=False,default_changed=False))
 print(json.dumps(dict(samples=24,legal=data['legal'],perturbation=perturb,first_differences=[dict(case=d['case'],comparison=d['comparison'],repeat=d.get('repeat'),first=d['iterations'][:2]) for d in diffs]),ensure_ascii=False))
if __name__=='__main__':main()
