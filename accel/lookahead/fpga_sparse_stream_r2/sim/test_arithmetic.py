from pathlib import Path
import os,sys,json,hashlib,shutil,subprocess
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/rtl'/sys.argv[1];r.mkdir(exist_ok=False);f=r/'source';f.mkdir()
u=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr';env=os.environ.copy();env['VERILATOR_ROOT']=str(u/'share/verilator')
for p in [s/'rtl/fp32_positive.sv',s/'sim/arithmetic_driver.cpp']:shutil.copy2(p,f/p.name)
cmd=[str(u/'bin/verilator'),'--cc','--exe','--build','-j','4','--top-module','pair_lane','--Mdir',str(r/'build'),'-Wno-fatal','-O3','-CFLAGS','-O3 -std=c++17 -ffp-contract=off',str(f/'fp32_positive.sv'),str(f/'arithmetic_driver.cpp')]
with (r/'build.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env).returncode
if rc:raise SystemExit('compile failed '+str(r))
with (r/'run.log').open('w') as log:rc=subprocess.run([str(r/'build/Vpair_lane')],stdout=log,stderr=subprocess.STDOUT).returncode
(r/'receipt.json').write_text(json.dumps({'returncode':rc,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.iterdir()}},indent=2));print((r/'run.log').read_text());sys.exit(rc)
