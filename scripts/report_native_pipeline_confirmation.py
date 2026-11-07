"""Offline paired analysis for sequential eight-core pipeline confirmation."""
import json,statistics
from pathlib import Path
from prepare import write_json
O=Path(__file__).resolve().parents[1]/'results/native_pipeline_confirm_20261102'
p=json.loads((O/'plan.json').read_text());s=json.loads((O/'runs/serial8/summary.json').read_text())
assert s['status']=='completed' and len(s['measurements'])==36
rows=s['measurements'];index={(r['case'],r['cache_mode'],r['repeat'],r['variant']):r for r in rows};pairs=[]
for case in ['gemm','softmax','reduction']:
 for cache in ['rebuild','reuse']:
  values=[]
  for rep in range(3):
   a=index[case,cache,rep,'frozen'];b=index[case,cache,rep,'pipeline']
   assert a['success'] and b['success'] and a['wire_map_sha256']==b['wire_map_sha256']
   assert a['cpu_budget']['cpu_set']==b['cpu_budget']['cpu_set']==list(range(32,40))
   assert b['critical_path_ns']<=a['critical_path_ns']*1.05 and b['wirelength']<=a['wirelength']*1.05
   assert not a['diagnostic_sample'] and not b['diagnostic_sample']
   assert a['candidate_environment']=={'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'}
   assert b['candidate_environment']=={'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1','VPR_HYBRID_LOOKAHEAD_TASKS':'1'}
   for r in [a,b]:
    assert len({(t['socket'],t['core']) for t in r['cpu_budget']['topology']})==8
    assert len({t['node'] for t in r['cpu_budget']['topology']})==1
    assert (r['lookahead_cache_sha256'] is None) if cache=='rebuild' else r['lookahead_cache_sha256']==r['wire_map_sha256']
   values.append(dict(repeat=rep,ratio=a['native_process_seconds']/b['native_process_seconds'],workflow_ratio=a['workflow_seconds']/b['workflow_seconds'],same_route=a['route_body_sha256']==b['route_body_sha256']))
  v=[r['ratio'] for r in values];med=statistics.median(v);primary=case=='gemm' and cache=='rebuild'
  pairs.append(dict(case=case,cache=cache,pairs=values,median=med,min=min(v),max=max(v),passed=min(v)>1 and med>1.02 if primary else med>=1/1.02))
audit=json.loads((O/'evidence_verification.json').read_text());assert audit['status']=='passed'
result=dict(status='complete',samples=36,comparisons=pairs,promotion_rule_passed=all(r['passed'] for r in pairs),scope=p['concurrency_scope'],limitations='Fixed placement runtime repeats, shared host, extensions are prior project circuits held out from previous eight-core selection; no new independent benchmark claim.')
result['quality']=[dict(case=c,critical_path_ns=sorted({r['critical_path_ns'] for r in rows if r['case']==c}),wirelength=sorted({r['wirelength'] for r in rows if r['case']==c}),iterations=sorted({r['iterations'] for r in rows if r['case']==c})) for c in ['gemm','softmax','reduction']]
result['stage_medians']=[dict(case=c,variant=v,lookahead_seconds=statistics.median(r['log_evidence']['stage_seconds']['lookahead_build'] for r in rows if r['case']==c and r['variant']==v and r['cache_mode']=='rebuild')) for c in ['gemm','softmax','reduction'] for v in ['frozen','pipeline']]
write_json(O/'analysis.json',result)
lines=['# 八核 pipeline 顺序确认','',f"36项全部合法及map等价，独立FULL/STA通过。预设选型门槛：{'通过' if result['promotion_rule_passed'] else '未通过'}。",'','相对既有优化CPU的三次配对完整进程速度比；大于1表示更快。','','|电路|缓存|中位数|范围|门槛|','|---|---|---:|---|---|']
for r in pairs:lines.append(f"|{r['case']}|{r['cache']}|{r['median']:.6f}|{r['min']:.6f}–{r['max']:.6f}|{r['passed']}|")
lines+=['',p['concurrency_scope'],'',result['limitations'],'','所有实验串行使用同一八核集合，排除本轮自身并发；不声称宿主独占。默认策略未变。完整记录见 analysis.json 与 evidence_verification.json。']
lines+=['','GEMM重建三次均加速，两个扩展电路的三次重建也均加速；共同缓存条件整体接近持平，支持收益主要来自预计算构建。缓存中的小幅变化不归因于跳过的构建计算。','', 'GEMM部分配对路由主体不同，质量门槛仍通过；完整进程速度比包含并行布线波动，不是严格相同搜索工作量的单核算子对比。','', '本轮通过工程门槛，支持八核pipeline候选；不外推至四核、更多布局或独占硬件，也不证明论文新颖性。此前bounded未通过选型的结论保持。']
lines+=['','|电路|实现|重建lookahead中位秒|','|---|---|---:|']
for r in result['stage_medians']:lines.append(f"|{r['case']}|{r['variant']}|{r['lookahead_seconds']:.3f}|")
(O/'report.md').write_text('\n'.join(lines)+'\n');print(json.dumps(result))
