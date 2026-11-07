"""Report repeated held-out pairs and cached same-binary control."""
import json,math,re,statistics
from pathlib import Path
from collections import defaultdict
from prepare import write_json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_cpu_repeat_20261102'
def dist(v):return dict(values=v,median=statistics.median(v),min=min(v),max=max(v)) if v else None
def main():
 audit=json.loads((OUT/'evidence_verification.json').read_text());assert audit['status']=='passed'
 rows=[]
 for stage in ['repeat','cached_toggle']:
  p=json.loads((OUT/(stage+'_plan.json')).read_text());s=json.loads((OUT/stage/'serial/summary.json').read_text());assert s['status']=='completed'
  expected=[(c['id'],q['repeat_start'],cache,v) for c in p['lanes']['serial']['cases'] for q in c['phases'] for cache in q['cache_modes'] for v in q['intended_execution_order']]
  assert [(r['case'],r['repeat'],r['cache_mode'],r['variant']) for r in s['measurements']]==expected
  for r in s['measurements']:
   assert r['workers']==8 and r['cpu_budget']['cpu_set']==list(range(32,40))
   env={} if r['variant']=='stock' else {'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'}
   if r['variant']=='pipeline':env['VPR_HYBRID_LOOKAHEAD_TASKS']='1'
   assert r['candidate_environment']==env and not r['diagnostic_sample']
   if r['cache_mode']=='reuse':assert r['log_evidence']['stage_seconds']['lookahead_build'] is None
   text=(Path(r['directory'])/'process.log').read_text(errors='replace');m=re.search(r'The entire flow of VPR took ([0-9.]+) seconds',text)
   r=dict(r,stage=stage,internal_flow_seconds=float(m[1]) if m else None);rows.append(r)
 assert len(rows)==120
 lookup={(r['stage'],r['case'],r['cache_mode'],r['repeat'],r['variant']):r for r in rows}
 comparisons=[]
 for stage,case,cache in sorted({(r['stage'],r['case'],r['cache_mode']) for r in rows}):
  variants=[('stock','frozen'),('stock','pipeline'),('frozen','pipeline')] if stage=='repeat' else [('same_cpu','pipeline')]
  for a,b in variants:
   pairs=[]
   for rep in range(3):
    x=lookup[stage,case,cache,rep,a];y=lookup[stage,case,cache,rep,b]
    valid=x['success'] and y['success'] and y['critical_path_ns']<=x['critical_path_ns']*1.05 and y['wirelength']<=x['wirelength']*1.05
    z=dict(repeat=rep,quality_passed=valid,control_key=x['key'],candidate_key=y['key'])
    if valid:z.update(process_ratio=x['native_process_seconds']/y['native_process_seconds'],internal_flow_ratio=x['internal_flow_seconds']/y['internal_flow_seconds'],same_route=x['route_body_sha256']==y['route_body_sha256'])
    pairs.append(z)
   good=[q for q in pairs if q['quality_passed']]
   comparisons.append(dict(stage=stage,case=case,cache=cache,control=a,candidate=b,pairs=pairs,valid_pairs=len(good),process_ratio=dist([q['process_ratio'] for q in good]),internal_flow_ratio=dist([q['internal_flow_ratio'] for q in good])))
 aggregate=[]
 for cache in ['rebuild','reuse']:
  for a,b in [('stock','frozen'),('stock','pipeline'),('frozen','pipeline')]:
   pp=[p for p in comparisons if p['stage']=='repeat' and p['cache']==cache and p['control']==a and p['candidate']==b]
   ok=len(pp)==6 and all(p['valid_pairs']==3 for p in pp)
   aggregate.append(dict(cache=cache,control=a,candidate=b,geomean=math.exp(sum(math.log(p['process_ratio']['median']) for p in pp)/6) if ok else None,internal_geomean=math.exp(sum(math.log(p['internal_flow_ratio']['median']) for p in pp)/6) if ok else None))
 configs=[]
 for k in sorted({(r['stage'],r['case'],r['cache_mode'],r['variant']) for r in rows}):
  rr=[r for r in rows if (r['stage'],r['case'],r['cache_mode'],r['variant'])==k]
  configs.append(dict(stage=k[0],case=k[1],cache=k[2],variant=k[3],process=dist([r['native_process_seconds'] for r in rr]),routing=dist([r['routing_seconds'] for r in rr if r['routing_seconds'] is not None]),iterations=[r['iterations'] for r in rr],heap_pushes=[r['heap_pushes'] for r in rr],route_hashes=[r.get('route_body_sha256') for r in rr],cpu_user=dist([r['cpu_budget_audit']['cpu_user_seconds'] for r in rr])))
 data=dict(status='complete',samples=len(rows),legal=sum(r['success'] for r in rows),comparisons=comparisons,aggregates=aggregate,configurations=configs,default_changed=False)
 write_json(OUT/'analysis.json',data);write_json(OUT/'acceptance.json',dict(status='complete',samples=len(rows),legal=data['legal'],evidence_audit='passed',actual_order_env_cpu_audit='passed',default_changed=False))
 lines=['# 新电路重复与缓存退化复查','',f"完成{len(rows)}项新测量，合法{data['legal']}项；原生及独立FULL/STA与map字节等价审计通过。旧单次数据不并入本轮。",'',
 '相同八个物理核32–39、单lane共享宿主；六个既有布局各三次运行重复。另对s38417两布局使用同一pipeline ELF、共享缓存，仅切换TASKS开关，各三次。未改二进制、默认或测量计时。资格准备关闭拥塞报告，正式测量保持开启。', '',
 '|缓存|控制→候选|六布局配对中位数等权几何平均|VPR内部flow敏感性指标|','|---|---|---:|---:|']
 for x in aggregate:lines.append(f"|{x['cache']}|{x['control']}→{x['candidate']}|{x['geomean']}|{x['internal_geomean']}|")
 lines+=['','每个电路两布局，故六布局等权等价于先电路内、再三电路等权。内部flow来自原日志，计时边界不同，仅作秒级进程退出轮询影响的敏感性对照，不能替代完整进程指标。三次样本范围不是置信区间。','', '|阶段|布局|缓存|控制→候选|进程速度比中位[范围]|合法质量配对|','|---|---|---|---|---:|---:|']
 for x in comparisons:
  d=x['process_ratio'];v=f"{d['median']:.4f} [{d['min']:.4f}, {d['max']:.4f}]" if d else '无'
  lines.append(f"|{x['stage']}|{x['case']}|{x['cache']}|{x['control']}→{x['candidate']}|{v}|{x['valid_pairs']}/3|")
 lines+=['','## s38417缓存工作量','', '|阶段|布局|实现|进程中位秒|路由中位秒|迭代轮数|heap pushes|','|---|---|---|---:|---:|---|---|']
 for x in configs:
  if x['case'].startswith('s38417') and x['cache']=='reuse':lines.append(f"|{x['stage']}|{x['case']}|{x['variant']}|{x['process']['median']:.3f}|{x['routing']['median']:.3f}|{x['iterations']}|{x['heap_pushes']}|")
 lines+=['','map等价不意味着原版和修复版路由轨迹一致。同ELF缓存开关对照用于判断TASKS开关是否引入稳定退化；不能据此单独分离两处状态修复各自的作用。共享宿主波动仍存在。全部配对、路由哈希和CPU工作时间见analysis.json；未改变默认。']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'samples':len(rows),'legal':data['legal'],'aggregates':aggregate}))
if __name__=='__main__':main()
