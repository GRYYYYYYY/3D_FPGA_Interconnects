from pathlib import Path
import os,sys,json,hashlib,shutil,subprocess
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/rtl'/sys.argv[1];r.mkdir(exist_ok=False);f=r/'source';f.mkdir()
C=int(sys.argv[2]) if len(sys.argv)>2 else 33;P=int(sys.argv[3]) if len(sys.argv)>3 else 8
onehot=int(sys.argv[5]) if len(sys.argv)>5 else 0
assert onehot in [0,1]
u=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr';env=os.environ.copy();env['VERILATOR_ROOT']=str(u/'share/verilator')
for p in [s/'fabric_model.hpp',s/'owner_primitives_model.hpp',s/'rtl/shared_fabric.sv',s/'rtl/priority_tree.sv',s/'rtl/sync_fifo.sv',s/'sim/fabric_driver.cpp']:shutil.copy2(p,f/('owner_model.hpp' if p.name=='owner_primitives_model.hpp' else p.name))
p=f/'fabric_model.hpp';p.write_text(p.read_text().replace('../fpga_sparse_stream/owner_model.hpp','owner_model.hpp'))
cmd=[str(u/'bin/verilator'),'--cc','--exe','--build','-j','4','--top-module','r2_shared_fabric','--Mdir',str(r/'build'),'-Wno-fatal','-O3','-CFLAGS',f'-O3 -std=c++17 -DFABRIC_C={C} -DFABRIC_P={P}',f'-GC={C}',f'-GP={P}',f'-GDATA_ONEHOT={onehot}',*map(str,f.glob('*.sv')),str(f/'fabric_driver.cpp')]
(r/'build_command.json').write_text(json.dumps({'command':cmd,'DATA_ONEHOT':onehot},indent=2))
with (r/'build.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env).returncode
if rc:raise SystemExit('RTL compile failed '+str(r))
cmd=['g++','-DR2_REGISTERED_READY=1','-O3','-std=c++17','-DINDEPENDENT_MODEL',f'-DFABRIC_C={C}',f'-DFABRIC_P={P}',str(f/'fabric_driver.cpp'),'-o',str(r/'model')]
with (r/'model_build.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
for kind,exe in [('rtl',r/'build/Vr2_shared_fabric'),('model',r/'model')]:
 with (r/f'{kind}.log').open('w') as log:rc=subprocess.run([str(exe),str(r/f'{kind}_cycles.csv'),*(['fault'] if len(sys.argv)>4 and sys.argv[4]=='fault' else [])],stdout=log,stderr=subprocess.STDOUT).returncode
 print(kind,rc,(r/f'{kind}.log').read_text(),flush=True)
 if rc:raise SystemExit(rc)
same=(r/'rtl_cycles.csv').read_bytes()==(r/'model_cycles.csv').read_bytes();(r/'calibration.json').write_text(json.dumps({'scope':f'{C} logical clients,{P} shared physical ports,64 tags/port,OOO/backpressure; standalone','cycle_log_exact':same,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.iterdir()}},indent=2));print('cycle_log_exact',same);sys.exit(not same)
