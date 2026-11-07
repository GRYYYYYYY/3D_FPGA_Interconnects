"""Explicit one-time recovery of a post-process evidence-ordering error.

No completed solver is repeated. The original frozen runner and plan remain intact.
"""
import fcntl
import json
import os
import resource
import socket
import sys
from pathlib import Path
import run_native_flat_baseline as original
from prepare import sha256, write_json
from scaling_common import metrics, verified, vpr_command

OUT=original.OUT


def evidence_with_completed_log(directory):
    """Use native successful exit markers and final iteration before measurement.json exists."""
    evidence=original_evidence(directory)
    native=metrics((Path(directory)/'process.log').read_text(errors='replace'))
    if evidence['final_overused_nodes'] is None and native['routing_success'] and native['full_check']:
        trace=evidence['iterations']
        assert trace and trace[-1]['overused_nodes']==0
        evidence['final_overused_nodes']=trace[-1]['overused_nodes']
    return evidence


original_evidence=original.log_evidence


def freeze():
    state=original.read(OUT/'summary.json')
    assert state['status']=='stopped_for_review' and len(state['measurements'])==7
    row=state['measurements'][-1]
    assert row['key']=='qualification_clma_2d_w8_r0_stock' and row['returncode']==0
    assert row['routing_success'] and row['full_check'] and row['log_evidence']['last_observed_overused_nodes']==0
    snapshot=OUT/'attempt1_terminal.json'
    assert not snapshot.exists();write_json(snapshot,state)
    amendment=dict(created_utc=original.now(),original_plan=original.bind(OUT/'plan.json'),
        previous_terminal=original.bind(snapshot),continuation=original.bind(Path(__file__)),
        reason='log_evidence reads routing_success from measurement.json, but runner called it before writing that file. Native stock clma completed legally; parsed final iteration has zero overuse. No algorithm/input/CPU/statistics change.',
        action='Preserve six pilots, preparation and first stock qualification. Complete only its missing original FULL/STA checker, then continue exact remaining original job order.',
        new_solver_retries=0,formal_started_before_fix=False)
    write_json(OUT/'continuation_plan.json',amendment)
    print('Frozen one-time continuation; no solver rerun',flush=True)


def run():
    lock=(OUT/'owner.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    amendment=original.read(OUT/'continuation_plan.json')
    for key in ['original_plan','previous_terminal','continuation']:verified(amendment[key])
    state=original.read(OUT/'summary.json')
    assert state==original.read(amendment['previous_terminal']['path']), 'Already resumed or state drift'
    plan=original.read(OUT/'plan.json')
    for x in [*plan['runner_bindings'].values(),*plan['binaries'].values(),plan['runtime'],plan['build']]:verified(x)
    for path,h in plan['source_bindings'].items():assert sha256(path)==h
    for entry in state['cases'].values():
        verified(entry['reference_map'])
        for x in original.read(verified(entry['case']))['inputs'].values():verified(x)
    assert socket.gethostname()==state['hostname']
    pool=state['pool'];os.sched_setaffinity(0,pool);original.pin_budget(16)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    state.update(status='running',previous_owner_pid=state['pid'],pid=os.getpid(),continuation_started_utc=original.now(),continuation=original.bind(OUT/'continuation_plan.json'))
    state.pop('error');state.pop('finished_utc');write_json(OUT/'summary.json',state)
    original.log_evidence=evidence_with_completed_log
    try:
        row=state['measurements'][-1];d=Path(row['directory']);case=original.read(state['cases']['clma_2d']['case']['path'])
        assert sha256(d/'wire_map.bin')==row['wire_map_sha256']==state['cases']['clma_2d']['reference_map']['sha256']
        row['log_evidence']=evidence_with_completed_log(d)
        assert row['log_evidence']['final_overused_nodes']==0
        cpus=pool[:8];os.sched_setaffinity(0,cpus);original.pin_budget(8)
        h=sha256(d/'routed.route');cd=d/'independent';cd.mkdir()
        cmd=vpr_command(plan['binaries']['original']['path'],case,d,200,route=False)
        original.set_option(cmd,'--num_workers',8)
        check=original.capture(plan,cmd,cd,original.environment(plan,'stock',cd),cpus)
        im=metrics((cd/'process.log').read_text(errors='replace'))
        assert sha256(d/'routed.route')==h
        row.update(independent=check,independent_metrics=im,route_sha256=h,
            success=check['returncode']==0 and im['full_check'] and all(im[k]==row[k] for k in ['critical_path_ns','wirelength']),
            finished_utc=original.now(),loadavg_after=os.getloadavg(),artifacts=original.artifacts(d),
            bookkeeping_recovered=True,solver_repeated=False)
        write_json(d/'measurement.json',row);write_json(OUT/'summary.json',state)
        done={r['key'] for r in state['measurements']}
        for job in plan['jobs']:
            if job['key'] in done:continue
            if job['phase']=='full_formal':
                if 'full_gate' not in state:
                    rows={r['arm']:r for r in state['measurements'] if r['phase']=='qualification'}
                    legal=len(rows)==4 and all(r['success'] for r in rows.values())
                    qs={a+'_vs_stock':original.quality(rows[a],rows['stock']) for a in original.ARMS} if legal else {}
                    if legal:qs.update({a+'_vs_per_group':original.quality(rows[a],rows['per_group']) for a in ['pipeline','flat']})
                    state['full_gate']=dict(passed=legal and all(q['passed'] for q in qs.values()),quality=qs)
                if not state['full_gate']['passed']:
                    state['skipped'].append(job|dict(reason='full_qualification_rejected'));continue
            original.execute_one(plan,state,job,state['cases'][job['graph']],pool)
        state['status']='completed'
    except Exception as exc:
        state.update(status='stopped_for_review',error=repr(exc));raise
    finally:
        state['finished_utc']=original.now();write_json(OUT/'summary.json',state)


if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
