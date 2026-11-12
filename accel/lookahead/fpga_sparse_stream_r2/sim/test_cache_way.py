from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
root=Path(__file__).resolve().parents[4]
s=root/'accel/lookahead/fpga_sparse_stream_r2'
r=root/'results/fpga_sparse_stream_r2_20261112/rtl'/sys.argv[1]
r.mkdir(exist_ok=False)
files=[s/'rtl/priority_tree.sv',s/'sim/cache_way_tb.sv']
for p in files:shutil.copy2(p,r/p.name)
bin=root.parent.parent/'Xilinx/Vivado/2022.2/bin'
env=os.environ.copy();env['LD_PRELOAD']='/usr/lib/x86_64-linux-gnu/libudev.so.1'
commands=[[str(bin/'xvlog'),'--sv','priority_tree.sv','cache_way_tb.sv'],
          [str(bin/'xelab'),'cache_way_tb','-s','cache_way'],
          [str(bin/'xsim'),'cache_way','-runall']]
receipts=[]
for i,cmd in enumerate(commands):
 with (r/f'stage{i}.log').open('w') as log:rc=subprocess.run(cmd,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 receipts.append({'command':cmd,'returncode':rc})
 if rc:break
passed=len(receipts)==3 and all(x['returncode']==0 for x in receipts) and 'CACHE_WAY_PASS' in (r/'stage2.log').read_text()
(r/'receipt.json').write_text(json.dumps({'all_pass':passed,'results':receipts,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2))
print('CACHE_WAY',passed);sys.exit(not passed)
