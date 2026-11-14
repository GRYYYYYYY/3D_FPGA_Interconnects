from pathlib import Path
import struct,random,json,hashlib,sys
R=Path(sys.argv[1]);R.mkdir(parents=True,exist_ok=True)
def f(x):return struct.unpack('<f',struct.pack('<I',x))[0]
def bits(x):
 try:return struct.unpack('<I',struct.pack('<f',x))[0]
 except OverflowError:return 0x7f800000
def legal(x):return x==0 or (x>>31==0 and 0<(x>>23&255)<255)
r=random.Random(873421)
bound=[0,1,0x7fffff,0x800000,0x800001,0xffffff,0x1000000,0x33800000,0x34000000,0x3f7fffff,0x3f800000,0x3f800001,0x3fffffff,0x40000000,0x7f000000,0x7f7fffff,0x7f800000,0x7fc00000,0x80000000,0xbf800000]
rows=[]
for a in bound:
 for b in bound:
  good=legal(a) and legal(b)
  c=bits(f(a)+f(b)) if good else 0
  rows.append((a,b,c,int(not good or c==0x7f800000),int(good)))
for i in range(4000):
 a=(r.randrange(1,255)<<23)|r.randrange(1<<23);b=(r.randrange(1,255)<<23)|r.randrange(1<<23);c=bits(f(a)+f(b));rows.append((a,b,c,int(c==0x7f800000),1))
(R/'arith.hex').write_text(''.join(f'{good:01x}{bad:01x}{c:08x}{b:08x}{a:08x}\n' for a,b,c,bad,good in rows))
(R/'arith_meta.json').write_text(json.dumps({'count':len(rows),'seed':873421,'oracle':'Python binary64 sum of binary32 operands, correctly rounded to binary32; sufficient precision for positive FP32 add; invalid result unchecked but error required','sha256':hashlib.sha256((R/'arith.hex').read_bytes()).hexdigest()},indent=2))
