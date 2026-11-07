"""Classify all qualification failures without treating missing endpoints as equal."""
from collections import Counter
import json
from pathlib import Path

from prepare import sha256, write_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_large_20261102'


def main():
    source=OUT/'qualification/serial/summary.json'
    summary=json.loads(source.read_text());assert summary['status']=='completed'
    counts=Counter();rows=[];bindings={str(source):sha256(source)}
    for row in summary['measurements']:
        p=Path(row['directory'])/'process.log';text=p.read_text(errors='replace');bindings[str(p)]=sha256(p)
        rc=row['returncode']
        if row['success']:reason='legal_independently_checked'
        elif row['status']=='timeout':reason='timeout'
        elif rc==-11:reason='SIGSEGV'
        elif rc==-6 and 'std::bad_alloc' in text:reason='SIGABRT_bad_alloc'
        elif rc==2:reason='routing_not_converged'
        else:reason='other_failure'
        counts[reason]+=1
        e=row['log_evidence'];iters=e.get('iterations',[])
        rows.append(dict(key=row['key'],case=row['case'],variant=row['variant'],classification=reason,
                         process_seconds=row['process_seconds'],returncode=rc,map_equivalent=row.get('wire_map_matches_serial',False),
                         stage_seconds=e['stage_seconds'],last_completed_iteration=iters[-1] if iters else None,
                         cpd=row.get('critical_path_ns'),wirelength=row.get('wirelength'),route_iterations=row.get('iterations'),
                         route_body_sha256=row.get('route_body_sha256'),route_identity_observable=bool(row['success'] and row.get('route_body_sha256'))))
    groups={}
    for case in sorted({r['case'] for r in rows}):
        arms={r['variant']:r for r in rows if r['case']==case};a,b=arms['reference'],arms['per_group']
        valid=a['route_identity_observable'] and b['route_identity_observable']
        groups[case]=dict(old_endpoint_observable=valid,
            old_endpoint_identical=all(a[k]==b[k] for k in ['route_body_sha256','cpd','wirelength','route_iterations']) if valid else None,
            explanation='Unavailable endpoint is unknown, not equal; None == None in the original gate display did not satisfy its separate legality gate.')
    overuse=OUT/'qualification/serial/bnn_s1_qualification_w8_r0_fixed_serial_rebuild/report_overused_nodes.rpt'
    bindings[str(overuse)]=sha256(overuse)
    code=ROOT/'vendor/vtr_cpu_paper/vpr/src/route/route.cpp';bindings[str(code)]=sha256(code)
    result=dict(status='review_complete',counts=dict(counts),rows=rows,endpoint_review=groups,
                original_gate_result_unchanged='failed',formal_started=False,default_changed=False,
                sources=bindings,review_source={'path':str(Path(__file__).resolve()),'sha256':sha256(__file__)},
                bnn_s1_remaining_conflict=dict(node=3329379,type='CHANY',layer=0,capacity=1,occupancy=2,nets=[1270,1278],
                    interpretation='Observed local in-layer routing conflict; not proof the graph is intrinsically unroutable or that vertical capacity is the bottleneck.'),
                crash_limitations='Two stock SIGSEGVs lack an established stack cause. Stock LSTM s2 throws std::bad_alloc; unchanged containing-cgroup OOM counters do not establish why allocation failed. Do not call these GPU failures or candidate QoR failures.')
    write_json(OUT/'review_20261103.json',result)
    lines=['# 大图资格结果复核（2026-11-03）','',
           '六个新布局均准备成功；30项资格全部执行，30份map字节等价，原证据审计90文件通过。正式144项没有启动。资格失败保持，未修改默认算法。','',
           '|类别|数量|已知结论|','|---|---:|---|',
           f'|900秒超时|{counts["timeout"]}|DLA/LSTM尚有持续拥塞；不是一次正常结束的慢速样本|',
           f'|原版SIGSEGV|{counts["SIGSEGV"]}|DLA两布局，具体崩溃原因未定位|',
           f'|原版SIGABRT / bad_alloc|{counts["SIGABRT_bad_alloc"]}|LSTM种子2，不能仅据此宣称系统物理内存耗尽|',
           f'|200轮未收敛|{counts["routing_not_converged"]}|BNN种子1的五臂；修复版末轮仍有一个过用节点|',
           f'|合法且独立FULL/STA通过|{counts["legal_independently_checked"]}|BNN种子2的五臂；质量均合格，严格端点门槛失败|','',
           '**预计算与路由收敛需要分开评价。** 以下为各资格样本中的lookahead构建秒数，单次观察，仅证明这些运行中预计算阶段缩短；不能把未完成路由计算为端到端加速，也不代替正式重复。','',
           '|布局|同ELF串行构建|同ELF组内并行|同ELF pipeline|','|---|---:|---:|---:|']
    for case in groups:
        arms={r['variant']:r for r in rows if r['case']==case}
        lines.append('|'+case+'|'+'|'.join(f'{arms[v]["stage_seconds"]["lookahead_build"]:.2f}' for v in ['fixed_serial','per_group','pipeline'])+'|')
    lines+=['',
            'DLA_s1串行构建臂在第50轮每轮约4.8秒，末尾第65轮约58.7秒，仍有2112个过用节点；LSTM_s1末尾第73轮约87.7秒，仍有95个过用节点。route.cpp在0.25×200=50轮后切换冲突模式，并周期性扩大搜索边界；日志中高扇出重布线及每轮工作量增长与此一致。现有证据支持收敛停滞伴随搜索范围扩张，尚未隔离所有运行时间成本。单纯延长超时未必能解决。','',
            'BNN_s1的修复版末轮冲突为层0 CHANY节点3329379，容量1、占用2，涉及来自同一DSP块的网络1270/1278。这不是已证实的垂直互连瓶颈，也没有证明图本身不可布通。','',
            'BNN_s2的reference、fixed_serial与pipeline均121轮、CPD11.4776ns、线长1668046；per_group为75轮、相同CPD、线长1668374（仅+0.0197%）。五臂都合法，失败的是旧冻结端点与新组内臂的严格一致性，不是5%质量门槛。不能把此次单样本的75轮视为稳定算法收益。','',
            '原qualification_gate.json对缺失route hash使用None==None，部分失败输入显示same_route/old_endpoint_identical=true。新review明确记为不可观察；原文件保留，整体拒绝结果不变，因为合法性门槛已失败。','',
            '已冻结后续八项缓存诊断：BNN_s1同图同缓存串行/并行各一次；BNN_s2同ELF、同缓存、TASKS=0/1各三次，交错执行。用于检查图上可行性与运行间轨迹变化，不报告速度比，不替换本轮负例，不启动144项正式矩阵。','',
            '后续判定：串行若合法，仅证明存在可行路由；同一缓存模式若反复得到不同路由，说明最终轨迹不具重复性，仍不等于已证明竞态。只有诊断完成后才决定新的资格协议，不能追溯放宽旧门槛。']
    (OUT/'review_20261103.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result['counts']))


if __name__=='__main__':main()
