from pathlib import Path
import os,sys,json,subprocess,hashlib,time,socket,shutil
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112';o=r/'software'/sys.argv[1];o.mkdir(exist_ok=False);src=o/'source';src.mkdir()
for p in [s/'cuda_prepared_pop.cu',s/'cpu_prepared_pop.cpp']:shutil.copy2(p,src/p.name)
cpus=[];cores=set()
for cpu in sorted(os.sched_getaffinity(0)):
 p=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology');key=((p/'physical_package_id').read_text(),(p/'core_id').read_text())
 if key not in cores:cores.add(key);cpus.append(cpu)
 if len(cpus)==8:break
assert len(cpus)==8;os.sched_setaffinity(0,cpus)
items=json.loads((r/'semantics/native_complete.json').read_text())
def prepared(c):
 p=Path(c[3])/'prepared.bin'
 return p if p.exists() else r/'semantics/large_prepared'/(Path(c[3]).name+'.bin')
for x in items:
 c=x['command']
 for p in [Path(c[1]),Path(c[2]),prepared(c)]:assert p.is_file(),str(p)
nvcc=shutil.which('nvcc');assert nvcc
(o/'environment.json').write_text(json.dumps({'hostname':socket.gethostname(),'affinity':cpus,'started_unix':time.time(),'nvcc':subprocess.check_output([nvcc,'--version'],text=True),'nvidia_smi':subprocess.check_output(['nvidia-smi'],text=True),'lscpu':subprocess.check_output(['lscpu'],text=True)},indent=2))
commands=[[nvcc,'-O3','-std=c++17','--fmad=false','-I'+str(root/'accel/lookahead/include'),'-I'+str(root/'accel/lookahead/round6_1'),str(src/'cuda_prepared_pop.cu'),'-o',str(o/'gpu')],['g++','-O3','-std=c++17','-fopenmp','-ffp-contract=off','-I'+str(root/'accel/lookahead/include'),'-I'+str(root/'accel/lookahead/round6_1'),str(src/'cpu_prepared_pop.cpp'),'-o',str(o/'cpu')]]
for i,c in enumerate(commands):
 with (o/f'build_{i}.log').open('w') as log:subprocess.run(c,stdout=log,stderr=subprocess.STDOUT,check=True)
(o/'binding.json').write_text(json.dumps({'build_commands':commands,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in src.iterdir()},'scope':'RESIDENT_COMPLETE_BATCH_V2','old_GPU_V2_rerun':False},indent=2))
def execute(name,c):
 t=time.time()
 with (o/(name+'.jsonl')).open('w') as log,(o/(name+'.stderr')).open('w') as err:rc=subprocess.run(c,stdout=log,stderr=err).returncode
 (o/(name+'.receipt.json')).write_text(json.dumps({'command':c,'returncode':rc,'start_unix':t,'end_unix':time.time()},indent=2))
 print(name,rc,flush=True)
 if rc:raise RuntimeError(name+' failed')
for x in json.loads((r/'semantics/native_fixtures/summary.json').read_text())['results']:
 d=r/'semantics/native_fixtures'/x['case']
 for kind in ['basic','compact']:
  name=x['case']+'_'+kind;execute(name,[str(o/'gpu'),str(d/'workload.bin'),str(d/'pop/prepared.bin'),str(d/'original_ALT.bin'),str(o/(name+'.bin')),'1',kind])
for x in items:
 c=x['command'];name=Path(c[3]).name
 for proc in range(3):
  for kind in ['basic','compact']:
   nm=f'{name}_{kind}_p{proc}';execute(nm,[str(o/'gpu'),c[1],str(prepared(c)),c[2],str(o/(nm+'.bin')),'4',kind])
  execute(f'{name}_cpu_p{proc}',[str(o/'cpu'),c[1],c[2],str(proc),'8','4'])
(o/'completed.json').write_text(json.dumps({'status':'complete','scope':'measured CUDA prepared CSR/online POP + same worker CPU; all complete batches; old GPU V2 reused unchanged'}))
