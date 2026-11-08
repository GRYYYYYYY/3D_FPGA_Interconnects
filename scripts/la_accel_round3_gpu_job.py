"""Measure cold first E1 and warm resident E1 with persistent allocations on one worker."""
import argparse,json,os,shutil,socket,subprocess,time,random,struct
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--workload',type=Path,action='append',required=True);p.add_argument('--all-cuda-jobs',action='store_true',help='One basic CTA per real native sample for the larger-graph cohort');a=p.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
 pools={};seen=set();initial=sorted(os.sched_getaffinity(0))
 for cpu in initial:
  d=Path(f'/sys/devices/system/cpu/cpu{cpu}');key=((d/'topology/physical_package_id').read_text(),(d/'topology/core_id').read_text())
  if key in seen:continue
  seen.add(key);node=sorted(d.glob('node*'))[0].name;pools.setdefault(node,[]).append(cpu)
 chosen=sorted(pools.values(),key=lambda x:(-len(x),x))[0][:8];assert len(chosen)==8;os.sched_setaffinity(0,chosen)
 src=o/'source';shutil.copytree(ROOT/'accel/lookahead',src)
 worker=dict(host=socket.gethostname(),affinity=chosen,initial_affinity=initial,cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text(),sources={str(p.relative_to(src)):sha256(p) for p in src.rglob('*') if p.is_file()},workloads={str(p.resolve()):sha256(p) for p in a.workload},cold_definition='First compute in a fresh process; graph allocation/upload precedes E1 and is separately reported.',warm_definition='Five subsequent complete batches using the same allocations; all state/output reset every invocation.',process_repeats=5)
 (o/'worker.json').write_text(json.dumps(worker,indent=2)+'\n');commands=[]
 def run(name,cmd):
  env={k:v for k,v in os.environ.items() if not k.startswith('OMP_')};env.update(OMP_DYNAMIC='FALSE',OMP_PROC_BIND='TRUE',OMP_PLACES='cores')
  start=time.monotonic()
  with (o/(name+'.log')).open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
  commands.append(dict(name=name,command=list(map(str,cmd)),returncode=r.returncode,host_elapsed_s=time.monotonic()-start));(o/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  if r.returncode:raise RuntimeError(name+' failed')
 try:
  for name,cmd in [('gpu',['nvidia-smi']),('nvcc',['nvcc','--version']),('cpu',['lscpu']),('compiler',['c++','--version'])]:run(name,cmd)
  cpu=o/'cpu_benchmark';gpu=o/'cuda_benchmark';inc='-I'+str(src/'include')
  run('build_cpu',['c++','-O2','-std=c++14','-fopenmp','-ffp-contract=off','-fno-fast-math',inc,str(src/'cpu_benchmark.cpp'),'-o',str(cpu)])
  run('build_cuda',['nvcc','-O2','-std=c++14','--fmad=false',inc,str(src/'cuda/cuda_benchmark.cu'),'-o',str(gpu)])
  schedule=[]
  for workload in a.workload:
   jobs=struct.unpack('<7Q',workload.open('rb').read(56))[3];case=workload.parent.name
   for process in range(5):
    for workers in [1,2,4,8]:
     if workers<=jobs:schedule.append((case,process,'cpu',workers,workload.resolve()))
    schedule.append((case,process,'cuda',jobs if a.all_cuda_jobs else min(8,jobs),workload.resolve()))
  random.Random(301).shuffle(schedule);records=[]
  for case,process,kind,parallel,workload in schedule:
   name=f'{case}_{kind}_{parallel}_process{process}'
   run(name,[str(cpu if kind=='cpu' else gpu),str(workload),str(parallel),'5'])
   rows=[json.loads(line) for line in (o/(name+'.log')).read_text().splitlines() if line.startswith('{')]
   assert len(rows)==6 and rows[0]['phase']=='cold_first_call' and all(x['all_golden_bits_match'] for x in rows)
   records.append(dict(case=case,process=process,kind=kind,parallel=parallel,workload_sha256=sha256(workload),measurements=rows,log=name+'.log'))
   (o/'measurements.json').write_text(json.dumps(records,indent=2)+'\n')
  (o/'finished.json').write_text(json.dumps(dict(status='passed',processes=len(records),binary_sha256={str(p):sha256(p) for p in [cpu,gpu]}),indent=2)+'\n')
 except Exception as e:
  (o/'finished.json').write_text(json.dumps(dict(status='failed',reason=str(e))));raise
if __name__=='__main__':main()
