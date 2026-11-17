#!/usr/bin/env python3
"""Recompute causal figures from retained runs. Never starts a solver or EDA."""
from pathlib import Path
import json,hashlib,csv,statistics as st,collections
P=Path(__file__).resolve().parent;R=P.parents[1];E=P/'evidence';T=P/'tables'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
bindings=read(E/'bindings.json')
for x in bindings:assert sha(E/x['snapshot'])==x['sha256'],x
rows=[];stats=[]
for cohort,filename in [('flat','flat_summary.json'),('large2d','large2d_summary.json')]:
 d=read(E/filename)
 for m in d['measurements']:
  if m['phase']!='component_formal':continue
  assert m['component_valid'] and m.get('map_matches_reference',True) and m['cpu_budget_audit']['verified']
  cmd=m['command'];rows.append(dict(cohort=cohort,case=m.get('case',m.get('graph')),workers=int(cmd[cmd.index('--num_workers')+1]),arm=m['arm'],repeat=m['repeat'],seconds=m.get('build_seconds',m.get('log_evidence',{}).get('stage_seconds',{}).get('lookahead_build')),key=m['key'],map_sha256=m.get('wire_map_sha256',m.get('map_sha256')),scope='construction_only',host=d.get('hostname',d.get('host'))))
for cohort,case,w in sorted(set((r['cohort'],r['case'],r['workers']) for r in rows)):
 arms={a:sorted([r for r in rows if (r['cohort'],r['case'],r['workers'],r['arm'])==(cohort,case,w,a)],key=lambda r:r['repeat']) for a in ['per_group','flat','pipeline']}
 if not all(arms.values()):continue
 assert all(len(v)==3 for v in arms.values())
 assert len({r['map_sha256'] for v in arms.values() for r in v})==1
 q=dict(cohort=cohort,case=case,workers=w)
 for a,rs in arms.items():
  xs=[r['seconds'] for r in rs];q[a]={'values':xs,'mean':st.mean(xs),'sd':st.stdev(xs)}
 for a,b in [('per_group','flat'),('flat','pipeline')]:
  assert [r['repeat'] for r in arms[a]]==[r['repeat'] for r in arms[b]]
  xs=[x['seconds']/y['seconds'] for x,y in zip(arms[a],arms[b])];q[a+'_over_'+b]={'values':xs,'mean':st.mean(xs),'sd':st.stdev(xs)}
 stats.append(q)
