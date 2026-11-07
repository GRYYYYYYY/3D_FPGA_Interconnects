"""Frozen repeated held-out study and same-ELF cached scheduling control."""
import copy,itertools,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from prepare import sha256,write_json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_repeat_20261102'
def main():
 OUT.mkdir(exist_ok=False)
 (OUT/'HANDOFF.before_study.md').write_text((ROOT/'HANDOFF.md').read_text())
 base=json.loads((ROOT/'results/native_cpu_evidence_20261102/generalization_plan.json').read_text())
 wrapper=ROOT/'scripts/run_native_cpu_evidence_tail.py'
 plans=[]
 for stage in ['repeat','cached_toggle']:
  p=copy.deepcopy(base);p['output']=str(OUT/stage)
  if stage=='cached_toggle':
   p['variants']={'same_cpu':{'binary':'cpu','parallel':True},'pipeline':p['variants']['pipeline']}
   p['lanes']['serial']['cases']=p['lanes']['serial']['cases'][4:]
  variants=list(p['variants']);caches=['rebuild','reuse'] if stage=='repeat' else ['reuse']
  for case in p['lanes']['serial']['cases']:
   case['phases']=[]
   for rep in range(3):
    order=variants[rep%len(variants):]+variants[:rep%len(variants)]
    shift=rep%len(order);declared=order[-shift:]+order[:-shift] if shift else order
    for cache in (caches if rep%2==0 else caches[::-1]):
     case['phases'].append(dict(name=stage,variants=declared,workers=[8],cache_modes=[cache],repeats=1,repeat_start=rep,intended_execution_order=order))
  p['runner_bindings'][wrapper.name]={'path':str(wrapper),'sha256':sha256(wrapper)}
  p['planned_samples']=len(p['lanes']['serial']['cases'])*len(variants)*len(caches)*3
  p['qualification_exception']='Overuse report off only for deliberately unconverged one-iteration cache preparation; timed runs unchanged.'
  p['promotion_rule']={'quality':'Both routes legal; CPD/WL <=5% worse; zero overuse; independent FULL/STA.', 'report':'All three runtime pairs, median and range. Equal circuit/layout weighting. Preserve failures. No automatic default change.'}
  p['repeats_scope']='Three new runtime repetitions of each fixed layout; previous one-shot results excluded.'
  path=OUT/(stage+'_plan.json');write_json(path,p);plans.append(path)
 write_json(OUT/'protocol.json',dict(status='frozen',samples=120,primary=108,cached_same_binary_control=12,cpu_cores=list(range(32,40)),scope='Shared host, serial lane. No new solver binaries or inputs. Timed wait polling unchanged; VPR internal flow time reported as sensitivity metric, not replacement.',default_changed=False))
 state=dict(status='running',pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat(),current=None,steps=[])
 def run(name,cmd):
  state['current']=name;step=dict(name=name,command=cmd);state['steps'].append(step)
  with (OUT/(name+'.log')).open('x') as log:
   child=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   step['pid']=child.pid;write_json(OUT/'supervisor.json',state);rc=child.wait()
  step['returncode']=rc;write_json(OUT/'supervisor.json',state)
  if rc:raise RuntimeError(name+' failed')
 try:
  for path in plans:
   p=json.loads(path.read_text());Path(p['output']).mkdir()
   run(path.stem,[sys.executable,str(wrapper),'--plan',str(path),'--lane','serial'])
  run('audit',[sys.executable,str(ROOT/'scripts/verify_native_cpu_study.py'),'--plan',str(plans[0]),'--plan',str(plans[1]),'--output',str(OUT/'evidence_verification.json')])
  state.update(status='measurements_and_audit_complete',current=None)
 except Exception as exc:state.update(status='stopped_for_review',error=repr(exc));raise
 finally:write_json(OUT/'supervisor.json',state)
if __name__=='__main__':main()
