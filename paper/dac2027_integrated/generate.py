"""Regenerate publication artifacts from frozen records only; no solver invocation."""
from pathlib import Path
import json,hashlib,runpy,statistics,importlib.util,ast
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parent; R=P.parents[1]; BASE='ea1d0d793f7655d421595fcf2ee961c9cdc9af92'
r62tree=ast.parse((R/'scripts/la_accel_round6_2_paper.py').read_text())
mathnode=next(n.value for n in r62tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='math' for t in n.targets))
r62_format=eval(compile(ast.Expression(mathnode),'<frozen R6.2 formatter>','eval'))
summary=runpy.run_path(str(R/'paper/dac2027/paper_statistics.py'),run_name='frozen_stats')['summary']
inputs={}
def read(s):
 p=R/s;raw=p.read_bytes();inputs[s]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
S='results/lookahead_r6_2_20261109T191213Z/evidence_snapshot/'
h=read(S+'holdout_results.json'); old=read('results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/native_e2.json'); cpu=read('paper/dac2027/statistics_expanded/statistics.json'); opt=read(S+'targeted_optimization_results.json')
read(S+'holdout_plan.json');read(S+'holdout_selection.json');read(S+'input_and_baseline_audit.json');read(S+'baseline_binding.json');read(S+'hardware_service_decision.json');read(S+'physical_memory_service_contract.json');read(S+'native_stage_attribution.json');read(S+'paper_binding.json')
# Verify the complete R6.2 manifest before using its summaries.
m=read(S+'manifest.json')
for rel,v in m['files'].items():assert hashlib.sha256((R/S/rel).read_bytes()).hexdigest()==v['sha256'],rel
assert len(cpu['formal_runs'])==603
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42})
ledger=[]; computed={}; macros=[]
def fmt(a):
 sd=a['sample_sd'];return r62_format(a['mean'],sd).strip('$') if sd is not None else f"{a['mean']:.3f}"
def claim(cid,rows,control,candidate,scope,cohort,source,table):
 a=sorted([x for x in rows if x['backend']==control],key=lambda x:x['repeat']);b=sorted([x for x in rows if x['backend']==candidate],key=lambda x:x['repeat']);assert len(a)==len(b)==3
 vals=[x[scope]/y[scope] for x,y in zip(a,b)];st=summary(vals);computed[cid]=st
 ledger.append(dict(claim_id=cid,source_commit=BASE,source_json=source,source_sha256=inputs[source],cohort=cohort,case=a[0]['case'],comparison=[control,candidate],scope=scope,representation='original',shift=20,statistic='mean_of_paired_ratios',n_process_pairs=3,value=st,measurement_kind='measured',rows=[dict(row_id=f"{x['case']}/{x['backend']}/{x['repeat']}",host=x['hostname'],binary_sha256=x['binary_sha256'],library_sha256=x['library_sha256'],inputs=x['input_bindings']) for x in a+b],table_figure=table,allowed_claim='native measured acceleration on the frozen case only',limitations=['not STRICT equivalent','same-family holdout only','runtime repeats, not placement repeats','cohort cannot be pooled']))
 return st
arms=['stock','flat','pipeline','alt_cpu','alt_cuda'];names=['Stock','Flat','Pipeline','ALT CPU','ALT CUDA']
rows=[x for x in h['formal_rows'] if x['case']=='lstm_s2']; assert len(rows)==15 and all(x['qualified'] for x in rows)
lines=[]
for arm,name in zip(arms,names):
 a=[x for x in rows if x['backend']==arm];lines.append(name+' & $'+fmt(summary(x['E2_s'] for x in a))+'$ & $'+fmt(summary(x['Process_wall_s'] for x in a))+'$'+r'\\')
