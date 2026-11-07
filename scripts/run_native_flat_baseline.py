"""One-owner flat/pipeline attribution, stage memory and a preselected larger 2D case."""
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import socket
import sys
from datetime import datetime, timezone

from prepare import sha256, write_json
from native_cpu_budget import pin_budget
from run_native_cpu_study import cpu_command, set_option
from run_native_lookahead_component import captured_process, component_evidence
from scaling_common import metrics, verified, vpr_command, vpr_environment
from report_native_joint import log_evidence
from qualify_native_cpu_width120 import quality

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_flat_baseline_20261105'
ARMS = ['per_group', 'pipeline', 'flat']


def read(p): return json.loads(Path(p).read_text())
def bind(p): return dict(path=str(Path(p).resolve()), sha256=sha256(p))
def now(): return datetime.now(timezone.utc).isoformat()


def freeze():
    assert not (OUT/'plan.json').exists()
    old = read(ROOT/'results/native_paper_closure_20261105/scaling/plan.json')
    build = read(OUT/'build_provenance.json')
    circuit_dir = Path(read(ROOT/'data/scaling_20261025/ex5p/vpr_case.json')['inputs']['circuit']['path']).parent
    clma = dict(circuit=bind(circuit_dir/'clma.blif'),
        architecture=bind(ROOT/'vendor/vtr_cpu_slices/vtr_flow/arch/timing/k6_N10_mem32K_40nm.xml'),
        seed=1, device_width=0, route_chan_width=100, target_utilization=.5)
    jobs = []
    def add(phase, graph, arm, workers, repeat=0):
        jobs.append(dict(key=f'{phase}_{graph}_w{workers}_r{repeat}_{arm}', phase=phase,
                         graph=graph, arm=arm, workers=workers, repeat=repeat))
    for w in [1,8]:
        for arm in ARMS: add('pilot','tseng_2d',arm,w)
    for arm in ['stock',*ARMS]: add('qualification','clma_2d',arm,8)
    for r in range(3):
        order = ['stock',*ARMS]; order = order[r:]+order[:r]
        for arm in order: add('full_formal','clma_2d',arm,8,r)
    graphs = ['bnn','dla_like.medium','clma_2d']
    for r in range(3):
        for gi,g in enumerate(graphs[r:]+graphs[:r]):
            for w in ([8,16] if (r+gi)%2 == 0 else [16,8]):
                order = ARMS[(r+gi)%3:]+ARMS[:(r+gi)%3]
                for arm in order: add('component_formal',g,arm,w,r)
    for g in graphs:
        for arm in ARMS: add('memory_diagnostic',g,arm,8)
    scripts = ['run_native_flat_baseline.py','build_native_flat_baseline.py',
               'prepare.py','native_cpu_budget.py','run_native_cpu_study.py',
               'run_native_lookahead_component.py','scaling_common.py',
               'report_native_joint.py','qualify_native_cpu_width120.py']
    plan = dict(status='frozen',created_utc=now(),jobs=jobs,cases=old['cases'],new_case=clma,
        binaries=dict(cpu=build['binary'],original=old['binaries']['original']),runtime=old['runtime'],
        build=bind(OUT/'build_provenance.json'), source_bindings=build['sources'],
        runner_bindings={n:bind(ROOT/'scripts'/n) for n in scripts},
        preferred_notebook='e6e06586-4338-4d74-8ecc-72bfa719011c',
        min_disk_gib=60, timeout_seconds=900, address_space_gib=64,
        selection='All BNN/DLA large scaling graphs plus clma from native BLIF collection (8381 .names vs tseng1046/des1591), chosen before candidate timing. Same 2D architecture; automatic minimum device at utilization0.5, channel100, seed1. No widening or sample replacement.',
        component_scope='54 formal complete-lookahead timers:3graphs x3arms x2core counts x3runtime repeats. One route iteration; rc2 may be stage-valid but never legal end-to-end evidence.',
        full_scope='Four qualification and conditional12 formal clma route/analysis processes at8physical cores. Original native parallel router included. Frozen RR/packed/place, map write included, no pack/place/graph construction speed claim.',
        quality_gate='All4 qualifications legal, map-equal and original-independent FULL/STA. Every corrected arm <=5% stock CPD/WL; pipeline and flat also <=5% per_group. Failed qualifications skip12 full timings, preserve component outcomes and failure denominator.',
        memory_scope='9 separate diagnostics at8cores plus6 non-timing small pilots. Two-ms-target /proc/self/statm live-RSS observer within MapLookahead::compute; sampled approximate peak, not exact bound. Label vector capacity and structural map backing exclude queue/allocator/cell payloads. No memory observer in formal/qualification runs.',
        statistics='Paired per graph/core/repeat, median and range of3 ratios; do not pool with historical hosts. Full vs stage vs diagnostic kept separate. Report every negative. No pipeline superiority assumed.',
        allocation='One NUMA pool of16 distinct physical cores, quota>=16. Sequential solvers, shared host, no exclusive-CPU claim.',
        failure_policy='No implicit retries. Stop on provenance, map, actual command/env/affinity drift or invalid component; retain failed preparation/legality and skip dependent full-flow claims.',
        formal_count=54, full_formal_count=12, qualification_count=4, diagnostic_count=9, pilot_count=6,
        default_changed=False, exclusive_host=False)
    assert len(jobs)==85 and len({x['key'] for x in jobs})==85
    write_json(OUT/'plan.json',plan)
    print('Frozen85 measurements plus one clma preparation',flush=True)


