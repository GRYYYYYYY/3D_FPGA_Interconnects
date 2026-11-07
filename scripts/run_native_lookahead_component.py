"""Native lookahead construction study on three byte-distinct width120 RR graphs.

The routing tail is capped at one iteration. A valid construction measurement is
never classified as successful routing or used for end-to-end process speedups.
"""
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
import threading

from native_cpu_budget import audited_process, pin_budget
from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_cpu_study import cpu_command, set_option
from scaling_common import metrics, verified, vpr_environment

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/native_cpu_width120_20261104'
OUT = ROOT/'results/native_lookahead_component_20261104'
ARMS = ['stock', 'fixed_serial', 'per_group', 'pipeline']
ENV = {'stock': ('0', '0'), 'fixed_serial': ('0', '0'), 'per_group': ('0', '1'), 'pipeline': ('1', '1')}


def read(p): return json.loads(Path(p).read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def binding(p): return dict(path=str(Path(p).resolve()), sha256=sha256(p))


def command_for(binary, case, directory):
    command = cpu_command(binary, case, directory, {'router': 'parallel'}, 8, iterations=1)
    command.remove('--analysis')
    set_option(command, '--generate_rr_node_overuse_report', 'off')
    set_option(command, '--write_router_lookahead', directory/'wire_map.bin')
    return command


def freeze():
    summary = read(BASE/'summary.json'); parent = read(BASE/'plan.json')
    assert summary['status'] == 'completed' and read(BASE/'audit.json')['status'] == 'passed'
    groups = defaultdict(list)
    for row in summary['measurements']: groups[row['generated_rr_graph']['sha256']].append(row)
    assert len(groups) == 3 and all(len(rows) == 2 for rows in groups.values())
    OUT.mkdir(exist_ok=False)
    cases = {}
    for digest, rows in groups.items():
        rows.sort(key=lambda x: x['case'])
        row = rows[0]; name = row['case'].rsplit('_s', 1)[0]; d = Path(row['directory'])
        assert len({r['wire_map_sha256'] for r in rows}) == 1
        cases[name] = dict(case=binding(d/'vpr_case.json'), reference_map=binding(d/'wire_map.bin'),
                           rr_sha256=digest, rr_bytes=Path(row['generated_rr_graph']['path']).stat().st_size,
                           represented_layouts=[r['case'] for r in rows], representative=row['case'],
                           historical_routing_outcomes={r['case']: r['success'] for r in rows})
    jobs = []
    def add(phase, name, repeat, arm):
        key = f'{phase}_{name}_r{repeat}_{arm}'; directory = OUT/key
        case = read(cases[name]['case']['path']); task, parallel = ENV[arm]
        jobs.append(dict(key=key, phase=phase, graph=name, repeat=repeat, arm=arm, directory=str(directory),
            environment={'VPR_HYBRID_LOOKAHEAD_TASKS': task, 'VPR_HYBRID_LOOKAHEAD_PARALLEL': parallel},
            command=command_for(parent['binaries']['original' if arm == 'stock' else 'cpu']['path'], case, directory)))
    for arm in ARMS: add('pilot', 'bnn', 0, arm)
    names = sorted(cases)
    for repeat in range(3):
        for offset in range(3):
            name = names[(offset+repeat) % 3]
            for i in range(4): add('formal', name, repeat, ARMS[(i+offset+repeat) % 4])
    scripts = ['run_native_lookahead_component.py', 'native_cpu_budget.py', 'prepare.py',
               'report_native_joint.py', 'run_native_cpu_study.py', 'scaling_common.py']
    source_names = ['vpr/src/base/vpr_api.cpp', 'vpr/src/route/router_lookahead/router_lookahead.cpp',
                    'vpr/src/route/router_lookahead/router_lookahead_map.cpp',
                    'vpr/src/route/router_lookahead/router_lookahead_map_utils.cpp']
    plan = dict(status='frozen', created_utc=now(), protocol='native_component_width120_v1', cases=cases, jobs=jobs,
        source_summary=binding(BASE/'summary.json'), source_audit=binding(BASE/'audit.json'),
        binaries=parent['binaries'], runtime=parent['runtime_binding'],
        runner_bindings={f: binding(ROOT/'scripts'/f) for f in scripts},
        scope_source_bindings={f: binding(ROOT/'vendor/vtr_cpu_slices'/f) for f in source_names},
        cpu_pool=list(range(32, 40)), workers=8, timeout_seconds=900, address_space_gib=64,
        minimum_free_disk_gib=60, pilot_runs=4, formal_runs=36, repeats=3,
        selection='All three byte-distinct RR graphs from all six preselected width120 layouts, including failures. Lowest layout id represents each identical graph; no selection by candidate timing or route legality.',
        timing='Use only complete Computing router lookahead map wall timer, including wire sampling/src-opin/minima; excludes graph loading, serialization, routing and process exit. Rebuild is not cold-filesystem-cache testing.',
        equivalence='Every serialized wire map must match the frozen width120 serial reference and the stock pilot where applicable. Serialization does not include all derived src/opin data; no expanded equivalence claim.',
        tail='Native parallel router is capped at one iteration after construction. Explicit analysis and overuse report are disabled uniformly. Normal rc2 with one completed iteration and implementation-failed footer is expected; route failure is preserved separately.',
        validity='Require exactly one complete positive build timer preceding Routing, byte-identical wire map, actual declared env/command, verified eight-core affinity and normal capped-process exit (0 or expected2). Timeout/crash/partial/mismatch is ineligible.',
        decision='All four pilots must pass before36 formal runs. Numerical formal failures are retained and prevent complete-cohort speedup claims; provenance/affinity/env drift stops. No automatic retries.',
        statistics='Pair within graph/repeat, report three ratios and median/range; geometric mean over three graph medians only if all36 formal measurements valid. Pilot/history excluded. Same-ELF contrasts isolate construction switches; stock contrast separately labelled.',
        concurrency='One solver at a time on physical cores32-39; shared host, no exclusivity claimed. Capture cgroup/load/actual env, clean inherited experimental switches.',
        end_to_end=dict(status='specified_not_submitted', prior_outcomes={r['case']: r['success'] for r in summary['measurements']},
            feasible_subset=['lstm_s2', 'bnn_s1', 'bnn_s2'],
            selection='Conditional subset determined solely by prior corrected-baseline width120 legality; all six outcomes must remain disclosed. Not a six-layout end-to-end success claim.',
            prerequisite='Fresh repeated baseline feasibility plus map/nativeFULL/independentFULL-STA qualification before any candidate timing matrix. Freeze exact commands/order/quality comparisons in a separate plan; do not retroactively alter width100 gates.',
            quality='At most5% CPD and wirelength regression against both same-ELF serial-build and per-group controls, with native and independent legality required. Route identity differences recorded rather than silently called identical; strict old endpoint gate remains failed.',
            eventual_design='Four arms, rebuild/reuse, three runtime repeats at identical eight-core budget on explicitly qualified subset; not submitted or automatically authorized by component completion.'),
        routing_success_claim=False, end_to_end_speedup_claim=False, default_changed=False)
    for entry in plan['binaries'].values(): verified(entry)
    write_json(OUT/'plan.json', plan)
    print('Frozen4 pilot +36 formal component runs on3 unique RR graphs', flush=True)


def captured_process(command, directory, env, timeout):
    captured = {}; stop = threading.Event(); owner = os.getpid()
    expected = str(command[0])
    def observe():
        while not stop.is_set():
            try:
                children = Path(f'/proc/{owner}/task/{owner}/children').read_text().split()
                for pid in children:
                    base = Path('/proc')/pid
                    args = [x.decode() for x in (base/'cmdline').read_bytes().split(b'\0') if x]
                    if not args or args[0] != expected: continue
                    values = {}
                    for item in (base/'environ').read_bytes().split(b'\0'):
                        if b'=' not in item: continue
                        k, v = item.decode().split('=', 1)
                        if k.startswith(('VPR_', 'H3D_GPU_')) or k in ['OMP_NUM_THREADS', 'LC_ALL']: values[k] = v
                    captured.update(pid=int(pid), command=args, environment=values,
                                    cpu_set=sorted(os.sched_getaffinity(int(pid))), utc=now())
                    return
            except (FileNotFoundError, ProcessLookupError): pass
            stop.wait(.1)
    watcher = threading.Thread(target=observe, daemon=True); watcher.start()
    try: outcome = audited_process(command, directory, env, timeout)
    finally: stop.set(); watcher.join(timeout=2)
    outcome['actual_process'] = captured
    return outcome


def component_evidence(row, directory, expected_digest):
    text = (directory/'process.log').read_text(errors='replace')
    timers = list(re.finditer(r'# Computing router lookahead map took ([\d.]+) seconds', text))
    routing = re.search(r'^# Routing\s*$', text, re.MULTILINE)
    digest = sha256(directory/'wire_map.bin') if (directory/'wire_map.bin').exists() else None
    evidence = log_evidence(directory); trace = evidence.get('iterations', [])
    normal_exit = len(trace) == 1 and trace[0]['iteration'] == 1 and (row['returncode'] == 0 or (
        row['returncode'] == 2 and 'VPR failed to implement circuit' in text))
    complete = len(timers) == 1 and routing is not None and timers[0].end() < routing.start()
    seconds = float(timers[0][1]) if len(timers) == 1 else None
    valid = bool(complete and seconds > 0 and normal_exit and row['status'] != 'timeout' and digest == expected_digest)
    return dict(component_valid=valid, build_seconds=seconds, complete_timer_before_routing=complete,
                normal_capped_exit=normal_exit, wire_map_sha256=digest, map_matches_reference=digest == expected_digest,
                tail_iterations=len(trace), routing_success_observed=row['routing_success'],
                routing_legality_independently_checked=False, log_evidence=evidence)


def report(plan, state):
    formal = [r for r in state['measurements'] if r['phase'] == 'formal']
    full = (state['status'] == 'completed' and len(formal) == 36
            and all(r.get('component_valid') for r in formal)
            and (OUT/'audit.json').exists() and read(OUT/'audit.json')['status'] == 'passed')
    comparisons = [('stock', 'pipeline'), ('fixed_serial', 'per_group'), ('fixed_serial', 'pipeline'), ('per_group', 'pipeline')]
    graph_results = {}
    if full:
        indexed = {(r['graph'], r['repeat'], r['arm']): r for r in formal}
        for graph in plan['cases']:
            pairs = {}
            for a, b in comparisons:
                ratios = [indexed[graph, i, a]['build_seconds']/indexed[graph, i, b]['build_seconds'] for i in range(3)]
                pairs[a+'_to_'+b] = dict(ratios=ratios, median=statistics.median(ratios), minimum=min(ratios), maximum=max(ratios))
            graph_results[graph] = dict(median_build_seconds={arm: statistics.median(indexed[graph, i, arm]['build_seconds'] for i in range(3)) for arm in ARMS}, comparisons=pairs)
    aggregate = {a+'_to_'+b: math.prod(g['comparisons'][a+'_to_'+b]['median'] for g in graph_results.values())**(1/3)
                 for a, b in comparisons} if full else {}
    result = dict(status=state['status'], formal_planned=36, formal_attempted=len(formal), formal_valid=sum(bool(r.get('component_valid')) for r in formal),
                  complete_cohort=full, graphs=graph_results, geometric_mean_of_graph_paired_medians=aggregate,
                  end_to_end_speedup_claim=False, default_changed=False, independent_rr_graphs=3, represented_layouts=6)
    write_json(OUT/'analysis.json', result)
    lines = ['# 原生lookahead三图阶段实验', '',
        '六布局按RR图逐字节去重后为三个独立图，全部纳入，不按路由成功筛选。四个pilot不并入36项正式测量。共享宿主，同八个物理核。',
        '仅报告完整lookahead构建计时：包含wire、src/opin和minima，排除RR加载、map序列化及路由。序列化wire map逐字节核验不等于所有派生表均被序列化验证。',
        '路由尾部统一限制一轮，未布通是保留的原生结果；component_valid不代表路由合法，不计算进程/端到端加速。', '',
        f'状态：{state["status"]}；正式执行{len(formal)}/36，有效{result["formal_valid"]}。', '']
    if full:
        lines += ['|图|原版构建秒|修复串行秒|组内秒|pipeline秒|组内→pipeline配对中位|', '|---|---:|---:|---:|---:|---:|']
        for name, g in graph_results.items():
            t = g['median_build_seconds']
            lines.append('|'+name+'|'+'|'.join(f'{t[a]:.2f}' for a in ARMS)+f'|{g["comparisons"]["per_group_to_pipeline"]["median"]:.4f}×|')
        lines += ['', '三个图配对速度比中位的等权几何平均：'+json.dumps(aggregate),
                  '每图仅三次runtime重复，范围与全部单次比值见analysis.json；不声称独占或普遍性能。原版对照与同ELF消融分开解释。']
    if state.get('error'): lines += ['', '停止原因：'+state['error']]
    lines += ['', '全部六布局既有宽120结果仍3合法/3失败。端到端条件子集协议尚未提交；旧宽100失败和144项未启动结论保持，默认不变。']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')


def run():
    plan = read(OUT/'plan.json')
    with (OUT/'owner.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUT/'summary.json').exists(): raise RuntimeError('Existing chain; observe instead of restarting')
        bindings = list(plan['runner_bindings'].values())+list(plan['scope_source_bindings'].values())+list(plan['binaries'].values())
        bindings += [plan[k] for k in ['source_summary', 'source_audit', 'runtime']]
        inputs = {}; cases = {}
        for name, item in plan['cases'].items():
            bindings += [item['case'], item['reference_map']]
            cases[name] = read(verified(item['case']))
            for entry in cases[name]['inputs'].values(): inputs[entry['path']] = entry
        for entry in bindings+list(inputs.values()): verified(entry)
        env = {k: v for k, v in vpr_environment(read(plan['runtime']['path'])).items()
               if not k.startswith(('VPR_CPU_', 'VPR_HYBRID_', 'H3D_GPU_'))}
        resource.setrlimit(resource.RLIMIT_AS, (64*1024**3, 64*1024**3)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.sched_setaffinity(0, plan['cpu_pool']); budget = pin_budget(8)
        state = dict(status='running', pid=os.getpid(), started_utc=now(), plan_binding=binding(OUT/'plan.json'),
                     cpu_budget=budget, measurements=[], default_changed=False)
        write_json(OUT/'summary.json', state)
        try:
            for job in plan['jobs']:
                if job['phase'] == 'formal' and not state.get('pilot_gate'):
                    pilots = [r for r in state['measurements'] if r['phase'] == 'pilot']
                    passed = len(pilots) == 4 and all(r.get('component_valid') for r in pilots)
                    state['pilot_gate'] = dict(passed=passed, jobs=[r['key'] for r in pilots], utc=now())
                    write_json(OUT/'pilot_gate.json', state['pilot_gate'])
                    if not passed:
                        state['status'] = 'pilot_rejected'; break
                assert shutil.disk_usage(OUT).free > plan['minimum_free_disk_gib']*1024**3, 'Disk floor'
                d = Path(job['directory']); d.mkdir(); case = cases[job['graph']]
                for role, name in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]: shutil.copyfile(case['inputs'][role]['path'], d/name)
                local = env | job['environment']
                row = dict(**job, status='running', component_valid=False, loadavg_before=os.getloadavg())
                state['measurements'].append(row); write_json(OUT/'summary.json', state)
                row.update(captured_process(job['command'], d, local, 900)); row.update(metrics((d/'process.log').read_text(errors='replace')))
                row['loadavg_after'] = os.getloadavg()
                write_json(d/'measurement.json', row)
                row.update(component_evidence(row, d, plan['cases'][job['graph']]['reference_map']['sha256']))
                actual = row['actual_process']; expected = {k: v for k, v in local.items() if k.startswith(('VPR_', 'H3D_GPU_')) or k in ['OMP_NUM_THREADS', 'LC_ALL']}
                assert actual.get('command') == job['command'] and actual.get('environment') == expected, 'Actual command/environment mismatch'
                assert row['cpu_budget_audit']['verified'] and row['cpu_budget_audit']['permitted_cpu_set'] == plan['cpu_pool'], 'CPU budget audit failed'
                if row['wire_map_sha256'] is not None: assert row['map_matches_reference'], 'Wire-map mismatch'
                for role, name in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]: assert sha256(d/name) == case['inputs'][role]['sha256']
                row['finished_utc'] = now(); write_json(d/'measurement.json', row); write_json(OUT/'summary.json', state)
                report(plan, state)
                print(json.dumps({k: row.get(k) for k in ['key', 'returncode', 'component_valid', 'build_seconds', 'routing_success_observed']}), flush=True)
            else: state['status'] = 'completed'
            for entry in bindings+list(inputs.values())+[state['plan_binding']]: verified(entry)
            artifacts = {}
            for row in state['measurements']:
                d = Path(row['directory'])
                observed = component_evidence(row, d, plan['cases'][row['graph']]['reference_map']['sha256'])
                assert all(row[k] == observed[k] for k in ['component_valid', 'build_seconds', 'wire_map_sha256', 'normal_capped_exit'])
                for filename in ['measurement.json', 'process.log', 'process.log.resources.json', 'wire_map.bin']:
                    if (d/filename).exists(): artifacts[str(d/filename)] = sha256(d/filename)
            write_json(OUT/'audit.json', dict(status='passed', bindings=artifacts, phase_validity_reparsed=True,
                note='Audit verifies evidence/provenance. Expected capped route failures are not legal routing successes.'))
        except Exception as exc:
            state.update(status='stopped_for_review', error=repr(exc)); raise
        finally:
            state['finished_utc'] = now(); write_json(OUT/'summary.json', state); report(plan, state)


if __name__ == '__main__': {'freeze': freeze, 'run': run}[sys.argv[1]]()
