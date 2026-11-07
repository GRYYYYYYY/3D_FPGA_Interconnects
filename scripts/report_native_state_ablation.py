"""Verify semantic endpoints before interpreting the repair factorial."""
import json,re,statistics
from pathlib import Path
from prepare import write_json,sha256
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_state_ablation_20261102'
def main():
 audit=json.loads((OUT/'evidence_verification.json').read_text());assert audit['status']=='passed'
 p=json.loads((OUT/'plan.json').read_text());s=json.loads((OUT/'runs/serial/summary.json').read_text());assert s['status']=='completed'
 rows=s['measurements'];assert len(rows)==36
 expected=[(c['id'],q['repeat_start'],v) for c in p['lanes']['serial']['cases'] for q in c['phases'] for v in q['intended_execution_order']]
 assert [(r['case'],r['repeat'],r['variant']) for r in rows]==expected
 for r in rows:
  assert r['cpu_budget']['cpu_set']==list(range(32,40)) and r['workers']==8 and r['cache_mode']=='reuse'
  env={} if r['variant']=='stock' else {'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'}
  if r['variant'] not in ['stock','frozen']:
   mode=r['variant'];env['VPR_CPU_REPAIR_MODE']=mode
   log=(Path(r['directory'])/'process.log').read_text(errors='replace')
   assert f'CPU_REPAIR mode={mode} dynamic={int(mode in ["dynamic","both"])} reload={int(mode in ["reload","both"])}' in log
  assert r['candidate_environment']==env and not r['diagnostic_sample']
  assert r['log_evidence']['stage_seconds']['lookahead_build'] is None
 lookup={(r['case'],r['repeat'],r['variant']):r for r in rows};cases=sorted({r['case'] for r in rows})
 endpoints=[]
 for case in cases:
  for a,b in [('stock','none'),('frozen','both')]:
   for rep in range(3):
    x=lookup[case,rep,a];y=lookup[case,rep,b];keys=['route_body_sha256','critical_path_ns','wirelength','iterations']
    same=x['success'] and y['success'] and all(x.get(k)==y.get(k) for k in keys)
    endpoints.append(dict(case=case,repeat=rep,control=a,mode=b,equivalent=bool(same)))
 configs=[]
 for case in cases:
  for v in p['variants']:
   rr=[lookup[case,rep,v] for rep in range(3)];good=[r for r in rr if r['success']]
   configs.append(dict(case=case,variant=v,legal=len(good),iterations=[r['iterations'] for r in rr],critical_path_ns=[r['critical_path_ns'] for r in rr],wirelength=[r['wirelength'] for r in rr],route_hashes=[r.get('route_body_sha256') for r in rr],heap_pushes=[r['heap_pushes'] for r in rr],process_median=statistics.median(r['native_process_seconds'] for r in good) if good else None,routing_median=statistics.median(r['routing_seconds'] for r in good) if good else None))
 pairs=[]
 for case in cases:
  for a,b in [('none','dynamic'),('none','reload'),('dynamic','both'),('reload','both')]:
   vv=[];quality=[];routes=[]
   for rep in range(3):
    x=lookup[case,rep,a];y=lookup[case,rep,b]
    ok=x['success'] and y['success'] and y['critical_path_ns']<=x['critical_path_ns']*1.05 and y['wirelength']<=x['wirelength']*1.05
    quality.append(bool(ok));routes.append(x.get('route_body_sha256')==y.get('route_body_sha256'))
    if ok:vv.append(x['native_process_seconds']/y['native_process_seconds'])
   pairs.append(dict(case=case,control=a,candidate=b,quality=quality,same_routes=routes,ratios=vv,median=statistics.median(vv) if vv else None))
 data=dict(status='complete',samples=36,legal=sum(r['success'] for r in rows),endpoint_gate_passed=all(e['equivalent'] for e in endpoints),endpoints=endpoints,configurations=configs,pairs=pairs,default_changed=False)
 write_json(OUT/'analysis.json',data);write_json(OUT/'acceptance.json',dict(status='complete',samples=36,legal=data['legal'],endpoint_gate_passed=data['endpoint_gate_passed'],evidence_audit='passed',order_env_cpu_mode_audit='passed',default_changed=False))
 lines=['# 并行状态修复的同二进制消融','',f"36项测量，合法{data['legal']}；端点等价门槛：{data['endpoint_gate_passed']}。",'',
 '固定两个s38417布局、八个物理核32–39、同一原版lookahead缓存，每臂三次。none/dynamic/reload/both为同一隔离ELF的四种组合；stock/frozen为原版/此前两修复版外部校验。none与stock、both与frozen按路由主体、CPD、线长、迭代轮数逐项校验，门槛不通过时不得作因果归属。', '',
 'dynamic恢复动态BB更新列表传给分区路由器；关闭时用本地副本接收并丢弃，模拟原按值传参。reload修复包含全量BB重载后的全网通知及通知时序后移；不是仅一个通知开关。默认保留两修复。仅复制并替换route.cpp.o，历史库/源码/二进制不改，构建命令和补丁已归档。', '',
 '|布局|模式|合法|迭代轮数|CPD ns|线长|进程中位秒|路由中位秒|','|---|---|---:|---|---|---|---:|---:|']
 for c in configs:lines.append(f"|{c['case']}|{c['variant']}|{c['legal']}/3|{c['iterations']}|{c['critical_path_ns']}|{c['wirelength']}|{c['process_median']}|{c['routing_median']}|")
 lines+=['','|布局|单因素比较|质量合格|配对速度比|路由主体相同|','|---|---|---|---|---|']
 for c in pairs:lines.append(f"|{c['case']}|{c['control']}→{c['candidate']}|{c['quality']}|{c['ratios']}|{c['same_routes']}|")
 lines+=['','只有两种布局和共享宿主，不能据此普遍撤销正确性修复。失败与质量超门槛配对不算速度比。原生FULL/STA、独立原版复核及map字节一致性见evidence_verification.json；完整工作量与路由哈希见analysis.json。']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n');print(json.dumps(data,ensure_ascii=False))
if __name__=='__main__':main()