def environment(plan, arm, directory, diagnostic=False):
    env={k:v for k,v in vpr_environment(read(plan['runtime']['path'])).items()
         if not k.startswith(('VPR_CPU_','VPR_HYBRID_','H3D_GPU_'))}
    env.update(VPR_HYBRID_LOOKAHEAD_TASKS='1' if arm in ['pipeline','flat'] else '0',
               VPR_HYBRID_LOOKAHEAD_PARALLEL='0' if arm=='stock' else '1')
    if arm in ['pipeline','flat']: env['VPR_CPU_GLOBAL_SCHEDULER']=arm
    if diagnostic:
        env['VPR_CPU_STAGE_MEMORY']=str(directory/'stage_memory.jsonl')
        env['VPR_HYBRID_LOOKAHEAD_REPORT']=str(directory/'lookahead_profile.jsonl')
    return env


def capture(plan, cmd, directory, env, cpus):
    assert shutil.disk_usage(OUT).free > plan['min_disk_gib']*1024**3, 'Disk floor'
    row=captured_process(cmd,directory,env,plan['timeout_seconds'])
    a=row['actual_process']
    wanted={k:v for k,v in env.items() if k.startswith(('VPR_','H3D_GPU_')) or k in ['OMP_NUM_THREADS','LC_ALL']}
    assert a.get('command')==list(map(str,cmd)) and a.get('environment')==wanted, 'Actual process drift'
    assert a.get('cpu_set')==cpus and row['cpu_budget_audit']['verified'], 'CPU drift'
    return row


def artifacts(directory):
    names=['process.log','process.log.resources.json','packed.net','fixed.place','wire_map.bin',
           'routed.route','stage_memory.jsonl','lookahead_profile.jsonl',
           'independent/process.log','independent/process.log.resources.json']
    return {n:bind(directory/n) for n in names if (directory/n).is_file()}


def check_diagnostic(directory, arm):
    mem=[json.loads(l) for l in (directory/'stage_memory.jsonl').read_text().splitlines()]
    profiles=[json.loads(l) for l in (directory/'lookahead_profile.jsonl').read_text().splitlines()]
    stage=[x for x in mem if x['kind']=='stage_rss']; storage=[x for x in mem if x['kind']=='storage']
    assert len(stage)==1 and stage[0]['entry_bytes']>0 and stage[0]['samples']>0 and stage[0]['read_failures']==0
    expected={'flat':'flat_parallel_for','pipeline':'ordered_pipeline','per_group':'per_group'}[arm]
    assert storage and all(x['scheduler']==expected for x in storage)
    if arm!='per_group': assert len(profiles)==1 and profiles[0]['scheduler']==expected
    assert all(x['workspaces']>0 and x['workspace_label_capacity_bytes']>0 for x in storage)
    return dict(stage=stage[0],storage=storage,profiles=profiles)


