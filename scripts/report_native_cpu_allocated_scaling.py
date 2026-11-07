"""Scaling statistics and trace/memory summaries, separate from exclusivity claims."""
import json,math,statistics
from collections import defaultdict
from pathlib import Path
from prepare import write_json,sha256
from scaling_common import verified
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105/scaling'
def read(p):return json.loads(Path(p).read_text())
def stat(a):return dict(ratios=a,median=statistics.median(a),minimum=min(a),maximum=max(a))
def main():
 p=read(OUT/'plan.json');s=read(OUT/'summary.json');rows=s['measurements'];rs=[r for r in rows if r['phase']=='formal'];idx={(r['graph'],r['workers'],r['repeat'],r['arm']):r for r in rs};scaling={};incremental={};memory={};diag={}
 for g in p['cases']:
  for a in ['per_group','pipeline']:
   for w in [1,2,4,8,16]:
    pair=[(idx.get((g,1,r,a)),idx.get((g,w,r,a))) for r in range(3)]
    if not all(x and y and x['component_valid'] and y['component_valid'] for x,y in pair):continue
    v=stat([x['build_seconds']/y['build_seconds'] for x,y in pair]);v['efficiency']=v['median']/w;v['median_seconds']=statistics.median(y['build_seconds'] for x,y in pair);scaling[f'{g}/{a}/{w}']=v
    memory[f'{g}/{a}/{w}']=dict(sampled_process_hwm_kib=[y['cpu_budget_audit']['peak_observed_hwm_kib'] for x,y in pair],sampled_process_rss_kib=[y['cpu_budget_audit']['peak_observed_rss_kib'] for x,y in pair],scope='5second sampled whole-process high-water mark, includes graph parsing and route tail; not exact stage peak or hard upper bound')
  for w in [1,2,4,8,16]:
   pair=[(idx.get((g,w,r,'per_group')),idx.get((g,w,r,'pipeline'))) for r in range(3)]
   if all(x and y and x['component_valid'] and y['component_valid'] for x,y in pair):incremental[f'{g}/{w}']=stat([x['build_seconds']/y['build_seconds'] for x,y in pair])
 for r in rows:
  if r['phase']!='diagnostic' or not r['component_valid']:continue
  f=Path(r['directory'])/'lookahead_profile.jsonl';events=[json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []
  diag[r['key']]=dict(events=events,source=str(f),source_sha256=sha256(f) if f.exists() else None,scope='Instrumented diagnostic only. Thread cumulative search_ns is not wall time, CPU busy, or idle wait. Formal timings exclude these rows.')
 complete=s['status']=='completed' and len(rs)==90 and all(r['component_valid'] for r in rs)
 if s['status']=='completed':
  for b in list(p['bindings'].values())+list(p['binaries'].values())+[p['runtime'],s['plan']]:verified(b)
  inputs={};art=[]
  for e in p['cases'].values():
   verified(e['case']);verified(e['reference_map']);c=read(e['case']['path'])
   for b in c['inputs'].values():inputs[b['path']]=b
  for b in inputs.values():verified(b)
  for r in rows:
   d=Path(r['directory']);assert read(d/'measurement.json')==r
   if r.get('wire_map_sha256'):assert sha256(d/'wire_map.bin')==r['wire_map_sha256']
   for n in ['measurement.json','process.log','wire_map.bin','lookahead_profile.jsonl']:
    f=d/n
    if f.exists():art.append(dict(path=str(f),sha256=sha256(f)))
  write_json(OUT/'audit.json',dict(status='passed',artifacts=art,rows=len(rows),complete_cohort=complete))
 allocation=read(OUT.parent/'platform/scaling_allocation_classification.json')
 analysis=dict(status=s['status'],formal_attempted=len(rs),formal_valid=sum(r['component_valid'] for r in rs),complete_cohort=complete,scaling=scaling,incremental=incremental,memory=memory,diagnostics=diag,allocation=allocation,strict_isolated_measurement=False,routing_success_claim=False)
 write_json(OUT/'analysis.json',analysis)
 lines=['# 另一CPU实例上的扩展性与内存测量','',f"状态{s['status']}，正式{len(rs)}/90项；有效{analysis['formal_valid']}项。",'', '资源为已有fpgaacc1实例、54CPU配额、同NUMA节点16个不同物理核内取1/2/4/8/16核。cpuset非独占，宿主共享；本实验不能补足严格隔离测量要求。', '', '|图/方法/核数|阶段秒中位|相对本方法1核加速|效率|','|---|---:|---:|---:|']
 for k,v in scaling.items():lines.append(f"|{k}|{v['median_seconds']:.3f}|{v['median']:.4f}×|{100*v['efficiency']:.2f}%|")
 lines+=['','|图/核数|组内→pipeline配对速度比中位|范围|','|---|---:|---:|']
 for k,v in incremental.items():lines.append(f"|{k}|{v['median']:.4f}×|{v['minimum']:.4f}–{v['maximum']:.4f}|")
 lines+=['','RSS/HWM是5秒采样的全进程观测，包含RR加载与1轮路由尾部，不等同lookahead阶段精确峰值。逐项原值在analysis.json。阶段结果允许预定未布通rc2，不能作为合法路由或完整流程速度证据。']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:analysis[k] for k in ['status','formal_attempted','formal_valid','complete_cohort']}))
if __name__=='__main__':main()
