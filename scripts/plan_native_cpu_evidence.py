"""Freeze the three-way, held-out-placement and core-scaling study."""
import copy
import json
from pathlib import Path
import shutil
from prepare import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/native_cpu_evidence_20261102'


def stage_plan(stage, cases, workers, variants, caches, repeats):
    plan = json.loads((ROOT/'results/native_pipeline_confirm_20261102/plan.json').read_text())
    plan['output'] = str(OUT/stage)
    plan['variants']['stock'] = {'binary':'original', 'parallel':False}
    plan['variants'] = {k:plan['variants'][k] for k in variants}
    lane = {'cpu_pool':list(range(32,32+max(workers))), 'cases':[]}
    for case_id, case_path in cases:
        phases=[]
        for rep in range(repeats):
            desired = variants if rep==0 else list(reversed(variants)) if rep==1 else variants[1:]+variants[:1]
            shift = rep % len(desired)
            declared = desired[-shift:]+desired[:-shift] if shift else desired
            for n in (workers if rep%2==0 else list(reversed(workers))):
                for cache in (caches if rep%2==0 else list(reversed(caches))):
                    phases.append(dict(name=stage,variants=declared,workers=[n],cache_modes=[cache],
                                       repeats=1,repeat_start=rep,intended_execution_order=desired))
        lane['cases'].append(dict(id=case_id,vpr_case=str(case_path),phases=phases))
    plan['lanes']={'serial':lane}
    plan['max_active_cpu_cores']=max(workers)
    plan['planned_samples']=len(cases)*len(workers)*len(variants)*len(caches)*repeats
    plan['concurrency_scope']='One sequential lane; physical cores starting at CPU32, one NUMA node; no owned preparation or solver overlaps. Shared host; no hardware exclusivity.'
    plan['promotion_rule']={'quality':'Both routes legal, independent FULL/STA, CPD and wirelength regression <=5%',
        'triad':'Pipeline/stock GEMM rebuild all three process ratios >1, median >1.05; frozen/pipeline attribution separately reported',
        'heldout':'Per-placement quality required; report each placement and circuit equally, do not pool placements as independent circuits. All failed cases retained.',
        'scope':'Evidence development, no automatic default switch. Stock variant deliberately avoids inherited original-failure skipping so all planned repetitions remain attempted.'}
    plan['repeats_scope']='Triad/scaling: three runtime repeats of fixed placement. Generalization: two newly generated placements per circuit, one runtime sample per arm/cache/placement.'
    return plan


def main():
    OUT.mkdir(exist_ok=False)
    shutil.copyfile(ROOT/'HANDOFF.md',OUT/'HANDOFF.before_study.md')
    inp=OUT/'sources';inp.mkdir()
    selected=[]
    for name in ['alu4','diffeq','s38417']:
        source=ROOT/'vendor/vtr_cpu_paper/vtr_flow/benchmarks/blif'/f'{name}.blif'
        target=inp/source.name;shutil.copyfile(source,target);text=target.read_text()
        selected.append(dict(id=name,source=str(source),path=str(target),sha256=sha256(target),
                             names=text.count('\n.names'),latches=text.count('\n.latch')))
    arch=Path(json.loads((ROOT/'data/scaling_20261025/ex5p/vpr_case.json').read_text())['inputs']['architecture']['path'])
    shutil.copyfile(arch,inp/'architecture.xml')
    protocol=dict(status='frozen',stages=['triad','prepare','generalization','scaling','audit'],
        selected_circuits=selected,selection='Selected before measuring: combinational ALU, sequential arithmetic, larger sequential logic; no use in prior CPU optimization matrices.',
        architecture=dict(path=str(inp/'architecture.xml'),sha256=sha256(inp/'architecture.xml'),source=str(arch)),
        placement_seeds=[1,2],route_chan_width=100,device_width=0,target_utilization=.6,
        preparation='Fresh original-VPR pack/place/serial route for each seed, timeout1800s, max200 routing iterations; preserve any failure, no timing-based replacements.',
        hardware={'cpu_quota':'54 cores','memory_limit_gib':300,'cpuset_partition':'member','exclusive_cpu_set':False,'scheduler_available':False},
        native_samples=66,preparation_runs=6,default_change=False)
    write_json(OUT/'protocol.json',protocol)
    gemm=[('gemm',ROOT/'data/scaling_20261025/gemm/vpr_case.json')]
    write_json(OUT/'triad_plan.json',stage_plan('triad',gemm,[8],['stock','frozen','pipeline'],['rebuild','reuse'],3))
    held=[(f"{c['id']}_s{s}",OUT/'prepared'/f"{c['id']}_s{s}"/'vpr_case.json') for c in selected for s in [1,2]]
    write_json(OUT/'generalization_plan.json',stage_plan('generalization',held,[8],['stock','frozen','pipeline'],['rebuild','reuse'],1))
    write_json(OUT/'scaling_plan.json',stage_plan('scaling',gemm,[4,16],['frozen','pipeline'],['rebuild'],3))
    print(OUT)


if __name__=='__main__':main()
