"""Frozen conditional-subset four-arm qualification and paired native flow study."""
from collections import defaultdict
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import statistics
import sys

from native_cpu_budget import pin_budget
from prepare import sha256, write_json
from qualify_native_cpu_width120 import quality
from report_native_joint import log_evidence
from run_native_cpu_study import cpu_command, set_option
from run_native_hybrid import route_body
from run_native_lookahead_component import captured_process
from scaling_common import metrics, verified, vpr_command, vpr_environment

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/native_cpu_width120_baseline_20261104'
OUT = ROOT/'results/native_cpu_width120_endtoend_20261104'
ARMS = ['stock', 'fixed_serial', 'per_group', 'pipeline']
SWITCHES = {'stock': ('0', '0'), 'fixed_serial': ('0', '0'), 'per_group': ('0', '1'), 'pipeline': ('1', '1')}
COMPARISONS = [('stock', 'fixed_serial'), ('stock', 'per_group'), ('stock', 'pipeline'),
               ('fixed_serial', 'per_group'), ('fixed_serial', 'pipeline'), ('per_group', 'pipeline')]


def read(p): return json.loads(Path(p).read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def binding(p): return dict(path=str(Path(p).resolve()), sha256=sha256(p))


def pair_quality(control, candidate):
    if not control.get('success') or not candidate.get('success'):
        return dict(eligible=False, passed=False)
    return quality(candidate, control)


def block_gate(arms, reference):
    complete = set(arms) == set(ARMS)
    legal = complete and all(r.get('success') for r in arms.values())
    prior = {a: quality(arms[a], reference) for a in ARMS[1:] if a in arms}
    paired = {a+'_to_'+b: pair_quality(arms[a], arms[b]) for a, b in COMPARISONS if a in arms and b in arms}
    same_elf = legal and all(q['passed'] for q in prior.values()) and all(
        paired[a+'_to_'+b]['passed'] for a, b in [('fixed_serial', 'per_group'), ('fixed_serial', 'pipeline'), ('per_group', 'pipeline')])
    return dict(passed=bool(same_elf), all_four_legal=bool(legal), corrected_vs_prior=prior, comparisons=paired,
                route_body_variants=len({r.get('route_body_sha256') for r in arms.values() if r.get('success')}))


def freeze():
    parent = read(BASE/'plan.json')
    assert read(BASE/'independent_review.json')['status'] == read(BASE/'acceptance.json')['status'] == 'passed'
    OUT.mkdir(exist_ok=False)
    names = list(parent['cases']); jobs = []
    def add(phase, case_name, repeat, mode, arm):
        key = f'{phase}_{case_name}_{mode}_r{repeat}_{arm}'; d = OUT/key; entry = parent['cases'][case_name]
        case = read(entry['case']['path']); binary = parent['binaries']['original' if arm == 'stock' else 'cpu']['path']
        command = cpu_command(binary, case, d, {'router': 'parallel'}, 8,
                              cache=entry['cache']['path'] if mode == 'reuse' else None, iterations=200)
        set_option(command, '--write_router_lookahead', d/'wire_map.bin')
        task, parallel = SWITCHES[arm]
        jobs.append(dict(key=key, phase=phase, case=case_name, repeat=repeat, mode=mode, arm=arm, directory=str(d),
            environment={'VPR_HYBRID_LOOKAHEAD_TASKS': task, 'VPR_HYBRID_LOOKAHEAD_PARALLEL': parallel}, command=command,
            independent_command=vpr_command(parent['binaries']['original']['path'], case, d, 200, route=False)))
    for i, name in enumerate(names):
        for j in range(4): add('qualification', name, 0, 'rebuild', ARMS[(i+j) % 4])
    for repeat in range(3):
        for offset in range(3):
            name = names[(repeat+offset) % 3]
            modes = ['rebuild', 'reuse'] if (repeat+offset) % 2 == 0 else ['reuse', 'rebuild']
            for mode_idx, mode in enumerate(modes):
                for j in range(4): add('formal', name, repeat, mode, ARMS[(repeat+offset+mode_idx+j) % 4])
    scripts = ['run_native_width120_endtoend.py', 'qualify_native_cpu_width120.py', 'native_cpu_budget.py', 'prepare.py',
               'report_native_joint.py', 'run_native_cpu_study.py', 'run_native_hybrid.py', 'run_native_lookahead_component.py', 'scaling_common.py']
    plan = dict(status='frozen', created_utc=now(), cases=parent['cases'], binaries=parent['binaries'], runtime=parent['runtime'], jobs=jobs,
        source_baseline_plan=binding(BASE/'plan.json'), source_baseline_review=binding(BASE/'independent_review.json'),
        source_baseline_acceptance=binding(BASE/'acceptance.json'), source_six_layout_summary=parent['source_six_layout_summary'],
        runner_bindings={name: binding(ROOT/'scripts'/name) for name in scripts}, cpu_pool=list(range(32, 40)),
        workers=8, max_iterations=200, timeout_seconds=900, address_space_gib=64, minimum_free_disk_gib=60,
        qualification_runs=12, formal_runs=72, repeats=3, default_changed=False, exclusive_host=False,
        selection='Exactly the predeclared LSTM_s2/BNN_s1/BNN_s2 layouts whose corrected cached baseline passed all9 repetitions. This is a conditional subset, not a six-layout generalization claim; original3/6 feasibility and width100 failures remain.',
        arms='Stock is the original binary with native parallel routing/eight-core budget. Other3 arms use the identical corrected ELF with only lookahead switches varied. State fixes remain enabled; stock comparisons include repair/trajectory differences.',
        qualification='All12 rebuild runs must have identical wire maps, native zero-overuse/FULL, independent original FULL/STA, actual commands/env/CPU and unchanged inputs. Each corrected arm CPD/WL <=1.05 prior width120 baseline; per_group <=1.05 fixed_serial; pipeline <=1.05 fixed_serial and per_group. Route identity is recorded, not required. Stock-relative5% quality is separately required for each stock speed claim.',
        formal='Exactly72 fresh runs:3 layouts x4 arms x2 cache modes x3 repeats, sequential rotated order. All rows checked. No qualification/pilot/history pooled into timings. Any numerical failure or corrected-quality gate failure prevents whole-subset aggregate claims; all outcomes retained without replacements.',
        statistics='Primary ratio: complete native process wall. Pair by layout/mode/repeat, report3 ratios and median/range per layout, then equal-layout geometric mean. Stock contrasts require all their pairwise5% CPD/WL gates. Workflow= native+independent process wall, excluding copy/hash/preflight; native-flow timer and routing time are secondary sensitivity measures.',
        time_boundary='Every run loads the same existing RR graph and fixed packed/placed inputs; map serialization is enabled uniformly in rebuild/reuse and included in process time. Reuse reads the exact shared wire cache; src/opin still computed. No comparison to prior RR-generating runs, and no cold-cache or exclusive-host claim.',
        execution='One solver or independent checker at a time on eight physical cores32-39. Capture actual commands/env/affinities, cgroup/memory/load. Clear inherited experimental overrides. Integrity failures stop; no retry or width/time escalation.',
        stop_policy='Only after the12 frozen qualifications all pass may this same owner proceed to the72 frozen formal runs. Rejected qualification leaves formal unstarted. Terminal audit/report written automatically; main-model review required before conclusions/default decisions.',
        original_width100_gate='failed_preserved', original_formal144_started=False, gpu_claim=False)
    write_json(OUT/'plan.json', plan)
    print('Frozen12 qualifications + conditional72 complete-process paired runs', flush=True)


def grouped_gates(rows, plan):
    blocks = defaultdict(dict)
    for row in rows: blocks[(row['case'], row['mode'], row['repeat'])][row['arm']] = row
    return {'|'.join(map(str, key)): block_gate(arms, plan['cases'][key[0]]['reference_metrics']) for key, arms in blocks.items()}


def audit_rows(rows, plan, name):
    artifacts = {}
    for row in rows:
        d = Path(row['directory']); parsed = metrics((d/'process.log').read_text(errors='replace'))
        assert all(parsed[k] == row[k] for k in ['routing_success', 'full_check', 'critical_path_ns', 'wirelength', 'iterations'])
        expected_success = False
        if row.get('independent_check'):
            checked = metrics((d/'independent/process.log').read_text(errors='replace'))
            expected_success = bool(row['returncode'] == 0 and parsed['routing_success'] and parsed['full_check']
                and row['map_matches_reference'] and log_evidence(d)['final_overused_nodes'] == 0
                and row['independent_check']['returncode'] == 0 and checked['full_check']
                and all(parsed[k] == checked[k] for k in ['critical_path_ns', 'wirelength']))
            assert sha256(d/'routed.route') == row['route_sha256']
            assert route_body(d/'routed.route') == row['route_body_sha256']
        assert row['success'] == expected_success, 'Legality classification mismatch'
        if (d/'wire_map.bin').exists(): assert sha256(d/'wire_map.bin') == row['map_sha256']
        for filename in ['measurement.json', 'process.log', 'process.log.resources.json', 'wire_map.bin', 'routed.route',
                         'independent/process.log', 'independent/process.log.resources.json', 'report_overused_nodes.rpt']:
            if (d/filename).exists(): artifacts[str(d/filename)] = sha256(d/filename)
    write_json(OUT/name, dict(status='passed', measurements=len(rows), bindings=artifacts,
        note='Evidence validity does not turn numerical failures into legal routes. Gate and performance eligibility are separate.'))


def report(plan, state):
    formal = [r for r in state['measurements'] if r['phase'] == 'formal']
    gates = grouped_gates(formal, plan)
    complete = state['status'] == 'completed' and len(formal) == 72 and (OUT/'audit.json').exists() and read(OUT/'audit.json')['status'] == 'passed'
    eligible = complete and len(gates) == 18 and all(g['passed'] for g in gates.values())
    results = {}; aggregates = {}
    if eligible:
        indexed = {(r['case'], r['mode'], r['repeat'], r['arm']): r for r in formal}
        for mode in ['rebuild', 'reuse']:
            results[mode] = {}; aggregates[mode] = {}
            for a, b in COMPARISONS:
                label = a+'_to_'+b; details = {}; all_passed = True
                for case in plan['cases']:
                    controls = [indexed[case, mode, i, a] for i in range(3)]
                    candidates = [indexed[case, mode, i, b] for i in range(3)]
                    qs = [pair_quality(x, y) for x, y in zip(controls, candidates)]
                    passed = all(q['passed'] for q in qs); all_passed = all_passed and passed
                    ratios = {}
                    if passed:
                        for metric in ['process_seconds', 'workflow_seconds', 'flow_seconds', 'routing_seconds']:
                            values = [x[metric]/y[metric] for x, y in zip(controls, candidates)]
                            ratios[metric] = dict(ratios=values, median=statistics.median(values), minimum=min(values), maximum=max(values))
                    details[case] = dict(quality_passed=passed, quality=qs, timing_ratios=ratios)
                results[mode][label] = details
                if all_passed:
                    aggregates[mode][label] = {metric: math.exp(statistics.mean(math.log(d['timing_ratios'][metric]['median']) for d in details.values()))
                        for metric in ['process_seconds', 'workflow_seconds', 'flow_seconds', 'routing_seconds']}
    result = dict(status=state['status'], formal_planned=72, formal_attempted=len(formal), formal_legal=sum(bool(r.get('success')) for r in formal),
        complete_audited_cohort=complete, corrected_quality_gate_passed=bool(eligible), block_gates=gates,
        paired_results=results, geometric_mean_of_layout_paired_medians=aggregates,
        qualification_gate=state.get('qualification_gate'), conditional_subset=list(plan['cases']),
        original_six_layouts_legal=3, original_six_layouts_total=6, default_changed=False)
    write_json(OUT/'analysis.json', result)
    lines = ['# 宽120条件子集四臂完整布线实验', '',
        '固定此前声明的LSTM_s2、BNN_s1、BNN_s2，原六布局3合法/3失败保持；不是六布局全部成功。原版与三个修复版配置均原生parallel路由、八物理核，后三者同ELF。共享宿主。',
        '12项rebuild资格通过后才运行72项独立正式样本：四臂、重建/缓存、各三次。资格和既有样本不并入。全体使用已有RR图和固定布局，进程计时包含统一map写出；不与旧生成RR的进程相除。', '',
        f'状态：{state["status"]}；正式执行{len(formal)}/72，合法{result["formal_legal"]}。',
        f'完整审计队列：{complete}；修复版质量门槛：{bool(eligible)}。', '']
    if aggregates:
        lines += ['|缓存模式|对照→候选|完整进程配对中位几何平均|含独立检查的workflow|', '|---|---|---:|---:|']
        for mode, contrasts in aggregates.items():
            for label, values in contrasts.items(): lines.append(f'|{mode}|{label}|{values["process_seconds"]:.6f}×|{values["workflow_seconds"]:.6f}×|')
        lines += ['', '全部单次配对、范围、CPD/WL质量差异及内部flow/routing敏感性见analysis.json。Stock对照含正确性修复/轨迹差异，不能全归因于lookahead；同ELF组内→pipeline用于增量归因。',
                  '缓存仍重算src/opin，缓存差异不自动等于纯路由差异。缺少stock相对比值表示该质量门槛不通过，不得丢掉坏配对再汇总。']
    if state.get('error'): lines += ['', '停止原因：'+state['error']]
    lines += ['', '默认不改，无GPU收益主张。原宽100严格端点失败和144项未启动保持。本协议以合法性/5%质量评价新条件子集，并显式记录route-body变化，不回填旧门槛。']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')


def run():
    plan = read(OUT/'plan.json')
    with (OUT/'owner.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUT/'summary.json').exists(): raise RuntimeError('Existing chain; observe instead of restarting')
        bindings = list(plan['runner_bindings'].values())+list(plan['binaries'].values())
        bindings += [plan[k] for k in ['runtime', 'source_baseline_plan', 'source_baseline_review', 'source_baseline_acceptance', 'source_six_layout_summary']]
        cases = {}; inputs = {}
        for name, item in plan['cases'].items():
            bindings += [item[k] for k in ['case', 'cache', 'reference']]
            cases[name] = read(verified(item['case']))
            for e in cases[name]['inputs'].values(): inputs[e['path']] = e
        def verify_all():
            for entry in bindings+list(inputs.values()): verified(entry)
        verify_all()
        env = {k: v for k, v in vpr_environment(read(plan['runtime']['path'])).items()
               if not k.startswith(('VPR_CPU_', 'VPR_HYBRID_', 'H3D_GPU_'))}
        resource.setrlimit(resource.RLIMIT_AS, (64*1024**3, 64*1024**3)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.sched_setaffinity(0, plan['cpu_pool']); budget = pin_budget(8)
        state = dict(status='running', pid=os.getpid(), started_utc=now(), plan_binding=binding(OUT/'plan.json'), cpu_budget=budget,
                     measurements=[], default_changed=False)
        write_json(OUT/'summary.json', state)
        def check_process(proc, command, local):
            expected = {k: v for k, v in local.items() if k.startswith(('VPR_', 'H3D_GPU_')) or k in ['OMP_NUM_THREADS', 'LC_ALL']}
            assert proc['actual_process'].get('command') == command and proc['actual_process'].get('environment') == expected
            assert proc['actual_process'].get('cpu_set') == plan['cpu_pool']
            assert proc['cpu_budget_audit']['verified'] and proc['cpu_budget_audit']['permitted_cpu_set'] == plan['cpu_pool']
        try:
            for job in plan['jobs']:
                if job['phase'] == 'formal' and not state.get('qualification_gate'):
                    rows = [r for r in state['measurements'] if r['phase'] == 'qualification']
                    verify_all(); verified(state['plan_binding']); audit_rows(rows, plan, 'qualification_audit.json')
                    gates = grouped_gates(rows, plan)
                    passed = len(rows) == 12 and len(gates) == 3 and all(g['passed'] for g in gates.values())
                    state['qualification_gate'] = dict(passed=passed, blocks=gates, measurements=len(rows), utc=now())
                    write_json(OUT/'qualification_gate.json', state['qualification_gate']); write_json(OUT/'summary.json', state)
                    if not passed: state['status'] = 'qualification_rejected'; break
                assert shutil.disk_usage(OUT).free > 60*1024**3, 'Disk floor'
                d = Path(job['directory']); d.mkdir(); case = cases[job['case']]; local = env | job['environment']
                for role, name in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]: shutil.copyfile(case['inputs'][role]['path'], d/name)
                row = dict(**job, status='running', success=False, loadavg_before=os.getloadavg())
                state['measurements'].append(row); write_json(OUT/'summary.json', state)
                row.update(captured_process(job['command'], d, local, 900)); text = (d/'process.log').read_text(errors='replace')
                row.update(metrics(text)); flow = re.findall(r'The entire flow of VPR took ([\d.]+) seconds', text)
                row['flow_seconds'] = float(flow[-1]) if flow else None
                row['loadavg_after'] = os.getloadavg(); write_json(d/'measurement.json', row)
                row['log_evidence'] = log_evidence(d); check_process(row, job['command'], local)
                row['map_sha256'] = sha256(d/'wire_map.bin') if (d/'wire_map.bin').exists() else None
                row['map_matches_reference'] = row['map_sha256'] == plan['cases'][job['case']]['cache']['sha256']
                if row['map_sha256'] is not None: assert row['map_matches_reference'], 'Map mismatch'
                build = row['log_evidence']['stage_seconds']['lookahead_build']
                if job['mode'] == 'reuse': assert build is None, 'Unexpected rebuild in reuse mode'
                elif row['returncode'] == 0: assert build is not None and build > 0, 'Missing completed rebuild'
                if row['returncode'] == 0 and row['routing_success'] and row['full_check'] and row['map_matches_reference']:
                    assert row['log_evidence']['final_overused_nodes'] == 0
                    row['route_sha256'] = sha256(d/'routed.route'); row['route_body_sha256'] = route_body(d/'routed.route')
                    cd = d/'independent'; cd.mkdir()
                    for name in ['packed.net', 'fixed.place', 'routed.route']: (cd/name).symlink_to(d/name)
                    checked_process = captured_process(job['independent_command'], cd, local, 900)
                    check_process(checked_process, job['independent_command'], local)
                    checked = metrics((cd/'process.log').read_text(errors='replace'))
                    row.update(independent_check=checked_process, independent_metrics=checked)
                    row['success'] = bool(checked_process['returncode'] == 0 and checked['full_check'] and all(checked[k] == row[k] for k in ['critical_path_ns', 'wirelength']))
                    row['workflow_seconds'] = row['process_seconds']+checked_process['process_seconds']
                    assert sha256(d/'routed.route') == row['route_sha256']
                    if row['success']: assert row['flow_seconds'] and row['routing_seconds'], 'Missing positive timers'
                row['prior_quality'] = quality(row, plan['cases'][job['case']]['reference_metrics'])
                for role, name in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]: assert sha256(d/name) == case['inputs'][role]['sha256']
                row['finished_utc'] = now(); write_json(d/'measurement.json', row); write_json(OUT/'summary.json', state); report(plan, state)
                print(json.dumps({k: row.get(k) for k in ['key', 'returncode', 'success', 'iterations', 'critical_path_ns', 'wirelength']}), flush=True)
            else: state['status'] = 'completed'
            verify_all(); verified(state['plan_binding']); audit_rows(state['measurements'], plan, 'audit.json')
        except Exception as exc:
            state.update(status='stopped_for_review', error=repr(exc)); raise
        finally:
            state['finished_utc'] = now(); write_json(OUT/'summary.json', state); report(plan, state)


if __name__ == '__main__': {'freeze': freeze, 'run': run}[sys.argv[1]]()
