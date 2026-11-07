#!/usr/bin/env python3
"""Reproduce the expanded manuscript from frozen records; never launch VPR."""
from pathlib import Path
from collections import defaultdict, Counter
from statistics import mean, stdev, geometric_mean
import json, csv, hashlib, shutil, math, re, zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
E=P/'evidence/expanded_20261105';E.mkdir(parents=True,exist_ok=True)
O=P/'statistics_expanded';O.mkdir(exist_ok=True)
T=P/'tables';F=P/'figures'
manifest=[]
def freeze(src, dest=None):
 src=Path(src);raw=src.read_bytes();dst=E/(dest or str(src.relative_to(ROOT)).replace('/','__'))
 if dst.exists():assert dst.read_bytes()==raw, f'Changed frozen source: {src}'
 else:dst.write_bytes(raw)
 manifest.append(dict(source=str(src),snapshot=str(dst.relative_to(P)),sha256=hashlib.sha256(raw).hexdigest()))
 return json.loads(raw) if src.suffix=='.json' else raw
cohorts={'component':'native_lookahead_component_20261104','e2e':'native_cpu_width120_endtoend_20261104',
 'k6':'native_paper_closure_20261105','scale':'native_paper_closure_20261105/scaling',
 'flat':'native_flat_baseline_20261105','large2d':'native_large2d_followup_20261105'}
S={};A={};plans={}
for c,r in cohorts.items():
 base=ROOT/'results'/r
 for fn in ['summary.json','analysis.json','plan.json','independent_review.json','audit.json','finalization.json']:
  if (base/fn).exists():
   d=freeze(base/fn)
   if fn=='summary.json':S[c]=d;assert d['status']=='completed',c
   if fn=='analysis.json':A[c]=d
   if fn=='plan.json':plans[c]=d
   if fn in ['independent_review.json','audit.json']:assert d['status']=='passed',(c,fn)
 for fn in ['review.md','report.md','build_provenance.json','storage_event_audit.json']:
  if (base/fn).exists():freeze(base/fn)
for fn in ['native_lookahead_method_argument.md','native_cpu_paper_evidence_index.md','native_cpu_paper_reproduction.md']:
 freeze(ROOT/'docs'/fn)
old=json.loads((P/'statistics/statistics.json').read_text())
rows=[];raw_lookup={}
for r in old['records']:
 rows.append(dict(cohort='old_'+r['cohort'],phase=r['phase'],case=r['case'],workers=r['workers'],mode=r['cache'],arm={'frozen':'per_group'}.get(r['variant'],r['variant']),repeat=r['repeat'],key=r['key'],scope='full',build=r['lookahead_seconds'],process=r['process_seconds'],workflow=r['workflow_seconds'],route=r['routing_seconds'],cpd=r['critical_path_ns'],wl=r['wirelength']))
for c,s in S.items():
 for m in s['measurements']:
  cmd=m['command'];formal=m['phase'] in ['formal','component_formal','full_formal']
  if not formal:continue
  scope='component' if c in ['component','scale'] or m['phase']=='component_formal' else 'full'
  assert m['cpu_budget_audit']['verified'],m['key']
  if scope=='component':
   assert m.get('component_valid') and m.get('map_matches_reference',True),m['key']
  else:
   assert m['success'] and m['full_check'] and m['routing_success'],m['key']
   independent=m.get('independent',m.get('independent_check'));assert independent['returncode']==0,m['key']
   assert m['independent_metrics']['full_check'],m['key']
  build=m.get('build_seconds',m.get('log_evidence',{}).get('stage_seconds',{}).get('lookahead_build'))
  r=dict(cohort=c,phase=m['phase'],case=m.get('case',m.get('graph')),workers=int(cmd[cmd.index('--num_workers')+1]),mode=m.get('mode','rebuild'),arm=m['arm'],repeat=m['repeat'],key=m['key'],scope=scope,build=build,process=m['process_seconds'] if scope=='full' else None,workflow=m.get('workflow_seconds') if scope=='full' else None,route=m.get('routing_seconds') if scope=='full' else None,cpd=m.get('critical_path_ns') if scope=='full' else None,wl=m.get('wirelength') if scope=='full' else None)
  rows.append(r);raw_lookup[(c,m['key'])]=m
