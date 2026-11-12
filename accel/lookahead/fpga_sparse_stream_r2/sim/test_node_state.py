from pathlib import Path
import os,sys,json,hashlib,shutil,subprocess
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/large_state'/sys.argv[1];r.mkdir(exist_ok=False);f=r/'source';f.mkdir()
u=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr';env=os.environ.copy();env['VERILATOR_ROOT']=str(u/'share/verilator')
for p in [s/'rtl/node_state.sv',s/'rtl/sync_fifo.sv',s/'sim/node_state_driver.cpp']:shutil.copy2(p,f/p.name)
cmd=[str(u/'bin/verilator'),'--cc','--exe','--build','-j','4','--top-module','r2_node_state','--Mdir',str(r/'build'),'-Wno-fatal','-O3','-CFLAGS','-O3 -std=c++17',*map(str,f.glob('*.sv')),str(f/'node_state_driver.cpp')]
with (r/'build.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
if p.returncode:raise SystemExit('build failed: '+str(r))
cmd=[str(r/'build/Vr2_node_state'),str(r/'cycles.csv')]
with (r/'run.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
(r/'receipt.json').write_text(json.dumps({'scope':'standalone finite cache/backing RTL; not complete large graph kernel','address_space_nodes':4194304,'backing_bytes':67108864,'cache_bytes':4096,'command':cmd,'returncode':p.returncode,'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.iterdir()}},indent=2));print((r/'run.log').read_text());sys.exit(p.returncode)
