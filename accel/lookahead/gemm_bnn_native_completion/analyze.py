#!/usr/bin/env python3
"""Recompute completed evidence only. Never invokes a solver or changes raw runs."""
from pathlib import Path
import argparse,csv,hashlib,json,math,statistics,subprocess,struct
H=Path(__file__).resolve().parent
ARMS=['stock','pipeline','alt_cuda']
PAIRS=[('stock','pipeline'),('pipeline','alt_cuda'),('stock','alt_cuda')]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def stat(xs):
 assert len(xs)==3 and all(math.isfinite(v) and v>0 for v in xs)
 return dict(n=3,samples=xs,mean=statistics.mean(xs),sample_SD=statistics.stdev(xs))
def fingerprint(x):return {k:v['sha256'] for k,v in x['input_bindings'].items()}
def table(case,cohort,rows,scope):
 by={(x['arm'],x['repeat']):x for x in rows}
 assert len(by)==len(rows)==9
 for r in range(3):
  group=[by[a,r] for a in ARMS]
  assert all(x['qualified'] and x['map_sha256'] and x['route_sha256'] and x['readback_identity'] for x in group)
  assert len({json.dumps(fingerprint(x),sort_keys=True) for x in group})==1
  assert len({tuple(x['affinity']) for x in group})==1
  assert len({x['cohort_id'] for x in group})==1
  assert all(x['independent']['returncode']==0 and x['independent']['metrics']['full_check'] for x in group)
  for x in group:
   assert x['zero_overuse'] and x['metrics']['full_check'] and x['metrics']['routing_success']
   assert all(x['independent']['metrics'][k]==x['metrics'][k] for k in ['critical_path_ns','wirelength'])
   assert '--route' not in x['independent']['command']
   assert all(x['metrics'][k]<=1.05*y['metrics'][k] for y in group[:2] for k in ['critical_path_ns','wirelength'])
  s,p,c=[x[scope] for x in group]
  assert all(math.isfinite(v) and v>0 for v in [s,p,c])
  assert math.isclose((s/p)*(p/c),s/c,rel_tol=1e-12)
 out=dict(case=case,cohort=cohort,new_measurement=case!='lstm_s2',scope=scope,n=3)
 for a in ARMS:out[a]=stat([by[a,r][scope] for r in range(3)])
 for a,b in PAIRS:
  out[a+'_to_'+b]=stat([by[a,r][scope]/by[b,r][scope] for r in range(3)])
  out[a+'_to_'+b]['ratio_of_means_display_only']=out[a]['mean']/out[b]['mean']
 return out
def capture(p):
 with p.open('rb') as f:head=list(struct.unpack('<7Q',f.read(56)))
 cut=p.stat().st_size-head[3]*head[5]*8
 assert cut>=56
 ih=hashlib.sha256();oh=hashlib.sha256()
 with p.open('rb') as f:
  left=cut
  while left:
   b=f.read(min(left,8*1024*1024));assert b;ih.update(b);left-=len(b)
  for b in iter(lambda:f.read(8*1024*1024),b''):oh.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),header=head,input_prefix_sha256=ih.hexdigest(),output_sha256=oh.hexdigest())
