from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114/front_allocator_rtl_a';P=R/'project/allocator.sim/sim_1/behav/xsim'
def main():
 pointers=[0,0];grants=[0,0];lines=(P/'allocator_cycles.txt').read_text().splitlines()
 for raw in lines:
  x=raw.split();cy=int(x[0]);free,valid,nonempty=map(lambda x:int(x,16),x[1:4])
  for mode in range(2):
   actual_accept,actual_alloc,actual_ids=[int(v,16) for v in x[4+3*mode:7+3*mode]];mask=free;used=set();accept=alloc=ids=0
   for n in range(8):
    if not(valid>>n&1):break
    available=[i for i in range(256) if mask>>i&1 and i//32 not in used]
    if not available:break
    if mode:available.sort(key=lambda i:(((i//4-pointers[mode])%64),i%4))
    i=available[0];accept|=1<<n;ids|=i<<(8*n)
    if nonempty>>n&1:
     alloc|=1<<n;mask&=~(1<<i);used.add(i//32)
     if mode:pointers[mode]=(i//4+1)%64
   assert (accept,alloc,ids)==(actual_accept,actual_alloc,actual_ids),(cy,mode,'grant mismatch')
   grants[mode]+=alloc.bit_count()
 assert len(lines)==1024
 (R/'calibration.json').write_text(json.dumps({'all_pass':True,'cycles_checked':1024,'grants_first_free_lane_rr':grants,'trace_sha256':hashlib.sha256((P/'allocator_cycles.txt').read_bytes()).hexdigest(),'scope':'full64-lane/256context/8grant allocation-only global greedy selector with one write/group; exact cycle check, no physical timing qualification and not final independent-group policy'},indent=2));print('ALLOCATOR_CALIBRATION_PASS',len(lines),grants)
if __name__=='__main__':main()
