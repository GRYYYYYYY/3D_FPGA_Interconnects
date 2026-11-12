"""Independently replay the complete Q40 and exact/overflow capacity boundaries."""
from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, sys
root=Path(__file__).resolve().parents[4]
r=root/'results/fpga_sparse_stream_r2_20261112'
models=sys.argv[1].split(',');rtl=sys.argv[2]
references=[]
for case in ['max_node_max_cell_q40','partial_line_missing_q40']:
 d=r/'rtl'/f'{rtl}_batch_capacity'/case
 ref=json.loads((d/'receipt2.json').read_text())
 assert ref['returncode']==0
 references.append((case,ref['command'],d/'rtl',False))
for count in [8192,8193]:
 d=r/'rtl'/f'{rtl}_hot_capacity8192'/str(count)
 ref=json.loads((d/'receipt.json').read_text())
 assert ref['passed']
 references.append((f'hot_{count}',ref['results'][2]['command'],d/'rtl',count==8193))
for model in models:
 out=r/'model'/model/f'boundary_calibration_{rtl}';out.mkdir(exist_ok=False)
 def run(item):
  name,original,old,reject=item;d=out/name;d.mkdir();cmd=original.copy()
  cmd[0]=str(r/'model'/model/'model');cmd[4]=str(d)
  with (d/'console.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
  exact=(d/'cycles.csv').exists() and (d/'cycles.csv').read_bytes()==(old/'cycles.csv').read_bytes()
  if reject:
   text=(d/'console.log').read_text();passed=rc!=0 and 'DUT error' in text and 'bank=' in text and not (d/'output.bin').exists()
  else:
   passed=rc==0 and (d/'output.bin').read_bytes()==(old/'output.bin').read_bytes()
   a,b=[json.loads((p/'summary.json').read_text()) for p in [d,old]]
   for v in [a,b]:v.pop('scope',None)
   passed &= a==b
  result={'case':name,'command':cmd,'returncode':rc,'reference':str(old),'cycle_log_exact':exact,'expected_rejection':reject,'passed':bool(passed and exact)}
  (d/'receipt.json').write_text(json.dumps(result,indent=2));print(model,name,result['passed'],flush=True);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,references))
 passed=all(x['passed'] for x in results)
 (out/'calibration.json').write_text(json.dumps({'all_pass':passed,'results':results,'executable_sha256':hashlib.sha256((r/'model'/model/'model').read_bytes()).hexdigest()},indent=2))
 if not passed:raise RuntimeError('boundary calibration failed')