(P/'tables/lstm.tex').write_text('\n'.join(lines)+'\n')
for base,tag in [('pipeline','Pipe'),('flat','Flat'),('alt_cpu','AltCpu'),('stock','Stock')]:
 for scope,short in [('E2_s','Build'),('Process_wall_s','Proc')]:
  st=claim('LSTM'+tag+short,rows,base,'alt_cuda',scope,'R6.2_P1_LSTM_rotated',S+'holdout_results.json','tab:lstm; fig:native');macros.append(r'\newcommand{\Lstm'+tag+short+'}{$'+fmt(st)+r'\times$}')
fig,axs=plt.subplots(1,2,figsize=(7,2.5))
for ax,scope,title in zip(axs,['E2_s','Process_wall_s'],['Native construction (E2)','Complete Process']):
 vals=[[x[scope] for x in rows if x['backend']==a] for a in arms];ax.bar(range(5),[np.mean(v) for v in vals],yerr=[np.std(v,ddof=1) for v in vals],color=['#9299a2','#589bb2','#346d95','#cc9953','#489b79'],capsize=3)
 ax.set_xticks(range(5),names,rotation=20);ax.set_ylabel('Seconds');ax.set_title(title);ax.spines[['top','right']].set_visible(False)
fig.tight_layout();fig.savefig(P/'figures/native.pdf');plt.close(fig)
lines=[]
for case in ['bnn','s38417']:
 a=[x for x in old['rows'] if x['case']==case];cols=[]
 for scope,tag in [('E2_s','Build'),('Process_wall_s','Proc')]:
  st=claim(case+tag,a,'optimized','alt_cuda',scope,'R6.1_native_worker','results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/native_e2.json','tab:legacy');cols.append('$'+fmt(st)+'$')
 lines.append(('BNN' if case=='bnn' else 's38417')+' & '+' & '.join(cols)+r'\\')
(P/'tables/legacy.tex').write_text('\n'.join(lines)+'\n')
# CPU scaling is a separate construction-only cohort; use existing frozen raw rows.
fig,axs=plt.subplots(1,2,figsize=(7,2.35))
for ax,case in zip(axs,['bnn','dla']):
 for arm in ['per_group','pipeline']:
  a=[x for x in cpu['formal_runs'] if x['cohort']=='scale' and x['case'].lower().startswith(case) and x['arm']==arm];
  if not a:continue
  cores=sorted(set(x['workers'] for x in a));v=[[x['build'] for x in a if x['workers']==n] for n in cores]
  ax.errorbar(cores,[np.mean(z) for z in v],yerr=[np.std(z,ddof=1) for z in v],marker='o',capsize=3,label='Group' if arm=='per_group' else 'Pipeline')
 ax.set_title(case.upper()+' / CPU scaling cohort');ax.set_xticks([1,2,4,8,16]);ax.set_xlabel('Physical cores');ax.set_ylabel('Construction seconds');ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False)
fig.tight_layout();fig.savefig(P/'figures/scaling.pdf');plt.close(fig)
# Bind the old CPU headline to existing paired observations, without pooling 603 records.
a=[x for x in cpu['pairs'] if x['cohort']=='old_evidence' and x['case']=='gemm' and x['workers']==8 and x['mode']=='rebuild' and x['control']=='stock' and x['candidate']=='pipeline' and x['metric']=='process' and 'triad' in x['control_key'] and x['scope']=='full'];assert len(a)==3
computed['CPU_GEMM_PROCESS']=summary(x['ratio'] for x in a)
ledger.append(dict(claim_id='CPU_GEMM_PROCESS',source_commit=BASE,source_json='paper/dac2027/statistics_expanded/statistics.json',source_sha256=inputs['paper/dac2027/statistics_expanded/statistics.json'],cohort='old_evidence/triad',case='gemm',scope='Process',comparison=['stock','pipeline'],statistic='mean_of_paired_ratios',n_process_pairs=3,rows=a,measurement_kind='measured',value=computed['CPU_GEMM_PROCESS'],table_figure='Abstract; Section V',limitations=['whole implementation comparison includes declared repairs','not a GPU speedup']))
# Include raw CPU measurements (with original binary/host/input bindings) in the data index.
selected={x.get('control_key') for x in a}|{x.get('candidate_key') for x in a}
for p in (R/'paper/dac2027/evidence').rglob('*.json'):
 if any(k and k in p.name for k in selected):read(str(p.relative_to(R)))
