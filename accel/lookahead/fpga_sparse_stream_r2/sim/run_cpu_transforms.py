from pathlib import Path
import os,sys,subprocess,json,time,hashlib,socket
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'software'/sys.argv[1];out.mkdir(parents=True,exist_ok=False);exe=r/'semantics/cpu_prepared_pop'
# Use eight distinct permitted physical cores; measurements share this host with
# synthesis and are explicitly labelled, never substituted for the GPU host CPU.
cpus=[];seen=set()
for cpu in sorted(os.sched_getaffinity(0),reverse=True):
 p=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology');key=((p/'physical_package_id').read_text(),(p/'core_id').read_text())
 if key not in seen:cpus.append(cpu);seen.add(key)
 if len(cpus)==8:break
os.sched_setaffinity(0,cpus)
(out/'environment.json').write_text(json.dumps({'hostname':socket.gethostname(),'affinity':cpus,'lscpu':subprocess.check_output(['lscpu'],text=True),'other_Vivado_processes_running':True,'same_GPU_host':False,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2))
items=[]
for x in json.loads((r/'semantics/native_complete.json').read_text()):
 c=x['command'];items.append((Path(c[3]).name,c[1],c[2]))
for name,w,g in items:
 for process in range(3):
  cmd=[str(exe),w,g,str(process),'8','4'];t=time.time()
  with (out/f'{name}_p{process}.jsonl').open('w') as log, (out/f'{name}_p{process}.stderr').open('w') as err:rc=subprocess.run(cmd,stdout=log,stderr=err).returncode
  (out/f'{name}_p{process}.receipt.json').write_text(json.dumps({'command':cmd,'returncode':rc,'start_unix':t,'end_unix':time.time()},indent=2));print(name,process,rc,flush=True)
  if rc:raise SystemExit(rc)
