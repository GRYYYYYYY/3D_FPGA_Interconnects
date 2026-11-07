"""Read-only probe of a new CPU allocation, no solver and no secrets."""
import json,os,socket,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'results/native_paper_closure_20261105/platform'
files=['/proc/self/cgroup','/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/cpuset.cpus.effective','/sys/fs/cgroup/cpuset.cpus.exclusive.effective','/sys/fs/cgroup/cpuset.cpus.partition','/sys/fs/cgroup/memory.max','/sys/fs/cgroup/cpu/cpu.cfs_quota_us','/sys/fs/cgroup/cpu/cpu.cfs_period_us']
r=dict(hostname=socket.gethostname(),utc=time.time(),pid=os.getpid(),affinity=sorted(os.sched_getaffinity(0)),files={p:Path(p).read_text() for p in files if Path(p).exists()},slurm={k:v for k,v in os.environ.items() if k.startswith('SLURM_') and not any(t in k for t in ['TOKEN','SECRET','PASS'])},commands={})
for key,cmd in [('topology',['lscpu','-e=CPU,CORE,SOCKET,NODE,ONLINE']),('identity',['lscpu']),('processes',['ps','-eo','pid,comm,pcpu','--sort=-pcpu']),('mounts',['findmnt','-T',str(root)])]:
 p=subprocess.run(cmd,capture_output=True,text=True);r['commands'][key]=dict(rc=p.returncode,stdout=p.stdout,stderr=p.stderr)
r['shared_workspace_readable']=root.is_dir();(out/'cpu_instance_probe.json').write_text(json.dumps(r,indent=2));print(json.dumps({'probe_written':str(out/'cpu_instance_probe.json'),'hostname':r['hostname'],'allowed_cpus':len(r['affinity'])}))
