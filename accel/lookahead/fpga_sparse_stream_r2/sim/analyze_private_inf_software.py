"""Analyze completed paired INF/control H100 runs and update conditional GPU budgets."""
from pathlib import Path
import hashlib,json,re,statistics,sys,fcntl
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';o=r/'software'/sys.argv[1]
assert json.loads((o/'completed.json').read_text())['status']=='complete'
groups={};receipts=list(o.glob('*.receipt.json'))
for p in receipts:assert json.loads(p.read_text())['returncode']==0
for p in sorted(o.glob('*.jsonl')):
 if not re.search(r'_p[0-2]$',p.stem):continue
 rows=[json.loads(x) for x in p.read_text().splitlines()];assert all(x['output_equal'] and x['scope']=='RESIDENT_COMPLETE_BATCH_V2' for x in rows)
 groups.setdefault(p.stem.rsplit('_p',1)[0],[]).extend(x['resident_s'] for x in rows if not x['warmup'])
assert len(groups)==24 and all(len(v)==9 for v in groups.values())
summary={'scope':'measured paired private-INF and unchanged prepared-POP CUDA/CPU on same H100 worker; full40 internal initialization/control counted; no FPGA measurement','cases':{k:{'n':len(v),'mean_s':statistics.mean(v),'sample_stdev_s':statistics.stdev(v),'raw_samples_s':v} for k,v in groups.items()},'all_receipts_pass':True,'receipt_count':len(receipts),'board_measured_FPGA':False}
budgets=[]
for case,old in [('bnn_export',.151799969444),('lstm_s2',.159888578444)]:
 values={kind:summary['cases'][case+'_'+kind]['mean_s'] for kind in ['basic','compact','control_basic','control_compact']};best=min(values.values());budgets.append({'case':case,'previous_prepared_POP_GPU_s':old,'new_same_worker_means':values,'best_new_variant':min(values,key=values.get),'comparison_GPU_seconds':min(old,best),'retains_stronger_historical_target':old<best,'budget200MHz_cycles':min(old,best)*2e8,'fpga_seconds':None,'board_measured':False})
summary['budgets']=budgets
lock=(o/'analysis.lock').open('a');fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
if (o/'summary.json').exists():assert json.loads((o/'summary.json').read_text())==summary,'conflicting existing software analysis'
else:
 with (o/'summary.json').open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
print(json.dumps(budgets,indent=2))