def write_csv(p,rows):
 if not rows:return
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('run',type=Path);ap.add_argument('--historical',required=True,type=Path);ap.add_argument('--map-diff',required=True,type=Path);a=ap.parse_args()
 r=a.run;done=read(r/'finished.json');rows=read(r/'rows.json');env=read(r/'environment/frozen.json');plan=read(r/'experiment_plan.json')
 assert done['status'] in ['COMPLETED_BOUNDED_MATRIX','INFRASTRUCTURE_OR_GATE_FAILURE']
 out=H/'tables';out.mkdir(exist_ok=True)
 assert read(r/'receipts/V1_publication.json')['new_experiments_allowed']
 assert all(sha(H/n)==h for n,h in read(r/'receipts/worker_freeze.json')['files'].items())
 unique=[(x['cohort_id'],x['case'],x['label'],x['arm']) for x in rows];assert len(unique)==len(set(unique))
 formal=[x for x in rows if x['formal']]
 for x in formal:
  assert x['affinity']==env['affinity'] and x['gpu_uuid']==env['gpu_uuid']
  assert x['cohort_id']==env['hostname']+'_post_V1_a'
  assert 'R61_CAPTURE' not in x['environment'] and 'R61_VERIFY_CPU' not in x['environment']
  assert not x['resource_before']['gpu_processes'].strip() and not x['resource_after']['gpu_processes'].strip()
  d=r/'formal'/x['case']/str(x['repeat'])/x['arm']
  assert sha(d/'wire_map.bin')==x['map_sha256'] and sha(d/'routed.route')==x['route_sha256']
  assert x['E2_s']<=x['Process_wall_s']
  assert read(d/'measurement.json')['Process_wall_s']==x['Process_wall_s']
 summary=[];quals=[];mapdiffs=[];captures=[];excluded=[]
 for case in ['gemm','bnn']:
  status=done['case_status'].get(case,dict(status='NOT_COMPLETED'))
  q={x['arm']:x for x in rows if x['case']==case and not x['formal']}
  meta=read(H/'metadata'/f'{case}.json')
  qr=dict(case=case,status=status['status'],N=meta['N'],E=meta['E'],samples=meta['J'],layers=len(set(j['layer'] for j in meta['jobs'])),threads=8,GPU=env['gpu_inventory'][0],cache='fresh map build',new_measurement=True,full_route=bool(q) and all(x['metrics']['routing_success'] for x in q.values()),zero_overuse=bool(q) and all(x['zero_overuse'] for x in q.values()),independent_FULL_STA=bool(q) and all(x['qualified'] for x in q.values()),complete_ALT_pair_equal=False,STRICT_map_equal=False,delay_word_differences=None,congestion_word_differences=None,missing_state_differences=None)
  if all(k in q for k in ['stock','pipeline','alt_cpu','alt_cuda']):
   gate=read(r/'receipts'/f'{case}_qualification_gate.json');qr.update(complete_ALT_pair_equal=gate['alt_complete_samples_and_input_equal'],STRICT_map_equal=gate['strict_map_equal'])
   for arm in ['alt_cpu','alt_cuda']:
    c=capture(Path(q[arm]['native_capture']['path']));assert c['sha256']==q[arm]['native_capture']['sha256'];captures.append(dict(case=case,arm=arm,**c))
   assert captures[-1]['input_prefix_sha256']==captures[-2]['input_prefix_sha256']
   assert captures[-1]['output_sha256']==captures[-2]['output_sha256']
   for left,right in [('pipeline','stock'),('alt_cpu','pipeline'),('alt_cuda','alt_cpu')]:
    paths=[r/'qualification'/case/'qualification'/z/'wire_map.bin' for z in [left,right]]
    diff=json.loads(subprocess.check_output([str(a.map_diff),*map(str,paths)],text=True,timeout=60));mapdiffs.append(dict(case=case,pair=left+'_vs_'+right,**diff))
    if left=='alt_cpu':qr.update({k:diff[k] for k in ['delay_word_differences','congestion_word_differences','missing_state_differences']})
  for arm in ['stock','pipeline','alt_cpu','alt_cuda']:
   qr[arm+'_CPD_ns']=q.get(arm,{}).get('metrics',{}).get('critical_path_ns');qr[arm+'_WL']=q.get(arm,{}).get('metrics',{}).get('wirelength')
  quals.append(qr)
  if status['status']!='COMPLETE':excluded.append(dict(case=case,status=status,reason='No complete qualified n=3 matched cohort; times remain diagnostics'));continue
  assert all(read(r/'receipts'/f'{case}_qualification_gate.json').values())
  fr=[x for x in formal if x['case']==case];assert len(fr)==9 and all(x['qualification_map_equal'] and x['paired_qor_passed'] for x in fr)
  for scope in ['Process_wall_s','E2_s']:summary.append(table(case,env['hostname'],fr,scope))
 old=read(a.historical);lstm=[]
 for x in old['formal_rows']:
  if x['case']=='lstm_s2' and x['backend'] in ARMS:lstm.append(x|dict(arm=x['backend'],cohort_id=x['hostname']))
 for scope in ['Process_wall_s','E2_s']:summary.append(table('lstm_s2',old['worker']['host'],lstm,scope))
 for scope,name in [('Process_wall_s','matched_process'),('E2_s','matched_e2')]:
  flat=[];tex=[]
  for x in [x for x in summary if x['scope']==scope]:
   y={k:x[k] for k in ['case','cohort','new_measurement','n']};cells=[]
   for k in ARMS+[a+'_to_'+b for a,b in PAIRS]:
    s=x[k];y[k+'_mean']=s['mean'];y[k+'_sample_SD']=s['sample_SD'];y[k+'_samples']=json.dumps(s['samples']);cells.append(f"${s['mean']:.3f}\\pm{s['sample_SD']:.3f}$")
   flat.append(y);tex.append(x['case'].replace('_s2','').upper()+(' (prior)' if not x['new_measurement'] else '')+' & '+' & '.join(cells)+r' \\')
  write_csv(out/(name+'.csv'),flat);(out/(name+'.tex')).write_text('\n'.join(tex)+'\n')
 write_csv(out/'qualification.csv',quals)
 result=dict(status='VALIDATED_COMPLETED_EVIDENCE',formal_processes_recorded=len(formal),qualified_new_cases=[q['case'] for q in quals if q['status']=='COMPLETE'],excluded=excluded,summary=summary,qualification=quals,map_differences=mapdiffs,captures=captures,environment=env,historical_LSTM=dict(path=str(a.historical),sha256=sha(a.historical),cohort=old['worker'],new_measurement=False),map_comparator=dict(path=str(a.map_diff),sha256=sha(a.map_diff)),scope=dict(E2='native MapLookahead::compute including conversion/preparation/device/readback/merge/interpolation',Process='process launch through exit, including RRG load/full route/check/STA/uniform serialization; pre-generated pack/place/RRG excluded',independent_readback='separate wall, no reroute'),estimator='mean of three within-repeat ratios; sample SD uses n-1; no cross-cohort products',FPGA_auto_resume_allowed=False)
 save(out/'results.json',result);save(r/'analysis/results.json',result)
 save(out/'claims.json',dict(qualified_new_cases=result['qualified_new_cases'],independent_C1_C2_multiplicative_causality=False,all_size_speedup=False,STRICT_ALT_equivalence=False,LSTM_rerun=False,DLA_rerun=False,FPGA_acceleration_claim=False,V1_unchanged=True,limitations=['Two fixed inputs, one allocation, three independent processes per arm','Stock E2 precision is 0.01 seconds','ALT changes search semantics; QoR gate is +5%, not zero degradation','Qualification and independent readback excluded from formal E2/Process']))
 print(json.dumps(dict(qualified=result['qualified_new_cases'],excluded=excluded,formal=len(formal)),indent=2))
if __name__=='__main__':main()
