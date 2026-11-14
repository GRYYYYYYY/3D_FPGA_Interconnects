#!/usr/bin/env python3
"""Read-only unique-receipt, full-output and whole-batch aggregation audit."""
from pathlib import Path
from collections import Counter
import json,csv,hashlib,datetime
R=Path('results/fpga_descriptor_front_20261114/model_d')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
binding=json.loads((R/'binding.json').read_text());unique={};duplicates=0
terms=['small_C0F1F2F3_terminal.json','representative_C0F1F2F3_terminal.json','full_C0F2_terminal.json']
for name in terms:
 t=json.loads((R/name).read_text());assert t['all_pass']
 for r in t['results']:
  k=(r['configuration'],r['case'],r['sample'],r['jitter'])
  if k in unique:
   duplicates+=1
   for f in ['binary_sha256','workload_sha256','golden_sha256','output_path','output_sha256','finite_path']:assert r[f]==unique[k][f],(k,f)
  unique[k]=r
assert len(unique)==334 and duplicates==14
for name,inp in binding['inputs'].items():
 assert sha(inp['workload'])==inp['workload_sha256'],name
 assert sha(inp['golden'])==inp['golden_sha256'],name
full=json.loads((R/'full_C0F2_terminal.json').read_text());batches=[];maxpop=(0,None)
for conf in ['C0','F2']:
 for case in ['bnn_export','lstm_s2']:
  rows=sorted([r for r in full['results'] if r['configuration']==conf and r['case']==case],key=lambda r:r['sample'])
  assert [r['sample'] for r in rows]==list(range(40)) and not any(r['jitter'] for r in rows)
  output=R/f'{conf}_{case}_output.bin';gold=Path(binding['inputs'][case]['golden']);joined=b''.join(Path(r['output_path']).read_bytes() for r in rows)
  assert output.read_bytes()==joined==gold.read_bytes()
  summary=json.loads((R/f'{conf}_{case}_summary.json').read_text());phases=Counter();counts=Counter();traffic=[[0]*32 for _ in range(12)];tail=[0]*8;bank_selection=Counter();lanehist=[0]*65;token_cycles=0;maxdir=maxspill=peakack=0;empty_final_waves=0
  for r in rows:
   f=json.loads(Path(r['finite_path']).read_text());phases.update(f['phase_cycles']);counts.update({k:f[k] for k in summary['counts']})
   for i in range(12):
    for p in range(32):traffic[i][p]+=f['traffic'][i][p]
   waves=[{k:int(v) for k,v in x.items()} for x in csv.DictReader(Path(r['finite_path']).with_name('waves.csv').open())]
   assert len(waves)==len(f['critical_final_bank_observers'])==f['waves']
   for w,ob in zip(waves,f['critical_final_bank_observers']):
    assert w['wave']==ob['wave'] and w['sample']==r['sample']
    assert sum(ob['exclusive_histogram'])==w['final_end']-w['pop_expand_end']
    if ob['last_busy_cycle']==0:
     assert w['candidates']==w['commits']==w['spills']==w['merges']==0 and ob['bank']==0 and not any(ob['exclusive_histogram'][:6])
     empty_final_waves+=1
    else:assert w['pop_expand_end']<=ob['last_busy_cycle']<w['final_end']-256
    assert ob['exclusive_histogram'][7]==256
    for i,n in enumerate(ob['exclusive_histogram']):tail[i]+=n
    bank_selection[ob['bank']]+=1
   assert sum(w['pop_expand_end']-w['start'] for w in waves)==f['phase_cycles']['pop_expand']
   assert sum(w['final_end']-w['pop_expand_end'] for w in waves)==f['phase_cycles']['finalize']
   for i,n in enumerate(f['emit_population_histogram']):lanehist[i]+=n
   token_cycles+=sum(sum(i*n for i,n in enumerate(g['occupancy_histograms'][0])) for g in f['group_stats'])
   maxdir=max(maxdir,max(f['directory_bank_peaks']));maxspill=max(maxspill,max(b['spill_id_peak'] for b in f['bank_stats']));peakack=max(peakack,f['output_ACK_peak_per_cycle'])
   assert summary['per_sample_cycles'][str(r['sample'])]==f['cycles']
   if f['pop_transactions']>maxpop[0]:maxpop=(f['pop_transactions'],[conf,case,r['sample']])
  assert dict(phases)==summary['phase_cycles'] and dict(counts)==summary['counts'] and traffic==summary['traffic']
  cycles=sum(phases.values());assert cycles==summary['conditional_cycles'] and summary['conditional_seconds']==cycles/summary['conditional_frequency_hz']
  assert summary['conditional_frequency_hz']==200000000 and summary['estimated_seconds_at_qualified_clock'] is None
  assert summary['complete_kernel_clock_qualified'] is False and summary['board_measured'] is False
  assert sha(output)==summary['full_output_sha256']==summary['golden_sha256']
  assert maxdir==summary['directory_peak_per_bank'] and maxspill==summary['spill_id_peak_per_bank']
  assert sum(tail)==phases['finalize'] and sum(i*n for i,n in enumerate(lanehist))==counts['candidates']
  batches.append({'configuration':conf,'case':case,'samples':40,'cycles':cycles,'phase_cycles':dict(phases),'critical_selected_bank_exclusive_histogram':tail,'critical_selected_bank_count':dict(bank_selection),'mean_front_token_lifetime_observed':token_cycles/counts['pop_transactions'],'mean_candidates_per_pop_expand_cycle':counts['candidates']/phases['pop_expand'],'output_sha256':sha(output),'max_directory':maxdir,'max_spill_ids':maxspill,'ACK_peak':peakack,'empty_final_waves_with_default_bank0':empty_final_waves})
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_334_UNIQUE_D_AND_4_FULL_BATCH_OUTPUTS','unique_receipts':len(unique),'duplicate_references_identical':duplicates,'actual_workload_and_golden_hashes_checked':len(binding['inputs']),'full_output_count':4,'batches':batches,'max_fullbatch_POP_observed':maxpop,'observer_limits':'Critical bank chosen after run by last active cycle; labels exclusive and wall-conserving but priority-coded state occupancy, not causal stall attribution or predicted speedup. Init/export included in cycle totals.','terminal_sha256':{p:sha(R/p) for p in terms},'new_simulations':0}
p=Path('results/fpga_descriptor_front_20261114/review/model_d_unique_full_batch_audit.json');assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(result['status']);print(json.dumps([{k:v for k,v in b.items() if k!='critical_selected_bank_count'} for b in batches],indent=2))
