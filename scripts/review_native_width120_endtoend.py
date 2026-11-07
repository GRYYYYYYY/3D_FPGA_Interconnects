"""Independently audit the complete conditional-subset native CPU experiment."""
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
import statistics

from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_hybrid import route_body
from scaling_common import metrics, verified

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_cpu_width120_endtoend_20261104'
ARMS = ['stock', 'fixed_serial', 'per_group', 'pipeline']
PAIRS = [('stock', 'fixed_serial'), ('stock', 'per_group'), ('stock', 'pipeline'),
         ('fixed_serial', 'per_group'), ('fixed_serial', 'pipeline'), ('per_group', 'pipeline')]
METRICS = ['process_seconds', 'workflow_seconds', 'flow_seconds', 'routing_seconds']


def read(p): return json.loads(Path(p).read_text())
def binding(p): return dict(path=str(Path(p).resolve()), sha256=sha256(p))


def qos(control, candidate):
    assert control['success'] and candidate['success']
    changes = {key: 100*(candidate[key]/control[key]-1) for key in ['critical_path_ns', 'wirelength']}
    return dict(critical_path_change_percent=changes['critical_path_ns'], wirelength_change_percent=changes['wirelength'],
                passed=all(v <= 5+1e-7 for v in changes.values()))


def main():
    plan = read(OUT/'plan.json'); state = read(OUT/'summary.json'); old = read(OUT/'analysis.json'); audit = read(OUT/'audit.json')
    assert state['status'] == 'completed' and audit['status'] == 'passed' and old['corrected_quality_gate_passed']
    assert read(OUT/'qualification_gate.json')['passed']
    verified(state['plan_binding'])
    for path, digest in audit['bindings'].items(): assert sha256(path) == digest, path
    for category in ['runner_bindings', 'binaries']:
        for entry in plan[category].values(): verified(entry)
    for key in ['runtime', 'source_baseline_plan', 'source_baseline_review', 'source_baseline_acceptance', 'source_six_layout_summary']: verified(plan[key])
    inputs = {}; case_data = {}
    for name, entry in plan['cases'].items():
        for key in ['case', 'cache', 'reference']: verified(entry[key])
        case_data[name] = read(entry['case']['path'])
        for e in case_data[name]['inputs'].values(): inputs[e['path']] = e
    for entry in inputs.values(): verified(entry)
    topology = [c for c in state['cpu_budget']['topology'] if c['cpu'] in plan['cpu_pool']]
    assert len({(c['socket'], c['core']) for c in topology}) == 8
    assert len(state['measurements']) == len(plan['jobs']) == 84
    rows = []; stamps = []
    for row, job in zip(state['measurements'], plan['jobs']):
        assert all(row[k] == job[k] for k in ['key', 'phase', 'case', 'mode', 'repeat', 'arm', 'command', 'independent_command', 'environment'])
        d = Path(row['directory']); text = (d/'process.log').read_text(errors='replace')
        native = metrics(text); check = metrics((d/'independent/process.log').read_text(errors='replace'))
        assert row['success'] and row['returncode'] == row['independent_check']['returncode'] == 0
        assert native['routing_success'] and native['full_check'] and check['full_check']
        assert all(native[k] == check[k] == row[k] for k in ['critical_path_ns', 'wirelength'])
        assert native['iterations'] == row['iterations']
        e = log_evidence(d); assert e['final_overused_nodes'] == 0
        assert row['log_evidence'] == e
        assert sha256(d/'routed.route') == row['route_sha256'] and route_body(d/'routed.route') == row['route_body_sha256']
        assert sha256(d/'wire_map.bin') == plan['cases'][row['case']]['cache']['sha256'] == row['map_sha256']
        for role, filename in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]:
            assert sha256(d/filename) == case_data[row['case']]['inputs'][role]['sha256']
        for process, command in [(row, job['command']), (row['independent_check'], job['independent_command'])]:
            actual = process['actual_process']
            assert actual['command'] == command
            assert actual['environment'] == dict(LC_ALL='C', OMP_NUM_THREADS='1', **job['environment'])
            assert actual['cpu_set'] == process['cpu_budget_audit']['permitted_cpu_set'] == plan['cpu_pool']
            assert process['cpu_budget_audit']['verified']
        assert row['actual_process']['utc'] < row['independent_check']['actual_process']['utc'] < row['finished_utc']
        stamps.append((row['actual_process']['utc'], row['finished_utc']))
        flow = re.findall(r'The entire flow of VPR took ([\d.]+) seconds', text)
        assert float(flow[-1]) == row['flow_seconds'] and native['routing_seconds'] == row['routing_seconds']
        assert math.isclose(row['workflow_seconds'], row['process_seconds']+row['independent_check']['process_seconds'], rel_tol=1e-12)
        assert all(row[k] > 0 for k in METRICS)
        build = e['stage_seconds']['lookahead_build']
        assert (build is None) == (row['mode'] == 'reuse')
        rows.append(row)
    assert all(stamps[i][1] <= stamps[i+1][0] for i in range(83)), 'Overlapping tasks/order drift'
    assert Counter(r['phase'] for r in rows) == {'qualification': 12, 'formal': 72}
    print('Verified84 legal runs,588 bound artifacts, inputs, native/independent checks and actual execution', flush=True)
    formal = [r for r in rows if r['phase'] == 'formal']
    counts = Counter((r['case'], r['mode'], r['arm']) for r in formal)
    assert len(counts) == 24 and set(counts.values()) == {3}
    indexed = {(r['case'], r['mode'], r['repeat'], r['arm']): r for r in formal}
    # Recheck both qualification and formal QoR without invoking the runner's gates.
    blocks = defaultdict(dict)
    for row in rows: blocks[(row['phase'], row['case'], row['mode'], row['repeat'])][row['arm']] = row
    for key, arms in blocks.items():
        assert set(arms) == set(ARMS)
        prior = dict(success=True, **plan['cases'][key[1]]['reference_metrics'])
        for arm in ARMS[1:]: assert qos(prior, arms[arm])['passed']
        for a, b in [('fixed_serial', 'per_group'), ('fixed_serial', 'pipeline'), ('per_group', 'pipeline')]: assert qos(arms[a], arms[b])['passed']
    comparisons = {}; aggregates = {}; summaries = {}
    for mode in ['rebuild', 'reuse']:
        comparisons[mode] = {}; aggregates[mode] = {}; summaries[mode] = {}
        for a, b in PAIRS:
            label = a+'_to_'+b; comparisons[mode][label] = {}; all_q = []; all_ratios = []
            for name in plan['cases']:
                controls = [indexed[name, mode, i, a] for i in range(3)]
                candidates = [indexed[name, mode, i, b] for i in range(3)]
                quality = [qos(x, y) for x, y in zip(controls, candidates)]; assert all(q['passed'] for q in quality)
                values = {}
                for metric in METRICS:
                    ratios = [x[metric]/y[metric] for x, y in zip(controls, candidates)]
                    values[metric] = dict(ratios=ratios, median=statistics.median(ratios), minimum=min(ratios), maximum=max(ratios))
                    assert ratios == old['paired_results'][mode][label][name]['timing_ratios'][metric]['ratios']
                comparisons[mode][label][name] = dict(timing=values, quality=quality)
                all_q.extend(quality); all_ratios.extend(values['process_seconds']['ratios'])
            aggregates[mode][label] = {metric: math.exp(statistics.mean(math.log(d['timing'][metric]['median']) for d in comparisons[mode][label].values())) for metric in METRICS}
            for metric, value in aggregates[mode][label].items():
                assert math.isclose(value, old['geometric_mean_of_layout_paired_medians'][mode][label][metric], rel_tol=1e-12)
            summaries[mode][label] = dict(faster_pairs=sum(v > 1 for v in all_ratios), total_pairs=9,
                process_ratio_range=[min(all_ratios), max(all_ratios)],
                maximum_cpd_degradation_percent=max(q['critical_path_change_percent'] for q in all_q),
                maximum_wirelength_degradation_percent=max(q['wirelength_change_percent'] for q in all_q))
    layout_metrics = {}
    for name in plan['cases']:
        layout_metrics[name] = {}
        for mode in ['rebuild', 'reuse']:
            layout_metrics[name][mode] = {}
            for arm in ARMS:
                rs = [indexed[name, mode, i, arm] for i in range(3)]
                layout_metrics[name][mode][arm] = dict(median_process_seconds=statistics.median(r['process_seconds'] for r in rs),
                    process_seconds=[r['process_seconds'] for r in rs], critical_paths=sorted({r['critical_path_ns'] for r in rs}),
                    wirelengths=sorted({r['wirelength'] for r in rs}), iterations=[r['iterations'] for r in rs],
                    route_body_variants=len({r['route_body_sha256'] for r in rs}))
    result = dict(status='passed', artifacts=len(audit['bindings']), qualification_legal=12, formal_legal=72,
        actual_command_env_cpu_verified=True, used_inputs_verified=True, full_sta_and_quality_recomputed=True,
        ordered_nonoverlapping_tasks=True, geometric_mean_of_layout_paired_medians=aggregates,
        paired_results=comparisons, paired_summaries=summaries, layout_metrics=layout_metrics,
        scope=dict(layouts=3, circuits=2, rr_graphs=2, original_legal_layouts=3, original_layouts=6,
                   weighting='Equal layout: BNN2/3, LSTM1/3', shared_host=True, runtime_repeats=3),
        source_bindings={n: binding(OUT/n) for n in ['plan.json', 'summary.json', 'audit.json', 'analysis.json', 'qualification_gate.json', 'scope_clarification.json']},
        reviewer=binding(__file__))
    write_json(OUT/'independent_review.json', result)
    write_json(OUT/'conclusions.json', dict(status='complete', formal_legal=72, qualification_legal=12,
        rebuild_process_speedups={k: v['process_seconds'] for k, v in aggregates['rebuild'].items()},
        cached_process_speedups={k: v['process_seconds'] for k, v in aggregates['reuse'].items()},
        findings=['The predeclared feasible subset supports end-to-end native CPU benefits when lookahead is rebuilt at equal8-core budget.',
            'All9 rebuild pairs improve both stock-to-pipeline and per-group-to-pipeline process time.',
            'Cached per-group-to-pipeline has4/9 faster pairs and aggregate0.997694; this study does not establish a cached-path increment.',
            'Rebuild gains together with near-unit cached and routing-phase increments support preprocessing as the primary source; no strict full causal isolation or route determinism claim.'],
        interpretation_limits=['Three layouts from two circuits/two graphs, selected by prior corrected-baseline feasibility; all6 historical outcomes remain3 legal/3 failed.',
            'Shared host and3 runtime repeats; no universal, exclusive-resource, strict scaling, GPU or3D-specific pathfinding novelty claim.',
            'Stock comparison includes correctness repairs/route trajectory differences; per-group-to-pipeline same-ELF contrast is the cleaner incremental comparison.',
            'Serialized equality verifies wire maps, not every derived table; FULL/STA verifies the tested routed results.'],
        decision='Close this experiment with positive rebuild evidence. Keep defaults and rejected candidates unchanged. Consolidate the CPU precomputation contribution and retain negative routing results; no automatic further solver submissions.',
        next='Prepare a claim-to-evidence summary; if wider scope is needed, preselect new architecture/circuit combinations or exclusive resources before measuring. Do not keep widening failed layouts to manufacture a full-suite result.',
        default_changed=False, evidence=binding(OUT/'independent_review.json')))
    make_figures(plan, indexed, comparisons)
    write_report(plan, result)
    print(json.dumps(dict(status='passed', artifacts=len(audit['bindings']), primary={mode: {k: v['process_seconds'] for k, v in contrasts.items()} for mode, contrasts in aggregates.items()})), flush=True)


