"""Summarize terminal large-input evidence, retaining qualification failures."""
from collections import defaultdict
import itertools
import json
import math
from pathlib import Path
import statistics

from prepare import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/native_cpu_large_20261102'


def read(path):
    return json.loads(path.read_text())


def stats(values):
    return dict(median=statistics.median(values), min=min(values), max=max(values), values=values) if values else None


def main():
    state = read(OUT/('continuation.json' if (OUT/'continuation.json').exists() else 'supervisor.json'))
    if state['status'] in ['running', 'waiting_original_preparation']:
        raise RuntimeError('Chain still running; do not publish a terminal report')
    preparation = read(OUT/('preparation_verified.json' if (OUT/'preparation_verified.json').exists() else 'preparation.json'))
    result = dict(status=state['status'], default_changed=False, preparation=preparation,
                  report_source={'path': str(Path(__file__).resolve()), 'sha256': sha256(__file__)},
                  completed_stages={}, env_errors=[], comparisons=[], aggregates=[], promotion_passed=False)
    for stage in ['qualification', 'formal']:
        path = OUT/stage/'serial/summary.json'
        if not path.exists():
            continue
        summary = read(path); plan = read(Path(summary['plan']))
        result['completed_stages'][stage] = dict(status=summary['status'], planned=plan['planned_samples'],
            attempted=len(summary['measurements']), legal=sum(bool(r['success']) for r in summary['measurements']))
        for row in summary['measurements']:
            if row['status'] == 'running':
                result['env_errors'].append(row['key'] + ': incomplete measurement')
                continue
            variant = plan['variants'][row['variant']]
            env = row.get('candidate_environment', {})
            checks = [bool(env.get('VPR_HYBRID_LOOKAHEAD_PARALLEL') == '1') == variant['parallel'],
                      all(env.get(k) == v for k, v in variant.get('env', {}).items()),
                      not any(k.startswith('VPR_CPU_') for k in env),
                      row['cpu_budget']['cpu_set'] == list(range(32,40)),
                      row['binary_sha256'] == plan['binaries'][variant['binary']]['sha256'],
                      row['command'][row['command'].index('--router_algorithm')+1] == 'parallel']
            if not all(checks): result['env_errors'].append(row['key'])
    gate_path = OUT/'qualification_gate.json'
    result['qualification_gate'] = read(gate_path) if gate_path.exists() else None
    lines = ['# 较大输入原生 CPU 扩展', '',
             '所有输入来自既有 Koios 套件；不是独立新基准。原版默认参数重新打包布局。共享宿主、单 lane；正式路由各臂八个物理核，串行仅指 lookahead 构建。', '',
             f'链终态：`{state["status"]}`。默认算法未改变。', '',
             '|准备输入|状态|准备秒|打包后放置块数|RR 节点|RR 边|', '|---|---|---:|---:|---:|---:|']
    for r in preparation['runs']:
        g = r.get('geometry', {})
        lines.append(f'|{r["case"]}|{r.get("inputs_ready",False)}|{r.get("process_seconds",0):.2f}|{g.get("placed_blocks","—")}|{g.get("rr_nodes","—")}|{g.get("rr_edges","—")}|')
    for stage, info in result['completed_stages'].items():
        lines += ['', f'{stage}：计划 {info["planned"]}，已尝试 {info["attempted"]}，合法 {info["legal"]}；状态 {info["status"]}。']
    if result['qualification_gate']:
        lines += ['', '资格门槛：'+result['qualification_gate']['status']+'；失败输入：'+str(result['qualification_gate']['failures'])+'。']
    formal = result['completed_stages'].get('formal')
    if formal and formal['status'] == 'completed':
        rows = read(OUT/'formal/serial/summary.json')['measurements']
        bykey = {(r['case'], r['cache_mode'], r['repeat'], r['variant']): r for r in rows}
        controls = [('fixed_serial','per_group'), ('per_group','pipeline'), ('fixed_serial','pipeline'), ('stock','pipeline')]
        lines += ['', '配对进程速度比 = 控制耗时 / 候选耗时。先各布局三次取中位数，再电路内两布局与电路间等权几何平均；原版对照另含状态修复。', '',
                  '|布局|缓存|比较|合格配对|进程速度比中位 [范围]|', '|---|---|---|---:|---:|']
        for case, cache, (control, candidate) in itertools.product(sorted({r['case'] for r in rows}), ['rebuild','reuse'], controls):
            pairs=[]
            for rep in range(3):
                x,y = bykey[case,cache,rep,control], bykey[case,cache,rep,candidate]
                q = (x['success'] and y['success'] and x.get('wire_map_matches_serial') and y.get('wire_map_matches_serial')
                     and all(y[k] <= 1.05*x[k]+1e-9 for k in ['critical_path_ns','wirelength']))
                pairs.append(dict(repeat=rep, quality_passed=bool(q),
                    process_ratio=x['process_seconds']/y['process_seconds'],
                    workflow_ratio=x['workflow_seconds']/y['workflow_seconds'],
                    control_cpd=x.get('critical_path_ns'), candidate_cpd=y.get('critical_path_ns'),
                    control_wirelength=x.get('wirelength'), candidate_wirelength=y.get('wirelength'),
                    same_route=x.get('route_body_sha256') == y.get('route_body_sha256')))
            valid = sum(p['quality_passed'] for p in pairs)
            entry = dict(case=case,cache=cache,control=control,candidate=candidate,pairs=pairs,valid_pairs=valid,
                         process_ratio=stats([p['process_ratio'] for p in pairs]) if valid == 3 else None,
                         workflow_ratio=stats([p['workflow_ratio'] for p in pairs]) if valid == 3 else None)
            result['comparisons'].append(entry)
            st=entry['process_ratio']
            value=f'{st["median"]:.6f} [{st["min"]:.6f}, {st["max"]:.6f}]' if st else '质量/合法性失败，不报汇总速度比'
            lines.append(f'|{case}|{cache}|{control}→{candidate}|{valid}/3|{value}|')
        for cache,(control,candidate) in itertools.product(['rebuild','reuse'],controls):
            entries = [e for e in result['comparisons'] if (e['cache'],e['control'],e['candidate'])==(cache,control,candidate)]
            grouped=defaultdict(list)
            for e in entries:
                grouped[e['case'].rsplit('_s',1)[0]].append(e)
            per_circuit = {k: math.exp(statistics.mean(math.log(e['process_ratio']['median']) for e in es))
                           if len(es)==2 and all(e['process_ratio'] for e in es) else None for k,es in grouped.items()}
            aggregate=math.exp(statistics.mean(math.log(v) for v in per_circuit.values())) if len(per_circuit)==3 and all(v is not None for v in per_circuit.values()) else None
            result['aggregates'].append(dict(cache=cache,control=control,candidate=candidate,circuits=per_circuit,geomean=aggregate))
        rebuild=next(e for e in result['aggregates'] if (e['cache'],e['control'],e['candidate'])==('rebuild','per_group','pipeline'))
        cache_entries=[e for e in result['comparisons'] if (e['cache'],e['control'],e['candidate'])==('reuse','per_group','pipeline')]
        result['promotion_passed'] = bool(not result['env_errors'] and result['qualification_gate']['status']=='passed'
            and all(r['success'] for r in rows) and rebuild['geomean'] is not None and rebuild['geomean']>=1.03
            and all(v is not None and v>=1 for v in rebuild['circuits'].values())
            and all(e['process_ratio'] and 1/e['process_ratio']['median']<=1.03 for e in cache_entries)
            and all(e['valid_pairs']==3 for e in result['comparisons'] if e['control']!='stock'))
        lines += ['', '预声明工程推广门槛：'+str(result['promotion_passed'])+'。这是工程选型门槛，不是统计显著性；即使通过也不自动更改默认。']
    else:
        lines += ['', '正式性能矩阵未完成，不报告新的加速比。']
    if state.get('error'): lines += ['', '停止原因：'+state['error']]
    if (OUT/'preparation_verified.json').exists():
        lines += ['', '准备后处理修正：原 XML 计数器假设 id 是 node 的首个属性，漏计节点；原始失败收据完整保留。修正器只按标签统计并重新核验既有输出，未重跑布局、修改 RR 图或更换输入。']
    lines += ['', '实际环境检查错误：'+str(result['env_errors'])+'。资格不通过时保留所有失败，不更换电路或调宽线宽来筛选正例。', '',
              '详见 protocol.json、preparation.json、qualification_gate.json、qualification_audit.json、formal_audit.json（存在的阶段）、analysis.json。']
    write_json(OUT/'analysis.json',result)
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':result['status'],'env_errors':result['env_errors'],'promotion_passed':result['promotion_passed']},ensure_ascii=False))


if __name__ == '__main__': main()