assert len(rows)==603,len(rows)
assert Counter(r['scope'] for r in rows)=={'full':414,'component':189}

def sm(xs):
 xs=list(xs);return dict(n=len(xs),values=xs,mean=mean(xs) if xs else None,sd=stdev(xs) if len(xs)>1 else None)
def fmt(s,nd=2):
 if not s['n']:return '--'
 if s['sd'] is None:return f"{s['mean']:.{nd}f}"
 return f"${s['mean']:.{nd}f}\\pm{s['sd']:.{nd}f}$"
def select(c,case,w=8,mode='rebuild',arm='pipeline',scope=None):
 rs=sorted([r for r in rows if (r['cohort'],r['case'],r['workers'],r['mode'],r['arm'])==(c,case,w,mode,arm) and (scope is None or r['scope']==scope)],key=lambda r:r['repeat'])
 assert rs,(c,case,w,mode,arm,scope)
 assert len({r['repeat'] for r in rs})==len(rs),(c,case,w,mode,arm,scope)
 return rs
def absstat(c,case,metric='build',w=8,mode='rebuild',arm='pipeline',scope=None):
 return sm(r[metric] for r in select(c,case,w,mode,arm,scope) if r[metric] is not None)
pairs=[]
def pair(c,case,control='stock',candidate='pipeline',metric='process',w=8,mode='rebuild',scope=None,control_w=None):
 a=select(c,case,control_w or w,mode,control,scope);b=select(c,case,w,mode,candidate,scope)
 assert [r['repeat'] for r in a]==[r['repeat'] for r in b]
 xs=[]
 for x,y in zip(a,b):
  ratio=x[metric]/y[metric];xs.append(ratio)
  if c in S:
   m=raw_lookup[(c,x['key'])];n=raw_lookup[(c,y['key'])]
   assert m.get('wire_map_sha256',m.get('map_sha256'))==n.get('wire_map_sha256',n.get('map_sha256'))
   # Same graph, input identity and CPU affinity are independently bound by the retained audit.
   if scope!='component' and metric=='process':
    assert y['cpd']<=1.05*x['cpd'] and y['wl']<=1.05*x['wl']
  pairs.append(dict(cohort=c,case=case,control=control,candidate=candidate,metric=metric,workers=w,control_workers=control_w or w,mode=mode,scope=scope,repeat=x['repeat'],control_key=x['key'],candidate_key=y['key'],ratio=ratio))
 return sm(xs)
def table(name,rs):
 (T/(name+'.tex')).write_text('\n'.join(' & '.join(map(str,r))+r' \\' for r in rs)+'\n')
macros=[];macro_values={}
def macro(name,s,d=3):
 macros.append('\\newcommand{\\'+name+'}{'+fmt(s,d)+'}');macro_values[name]=s
macro('PrimarySpeed',pair('old_evidence','gemm'))
macro('PrimaryCache',pair('old_evidence','gemm',mode='reuse'))
macro('PrimaryBuild',pair('old_evidence','gemm',metric='build'))
for case,label in [('bnn','Bnn'),('dla_like.medium','Dla')]:
 macro(label+'Scaling',pair('scale',case,'pipeline','pipeline','build',16,scope='component',control_w=1))
 macro(label+'GroupSixteen',pair('scale',case,'per_group','pipeline','build',16,scope='component'))
