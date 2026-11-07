"""Predeclared genuinely large2D BNN on the preserved original KOIOS2D architecture."""
import fcntl
import json
import os
from pathlib import Path
import resource
import socket
import sys
import run_native_flat_baseline as base
from continue_native_flat_baseline import evidence_with_completed_log
from prepare import write_json,sha256
from scaling_common import verified

ROOT=base.ROOT
OUT=ROOT/'results/native_large2d_followup_20261105'
PARENT=ROOT/'results/native_flat_baseline_20261105'


def freeze():
    OUT.mkdir(exist_ok=False)
    p=base.read(PARENT/'plan.json')
    d=Path(base.read(p['cases']['bnn']['case']['path'])['inputs']['circuit']['path']).parent
    architecture=d/'2d_architecture.xml';circuit=d/'bnn.blif'
    jobs=[]
    def add(phase,arm,r=0):jobs.append(dict(key=f'{phase}_bnn_2d_w8_r{r}_{arm}',phase=phase,graph='bnn_2d',workers=8,repeat=r,arm=arm))
    for a in ['stock',*base.ARMS]:add('qualification',a)
    for r in range(3):
        arms=['stock',*base.ARMS];arms=arms[r:]+arms[:r]
        for a in arms:add('full_formal',a,r)
    for r in range(3):
        arms=base.ARMS[r:]+base.ARMS[:r]
        for a in arms:add('component_formal',a,r)
    for a in base.ARMS:add('memory_diagnostic',a)
    plan=dict(status='frozen',created_utc=base.now(),jobs=jobs,
        new_case=dict(circuit=base.bind(circuit),architecture=base.bind(architecture),seed=1,device_width=0,route_chan_width=120,target_utilization=.5),
        binaries=p['binaries'],runtime=p['runtime'],build=p['build'],source_bindings=p['source_bindings'],
        runner_bindings=p['runner_bindings']|{n:base.bind(ROOT/'scripts'/n) for n in ['run_native_large2d_followup.py','continue_native_flat_baseline.py']},
        predecessor_plan=base.bind(PARENT/'plan.json'),predecessor_summary=str(PARENT/'summary.json'),
        timeout_seconds=900,preparation_timeout_seconds=1800,min_disk_gib=60,address_space_gib=64,
        preferred_notebook=p['preferred_notebook'],default_changed=False,exclusive_host=False,
        selection='BNN127676 .names and125 two_mult_18x19 primitives; original preserved2d_architecture.xml, implicit single layer. Auto-select existing fixed layout at0.5utilization, channel120, seed1. No architecture edits, artificial expansion, width retries or circuit replacement.',
        scope='Separate follow-up cohort.4full qualifications, conditional12full formal,9stage formal(3arms x3repeats at8cores),3memory diagnostics. Same binaries/method/quality gates as parent.',
        dependency='Run only after parent owner exits with completed status and terminal independent review passes; no solver overlap on fpgaacc2.',
        failure_policy='Preparation failure skips all28jobs and retains failure. Stock qualification failure skips remaining full qualifications and12full timings; still run valid one-iteration construction measurements. Any map/env/affinity/input drift stops. No retries.',
        timing='Preparation excluded. Full processes read frozen packed/place/RR and write map. Stage rows cap routing to1iteration and never count as legal process evidence.',
        quality_gate=p['quality_gate'],memory_scope=p['memory_scope'],statistics=p['statistics'])
    assert len(jobs)==28
    write_json(OUT/'plan.json',plan)
    print('Frozen28 conditional measurements plus bounded BNN2D preparation',flush=True)


