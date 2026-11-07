#!/usr/bin/env python3
"""Export all scale attempts and quality-qualified paired speedups, including failures."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import statistics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    a=p.parse_args();report=json.loads((a.run/'summary.json').read_text())
    fields=['case','category','variant','repeat','status','success','process_seconds','workflow_seconds',
            'routing_seconds','search_seconds','critical_path_ns','wirelength','full_check','iterations',
            'audit_seconds','export_seconds','offline_preparation_seconds','route_fingerprint']
    with (a.run/'measurements.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(report['rows'])
    work=[]
    for case in report['cases']:
        graph=json.loads((Path(case['projection']['unit'])/'manifest.json').read_text())
        prepared=json.loads(Path(case['prepared']).read_text())
        for row in report['rows']:
            if row['case']!=case['id']:continue
            gpu=row.get('gpu_metrics') or {}
            work.append({'case':case['id'],'variant':row['variant'],'repeat':row['repeat'],'status':row['status'],
                         'nodes':graph['nodes'],'edges':graph['edges'],'nets':graph['nets'],
                         'sinks':prepared['sinks'],'max_fanout':prepared['max_fanout'],
                         'native_heap_pops':row.get('heap_pops'),'native_heap_pushes':row.get('heap_pushes'),
                         'native_search_seconds':row.get('search_seconds') if row['variant']=='vpr' else None,
                         **{k:gpu.get(k) for k in ('preparations','searches','rounds','frontier_vertices','h2d_bytes','d2h_bytes','prepare_seconds','search_seconds')},
                         'audit_seconds':row.get('audit_seconds'),'export_seconds':row.get('export_seconds'),
                         'validation_seconds':(row.get('native_validation') or {}).get('process_seconds')})
    with (a.run/'work_counters.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,list(work[0]) if work else ['case']);writer.writeheader();writer.writerows(work)
    partial=[]
    for row in report['rows']:
        if row['variant']=='vpr' or row['status'] not in ('timeout','failed','error'):continue
        log=a.run/f"{row['case']}_{row['variant']}_{row['repeat']}"/'process.log'
        if not log.exists():continue
        matches=re.findall(r'progress iteration=(\d+) committed=(\d+) pending=(\d+) elapsed=([\d.eE+-]+)'
                           r' gpu_search_seconds=([\d.eE+-]+) frontier_vertices=(\d+) h2d_bytes=(\d+)',log.read_text(errors='replace'))
        if not matches:continue
        iteration,committed,pending,elapsed,search,frontiers,upload=matches[-1]
        partial.append({'case':row['case'],'variant':row['variant'],'repeat':row['repeat'],'status':row['status'],
                        'iteration':int(iteration),'committed_in_iteration':int(committed),'pending_in_iteration':int(pending),
                        'last_logged_routing_seconds':float(elapsed),'last_logged_search_seconds':float(search),
                        'last_logged_frontier_vertices':int(frontiers),'last_logged_h2d_bytes':int(upload)})
    with (a.run/'partial_progress.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,list(partial[0]) if partial else ['case']);writer.writeheader();writer.writerows(partial)
    lines=['# VPR–GPU 规模实验结果','',f"状态：`{report['status']}`；CPU-only：`{report['cpu_only']}`。",
           '', '完整流程时间为固定端点下的路由至 FULL/STA；离线图转换、端点来源限制见实验协议。',
           '失败和未尝试项保留；仅完整合法解可参与质量/加速比计算。','',
           '| 电路 | 方法 | 成功/尝试 | 未尝试 | 路由进程 s | 完整流程 s | 路由主体 s | 搜索 s | CPD ns | 线长 |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    summaries=[]
    for case in report['cases']:
        for variant in ('vpr','unit','delay_proxy'):
            rows=[r for r in report['rows'] if r['case']==case['id'] and r['variant']==variant]
            attempted=[r for r in rows if not r['status'].startswith('not_attempted')]
            good=[r for r in attempted if r.get('success')]
            def median(key):
                values=[r[key] for r in good if r.get(key) is not None]
                return statistics.median(values) if values else None
            values={key:median(key) for key in ('process_seconds','workflow_seconds','routing_seconds','search_seconds','critical_path_ns','wirelength')}
            def fmt(value):return '—' if value is None else f'{value:.3f}'
            lines.append(f"| {case['id']} | {variant} | {len(good)}/{len(attempted)} | {len(rows)-len(attempted)} | "+' | '.join(fmt(v) for v in values.values())+' |')
            summaries.append({'case':case['id'],'category':case['category'],'variant':variant,
                              'attempts':len(attempted),'successes':len(good),
                              'unattempted':len(rows)-len(attempted),
                              'status_counts':dict(Counter(r['status'] for r in rows)),
                              'successful_route_fingerprints':sorted({r['route_fingerprint'] for r in good if r.get('route_fingerprint')}),
                              'workflow_range_seconds':([min(r['workflow_seconds'] for r in good),
                                                         max(r['workflow_seconds'] for r in good)] if good else None),
                              **values})
    lines += ['', '表中时间是成功重复的中位数；失败/超时的实际耗时见 CSV。不得把缺失时间当作零。','',
              '| 电路 | GPU 方法 | 有效配对 | 完整流程加速 | 路由主体加速 | CPD 变化 | 线长变化 | 三次均满足 5% / 10% / 20% |',
              '|---|---|---:|---:|---:|---:|---:|---|']
    qualified=[]
    for case in report['cases']:
        for variant in ('unit','delay_proxy'):
            pairs=[r for r in report.get('comparisons',[]) if r['case']==case['id'] and r['variant']==variant and r['eligible']]
            if not pairs:
                lines.append(f"| {case['id']} | {variant} | 0 | — | — | — | — | 无有效解 |");continue
            def mid(k):return statistics.median(r[k] for r in pairs)
            bands={str(b):len(pairs)>=3 and all(r['quality_bands'][str(b)] and r['workflow_speedup']>1 for r in pairs) for b in (5,10,20)}
            lines.append(f"| {case['id']} | {variant} | {len(pairs)} | {mid('workflow_speedup'):.3f}× | {mid('routing_speedup'):.3f}× | {mid('critical_path_change_percent'):+.2f}% | {mid('wirelength_change_percent'):+.2f}% | "+' / '.join('通过' if bands[str(b)] else '未通过' for b in (5,10,20))+' |')
            qualified.append({'case':case['id'],'category':case['category'],'variant':variant,'bands':bands})
    lines += ['', '上表最后一列同时要求至少三次完整合法配对、每次完整流程均加速，且 CPD/线长均在对应预算内。',
              '拥塞压力案例与 Koios 规模序列分别判断；单点加速不能证明随规模增长的交叉规律。','']
    if not any(any(r['bands'].values()) for r in qualified):
        lines += ['当前记录尚无满足上述重复次数和质量约束的稳定加速点。','']
    lines += ['| 失败或超时尝试 | 状态 | 已耗完整流程 s | 完成迭代 | 最后超用量 |',
              '|---|---|---:|---:|---:|']
    for row in report['rows']:
        if row['status'] not in ('failed','timeout','invalid_route','error'):continue
        last=row.get('last_iteration') or {}
        lines.append(f"| {row['case']} / {row['variant']} / {row['repeat']} | {row['status']} | "
                     +f"{row.get('workflow_seconds',0):.3f} | {row.get('iterations','—')} | {last.get('overflow','—')} |")
    lines += ['', '超时没有完整结果时，迭代和超用量保持缺失；日志中的中途进度不能作为完整路由质量。',
              '`partial_progress.csv` 保存失败/超时前最后一次已打印的进度；它不是结束时计数，不参与速度或质量比。',
              '路由进程限时 600 秒，审计、导出和 FULL/STA 另行计时，因此成功的完整流程可能超过 600 秒。',
              '',f"源码复核：`{report.get('source_unchanged','pending')}`；输入复核：`{report.get('inputs_unchanged','pending')}`。",'']
    (a.run/'report.md').write_text('\n'.join(lines))
    (a.run/'aggregate.json').write_text(json.dumps({'status':report['status'],'summaries':summaries,'qualified':qualified},indent=2)+'\n')
    # Standalone, exportable scientific figure; gaps mean no successful full route.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
        case_order=[c['id'] for c in report['cases'] if c['category']=='scale']
        for ax,key,label in zip(axes,('workflow_seconds','routing_seconds'),('Fixed-endpoint workflow (s)','Routing body (s)')):
            for variant in ('vpr','unit','delay_proxy'):
                values={r['case']:r[key] for r in summaries if r['variant']==variant}
                y=[values.get(c) if values.get(c) is not None else float('nan') for c in case_order]
                ax.plot(range(len(case_order)),y,marker='o',label=variant)
                if key=='workflow_seconds':
                    for x,c in enumerate(case_order):
                        failed=[r for r in report['rows'] if r['case']==c and r['variant']==variant and
                                r['status'] in ('timeout','failed','invalid_route') and r.get('workflow_seconds')]
                        if failed:
                            limit=max(r['workflow_seconds'] for r in failed)
                            ax.scatter([x],[limit],marker='x',color='black',zorder=5)
                            reason='timeout' if failed[0]['status']=='timeout' else 'invalid'
                            ax.annotate(f'{variant} {reason}', (x,limit),xytext=(3,5 if variant=='unit' else -12),
                                        textcoords='offset points',fontsize=7)
            ax.set_xticks(range(len(case_order)),case_order,rotation=15)
            ax.set_yscale('log');ax.set_ylabel(label);ax.grid(alpha=.25);ax.legend()
        fig.suptitle('Same-worker VPR / CUDA scaling; successful FULL-checked routes only')
        fig.savefig(a.run/'scaling.png',dpi=180);fig.savefig(a.run/'scaling.svg');plt.close(fig)
        fig,ax=plt.subplots(figsize=(8,5.2),layout='constrained')
        from matplotlib.patches import Rectangle
        for budget in (20,10,5):
            ax.add_patch(Rectangle((-5,-5),budget+5,budget+5,fill=False,linestyle='--',alpha=.5))
            ax.text(budget,budget,f' {budget}%',fontsize=8)
        colors={'unit':'tab:orange','delay_proxy':'tab:green'}
        for case in report['cases']:
            for variant in ('unit','delay_proxy'):
                pairs=[x for x in report.get('comparisons',[]) if x['case']==case['id'] and x['variant']==variant and x['eligible']]
                if not pairs:continue
                x=statistics.median(v['critical_path_change_percent'] for v in pairs)
                y=statistics.median(v['wirelength_change_percent'] for v in pairs)
                ax.scatter([x],[y],color=colors[variant],marker='o' if variant=='unit' else '^')
                ax.annotate(case['id']+' / '+variant,(x,y),xytext=(5,4),textcoords='offset points',fontsize=7)
        ax.set_xlabel('CPD change versus paired VPR (%)');ax.set_ylabel('Wirelength change versus paired VPR (%)')
        ax.set_title('Quality trade-offs; complete FULL-checked pairs only');ax.grid(alpha=.2)
        ax.margins(.2);fig.savefig(a.run/'quality.png',dpi=180);fig.savefig(a.run/'quality.svg');plt.close(fig)
    except ImportError:
        pass
    print(a.run/'report.md')


if __name__=='__main__':main()
