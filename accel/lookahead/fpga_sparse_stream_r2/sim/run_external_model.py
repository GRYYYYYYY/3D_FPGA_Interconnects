from pathlib import Path
import sys,json,subprocess,concurrent.futures
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';variant=sys.argv[1];rtl=sys.argv[2] if len(sys.argv)>2 else 'external_b';d=r/'model'/variant;out=d/'native_l60';out.mkdir(exist_ok=False)
items=json.loads((r/'semantics/native_complete.json').read_text())[:2]
def run(x):
 c=x['command'];name=Path(c[3]).name;o=out/name;o.mkdir();cmd=[str(d/'model'),c[1],str(Path(c[3])/'prepared.bin'),c[2],str(o),'60','1729','2']
 with (o/'console.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 old=r/f'rtl/{rtl}_native_l60'/name;cycles=(o/'cycles.csv').read_bytes();ref=(old/'cycles.csv').read_bytes();result={'case':name,'returncode':rc,'command':cmd,'cycle_log_exact':cycles==ref,'reference':str(old)}
 (o/'receipt.json').write_text(json.dumps(result,indent=2));print(result,(o/'console.log').read_text()[-500:],flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,items))
(out/'calibration.json').write_text(json.dumps(results,indent=2));sys.exit(any(x['returncode'] or not x['cycle_log_exact'] for x in results))
