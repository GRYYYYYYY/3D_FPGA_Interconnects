"""Continue after the completed parent's plotting environment failure, without reruns."""
import fcntl
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from prepare import write_json
from scaling_common import verified
from run_native_flat_baseline import ROOT,read,bind,now

OUT=ROOT/'results/native_flat_baseline_20261105'
LARGE=ROOT/'results/native_large2d_followup_20261105'


def freeze():
    old=read(OUT/'supervisor.json');assert old['status']=='stopped_for_review'
    assert 'plot_parent failed' in old['error']
    review=read(OUT/'independent_review.json');assert review['status']=='passed';verified(review['summary'])
    assert not (LARGE/'summary.json').exists() and not (LARGE/'remote_receipt.json').exists()
    plan=dict(created_utc=now(),previous_supervisor=bind(OUT/'supervisor.json'),previous_pid=old['pid'],
        parent_review=bind(OUT/'independent_review.json'),parent_figures=bind(OUT/'figures.json'),
        large_plan=bind(LARGE/'plan.json'),hostname=old['hostname'],
        scripts={n:bind(ROOT/'scripts'/n) for n in ['continue_native_flat_supervisor.py','run_native_large2d_followup.py','review_native_flat_baseline.py','plot_native_flat_baseline_v2.py','assemble_native_cpu_paper.py']},
        reason='Inherited Jupyter MPLBACKEND rejected at matplotlib import. v2 explicitly sets Agg before import and reserves legend space. Parent review passed and local figures generated; no parent solver or review rerun.',
        action='One launch of still-unstarted frozen BNN2D chain; terminal review, Agg plots and table assembly. Stop on errors; no retries.')
    assert not (OUT/'supervisor_continuation_plan.json').exists()
    write_json(OUT/'supervisor_continuation_plan.json',plan);print('Frozen supervisor continuation',flush=True)


def run():
    lock=(OUT/'supervisor.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (OUT/'supervisor_continuation.json').exists()
    p=read(OUT/'supervisor_continuation_plan.json')
    for x in [p['previous_supervisor'],p['parent_review'],p['parent_figures'],p['large_plan'],*p['scripts'].values()]:verified(x)
    assert socket.gethostname()==p['hostname'] and not Path('/proc',str(p['previous_pid'])).exists()
    assert not (LARGE/'summary.json').exists() and not (LARGE/'remote_receipt.json').exists()
    state=dict(status='launching_large2d',pid=os.getpid(),hostname=socket.gethostname(),started_utc=now(),
        plan=bind(OUT/'supervisor_continuation_plan.json'),events=[],no_retries=True)
    def checkpoint():write_json(OUT/'supervisor_continuation.json',state)
    def step(name,cmd):
        for x in p['scripts'].values():verified(x)
        state['status']=name;checkpoint()
        with (OUT/(name+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        state['events'].append(dict(step=name,returncode=r.returncode,finished_utc=now()));checkpoint()
        assert r.returncode==0,name+' failed'
    checkpoint()
    try:
        with (LARGE/'remote_owner.log').open('x') as log:
            proc=subprocess.Popen(['/usr/bin/python3',str(ROOT/'scripts/run_native_large2d_followup.py'),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        receipt=dict(pid=proc.pid,hostname=socket.gethostname(),supervisor_pid=os.getpid(),started_utc=now(),plan=p['large_plan'])
        write_json(LARGE/'remote_receipt.json',receipt);state.update(status='watching_large2d',large_owner=proc.pid);checkpoint()
        while proc.poll() is None:
            if (LARGE/'summary.json').exists():
                s=read(LARGE/'summary.json');state['last_observation']=dict(utc=now(),status=s['status'],
                    completed=sum('finished_utc'in r for r in s['measurements']),started=len(s['measurements']),
                    current=s['measurements'][-1]['key'] if s['measurements'] else 'preparation')
            checkpoint();time.sleep(30)
        assert proc.returncode==0,'BNN2D runner failed; no retry'
        s=read(LARGE/'summary.json');assert s['status'] in ['completed','completed_with_preparation_failure']
        step('continued_review_large2d',['/usr/bin/python3',str(ROOT/'scripts/review_native_flat_baseline.py'),str(LARGE)])
        step('continued_plot_large2d',[str(ROOT/'.venv-report/bin/python'),str(ROOT/'scripts/plot_native_flat_baseline_v2.py'),str(LARGE)])
        step('continued_tables_final',['/usr/bin/python3',str(ROOT/'scripts/assemble_native_cpu_paper.py')])
        state['status']='completed_pending_main_visual_and_scientific_review'
    except Exception as exc:
        state.update(status='stopped_for_review',error=repr(exc));raise
    finally:state['finished_utc']=now();checkpoint()


if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
