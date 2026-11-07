"""Nine fresh cached corrected-baseline runs on the predeclared feasible subset."""
from collections import defaultdict
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import sys

from native_cpu_budget import pin_budget
from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_cpu_study import cpu_command, set_option
from run_native_hybrid import route_body
from run_native_lookahead_component import captured_process
from scaling_common import metrics, verified, vpr_command, vpr_environment

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/native_cpu_width120_20261104'
COMPONENT = ROOT/'results/native_lookahead_component_20261104'
OUT = ROOT/'results/native_cpu_width120_baseline_20261104'


def read(p): return json.loads(Path(p).read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def binding(p): return dict(path=str(Path(p).resolve()), sha256=sha256(p))


def quality(row, reference):
    if not row.get('success'): return dict(eligible=False, passed=False)
    cpd = row['critical_path_ns']/reference['critical_path_ns']-1
    wire = row['wirelength']/reference['wirelength']-1
    return dict(eligible=True, critical_path_change_percent=100*cpd,
                wirelength_change_percent=100*wire, passed=cpd <= .05+1e-9 and wire <= .05+1e-9)


def freeze():
    assert read(COMPONENT/'independent_review.json')['status'] == 'passed'
    parent = read(COMPONENT/'plan.json'); old = read(BASE/'summary.json')
    names = parent['end_to_end']['feasible_subset']
    assert sorted(names) == sorted(r['case'] for r in old['measurements'] if r['success'])
    OUT.mkdir(exist_ok=False)
    cases = {}
    for name in names:
        ref = next(r for r in old['measurements'] if r['case'] == name)
        d = Path(ref['directory'])
        cases[name] = dict(case=binding(d/'vpr_case.json'), cache=binding(d/'wire_map.bin'),
                           reference=binding(d/'measurement.json'), reference_metrics={k: ref[k] for k in ['critical_path_ns', 'wirelength', 'iterations', 'route_body_sha256']})
    jobs = []
    for repeat in range(3):
        for i in range(3):
            name = names[(i+repeat) % 3]; key = f'{name}_cached_baseline_r{repeat}'; d = OUT/key
            case = read(cases[name]['case']['path'])
            command = cpu_command(parent['binaries']['cpu']['path'], case, d, {'router': 'parallel'}, 8,
                                  cache=cases[name]['cache']['path'], iterations=200)
            set_option(command, '--write_router_lookahead', d/'wire_map.bin')
            jobs.append(dict(key=key, case=name, repeat=repeat, directory=str(d), command=command,
                             independent_command=vpr_command(parent['binaries']['original']['path'], case, d, 200, route=False)))
    scripts = ['qualify_native_cpu_width120.py', 'native_cpu_budget.py', 'prepare.py', 'report_native_joint.py',
               'run_native_cpu_study.py', 'run_native_hybrid.py', 'run_native_lookahead_component.py', 'scaling_common.py']
    plan = dict(status='frozen', created_utc=now(), cases=cases, jobs=jobs, binaries=parent['binaries'], runtime=parent['runtime'],
        source_component_plan=binding(COMPONENT/'plan.json'), source_component_review=binding(COMPONENT/'independent_review.json'),
        source_six_layout_summary=binding(BASE/'summary.json'),
        runner_bindings={name: binding(ROOT/'scripts'/name) for name in scripts},
        environment={'VPR_HYBRID_LOOKAHEAD_TASKS': '0', 'VPR_HYBRID_LOOKAHEAD_PARALLEL': '0'}, cpu_pool=list(range(32, 40)),
        timeout_seconds=900, max_iterations=200, repeats=3, address_space_gib=64, minimum_free_disk_gib=60,
        selection='Exactly the three layouts predeclared in the component plan, selected by prior corrected-baseline feasibility, not by candidate timing. Full six-layout3/6 historical outcome remains disclosed.',
        scope='Feasibility and quality prerequisite only; corrected ELF, cached wire map (src/opin still computed), native parallel eight-core routing. No candidate arms or speedup ratios.',
        acceptance='All9 runs must be native/legal/zero-overuse, map-identical, independently FULL/STA checked with matching CPD/WL, and each CPD/WL no worse than5% above its fixed prior width120 baseline. Route-body variation is reported, not treated as identity.',
        failure_policy='Retain all9 planned numerical outcomes without retries or replacement. Stop on provenance/map/actual-env/CPU drift. Any failed legality/quality blocks this prerequisite; no automatic candidate performance submission.',
        original_width100_gate='failed_preserved', original_formal144_started=False, candidate_performance_started=False,
        default_changed=False, exclusive_host=False, performance_claim=False)
    write_json(OUT/'plan.json', plan)
    print('Frozen9 baseline feasibility/quality runs; no candidate matrix', flush=True)


def report(plan, state):
    rows = state['measurements']; groups = defaultdict(list)
    for r in rows: groups[r['case']].append(r)
    audited = (OUT/'audit.json').exists() and read(OUT/'audit.json')['status'] == 'passed'
    complete = state['status'] == 'completed' and len(rows) == 9 and audited
    gate = dict(status='passed' if complete and all(r.get('success') and r.get('quality', {}).get('passed') for r in rows) else ('failed' if complete else 'pending'),
        attempted=len(rows), planned=9, legal=sum(bool(r.get('success')) for r in rows),
        quality_passed=sum(bool(r.get('quality', {}).get('passed')) for r in rows),
        cases={name: dict(attempted=len(rs), legal=sum(bool(r.get('success')) for r in rs),
            route_body_variants=len({r['route_body_sha256'] for r in rs if r.get('success')}),
            iterations=[r.get('iterations') for r in rs], critical_path_ns=[r.get('critical_path_ns') for r in rs if r.get('success')],
            wirelength=[r.get('wirelength') for r in rs if r.get('success')]) for name, rs in groups.items()},
        performance_claim=False, candidate_performance_started=False, original_six_layouts_legal=3, original_six_layouts_total=6)
    write_json(OUT/'acceptance.json', gate)
    lines = ['# 宽120条件子集重复基线资格', '',
        '预先声明LSTM_s2、BNN_s1、BNN_s2，各三次同修复ELF/同缓存/同八核原生并行路由。这里只验证重复合法性和相对既有基线的5%质量门槛，不计算速度比。',
        '原六布局3合法/3失败分母保留；不把条件子集说成全部六布局通过。', '',
        '|布局|重复|退出码|合法且独立复核|轮数|CPD ns|线长|质量门槛|', '|---|---:|---:|---|---:|---:|---:|---|']
    for r in rows:
        lines.append(f'|{r["case"]}|{r["repeat"]}|{r.get("returncode")}|{r.get("success", False)}|{r.get("iterations")}|{r.get("critical_path_ns") if r.get("success") else None}|{r.get("wirelength") if r.get("success") else None}|{r.get("quality", {}).get("passed", False)}|')
    lines += ['', f'队列状态：{state["status"]}；资格：{gate["status"]}；合法{gate["legal"]}/{len(rows)}，质量通过{gate["quality_passed"]}/{len(rows)}。',
              '最终route-body种类、全部迭代/质量值见acceptance.json；逐字节wire map一致不意味着路由主体一致。',
              '通过本资格仍需单独冻结原版/修复串行构建/组内/pipeline候选资格与完整性能协议，无自动后续提交。默认未改。']
    if state.get('error'): lines += ['', '停止原因：'+state['error']]
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')


def run():
    plan = read(OUT/'plan.json')
    with (OUT/'owner.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUT/'summary.json').exists(): raise RuntimeError('Existing chain; observe instead of restarting')
        bindings = list(plan['runner_bindings'].values())+list(plan['binaries'].values())
        bindings += [plan[k] for k in ['runtime', 'source_component_plan', 'source_component_review', 'source_six_layout_summary']]
        cases = {}; inputs = {}
        for name, item in plan['cases'].items():
            bindings += [item[k] for k in ['case', 'cache', 'reference']]
            cases[name] = read(verified(item['case']))
            for entry in cases[name]['inputs'].values(): inputs[entry['path']] = entry
        for entry in bindings+list(inputs.values()): verified(entry)
        env = {k: v for k, v in vpr_environment(read(plan['runtime']['path'])).items()
               if not k.startswith(('VPR_CPU_', 'VPR_HYBRID_', 'H3D_GPU_'))} | plan['environment']
        expected_env = {k: v for k, v in env.items() if k.startswith(('VPR_', 'H3D_GPU_')) or k in ['OMP_NUM_THREADS', 'LC_ALL']}
        resource.setrlimit(resource.RLIMIT_AS, (64*1024**3, 64*1024**3)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.sched_setaffinity(0, plan['cpu_pool']); budget = pin_budget(8)
        state = dict(status='running', pid=os.getpid(), started_utc=now(), plan_binding=binding(OUT/'plan.json'), cpu_budget=budget, measurements=[])
        write_json(OUT/'summary.json', state)
        def check_process(outcome, command):
            assert outcome['actual_process'].get('command') == command
            assert outcome['actual_process'].get('environment') == expected_env
            assert outcome['cpu_budget_audit']['verified'] and outcome['cpu_budget_audit']['permitted_cpu_set'] == plan['cpu_pool']
        try:
            for job in plan['jobs']:
                assert shutil.disk_usage(OUT).free > 60*1024**3, 'Disk floor'
                d = Path(job['directory']); d.mkdir(); case = cases[job['case']]
                for role, name in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]: shutil.copyfile(case['inputs'][role]['path'], d/name)
                row = dict(**job, status='running', success=False, environment=plan['environment'])
                state['measurements'].append(row); write_json(OUT/'summary.json', state)
                row.update(captured_process(job['command'], d, env, 900))
                row.update(metrics((d/'process.log').read_text(errors='replace')))
                write_json(d/'measurement.json', row)
                row['log_evidence'] = log_evidence(d)
                check_process(row, job['command'])
                row['map_sha256'] = sha256(d/'wire_map.bin') if (d/'wire_map.bin').exists() else None
                row['map_matches_reference'] = row['map_sha256'] == plan['cases'][job['case']]['cache']['sha256']
                if row['map_sha256'] is not None: assert row['map_matches_reference'], 'Cache mismatch'
                assert row['log_evidence']['stage_seconds']['lookahead_build'] is None, 'Unexpected rebuild'
                if row['returncode'] == 0 and row['routing_success'] and row['full_check'] and row['map_matches_reference']:
                    assert row['log_evidence']['final_overused_nodes'] == 0
                    row['route_sha256'] = sha256(d/'routed.route'); row['route_body_sha256'] = route_body(d/'routed.route')
                    # captured_process uses process.log, so run the independent check in
                    # a dedicated directory with identical local input filenames.
                    checkdir = d/'independent'; checkdir.mkdir()
                    for name in ['packed.net', 'fixed.place', 'routed.route']: (checkdir/name).symlink_to(d/name)
                    # Frozen command uses absolute parent filenames; only logs differ.
                    outcome = captured_process(job['independent_command'], checkdir, env, 900)
                    check_process(outcome, job['independent_command'])
                    checked = metrics((checkdir/'process.log').read_text(errors='replace'))
                    row.update(independent_check=outcome, independent_metrics=checked)
                    row['success'] = bool(outcome['returncode'] == 0 and checked['full_check']
                        and all(checked[k] == row[k] for k in ['critical_path_ns', 'wirelength']))
                    assert sha256(d/'routed.route') == row['route_sha256']
                row['quality'] = quality(row, plan['cases'][job['case']]['reference_metrics'])
                for role, name in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]: assert sha256(d/name) == case['inputs'][role]['sha256']
                row['finished_utc'] = now(); write_json(d/'measurement.json', row); write_json(OUT/'summary.json', state)
                report(plan, state)
                print(json.dumps({k: row.get(k) for k in ['key', 'returncode', 'success', 'iterations', 'critical_path_ns', 'wirelength', 'quality']}), flush=True)
            for entry in bindings+list(inputs.values())+[state['plan_binding']]: verified(entry)
            artifacts = {}
            for row in state['measurements']:
                d = Path(row['directory']); parsed = metrics((d/'process.log').read_text(errors='replace'))
                assert all(parsed[k] == row[k] for k in ['routing_success', 'full_check', 'critical_path_ns', 'wirelength', 'iterations'])
                if row['success']:
                    checked = metrics((d/'independent/process.log').read_text(errors='replace'))
                    assert checked['full_check'] and parsed['full_check'] and log_evidence(d)['final_overused_nodes'] == 0
                    assert all(parsed[k] == checked[k] for k in ['critical_path_ns', 'wirelength'])
                    assert sha256(d/'routed.route') == row['route_sha256']
                assert row['quality'] == quality(row, plan['cases'][row['case']]['reference_metrics'])
                for name in ['measurement.json', 'process.log', 'process.log.resources.json', 'wire_map.bin', 'routed.route',
                             'independent/process.log', 'independent/process.log.resources.json', 'report_overused_nodes.rpt']:
                    if (d/name).exists(): artifacts[str(d/name)] = sha256(d/name)
            write_json(OUT/'audit.json', dict(status='passed', bindings=artifacts, note='Artifacts/commands/env/CPU/inputs and quality reparsed; not a speedup study.'))
            state['status'] = 'completed'
        except Exception as exc:
            state.update(status='stopped_for_review', error=repr(exc)); raise
        finally:
            state['finished_utc'] = now(); write_json(OUT/'summary.json', state); report(plan, state)


if __name__ == '__main__': {'freeze': freeze, 'run': run}[sys.argv[1]]()
