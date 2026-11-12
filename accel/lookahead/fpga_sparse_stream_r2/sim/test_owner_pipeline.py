from pathlib import Path
import os,json,hashlib,shutil,subprocess,sys
root=Path(__file__).resolve().parents[4];src=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/rtl'/sys.argv[1];r.mkdir(exist_ok=False)
u=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr';env=os.environ.copy();env['VERILATOR_ROOT']=str(u/'share/verilator')
frozen=r/'source';frozen.mkdir()
for p in [src/'rtl/owner_pipeline.sv',src/'rtl/sync_fifo.sv',src/'sim/owner_pipeline_driver.cpp']:shutil.copy2(p,frozen/p.name)
cmd=[str(u/'bin/verilator'),'--cc','--exe','--build','-j','4','--top-module','sparse_owner_pipe','--Mdir',str(r/'build'),'-Wno-fatal','-O3','-CFLAGS','-O3 -std=c++17',*map(str,frozen.glob('*.sv')),str(frozen/'owner_pipeline_driver.cpp')]
with (r/'build.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
results=[]
for mode in ['stress','warm']:
 cmd=[str(r/'build/Vsparse_owner_pipe'),str(r/f'{mode}_cycles.csv'),mode]
 with (r/f'{mode}.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 results.append({'mode':mode,'command':cmd,'returncode':p.returncode});print((r/f'{mode}.log').read_text(),flush=True)
(r/'receipt.json').write_text(json.dumps({'results':results,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen.iterdir()}},indent=2))
assert all(x['returncode']==0 for x in results)
