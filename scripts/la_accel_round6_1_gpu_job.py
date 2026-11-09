"""One owner; predeclared finite matrices and gated live native CUDA. No fallback."""
import os,sys,json,subprocess,time,socket,shutil,random,struct
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();o=Path(sys.argv[2]).resolve();o.mkdir(exist_ok=False)
pools={};seen=set()
for cpu in sorted(os.sched_getaffinity(0)):
 d=Path(f'/sys/devices/system/cpu/cpu{cpu}');key=((d/'topology/physical_package_id').read_text(),(d/'topology/core_id').read_text())
 if key in seen:continue
 seen.add(key);pools.setdefault(sorted(d.glob('node*'))[0].name,[]).append(cpu)
cpus=sorted(pools.values(),key=lambda x:(-len(x),x))[0][:8];quota=Path('/sys/fs/cgroup/cpu.max').read_text().split();assert len(cpus)==8 and (quota[0]=='max' or int(quota[0])/int(quota[1])>=8);os.sched_setaffinity(0,cpus)
src=o/'source';shutil.copytree(R/'accel/lookahead',src);commands=[]
(o/'worker.json').write_text(json.dumps(dict(host=socket.gethostname(),affinity=cpus,cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text(),sources={str(p.relative_to(src)):sha256(p) for p in src.rglob('*') if p.is_file()},protocol='three fresh processes, three warm complete batches each; all solver timings sequential; phase profiling separate; one NUMA pool8 physical cores'),indent=2))
def run(name,cmd,timeout=900,native=False):
 env={k:v for k,v in os.environ.items() if not k.startswith('OMP_')}
 if not native:env.update(OMP_DYNAMIC='FALSE',OMP_PROC_BIND='TRUE',OMP_PLACES='cores')
 start=time.monotonic()
 with (o/(name+'.log')).open('w') as f:
  try:p=subprocess.run(list(map(str,cmd)),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout);rc=p.returncode
  except subprocess.TimeoutExpired:rc=124
 commands.append(dict(name=name,command=list(map(str,cmd)),returncode=rc,elapsed_s=time.monotonic()-start));(o/'commands.json').write_text(json.dumps(commands,indent=2))
 if rc:raise RuntimeError(name+': '+str(rc))
 return [json.loads(x) for x in (o/(name+'.log')).read_text().splitlines() if x.startswith('{')]
