from pathlib import Path
import os,sys,json,hashlib,shutil,subprocess
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/rtl'/(sys.argv[1]+'_build');r.mkdir(exist_ok=False);f=r/'source';f.mkdir()
u=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr';env=os.environ.copy();env['VERILATOR_ROOT']=str(u/'share/verilator')
for p in [*s.glob('rtl/*.sv'),s/'sim/external_tile_driver.cpp']:shutil.copy2(p,f/p.name)
cmd=[str(u/'bin/verilator'),'--cc','--exe','--build','-j','4','--top-module','r2_external_tile','--Mdir',str(r),'-Wno-fatal','-O3','-CFLAGS',f'-O3 -std=c++17 -I{root}/accel/lookahead/include',*sys.argv[2:],*map(str,f.glob('*.sv')),str(f/'external_tile_driver.cpp')]
(r/'source_binding.json').write_text(json.dumps({'command':cmd,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.iterdir()}},indent=2))
with (r/'build.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
print('BUILD',p.returncode,r);sys.exit(p.returncode)
