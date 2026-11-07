"""Pin native controls to distinct physical cores; audit all child threads."""
import os
from pathlib import Path
import resource
import signal
import subprocess
import time
from prepare import write_json


def choose_cores(topology, count, preferred_node=None):
    chosen=[]; seen=set()
    for cpu in sorted(topology, key=lambda c:(c['node']!=preferred_node,c['socket'],c['core'],c['cpu'])):
        key=(cpu['socket'],cpu['core'])
        if key not in seen:
            chosen.append(cpu['cpu']);seen.add(key)
        if len(chosen)==count:return sorted(chosen)
    raise ValueError('Insufficient distinct physical cores in allowed CPU set')


def cgroup_cpu():
    paths=['/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/cpu.stat',
           '/sys/fs/cgroup/cpu/cpu.cfs_quota_us','/sys/fs/cgroup/cpu/cpu.cfs_period_us',
           '/sys/fs/cgroup/cpu/cpu.stat','/proc/self/cgroup',
           '/sys/fs/cgroup/memory.events','/sys/fs/cgroup/memory.events.local',
           '/sys/fs/cgroup/memory.max','/sys/fs/cgroup/memory.peak']
    return {p:Path(p).read_text() for p in paths if Path(p).is_file()}


def pin_budget(count):
    if count<=0:raise ValueError('CPU core count must be positive')
    allowed=sorted(os.sched_getaffinity(0));topology=[]
    for cpu in allowed:
        path=Path(f'/sys/devices/system/cpu/cpu{cpu}')
        nodes=list(path.glob('node[0-9]*'))
        topology.append({'cpu':cpu,'socket':int((path/'topology/physical_package_id').read_text()),
                         'core':int((path/'topology/core_id').read_text()),'node':int(nodes[0].name[4:]) if nodes else -1})
    preferred=None
    try:
        bus=subprocess.check_output(['nvidia-smi','--query-gpu=pci.bus_id','--format=csv,noheader'],text=True,stderr=subprocess.DEVNULL,timeout=10).splitlines()[0].lower()
        preferred=int((Path('/sys/bus/pci/devices')/bus[-12:]/'numa_node').read_text())
    except (OSError,ValueError,subprocess.SubprocessError,IndexError):pass
    before=cgroup_cpu()
    quota=before.get('/sys/fs/cgroup/cpu.max','max 100000').split()
    if quota[0]!='max' and int(quota[0])/int(quota[1])<count:raise ValueError('Cgroup quota below requested CPU budget')
    if '/sys/fs/cgroup/cpu/cpu.cfs_quota_us' in before:
        q=int(before['/sys/fs/cgroup/cpu/cpu.cfs_quota_us']);period=int(before['/sys/fs/cgroup/cpu/cpu.cfs_period_us'])
        if q>=0 and q/period<count:raise ValueError('Cgroup quota below requested CPU budget')
    chosen=choose_cores(topology,count,preferred);os.sched_setaffinity(0,chosen)
    return {'cores':count,'cpu_set':chosen,'allowed_before':allowed,'topology':topology,
            'preferred_gpu_numa_node':preferred,'cgroup':before,
            'scope':'One logical CPU per distinct physical core. Every VPR and CUDA service thread inherits this same set; no exclusivity against other workloads claimed.'}


def audit_threads(pid, permitted):
    observations=[]
    for task in Path(f'/proc/{pid}/task').glob('*'):
        try:
            actual=set(os.sched_getaffinity(int(task.name)))
            observations.append({'tid':int(task.name),'cpus':sorted(actual),'within_budget':actual<=permitted})
        except ProcessLookupError:pass
    return observations


def audited_process(command,directory,env,timeout,log_name='process.log'):
    directory=Path(directory);command=list(map(str,command));permitted=set(os.sched_getaffinity(0))
    record={'command':command,'timeout_seconds':timeout,'status':'running'}
    audit={'permitted_cpu_set':sorted(permitted),'samples':0,'max_threads':0,'affinity_violations':[],
           'cgroup_before':cgroup_cpu(),'peak_observed_rss_kib':0,'peak_observed_hwm_kib':0,
           'note':'Affinities and memory sampled every five seconds; transient changes are not observable. Memory event counters cover the containing cgroup.'}
    usage=resource.getrusage(resource.RUSAGE_CHILDREN);started=time.perf_counter()
    with (directory/log_name).open('w') as log:
        process=subprocess.Popen(command,cwd=directory,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        while True:
            tasks=audit_threads(process.pid,permitted)
            try:
                for line in Path(f'/proc/{process.pid}/status').read_text().splitlines():
                    for name,key in [('VmRSS:','peak_observed_rss_kib'),('VmHWM:','peak_observed_hwm_kib')]:
                        if line.startswith(name):audit[key]=max(audit[key],int(line.split()[1]))
            except FileNotFoundError:pass
            if tasks:
                audit['samples']+=1;audit['max_threads']=max(audit['max_threads'],len(tasks))
                audit['affinity_violations'].extend(x for x in tasks if not x['within_budget'])
            left=timeout-(time.perf_counter()-started)
            try:
                rc=process.wait(timeout=max(0,min(5,left)))
                record.update(returncode=rc,status='completed' if rc==0 else 'failed');break
            except subprocess.TimeoutExpired:
                if time.perf_counter()-started<timeout:continue
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                record.update(returncode=process.returncode,status='timeout');break
    record['process_seconds']=time.perf_counter()-started
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    audit.update(cpu_user_seconds=after.ru_utime-usage.ru_utime,cpu_system_seconds=after.ru_stime-usage.ru_stime,
                 cgroup_after=cgroup_cpu(),verified=audit['samples']>0 and not audit['affinity_violations'])
    record['cpu_budget_audit']=audit
    write_json(directory/(log_name+'.resources.json'),audit)
    return record