try:
 for name,cmd in [('gpu',['nvidia-smi']),('nvcc',['nvcc','--version']),('cpu',['lscpu']),('compiler',['c++','--version'])]:run(name,cmd)
 inc='-I'+str(src/'include');cpu=o/'cpu61';strict=o/'strict61';gpu=o/'cuda61';basic=o/'cuda6';lib=o/'libcuda61.so'
 run('build_cpu',['c++','-O3','-std=c++14','-fopenmp','-ffp-contract=off','-fno-fast-math',inc,src/'round6_1/cpu61.cpp','-o',cpu])
 run('build_strict',['c++','-O3','-std=c++14','-fopenmp','-ffp-contract=off','-fno-fast-math',inc,src/'round6_1/strict61.cpp','-o',strict])
 run('build_gpu',['nvcc','-O3','-std=c++14','--fmad=false',inc,src/'round6_1/cuda61.cu','-o',gpu])
 run('build_basic',['nvcc','-O3','-std=c++14','--fmad=false',inc,src/'round6/cuda6.cu','-o',basic])
 run('build_backend',['nvcc','-O3','-std=c++14','--fmad=false','-shared','-Xcompiler=-fPIC,-fopenmp',inc,src/'round6_1/cuda_backend61.cu','-o',lib])
 fixtures=sorted((R/'results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/semantic_fixtures').glob('*.bin'))
 small=[]
 for case,rd in [('native_d3_w8','round3_20261108T141500Z'),('native_d4_w8','round3_20261108T141500Z'),('native_d5_w8','round4_20261108T182500Z'),('native_d6_w8','round5_20261109T054024Z'),('native_d8_w8','round5_20261109T054024Z'),('native_d6_w8_l1','round5_20261109T054024Z')]:small.append(R/f'results/lookahead_accel_{rd}/evidence_snapshot/{case}/workload.bin')
 functional=[]
 for path in fixtures+small:
  case=path.stem if path.name!='workload.bin' else path.parent.name
  for shift in [0,20]:
   ref=o/'functional_reference.bin';dest=o/'functional_output.bin';run(f'cpu_ref_{case}_{shift}',[cpu,path,shift,1,0,ref,0,'original']);z=run(f'compact_cuda_{case}_{shift}',[gpu,path,shift,0,ref,dest,'compact',0]);assert dest.read_bytes()==ref.read_bytes();functional.append(dict(case=case,shift=shift,pass_=True))
 (o/'functional.json').write_text(json.dumps(functional,indent=2))
 work=[(c,R/'results/lookahead_accel_20261108T125500Z'/c/'workload.bin') for c in ['tseng_export','bnn_export']];refs={}
 for case,path in work:
  # Capacity preflight includes the frozen E+1 heap per CPU worker.
  h=struct.unpack('<7Q',path.open('rb').read(56));assert h[1]<(1<<23) and h[2]<2**32
  (o/(case+'_preflight.json')).write_text(json.dumps(dict(path=str(path),sha256=sha256(path),header=h,strict8_scratch_bytes=8*(5*h[1]+12*(h[2]+1)),compact_graph_bytes=8*(h[1]+1)+2*h[1]+4*h[2]+8*h[4],scope='no admission relaxation; raw CSR order'),indent=2))
  for shift in [0,20]:
   ref=o/f'{case}_s{shift}_reference.bin';run(f'reference_{case}_{shift}',[cpu,path,shift,8,0,ref,0,'original']);refs[case,shift]=ref
 # A1 and B1/B2 same host, with fixed old legal thread choices.
 schedule=[]
 for case,path in work:
  for rep in range(3):
   for workers in ([4,8] if case=='bnn_export' else [1,4,8]):
    for kind in ['strict','early','alt_original','alt_compact','alt_direct']:schedule.append((case,path,rep,kind,workers))
   for kind in ['gpu_basic','gpu_compact']:schedule.append((case,path,rep,kind,0))
 random.Random(6101).shuffle(schedule);records=[]
 for case,path,rep,kind,workers in schedule:
  name=f'{case}_{kind}_w{workers}_p{rep}';dest=o/(name+'.bin')
  if kind in ['strict','early']:cmd=[strict,path,workers,3,'full' if kind=='strict' else 'early']
  elif kind.startswith('alt_'):cmd=[cpu,path,20,workers,3,dest,0,kind.split('_')[1]]
  elif kind=='gpu_basic':cmd=[basic,path,20,3,refs[case,20],dest]
  else:cmd=[gpu,path,20,3,refs[case,20],dest,'compact',0]
  rows=run(name,cmd);assert len(rows)==4
  if kind not in ['strict','early']:assert dest.read_bytes()==refs[case,20].read_bytes();dest.unlink()
  records.append(dict(case=case,kind=kind,workers=workers,process=rep,measurements=rows));(o/'measurements.json').write_text(json.dumps(records,indent=2))
 # A5 separate, only two inputs x two shifts. No profiling in the table above.
 phases=[]
 for case,path in work:
  for shift in [0,20]:phases.append(dict(case=case,shift=shift,measurements=run(f'phase_{case}_{shift}',[gpu,path,shift,0,refs[case,shift],o/'phase_output.bin','original',1])))
 (o/'phase_profile.json').write_text(json.dumps(phases,indent=2))
 # Verify actual A2 flags before A3/A4; do not infer completion from a partial JSON.
 a2=r/'native_cpu_qualification_b/runs.json';deadline=time.monotonic()+600
 while not a2.exists() or len(json.load(open(a2)))!=6:
  if time.monotonic()>deadline:raise RuntimeError('A2 incomplete; native CUDA not started')
  time.sleep(5)
 d=json.load(open(a2))
 for case in ['s38417','bnn']:
  c=next(x for x in d if x['case']==case and x['arm']=='control');a=next(x for x in d if x['case']==case and x['arm']=='alt_s20')
  assert a['returncode']==0 and a['alt_dispatch_verified'] and a['metrics']['full_check'] and a.get('readback_identity') and a['independent']['metrics']['full_check']
  for k in ['critical_path_ns','wirelength']:assert a['metrics'][k]<=1.05*c['metrics'][k]
 run('native_live_matrix',['python3',R/'scripts/la_accel_round6_1_native_worker.py',r,o/'native'],timeout=7200,native=True)
 (o/'finished.json').write_text(json.dumps(dict(status='passed',matched_processes=len(records),functional_configurations=len(functional),native=json.load(open(o/'native/finished.json'))),indent=2))
except Exception as e:
 (o/'finished.json').write_text(json.dumps(dict(status='failed',reason=str(e)),indent=2));raise
