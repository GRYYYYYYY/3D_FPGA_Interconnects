"""Model from independently measured rebuild/hit runs; never label as batch execution."""
import json,re,math,statistics
from pathlib import Path
from prepare import write_json,sha256
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105'
def read(p):return json.loads(Path(p).read_text())
def calc(rows,case_names):
 idx={(r['case'],r['mode'],r['repeat'],r['arm']):r for r in rows if r['phase']=='formal'};out={}
 for c in case_names:
  for a,b in [('stock','pipeline'),('per_group','pipeline')]:
   for k in [1,2,5,10]:
    values=[]
    for rep in range(3):
     needed=[idx.get((c,m,rep,x)) for x in [a,b] for m in ['rebuild','reuse']]
     if not all(r and r['success'] for r in needed):continue
     ar,ah,br,bh=needed;values.append((ar['process_seconds']+(k-1)*ah['process_seconds'])/(br['process_seconds']+(k-1)*bh['process_seconds']))
    if len(values)==3:out[f'{c}/{a}_to_{b}/K{k}']=dict(values=values,median=statistics.median(values))
 return out
new=read(OUT/'summary.json');oldpath=ROOT/'results/native_cpu_width120_endtoend_20261104/summary.json';old=read(oldpath)
model=dict(scope='Analytical sums of separately measured rebuild and reuse process times: T(K)=R+(K-1)H. Not new batch observations, not full compilation, no unmeasured cache hit-rate claim.',small_prediction=calc(new['measurements'],['tseng_s1','des_s1']),historical_large_prediction=calc(old['measurements'],['lstm_s2','bnn_s1','bnn_s2']),historical_binding=dict(path=str(oldpath),sha256=sha256(oldpath)))
a=read(OUT/'analysis.json');validation={}
for key,actual in a['actual_cache_batches'].items():
 pred=model['small_prediction'].get(key)
 if pred:validation[key]=dict(predicted_ratio=pred['median'],actual_ratio=actual['median'],relative_ratio_error_percent=100*(pred['median']/actual['median']-1))
model['small_model_vs_actual']=validation
# Secondary timer sensitivity: preserve primary declared process metric.
flow={}
for r in new['measurements']:
 if r['phase']!='formal':continue
 text=(Path(r['directory'])/'process.log').read_text();m=re.findall(r'The entire flow of VPR took ([\d.]+) seconds',text)
 if m:flow[r['case'],r['mode'],r['repeat'],r['arm']]=float(m[-1])
secondary={}
for mode in ['rebuild','reuse']:
 for x,y in [('stock','pipeline'),('per_group','pipeline')]:
  med=[]
  for c in ['tseng_s1','tseng_s2','des_s1','des_s2']:
   vals=[flow[c,mode,r,x]/flow[c,mode,r,y] for r in range(3)];med.append(statistics.median(vals))
  secondary[mode+'/'+x+'_to_'+y]=math.prod(med)**.25
model['internal_flow_secondary']=secondary
model['timer_limit']='Primary process timer includes Python timed-wait completion detection (polling may add ~50 ms on POSIX). New2D processes last about1–2s; small percent differences need caution. Native internal flow timer is secondary, not a replacement endpoint.'
write_json(OUT/'amortization_and_timer_sensitivity.json',model)
lines=['# 缓存摊销模型与计时敏感性','',model['scope'],'','模型来自各臂独立测得的重建R和缓存H，不以实际batch重新拟合；小图实际batch另列，K前缀相关。历史大图这里只计算情景，不能称新增真实大图批次。','','|历史大图/对照/K|估算速度比中位|','|---|---:|']
for k,v in model['historical_large_prediction'].items():lines.append(f"|{k}|{v['median']:.6f}×|")
lines+=['','短小2D进程约1–2秒，Python超时wait的退出检测可能影响几百分点差值。原生内部flow作为辅助敏感性指标，不替换预先声明的进程wall。','', '|模式/对照|原生内部flow速度比|','|---|---:|']
for k,v in secondary.items():lines.append(f'|{k}|{v:.6f}×|')
(OUT/'amortization_and_timer_sensitivity.md').write_text('\n'.join(lines)+'\n');print(json.dumps(secondary))
