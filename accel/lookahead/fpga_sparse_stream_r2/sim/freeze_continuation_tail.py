"""Append a verified, selected evidence snapshot; live observations stay timestamped."""
from pathlib import Path
import datetime,gzip,hashlib,json,sys
root=Path(__file__).resolve().parents[4]
r=root/'results/fpga_sparse_stream_r2_20261112'
out=r/'evidence_snapshot'/sys.argv[1]
out.mkdir(exist_ok=False)
roots=['accumulator/rtl_micro_two_waves_e','continuation_82860ce',
       'software/private_inf_submit_a','software/private_inf_local_a',
       'supervision/private_inf_gpu_watch','supervision/finalize_recovered_native_2150']
paths=set()
for name in roots:
 for p in (r/name).rglob('*'):
  if p.is_file() and 'build' not in p.relative_to(r/name).parts and p.suffix in {'.json','.jsonl','.csv','.log','.py','.cpp','.hpp','.sv','.md','.yaml','.txt'}:
   paths.add(p)
paths.update((r/'analysis').glob('wave_*.json'))
records=[]
for p in sorted(paths):
 raw=p.read_bytes();target=out/p.relative_to(r);target.parent.mkdir(parents=True,exist_ok=True)
 compressed=len(raw)>16384
 if compressed:target=target.with_name(target.name+'.gz')
 target.write_bytes(gzip.compress(raw,mtime=0) if compressed else raw)
 restored=gzip.decompress(target.read_bytes()) if compressed else target.read_bytes()
 assert restored==raw
 records.append({'raw_path':str(p.relative_to(r)),'raw_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'archive':str(target.relative_to(out))})
manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'Selected continuation tail after checkpoint2135; completed ninth RTL test, analyses and timestamped supervision observations. Running experiments are not complete results.',
 'roots':roots,'additional_glob':'analysis/wave_*.json','all_archived_bytes_verified':True,'files':records}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'files':len(records),'raw_bytes':sum(x['raw_bytes'] for x in records),'snapshot':str(out)}))
