"""Freeze stage-specific comparisons before launching native CPU experiments."""
import argparse
import json
from pathlib import Path

from prepare import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_cpu_slices_20261101'


def require_gate(stage):
    """A completed process is insufficient: every native gate must be legal."""
    plan = json.loads((OUT/(stage+'_plan.json')).read_text())
    count = 0
    for lane in plan['lanes']:
        summary = json.loads((Path(plan['output'])/lane/'summary.json').read_text())
        if summary['status'] != 'completed' or not summary.get('all_routes_successful'):
            raise RuntimeError('Gate not passed: '+stage+'/'+lane)
        for row in summary['measurements']:
            if not row['success'] or not row.get('wire_map_matches_serial'):
                raise RuntimeError('Native gate failure: '+row['key'])
            count += 1
    if count != plan['planned_samples']:
        raise RuntimeError('Incomplete gate sample count: '+stage)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['diagnostic', 'slice_gate', 'storage_gate', 'confirmation'])
    parser.add_argument('--binary', type=Path, required=True)
    args = parser.parse_args()
    old = json.loads((ROOT/'results/native_cpu_paper_20261031/plan.json').read_text())
    paths = {}
    for lane in old['lanes'].values():
        for case in lane['cases']: paths[case['id']] = case['vpr_case']
    paths['ex5p_2d'] = str(ROOT/'results/native_cpu_paper_20261031/architecture_inputs_v2/ex5p_native_l1_w100/vpr_case.json')
    binaries = {'original':old['binaries']['original'],
                'cpu':{'path':str(args.binary.resolve()), 'sha256':sha256(args.binary)},
                'frozen':{'path':str(ROOT/'results/native_cpu_paper_20261031/bin/vpr_cpu'),
                          'sha256':sha256(ROOT/'results/native_cpu_paper_20261031/bin/vpr_cpu')}}
    variants = {name:{'binary':'cpu','parallel':True,'env':{'VPR_CPU_LOOKAHEAD_MODE':name}}
                for name in ['legacy','refactored','slice','compact','bounded']}
    variants['pipeline'] = {'binary':'cpu','parallel':True,'env':{'VPR_HYBRID_LOOKAHEAD_TASKS':'1'}}
    variants['frozen'] = {'binary':'frozen','parallel':True}
    variants['bounded']['env']['VPR_CPU_LOOKAHEAD_UNALIGNED'] = '0'
    lanes = {}
    memory_config = None
    if args.stage in ['storage_gate','confirmation']:
        require_gate('slice_gate')
        if args.stage == 'confirmation':
            require_gate('storage_gate')
            if (OUT/'alignment_gate_plan.json').exists(): require_gate('alignment_gate')
        memory_path = OUT/'memory_config.json'
        memory_config = json.loads(memory_path.read_text())
        variants['bounded']['env'].update(memory_config['environment'])

    def add(name, cases, cores, names, workers, caches, repeats=1, repeat_start=0):
        lanes[name] = {'cpu_pool':cores, 'cases':[{'id':case,'vpr_case':paths[case],
            'phases':[{'name':args.stage,'variants':names,'workers':workers,'cache_modes':caches,
                       'repeats':repeats,'repeat_start':repeat_start}]} for case in cases]}

    if args.stage == 'diagnostic':
        add('gemm',['gemm'],list(range(0,4)),['frozen','legacy','refactored','pipeline'],[4],['rebuild'])
        add('elliptic',['elliptic'],list(range(8,12)),['frozen','legacy','refactored','pipeline'],[4],['rebuild'])
    elif args.stage == 'slice_gate':
        add('small',['ex5p_2d','ex5p'],list(range(16,24)),['slice'],[1,4,8],['rebuild'])
        add('gemm',['gemm'],list(range(24,32)),['slice'],[1,4,8],['rebuild'])
        add('elliptic',['elliptic'],list(range(32,40)),['slice'],[1,4,8],['rebuild'])
    elif args.stage == 'storage_gate':
        add('small',['ex5p_2d','ex5p'],list(range(16,24)),['compact','bounded'],[1,4,8],['rebuild'])
        add('gemm',['gemm'],list(range(0,8)),['compact','bounded'],[4],['rebuild'])
        add('elliptic',['elliptic'],list(range(8,16)),['compact','bounded'],[4],['rebuild'])
    else:
        # Split the slower GEMM 4/8-core runs, while elliptic repeats remain
        # sequential. Eight disjoint lanes use 48 physical cores in total.
        formal_variants = ['frozen','slice','compact','pipeline','bounded']
        for i in range(3):
            add('gemm_w4_r'+str(i),['gemm'],list(range(4*i,4*i+4)),formal_variants,[4],['rebuild','reuse'],repeat_start=i)
            first=[12,20,32][i]
            add('gemm_w8_r'+str(i),['gemm'],list(range(first,first+8)),formal_variants,[8],['rebuild','reuse'],repeat_start=i)
        add('elliptic_w4',['elliptic'],list(range(28,32)),formal_variants,[4],['rebuild','reuse'],repeats=3)
        add('elliptic_w8',['elliptic'],list(range(40,48)),formal_variants,[8],['rebuild','reuse'],repeats=3)
        orders = [['frozen','slice','compact','pipeline','bounded'],
                  ['bounded','pipeline','compact','slice','frozen'],
                  ['slice','pipeline','frozen','bounded','compact']]
        for lane in lanes.values():
            for case in lane['cases']:
                original = case['phases'][0]
                phases = []
                for repeat in range(original['repeat_start'], original['repeat_start'] + original['repeats']):
                    desired = orders[repeat]
                    shift = repeat % len(desired)
                    # The inherited runner rotates jobs by repeat. Undo that
                    # rotation here to obtain the explicitly declared order.
                    declared = desired[-shift:] + desired[:-shift] if shift else desired
                    caches = ['reuse','rebuild'] if repeat == 1 else ['rebuild','reuse']
                    for cache in caches:
                        phases.append(dict(original, variants=declared, cache_modes=[cache],
                                           repeats=1, repeat_start=repeat,
                                           intended_execution_order=desired))
                case['phases'] = phases
    scripts = ['run_native_cpu_slices.py','supervise_native_cpu_slices.py','run_native_cpu_study.py',
               'native_cpu_budget.py','scaling_common.py','report_native_joint.py','run_native_hybrid.py','prepare.py']
    plan = {'output':str(OUT/args.stage), 'runtime':old['runtime'], 'binaries':binaries,
            'variants':variants,'lanes':lanes,'timeout_seconds':900,'max_active_cpu_cores':48,
            'diagnostics':args.stage in ['diagnostic','storage_gate'],
            'qualification_env':{'VPR_CPU_LOOKAHEAD_MODE': 'refactored' if args.stage=='diagnostic' else 'slice' if args.stage=='slice_gate' else 'bounded'},
            'runner_bindings':{name:{'path':str(ROOT/'scripts'/name),'sha256':sha256(ROOT/'scripts'/name)} for name in scripts},
            'concurrency_scope':'Disjoint physical CPU sets across lanes; same set within each comparison. Shared host and memory; no exclusivity claim.',
            'measurement_scope':'Full VPR process including identical map serialization, native FULL/STA; fixed pack/place, identical input pre-read. Separate independent FULL/STA readback in workflow.',
            'quality_gate':{'critical_path_max_regression_percent':5,'wirelength_max_regression_percent':5,'overused_nodes':0},
            'repeats_scope':'Runtime repeats at one fixed placement seed; retain all failures. Diagnostic runs excluded from speedup claims.'}
    if memory_config:
        plan['memory_config'] = memory_config
        plan['qualification_env'].update(memory_config['environment'])
        plan['qualification_env']['VPR_CPU_LOOKAHEAD_UNALIGNED'] = '0'
    plan['promotion_rule'] = {
        'primary':'bounded versus frozen, GEMM rebuild at both 4 and 8 cores',
        'require_all_three_process_ratios_above':1.0,
        'require_median_process_ratio_above':1.02,
        'elliptic_and_cache_median_process_max_regression_percent':2,
        'all_routes_maps_quality_must_pass':True,
        'note':'Conservative engineering selection; runtime repeats on a shared host are not a publication confidence interval.'}
    if args.stage == 'confirmation':
        plan['additional_control_rationale'] = 'D0 did not reproduce the historical refactoring penalty. Include same-binary ordered pipeline to distinguish existing cross-group parallelism from scalar storage and bounded slice submission; declared before formal measurements.'
    count = sum(len(p['variants'])*len(p['workers'])*len(p['cache_modes'])*p['repeats']
                for lane in lanes.values() for c in lane['cases'] for p in c['phases'])
    plan['planned_samples'] = count
    target = OUT/(args.stage+'_plan.json')
    if target.exists(): raise RuntimeError('Refuse to replace a frozen plan')
    write_json(target,plan)
    print(json.dumps({'plan':str(target),'planned_samples':count}))


if __name__=='__main__':
    main()
