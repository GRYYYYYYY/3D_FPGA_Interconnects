"""Analyze completed paired INF/control H100 runs and update conditional GPU budgets."""
from pathlib import Path
import hashlib,json,re,statistics,sys,fcntl
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';o=r/'software'/sys.argv[1]
assert json.loads((o/'completed.json').read_text())['status']=='complete'
groups={};process_means={};receipts=list(o.glob('*.receipt.json'))
assert len(receipts)==254,'expected 182 fixture and 72 native receipts'
for p in receipts:assert json.loads(p.read_text())['returncode']==0
for p in sorted(o.glob('*.jsonl')):
 if not re.search(r'_p[0-2]$',p.stem):continue
 rows=[json.loads(x) for x in p.read_text().splitlines()];assert all(x['output_equal'] and x['scope']=='RESIDENT_COMPLETE_BATCH_V2' for x in rows)
 assert len(rows)==4 and sum(bool(x['warmup']) for x in rows)==1
 key=p.stem.rsplit('_p',1)[0];samples=[x['resident_s'] for x in rows if not x['warmup']]
 groups.setdefault(key,[]).extend(samples)
 process_means.setdefault(key,{})[p.stem.rsplit('_p',1)[1]]=statistics.mean(samples)
assert len(groups)==24 and all(len(v)==9 for v in groups.values())
summary={'scope':'measured paired private-INF and unchanged prepared-POP CUDA/CPU on same H100 worker; full40 internal initialization/control counted; no FPGA measurement','cases':{k:{'n':len(v),'mean_s':statistics.mean(v),'sample_stdev_s':statistics.stdev(v),'raw_samples_s':v} for k,v in groups.items()},'all_receipts_pass':True,'receipt_count':len(receipts),'board_measured_FPGA':False}
budgets=[]
for case,old in [('bnn_export',.151799969444),('lstm_s2',.159888578444)]:
 values={kind:summary['cases'][case+'_'+kind]['mean_s'] for kind in ['basic','compact','control_basic','control_compact']};best=min(values.values());budgets.append({'case':case,'previous_prepared_POP_GPU_s':old,'new_same_worker_means':values,'best_new_variant':min(values,key=values.get),'comparison_GPU_seconds':min(old,best),'retains_stronger_historical_target':old<best,'budget200MHz_cycles':min(old,best)*2e8,'fpga_seconds':None,'board_measured':False})
summary['budgets']=budgets
summary['process_means_s']=process_means
summary['paired_process_ratios_INF_over_control']={}
for key,means in process_means.items():
 if '_control_' in key:continue
 case,kind=key.rsplit('_',1);control=process_means[case+'_control_'+kind]
 summary['paired_process_ratios_INF_over_control'][key]={p:means[p]/control[p] for p in sorted(means)}
lock=(o/'analysis.lock').open('a');fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
if (o/'summary.json').exists():assert json.loads((o/'summary.json').read_text())==summary,'conflicting existing software analysis'
else:
 with (o/'summary.json').open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
print(json.dumps(budgets,indent=2))

# Append a new comparison view; never rewrite historical experiments/budgets.
updates=[]
for budget in budgets:
 case=budget['case'];target=budget['comparison_GPU_seconds']
 for path in sorted((r/'accumulator').glob('inf_finite_native_*/'+case+'/finite_service.json')):
  receipt=path.with_name('receipt.json')
  if not receipt.exists():continue
  qualified=json.loads(receipt.read_text())
  if qualified['returncode'] or not qualified['output_exact']:continue
  model=json.loads(path.read_text());cycles=model['cycles'];freq=model['assumed_MHz']
  updates.append({'case':case,'source':str(path.relative_to(r)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'qualified_software_target_s':target,'conditional_model_s':cycles/(freq*1e6),'fails_necessary_budget_for_this_schedule':cycles>target*freq*1e6,'fpga_seconds':None,'board_measured':False,'scope':model['scope']})
old=r/'analysis/wave_accumulator_bounded_a.json'
if old.exists():
 for row in json.loads(old.read_text())['rows']:
  target=next(x['comparison_GPU_seconds'] for x in budgets if x['case']==row['case'])
  updates.append({'case':row['case'],'historical_layout':row['layout'],'ports':row['physical_ports'],'gap_cycles':row['gap_cycles'],'assumed_frequency_MHz':row['assumed_frequency_MHz'],'qualified_software_target_s':target,'conditional_lower_bound_s':row['conditional_seconds_lower_bound'],'fails_necessary_budget':row['conditional_seconds_lower_bound']>target,'fpga_seconds':None,'board_measured':False})
derived=r/'inf_followup_5af9908/review_bundle/FPGA_INF_Followup_5af9908/derived_layout_screen.json'
if derived.exists():
 for row in json.loads(derived.read_text())['rows']:
  target=next(x['comparison_GPU_seconds'] for x in budgets if x['case']==row['case'])
  cycles=row.get('phase_bound_plus_init_and_bitmap_cycles',row['limited_phase_bound_cycles'])
  updates.append({'case':row['case'],'historical_layout':row['layout'],'source':str(derived.relative_to(r)),'source_sha256':hashlib.sha256(derived.read_bytes()).hexdigest(),'gap_cycles':row['gap_cycles'],'assumed_frequency_MHz':200,'qualified_software_target_s':target,'partial_bound_s':cycles/2e8,'remaining_budget_s':target-cycles/2e8,'scope':'partial arithmetic bound only; omits actual frontend/controller/RAW/ACK; not FPGA prediction','fpga_seconds':None,'board_measured':False})
# Content-address each comparison view so independently finishing model evidence
# can add a later view without invalidating the earlier software measurement.
value={'scope':'comparison update only; retains stronger historical target; no historical result rewritten','rows':updates}
raw=(json.dumps(value,indent=2)+'\n').encode();digest=hashlib.sha256(raw).hexdigest()
new=o/('architecture_budget_update_'+digest[:16]+'.json')
if new.exists():assert new.read_bytes()==raw
else:
 with new.open('xb') as f:f.write(raw)
