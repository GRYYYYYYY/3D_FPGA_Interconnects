"""Native ALT fixtures including eligibility, qid remapping and numeric rejection."""
from pathlib import Path
import concurrent.futures,hashlib,importlib.util,json,random,struct,subprocess,sys
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/semantics/native_fixtures';r.mkdir(parents=True,exist_ok=True)
p=s/'config/guidance_package/FPGA_Sparse_Stream_R2_20261112/semantic_validation/validate_pop_reduce.py'
spec=importlib.util.spec_from_file_location('fixtures',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cases=m.directed();rng=random.Random(20261112)
palette=[(0,0),(0,1),(.125,.25),(.25,0),(1,2),(8,100),(8.5,0),(2,1)]
for i in range(80):
 n=rng.randrange(2,28);nc=rng.randrange(1,9)
 cases.append(m.fixture(f'native_random_{i:03d}',[rng.choice(palette) for _ in range(n)],[[v for v in range(n) if rng.random()<.14] for u in range(n)],[rng.randrange(nc) if rng.random()<.4 else -1 for _ in range(n)],nc,rng.randrange(n)))
cases.append(m.fixture('eligible_break_and_skip',[(0,0),(1,2),(2,3),(0,0),(0,0)],[[3,1,4,2],[],[],[],[]],[-1,0,1,-1,-1],2))
def write(g,out):
 n=len(g['cost']);nc=g['cells'];costs=[];ids=[];cost_keys=[]
 for c in g['cost']:
  key=struct.pack('<2f',*c)
  if key not in cost_keys:cost_keys.append(key);costs.append(tuple(c))
  ids.append(cost_keys.index(key))
 assert len(costs)<=16
 nodes=[(1 if g['cell'][i]>=0 else 0,ids[i],1,-1) for i in range(n)]
 if g['name']=='eligible_break_and_skip':nodes[3]=(0,ids[3],0,-1);nodes[4]=(2,ids[4],1,-1)
 row=[0];edges=[]
 for a in g['edges']:edges.extend(a);row.append(len(edges))
 cell=g['cell']+[(c+1)%nc if c>=0 else -1 for c in g['cell']]
 with out.open('wb') as f:
  f.write(struct.pack('<7Q',0x31414c5443495254,n,len(edges),2,len(costs),nc,1));f.write(struct.pack('<%dQ'%(n+1),*row))
  for x in nodes:f.write(struct.pack('<IIIi',*x))
  for v in edges:f.write(struct.pack('<II',v,0))
  for c in costs:f.write(struct.pack('<2f',*c))
  for q in range(2):f.write(struct.pack('<6I',g['source'],0,q,0,0,0))
  f.write(struct.pack('<%di'%len(cell),*cell));f.write(struct.pack('<%dI'%(nc*4),*([0x7fc00000]*(nc*4))))
def run(g):
 d=r/g['name'];d.mkdir(exist_ok=False);w=d/'workload.bin';gold=d/'original_ALT.bin';write(g,w)
 cmds=[[str(r.parent/'original_ALT'),str(w),str(gold)],[str(r.parent/'reference_pop_reduce'),str(w),str(gold),str(d/'pop'),'512','128']]
 for i,cmd in enumerate(cmds):
  with (d/f'run{i}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 result={'case':g['name'],'commands':cmds,'workload_sha256':h(w),'golden_sha256':h(gold),'pop_sha256':h(d/'pop/output.bin'),'jobs':2}
 assert result['golden_sha256']==result['pop_sha256'];(d/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');return result
if '--rejections-only' not in sys.argv:
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,cases))
 (r/'summary.json').write_text(json.dumps({'scope':'native C++ functional and bucket-closure verification; no RTL timing claim','cases':len(results),'jobs':2*len(results),'all_exact':True,'results':results},indent=2)+'\n')
 print('NATIVE_FIXTURES_PASS',len(results),flush=True)
# Admission failures retain logs and publish no partial map.
failures=[]
for name,bits in [('negative_zero',0x80000000),('negative',0xbf800000),('subnormal',1),('nan',0x7fc00000),('infinity',0x7f800000)]:
 g=m.fixture(name,[(0,0),(struct.unpack('<f',struct.pack('<I',bits))[0],0)],[[1],[]],[-1,0]);d=r/(name+'_bit_exact');d.mkdir();w=d/'workload.bin';write(g,w)
 cmd=[str(r.parent/'reference_pop_reduce'),str(w),str(r/'zero_outdegree_target/original_ALT.bin'),str(d/'rejected'),'512','128']
 with (d/'reject.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 assert rc!=0 and not (d/'rejected/output.bin').exists()
 assert 'UNSUPPORTED_NUMERIC admission' in (d/'reject.log').read_text()
 failures.append({'case':name,'command':cmd,'returncode':rc,'no_output':True})
(r/'numeric_rejections_bit_exact.json').write_text(json.dumps(failures,indent=2)+'\n');print('NUMERIC_REJECTIONS_PASS',len(failures))
