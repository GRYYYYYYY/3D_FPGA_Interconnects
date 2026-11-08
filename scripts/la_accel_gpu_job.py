"""Compile and measure STRICT CUDA on a real GPU worker; no host fallback."""
import argparse,subprocess,json,os,time,sys,socket
from prepare import sha256
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--pin-physical',type=int,default=0);p.add_argument('--main-controls-only',action='store_true');a=p.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False);exp=a.experiment.resolve();records=[]
 initial_affinity=sorted(os.sched_getaffinity(0))
 if a.pin_physical:
  pools={};seen=set()
  for cpu_id in initial_affinity:
   entry=Path('/sys/devices/system/cpu')/('cpu'+str(cpu_id));key=((entry/'topology/physical_package_id').read_text(),(entry/'topology/core_id').read_text());nodes=sorted(entry.glob('node*'));node=nodes[0].name if nodes else 'unknown'
   if key in seen:continue
   seen.add(key);pools.setdefault(node,[]).append(cpu_id)
  chosen=sorted(pools.values(),key=lambda x:(-len(x),x))[0][:a.pin_physical];assert len(chosen)==a.pin_physical
  os.sched_setaffinity(0,chosen);os.environ['OMP_PROC_BIND']='true';os.environ['OMP_PLACES']='cores'
 (o/'worker.json').write_text(json.dumps(dict(hostname=socket.gethostname(),initial_affinity=initial_affinity,affinity=sorted(os.sched_getaffinity(0)),requested_physical_cores=a.pin_physical,cgroup={k:Path('/sys/fs/cgroup/'+k).read_text() for k in ['cpu.max','memory.max']},sources={str(p.relative_to(ROOT)):sha256(p) for p in (ROOT/'accel/lookahead').rglob('*') if p.is_file()}),indent=2))
 def run(name,cmd,timeout=600):
  start=time.time();r=None;failure=None
  with (o/(name+'.log')).open('w') as log:
   try:
    env=os.environ.copy()
    if name=='native_controls':
     # libgomp may otherwise pin VPR's main thread to one CPU before its audit.
     env.pop('OMP_PROC_BIND',None);env.pop('OMP_PLACES',None)
    r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,env=env)
   except subprocess.TimeoutExpired:failure='timeout'
  records.append(dict(name=name,command=cmd,returncode=r.returncode if r else None,failure_reason=failure,host_elapsed_s=time.time()-start));(o/'commands.json').write_text(json.dumps(records,indent=2));return r is not None and r.returncode==0
 if not run('device',['nvidia-smi']):return 1
 if not run('compiler',['nvcc','--version']):return 1
 binary=o/'lookahead_cuda'
 if not run('build',['nvcc','-O2','-std=c++14','--fmad=false','-I'+str(ROOT/'accel/lookahead/include'),str(ROOT/'accel/lookahead/cuda/lookahead_cuda.cu'),'-o',str(binary)]):return 1
 cpu=o/'cpu_reference'
 if not run('cpu_build',['c++','-O2','-std=c++14','-fopenmp','-ffp-contract=off','-fno-fast-math','-I'+str(ROOT/'accel/lookahead/include'),str(ROOT/'accel/lookahead/cpu_reference.cpp'),'-o',str(cpu)]):return 1
 for case in ['tseng_export','tseng_eligible','bnn_export']:
  run('cpu_'+case,[sys.executable,str(ROOT/'scripts/la_accel_run.py'),'--backend','cpu','--workers','8','--binary',str(cpu),'--workload',str(exp/case/'workload.bin'),'--repeats','3','--output',str(o/('cpu_'+case))])
 run('native_controls',[sys.executable,str(ROOT/'scripts/reproduce_native_lookahead.py'),'--output',str(o/'native_controls'),'--case','tseng_2d','--workers','8','--repeats','3','--include-stock','--execute'])
 # Semantic fixture first, then real full graphs. Never clone tasks to increase occupancy.
 if not run('adversarial',[str(binary),str(exp/'adversarial.bin'),str(o/'adversarial.bin'),'3']):return 1
 for case,contexts in ([('tiny_native',[4]),('tseng_export',[8]),('bnn_export',[40])] if a.main_controls_only else [('tiny_native',[1,2,4]),('tseng_export',[1,2,4,8]),('bnn_export',[40])]):
  for B in contexts:
   run(f'{case}_B{B}',[sys.executable,str(ROOT/'scripts/la_accel_run.py'),'--backend','cuda','--binary',str(binary),'--workload',str(exp/case/'workload.bin'),'--contexts',str(B),'--repeats','1','--timeout','600','--output',str(o/f'{case}_B{B}')],timeout=620)
 (o/'finished.json').write_text(json.dumps({'status':'completed' if all(r['returncode']==0 for r in records) else 'completed_with_failures','all_commands_successful':all(r['returncode']==0 for r in records)},indent=2))
 return 0 if all(r['returncode']==0 for r in records) else 1
if __name__=='__main__':raise SystemExit(main())
