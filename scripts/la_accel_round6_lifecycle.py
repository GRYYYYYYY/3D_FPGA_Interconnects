"""Explicit failure/lifecycle contract; all files generated under the R6 root."""
import subprocess,struct,json,sys
from pathlib import Path
o=Path(sys.argv[1]);o.mkdir(exist_ok=False);exe=sys.argv[2]
def work(name,edges,costs,jobs,cells,golden=None):
 n=len(edges);e=sum(map(len,edges));nc=2;j=len(jobs);data=struct.pack('<7Q',0x31414c5443495254,n,e,j,len(costs),nc,1);row=[0]
 for x in edges:row.append(row[-1]+len(x))
 data+=struct.pack('<'+'Q'*(n+1),*row)
 for u in range(n):data+=struct.pack('<IIIi',1,min(u,len(costs)-1),1,-1)
 for ns in edges:
  for v in ns:data+=struct.pack('<II',v,0)
 for x in costs:data+=struct.pack('<ff',*x)
 for source in jobs:data+=struct.pack('<6I',source,0,0,0,0,0)
 data+=struct.pack('<'+'i'*len(cells),*cells);data+=(struct.pack('<II',0x7fc00000,0x7fc00000)*nc*j)
 p=o/(name+'.bin');p.write_bytes(data);return p
spec=[('zero_cycle',[[1],[0,2],[]],[(0,0)]*3,[0],[-1,-1,1],0,[]),('empty_targets',[[]],[(0,0)],[0],[-1],0,[]),('empty_batch',[[]],[(0,0)],[],[],0,[]),('unreachable',[[],[]],[(0,0)]*2,[0],[-1,1],0,[]),('overflow',[[1],[2],[]],[(0,0),(3e38,0),(3e38,0)],[0],[-1,-1,1],3,[]),('negative',[[1],[]],[(0,0),(-1,0)],[0],[-1,1],10,[]),('nan',[[1],[]],[(0,0),(float('nan'),0)],[0],[-1,1],10,[]),('subnormal',[[1],[]],[(0,0),(1e-40,0)],[0],[-1,1],10,[]),('member_capacity',[[1,2,3],[],[],[]],[(0,0)]*4,[0],[-1,-1,-1,1],1,['100','1']),('edge_budget',[[1],[2],[]],[(0,0)]*3,[0],[-1,-1,1],2,['1'])]
records=[]
for name,edges,costs,jobs,cells,expected,extra in spec:
 p=work(name,edges,costs,jobs,cells)
 for shift in [0,20]:
  out=o/f'{name}_s{shift}.out';cmd=[exe,str(p),str(shift),'1','1',str(out),'2']+extra;r=subprocess.run(cmd,capture_output=True,text=True,timeout=15);assert r.returncode==expected,(name,r.returncode,r.stdout,r.stderr)
  if expected:assert not out.exists()
  (o/f'{name}_s{shift}.log').write_text(r.stdout+r.stderr);records.append(dict(case=name,shift=shift,expected=expected,returncode=r.returncode,partial_map_published=expected!=0 and out.exists()))
# Truncated input rejection and repeated graph/cost changes use fresh immutable input on each invocation.
p=o/'truncated.bin';p.write_bytes(b'bad');r=subprocess.run([exe,str(p),'0','1','0',str(o/'truncated.out'),'0'],capture_output=True,text=True);assert r.returncode==10
records.append(dict(case='truncated',returncode=r.returncode));(o/'result.json').write_text(json.dumps(records,indent=2))
print(len(records),'lifecycle checks passed')
