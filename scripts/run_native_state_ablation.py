"""Single-owner 2x2 state-repair attribution with external endpoint controls."""
from pathlib import Path
import json,subprocess,sys,os
from datetime import datetime,timezone
from prepare import sha256,write_json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_state_ablation_20261102'
def main():
 assert not (OUT/'supervisor.json').exists()
 p=json.loads((ROOT/'results/native_cpu_evidence_20261102/generalization_tail_plan.json').read_text())
 p['output']=str(OUT/'runs');p['binaries']['cpu']=json.loads((OUT/'build_provenance.json').read_text())['binary']
 p['variants']={'stock':{'binary':'original','parallel':False},'frozen':{'binary':'frozen','parallel':True}}
 for mode in ['none','dynamic','reload','both']:p['variants'][mode]={'binary':'cpu','parallel':True,'env':{'VPR_CPU_REPAIR_MODE':mode}}
 p['qualification_env']={};p['planned_samples']=36
 p['promotion_rule']={'purpose':'State-repair attribution, not deployment. Both/none endpoint route/quality/iterations must match frozen/stock controls to interpret factorial comparisons. No speed ratio for invalid/quality-regressed routes.','default_change':False}
 p['repeats_scope']='Two existing s38417 layouts, same eight physical cores, shared cache, six arms, three new runtime repeats.'
 variants=list(p['variants'])
 for case in p['lanes']['serial']['cases']:
  case['phases']=[]
  for rep in range(3):
   order=variants if rep==0 else variants[::-1] if rep==1 else variants[3:]+variants[:3]
   shift=rep%6;declared=order[-shift:]+order[:-shift] if shift else order
   case['phases'].append(dict(name='state',variants=declared,workers=[8],cache_modes=['reuse'],repeats=1,repeat_start=rep,intended_execution_order=order))
 write_json(OUT/'plan.json',p);(OUT/'runs').mkdir()
 state=dict(status='running',pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat(),steps=[])
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
 except Exception as exc:state.update(status='stopped_for_review',error=repr(exc));raise
 finally:write_json(OUT/'supervisor.json',state)
if __name__=='__main__':main()
