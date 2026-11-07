"""Continue only unstarted measurements after a disk-floor preflight stop."""
import fcntl
import os
from pathlib import Path
import resource
import shutil
import socket
import subprocess
import sys
import run_native_large2d_followup as large
from continue_native_flat_baseline import evidence_with_completed_log
from prepare import write_json, sha256
from scaling_common import verified

base = large.base
OUT, ROOT = large.OUT, large.ROOT


def freeze():
    state = base.read(OUT/'summary.json')
    assert state['status'] == 'stopped_for_review' and state['error'] == "AssertionError('Disk floor')"
    done = state['measurements'][:-1]
    pending = state['measurements'][-1]
    assert len(done) == 20 and all('finished_utc' in r for r in done)
    assert 'returncode' not in pending and 'finished_utc' not in pending
    directory = Path(pending['directory'])
    assert {x.name for x in directory.iterdir()} == {'packed.net', 'fixed.place'}
    probe = base.read(OUT/'stopped_owner_probe.json')
    assert probe['hostname'] == state['hostname'] and not any(probe['pids'].values())
    assert shutil.disk_usage(OUT).free > 66 * 1024**3
    snapshot = OUT/'disk_stop_terminal.json'
    assert not snapshot.exists()
    write_json(snapshot, state)
    plan = dict(created_utc=base.now(), original_plan=base.bind(OUT/'plan.json'),
        previous_terminal=base.bind(snapshot), owner_probe=base.bind(OUT/'stopped_owner_probe.json'),
        deduplication=base.bind(large.PARENT/'completed_input_deduplication_remaining.json'),
        previous_supervisor=base.bind(large.PARENT/'supervisor_continuation.json'),
        scripts={n:base.bind(ROOT/'scripts'/n) for n in ['continue_native_large2d_disk.py',
            'review_native_flat_baseline.py','plot_native_flat_baseline_v2.py','assemble_native_cpu_paper.py']},
        preflight_inputs={x.name:base.bind(x) for x in directory.iterdir()},
        completed_solver_runs_retained=len(done), remaining_solver_runs=8, solver_retries=0,
        reason='Disk-floor check raised before captured_process for the fifth component row. No process/log/measurement exists for that row.',
        action='Preserve terminal snapshot and input-only directory; continue eight unstarted jobs in frozen order with unchanged 60GiB floor. No completed measurement is repeated.',
        qualification_and_full_formal_unchanged=True, no_automatic_retries=True)
    write_json(OUT/'disk_continuation_plan.json', plan)
    print('Frozen disk continuation: 20 retained, eight unstarted', flush=True)


def run():
    lock = (OUT/'owner.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    amendment = base.read(OUT/'disk_continuation_plan.json')
    for key in ['original_plan','previous_terminal','owner_probe','deduplication','previous_supervisor']:
        verified(amendment[key])
    for x in [*amendment['scripts'].values(), *amendment['preflight_inputs'].values()]:
        verified(x)
    state = base.read(OUT/'summary.json')
    assert state == base.read(verified(amendment['previous_terminal']))
    assert socket.gethostname() == state['hostname']
    assert not any(Path('/proc', p).exists() for p in base.read(verified(amendment['owner_probe']))['pids'])
    plan = base.read(verified(amendment['original_plan']))
    for x in [*plan['runner_bindings'].values(), *plan['binaries'].values(), plan['runtime'], plan['build']]:
        verified(x)
    for path, digest in plan['source_bindings'].items():
        assert sha256(path) == digest
    case = base.read(verified(state['cases']['bnn_2d']['case']))
    for x in case['inputs'].values():
        verified(x)
    assert shutil.disk_usage(OUT).free > 66 * 1024**3
    preflight = state['measurements'].pop()
    preserved = OUT/'preflight_disk_stop'
    preserved.mkdir()
    Path(preflight['directory']).rename(preserved/preflight['key'])
    pool = state['pool']
    os.sched_setaffinity(0,pool); base.pin_budget(16)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    state.update(status='running', previous_owner_pid=state['pid'], pid=os.getpid(),
        disk_continuation=base.bind(OUT/'disk_continuation_plan.json'), continuation_started_utc=base.now())
    state.pop('error'); state.pop('finished_utc')
    base.OUT=OUT; base.log_evidence=evidence_with_completed_log
    write_json(OUT/'summary.json',state)
    terminal=dict(status='running_remaining_measurements',pid=os.getpid(),hostname=socket.gethostname(),
        started_utc=base.now(),plan=base.bind(OUT/'disk_continuation_plan.json'),events=[],no_retries=True)
    def checkpoint(): write_json(OUT/'disk_continuation_status.json',terminal)
    checkpoint()
    try:
        done={r['key'] for r in state['measurements']}
        for job in plan['jobs']:
            if job['key'] not in done:
                base.execute_one(plan,state,job,state['cases']['bnn_2d'],pool)
        state.update(status='completed',finished_utc=base.now())
        write_json(OUT/'summary.json',state)
        first=base.read(verified(amendment['previous_terminal']))
        assert first['measurements'][:-1] == state['measurements'][:20]
        assert first['preparation'] == state['preparation'] and first['full_gate'] == state['full_gate']
        for name,item in amendment['preflight_inputs'].items():
            assert sha256(preserved/preflight['key']/name) == item['sha256']
        for step, interpreter, script, args in [
            ('review','/usr/bin/python3','review_native_flat_baseline.py',[str(OUT)]),
            ('plot',str(ROOT/'.venv-report/bin/python'),'plot_native_flat_baseline_v2.py',[str(OUT)]),
            ('tables','/usr/bin/python3','assemble_native_cpu_paper.py',[])]:
            verified(amendment['scripts'][script]);terminal['status']=step;checkpoint()
            with (OUT/('disk_continued_'+step+'.log')).open('x') as log:
                result=subprocess.run([interpreter,str(ROOT/'scripts'/script),*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            terminal['events'].append(dict(step=step,returncode=result.returncode,finished_utc=base.now()));checkpoint()
            assert result.returncode==0,step+' failed; no retry'
            if step=='review':
                write_json(OUT/'disk_continuation_review.json',dict(status='passed',checked_utc=base.now(),
                    amendment=base.bind(OUT/'disk_continuation_plan.json'),review=base.bind(OUT/'independent_review.json'),
                    summary=base.bind(OUT/'summary.json'),retained_rows_unchanged=20,
                    completed_solver_retries=0,preparation_and_gate_unchanged=True,preflight_inputs_preserved=True))
        terminal['status']='completed_pending_main_visual_and_scientific_review'
    except Exception as exc:
        terminal.update(status='stopped_for_review',error=repr(exc))
        if state['status']!='completed':
            state.update(status='stopped_for_review',error=repr(exc),finished_utc=base.now())
            write_json(OUT/'summary.json',state)
        raise
    finally:
        terminal['finished_utc']=base.now();checkpoint()


if __name__=='__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
