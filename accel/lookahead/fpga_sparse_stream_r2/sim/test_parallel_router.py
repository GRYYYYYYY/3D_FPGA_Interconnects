from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
root=Path(__file__).resolve().parents[4]
s=root/'accel/lookahead/fpga_sparse_stream_r2'
r=root/'results/fpga_sparse_stream_r2_20261112/rtl'/sys.argv[1]
r.mkdir(exist_ok=False)
files=[s/'rtl/priority_tree.sv',s/'rtl/sync_fifo.sv',s/'rtl/parallel_router.sv',
       s/'sim/parallel_router_legacy.sv',s/'sim/parallel_router_tb.sv']
for p in files:shutil.copy2(p,r/p.name)
bin=root.parent.parent/'Xilinx/Vivado/2022.2/bin'
env=os.environ.copy();env['LD_PRELOAD']='/usr/lib/x86_64-linux-gnu/libudev.so.1'
commands=[[str(bin/'xvlog'),'--sv',*[p.name for p in files]],
          [str(bin/'xelab'),'parallel_router_tb','-s','router'],
          [str(bin/'xsim'),'router','-runall']]
receipts=[]
for i,cmd in enumerate(commands):
 with (r/f'stage{i}.log').open('w') as log:rc=subprocess.run(cmd,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 receipts.append({'command':cmd,'returncode':rc})
 if rc:break
passed=len(receipts)==3 and all(x['returncode']==0 for x in receipts) and 'PARALLEL_ROUTER_PASS all4_complete_streams' in (r/'stage2.log').read_text()
(r/'receipt.json').write_text(json.dumps({'all_pass':passed,'scope':'four8/32 candidate and cell routers, legacy full-cycle differential plus independent bounded FIFO/order/serial-arbitration scoreboard, reset under load, saturation/drain','results':receipts,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
print('PARALLEL_ROUTER',passed);sys.exit(not passed)
