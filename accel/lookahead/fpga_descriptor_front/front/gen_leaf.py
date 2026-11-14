from pathlib import Path
import sys,struct,json,hashlib
R=Path(sys.argv[1]);R.mkdir(parents=True,exist_ok=True)
def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
def fp(b):return struct.unpack('<f',struct.pack('<I',b))[0]
def pair(a,b):return bits(a)<<32|bits(b)
cost=[pair(0,0),pair(1,.5),pair(2**-24,2**-23),pair(.25,1),pair(3.5,.75)]+[pair(2**(i-9),2**(i-11)) for i in range(5,16)]
parents=[];edges=[0]*16384;gold=[0]*16384;desc8=[];desc16=[];off=0;counts={'candidate':0,'target':0,'stale':0,'parents':128}
for k in range(128):
 stale=k%17==5;degree=[0,1,7,8,9,37,2,16,0,31,64,3][k%12];valid=k%3!=1;cell=k%8 if valid else 0
 off=((off+15)//8)*8+k%8;begin=off;end=begin+degree;p=pair(1+k%7*.125,0 if k%11==0 else .5+k%9*.25)
 if k==63:begin=0xfffffff8;end=0xffffffff;degree=7
 for j in range(degree):
  dst=(off+j+1) if k!=63 else 16000+j;idx=(k+j)%16;edge=(idx<<28)|dst
  if k!=63:edges[off+j]=edge
  else:edges[16376+j]=edge
  if not stale:
   gold[dst]=pair(fp(p>>32)+fp(cost[idx]>>32),fp(p&0xffffffff)+fp(cost[idx]&0xffffffff));counts['candidate']+=1
 off+=degree
 desc8.append(begin|degree<<32|cell<<48|int(valid)<<63)
 desc16.append(begin|end<<32|cell<<64|int(valid)<<96)
 parents.append((int(stale),p))
 counts['target']+=int(valid and not stale);counts['stale']+=int(stale)
assert off<16000
for name,rows,width in [('cost.hex',cost,16),('edge.hex',edges,8),('gold.hex',gold,16),('desc8.hex',desc8,16),('desc16.hex',desc16,32),('parent.hex',[(st<<64)|p for st,p in parents],17)]:
 (R/name).write_text(''.join(f'{x:0{width}x}\n' for x in rows))
counts['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in R.glob('*.hex')};(R/'leaf_meta.json').write_text(json.dumps(counts,indent=2));print(counts)