scale=[x for x in cpu['formal_runs'] if x['cohort']=='scale' and x['case'].lower().startswith(('bnn','dla'))]
ledger.append(dict(claim_id='CPU_SCALING_FIGURE',source_commit=BASE,source_json='paper/dac2027/statistics_expanded/statistics.json',cohort='scale / host B',scope='construction_only',rows=scale,measurement_kind='measured',table_figure='Fig. 2',limitations=['capped routing, not legal full flows','not paired to native GPU cohort']))
ledger.append(dict(claim_id='ALT_SEMANTICS_QOR',source_commit=BASE,source_json=S+'holdout_results.json',cohort='R6.2_P1_LSTM_qualification',scope='sample/map/QoR',measurement_kind='measured',rows=h['qualification'],map_differences=h['map_differences'],complete_pairs_equal=h['all_live_CPU_CUDA_pairs_equal'],table_figure='tab:qor',limitations=['route SHA differs between ALT CPU and CUDA','only each route retains identity during independent check','no universal QoR guarantee']))
for x in opt['paired_statistics']:
 a=sorted([v for v in opt['rows'] if v['case']==x['case'] and v['backend']=='alt_cuda' and not v['qualification_diagnostic']],key=lambda v:v['optimization_repeat'])
 b=sorted([v for v in opt['rows'] if v['case']==x['case'] and v['backend']=='alt_cuda_reserve' and not v['qualification_diagnostic']],key=lambda v:v['optimization_repeat'])
 st=summary(v[x['scope']]/w[x['scope']] for v,w in zip(a,b));assert len(a)==len(b)==3
 assert abs(st['mean']-x['paired']['mean'])<1e-12
 computed['OPT_'+x['case']+'_'+x['scope']]=st
ledger.append(dict(claim_id='CONVERSION_OPT',source_commit=BASE,source_json=S+'targeted_optimization_results.json',cohort='R6.2_P2 paired CUDA only',scope='E2/Process',rows=opt['rows'],paired_statistics=opt['paired_statistics'],measurement_kind='measured',table_figure='Section V discussion',limitations=['not compact','not qualified on LSTM','mixed Process direction','cannot multiply cohort speedups']))
ledger.append(dict(claim_id='FPGA_GATE',source_commit=BASE,source_json=S+'hardware_service_decision.json',scope='physical model / evidence availability',measurement_kind='model, not board measurement',fpga_superiority_verified=False,board_measured=False,status='UNRESOLVED_NO_SUPPORTED_MEMORY_EVIDENCE',table_figure='Section VI',limitations=['no frequency or calibrated random RMW service']))
# Generate the semantic/QoR table from qualification rows, not handwritten anchors.
q={x['backend']:x for x in h['qualification']};diff=next(x for x in h['map_differences'] if x['pair']=='alt_cpu_vs_flat')
assert q['alt_cpu']['route_sha256']!=q['alt_cuda']['route_sha256']
assert q['alt_cpu']['map_sha256']==q['alt_cuda']['map_sha256']
qrows=[('ALT CPU/CUDA complete samples','Equal' if h['all_live_CPU_CUDA_pairs_equal'] else 'Different'),
 ('ALT CPU/CUDA map ('+f"{diff['entries']:,}"+' entries)','Equal'),
 ('Delay / congestion / missing differences',f"{diff['delay_word_differences']} / {diff['congestion_word_differences']:,} / {diff['missing_state_differences']}"),
 ('ALT CPU/CUDA route SHA','Different'),('Independent FULL/STA; zero overuse','Pass' if all(x['qualified'] for x in q.values()) else 'Fail'),
 ('CPD: all five arms (ns)',str(q['stock']['metrics']['critical_path_ns'])),
 ('Wirelength: Stock / Flat',f"{q['stock']['metrics']['wirelength']:,} / {q['flat']['metrics']['wirelength']:,}"),
 ('Wirelength: ALT CPU / CUDA',f"{q['alt_cpu']['metrics']['wirelength']:,} / {q['alt_cuda']['metrics']['wirelength']:,}")]