def execute_one(plan,state,job,entry,pool):
    d=OUT/job['key'];d.mkdir()
    case=read(verified(entry['case']));verified(entry['reference_map'])
    for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:
        shutil.copyfile(case['inputs'][role]['path'],d/name)
    cpus=pool[:job['workers']];os.sched_setaffinity(0,cpus);budget=pin_budget(job['workers'])
    full=job['phase'] in ['qualification','full_formal']
    diagnostic=job['phase'] in ['pilot','memory_diagnostic']
    binary=plan['binaries']['original' if job['arm']=='stock' else 'cpu']['path']
    cmd=cpu_command(binary,case,d,{'router':'parallel'},job['workers'],iterations=200 if full else 1)
    set_option(cmd,'--generate_rr_node_overuse_report','off')
    set_option(cmd,'--write_router_lookahead',d/'wire_map.bin')
    if not full: cmd.remove('--analysis')
    env=environment(plan,job['arm'],d,diagnostic)
    row=job|dict(directory=str(d),started_utc=now(),success=False,cpu_budget=budget,loadavg_before=os.getloadavg())
    state['measurements'].append(row);write_json(OUT/'summary.json',state)
    row.update(capture(plan,cmd,d,env,cpus))
    row.update(metrics((d/'process.log').read_text(errors='replace')))
    ev=log_evidence(d);row['build_seconds']=ev['stage_seconds']['lookahead_build'];row['log_evidence']=ev
    if (d/'wire_map.bin').exists():
        row['wire_map_sha256']=sha256(d/'wire_map.bin')
        assert row['wire_map_sha256']==entry['reference_map']['sha256'], 'Wire map mismatch'
    log=(d/'process.log').read_text(errors='replace')
    if job['arm'] in ['flat','pipeline']:
        assert log.count('CPU_GLOBAL_SCHEDULER='+job['arm']+' ')==1, 'Scheduler dispatch mismatch'
    if full:
        if row['returncode']==0 and row['routing_success'] and row['full_check']:
            assert ev['final_overused_nodes']==0 and row.get('wire_map_sha256')
            h=sha256(d/'routed.route');cd=d/'independent';cd.mkdir()
            ic=vpr_command(plan['binaries']['original']['path'],case,d,200,route=False)
            # Checker is deliberately original VPR; same CPU budget and input path.
            set_option(ic,'--num_workers',job['workers'])
            ir=capture(plan,ic,cd,environment(plan,'stock',cd),cpus)
            im=metrics((cd/'process.log').read_text(errors='replace'))
            row.update(independent=ir,independent_metrics=im,route_sha256=h)
            assert h==sha256(d/'routed.route')
            row['success']=ir['returncode']==0 and im['full_check'] and all(im[k]==row[k] for k in ['critical_path_ns','wirelength'])
    else:
        row.update(component_evidence(row,d,entry['reference_map']['sha256']))
    if diagnostic: row['memory']=check_diagnostic(d,job['arm'])
    for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:
        assert sha256(d/name)==case['inputs'][role]['sha256']
    row.update(finished_utc=now(),loadavg_after=os.getloadavg(),artifacts=artifacts(d))
    write_json(d/'measurement.json',row);write_json(OUT/'summary.json',state)
    print(json.dumps({k:row.get(k) for k in ['key','returncode','success','component_valid','build_seconds']}),flush=True)
    if not full: assert row['component_valid'], 'Invalid construction sample'
    return row


def prepare_clma(plan,state,pool):
    c=plan['new_case'];d=OUT/'prepare_clma_2d';d.mkdir()
    cpus=pool[:8];os.sched_setaffinity(0,cpus);pin_budget(8)
    cmd=[plan['binaries']['original']['path'],c['architecture']['path'],c['circuit']['path'],
         '--pack','--place','--route','--analysis','--route_chan_width','100',
         '--device_width','0','--target_utilization','0.5','--seed','1',
         '--num_workers','8','--router_algorithm','parallel','--router_lookahead','map',
         '--flat_routing','off','--check_route','full','--net_file',str(d/'packed.net'),
         '--place_file',str(d/'fixed.place'),'--route_file',str(d/'routed.route'),
         '--write_rr_graph',str(d/'rr_graph.xml'),'--write_router_lookahead',str(d/'wire_map.bin'),
         '--max_router_iterations','1','--routing_failure_predictor','off','--timing_report_npaths','0']
    state['preparation']=dict(status='running',started_utc=now(),command=cmd)
    write_json(OUT/'summary.json',state)
    row=capture(plan,cmd,d,environment(plan,'stock',d),cpus)
    row['ready']=row['returncode'] in [0,2] and all((d/n).is_file() for n in ['packed.net','fixed.place','rr_graph.xml','wire_map.bin'])
    if row['ready']:
        paths=dict(architecture=c['architecture']['path'],circuit=c['circuit']['path'],packed_netlist=d/'packed.net',placement=d/'fixed.place',rr_graph=d/'rr_graph.xml')
        case={k:c[k] for k in ['seed','device_width','route_chan_width','target_utilization']}
        case.update(id='clma_2d',inputs={k:bind(v) for k,v in paths.items()})
        write_json(d/'vpr_case.json',case)
        row.update(case=bind(d/'vpr_case.json'),reference_map=bind(d/'wire_map.bin'))
    row.update(finished_utc=now(),artifacts=artifacts(d));write_json(d/'preparation.json',row)
    state['preparation'].update(row);write_json(OUT/'summary.json',state)
    print('clma preparation ready:',row['ready'],flush=True)
    return row


