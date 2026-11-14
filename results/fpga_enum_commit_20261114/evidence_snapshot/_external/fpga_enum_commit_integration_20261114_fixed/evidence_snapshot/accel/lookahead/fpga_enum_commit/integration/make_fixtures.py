from pathlib import Path
import json,struct,hashlib
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_integration_20261114_a';OUT=R/'fixtures';INF=0x7f8000007f800000

def main():
 OUT.mkdir(exist_ok=False);rows=[]
 def write(name,events,before,after,repetitions=1,source=None):
  banks=[[e for e in events if (e[0]>>7)&1==b] for b in [0,1]]
  for b,es in enumerate(banks):(OUT/(name+f'_edge{b}.hex')).write_text(''.join(f'{n:08x}{p:016x}\n' for n,p in es))
  for mode,values in [('before',before),('after',after)]:
   (OUT/(name+'_'+mode+'.hex')).write_text(''.join(f'@{line>>5:08x}\n'+''.join(f'{p:016x}' for p in reversed(pair))+'\n' for line,pair in sorted(values.items())))
  rows.append({'name':name,'edges':[len(x) for x in banks],'lines':len(after),'waves':repetitions,'source':source})
 for rec in json.loads((ROOT/'results/fpga_enum_commit_20261114/native_projection_b/manifest.json').read_text()):
  p=ROOT/rec['path'];data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==rec['sha256'];h=struct.unpack_from('<6Q',data);off=48;edges=[]
  for _ in range(h[4]):edges.append(struct.unpack_from('<IQ',data,off));off+=12
  before={};after={}
  for _ in range(h[5]):
   l,mask,*v=struct.unpack_from('<II8Q',data,off);off+=72;before[l]=v[:4];after[l]=v[4:]
  assert off==len(data);write(p.stem,edges,before,after,source=rec)
 for name,kind in [('resident_two_waves','resident'),('hot_set_word','hot'),('bitmap_shared_word','bitmap')]:
  events=[]
  if kind=='resident':
   for q in range(128):
    for b in range(2):
     for sec in range(4):events.append((q*256+b*128+sec,0x3f80000040000000+(q%7)*0x100000001+sec))
  elif kind=='hot':
   for i in range(2048):
    q=(i%12)*1024
    for b in range(2):events.append((q*256+b*128+i%4,0x3f80000040000000+((2047-i)%256)*0x100000001))
  else:
   for q in range(64):
    for b in range(2):
     for sec in range(4):events.append((q*256+b*128+sec,0x3f80000040000000+q+sec))
  before={n//4:[INF]*4 for n,p in events};after={l:v.copy() for l,v in before.items()}
  for n,p in events:after[n//4][n%4]=min(after[n//4][n%4],p)
  write(name,events,before,after,2)
 (OUT/'cases.txt').write_text(''.join(f"{x['name']} {x['edges'][0]} {x['edges'][1]} {x['lines']} {x['waves']}\n" for x in rows))
 (OUT/'manifest.json').write_text(json.dumps({'cases':rows,'scope':'native canonical prestate, freshly cleared PV; no hidden pending RAM injection','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file()}},indent=2))
 print('FIXTURES',len(rows))
if __name__=='__main__':main()
