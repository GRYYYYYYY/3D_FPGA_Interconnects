from pathlib import Path
import json,subprocess,concurrent.futures,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';v=sys.argv[1]
def run(name):
 d=r/'semantics'/name;out=r/'rtl'/f'{v}_{name}';out.mkdir(exist_ok=False)
 cmds=[]
 if not (d/'original_ALT.bin').exists():cmds.append([str(r/'semantics/original_ALT'),str(d/'workload.bin'),str(d/'original_ALT.bin')])
 if not (d/'pop/prepared.bin').exists():cmds.append([str(r/'semantics/reference_pop_reduce'),str(d/'workload.bin'),str(d/'original_ALT.bin'),str(d/'pop'),'524288','524288'])
 cmds.append([str(r/f'rtl/{v}_build/Vsparse_tile'),str(d/'workload.bin'),str(d/'pop/prepared.bin'),str(d/'original_ALT.bin'),str(out),'120','20261112','2'])
 results=[]
 for i,cmd in enumerate(cmds):
  with (out/f'run{i}.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  results.append({'command':cmd,'returncode':p.returncode})
  if p.returncode:break
 (out/'receipt.json').write_text(json.dumps(results,indent=2));print(name,p.returncode,flush=True);return p.returncode
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:assert not any(pool.map(run,['stress','stress_random']))
