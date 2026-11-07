"""Recompute pairwise quality, timings and real cache-prefix aggregates."""
from collections import defaultdict
import json,math,statistics,sys
from pathlib import Path
from prepare import write_json,sha256
from scaling_common import verified,metrics
from qualify_native_cpu_width120 import quality
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105'
def read(p):return json.loads(Path(p).read_text())
def ratios(values):return dict(values=values,median=statistics.median(values),minimum=min(values),maximum=max(values))
def main():
 p=read(OUT/'plan.json');s=read(OUT/'summary.json');rows=s['measurements'];formal=[r for r in rows if r['phase']=='formal'];finished=s['status']=='completed'
 audit=[]
 if finished:
  for b in list(p['runner_bindings'].values())+list(p['binaries'].values())+[p['runtime'],s['plan']]:verified(b)
  inputs={}
  for c,v in s['prepared'].items():
   if v['ready']:
    verified(v['case']);verified(v['reference_map']);case=read(v['case']['path'])
    for b in case['inputs'].values():inputs[b['path']]=b
  for b in inputs.values():verified(b)
  for r in rows:
   d=Path(r['directory']);m=read(d/'measurement.json');assert m==r
   raw=metrics((d/'process.log').read_text(errors='replace'))
   for k in ['routing_success','full_check','critical_path_ns','wirelength']:assert raw[k]==r[k]
   if r.get('map_sha256'):assert sha256(d/'wire_map.bin')==r['map_sha256']
   if r.get('success'):
    assert sha256(d/'routed.route')==r['route_sha256'];im=metrics((d/'independent/process.log').read_text(errors='replace'));assert im['full_check'] and all(im[k]==r[k] for k in ['critical_path_ns','wirelength'])
   for name in ['process.log','measurement.json','wire_map.bin','routed.route','independent/process.log']:
    f=d/name
    if f.exists():audit.append(dict(path=str(f),sha256=sha256(f)))
  write_json(OUT/'audit.json',dict(status='passed',rows=len(rows),artifacts=audit,unique_inputs=len(inputs),scope='Frozen bindings, all row files/raw metrics/maps/routes/independent metrics; actual affinity/env checked by runner. No exclusivity claim.'))
 idx={(r['case'],r['mode'],r['repeat'],r['arm']):r for r in formal};comparisons={};quality_rows=[]
 for name in p['cases']:
  for mode in ['rebuild','reuse']:
   for a,b in [('stock','fixed_serial'),('stock','per_group'),('stock','pipeline'),('fixed_serial','pipeline'),('per_group','pipeline')]:
    pairs=[(idx.get((name,mode,i,a)),idx.get((name,mode,i,b))) for i in range(3)]
    eligible=all(x and y and x.get('success') and y.get('success') and quality(y,x)['passed'] for x,y in pairs)
    if not eligible:continue
    key=f'{name}/{mode}/{a}_to_{b}';comparisons[key]={'process':ratios([x['process_seconds']/y['process_seconds'] for x,y in pairs]),'qor':[quality(y,x) for x,y in pairs]}
    if mode=='rebuild' and all(x.get('build_seconds',0)>0 and y.get('build_seconds',0)>0 for x,y in pairs):comparisons[key]['lookahead']=ratios([x['build_seconds']/y['build_seconds'] for x,y in pairs])
 aggregates={}
 for mode in ['rebuild','reuse']:
  for cmp in ['stock_to_pipeline','fixed_serial_to_pipeline','per_group_to_pipeline']:
   entries=[comparisons.get(f'{c}/{mode}/{cmp}') for c in p['cases']]
   if all(entries):aggregates[mode+'/'+cmp]=math.prod(e['process']['median'] for e in entries)**.25
 groups=defaultdict(list)
 for r in rows:
  if r['phase']=='batch':groups[(r['case'],r['repeat'],r['arm'])].append(r)
 batches={}
 for c in ['tseng_s1','des_s1']:
  for a,b in [('stock','pipeline'),('per_group','pipeline')]:
   for k in [1,2,5]:
    vals=[]
    for i in range(3):
     x=sorted(groups[c,i,a],key=lambda r:r['index'])[:k];y=sorted(groups[c,i,b],key=lambda r:r['index'])[:k]
     if len(x)!=k or len(y)!=k or not all(xx['success'] and yy['success'] and quality(yy,xx)['passed'] for xx,yy in zip(x,y)):continue
     vals.append(sum(r['process_seconds'] for r in x)/sum(r['process_seconds'] for r in y))
    if len(vals)==3:batches[f'{c}/{a}_to_{b}/K{k}']=ratios(vals)
 compressed={}
 for c in ['tseng_s1','des_s1']:
  rs=sorted([r for r in rows if r['phase']=='compressed' and r['case']==c],key=lambda r:r['repeat'])
  if len(rs)!=3:continue
  pairs=[(idx.get((c,'rebuild',r['repeat'],'stock')),r) for r in rs]
  ok=all(x and x['success'] and y['success'] and quality(y,x)['passed'] for x,y in pairs)
  compressed[c]=dict(quality_eligible=ok,qor=[quality(y,x) for x,y in pairs if x],process=ratios([x['process_seconds']/y['process_seconds'] for x,y in pairs]) if ok else None)
 graphs={c:read(v['case']['path'])['inputs']['rr_graph']['sha256'] for c,v in s['prepared'].items() if v['ready']}
 analysis=dict(status=s['status'],attempted=len(rows),legal=sum(bool(r.get('success')) for r in rows),formal_attempted=len(formal),formal_expected=96,skipped=s['skipped'],cases_rr_hash=graphs,distinct_rr_graphs=len(set(graphs.values())),comparisons=comparisons,equal_layout_aggregate=aggregates,actual_cache_batches=batches,compressed_map=compressed,
  scope='One new architecture family; two held-out circuits, two layout seeds. Equal layout equals equal circuit weight here (2 layouts each). Shared host. Prefixes K1/2/5 correlated. Graph hash includes serialization metadata; no claim of distinct topology from hash alone.',complete_cohort=finished and len(formal)==96 and all(r['success'] for r in formal))
 write_json(OUT/'analysis.json',analysis)
 lines=['# 论文证据补齐：新架构与真实缓存批次','',f"状态：{s['status']}；已尝试{len(rows)}项，合法且独立检查通过{analysis['legal']}项；正式{len(formal)}/96项。",'', '两电路tseng/des、两个布局种子、原生k6_N10_mem32K_40nm架构。共享宿主；不称独占或完整编译加速。资格失败保留，不补样。','', '|模式/对照|四布局等权配对中位几何平均|','|---|---:|']
 for k,v in aggregates.items():lines.append(f'|{k}|{v:.6f}×|')
 lines+=['','|实际批次/对照/前缀长度|三次配对中位|范围|','|---|---:|---:|']
 for k,v in batches.items():lines.append(f"|{k}|{v['median']:.6f}×|{v['minimum']:.6f}–{v['maximum']:.6f}|")
 lines+=['','真实批次每个臂第一次重建并写出自己的等价缓存，随后4次读取该缓存。K=1/2/5为同一批次的相关前缀，不是独立实验，也不是五个独立设计。主时间为这些原生进程wall之和，不含独立检查。','', 'compressed_map为替代模型，对照需合法性和质量通过，不要求与map字节相等。结果与QoR见analysis.json。','', '第1项方法整理见method_and_ablation.md；第3项远端资源与扩展性见platform/及scaling/，须单独报告，不能把共享宿主结果包装成隔离结果。']
 lines+=['', '短进程计时敏感性及大图摊销模型见amortization_and_timer_sensitivity.md；内部flow指标方向一致，但几百分点差异仍需谨慎。', '', '![新架构与真实缓存批次](architecture_cache.png)']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:analysis[k] for k in ['status','attempted','legal','formal_attempted','equal_layout_aggregate']},ensure_ascii=False))
if __name__=='__main__':main()
