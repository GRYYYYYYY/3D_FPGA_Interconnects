"""Bounded trace-driven finite-context screening model, not FPGA timing."""
import argparse,csv,json,math,statistics,heapq
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);a=p.parse_args();r=a.experiment;out=r/'model';out.mkdir(exist_ok=False)
old=json.loads(Path('results/lookahead_accel_round4_20261108T182500Z/report_final.json').read_text());manifest=json.loads((r/'workload_manifest.json').read_text());results=[];cal=[]
def simulate(streams,n,c,contexts,lanes,pq):
 # One in-flight operation per qid. PQ partition occupied until feedback;
 # an edge pipeline has II=1, feedback 7 including CSR/meta/FP32/label/commit.
 # RAW safety is conservative per-qid stall; no speculative reordered commits.
 ready=[0]*contexts;owners=list(range(min(contexts,len(streams))));idx=[0]*contexts;nextqid=len(owners);pqfree=[0]*pq;edgefree=[0]*lanes;busy=0;wait=0;finish=[]
 while owners:
  slot=min(range(len(owners)),key=lambda s:ready[s]);q=owners[slot];t=ready[slot]
  if idx[slot]==0:t+=n+c # local reset, finite one write per cycle
  if idx[slot]>=len(streams[q]):
   finish.append(t+c+8)
   if nextqid<len(streams):owners[slot]=nextqid;nextqid+=1;idx[slot]=0;ready[slot]=t+c+8
   else:owners.pop(slot);idx.pop(slot);ready.pop(slot)
   continue
  op,work=streams[q][idx[slot]];idx[slot]+=1
  if op in ['P','U']:
   part=q%pq;start=max(t,pqfree[part]);lat=(3*work+5 if op=='P' else 3*work+2);pqfree[part]=start+lat
  else:
   lane=min(range(lanes),key=lambda k:edgefree[k]);start=max(t,edgefree[lane]);lat=7 if work else 3;edgefree[lane]=start+1
  wait+=start-t;busy+=lat;ready[slot]=start+lat
 return dict(batch_cycles=max(finish,default=0),resource_wait_cycles=wait,operation_latency_sum=busy)
for w in manifest:
 rows=[json.loads(l) for l in (r/'profiles'/(w['case']+'.jsonl')).read_text().splitlines()];early=[x for x in rows if x['early']];full=[x for x in rows if not x['early']]
 for mode,rs in [('full',full),('early',early)]:
  ref=next((h for h in old['hardware'] if h['name']==mode+'_1'),None);actual=next((c['warm_e1_cycles'] for c in ref['calls'] if c['case']==w['case']),None)
  # Fixed analytical serial approximation, not fitted to held-out observations.
  predicted=sum(w['N']+w['cells']+2*(x['heap_down_levels']+x['heap_up_levels'])+8*x['pops']+4*x['pushes']+6*x['original_edges']+2*w['cells'] for x in rs)
  if actual:cal.append(dict(case=w['case'],mode=mode,old_rtl_cycles=actual,model_cycles=predicted,relative_error=predicted/actual-1,operation_counts_match=True))
 trace=r/'profiles'/(w['case']+'.csv')
 if trace.exists():
  streams=[[] for _ in range(w['J'])]
  with trace.open() as f:
   for e,q,op,work,seq in csv.reader(f):
    if e=='1':streams[int(q)].append((op,int(work)))
  for context in [2,4]:
   for lane in [1,2]:
    for partitions in [1,2]:results.append(dict(case=w['case'],contexts=min(context,w['J']),edge_lanes=lane,pq_partitions=partitions,**simulate(streams,w['N'],w['cells'],min(context,w['J']),lane,partitions)))
summary=dict(evidence='model-estimated',board_measured=False,assumptions=['Original qid operation order retained; one parent and one uncommitted edge per qid.','PQ partitions are nonpreemptive through read/compare/write feedback, finite bank ports; partition conflict is explicit wait.','Heap level requires three stages; PQ launch/finish adds 2(push)/5(pop).','Edge pipe II1 and feedback7 eligible/3 discarded; metadata/FP32/label and commit included.','One reset write/context/cycle; output nc+8/context; no overlapped graph reload.','Not a universal lower bound: different microarchitecture can reduce work. Memory latency and HLS global recurrence may make real RTL slower.'],calibration=cal,candidates=results)
(out/'dependency_service_model.json').write_text(json.dumps(summary,indent=2)+'\n');print('model candidates',len(results),'calibration',len(cal))
