"""Predeclared sequential CPU/CUDA screen on one NUMA pool. No CPU fallback."""
import os,sys,json,subprocess,time,socket,shutil,random,struct,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];o=Path(sys.argv[1]).resolve();o.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest()
pools={};seen=set()
for cpu in sorted(os.sched_getaffinity(0)):
 d=Path(f'/sys/devices/system/cpu/cpu{cpu}');key=((d/'topology/physical_package_id').read_text(),(d/'topology/core_id').read_text())
 if key in seen:continue
 seen.add(key);node=sorted(d.glob('node*'))[0].name;pools.setdefault(node,[]).append(cpu)
quota=Path('/sys/fs/cgroup/cpu.max').read_text().split();limit=8 if quota[0]=='max' else min(8,int(quota[0])//int(quota[1]));cpus=sorted(pools.values(),key=lambda x:(-len(x),x))[0][:limit];assert len(cpus)>=4;os.sched_setaffinity(0,cpus)
src=o/'source';shutil.copytree(R/'accel/lookahead/round6',src/'round6');shutil.copytree(R/'accel/lookahead/include',src/'include');commands=[]
(o/'worker.json').write_text(json.dumps(dict(host=socket.gethostname(),affinity=cpus,cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text(),process_repeats=3,warm_repeats=3,scope='complete real batch E1: resets, search, closure, output materialization and synchronization; excludes load/preparation and verification',sources={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()}),indent=2))
def run(name,cmd,timeout=600):
 env={k:v for k,v in os.environ.items() if not k.startswith('OMP_')};env.update(OMP_DYNAMIC='FALSE',OMP_PROC_BIND='TRUE',OMP_PLACES='cores');start=time.monotonic()
 with (o/(name+'.log')).open('w') as f:
  try:p=subprocess.run(list(map(str,cmd)),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout);rc=p.returncode
  except subprocess.TimeoutExpired:rc=124
 commands.append(dict(name=name,command=list(map(str,cmd)),returncode=rc,elapsed_s=time.monotonic()-start));(o/'commands.json').write_text(json.dumps(commands,indent=2))
 if rc:raise RuntimeError(f'{name}: rc={rc}')
 return [json.loads(x) for x in (o/(name+'.log')).read_text().splitlines() if x.startswith('{')]
try:
 for name,cmd in [('gpu',['nvidia-smi']),('compiler',['c++','--version']),('nvcc',['nvcc','--version']),('lscpu',['lscpu'])]:run(name,cmd)
 cpu=o/'cpu6';gpu=o/'cuda6';inc='-I'+str(src/'include')
 run('build_cpu',['c++','-O3','-std=c++14','-fopenmp','-ffp-contract=off','-fno-fast-math',inc,src/'round6/cpu6.cpp','-o',cpu])
 run('build_cuda',['nvcc','-O3','-std=c++14','--fmad=false',inc,src/'round6/cuda6.cu','-o',gpu])
 small=[]
 for case,rd in [('native_d3_w8','round3_20261108T141500Z'),('native_d4_w8','round3_20261108T141500Z'),('native_d5_w8','round4_20261108T182500Z'),('native_d6_w8','round5_20261109T054024Z'),('native_d8_w8','round5_20261109T054024Z'),('native_d6_w8_l1','round5_20261109T054024Z')]:small.append((case,R/f'results/lookahead_accel_{rd}/evidence_snapshot/{case}/workload.bin'))
 fixtures=R/'results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/semantic_fixtures'
 # All semantic fixtures, both modes; a fresh process per test retains independent status.
 for path in sorted(fixtures.glob('*.bin')):
  for shift in [0,20]:
   ref=o/f'ref_{path.stem}_{shift}.bin';run(f'fixture_cpu_{path.stem}_{shift}',[cpu,path,shift,1,0,ref,0]);run(f'fixture_cuda_{path.stem}_{shift}',[gpu,path,shift,0,ref,o/'fixture_last.bin'])
   ref.unlink()
 work=small+[ (c,R/'results/lookahead_accel_20261108T125500Z'/c/'workload.bin') for c in ['tseng_export','bnn_export']]
 refs={};inputs=[]
 for case,path in work:
  inputs.append(dict(case=case,path=str(path),sha256=sha(path)))
  for shift in [0,20]:
   ref=o/f'{case}_s{shift}_reference.bin';run(f'reference_{case}_s{shift}',[cpu,path,shift,len(cpus),0,ref,0]);refs[case,shift]=ref
 (o/'inputs.json').write_text(json.dumps(inputs,indent=2))
 schedule=[]
 for case,path in work:
  for shift in [0,20]:
   for rep in range(3):
    for workers in ([4,len(cpus)] if case=='bnn_export' else [1,4,len(cpus)]):schedule.append((case,path,shift,rep,'cpu',workers))
    schedule.append((case,path,shift,rep,'cuda',0))
 random.Random(601).shuffle(schedule);records=[]
 for case,path,shift,rep,kind,workers in schedule:
  name=f'{case}_s{shift}_{kind}_w{workers}_p{rep}';dest=o/(name+'.bin')
  cmd=[cpu,path,shift,workers,3,dest,0] if kind=='cpu' else [gpu,path,shift,3,refs[case,shift],dest]
  rows=run(name,cmd);assert len(rows)==4
  assert dest.read_bytes()==refs[case,shift].read_bytes()
  records.append(dict(case=case,shift=shift,process=rep,kind=kind,workers=workers,measurements=rows));(o/'measurements.json').write_text(json.dumps(records,indent=2));dest.unlink()
 (o/'finished.json').write_text(json.dumps(dict(status='passed',records=len(records),fixture_configurations=1018,binary_sha256={str(p):sha(p) for p in [cpu,gpu]}),indent=2))
except Exception as e:
 (o/'finished.json').write_text(json.dumps(dict(status='failed',reason=str(e)),indent=2));raise