(P/'tables/qor.tex').write_text('\n'.join(k+' & '+v+r'\\' for k,v in qrows)+'\n')
# Bind every plotted STRICT observation to its raw frozen measurement where present.
selected.update(x['key'] for x in scale)
raw_cpu=[]
for p in (R/'paper/dac2027/evidence').rglob('*.json'):
 if any(k and k in p.name for k in selected):
  rel=str(p.relative_to(R));read(rel);raw_cpu.append(dict(path=rel,sha256=inputs[rel]))
ledger[0]['statistics_policy']='paired arithmetic mean and sample SD; ddof=1'
ledger.append(dict(claim_id='CPU_RAW_INDEX',source_commit=BASE,raw_measurement_bindings=raw_cpu,cohort='CPU separate GEMM and scale',scope='raw record provenance including original host/binary/input fields',measurement_kind='measured'))
stage=read(S+'native_stage_attribution.json')
ledger.append(dict(claim_id='STAGE_ATTRIBUTION',source_commit=BASE,source_json=S+'native_stage_attribution.json',cohort='R6.1 repeat1 conditional bound; R6.2 one diagnostic profile separate',scope='within-process E1/E2/Process partitions',table_figure='Section V-D',measurement_kind='measured timers with derived conditional bounds',records=stage,limitations=['profile is not formal speedup','nested intervals not summed','conditional bound freezes all other work']))
b=next(v for v in stage['legacy_within_process'] if v['case']=='bnn' and v['repeat']==1)
macros += [r'\newcommand{\StageProcBound}{'+f"{b['Process_s']/(b['Process_s']-b['E1_s']):.6f}"+'}']
scale_source='paper/dac2027/evidence/expanded_20261105/results__native_paper_closure_20261105__scaling__summary.json'
scale_plan='paper/dac2027/evidence/expanded_20261105/results__native_paper_closure_20261105__scaling__plan.json'
ss=read(scale_source);sp=read(scale_plan);raw_by_key={v['key']:v for v in ss['measurements']}
for v in scale:assert raw_by_key[v['key']]['build_seconds']==v['build']
sc=next(x for x in ledger if x['claim_id']=='CPU_SCALING_FIGURE')
sc.update(source_json=scale_source,source_sha256=inputs[scale_source],worker_host=ss['hostname'],raw_rows=[raw_by_key[v['key']] for v in scale],plan=sp,plan_source=scale_plan)
gc=next(x for x in ledger if x['claim_id']=='CPU_GEMM_PROCESS')
raw={}
for v in raw_cpu:
 rr=read(v['path'])
 if rr.get('key') in {z['control_key'] for z in gc['rows']}|{z['candidate_key'] for z in gc['rows']}:raw[rr['key']]=rr
gc.update(raw_measurements=list(raw.values()),host_label='A (historical CPU cohort)',hostname='not recorded in these per-run measurement receipts')
(P/'tables/macros.tex').write_text('\n'.join(macros)+'\n')
(P/'claims_accel.json').write_text(json.dumps(ledger,indent=2)+'\n');(P/'computed_statistics.json').write_text(json.dumps(computed,indent=2)+'\n');(P/'data_bindings.json').write_text(json.dumps(dict(base_commit=BASE,inputs=inputs,CPU_formal=603,CPU_full=414,CPU_construction_only=189,R62_managed=43,R62_formal=33,R62_qualification=9,R62_profile=1,new_experiments=0),indent=2)+'\n')
print('Generated frozen tables, figures and',len(ledger),'claims')
