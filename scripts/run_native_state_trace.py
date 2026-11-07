"""Sequential diagnostic trace/control matrix; no performance promotion."""
import json,subprocess,sys,os
from pathlib import Path
from prepare import sha256,write_json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_state_trace_20261102'
def main():
 assert not (OUT/'supervisor.json').exists()
 write_json(OUT/'build_provenance.json',dict(binary=dict(path=str(OUT/'bin/vpr_trace'),sha256=sha256(OUT/'bin/vpr_trace')),sources={str(f):sha256(f) for f in (OUT/'source').iterdir()},actual_makefile=(OUT/'Makefile').read_text(),build_log_sha256=sha256(OUT/'build.log'),first_build_failure='Duplicated overlay headers; fixed by putting isolated source include directory first. Failed log retained.'))
 p=json.loads((ROOT/'results/native_state_ablation_20261102/plan.json').read_text());p['output']=str(OUT/'runs');p['binaries']['state']=p['binaries']['cpu'];p['binaries']['cpu']=json.loads((OUT/'build_provenance.json').read_text())['binary'];p['variants']={}
 for prefix,binary,trace in [('state','state',False),('off','cpu',False),('on','cpu',True)]:
  for mode in ['none','both']:
   env={'VPR_CPU_REPAIR_MODE':mode}
   if trace:env.update(VPR_CPU_STATE_TRACE='1',VPR_CPU_STATE_TRACE_ITERS='5')
   p['variants'][prefix+'_'+mode]=dict(binary=binary,parallel=True,env=env)
 variants=list(p['variants']);p['planned_samples']=24;p['measurement_scope']='All24 are diagnostic controls; no speedup claims. Trace records only first5 iterations; timer flag diagnostics=false avoids unrelated heavy instrumentation.'
 p['promotion_rule']={'purpose':'Locate earliest BB/assignment/per-partition order divergence. Compare tracing on/off and old/new ELF endpoints; retain perturbation.','default_change':False}
 for case in p['lanes']['serial']['cases']:
  case['phases']=[]
  for rep in range(2):
   order=variants if rep==0 else variants[::-1];shift=rep%6;declared=order[-shift:]+order[:-shift] if shift else order
   case['phases'].append(dict(name='trace',variants=declared,workers=[8],cache_modes=['reuse'],repeats=1,repeat_start=rep,intended_execution_order=order))
 write_json(OUT/'plan.json',p);(OUT/'runs').mkdir();state=dict(status='running',pid=os.getpid(),steps=[])
 def run(label,cmd):
  state['current']=label;step=dict(label=label,command=cmd);state['steps'].append(step)
  with (OUT/(label+'.log')).open('x') as log:
   child=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);step['pid']=child.pid;write_json(OUT/'supervisor.json',state);rc=child.wait()
  step['returncode']=rc;write_json(OUT/'supervisor.json',state)
  if rc:raise RuntimeError(label+' failed')
 try:
  run('measure',[sys.executable,str(ROOT/'scripts/run_native_cpu_evidence_tail.py'),'--plan',str(OUT/'plan.json'),'--lane','serial'])
  run('audit',[sys.executable,str(ROOT/'scripts/verify_native_cpu_study.py'),'--plan',str(OUT/'plan.json'),'--output',str(OUT/'evidence_verification.json')])
  state.update(status='measurements_and_audit_complete',current=None)
 except Exception as e:state.update(status='stopped_for_review',error=repr(e));raise
 finally:write_json(OUT/'supervisor.json',state)
if __name__=='__main__':main()
