"""Single advancement owner for the predeclared sequential evidence stages."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from prepare import write_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_evidence_20261102'


def read(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return None


def main():
    with (OUT/'continuation.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUT/'continuation.json').exists():
            previous=read(OUT/'continuation.json')
            if '--resume-waiting-triad' not in sys.argv or previous.get('current')!='triad' or previous.get('steps'):
                raise RuntimeError('Existing chain; inspect it instead of restarting')
            old=Path('/proc')/str(previous['pid'])/'cmdline'
            if old.exists() and b'continue_native_cpu_evidence.py' in old.read_bytes():
                raise RuntimeError('Previous controller remains live')
            archive=OUT/'continuation.interrupted.json'
            if archive.exists():raise RuntimeError('Recovery already attempted; review before another recovery')
            write_json(archive,previous)
        state={'status':'running','pid':os.getpid(),'started_utc':datetime.now(timezone.utc).isoformat(),
               'current':'triad','steps':[],'policy':'No automatic retry or overlapping native solver/preparation.'}
        write_json(OUT/'continuation.json',state)
        try:
            while True:
                receipt=read(OUT/'triad/supervisor.json')
                if receipt and receipt['status']!='running':break
                time.sleep(10)
            if receipt['status']!='completed':raise RuntimeError('Triad supervisor failed; main-model review needed')
            summary=read(OUT/'triad/serial/summary.json')
            if not summary or not summary.get('all_routes_successful'):raise RuntimeError('Triad numerical failure; main-model review needed')
            commands=[('prepare',[sys.executable,str(ROOT/'scripts/prepare_native_cpu_evidence.py')]),
                ('generalization',[sys.executable,str(ROOT/'scripts/supervise_native_cpu_slices.py'),'--plan',str(OUT/'generalization_plan.json')]),
                ('scaling',[sys.executable,str(ROOT/'scripts/supervise_native_cpu_slices.py'),'--plan',str(OUT/'scaling_plan.json')]),
                ('audit',[sys.executable,str(ROOT/'scripts/verify_native_cpu_study.py'),
                          '--plan',str(OUT/'triad_plan.json'),'--plan',str(OUT/'generalization_plan.json'),
                          '--plan',str(OUT/'scaling_plan.json'),'--output',str(OUT/'evidence_verification.json')])]
            for stage,command in commands:
                state['current']=stage;step={'stage':stage,'command':command,'status':'running'};state['steps'].append(step)
                write_json(OUT/'continuation.json',state)
                with (OUT/(stage+'_controller.log')).open('x') as stream:
                    child=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                    step['pid']=child.pid;write_json(OUT/'continuation.json',state);rc=child.wait()
                step.update(status='completed' if rc==0 else 'failed',returncode=rc)
                write_json(OUT/'continuation.json',state)
                if rc:raise RuntimeError(stage+' failed; main-model review needed')
                if stage in ['generalization','scaling']:
                    receipt=read(OUT/stage/'supervisor.json');summary=read(OUT/stage/'serial/summary.json')
                    if not receipt or receipt['status']!='completed' or not summary or not summary.get('all_routes_successful'):
                        raise RuntimeError(stage+' numerical/supervisor failure; main-model review needed')
                print(json.dumps(step),flush=True)
            state.update(status='measurements_and_audit_complete',current=None,finished_utc=datetime.now(timezone.utc).isoformat())
        except Exception as exc:
            state.update(status='stopped_for_review',error=repr(exc));raise
        finally:write_json(OUT/'continuation.json',state)


if __name__=='__main__':main()
