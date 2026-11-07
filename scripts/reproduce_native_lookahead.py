"""Preview or reproduce frozen native controls in a fresh output directory.

New repetitions never enter historical paper statistics automatically.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import socket
import run_native_flat_baseline as base
from continue_native_flat_baseline import evidence_with_completed_log
from scaling_common import verified
from prepare import write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',required=True,choices=['tseng_2d','clma_2d','bnn','dla_like.medium','bnn_2d'])
    parser.add_argument('--workers',type=int,choices=[1,2,4,8,16],default=8)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--kind',choices=['component','full','memory'],default='component')
    parser.add_argument('--include-stock',action='store_true',help='Include original VPR at the same CPU budget; component/full only.')
    parser.add_argument('--execute',action='store_true',help='Without this flag, only print the concrete commands.')
    args=parser.parse_args();assert 1<=args.repeats<=10
    assert not (args.include_stock and args.kind=='memory'), 'Original ELF has no stage-memory instrumentation'
    parent=base.ROOT/'results'/('native_large2d_followup_20261105' if args.case=='bnn_2d' else 'native_flat_baseline_20261105')
    old=base.read(parent/'summary.json');plan=base.read(parent/'plan.json');entry=old['cases'][args.case]
    case=base.read(entry['case']['path']);out=args.output.resolve()
    assert not out.exists(),'Choose a fresh output directory'
    assert not any(out.is_relative_to(base.ROOT/'results'/n) for n in ['native_flat_baseline_20261105','native_large2d_followup_20261105']), 'Keep frozen evidence directories unchanged'
    phase={'component':'component_formal','full':'full_formal','memory':'memory_diagnostic'}[args.kind]
    jobs=[]
    methods=(['stock'] if args.include_stock else [])+base.ARMS
    for r in range(args.repeats):
        arms=methods[r%len(methods):]+methods[:r%len(methods)]
        for a in arms:jobs.append(dict(key=f'{phase}_{args.case}_w{args.workers}_r{r}_{a}',phase=phase,graph=args.case,workers=args.workers,repeat=r,arm=a))
    preview=[]
    for j in jobs:
        d=out/j['key'];binary=plan['binaries']['original' if j['arm']=='stock' else 'cpu']['path']
        cmd=base.cpu_command(binary,case,d,{'router':'parallel'},args.workers,iterations=200 if args.kind=='full' else 1)
        base.set_option(cmd,'--generate_rr_node_overuse_report','off');base.set_option(cmd,'--write_router_lookahead',d/'wire_map.bin')
        if args.kind!='full':cmd.remove('--analysis')
        env=base.environment(plan,j['arm'],d,args.kind=='memory')
        selected={k:v for k,v in env.items() if k.startswith(('VPR_','H3D_GPU_')) or k in ['OMP_NUM_THREADS','LC_ALL']}
        preview.append(j|dict(command=cmd,environment=selected,diagnostic=args.kind=='memory'))
    if not args.execute:
        print(json.dumps(dict(executed=False,output=str(out),jobs=preview,scope='Preview only. Corrected arms share one ELF; optional stock uses original ELF. All use the same inputs/reference map and CPU budget.'),indent=2));return
    # Refuse a competing local solver chain. A different host is a new population.
    for name in ['native_flat_baseline_20261105','native_large2d_followup_20261105']:
        p=base.ROOT/'results'/name/'summary.json'
        if p.exists():
            s=base.read(p)
            assert not (s['status']=='running' and s['hostname']==socket.gethostname()), 'Active paper solver on this host; do not overlap it'
    for x in [*plan['runner_bindings'].values(),*plan['binaries'].values(),plan['runtime'],plan['build'],entry['case'],entry['reference_map']]:verified(x)
    for x in case['inputs'].values():verified(x)
    topology=[];nodes={}
    for cpu in sorted(os.sched_getaffinity(0)):
        p=Path(f'/sys/devices/system/cpu/cpu{cpu}');ns=list(p.glob('node[0-9]*'))
        node=int(ns[0].name[4:]) if ns else -1
        core=(int((p/'topology/physical_package_id').read_text()),int((p/'topology/core_id').read_text()))
        nodes.setdefault(node,{}).setdefault(core,cpu)
    pools=sorted(sorted(v.values())[:args.workers] for v in nodes.values() if len(v)>=args.workers);assert pools
    pool=pools[0];os.sched_setaffinity(0,pool);budget=base.pin_budget(args.workers)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    out.mkdir(parents=True,exist_ok=False);base.OUT=out;base.log_evidence=evidence_with_completed_log
    new_plan=plan|dict(output=str(out),jobs=jobs,reproduction_script=base.bind(Path(__file__)),parent_plan=base.bind(parent/'plan.json'),paper_pooling=False)
    write_json(out/'plan.json',new_plan)
    state=dict(status='running',pid=os.getpid(),hostname=socket.gethostname(),started_utc=base.now(),plan=base.bind(out/'plan.json'),
        pool=pool,cpu_budget=budget,cases={args.case:entry},measurements=[],exclusive_host=False,paper_pooling=False)
    write_json(out/'summary.json',state)
    try:
        for job in jobs:base.execute_one(new_plan,state,job,entry,pool)
        state['status']='completed_unreviewed_new_cohort'
    except Exception as exc:
        state.update(status='stopped_for_review',error=repr(exc));raise
    finally:state['finished_utc']=base.now();write_json(out/'summary.json',state)


if __name__=='__main__':main()
