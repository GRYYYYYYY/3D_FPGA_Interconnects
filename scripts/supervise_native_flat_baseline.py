"""Single observation/dependency owner. No retries or recovery submissions."""
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from prepare import sha256,write_json
from scaling_common import verified
from run_native_flat_baseline import now,bind,read,ROOT

OUT=ROOT/'results/native_flat_baseline_20261105'
LARGE=ROOT/'results/native_large2d_followup_20261105'


def freeze():
    assert not (OUT/'supervisor_plan.json').exists()
    s=read(OUT/'summary.json');assert s['status']=='running'
    write_json(OUT/'supervisor_plan.json',dict(created_utc=now(),predecessor_owner=s['pid'],hostname=s['hostname'],
        parent_plan=bind(OUT/'plan.json'),continuation=bind(OUT/'continuation_plan.json'),large_plan=bind(LARGE/'plan.json'),
        scripts={n:bind(ROOT/'scripts'/n) for n in ['supervise_native_flat_baseline.py','run_native_large2d_followup.py','review_native_flat_baseline.py','plot_native_flat_baseline.py','assemble_native_cpu_paper.py']},
        policy='Observe existing owner. After its normal completion and exit, independently review/plot. Only if review passes, launch the one predeclared large2D chain. No solver retries, resubmissions, cancellation or resource changes. Stop on unknown errors.',
        monitor='Deterministic30second poll; no supported luna delegation interface. Main model retains scientific interpretation/visual review.'))
    print('Frozen single-owner dependency supervisor',flush=True)


def run():
    lock=(OUT/'supervisor.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (OUT/'supervisor.json').exists(),'Existing supervision; do not duplicate'
    plan=read(OUT/'supervisor_plan.json')
    for x in [*plan['scripts'].values(),plan['parent_plan'],plan['continuation'],plan['large_plan']]:verified(x)
    assert socket.gethostname()==plan['hostname']
    state=dict(status='watching_parent',pid=os.getpid(),hostname=socket.gethostname(),started_utc=now(),
        plan=bind(OUT/'supervisor_plan.json'),parent_owner=plan['predecessor_owner'],events=[],no_retries=True)
    def checkpoint():write_json(OUT/'supervisor.json',state)
    def step(name,command):
        for x in plan['scripts'].values():verified(x)
        state['status']=name;checkpoint()
        with (OUT/(name+'.log')).open('x') as log:
            proc=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=False)
        state['events'].append(dict(step=name,returncode=proc.returncode,finished_utc=now()));checkpoint()
        assert proc.returncode==0, name+' failed; inspect step log'
    def observe(directory,pid):
        while True:
            s=read(directory/'summary.json')
            state['last_observation']=dict(utc=now(),directory=str(directory),owner=pid,status=s['status'],
                completed=sum('finished_utc' in r for r in s['measurements']),started=len(s['measurements']),
                current=s['measurements'][-1]['key'] if s['measurements'] else 'preparation')
            checkpoint()
            if s['status']!='running':
                assert s['status'] in ['completed','completed_with_preparation_failure'], 'Owner stopped: '+str(s.get('error'))
                # Its final checkpoint can precede interpreter exit by a moment.
                for _ in range(6):
                    if not Path('/proc',str(pid)).exists():return s
                    time.sleep(5)
                raise RuntimeError('Terminal owner still has /proc entry; reconcile before downstream')
            assert Path('/proc',str(pid)).exists(),'Owner disappeared while summary still running'
            time.sleep(30)
    checkpoint()
    try:
        observe(OUT,plan['predecessor_owner'])
        step('review_parent',['/usr/bin/python3',str(ROOT/'scripts/review_native_flat_baseline.py')])
        step('plot_parent',[str(ROOT/'.venv-report/bin/python'),str(ROOT/'scripts/plot_native_flat_baseline.py'),str(OUT)])
        step('tables_after_parent',['/usr/bin/python3',str(ROOT/'scripts/assemble_native_cpu_paper.py')])
        for x in [plan['large_plan'],*plan['scripts'].values()]:verified(x)
        assert not (LARGE/'summary.json').exists()
        with (LARGE/'remote_owner.log').open('x') as log:
            proc=subprocess.Popen(['/usr/bin/python3',str(ROOT/'scripts/run_native_large2d_followup.py'),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        receipt=dict(pid=proc.pid,hostname=socket.gethostname(),supervisor_pid=os.getpid(),started_utc=now(),plan=plan['large_plan'])
        write_json(LARGE/'remote_receipt.json',receipt)
        state.update(status='watching_large2d',large_owner=proc.pid);checkpoint()
        # Fresh runner verifies frozen sources before creating its first checkpoint.
        while not (LARGE/'summary.json').exists():
            assert proc.poll() is None,'Large2D owner exited before first checkpoint'
            time.sleep(5)
        # Reap our child while observing; otherwise a completed child remains a zombie.
        while proc.poll() is None:
            s=read(LARGE/'summary.json');state['last_observation']=dict(utc=now(),directory=str(LARGE),owner=proc.pid,status=s['status'],
                completed=sum('finished_utc' in r for r in s['measurements']),started=len(s['measurements']),
                current=s['measurements'][-1]['key'] if s['measurements'] else 'preparation')
            checkpoint();time.sleep(30)
        assert proc.returncode==0, 'Large2D runner failed; no retry'
        s=read(LARGE/'summary.json');assert s['status'] in ['completed','completed_with_preparation_failure']
        step('review_large2d',['/usr/bin/python3',str(ROOT/'scripts/review_native_flat_baseline.py'),str(LARGE)])
        step('plot_large2d',[str(ROOT/'.venv-report/bin/python'),str(ROOT/'scripts/plot_native_flat_baseline.py'),str(LARGE)])
        step('tables_final',['/usr/bin/python3',str(ROOT/'scripts/assemble_native_cpu_paper.py')])
        state['status']='completed_pending_main_visual_and_scientific_review'
    except Exception as exc:
        state.update(status='stopped_for_review',error=repr(exc));raise
    finally:state['finished_utc']=now();checkpoint()


if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