write(E/'causal_statistics.json',stats)
with (E/'causal_runs.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
lines=[]
for q in stats:
 vals=[q['case'].replace('_',r'\_').replace('dla\_like.medium','DLA'),str(q['workers'])]+[f"${q[a]['mean']:.2f}\\pm{q[a]['sd']:.2f}$" for a in ['per_group','flat','pipeline']]
 lines.append(' & '.join(vals)+r'\\')
(T/'causal.tex').write_text('\n'.join(lines)+'\n')
# Standard PGFPlots scientific figure; means and actual between-process SD.
fig=[r'\begin{tikzpicture}',r'\begin{groupplot}[group style={group size=2 by 1,horizontal sep=0.8cm},width=4.15cm,height=3.7cm,xtick={8,16},xmin=7,xmax=17,ymin=0,ymax=40,xlabel={Physical cores},ylabel={Build (s)},label style={font=\scriptsize},tick label style={font=\scriptsize},legend style={font=\scriptsize,at={(1.15,1.08)},anchor=south,legend columns=3},error bars/y dir=both,error bars/y explicit]']
for i,case in enumerate(['bnn','dla_like.medium']):
 fig.append(r'\nextgroupplot[title={'+''+'},ylabel={'+('Build (s)' if i==0 else '')+'}]')
 for arm,mark in [('per_group','square*'),('flat','triangle*'),('pipeline','o')]:
  coords=' '.join(f"({q['workers']},{q[arm]['mean']}) +- (0,{q[arm]['sd']})" for q in stats if q['case']==case)
  fig.append(r'\addplot+[mark='+mark+'] coordinates {'+coords+'};')
 if i==0:fig.append(r'\legend{Group,Flat,Pipeline}')
fig.extend([r'\end{groupplot}',r'\end{tikzpicture}']);(P/'figures/causal.tex').write_text('\n'.join(fig)+'\n')
profiles=[]
for shift in [0,20]:
 records=[json.loads(x) for x in (E/f'bnn_export_s{shift}.log').read_text().splitlines() if x.startswith('{')]
 ps=[r for r in records if r['kind']=='profile'];ws=[w for p in ps for w in p['waves']];assert len(ps)==40
 eligible=sum(p['eligible'] for p in ps)
 profiles.append(dict(shift=shift,samples=len(ps),waves=len(ws),max_qid_waves=max(len(p['waves']) for p in ps),eligible_edges=eligible,weighted_frontier=sum(w[1]*w[3] for w in ws)/eligible))
a,b=profiles;ratios={'wave_reduction':a['waves']/b['waves'],'round_reduction':a['max_qid_waves']/b['max_qid_waves'],'edge_work_increase_percent':100*(b['eligible_edges']/a['eligible_edges']-1),'weighted_frontier_ratio':b['weighted_frontier']/a['weighted_frontier']};write(E/'wave_statistics.json',dict(profiles=profiles,ratios=ratios))
(T/'waves.tex').write_text('\n'.join(name+' & '+fmt.format(a[key])+' & '+fmt.format(b[key])+r'\\' for name,key,fmt in [('Total sample waves','waves','{:,}'),('Maximum per-sample waves','max_qid_waves','{:,}'),('Eligible edge proposals','eligible_edges','{:,}'),('Edge-weighted frontier','weighted_frontier','{:,.0f}')])+'\n')
# Cache is a distinct mode with qualified full routes; never compare it to construction speed.
d=read(E/'cache_summary.json');cache=[]
for m in d['measurements']:
 if m.get('phase')=='formal' and m.get('mode')=='reuse':
  assert m['success'] and m['full_check'] and m['routing_success']
  assert m.get('independent',m.get('independent_check'))['returncode']==0
  assert '--read_router_lookahead' in m['command']
  cache.append({k:m.get(k) for k in ['key','case','arm','repeat','command','wire_map_sha256','map_sha256','process_seconds','independent_metrics']})
write(E/'cache_reuse_audit.json',{'qualified_formal_reuse_records':len(cache),'records':cache,'scope':'Historical fixed-input read-cache arms; not a fresh build speed ranking'})
allrows=read(R/'paper/dac2027/statistics_expanded/statistics.json')['formal_runs'];counts=collections.Counter((x['workers'],x['scope']) for x in allrows)
write(E/'CPU_scope_audit.json',{'records_by_workers_scope':[{ 'workers':k[0],'scope':k[1],'records':v} for k,v in sorted(counts.items())],'native_64worker_E2_claim':False,'resident_64worker_is_separate':True})
print(json.dumps({'causal_rows':len(rows),'configurations':len(stats),'wave_ratios':ratios,'qualified_cache_records':len(cache)},indent=2))
# Recompute native LSTM timing from actual formal rows and paired process identifiers.
d=read(E/'holdout_results.json');native={}
for arm in ['stock','flat','pipeline','alt_cpu','alt_cuda']:
 rs=sorted([x for x in d['formal_rows'] if x['case']=='lstm_s2' and x['backend']==arm],key=lambda x:x['repeat'])
 assert len(rs)==3,(arm,len(rs));assert all(x['qualified'] for x in rs)
 native[arm]=rs
lines=[]
for arm,label in [('stock','Stock'),('flat','Flat'),('pipeline','Pipeline'),('alt_cpu','ALT CPU'),('alt_cuda','ALT CUDA')]:
 vals=[]
 for metric in ['E2_s','Process_wall_s']:
  xs=[r[metric] for r in native[arm]];vals.append(f'${st.mean(xs):.3f}\\pm{st.stdev(xs):.3f}$')
 lines.append(label+' & '+' & '.join(vals)+r'\\')
assert (T/'lstm.tex').read_text()== '\n'.join(lines)+'\n'
paired={}
for arm in ['stock','flat','pipeline','alt_cpu']:
 for metric in ['E2_s','Process_wall_s']:
  assert [x['repeat'] for x in native[arm]]==[x['repeat'] for x in native['alt_cuda']]
  xs=[a[metric]/b[metric] for a,b in zip(native[arm],native['alt_cuda'])];paired[arm+'/'+metric]={'ratios':xs,'mean':st.mean(xs),'sd':st.stdev(xs)}
write(E/'native_recomputed_ratios.json',paired)
for m in d['map_differences']:
 if m['pair']=='alt_cpu_vs_flat':assert [m[x] for x in ['delay_word_differences','congestion_word_differences','missing_state_differences']]==[0,23111,0]
assert d['all_live_CPU_CUDA_pairs_equal']

print("PASS software-only retained statistics; no new solver execution")

# Independent recomputation of the historical eight-core GEMM cohort.
gemm={}
for x in read(E/'gemm_source_manifest.json'):
 f=E/'gemm'/Path(x['snapshot']).name;assert sha(f)==x['sha256'];r=read(f);assert r['success'] and r['full_check'] and r['independent_metrics']['full_check'];gemm[(r['repeat'],r['variant'])]=r
ratios=[];absolute={}
for arm in ['stock','frozen','pipeline']:
 rs=[gemm[(i,arm)] for i in range(3)];absolute[arm]={}
 for metric in ['process_seconds','lookahead']:
  vals=[r['process_seconds'] if metric=='process_seconds' else r['log_evidence']['stage_seconds']['lookahead_build'] for r in rs];absolute[arm][metric]={'values':vals,'mean':st.mean(vals),'sd':st.stdev(vals)}
for i in range(3):
 a,b=gemm[(i,'stock')],gemm[(i,'pipeline')];assert a['inputs']==b['inputs'];ratios.append(a['process_seconds']/b['process_seconds'])
assert abs(st.mean(ratios)-read(E/'native_computed_statistics.json')['CPU_GEMM_PROCESS']['mean'])<1e-12
write(E/'gemm_recomputed.json',dict(absolute=absolute,paired_Process=dict(values=ratios,mean=st.mean(ratios),sd=st.stdev(ratios))))
# Resident CPU is a separate software scope, recomputed from process means.
for c in read(E/'resident_CPU_delivery.json')['configurations']:
 means=[st.mean(x) for x in c['retained_seconds_by_process']];assert abs(st.mean(means)-c['mean_of_process_means_seconds'])<1e-12 and c['all_output_exact']
print('PASS GEMM raw paired cohort and separate resident CPU statistics')
