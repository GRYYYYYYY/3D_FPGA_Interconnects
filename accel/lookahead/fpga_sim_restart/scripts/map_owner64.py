#!/usr/bin/env python3
import pathlib,sys,json
src=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(exist_ok=True)
N=65536;owner=5;ops=[]
for row in (src/'stimulus.txt').read_text().splitlines():
 op,l,s,p=row.split();line=int(l,16)*64+owner if op=='0' else 0
 assert line<N
 ops.append(f'{op} {line:x} {s} {p}\n')
(out/'stimulus.txt').write_text(''.join(ops))
old=(src/'expected.hex').read_text().splitlines();inf='7f8000007f800000'*4;new=[]
for phase in range(2):
 a=[inf]*N
 for i,x in enumerate(old[phase*2048:(phase+1)*2048]):
  if i*64+owner<N:a[i*64+owner]=x
  else:assert x==inf
 new.extend(a)
(out/'expected.hex').write_text('\n'.join(new)+'\n')
(out/'mapping.json').write_text(json.dumps(dict(owner_count=64,owner=owner,owner_bits=6,N=N,scope='single owner address mapping, not 64-owner concurrency'),indent=2))
