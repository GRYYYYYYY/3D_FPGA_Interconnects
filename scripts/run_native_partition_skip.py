"""Quality-first no-op partition update experiment with conditional timing."""
import copy,json,subprocess,sys,os
from pathlib import Path
from prepare import sha256,write_json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_partition_skip_20261102'
def read(p):return json.loads(p.read_text())
def quality(a,b):return bool(a['success'] and b['success'] and b['critical_path_ns']<=a['critical_path_ns']*1.05 and b['wirelength']<=a['wirelength']*1.05)
def gate(stage):
 s=read(OUT/stage/'serial/summary.json');rows=s['measurements'];cases=sorted({r['case'] for r in rows});checks=[]
 for case in cases:
  rr={r['variant']:r for r in rows if r['case']==case};a,b=rr['control'],rr['candidate']
  checks.append(dict(case=case,check='candidate_quality',passed=quality(a,b),control_cpd=a['critical_path_ns'],candidate_cpd=b['critical_path_ns'],control_wl=a['wirelength'],candidate_wl=b['wirelength']))
  if stage=='gate':
   ref=rr['reference'];checks.append(dict(case=case,check='control_endpoint',passed=a['success'] and ref['success'] and all(a.get(k)==ref.get(k) for k in ['iterations','critical_path_ns','wirelength','route_body_sha256'])))
   da,db=rr['tracectrl'],rr['traceskip'];checks.append(dict(case=case,check='diagnostic_quality',passed=quality(da,db)))
   for v in ['tracectrl','traceskip']:
    r=rr[v];path=Path(r['directory'])/'state_invariants.tsv';records=[list(map(int,l.split())) for l in path.read_text().splitlines()]
    ok=bool(r['success'] and [x[0] for x in records]==list(range(1,r['iterations']+1)) and all(x[1]>0 and x[2]==0 for x in records))
    checks.append(dict(case=case,check=v+'_all_iteration_containment',passed=ok,iterations=len(records),stale=sum(x[2] for x in records)))
   t=Path(db['directory'])/'state_trace.tsv';skips=sum(line.split()[2]=='8' for line in t.read_text().splitlines());checks.append(dict(case=case,check='skip_exercised',passed=skips>0,first5_skips=skips))
 result=dict(status='passed' if all(x['passed'] for x in checks) else 'failed',checks=checks);write_json(OUT/(stage+'_acceptance.json'),result);return result['status']=='passed'
def main():
 assert not (OUT/'supervisor.json').exists()
 base=read(ROOT/'results/native_cpu_evidence_20261102/generalization_plan.json');build=read(OUT/'build_provenance.json');base['binaries']['cpu']=build['binaries']['plain'];base['binaries']['diag']=build['binaries']['diag'];base['qualification_env']={}
 variants={'reference':dict(binary='frozen',parallel=True),'control':dict(binary='cpu',parallel=True,env={'VPR_CPU_SKIP_SAME_PARTITION':'0'}),'candidate':dict(binary='cpu',parallel=True,env={'VPR_CPU_SKIP_SAME_PARTITION':'1'})}
 for name,value in [('tracectrl','0'),('traceskip','1')]:variants[name]=dict(binary='diag',parallel=True,env={'VPR_CPU_REPAIR_MODE':'both','VPR_CPU_STATE_TRACE':'1','VPR_CPU_STATE_TRACE_ITERS':'5','VPR_CPU_SKIP_SAME_PARTITION':value})
 plans={}
 for stage in ['gate','guard','formal']:
  p=copy.deepcopy(base);p['output']=str(OUT/stage);p['variants']={k:v for k,v in variants.items() if stage=='gate' or k in ['control','candidate']}
  p['promotion_rule']={'gate':'All routes legal with independent checks, CPD/WL no worse than5%; gate control endpoint equals frozen; diagnostic containment all iterations zero violations.','formal':'Only after gate and elliptic guard pass. Three repeats; report all pairs. Candidate recommendation requires all quality checks, geometric mean>1.02 and no layout/cache median<0.98. No automatic default change.'}
  p['measurement_scope']='Diagnostic/quality gate, not speed evidence' if stage!='formal' else 'Uninstrumented same-ELF full-process timing, shared host, serial lane; old data not pooled.'
  if stage=='gate':p['lanes']['serial']['cases']=p['lanes']['serial']['cases'][4:]
  if stage=='guard':p['lanes']['serial']['cases']=[dict(id='elliptic',vpr_case=str(ROOT/'data/scaling_elliptic_20261025/elliptic/vpr_case.json'))]
  n=4 if stage=='guard' else 8;reps=3 if stage=='formal' else 1;caches=['rebuild','reuse'] if stage=='formal' else ['reuse'];vv=list(p['variants'])
  for case in p['lanes']['serial']['cases']:
   case['phases']=[]
   for rep in range(reps):
    order=vv if rep%2==0 else vv[::-1];shift=rep%len(vv);declared=order[-shift:]+order[:-shift] if shift else order
    for cache in (caches if rep%2==0 else caches[::-1]):case['phases'].append(dict(name=stage,variants=declared,workers=[n],cache_modes=[cache],repeats=1,repeat_start=rep,intended_execution_order=order))
  p['planned_samples']=len(p['lanes']['serial']['cases'])*len(vv)*len(caches)*reps
  path=OUT/(stage+'_plan.json');write_json(path,p);plans[stage]=path
 write_json(OUT/'protocol.json',dict(gate_samples=10,guard_samples=2,conditional_formal_samples=72,stop_before_timing_if_gate_fails=True,quality_regression_limit_percent=5,default_changed=False))
 state=dict(status='running',pid=os.getpid(),steps=[],completed_stages=[])
 def run(label,cmd):
  state['current']=label;step=dict(label=label,command=cmd);state['steps'].append(step)
  with (OUT/(label+'.log')).open('x') as log:
   c=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);step['pid']=c.pid;write_json(OUT/'supervisor.json',state);rc=c.wait()
  step['returncode']=rc;write_json(OUT/'supervisor.json',state)
  if rc:raise RuntimeError(label+' failed')
 try:
  for stage in ['gate','guard','formal']:
   (OUT/stage).mkdir()
   run(stage,[sys.executable,str(ROOT/'scripts/run_native_cpu_evidence_tail.py'),'--plan',str(plans[stage]),'--lane','serial']);state['completed_stages'].append(stage)
   if stage!='formal' and not gate(stage):state['rejected_at']=stage;break
  cmd=[sys.executable,str(ROOT/'scripts/verify_native_cpu_study.py')]
  for stage in state['completed_stages']:cmd+=['--plan',str(plans[stage])]
  cmd+=['--output',str(OUT/'evidence_verification.json')];run('audit',cmd)
  state.update(status='candidate_rejected' if 'rejected_at' in state else 'measurements_and_audit_complete',current=None)
 except Exception as e:state.update(status='stopped_for_review',error=repr(e));raise
 finally:write_json(OUT/'supervisor.json',state)
if __name__=='__main__':main()
