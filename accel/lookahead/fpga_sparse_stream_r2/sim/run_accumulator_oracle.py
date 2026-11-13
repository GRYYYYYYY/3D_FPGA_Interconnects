"""Freeze and run functional private-INF/cache instrumentation; not hardware timing."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,subprocess,sys,time
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';s=root/'accel/lookahead/fpga_sparse_stream_r2'
tag=sys.argv[1];out=r/'accumulator'/tag;out.mkdir(exist_ok=False);f=out/'source';f.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[s/'wave_accumulator_reference.cpp',s/'wave_accumulator_profile.hpp',* (root/'accel/lookahead/include').glob('*.hpp'),*(root/'accel/lookahead/round6_1').glob('*.hpp')]
for p in files:(f/p.name).write_bytes(p.read_bytes())
cmd=['g++','-O3','-std=c++17','-ffp-contract=off','-DPROFILE_PRIVATE_INF=1','-I'+str(f),str(f/'wave_accumulator_reference.cpp'),'-o',str(out/'oracle')]
with (out/'build.log').open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
(out/'source_binding.json').write_text(json.dumps({'command':cmd,'returncode':rc,'source_sha256':{p.name:sha(f/p.name) for p in files}},indent=2)+'\n');assert rc==0
cases=json.loads((r/'semantics/native_complete.json').read_text())
def run(old):
 case=Path(old['command'][3]).name;d=out/case;d.mkdir();cmd=[str(out/'oracle'),*old['command'][1:3],str(d),*old['command'][4:]];t=time.time()
 with (d/'console.log').open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 v={'command':cmd,'returncode':rc,'wall_seconds':time.time()-t,'executable_sha256':sha(out/'oracle'),'output_exact':rc==0 and sha(d/'output.bin')==old['output_sha256'],'scope':'functional INF oracle and finite table instrumentation; not hardware cycles or timed CPU baseline'}
 (d/'receipt.json').write_text(json.dumps(v,indent=2)+'\n');assert v['output_exact'];return v
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,cases))
(out/'terminal.json').write_text(json.dumps({'all_pass':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':results},indent=2)+'\n');print('PRIVATE_INF_COMPLETE',flush=True)
