"""One allocation. Inherit the bound NUMA policy through exec."""
import ctypes, datetime, json, os, platform, shutil, socket, subprocess, time
from pathlib import Path

here = Path(__file__).resolve().parent
from cohort import run
run.mkdir(exist_ok=False)
def read(path): return Path(path).read_text().strip()
def query(*args): return subprocess.check_output(args,text=True).strip()
def now(): return datetime.datetime.now(datetime.timezone.utc)
deadline=datetime.datetime.fromisoformat('2026-11-19T13:00:00+00:00')
cg=Path('/sys/fs/cgroup')
cpus=[]
cores=set()
for cpu in sorted(os.sched_getaffinity(0)):
    p=Path(f'/sys/devices/system/cpu/cpu{cpu}')
    identity=(read(p/'topology/physical_package_id'), read(p/'topology/core_id'))
    if (p/'node0').exists() and identity not in cores:
        cpus.append(cpu);cores.add(identity)
    if len(cpus)==8: break
gpu=query('nvidia-smi','--query-gpu=uuid,name,memory.total,memory.free,power.limit,pstate,clocks.sm,clocks.mem','--format=csv,noheader,nounits')
model=next(x.split(':',1)[1].strip() for x in read('/proc/cpuinfo').splitlines() if x.startswith('model name'))
env=dict(host=socket.gethostname(),boot=read('/proc/sys/kernel/random/boot_id'),cpu=model,
         cpus=cpus,physical=sorted(cores),topology=query('lscpu','-p=CPU,CORE,SOCKET,NODE'),gpu=gpu,
         cpu_max=read(cg/'cpu.max'),memory_max=read(cg/'memory.max'),cpuset=read(cg/'cpuset.cpus.effective'),
         cuda=query('nvcc','--version'),compiler=query('g++','--version'),utc=now().isoformat(),
         deadline=deadline.isoformat(),os=platform.platform(),numa_node=0)
f=run/'environment.json'
f.write_text(json.dumps(env,indent=2))
assert '8462Y+' in model and 'H100' in gpu and len(gpu.splitlines())==1 and len(cpus)==8,env
assert int(gpu.split(',')[2])>=80000 and int(env['memory_max'])==200*(1<<30)
q,t=map(int,env['cpu_max'].split());assert q/t==10
os.sched_setaffinity(0,cpus)
mask=ctypes.c_ulong(1)
lib=ctypes.CDLL(None,use_errno=True)
assert platform.machine()=='x86_64' and lib.syscall(238,2,ctypes.byref(mask),64)==0,ctypes.get_errno()
env['memory_policy']='MPOL_BIND node 0'
env['cpu_governors']={c:read(p) if p.exists() else 'unexposed' for c in cpus for p in [Path(f'/sys/devices/system/cpu/cpu{c}/cpufreq/scaling_governor')]}
f.write_text(json.dumps(env,indent=2))
os.environ['CUDA_VISIBLE_DEVICES']=gpu.split(',')[0].strip()
while now()<deadline:
    if (here/'build/ready').is_file():
        os.execv(shutil.which('python3'),['python3',str(here/'worker.py')])
    time.sleep(10)
raise SystemExit('Reservation deadline reached')
