from pathlib import Path
import json,statistics,sys,re
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';o=r/'software'/sys.argv[1];groups={};receipts=[]
for p in o.glob('*.receipt.json'):
 x=json.loads(p.read_text());assert x['returncode']==0;receipts.append(x)
for p in o.glob('*.jsonl'):
 if not re.search(r'_p[0-2]$',p.stem):continue
 rows=[json.loads(l) for l in p.read_text().splitlines()];assert all(x['output_equal'] for x in rows);k=p.stem.rsplit('_p',1)[0];groups.setdefault(k,[]).extend(x['resident_s'] for x in rows if not x['warmup'])
data={'scope':'RESIDENT_COMPLETE_BATCH_V2 measured software, exact native ALT output; same worker CPU vs GPU; mutable initialization and required host loop counted; external preparation/H2D/finalD2H excluded','cases':{k:{'n':len(v),'mean_s':statistics.mean(v),'sample_stdev_s':statistics.stdev(v),'raw_samples_s':v} for k,v in groups.items()},'all_receipts_pass':True,'receipt_count':len(receipts),'board_measured_FPGA':False}
assert len(groups)==12 and all(len(v)==9 for v in groups.values())
(o/'summary.json').write_text(json.dumps(data,indent=2));print(len(receipts),'PASS',len(groups),'cohorts')