def prepare(plan,state,pool):
    c=plan['new_case'];d=OUT/'prepare_bnn_2d';d.mkdir()
    cpus=pool[:8];os.sched_setaffinity(0,cpus);base.pin_budget(8)
    cmd=[plan['binaries']['original']['path'],c['architecture']['path'],c['circuit']['path'],
        '--pack','--place','--route','--analysis','--route_chan_width','120','--device_width','0',
        '--target_utilization','0.5','--seed','1','--num_workers','8','--router_algorithm','parallel',
        '--router_lookahead','map','--flat_routing','off','--check_route','full',
        '--net_file',str(d/'packed.net'),'--place_file',str(d/'fixed.place'),
        '--route_file',str(d/'routed.route'),'--write_rr_graph',str(d/'rr_graph.xml'),
        '--write_router_lookahead',str(d/'wire_map.bin'),'--max_router_iterations','1',
        '--routing_failure_predictor','off','--timing_report_npaths','0']
    state['preparation']=dict(status='running',started_utc=base.now(),command=cmd)
    write_json(OUT/'summary.json',state)
    row=base.capture(plan|dict(timeout_seconds=plan['preparation_timeout_seconds']),cmd,d,base.environment(plan,'stock',d),cpus)
    row['ready']=row['returncode'] in [0,2] and all((d/n).is_file() for n in ['packed.net','fixed.place','rr_graph.xml','wire_map.bin'])
    if row['ready']:
        paths=dict(architecture=c['architecture']['path'],circuit=c['circuit']['path'],packed_netlist=d/'packed.net',placement=d/'fixed.place',rr_graph=d/'rr_graph.xml')
        case={k:c[k] for k in ['seed','device_width','route_chan_width','target_utilization']}
        case.update(id='bnn_2d',inputs={k:base.bind(v) for k,v in paths.items()})
        write_json(d/'vpr_case.json',case);row.update(case=base.bind(d/'vpr_case.json'),reference_map=base.bind(d/'wire_map.bin'))
    row.update(finished_utc=base.now(),artifacts=base.artifacts(d));write_json(d/'preparation.json',row)
    state['preparation'].update(row);write_json(OUT/'summary.json',state)
    print('BNN2D ready:',row['ready'],flush=True)
    return row


def run():
    plan=base.read(OUT/'plan.json');lock=(OUT/'owner.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (OUT/'summary.json').exists(),'No implicit retry'
    parent=base.read(PARENT/'summary.json');review=base.read(PARENT/'independent_review.json')
    assert parent['status']=='completed' and review['status']=='passed'
    verified(review['summary']);verified(plan['predecessor_plan'])
    assert socket.gethostname()==parent['hostname']
    assert not Path('/proc',str(parent['pid'])).exists(),'Predecessor still alive'
    for x in [*plan['runner_bindings'].values(),*plan['binaries'].values(),plan['runtime'],plan['build'],plan['new_case']['architecture'],plan['new_case']['circuit']]:verified(x)
    for path,h in plan['source_bindings'].items():assert sha256(path)==h
    pool=parent['pool'];os.sched_setaffinity(0,pool);budget=base.pin_budget(16)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    state=dict(status='running',pid=os.getpid(),hostname=socket.gethostname(),started_utc=base.now(),
        plan=base.bind(OUT/'plan.json'),pool=pool,topology=parent['topology'],cpu_budget=budget,exclusive_host=False,
        predecessor_review=base.bind(PARENT/'independent_review.json'),measurements=[],skipped=[],cases={})
    base.OUT=OUT;base.log_evidence=evidence_with_completed_log
    write_json(OUT/'summary.json',state)
    try:
        prep=prepare(plan,state,pool)
        if not prep['ready']:
            state.update(status='completed_with_preparation_failure',skipped=[j|dict(reason='preparation_failed') for j in plan['jobs']]);return
        state['cases']['bnn_2d']={k:prep[k] for k in ['case','reference_map']}
        for job in plan['jobs']:
            stock=next((r for r in state['measurements'] if r['phase']=='qualification' and r['arm']=='stock'),None)
            if job['phase']=='qualification' and job['arm']!='stock' and not stock['success']:
                state['skipped'].append(job|dict(reason='stock_qualification_failed'));continue
            if job['phase']=='full_formal':
                if 'full_gate' not in state:
                    rows={r['arm']:r for r in state['measurements'] if r['phase']=='qualification'}
                    legal=len(rows)==4 and all(r['success'] for r in rows.values())
                    checks={a+'_vs_stock':base.quality(rows[a],rows['stock']) for a in base.ARMS} if legal else {}
                    if legal:checks.update({a+'_vs_per_group':base.quality(rows[a],rows['per_group']) for a in ['pipeline','flat']})
                    state['full_gate']=dict(passed=legal and all(x['passed'] for x in checks.values()),quality=checks)
                if not state['full_gate']['passed']:
                    state['skipped'].append(job|dict(reason='full_qualification_rejected'));continue
            base.execute_one(plan,state,job,state['cases']['bnn_2d'],pool)
        state['status']='completed'
    except Exception as exc:
        state.update(status='stopped_for_review',error=repr(exc));raise
    finally:
        state['finished_utc']=base.now();write_json(OUT/'summary.json',state)


if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