macro('DlaFour',pair('scale','dla_like.medium','per_group','pipeline','build',4,scope='component'))
macro('BnnTwoDProcess',pair('large2d','bnn_2d',scope='full'))
macro('BnnTwoDFlat',pair('large2d','bnn_2d','flat','pipeline',scope='full'))
macro('BnnTwoDBuildFlat',pair('large2d','bnn_2d','flat','pipeline','build',scope='full'))
# Dense component table: exact timing boundaries and paired ratios.
rs=[]
for c,case in [('component','bnn'),('component','lstm'),('component','dla_like.medium')]:
 rs.append([case.replace('dla_like.medium','DLA'),*[fmt(absstat(c,case,arm=a)) for a in ['stock','fixed_serial','per_group','pipeline']],fmt(pair(c,case,metric='build',scope='component'),3),fmt(pair(c,case,'per_group',metric='build',scope='component'),3)])
table('expanded_component',rs)
# Full process table, every fixed configuration separately; never pool hosts or arms.
rs=[]
for c,case in [('old_evidence','gemm'),('e2e','lstm_s2'),('e2e','bnn_s1'),('e2e','bnn_s2'),('k6','tseng_s1'),('k6','tseng_s2'),('k6','des_s1'),('k6','des_s2'),('flat','clma_2d'),('large2d','bnn_2d')]:
 for mode in ['rebuild','reuse'] if c not in ['flat','large2d'] else ['rebuild']:
  scope='full';ss=lambda a:fmt(absstat(c,case,'process',mode=mode,arm=a,scope=scope))
  rs.append([case.replace('_',r'\_'),{'rebuild':'B','reuse':'C'}[mode],ss('stock'),ss('fixed_serial') if c in ['e2e','k6'] else '--',ss('per_group'),ss('pipeline'),ss('flat') if c in ['flat','large2d'] else '--',fmt(pair(c,case,mode=mode,scope=scope),3),fmt(pair(c,case,'per_group',mode=mode,scope=scope),3)])
table('expanded_full',rs)
rs=[]
for c,cases,ws in [('flat',['bnn','dla_like.medium','clma_2d'],[8,16]),('large2d',['bnn_2d'],[8])]:
 for case in cases:
  for w in ws:
   rs.append([case.replace('dla_like.medium','DLA').replace('_',r'\_'),w,*[fmt(absstat(c,case,w=w,arm=a,scope='component')) for a in ['per_group','flat','pipeline']],fmt(pair(c,case,'per_group','flat','build',w,scope='component'),3),fmt(pair(c,case,'flat','pipeline','build',w,scope='component'),3)])
table('expanded_flat',rs)
# Formal means across layouts/circuits; explicitly equal circuits, not equal layouts.
aggregates=[]
for c,cases in [('e2e',['lstm_s2','bnn_s1','bnn_s2']),('k6',['tseng_s1','tseng_s2','des_s1','des_s2'])]:
 for mode in ['rebuild','reuse']:
  for control in ['stock','fixed_serial','per_group']:
   bycirc=defaultdict(list)
   for case in cases:bycirc[case.rsplit('_s',1)[0]].append(pair(c,case,control,mode=mode,scope='full')['mean'])
   value=geometric_mean(geometric_mean(xs) for xs in bycirc.values())
   aggregates.append(dict(cohort=c,mode=mode,control=control,candidate='pipeline',weighting='geometric mean of per-layout mean paired ratios within each circuit, then equal-circuit geometric mean',value=value))
   if c=='e2e' and mode=='rebuild' and control=='stock':macros.append(f'\\newcommand{{\\LargeThreeDProcess}}{{{value:.3f}}}')
# Measured cache prefixes, ratios reconstructed from actual sums.
batchrows=[];batchstats=[]
batch_records=[m for m in S['k6']['measurements'] if m['phase']=='batch']
assert len(batch_records)==90
def batch_prefix(case,arm,repeat,k):
 ms=sorted([m for m in batch_records if (m['case'],m['arm'],m['repeat'])==(case,arm,repeat) and m['index']<k],key=lambda m:m['index'])
 assert [m['index'] for m in ms]==list(range(k))
 for m in ms:
  assert m['success'] and m['full_check'] and m['routing_success'] and m['cpu_budget_audit']['verified']
  assert m['mode']==('rebuild' if m['index']==0 else 'reuse')
 return math.fsum(m['process_seconds'] for m in ms)
