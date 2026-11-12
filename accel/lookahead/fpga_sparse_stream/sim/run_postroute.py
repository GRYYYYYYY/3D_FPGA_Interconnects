"""Audit the terminal routed checkpoint without modifying or rerouting it."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time

root=Path(__file__).resolve().parents[4]
ap=argparse.ArgumentParser();ap.add_argument('--wait',action='store_true');args=ap.parse_args()
out=root/'results/fpga_sparse_stream_20261112/tile_ooc_resident_batch'
while args.wait and not (out/'receipt.json').exists():time.sleep(10)
receipt=json.loads((out/'receipt.json').read_text())
assert receipt['returncode']==0,'implementation did not complete successfully'
assert not (out/'postroute_receipt.json').exists(),'retain previous audit; do not overwrite'
src=Path(__file__).with_name('postroute_audit.tcl');frozen=out/'source/postroute_audit.tcl'
shutil.copy2(src,frozen)
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
before=digest(out/'routed.dcp')
exe='/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado'
cmd=['taskset','-c','0-7',exe,'-mode','batch','-source',str(frozen),'-tclargs',str(out),'-log',str(out/'postroute_vivado.log'),'-journal',str(out/'postroute_vivado.jou')]
env=os.environ.copy();env['LD_PRELOAD']='/usr/lib/x86_64-linux-gnu/libudev.so.1'
print('POSTROUTE_START',flush=True)
with open(out/'postroute_console.log','w') as log:rc=subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,env=env).returncode
after=digest(out/'routed.dcp')
(out/'postroute_receipt.json').write_text(json.dumps({'command':cmd,'returncode':rc,'script_sha256':digest(frozen),'checkpoint_sha256_before':before,'checkpoint_sha256_after':after,'checkpoint_unchanged':before==after,'125MHz_scope':'same routed checkpoint constraint recheck; not new implementation or architecture performance'},indent=2)+'\n')
print('POSTROUTE_RETURN',rc,flush=True)
assert before==after,'audit modified checkpoint'
raise SystemExit(rc)
