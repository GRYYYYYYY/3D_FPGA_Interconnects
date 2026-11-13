"""Resolve quoted include closure, freeze exact inputs and compile both CPU variants."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,shutil
root=Path(__file__).resolve().parents[4];base=root/'accel/lookahead'
out=Path(sys.argv[1]).resolve();out.mkdir(exist_ok=False);src=out/'source';src.mkdir()
search=[base/'fpga_sparse_stream_r2',base/'round6_1',base/'include']
todo=[search[0]/n for n in ['cuda_private_inf.cu','cpu_private_inf.cpp','cuda_prepared_pop.cu','cpu_prepared_pop.cpp']];seen={};records=[]
while todo:
 p=todo.pop().resolve();raw=p.read_bytes()
 if p.name in seen:
  assert seen[p.name]==p,'flat snapshot filename collision';continue
 seen[p.name]=p;(src/p.name).write_bytes(raw)
 records.append({'original_path':str(p.relative_to(root)),'snapshot':p.name,'sha256':hashlib.sha256(raw).hexdigest()})
 for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"',raw.decode(),re.M):
  matches={q.resolve() for d in [p.parent,*search] if (q:=d/name).is_file()}
  assert len(matches)==1,(p,name,matches)
  todo.extend(matches)
worker=Path(__file__).with_name('gpu_private_inf_worker.py');shutil.copy2(worker,out/worker.name)
manifest={'root':str(root),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'files':sorted(records,key=lambda x:x['snapshot']),'worker_sha256':hashlib.sha256(worker.read_bytes()).hexdigest()}
(out/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
build=[]
for name in ['cpu_private_inf','cpu_prepared_pop']:
 cmd=['g++','-O3','-std=c++17','-fopenmp','-ffp-contract=off','-I'+str(src),str(src/(name+'.cpp')),'-o',str(out/name)]
 with (out/(name+'.build.log')).open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 build.append({'command':cmd,'returncode':rc,'binary_sha256':hashlib.sha256((out/name).read_bytes()).hexdigest() if rc==0 else None})
(out/'preflight.json').write_text(json.dumps({'source_complete':True,'files':len(records),'builds':build,'all_pass':all(x['returncode']==0 for x in build),'CUDA_compile':'first stage on allocated matching toolkit node'},indent=2)+'\n')
assert all(x['returncode']==0 for x in build)
print('SOURCE_CLOSURE_CPU_PREFLIGHT_PASS',len(records))