for case in ['tseng_s1','des_s1']:
 for control in ['stock','per_group']:
  vals=[]
  for k in [1,2,5]:
   arr=[batch_prefix(case,control,r,k)/batch_prefix(case,'pipeline',r,k) for r in range(3)]
   reference=A['k6']['actual_cache_batches'][f'{case}/{control}_to_pipeline/K{k}']['values']
   assert all(math.isclose(x,y,rel_tol=1e-12) for x,y in zip(arr,reference))
   s=sm(arr)
   vals.append(fmt(s,3));batchstats.append(dict(case=case,control=control,k=k,**s))
  batchrows.append([case.replace('_',r'\_'),{'stock':'Stock','per_group':'Group'}[control]]+vals)
table('expanded_cache',batchrows)
# Stage memory diagnostics: one observation/arm, not formal performance repeats.
rs=[]
for c in ['flat','large2d']:
 for key,m in A[c]['memory'].items():
  case,arm=key.split('/')
  rs.append([case.replace('dla_like.medium','DLA').replace('_',r'\_'),{'per_group':'Group','pipeline':'Pipeline','flat':'Flat'}[arm],f"{m['entry_mib']:.1f}",f"{m['observed_peak_mib']:.1f}",f"{m['observed_growth_mib']:.1f}",f"{m['max_live_workspace_label_capacity_mib']:.1f}",m['max_workspaces'],m['sample_map_bound'],m['group_map_count']])
table('expanded_memory',rs)
(T/'expanded_macros.tex').write_text('\n'.join(macros)+'\n')
# Complete machine-readable summary, including nondisplayed metrics.
grp=defaultdict(list)
for r in rows:grp[tuple(r[k] for k in ['cohort','phase','case','workers','mode','arm','scope'])].append(r)
summary=[]
for key,group in grp.items():
 for metric in ['build','process','workflow','route','cpd','wl']:
  xs=[r[metric] for r in sorted(group,key=lambda r:r['repeat']) if r[metric] is not None]
  if xs:summary.append(dict(zip(['cohort','phase','case','workers','mode','arm','scope'],key))|dict(metric=metric,**sm(xs)))
for s in summary:
 xs=s['values'];mu=math.fsum(xs)/len(xs);assert math.isclose(mu,s['mean'],rel_tol=1e-12)
 if len(xs)>1:assert math.isclose(math.sqrt(math.fsum((x-mu)**2 for x in xs)/(len(xs)-1)),s['sd'],rel_tol=1e-11,abs_tol=1e-12)
# Deduplicate pairs reused by several displays.
pairs=list({json.dumps(p,sort_keys=True):p for p in pairs}.values())
def csvout(fn,rs):
 with (O/fn).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