def run():
    plan=read(OUT/'plan.json');lock=(OUT/'owner.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (OUT/'summary.json').exists(),'Existing owner or previous attempt; never implicitly retry'
    for x in [*plan['runner_bindings'].values(),*plan['binaries'].values(),plan['runtime'],plan['build']]: verified(x)
    for path,digest in plan['source_bindings'].items(): assert sha256(path)==digest
    for x in [plan['new_case']['circuit'],plan['new_case']['architecture']]: verified(x)
    for entry in plan['cases'].values():
        verified(entry['reference_map']);case=read(verified(entry['case']))
        for x in case['inputs'].values(): verified(x)
    allowed=sorted(os.sched_getaffinity(0));topology=[];groups={}
    for cpu in allowed:
        p=Path(f'/sys/devices/system/cpu/cpu{cpu}');nodes=list(p.glob('node[0-9]*'))
        x=dict(cpu=cpu,core=int((p/'topology/core_id').read_text()),socket=int((p/'topology/physical_package_id').read_text()),node=int(nodes[0].name[4:]) if nodes else -1)
        topology.append(x);groups.setdefault(x['node'],{}).setdefault((x['socket'],x['core']),cpu)
    pools=sorted([sorted(x.values())[:16] for x in groups.values() if len(x)>=16]);assert pools
    pool=pools[0];os.sched_setaffinity(0,pool);budget=pin_budget(16)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    state=dict(status='running',pid=os.getpid(),hostname=socket.gethostname(),started_utc=now(),
        plan=bind(OUT/'plan.json'),pool=pool,topology=topology,initial_affinity=allowed,cpu_budget=budget,
        exclusive_host=False,measurements=[],skipped=[],cases=dict(plan['cases']))
    write_json(OUT/'summary.json',state)
    try:
        # Native pilot verifies both scheduler branches and diagnostics at1/8cores.
        for job in plan['jobs']:
            if job['phase']=='pilot':execute_one(plan,state,job,state['cases'][job['graph']],pool)
        prep=prepare_clma(plan,state,pool)
        if prep['ready']: state['cases']['clma_2d']={k:prep[k] for k in ['case','reference_map']}
        for job in plan['jobs']:
            if job['phase']=='pilot':continue
            if job['graph'] not in state['cases']:
                state['skipped'].append(job|dict(reason='clma_preparation_failed'));continue
            if job['phase']=='full_formal':
                if 'full_gate' not in state:
                    rows={r['arm']:r for r in state['measurements'] if r['phase']=='qualification'}
                    legal=len(rows)==4 and all(r['success'] for r in rows.values())
                    qs={a+'_vs_stock':quality(rows[a],rows['stock']) for a in ARMS} if legal else {}
                    if legal:qs.update({a+'_vs_per_group':quality(rows[a],rows['per_group']) for a in ['pipeline','flat']})
                    state['full_gate']=dict(passed=legal and all(q['passed'] for q in qs.values()),quality=qs)
                if not state['full_gate']['passed']:
                    state['skipped'].append(job|dict(reason='full_qualification_rejected'));continue
            execute_one(plan,state,job,state['cases'][job['graph']],pool)
        state['status']='completed'
    except Exception as exc:
        state.update(status='stopped_for_review',error=repr(exc));raise
    finally:
        state['finished_utc']=now();write_json(OUT/'summary.json',state)


if __name__=='__main__': {'freeze':freeze,'run':run}[sys.argv[1]]()
