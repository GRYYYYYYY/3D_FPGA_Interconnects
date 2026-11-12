from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';variant=sys.argv[1];lat=sys.argv[2] if len(sys.argv)>2 else '60';exe=r/f'rtl/{variant}_build/Vsparse_tile';out=r/f'rtl/{variant}_fixtures_l{lat}';out.mkdir(exist_ok=False)
items=json.load(open(r/'semantics/native_fixtures/summary.json'))['results']
def run(x):
 p=r/'semantics/native_fixtures'/x['case'];d=out/x['case'];d.mkdir();cmd=[str(exe),str(p/'workload.bin'),str(p/'pop/prepared.bin'),str(p/'original_ALT.bin'),str(d),lat,'20261112','2']
 with (d/'console.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 result={'case':x['case'],'command':cmd,'returncode':rc}
 (d/'receipt.json').write_text(json.dumps(result,indent=2));print(x['case'],rc,flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,items))
(out/'summary.json').write_text(json.dumps({'all_pass':all(x['returncode']==0 for x in results),'tests':len(results),'results':results,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_binding':json.load(open(exe.parent/'source_binding.json'))},indent=2))
if not all(x['returncode']==0 for x in results):sys.exit(1)
