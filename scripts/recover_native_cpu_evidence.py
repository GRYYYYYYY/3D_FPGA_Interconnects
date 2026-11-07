"""One reviewed recovery: retain 24 samples, finish 12, then scaling and audit.

The combined generalization directory is explicitly a derived evidence view.
Original failed receipts and every per-measurement record remain untouched.
"""
from datetime import datetime,timezone
import copy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare import sha256,write_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_evidence_20261102'
def read(p):return json.loads(p.read_text())
def stamp():return datetime.now(timezone.utc).isoformat()
def binding(p):return dict(path=str(p),sha256=sha256(p))


def combine():
    original_plan=read(OUT/'generalization_plan.json')
    original=read(OUT/'generalization/serial/summary.json')
    tail=read(OUT/'generalization_tail/serial/summary.json')
    assert original['status']=='failed' and len(original['measurements'])==24
    assert tail['status']=='completed' and len(tail['measurements'])==12
    assert all(c['status']=='passed' for c in tail['cache_qualifications'])
    failed=[c for c in original['cache_qualifications'] if c['status']!='passed']
    assert len(failed)==1 and failed[0]['case']=='s38417_s1'
    fresh=next(c for c in tail['cache_qualifications'] if c['case']=='s38417_s1')
    assert failed[0]['builders'][0]['wire_map_sha256']==fresh['sha256']
    plan=copy.deepcopy(original_plan);plan['output']=str(OUT/'generalization_complete')
    plan['runner_bindings'].update(read(OUT/'generalization_tail_plan.json')['runner_bindings'])
    plan['derived_evidence_view']=True
    plan['qualification_exception']='Tail setup only: disable post-route overuse report; measured commands unchanged.'
    plan_path=OUT/'generalization_complete_plan.json';write_json(plan_path,plan)
    rows=original['measurements']+tail['measurements']
    expected=[]
    for c in original_plan['lanes']['serial']['cases']:
        for phase in c['phases']:
            for n in phase['workers']:
                for cache in phase['cache_modes']:
                    for v in phase['intended_execution_order']:
                        expected.append((c['id'],n,cache,phase['repeat_start'],v))
    assert [(r['case'],r['workers'],r['cache_mode'],r['repeat'],r['variant']) for r in rows]==expected
    for r in rows:
        assert read(Path(r['directory'])/'measurement.json')==r
        cmd=r['command'];assert cmd[cmd.index('--generate_rr_node_overuse_report')+1]=='on'
    for c in tail['cache_qualifications']:
        for b in c['builders']:
            cmd=b['command'];assert cmd[cmd.index('--generate_rr_node_overuse_report')+1]=='off'
    view=copy.deepcopy(original)
    view.update(status='completed',plan=str(plan_path),plan_sha256=sha256(plan_path),measurements=rows,
                cache_qualifications=[c for c in original['cache_qualifications'] if c['status']=='passed']+tail['cache_qualifications'],
                all_routes_successful=all(r['success'] for r in rows),finished_utc=tail['finished_utc'],
                derived_evidence_view=True,retained_failed_qualification=failed)
    view.pop('error',None)
    directory=OUT/'generalization_complete/serial';directory.mkdir(parents=True,exist_ok=False)
    write_json(directory/'summary.json',view)
    files=[OUT/'generalization_plan.json',OUT/'generalization_tail_plan.json',
           OUT/'generalization/serial/summary.json',OUT/'generalization_tail/serial/summary.json',
           OUT/'generalization/serial/s38417_s1_cache_original/process.log',
           OUT/'generalization/serial/s38417_s1_cache_original/lookahead.bin']
    write_json(OUT/'generalization_join.json',dict(status='passed',created_utc=stamp(),sources=[binding(p) for p in files],
        output=binding(directory/'summary.json'),plan=binding(plan_path),retained=24,continued=12,
        failed_qualifications=failed,all_original_planned_keys_present_in_order=True,
        no_timed_measurement_repeated=True,measured_overuse_report_remains_on=True,
        scope='Derived concatenation for auditing; original stage remains failed with its setup failure. No failed sample is relabeled successful.'))


def main():
    with (OUT/'continuation.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert read(OUT/'continuation.json')['status']=='stopped_for_review'
        assert read(OUT/'generalization/supervisor.json')['status']=='failed'
        assert not (OUT/'recovery.json').exists(),'Recovery already exists; inspect it'
        old=read(OUT/'generalization/serial/summary.json')
        assert len(old['measurements'])==24 and all(r['success'] for r in old['measurements'])
        plan=read(OUT/'generalization_plan.json');plan['output']=str(OUT/'generalization_tail')
        plan['lanes']['serial']['cases']=plan['lanes']['serial']['cases'][4:];plan['planned_samples']=12
        assert [c['id'] for c in plan['lanes']['serial']['cases']]==['s38417_s1','s38417_s2']
        wrapper=ROOT/'scripts/run_native_cpu_evidence_tail.py'
        plan['runner_bindings'][wrapper.name]=binding(wrapper)
        plan['qualification_exception']='Disable overuse report only for one-iteration cache builders; all measured commands unchanged.'
        write_json(OUT/'generalization_tail_plan.json',plan)
        (OUT/'generalization_tail').mkdir()
        state=dict(status='running',pid=os.getpid(),started_utc=stamp(),current=None,steps=[],
                   reason='Original cache built, then overuse_report.cpp:366 asserted while reporting intentionally unconverged setup. Preserve failure; no binary change.')
        def run(stage,command):
            state['current']=stage;step=dict(stage=stage,command=command,status='running',started_utc=stamp())
            state['steps'].append(step);write_json(OUT/'recovery.json',state)
            with (OUT/(stage+'_recovery.log')).open('x') as log:
                p=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                step['pid']=p.pid;write_json(OUT/'recovery.json',state);rc=p.wait()
            step.update(returncode=rc,status='completed' if rc==0 else 'failed',finished_utc=stamp())
            write_json(OUT/'recovery.json',state)
            if rc:raise RuntimeError(stage+' process failed')
        try:
            run('generalization_tail',[sys.executable,str(wrapper),'--plan',str(OUT/'generalization_tail_plan.json'),'--lane','serial'])
            combine()
            run('scaling',[sys.executable,str(ROOT/'scripts/supervise_native_cpu_slices.py'),'--plan',str(OUT/'scaling_plan.json')])
            assert read(OUT/'scaling/serial/summary.json')['status']=='completed'
            run('audit',[sys.executable,str(ROOT/'scripts/verify_native_cpu_study.py'),
                '--plan',str(OUT/'triad_plan.json'),'--plan',str(OUT/'generalization_complete_plan.json'),
                '--plan',str(OUT/'scaling_plan.json'),'--output',str(OUT/'evidence_verification.json')])
            state.update(status='measurements_and_audit_complete',current=None,finished_utc=stamp())
        except Exception as exc:
            state.update(status='stopped_for_review',error=repr(exc));raise
        finally:write_json(OUT/'recovery.json',state)


if __name__=='__main__':main()
