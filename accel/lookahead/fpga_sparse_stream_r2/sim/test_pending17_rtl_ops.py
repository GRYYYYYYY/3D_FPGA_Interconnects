from pathlib import Path
import sys,os,json,subprocess,hashlib
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';s=root/'accel/lookahead/fpga_sparse_stream_r2';d=r/'accumulator'/sys.argv[1];d.mkdir(exist_ok=False);src=d/'source';src.mkdir()
for p in [s/'rtl/pending17_service.sv',s/'pending17.hpp',s/'sim/pending17_rtl_ops.cpp']:(src/p.name).write_bytes(p.read_bytes())
text=(src/'pending17_service.sv').read_text();(src/'pending17_transform.sv').write_text(text[:text.index('endmodule')+len('endmodule')]+'\n')
u=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr';env=os.environ.copy();env['VERILATOR_ROOT']=str(u/'share/verilator')
cmd=[str(u/'bin/verilator'),'--cc','--exe','--build','-j','4','--top-module','pending17_transform','--Mdir',str(d/'build'),'-Wno-fatal','-CFLAGS','-O2 -std=c++17 -I'+str(src),str(src/'pending17_transform.sv'),str(src/'pending17_rtl_ops.cpp')]
with (d/'build.log').open('x') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env).returncode
(d/'binding.json').write_text(json.dumps({'command':cmd,'returncode':rc,'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in src.iterdir()}},indent=2));assert rc==0
with (d/'result.json').open('x') as f:rc=subprocess.run([str(d/'build/Vpending17_transform')],stdout=f,stderr=subprocess.STDOUT).returncode
assert rc==0;print('RTL_PENDING17_OPERATIONS_PASS')