csvout('formal_runs.csv',rows);csvout('absolute_summary.csv',summary);csvout('displayed_pairs.csv',pairs);csvout('circuit_aggregates.csv',aggregates);csvout('cache_prefix_statistics.csv',batchstats)
(O/'statistics.json').write_text(json.dumps(dict(formal_runs=rows,summary=summary,pairs=pairs,aggregates=aggregates,macro_values=macro_values,cache_prefixes=batchstats),indent=2)+'\n')
(E/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(O/'verification.json').write_text(json.dumps(dict(status='passed',formal_records=len(rows),full_formal=414,component_formal=189,original_legal_formal=222,new_formal=381,summary_count=len(summary),all_mean_sd_recomputed=True,source_cohorts_reviewed=True,new_solver_runs=0),indent=2)+'\n')
(O/'README.txt').write_text('Expanded manuscript statistics, 2026-11-05.\n603 formal records = 414 legal full-flow + 189 construction-only. Construction-only capped route tails are not legal routed designs.\nMeans and n-1 sample SD within fixed configuration; paired speedups computed before aggregation.\nCircuit aggregates use equal-circuit geometric means of per-layout mean paired ratios. Historical reports used medians and sometimes layout weights; they are retained unchanged in evidence.\n90 cache-batch processes, compressed-map alternatives, pilots, qualifications and instrumented memory diagnostics are separate from the 603 formal records.\nNo new solver runs. Shared-host cohorts remain separate.\n')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'axes.titlesize':9,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
blue='#24577A';orange='#C87625';green='#287D67';gray='#727D88';purple='#705B99'
def save(fig,name):
 for ext in ['pdf','svg','png']:fig.savefig(F/f'{name}.{ext}',bbox_inches='tight',dpi=220)
 plt.close(fig)
# Measured motivation figure. Whole-process residual is computed per run, not inferred from a two-stage sum.
fig,ax=plt.subplots(1,2,figsize=(7.05,2.55))
arms=['stock','per_group','pipeline'];labels=['Stock VPR','Group','Pipeline']
for i,(a,label,col) in enumerate(zip(arms,labels,[gray,orange,blue])):
 s=absstat('old_evidence','gemm',arm=a);ax[0].bar(i,s['mean'],yerr=s['sd'],color=col,capsize=3,width=.65)
 ax[0].text(i,s['mean']+5,f"{s['mean']:.2f}",ha='center',fontsize=8)
 ax[0].scatter([i-.08,i,i+.08],s['values'],c='black',s=8,zorder=4)
 ax[0].set(xticks=range(3),xticklabels=labels,ylabel='Lookahead construction (s)',ylim=(0,180),title='(a) Same eight-core budget')
rs=[select('old_evidence','gemm',arm=a) for a in arms]
build=[mean(r['build'] for r in rr) for rr in rs];route=[mean(r['route'] for r in rr) for rr in rs];other=[mean(r['process']-r['build']-r['route'] for r in rr) for rr in rs]
ax[1].bar(range(3),build,label='Lookahead',color=blue)
ax[1].bar(range(3),route,bottom=build,label='Routing',color=orange)
ax[1].bar(range(3),other,bottom=np.array(build)+route,label='Other process work',color='#CFD6DC')
for i,a in enumerate(arms):
 s=absstat('old_evidence','gemm','process',arm=a);ax[1].errorbar(i,s['mean'],yerr=s['sd'],color='black',capsize=3);ax[1].text(i,s['mean']+8,f"{s['mean']:.2f}",ha='center')
ax[1].set(xticks=range(3),xticklabels=labels,ylabel='VPR process (s)',ylim=(0,410),title='(b) Construction drives process savings');ax[1].legend(frameon=False,fontsize=6.6,loc='upper right')
for a in ax:a.grid(axis='y',alpha=.12);a.set_axisbelow(True)
fig.tight_layout(w_pad=2);save(fig,'expanded_motivation')
# Scaling on its own host, ratio of paired observations to same-method 1-core.
fig,axs=plt.subplots(2,3,figsize=(7.05,4.15));ws=[1,2,4,8,16]
for j,case in enumerate(['bnn','dla_like.medium','tseng_2d']):
 for arm,col,marker in [('per_group',orange,'s'),('pipeline',blue,'o')]:
  gs=[absstat('scale',case,w=w,arm=arm) for w in ws]
  axs[0,j].errorbar(ws,[s['mean'] for s in gs],yerr=[s['sd'] for s in gs],marker=marker,color=col,label={'per_group':'Group','pipeline':'Pipeline'}[arm],capsize=2)
  base=select('scale',case,1,arm=arm)
  sp=[sm(x['build']/y['build'] for x,y in zip(base,select('scale',case,w,arm=arm))) for w in ws]
  axs[1,j].errorbar(ws,[s['mean'] for s in sp],yerr=[s['sd'] for s in sp],marker=marker,color=col,capsize=2)
 axs[0,j].set_title({'bnn':'BNN (3D)','dla_like.medium':'DLA (3D)','tseng_2d':'tseng (2D)'}[case]);axs[0,j].legend(frameon=False)
 axs[1,j].plot(ws,ws,ls=':',color='0.6',lw=.8);axs[1,j].set_ylim(0,17)
 for i in [0,1]:axs[i,j].set_xscale('log',base=2);axs[i,j].set_xticks(ws,ws);axs[i,j].grid(alpha=.12)
 axs[1,j].set_xlabel('Physical cores')
axs[0,0].set_ylabel('Lookahead time (s)');axs[1,0].set_ylabel('Speedup vs. same method at 1 core')
fig.tight_layout(h_pad=.8,w_pad=1.2);save(fig,'expanded_scaling')
# 3D graph and exploration context, informed by supplied graphics, redrawn from verified semantics.
fig,axs=plt.subplots(1,2,figsize=(7.05,2.75),gridspec_kw={'width_ratios':[1,1.3]})
a=axs[0];a.set(xlim=(-.2,4.6),ylim=(-.4,3.4));a.axis('off')
for layer,dy in [(0,0),(1,1.5)]:
 a.add_patch(Polygon([(0,dy), (3,dy),(4,dy+.8),(1,dy+.8)],facecolor='#E3EDF5',edgecolor=blue,lw=1))
 for x in [.6,1.5,2.4]:
  for y in [.2,.55]:a.add_patch(Rectangle((x+y,dy+y),.23,.14,facecolor=blue))
 a.text(.1,dy+.95,f'Active fabric layer {layer}',fontsize=8,color=blue)
for x in [1.1,2.8]:a.plot([x,x],[.5,2.0],color=orange,lw=3)
a.text(3.1,1.2,'CHANZ\n+ switch delay',fontsize=7,color=orange,ha='center')
a.text(.1,-.3,r'$F[\ell_s,\ell_t,c,s,\Delta x,\Delta y]$',fontsize=10)
a.set_title('(a) Layer-aware resource and cost model')
b=axs[1];b.set(xlim=(0,10),ylim=(0,5));b.axis('off')
boxes=[(.2,3.2,2.7,1,'Architecture\n+ resource graph',gray),(3.65,3.2,2.7,1,'Parallel lookahead\nconstruction (ours)',blue),(7.1,3.2,2.7,1,'Native routing\n+ QoR evaluation',green)]
for x,y,w,h,txt,col in boxes:b.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',facecolor=col,edgecolor='none'));b.text(x+w/2,y+h/2,txt,ha='center',va='center',color='white',fontsize=7)
for x in [3,6.5]:b.annotate('',xy=(x+.5,3.7),xytext=(x,3.7),arrowprops={'arrowstyle':'->'})
b.annotate('changed topology / costs: rebuild',xy=(1.5,3),xytext=(5,2),ha='center',fontsize=7,arrowprops={'arrowstyle':'->','connectionstyle':'angle,angleA=0,angleB=-90,rad=8'})
b.text(5,.95,'Same compatible graph: reuse the table\nLayer assignment alone need not invalidate it',ha='center',fontsize=8)
b.text(5,.15,'Architecture exploration and placement evaluation\nbenefit from a faster, equivalent routing backend',ha='center',fontsize=8,color=blue)
b.set_title('(b) Repeated CAD evaluation')
fig.tight_layout();save(fig,'expanded_context')
# Dependencies and task-level parallelism; schedule is explicitly illustrative.
fig,axs=plt.subplots(1,3,figsize=(7.05,2.5),gridspec_kw={'width_ratios':[1,1,1.15]})
for k in [0,1]:
 a=axs[k];a.set(xlim=(0,2.5),ylim=(-.7,8));a.invert_yaxis();a.set_yticks([0.5,3.5,7.5],['0','3','7']);a.set_xticks([]);a.set_xlabel('Illustrative time');a.set_ylabel('Worker' if k==0 else '')
 for w in range(8):
  for t in range(2):
   active=(k==1 or w<4);a.add_patch(Rectangle((t*1.15,w),1,.78,facecolor=(blue if (w//4+t)%2==0 else orange) if active else '#E9ECEF',edgecolor='white'))
   if active:a.text(t*1.15+.5,w+.4,f'g{t if k==0 else 2*t+w//4}',ha='center',va='center',color='white',fontsize=6)
 a.set_title(['(a) Group barriers','(b) Cross-group tasks'][k],fontsize=8)
a=axs[2];a.axis('off');a.set(xlim=(0,4),ylim=(0,5))
for y,text_,col in [(4,'Ordered (group, sample) jobs',gray),(2.8,'Private native floods',blue),(1.6,'Ordered delay/congestion merge',orange),(.4,'Layer-pair commit + interpolation',green)]:
 a.add_patch(FancyBboxPatch((0,y),3.9,.65,boxstyle='round,pad=.03',facecolor=col,edgecolor='none'));a.text(1.95,y+.33,text_,ha='center',va='center',fontsize=6.5,color='white')
 if y>.4:a.annotate('',xy=(1.95,y-.5),xytext=(1.95,y),arrowprops={'arrowstyle':'->'})
a.set_title('(c) Pipeline execution contract',fontsize=8)
fig.tight_layout(w_pad=.9);save(fig,'expanded_schedule')
print(json.dumps({'formal':len(rows),'full':414,'component':189,'aggregates':aggregates,'key_results':macro_values},indent=2))
# Dataset inventory: count the actual width-120 XML rather than copied width-100 geometry.
scans={x['case']:x for x in json.loads((E/'input_graph_scan.json').read_text())}
datasets=[]
def geometry(place):
 lines=Path(place).read_text().splitlines();xy=re.search(r'Array size: (\d+) x (\d+)', '\n'.join(lines)).groups()
 counts=Counter(l.split()[4] for l in lines if len(l.split())>=6 and l.split()[-1].startswith('#') and not l.startswith('#'))
 return [int(x) for x in xy]+[len(counts)],dict(counts),sum(counts.values())
def ds(name,typ,family,layers,nlayouts,nets,place,graph,scope):
 grid,lc,blocks=geometry(place);assert grid[-1]==layers,(name,grid)
 row=dict(case=name,type=typ,architecture=family,layers=layers,layouts=nlayouts,nets=nets,placed_blocks=blocks,grid=grid,placed_layer_counts=lc,rr_nodes=graph['rr_nodes'],rr_edges=graph['rr_edges'],chanz=graph['chanz_nodes'],role=scope)
 datasets.append(row)
for name,typ in [('gemm','Matrix multiply'),('softmax','NN softmax'),('reduction','NN reduction'),('elliptic','DSP filter')]:
 base=ROOT/('data/scaling_elliptic_20261025/elliptic' if name=='elliptic' else f'data/scaling_20261025/{name}')
 inp=freeze(base/'prepared.json');g=freeze(base/'unit/manifest.json')
 ds(name,typ,'Hecate' if name=='elliptic' else 'KOIOS-3D',2,1,inp['nets'],inp['inputs']['placement']['path'],dict(rr_nodes=g['nodes'],rr_edges=g['edges'],chanz_nodes=g['nodes_by_type']['CHANZ']),'Full, ablation' if name in ['gemm','elliptic'] else 'Full confirmation')
for name,typ,nets in [('alu4','Logic / ALU',713),('diffeq','Arithmetic',1084),('s38417','Sequential logic',4444)]:
 p=ROOT/f'results/native_cpu_evidence_20261102/prepared/{name}_s1';inp=freeze(p/'vpr_case.json');scan=scans[name+'_s1'];assert scan['sha256']==inp['inputs']['rr_graph']['sha256']
 ds(name,typ,'Hecate',2,2,nets,inp['inputs']['placement']['path'],scan,'Fresh layouts')
for name,label,typ in [('bnn','BNN-3D','Binary NN'),('lstm','LSTM','Recurrent NN'),('dla_like.medium','DLA','DL accelerator')]:
 inp=freeze(ROOT/f'results/native_cpu_width120_20261104/{name}_s1/vpr_case.json');m=next(m for m in S['component']['measurements'] if m['graph']==name and m['phase']=='formal');scan=scans[name+'_s1'];assert scan['sha256']==plans['component']['cases'][name]['rr_sha256'] if isinstance(plans['component']['cases'],dict) else True
 nets=m['log_evidence']['iterations'][0]['rerouted_nets']
 ds(label,typ,'KOIOS-3D',2,2,nets,inp['inputs']['placement']['path'],scan,'Stage; conditional full' if name!='dla_like.medium' else 'Stage; failed full')
for c,case,label,typ,layouts,nets,family in [('k6','tseng_s1','tseng','Arithmetic',2,572,'k6'),('k6','des_s1','des','Cryptographic',2,954,'k6'),('flat','clma_2d','clma','Logic',1,4585,'k6'),('large2d','bnn_2d','BNN-2D','Binary NN',1,78308,'KOIOS-2D')]:
 m=next(m for m in S[c]['measurements'] if m.get('case',m.get('graph'))==case and m['phase'] in ['formal','full_formal']);cmd=m['command'];scan=scans[case]
 ds(label,typ,family,1,layouts,nets,cmd[cmd.index('--place_file')+1],scan,'Full, scaling' if c=='k6' else 'Full, flat control')
rs=[]
for d in datasets:
 rs.append([d['case'],d['type'],d['architecture'],f"{d['grid'][0]}$\\times${d['grid'][1]}$\\times${d['layers']}",d['layouts'],f"{d['placed_blocks']:,}",f"{d['nets']:,}",f"{d['rr_nodes']/1e6:.3f}",f"{d['rr_edges']/1e6:.3f}",f"{d['chanz']:,}"])
table('expanded_datasets',rs);csvout('datasets.csv',datasets)
(O/'datasets.json').write_text(json.dumps(datasets,indent=2)+'\n')
(E/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# End-to-end process speedups; separate cohorts and graphs explicitly.
fig,axs=plt.subplots(1,2,figsize=(7.05,2.6),gridspec_kw={'width_ratios':[1,1]})
for ax,c,cases,title in [(axs[0],'e2e',['lstm_s2','bnn_s1','bnn_s2'],'(a) Conditional 3D subset'),(axs[1],'k6',['tseng_s1','tseng_s2','des_s1','des_s2'],'(b) Independent 2D architecture')]:
 for offset,mode,marker,col in [(-.11,'rebuild','o',blue),(.11,'reuse','s',orange)]:
  gs=[pair(c,case,mode=mode,scope='full') for case in cases]
  ax.errorbar(np.arange(len(cases))+offset,[g['mean'] for g in gs],yerr=[g['sd'] for g in gs],fmt=marker,capsize=3,color=col,label={'rebuild':'Rebuild','reuse':'Cache'}[mode])
  for j,g in enumerate(gs):ax.scatter(j+offset+np.array([-.035,0,.035]),g['values'],s=7,color=col,alpha=.65)
 ax.axhline(1,color='0.5',ls='--',lw=.8);ax.set_xticks(range(len(cases)),[x.replace('_',' ') for x in cases],fontsize=7);ax.set_title(title);ax.grid(axis='y',alpha=.15);ax.legend(frameon=False,loc='upper right')
axs[0].set_ylabel('Process speedup: Stock / Pipeline');axs[0].set_ylim(.8,1.95);axs[1].set_ylim(.75,1.55)
fig.tight_layout(w_pad=2);save(fig,'expanded_endtoend')
# Include comparisons used only by plots as well as those used by tables.
pairs=list({json.dumps(p,sort_keys=True):p for p in pairs}.values())
csvout('displayed_pairs.csv',pairs)
(O/'statistics.json').write_text(json.dumps(dict(formal_runs=rows,summary=summary,pairs=pairs,aggregates=aggregates,macro_values=macro_values,cache_prefixes=batchstats),indent=2)+'\n')
# Package derived statistics separately from the anonymous typesetting source.
with zipfile.ZipFile(P/'statistics_expanded.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
 for path in O.iterdir():
  if path.is_file():z.write(path,path.name)
print('Dataset inventory:',len(datasets),'architecture/circuit rows; total layout instances:',sum(d['layouts'] for d in datasets))
