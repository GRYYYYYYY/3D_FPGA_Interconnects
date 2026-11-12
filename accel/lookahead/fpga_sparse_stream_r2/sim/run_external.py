from pathlib import Path
import subprocess,json,sys,concurrent.futures
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';variant=sys.argv[1];lat=sys.argv[2] if len(sys.argv)>2 else '60';suite=sys.argv[3] if len(sys.argv)>3 else 'native';exe=r/f'rtl/{variant}_build/Vr2_external_tile';out=r/f'rtl/{variant}_{suite}_l{lat}';out.mkdir(exist_ok=False)
items=[]
if suite=='native':
 for x in json.loads((r/'semantics/native_complete.json').read_text())[:2]:
  c=x['command'];items.append((Path(c[3]).name,c[1],str(Path(c[3])/'prepared.bin'),c[2]))
elif suite=='fixtures':
 for x in json.loads((r/'semantics/native_fixtures/summary.json').read_text())['results']:
  d=r/'semantics/native_fixtures'/x['case'];items.append((x['case'],str(d/'workload.bin'),str(d/'pop/prepared.bin'),str(d/'original_ALT.bin')))
else:
 for name in suite.split(','):
  d=r/'semantics'/name;items.append((name,str(d/'workload.bin'),str(d/'pop/prepared.bin'),str(d/'original_ALT.bin')))
def run(x):
 name,w,p,g=x;d=out/name;d.mkdir();cmd=[str(exe),w,p,g,str(d),lat,'1729','2']
 with (d/'console.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 y={'name':name,'command':cmd,'returncode':rc};(d/'receipt.json').write_text(json.dumps(y,indent=2));print(name,rc,flush=True);return y
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:items=list(pool.map(run,items))
(out/'summary.json').write_text(json.dumps({'all_pass':all(x['returncode']==0 for x in items),'results':items},indent=2));sys.exit(not all(x['returncode']==0 for x in items))
