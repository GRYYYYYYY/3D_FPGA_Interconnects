from pathlib import Path
import sys,json,subprocess,concurrent.futures
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';variant=sys.argv[1];rtl=sys.argv[2] if len(sys.argv)>2 else 'external_b';d=r/'model'/variant;out=d/(sys.argv[3] if len(sys.argv)>3 else 'suite_calibration');out.mkdir(exist_ok=False)
references=[]
for pattern in [f'{rtl}_native_l60/*/receipt.json',f'{rtl}_fixtures_l60/*/receipt.json',f'{rtl}_stress,stress_random_l120/*/receipt.json',f'{rtl}_external_nodes_65536,external_nodes_4194304_l60/*/receipt.json']:
 references.extend((r/'rtl').glob(pattern))
def run(receipt):
 ref=json.loads(receipt.read_text());old=receipt.parent;name=old.parent.name+'__'+old.name;o=out/name;o.mkdir();cmd=ref['command'].copy();cmd[0]=str(d/'model');cmd[4]=str(o)
 with (o/'console.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 exact=(o/'cycles.csv').read_bytes()==(old/'cycles.csv').read_bytes();outputs=(o/'output.bin').exists() and (o/'output.bin').read_bytes()==(old/'output.bin').read_bytes()
 result={'case':name,'command':cmd,'returncode':rc,'cycle_log_exact':exact,'outputs_exact':outputs,'reference':str(receipt)};(o/'receipt.json').write_text(json.dumps(result,indent=2));print(name,rc,exact,flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,references))
(out/'calibration.json').write_text(json.dumps({'scope':'complete topology identified by frozen model and referenced RTL receipts; latency/backpressure/capacity as receipts; no extrapolation','all_pass':all(x['returncode']==0 and x['cycle_log_exact'] and x['outputs_exact'] for x in results),'results':results},indent=2));sys.exit(not all(x['returncode']==0 and x['cycle_log_exact'] and x['outputs_exact'] for x in results))
