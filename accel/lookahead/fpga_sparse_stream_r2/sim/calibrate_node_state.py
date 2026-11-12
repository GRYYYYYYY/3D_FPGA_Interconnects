from pathlib import Path
import subprocess,sys,json,hashlib,shutil
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/large_state'/sys.argv[1];r.mkdir(exist_ok=False);f=r/'source';f.mkdir()
for p in [s/'node_state_model.hpp',s/'sim/node_state_driver.cpp',s.parent/'fpga_sparse_stream/owner_model.hpp']:shutil.copy2(p,f/p.name)
p=f/'node_state_model.hpp';p.write_text(p.read_text().replace('../fpga_sparse_stream/owner_model.hpp','owner_model.hpp'))
p=f/'node_state_driver.cpp';p.write_text(p.read_text().replace('#include "Vr2_node_state.h"\n#include "verilated.h"','#include "node_state_model.hpp"\nusing Vr2_node_state=r2_model::NodeStateCycle;').replace('Verilated::commandArgs(argc,argv);',''))
cmd=['g++','-O3','-std=c++17',str(p),'-o',str(r/'model')]
with (r/'build.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
if rc:raise SystemExit('compile failed '+str(r))
with (r/'run.log').open('w') as log:rc=subprocess.run([str(r/'model'),str(r/'cycles.csv')],stdout=log,stderr=subprocess.STDOUT).returncode
rtl=root/'results/fpga_sparse_stream_r2_20261112/large_state/node_state_b/cycles.csv';same=(r/'cycles.csv').read_bytes()==rtl.read_bytes()
(r/'calibration.json').write_text(json.dumps({'scope':'standalone node-state finite-cache service only','returncode':rc,'cycle_log_exact':same,'RTL_reference':str(rtl),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.iterdir()}},indent=2));print((r/'run.log').read_text(),same);sys.exit(rc or not same)