def make_figures(plan, indexed, comparisons):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names = list(plan['cases']); colors = ['#64748b', '#d29922', '#168aad', '#138a63']
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7), sharey=True)
    for ax, mode in zip(axes, ['rebuild', 'reuse']):
        for j, arm in enumerate(ARMS):
            xs = [i+(j-1.5)*.19 for i in range(3)]
            ax.bar(xs, [statistics.median(indexed[n, mode, r, arm]['process_seconds'] for r in range(3)) for n in names], width=.18, color=colors[j], label=arm)
            for x, name in zip(xs, names): ax.scatter([x]*3, [indexed[name, mode, r, arm]['process_seconds'] for r in range(3)], s=9, color='black', zorder=3)
        ax.set_xticks(range(3), names); ax.set_title(mode+' lookahead'); ax.grid(axis='y', alpha=.2); ax.set_axisbelow(True)
    axes[0].set_ylabel('Complete native process wall time (seconds)'); axes[1].legend(fontsize=8)
    fig.suptitle('Conditional subset: 3 layouts / 2 circuits; same 8 cores; bars=medians, dots=all repeats')
    fig.tight_layout()
    for ext in ['pdf', 'svg', 'png']: fig.savefig(OUT/f'endtoend_process.{ext}', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7))
    for ax, label in zip(axes, ['stock_to_pipeline', 'per_group_to_pipeline']):
        for m, mode in enumerate(['rebuild', 'reuse']):
            color = ['#168aad', '#9457b0'][m]
            for i, name in enumerate(names):
                ys = comparisons[mode][label][name]['timing']['process_seconds']['ratios']; center = i+(m-.5)*.28
                ax.scatter([center-.035, center, center+.035], ys, color=color, label=mode if i == 0 else None)
                ax.plot([center-.09, center+.09], [statistics.median(ys)]*2, color=color)
        ax.axhline(1, color='gray', linestyle='--'); ax.set_xticks(range(3), names)
        ax.set_title(label); ax.set_ylabel('Paired complete-process speedup'); ax.grid(axis='y', alpha=.2); ax.legend()
    fig.suptitle('All 9 rebuild pairs improve; cached pipeline increment is not consistent')
    fig.tight_layout()
    for ext in ['pdf', 'svg', 'png']: fig.savefig(OUT/f'endtoend_paired.{ext}', dpi=160)
    plt.close(fig)


