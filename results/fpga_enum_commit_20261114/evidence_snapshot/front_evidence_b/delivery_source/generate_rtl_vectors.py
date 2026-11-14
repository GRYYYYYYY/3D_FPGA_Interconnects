from pathlib import Path
import struct,json,hashlib
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114/front_rtl_a';R.mkdir(parents=True,exist_ok=False)
def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
def value(b):return struct.unpack('<f',struct.pack('<I',b))[0]
def pair(a,b):return bits(a)<<32|bits(b)
# Positive normals/+0, including near halfway round-to-even operands.
cost=[pair(0,0),pair(1,0.5),pair(2**-24,2**-23),pair(0.25,1),pair(3.5,0.75)]+[pair(2**(i-9),2**(i-11)) for i in range(5,16)]
parents=[];edge=[0]*8192;gold=[0]*8192;off=0
for q in range(2):
 for k in range(72):
  degree=[0,1,7,8,9,37,2,16,0,31,64,3][k%12];off=((off+15)//8)*8+(k%8);start=off;parent=pair(1+(k%7)*0.125,0 if k%11==0 else 0.5+(k%9)*0.25)
  for j in range(degree):
   idx=(k+j)%16;dst=off+1;edge[off]=(idx<<28)|dst
   gold[dst]=pair(value(parent>>32)+value(cost[idx]>>32),value(parent&0xffffffff)+value(cost[idx]&0xffffffff));off+=1
  parents.append({'node':q*72+k,'parent':parent,'begin':start,'end':off,'epoch':q+1})
assert off<8192
for name,rows,width in [('cost.hex',cost,16),('edge.hex',edge,8),('gold.hex',gold,16)]:
 (R/name).write_text(''.join(f'{x:0{width}x}\n' for x in rows))
(R/'parent.hex').write_text(''.join(f"{x['epoch']:04x}{x['node']:08x}{x['parent']:016x}{x['begin']:016x}{x['end']:016x}\n" for x in parents))
(R/'vectors.json').write_text(json.dumps({'parents':parents,'cost':cost,'candidate_count':sum(x['end']-x['begin'] for x in parents),'scope':'scaled allocation/tagged actual descriptor/FP32 contract, two continuous epochs; header/meta/pending outside DUT','memory_latency_cycles':16,'request_gap_cycles':1,'physical_port_count':1,'credit_limit':32,'response_capacity':1,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in R.glob('*.hex')}},indent=2))
print(R,'candidates',sum(x['end']-x['begin'] for x in parents))
