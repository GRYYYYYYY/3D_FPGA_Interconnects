#!/usr/bin/env python3
"""Report whole timing-feedback workflows; retain failed epochs and attempts."""
import argparse
import csv
import json
from pathlib import Path
import statistics


def dump_csv(path, rows, fields):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def fmt(value, digits=3):
    return '—' if value is None else f'{value:.{digits}f}'


def report(run):
    source = json.loads((run / 'summary.json').read_text())
    rows = source['rows']
    keys = ['case', 'variant', 'repeat', 'status', 'success', 'workflow_seconds',
            'process_seconds', 'routing_seconds', 'search_seconds',
            'critical_path_ns', 'wirelength', 'full_check', 'selected_epoch']
    dump_csv(run / 'measurements.csv', rows, keys)
    epochs = []
    counters = ['preparations', 'searches', 'rounds', 'frontier_vertices',
                'h2d_bytes', 'd2h_bytes', 'prepare_seconds', 'search_seconds',
                'state_updates', 'window_vertices', 'window_fallbacks',
                'window_h2d_bytes','spatial_index_bytes','box_queries','cpu_window_seconds',
                'window_upload_seconds','window_init_seconds','relaxation_seconds','traceback_seconds',
                'state_update_seconds','tree_update_seconds']
    for row in rows:
        for e in row.get('epochs', [row]):
            epochs.append({**e, **{k: row[k] for k in ['case', 'variant', 'repeat']},
                           **(e.get('gpu_metrics') or {}),
                           'selected': e.get('epoch') == row.get('selected_epoch') if 'epoch' in e else None,
                           'overflow': (e.get('last_iteration') or {}).get('overflow'),
                           'unrouted': (e.get('last_iteration') or {}).get('unrouted'),
                           'validation_seconds': (e.get('validation') or {}).get('process_seconds')})
    dump_csv(run / 'epochs.csv', epochs,
             list(dict.fromkeys(keys + ['epoch', 'selected', 'iterations', 'overflow', 'unrouted',
                                       'audit_seconds', 'export_seconds', 'validation_seconds', 'feedback_seconds',
                                       'refinement_mode','refinement_converged','refinement_connections','refinement_accepted',
                                       'refinement_failed_overflow','refinement_failed_unrouted','congestion_connections_reused'] + counters)))
    baseline = {(r['case'], r['repeat']): r for r in rows if r['variant'] == 'vpr'}
    pairs = []
    for row in rows:
        if row['variant'] == 'vpr':
            continue
        b = baseline.get((row['case'], row['repeat']))
        p = {k: row[k] for k in ['case', 'variant', 'repeat']}
        p['eligible'] = bool(b and b.get('success') and b.get('full_check') and row.get('success') and row.get('full_check'))
        if p['eligible']:
            for k in ['workflow', 'process', 'routing', 'search']:
                bk, rk = b.get(k + '_seconds'), row.get(k + '_seconds')
                p[k + '_speedup'] = bk / rk if bk is not None and rk is not None and rk > 0 else None
            p['cpd_change_percent'] = 100 * (row['critical_path_ns'] / b['critical_path_ns'] - 1)
            p['wire_change_percent'] = 100 * (row['wirelength'] / b['wirelength'] - 1)
            p['quality_bands'] = {str(limit): all(row[k] <= b[k] * (1 + limit / 100) for k in ('critical_path_ns', 'wirelength'))
                                  for limit in [5, 10, 20]}
        pairs.append(p)
    (run / 'comparisons.json').write_text(json.dumps(pairs, indent=2) + '\n')
    phases = []
    for row in rows:
        if 'epochs' not in row or row.get('workflow_seconds') is None:
            continue
        item = {k: row[k] for k in ['case', 'variant', 'repeat', 'status', 'success', 'workflow_seconds']}
        for key in ['process_seconds', 'audit_seconds', 'export_seconds', 'feedback_seconds']:
            item[key] = sum(e.get(key, 0) for e in row['epochs'])
        item['native_seconds'] = sum(e.get('validation', {}).get('process_seconds', 0) for e in row['epochs'])
        item['routing_seconds'] = row.get('routing_seconds')
        item['initialization_and_process_overhead_seconds'] = (item['process_seconds'] - item['routing_seconds']
                                                               if item['routing_seconds'] is not None else None)
        item['other_seconds'] = row['workflow_seconds'] - sum(item[k] for k in
            ['process_seconds', 'audit_seconds', 'export_seconds', 'feedback_seconds', 'native_seconds'])
        phases.append(item)
    (run / 'workflow_phases.json').write_text(json.dumps(phases, indent=2) + '\n')
    lines = ['# 目标导向时序布线：同机对照', '',
             f"状态：`{source['status']}`；重复次数：{source['protocol']['repeats']}；每次最多 {source['protocol']['epochs']} 个反馈轮次。",
             f"代码不变：`{source.get('source_unchanged')}`；输入不变：`{source.get('inputs_unchanged')}`。", '',
             '完整流程含所有尝试的布线、审计、导出、原生 FULL/STA 和反馈。进程/主体/搜索时间对全部反馈轮次求和；',
             ('增量模式按 CPD 最小、再按线长选择合法检查点；完整重布线参考按 CPD×线长选择。' if source['protocol'].get('incremental_target') else
              'CPD/线长属于预先规定的 CPD×线长最小合法检查点。')+'离线投影、侧文件准备和输入哈希校验不计入在线流程。',
             ('本次使用 STA 派生关键度与树上开关延迟。' if source['protocol']['epochs'] > 1 else
              '本次仅一轮：关键度统一初始化为 0.5，保留树前缀延迟；只做 FULL/STA 验证，没有 STA 反馈重布线。'),
             '适用范围为已验证零 RC 的架构，不是原 VPR 的逐项复刻。', '',
             '| 电路 | 方法 | 合法/尝试 | 完整流程 s | 布线进程合计 s | 主体合计 s | 搜索合计 s | CPD ns | 线长 |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    aggregates = []
    for case in source['cases']:
        for variant in ['vpr', 'legacy_cuda', 'target_reference', 'target', 'cpu_target']:
            rr = [r for r in rows if r['case'] == case['id'] and r['variant'] == variant]
            if not rr:
                continue
            attempted = [r for r in rr if not r['status'].startswith('not_attempted')]
            good = [r for r in attempted if r.get('success')]
            def median(key):
                values = [r[key] for r in good if r.get(key) is not None]
                return statistics.median(values) if values else None
            ag = {'case': case['id'], 'variant': variant, 'attempts': len(attempted), 'successes': len(good),
                  **{k: median(k) for k in ['workflow_seconds', 'process_seconds', 'routing_seconds', 'search_seconds', 'critical_path_ns', 'wirelength']}}
            aggregates.append(ag)
            lines.append(f"| {case['id']} | {variant} | {len(good)}/{len(attempted)} | " +
                         ' | '.join(fmt(ag[k]) for k in ['workflow_seconds', 'process_seconds', 'routing_seconds', 'search_seconds', 'critical_path_ns']) +
                         ' | ' + fmt(ag['wirelength'], 0) + ' |')
    lines += ['', '时间表为合法尝试的中位数；失败耗时保留在下表与 CSV。一次尝试不能证明稳定加速。', '',
              '| 电路 | 方法/重复 | 完整流程加速比 | 主体加速比 | CPD 变化 | 线长变化 |',
              '|---|---|---:|---:|---:|---:|']
    for p in pairs:
        if p['eligible']:
            lines.append(f"| {p['case']} | {p['variant']}/{p['repeat']} | {fmt(p['workflow_speedup'])}× | " +
                         f"{fmt(p['routing_speedup'])}× | {p['cpd_change_percent']:+.2f}% | {p['wire_change_percent']:+.2f}% |")
    lines += ['', '加速比 = 同重复原 VPR 时间 / 候选流程时间；大于 1 才是加速。', '',
              '| 流程分解（全部尝试） | 路由进程 s | 独立审计 s | 导出 s | 原生 FULL/STA s | 反馈生成 s | 其他 s |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for item in phases:
        lines.append(f"| {item['case']}/{item['variant']}/{item['repeat']} | " +
                     ' | '.join(fmt(item[k]) for k in ['process_seconds', 'audit_seconds', 'export_seconds',
                                                      'native_seconds', 'feedback_seconds', 'other_seconds']) + ' |')
    lines += ['', '路由进程包括图/上下文初始化和全部路由阶段；原生回验可能重新加载原生资源图。其他项包括复制、结果解析、检查点与会话结束等。',
              '超时轮次的内部主体计时缺失时，不推算初始化和搜索耗时；完整已耗时间仍保留。', '',
              '| 失败尝试或反馈轮次 | 状态 | 已耗流程 s | 超用 | 未连通 |', '|---|---|---:|---:|---:|']
    for e in epochs:
        if not e.get('success') or e.get('refinement_converged') is False:
            label = f"{e['case']}/{e['variant']}/{e['repeat']}" + (f"/epoch_{e['epoch']}" if 'epoch' in e else '')
            rollback=e.get('refinement_converged') is False
            status='协商失败，已恢复合法树' if rollback else e['status']
            overflow=e.get('refinement_failed_overflow') if rollback else e.get('overflow','—')
            unrouted=e.get('refinement_failed_unrouted') if rollback else e.get('unrouted','—')
            lines.append(f"| {label} | {status} | {fmt(e.get('workflow_seconds'))} | {overflow} | {unrouted} |")
    lines += ['', '失败细化之前若有合法检查点，流程可保留该检查点，但失败轮次仍计时、仍列出。超时没有完整主体计时，保持缺失。', '',
              '| 电路 | 方法 | 已完成轮次累计 H2D GB | 前沿访问次数 | 稀疏状态记录 | 窗口节点次数 |',
              '|---|---|---:|---:|---:|---:|']
    for case in source['cases']:
        for variant in ['legacy_cuda', 'target_reference', 'target']:
            ee = [e for e in epochs if e['case'] == case['id'] and e['variant'] == variant and 'h2d_bytes' in e]
            if ee:
                lines.append(f"| {case['id']} | {variant} | {sum(e['h2d_bytes'] for e in ee)/1e9:.3f} | " +
                             ' | '.join(str(sum(e.get(k, 0) for e in ee)) for k in ['frontier_vertices', 'state_updates', 'window_vertices']) + ' |')
    lines += ['', '计数汇总覆盖所有产生完整内部计数的尝试（成功或失败），不补齐超时缺失值；不等同于整组完整计数。',
              'H2D 包括初始图/索引、稀疏占用/历史、树前缀及窗口列表或描述符。设备窗口按描述符的逻辑载荷计数，不是驱动实际 PCIe 流量；稀疏状态每条 12 字节。',
              '旧版稀疏状态计数为零表示未采用此接口，并非没有上传状态。',
              '旧版前沿计数、新版实际展开计数和 VPR 堆弹出不是等价操作，不能直接作为速度比。',
              'CPU/GPU 等代价路径可能不同；独立最短路 oracle 检查目标代价，原生 FULL/STA 检查实际完整树。', '']
    references = {(r['case'], r['repeat']): r for r in rows if r['variant'] == 'target_reference'}
    arithmetic = []
    if references:
        lines += ['| 冻结参考实现配对 | 完整流程加速比 | 主体加速比 | 搜索加速比 | 最终路径相同 |',
                  '|---|---:|---:|---:|---|']
        for row in rows:
            b = references.get((row['case'], row['repeat']))
            if row['variant'] != 'target' or not b or not row.get('success') or not b.get('success'):
                continue
            item = {'case': row['case'], 'repeat': row['repeat'],
                    'path_equal': row.get('route_fingerprint') == b.get('route_fingerprint')}
            for key in ['workflow', 'routing', 'search']:
                bk, rk = b.get(key + '_seconds'), row.get(key + '_seconds')
                item[key + '_speedup'] = bk / rk if bk is not None and rk is not None and rk > 0 else None
            arithmetic.append(item)
            lines.append(f"| {row['case']}/{row['repeat']} | " +
                         ' | '.join(fmt(item[k + '_speedup']) + '×' for k in ['workflow', 'routing', 'search']) +
                         f" | {item['path_equal']} |")
        lines += ['', '该表比较本次候选与任务指定的冻结参考实现；具体差异见任务配置，不能把该加速比当作对原 VPR 的加速比。', '']
        (run / 'arithmetic_comparisons.json').write_text(json.dumps(arithmetic, indent=2) + '\n')
    (run / 'report.md').write_text('\n'.join(lines))
    (run / 'aggregate.json').write_text(json.dumps(aggregates, indent=2) + '\n')
    return source, aggregates


def plot(run, source, aggregates):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    order = [c['id'] for c in source['cases'] if c.get('category') != 'congestion']
    if not order:
        order = [c['id'] for c in source['cases']]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout='constrained')
    present = {row['variant'] for row in source['rows']}
    for variant in [v for v in ['vpr', 'legacy_cuda', 'target_reference', 'target', 'cpu_target'] if v in present]:
        by_case = {r['case']: r for r in aggregates if r['variant'] == variant}
        for ax, key, label in zip(axes, ['workflow_seconds', 'critical_path_ns'], ['Full fixed-endpoint workflow (s)', 'Critical path (ns)']):
            values = [by_case.get(c, {}).get(key) for c in order]
            ax.plot(range(len(order)), [float('nan') if v is None else v for v in values], marker='o', label=variant)
            ax.set_xticks(range(len(order)), order, rotation=15)
            ax.set_ylabel(label); ax.grid(alpha=.25); ax.legend()
    axes[0].set_yscale('log')
    fig.suptitle('FULL-checked routes; all feedback epochs timed; gaps indicate failure')
    fig.savefig(run / 'target_scaling.png', dpi=180); fig.savefig(run / 'target_scaling.svg')
    plt.close(fig)

    # Plot measured points without connecting them into an assumed scaling law.
    pairs = json.loads((run / 'comparisons.json').read_text())
    points = []
    for case in source['cases']:
        selected = [p for p in pairs if p['case'] == case['id'] and p['variant'] == 'target' and p['eligible']]
        baseline = [r for r in source['rows'] if r['case'] == case['id'] and r['variant'] == 'vpr' and r.get('success')]
        if not selected or not baseline:
            continue
        graph = json.loads((Path(case['projection']) / 'manifest.json').read_text())
        points.append(dict(case=case['id'], nodes=graph['nodes'],
                           vpr_routing_seconds=statistics.median(r['routing_seconds'] for r in baseline),
                           speedup=statistics.median(p['workflow_speedup'] for p in selected),
                           quality=all(p['quality_bands']['5'] for p in selected)))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout='constrained')
    for ax, key, label in zip(axes, ['nodes', 'vpr_routing_seconds'],
                              ['RRG nodes', 'Original VPR routing time (s)']):
        for index, point in enumerate(points):
            ax.scatter(point[key], point['speedup'], color='#137c66' if point['quality'] else '#bb6507', s=48)
            ax.annotate(point['case'], (point[key], point['speedup']), xytext=(4, 7 if index % 2 == 0 else -15), textcoords='offset points', fontsize=8)
        ax.axhline(1, color='#555555', linestyle='--', linewidth=1)
        ax.set_xscale('log'); ax.set_xlabel(label); ax.set_ylabel('Full-workflow speedup over VPR')
        ax.grid(alpha=.2); ax.margins(x=.2, y=.2); ax.set_ylim(bottom=0)
    bootstrap = source['protocol'].get('congestion_mode') or 'frozen default'
    refinement = source['protocol'].get('refine_mode') or ('incremental STA' if source['protocol'].get('incremental_target') else 'full restart')
    fig.suptitle(f"{bootstrap} bootstrap / {refinement} refinement\n"
                 'Measured pairs: green <=5% CPD/wire loss; orange exceeds budget', fontsize=11)
    fig.savefig(run / 'target_crossover.png', dpi=180); fig.savefig(run / 'target_crossover.svg')
    plt.close(fig)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--plot', action='store_true')
    a = p.parse_args()
    source, aggregates = report(a.run)
    if a.plot:
        plot(a.run, source, aggregates)
    print(a.run / 'report.md')