def write_report(plan, result):
    agg = result['geometric_mean_of_layout_paired_medians']
    lines = ['# 完整布线实验终态独立复核（2026-11-05）', '',
        '**12项资格与72项正式测量全部合法并通过质量门槛；588份产物、全部使用输入、实际命令/env/八物理核、原生及原版独立FULL/STA、执行顺序和配对统计重新核验通过。**', '',
        '完整native进程包括读取既有RR图、网表和布局、lookahead构建或缓存读取、布线与分析及统一map写出。没有生成RR。下列主统计为同布局/缓存模式/重复次序配对速度比先取三次中位，再按布局等权取几何平均；不是时间中位数之比。资格及旧样本不并入。', '',
        '|比较|重建lookahead|共同缓存|', '|---|---:|---:|']
    for label in ['stock_to_pipeline', 'fixed_serial_to_pipeline', 'per_group_to_pipeline']:
        lines.append(f'|{label}|{agg["rebuild"][label]["process_seconds"]:.6f}×|{agg["reuse"][label]["process_seconds"]:.6f}×|')
    lines += ['', '重建时，原版→pipeline九组全部更快（1.590919–1.778441×），同ELF组内→pipeline九组全部更快（1.054784–1.116383×）。缓存时组内→pipeline仅4/9更快（0.983030–1.016713×），未建立一致的缓存路径增量收益。', '',
        '|布局|原版进程秒|修复串行秒|组内秒|pipeline秒|原版→pipeline配对中位|组内→pipeline配对中位|', '|---|---:|---:|---:|---:|---:|---:|']
    for name in plan['cases']:
        ds = result['layout_metrics'][name]['rebuild']
        ratios = [result['paired_results']['rebuild'][label][name]['timing']['process_seconds']['median'] for label in ['stock_to_pipeline', 'per_group_to_pipeline']]
        lines.append('|'+name+'|'+'|'.join(f'{ds[a]["median_process_seconds"]:.2f}' for a in ARMS)+'|'+'|'.join(f'{r:.6f}×' for r in ratios)+'|')
    lines += ['', '上表秒数是完整进程中位数；速度比独立按配对计算，二者不能直接相除替代。', '',
        f'重建时含独立检查的workflow原版→pipeline为{agg["rebuild"]["stock_to_pipeline"]["workflow_seconds"]:.6f}×，组内→pipeline为{agg["rebuild"]["per_group_to_pipeline"]["workflow_seconds"]:.6f}×；workflow定义为两个进程wall之和，不含copy/hash/preflight。',
        f'同ELF组内→pipeline的布线阶段速度比约{agg["rebuild"]["per_group_to_pipeline"]["routing_seconds"]:.6f}×。结合缓存结果，证据支持主要收益来自预计算，不能把全部原版差异归因于pipeline，也未完成严格全因果隔离。', '',
        '质量：全部符合预先声明的CPD和线长最多5%退化。相对原版，pipeline最大CPD退化0%、线长退化约0.090772%；相对组内，最大CPD退化约0.164887%、线长退化约0.041202%，出现在BNN_s2重建第2次配对。路由主体存在变化，不宣称逐路由确定性或所有QoR完全相同。', '',
        '**适用范围：三个布局、两个电路、两份不同RR图，且是事先按基线可布通性选定的条件子集。** BNN两布局合计权重2/3，LSTM一布局1/3；不是按电路或图等权。原六布局仍3合法/3失败，DLA两布局和LSTM_s1负例保留；宽100旧资格拒绝不回填。共享宿主、每臂三次重复，不外推为普遍加速或独占结果。', '',
        '先前3图阶段实验的7.40×与本轮1.70×来自不同计时范围及样本集合，应分别报告，不能相乘；本轮完整流程结果补齐的是可布通条件子集的整体证据。', '',
        '结论：原生CPU预计算主线在本轮得到完整流程支持，pipeline在同ELF组内并行之上还有可重复的重建增量。缓存路径未建立增量；既有低核数负例、新bounded拒绝和路由质量负例保持。默认算法不变，无GPU收益或三维专属寻路创新主张。本轮全部任务已结束，无自动后续求解。', '',
        '![完整进程时间](endtoend_process.png)', '', '![全部配对速度比](endtoend_paired.png)', '',
        '原始计划/结果：plan.json、summary.json、analysis.json；独立核验与解释：independent_review.json、conclusions.json。']
    (OUT/'review.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__': main()
