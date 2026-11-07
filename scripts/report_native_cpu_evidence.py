"""Audit attribution and report all predeclared native CPU evidence stages."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
from prepare import sha256, write_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_evidence_20261102'


def read(path):return json.loads(path.read_text())


def distribution(values):
    return dict(values=values,median=statistics.median(values),min=min(values),max=max(values)) if values else None


def placement(path):
    entries=[]
    for line in path.read_text().splitlines():
        fields=line.split()
        if len(fields)>=5 and all(v.lstrip('-').isdigit() for v in fields[1:5]):
            entries.append([fields[0],*map(int,fields[1:5])])
    assert entries,'No placement coordinates: '+str(path)
    return dict(coordinates_sha256=hashlib.sha256(json.dumps(sorted(entries)).encode()).hexdigest(),
                blocks=len(entries),layer_counts=dict(Counter(e[4] for e in entries)))


def main():
    evidence=read(OUT/'evidence_verification.json');assert evidence['status']=='passed'
    join=read(OUT/'generalization_join.json')
    assert join['status']=='passed' and join['retained']==24 and join['continued']==12
    for b in join['sources']+[join['output'],join['plan']]:
        assert sha256(Path(b['path']))==b['sha256'],b['path']
    rows=[];stages=[]
    for stage in ['triad','generalization','scaling']:
        name='generalization_complete' if stage=='generalization' else stage
        plan=read(OUT/(name+'_plan.json'));summary=read(Path(plan['output'])/'serial/summary.json')
        assert summary['status']=='completed'
        expected=[]
        for case in plan['lanes']['serial']['cases']:
            for phase in case['phases']:
                for n in phase['workers']:
                    for cache in phase['cache_modes']:
                        for v in phase['intended_execution_order']:
                            expected.append((case['id'],n,cache,phase['repeat_start'],v))
        actual=[(r['case'],r['workers'],r['cache_mode'],r['repeat'],r['variant']) for r in summary['measurements']]
        assert actual==expected and len(actual)==plan['planned_samples'],'Incomplete/reordered '+stage
        for row in summary['measurements']:
            expected_env={} if row['variant']=='stock' else {'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'}
            if row['variant']=='pipeline':expected_env['VPR_HYBRID_LOOKAHEAD_TASKS']='1'
            assert row['candidate_environment']==expected_env and not row['diagnostic_sample'],row['key']
            cpus=set(row['cpu_budget']['cpu_set']);topo=[t for t in row['cpu_budget']['topology'] if t['cpu'] in cpus]
            assert cpus==set(range(32,32+row['workers']))
            assert len({(t['socket'],t['core']) for t in topo})==row['workers'] and len({t['node'] for t in topo})==1
            if row['cache_mode']=='rebuild':
                assert row['lookahead_cache_sha256'] is None
            else:
                assert row['lookahead_cache_sha256']
                if row.get('wire_map_sha256'):
                    assert row['lookahead_cache_sha256']==row['wire_map_sha256']
            rows.append(dict(row,stage=stage))
        stages.append(dict(stage=stage,planned=plan['planned_samples'],completed=len(actual),successful=sum(r['success'] for r in summary['measurements'])))
    maps=defaultdict(set)
    for row in rows:
        if row.get('wire_map_sha256'):maps[row['case']].add(row['wire_map_sha256'])
    assert all(len(h)==1 for h in maps.values())
    look={(r['stage'],r['case'],r['workers'],r['cache_mode'],r['repeat'],r['variant']):r for r in rows}
    configs=sorted({(r['stage'],r['case'],r['workers'],r['cache_mode']) for r in rows})
    comparisons=[]
    for stage,case,n,cache in configs:
        for control,candidate in ([('frozen','pipeline')] if stage=='scaling' else [('stock','frozen'),('stock','pipeline'),('frozen','pipeline')]):
            pairs=[];invalid=[]
            for rep in ([0] if stage=='generalization' else range(3)):
                a=look[stage,case,n,cache,rep,control];b=look[stage,case,n,cache,rep,candidate]
                quality=bool(a['success'] and b['success'] and b['critical_path_ns']<=a['critical_path_ns']*1.05 and b['wirelength']<=a['wirelength']*1.05)
                item=dict(repeat=rep,control_key=a['key'],candidate_key=b['key'],quality_passed=quality,
                          control_success=a['success'],candidate_success=b['success'])
                if a['success'] and b['success']:
                    item.update(critical_path_regression_percent=100*(b['critical_path_ns']/a['critical_path_ns']-1),
                                wirelength_regression_percent=100*(b['wirelength']/a['wirelength']-1))
                if quality:
                    item.update(process_ratio=a['native_process_seconds']/b['native_process_seconds'],
                        workflow_ratio=a['workflow_seconds']/b['workflow_seconds'],same_route=a['route_body_sha256']==b['route_body_sha256'],
                        control_seconds=a['native_process_seconds'],candidate_seconds=b['native_process_seconds'])
                    pairs.append(item)
                else:invalid.append(item)
            comparisons.append(dict(stage=stage,case=case,workers=n,cache=cache,control=control,candidate=candidate,
                valid_pairs=len(pairs),pairs=pairs,invalid=invalid,process_ratio=distribution([p['process_ratio'] for p in pairs]),
                workflow_ratio=distribution([p['workflow_ratio'] for p in pairs])))
    layouts=[]
    for c in read(OUT/'protocol.json')['selected_circuits']:
        values=[]
        for seed in [1,2]:
            case=read(OUT/'prepared'/f"{c['id']}_s{seed}"/'vpr_case.json')
            item=dict(circuit=c['id'],seed=seed,**placement(Path(case['inputs']['placement']['path'])))
            layouts.append(item);values.append(item['coordinates_sha256'])
        assert len(set(values))==2,'Seeds did not produce distinct coordinates: '+c['id']
    summaries=[]
    for key in sorted({(r['stage'],r['case'],r['workers'],r['cache_mode'],r['variant']) for r in rows}):
        selected=[r for r in rows if (r['stage'],r['case'],r['workers'],r['cache_mode'],r['variant'])==key]
        legal=[r for r in selected if r['success']]
        phase=defaultdict(list)
        for r in legal:
            for name,value in r['log_evidence']['stage_seconds'].items():
                if value is not None:phase[name].append(value)
        summaries.append(dict(stage=key[0],case=key[1],workers=key[2],cache=key[3],variant=key[4],
            legal_samples=len(legal),attempted_samples=len(selected),
            process_seconds=distribution([r['native_process_seconds'] for r in legal]),
            workflow_seconds=distribution([r['workflow_seconds'] for r in legal]),
            peak_hwm_kib=distribution([r['cpu_budget_audit']['peak_observed_hwm_kib'] for r in selected]),
            stage_median_seconds={k:statistics.median(v) for k,v in phase.items()},
            quality=[dict(critical_path_ns=r.get('critical_path_ns'),wirelength=r.get('wirelength'),iterations=r.get('iterations'),success=r['success']) for r in selected]))
    triad=next(p for p in comparisons if (p['stage'],p['cache'],p['control'],p['candidate'])==('triad','rebuild','stock','pipeline'))
    triad_pass=triad['valid_pairs']==3 and triad['process_ratio']['min']>1 and triad['process_ratio']['median']>1.05
    heldout=[]
    for cache in ['rebuild','reuse']:
        for control,candidate in [('stock','frozen'),('stock','pipeline'),('frozen','pipeline')]:
            circuit_values=[]
            for circuit in ['alu4','diffeq','s38417']:
                pp=[p for p in comparisons if p['stage']=='generalization' and p['case'].startswith(circuit+'_s')
                    and p['cache']==cache and p['control']==control and p['candidate']==candidate]
                eligible=len(pp)==2 and all(p['valid_pairs']==1 for p in pp)
                value=math.exp(sum(math.log(p['process_ratio']['median']) for p in pp)/2) if eligible else None
                circuit_values.append(dict(circuit=circuit,placements=2,quality_eligible=eligible,geomean=value))
            overall=math.exp(sum(math.log(c['geomean']) for c in circuit_values)/3) if all(c['quality_eligible'] for c in circuit_values) else None
            heldout.append(dict(cache=cache,control=control,candidate=candidate,circuits=circuit_values,
                geomean=overall,scope='Equal-weight geometric mean of two placements within each circuit, then of three circuits; withheld if any required pair fails quality. No confidence interval.'))
    data=dict(status='complete',stages=stages,comparisons=comparisons,configuration_summaries=summaries,
              fresh_placements=layouts,triad_primary_passed=triad_pass,heldout_aggregates=heldout,
              retained_setup_failures=join['failed_qualifications'],generalization_join_audit='passed',
              failures=[dict(stage=r['stage'],key=r['key'],returncode=r['returncode']) for r in rows if not r['success']],
              scope='Same-core comparisons; shared host. Generalization uses two placements per circuit, one runtime measurement per arm/cache/placement. Core counts were measured sequentially, not simultaneous strong-scaling isolation.',
              default_changed=False)
    write_json(OUT/'analysis.json',data)
    write_json(OUT/'acceptance.json',dict(status='complete',completed_utc=datetime.now(timezone.utc).isoformat(),
        planned_samples=66,actual_samples=len(rows),legal_samples=sum(r['success'] for r in rows),
        evidence_audit=evidence['status'],actual_env_order_cpu_audit='passed',fresh_layouts=6,distinct_coordinates_per_circuit=True,
        retained_setup_failures=len(join['failed_qualifications']),generalization_join_audit='passed',
        triad_primary_passed=triad_pass,default_changed=False))
    lines=['# CPU 三方基线、泛化与核数扩展','',
        f"完成 {len(rows)}/66 个正式样本，合法 {sum(r['success'] for r in rows)} 项；三方主门槛{'通过' if triad_pass else '未通过'}。",'',
        'stock为锁定原版VPR的原生并行路由，frozen为已有组内采样CPU，pipeline为已有跨组调度。每一比较CPU预算相同。速度比=控制时间/候选时间；运行时间中位数之比不等于配对速度比中位数。', '',
        '## GEMM 同八核三方对照','', '|缓存|控制→候选|配对进程速度比中位 [范围]|合法质量配对|','|---|---|---:|---:|']
    def ratio(p):
        d=p['process_ratio'];return f"{d['median']:.4f} [{d['min']:.4f}, {d['max']:.4f}]" if d else '无合格配对'
    for p in comparisons:
        if p['stage']=='triad':lines.append(f"|{p['cache']}|{p['control']}→{p['candidate']}|{ratio(p)}|{p['valid_pairs']}/3|")
    lines+=['','各阶段墙钟与完整进程中位数（秒）：','',
            '|缓存|实现|RR图载入|lookahead构建|布线|完整进程|含独立复核的workflow|',
            '|---|---|---:|---:|---:|---:|---:|']
    def number(value):return f'{value:.2f}' if value is not None else '—'
    for cache in ['rebuild','reuse']:
        for variant in ['stock','frozen','pipeline']:
            s=next(s for s in summaries if (s['stage'],s['cache'],s['variant'])==('triad',cache,variant))
            phase=s['stage_median_seconds']
            values=[phase.get(k) for k in ['rr_graph_load','lookahead_build','routing']]
            values += [s[k]['median'] if s[k] else None for k in ['process_seconds','workflow_seconds']]
            lines.append('|'+ '|'.join([cache,variant,*map(number,values)])+'|')
    lines+=['','阶段计时仅覆盖日志已有的阶段；不能相加冒充完整进程。完整进程包含原生FULL/STA与map写出，workflow另外包含独立原版FULL/STA复核；均不含本轮新电路的pack/place准备。缓存场景跳过lookahead构建。只在合法样本内计算本表中位数；失败保留在完整数据中。']
    lines+=['','## 新电路与新布局','', 'alu4、diffeq、s38417按输入逻辑规模与时序结构预选，种子1/2均重新打包布局，实际坐标已核验不同。每个布局每个变体/缓存只有一次运行，不把它们包装为三次运行重复，也不把两个布局计成两种电路。', '',
            '|电路布局|缓存|控制→候选|进程速度比|质量合格|','|---|---|---|---:|---|']
    for p in comparisons:
        if p['stage']=='generalization':lines.append(f"|{p['case']}|{p['cache']}|{p['control']}→{p['candidate']}|{ratio(p)}|{p['valid_pairs']==1}|")
    lines+=['','按每个电路内两布局、再三个电路等权几何平均；有任一质量不合格配对时不报告完整集合平均。','',
            '|缓存|控制→候选|三电路等权几何平均|','|---|---|---:|']
    for h in heldout:
        value=f"{h['geomean']:.4f}" if h['geomean'] is not None else '质量集合不完整'
        lines.append(f"|{h['cache']}|{h['control']}→{h['candidate']}|{value}|")
    lines+=['','各布局完整进程的绝对时间（秒；每项一次）：','',
            '|电路布局|缓存|stock|frozen|pipeline|','|---|---|---:|---:|---:|']
    for case in sorted({r['case'] for r in rows if r['stage']=='generalization'}):
        for cache in ['rebuild','reuse']:
            values=[look['generalization',case,8,cache,0,v] for v in ['stock','frozen','pipeline']]
            lines.append('|'+ '|'.join([case,cache,*[number(r['native_process_seconds'])+('（失败）' if not r['success'] else '') for r in values]])+'|')
    lines+=['','小电路只有秒级运行时间。冻结执行器使用Python的带超时wait，当前POSIX实现的退出轮询sleep最大为50毫秒，实测进程时间包含退出检测等待及监督开销；共享调度还可增加波动。这不是严格误差上界。未事后扣除这些开销，也未改用另一个指标挑选结果；单次的小幅百分比差异不能视为稳定加速。']
    lines+=['','## 核数与资源','', '|物理核|pipeline相对frozen重建速度比|配对数|','|---:|---:|---:|']
    for n in [4,8,16]:
        p=next(p for p in comparisons if p['workers']==n and p['case']=='gemm' and p['cache']=='rebuild' and p['control']=='frozen' and p['candidate']=='pipeline')
        lines.append(f"|{n}|{ratio(p)}|{p['valid_pairs']}/3|")
    lines+=['','绝对时间中位数（秒）：','',
            '|物理核|frozen构建|pipeline构建|frozen进程|pipeline进程|',
            '|---:|---:|---:|---:|---:|']
    for n in [4,8,16]:
        ss=[next(s for s in summaries if s['case']=='gemm' and s['workers']==n and s['cache']=='rebuild' and s['variant']==v) for v in ['frozen','pipeline']]
        values=[s['stage_median_seconds'].get('lookahead_build') for s in ss]+[s['process_seconds']['median'] if s['process_seconds'] else None for s in ss]
        lines.append('|'+ '|'.join([str(n),*map(number,values)])+'|')
    lines+=['', '八核来自本轮三方阶段，四/十六核来自后续扩展；每个核数内配对公平，跨核数时间仍可能受时段变化影响。RSS为每五秒观察的进程HWM，可能被RR XML载入支配，不代表临时map内存；各项原值见analysis.json。', '',
        '## 贡献与限制','',
        '当前主线是原生lookahead预计算的采样并行与跨组调度，保留map字节等价和原生路由/STA接口。已有文献中的采样map、确定性并行与pipeline原语不作首次贡献。新bounded仍为上一轮未建立稳定增量的候选。', '',
        'stock与两种改进CPU之间还包含此前的并行状态修复，原生路由轨迹可能不同；不能将完整进程差值全部归于单个lookahead调度算子，也不将路由质量变化归因于map优化。frozen与pipeline对照和共同缓存用于补充归因。', '',
        '本轮未启用GPU，未改变默认调度。节点无独占调度入口；所有本轮准备和求解顺序执行，但宿主、存储和内存共享。只有三种新电路、每种两个布局，不能外推为全面超过SOTA或论文新颖性已成立。存在失败或质量超门槛的配对时保留记录并排除其速度比。', '',
        '泛化初始执行在24项正式测量后，s38417_s1的单轮缓存资格准备触发overuse_report.cpp:366断言，map已成功写出。原失败目录和回执保留。复核后，仅剩余两布局的缓存准备关闭拥塞报告输出，正式测量的该参数仍为on，二进制、调度和输入不变；保留24项，补完未执行的12项，没有重跑正式样本。原失败map与重做资格的原版/优化map字节相同。generalization_complete为可追溯的合并证据视图，原generalization状态仍为failed。', '',
        '完整证据：analysis.json、acceptance.json、evidence_verification.json、generalization_join.json、protocol.json、原始及补充*_plan.json、preparation.json与measurement_resolution.json。前序查新见../../docs/native_lookahead_novelty_analysis.md。']
    reuse_pairs=[(p,q) for p in comparisons if p['stage']=='generalization' and p['cache']=='reuse' and p['control']=='stock' and p['candidate']=='pipeline' for q in p['pairs']]
    if reuse_pairs:
        p,q=min(reuse_pairs,key=lambda item:item[1]['process_ratio'])
        lines+=['',f"缓存场景最差的原版→pipeline泛化配对为{p['case']}：速度比{q['process_ratio']:.4f}，候选时间变化{100*(1/q['process_ratio']-1):+.2f}%。该单项不能被集合平均掩盖；本轮没有据此启用普遍默认策略。"]
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(status='complete',samples=len(rows),triad_pass=triad_pass,failures=data['failures'])))


if __name__=='__main__':main()
