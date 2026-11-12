"""Reproduce the bounded owner/changed composition regression in a new run dir."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys

root=Path(__file__).resolve().parents[4]
src=root/'accel/lookahead/fpga_sparse_stream_r2'
old=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr'
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'results/fpga_sparse_stream_r2_20261112/rtl/owner_changed_pipe_a'
out.mkdir(parents=True,exist_ok=False)
frozen=out/'source';frozen.mkdir()
files=[src/'rtl'/n for n in ['owner_pipeline.sv','sync_fifo.sv','changed_pipeline.sv']]
files += [src/'sim'/n for n in ['owner_changed_tb.sv','owner_changed_driver.cpp']]
for p in files:shutil.copy2(p,frozen/p.name)
env=os.environ.copy();env.setdefault('VERILATOR_ROOT',str(old/'share/verilator'))
cmd=[env.get('SPARSE_VERILATOR',str(old/'bin/verilator')),'--cc','--exe','--build','-j','4','--top-module','owner_changed_tb','--Mdir',str(out/'build'),'-Wno-fatal','-O3','-CFLAGS','-O3 -std=c++17',*[str(frozen/p.name) for p in files]]
run=[str(out/'build/Vowner_changed_tb'),str(out/'cycles.csv')]
with open(out/'build.log','w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env).returncode
if rc==0:
 with open(out/'run.log','w') as log:rc=subprocess.run(run,stdout=log,stderr=subprocess.STDOUT,env=env).returncode
passed=rc==0 and 'OWNER_CHANGED_PASS' in (out/'run.log').read_text()
(out/'receipt.json').write_text(json.dumps({'build_command':cmd,'run_command':run,'returncode':rc,'explicit_pass':passed,'source_sha256':{p.name:hashlib.sha256((frozen/p.name).read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
if not passed:raise SystemExit('owner/changed regression failed; see '+str(out))
print((out/'run.log').read_text(),end='')
