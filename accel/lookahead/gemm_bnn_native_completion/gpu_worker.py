"""One worker, two cases, four qualification arms, three rotated formal arms.
No FPGA actions, retries, parameter search, profile or extra workloads.
"""
import runner as w
from pathlib import Path
import os,sys,json,subprocess,time,socket,fcntl,datetime,hashlib,shutil,ctypes,platform
H=w.H;ROOT=w.ROOT;R=ROOT/'results/gemm_bnn_native_completion_20261117/gpu_matched_a'
R.mkdir(parents=True,exist_ok=False)
for d in ['environment','qualification','formal','analysis','receipts']:(R/d).mkdir()
lock=(R/'runner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def query(args):return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT,timeout=30)
def snap():return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cpu_stat=Path('/sys/fs/cgroup/cpu.stat').read_text(),memory_current=Path('/sys/fs/cgroup/memory.current').read_text(),gpu=query(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.free,utilization.gpu','--format=csv,noheader,nounits']),gpu_processes=query(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_memory','--format=csv,noheader,nounits']))
def qos(row,controls):return bool(row['qualified'] and row['E2_s'] and all(c['qualified'] and all(row['metrics'][k]<=1.05*c['metrics'][k] for k in ['critical_path_ns','wirelength']) for c in controls))
rows=[];statuses={}
def flush():w.save(R/'rows.json',rows);w.save(R/'case_status.json',statuses)
try:
 gate=w.read(H/'V1_publication.json');assert gate['new_experiments_allowed']
 w.save(R/'receipts/V1_publication.json',gate)
 frozen=w.read(H/'worker_freeze.json');assert all(w.sha(H/n)==h for n,h in frozen['files'].items()),'worker source drift'
 w.save(R/'receipts/worker_freeze.json',frozen)
 for x in w.bins.values():assert w.sha(x['path'])==x['sha256']
 for c in w.inputs.values():
  for x in c['case']['inputs'].values():assert w.sha(x['path'])==x['sha256']
 for x in w.runtime['libraries']:assert w.sha(x['path'])==x['sha256']
 pools={};seen=set()
 for cpu in sorted(os.sched_getaffinity(0)):
  p=Path(f'/sys/devices/system/cpu/cpu{cpu}');key=((p/'topology/physical_package_id').read_text(),(p/'topology/core_id').read_text())
  if key in seen:continue
  seen.add(key);pools.setdefault(int(sorted(p.glob('node*'))[0].name[4:]),[]).append(cpu)
 node,allcpus=sorted(pools.items(),key=lambda x:(-len(x[1]),x[1]))[0];cpus=allcpus[:8];quota=Path('/sys/fs/cgroup/cpu.max').read_text().split();assert len(cpus)==8 and (quota[0]=='max' or int(quota[0])/int(quota[1])>=8)
 os.sched_setaffinity(0,cpus)
 assert platform.machine()=='x86_64'
 libc=ctypes.CDLL(None,use_errno=True);mask=ctypes.c_ulong(1<<node);rc=libc.syscall(238,2,ctypes.byref(mask),ctypes.c_ulong(64))
 policy={'requested':'MPOL_BIND','node':node,'syscall_rc':rc,'errno':ctypes.get_errno() if rc else 0,'effective':'inherited MPOL_BIND' if rc==0 else 'default local first-touch after affinity on one NUMA node; hard memory bind denied'}
 gpus=query(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.free','--format=csv,noheader,nounits']).strip().splitlines();assert len(gpus)==1,'one GPU allocation required'
 parts=[v.strip() for v in gpus[0].split(',')];uuid=parts[1];assert 'H100' in parts[2] and float(parts[3])>=80000
 os.environ['CUDA_VISIBLE_DEVICES']=uuid
 before=snap();assert not before['gpu_processes'].strip(),'competing GPU process'
 env=dict(memory_policy=policy,hostname=socket.gethostname(),affinity=cpus,numa_node=node,cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text(),memory_max=Path('/sys/fs/cgroup/memory.max').read_text(),cpuset=Path('/sys/fs/cgroup/cpuset.cpus.effective').read_text(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),lscpu=query(['lscpu']),gpu_uuid=uuid,gpu_inventory=gpus,cuda=query(['nvcc','--version']),snapshot=before)
 w.save(R/'environment/frozen.json',env)
 w.plan=w.plan|dict(resources=env,formal_allowed=True,formal_resource_contract_frozen=True,run=str(R),formal_block_reason=None,source_code_binding=frozen,qualification_case_order=['bnn','gemm'],original_index_rule='actual live ABI unsigned32 with signed cell index; historical offline STRICT N<2^23 not silently imposed on live ALT; code unchanged')
 w.R=R;w.save(R/'experiment_plan.json',w.plan);w.save(R/'runner_identity.json',w.identity(os.getpid()))
 for case in ['bnn','gemm']:
  meta=w.read(H/'metadata'/f'{case}.json');free=int(float(parts[4])*1024**2)
  if meta['cuda_estimated_bytes']>free*.8 or meta['invalid_admitted_cost_nodes'] or meta['N']>=2**32 or meta['E']>=2**32-1 or meta['cells']>=2**31 or meta['J']>65535:
   statuses[case]=dict(status='CAPACITY_OR_INPUT_BLOCKED',metadata=meta);flush();continue
  qual={};statuses[case]=dict(status='QUALIFYING');flush()
  for arm in ['stock','pipeline','alt_cpu','alt_cuda']:
   state=snap();assert not state['gpu_processes'].strip(),'competing GPU process before qualification'
   x=w.run(case,arm,'qualification',capture=arm.startswith('alt'));x['resource_before']=state;x['resource_after']=snap();rows.append(x);qual[arm]=x;flush()
   if not x['qualified']:
    statuses[case]=dict(status='QUALIFICATION_FAILED',arm=arm,returncode=x['returncode']);flush();break
  if len(qual)!=4 or not all(x['qualified'] for x in qual.values()):continue
  gatecase=dict(strict_map_equal=qual['stock']['map_sha256']==qual['pipeline']['map_sha256'],alt_complete_samples_and_input_equal=qual['alt_cpu'].get('native_capture',{}).get('sha256')==qual['alt_cuda'].get('native_capture',{}).get('sha256') and bool(qual['alt_cpu'].get('native_capture')),alt_maps_equal=qual['alt_cpu']['map_sha256']==qual['alt_cuda']['map_sha256'],cuda_live_cpu_full_verify=len(qual['alt_cuda']['pair_verify_lines'])==1 and 'all_pairs_equal=1' in qual['alt_cuda']['pair_verify_lines'][0],qor_all=all(qos(x,[qual['stock'],qual['pipeline']]) for x in qual.values()))
  w.save(R/'receipts'/f'{case}_qualification_gate.json',gatecase)
  if not all(gatecase.values()):statuses[case]=dict(status='QUALIFICATION_FAILED',gates=gatecase);flush();continue
  statuses[case]=dict(status='FORMAL_RUNNING',qualified=True);flush();failed=False
  for rep,order in enumerate(w.plan['orders']):
   group={}
   for arm in order:
    state=snap();assert not state['gpu_processes'].strip(),'competing GPU process before formal run'
    x=w.run(case,arm,str(rep),formal=True);x['repeat']=rep;x['gpu_uuid']=uuid;x['resource_before']=state;x['resource_after']=snap();x['qualification_map_equal']=x['map_sha256']==qual[arm]['map_sha256'];rows.append(x);group[arm]=x;flush()
    if not x['qualified'] or not x['qualification_map_equal']:failed=True;break
   if failed:break
   for x in group.values():x['paired_qor_passed']=qos(x,[group['stock'],group['pipeline']]);x['paired_group_complete']=True
   flush()
   if not all(x['paired_qor_passed'] for x in group.values()):failed=True;break
  statuses[case]=dict(status='FORMAL_FAILED' if failed else 'COMPLETE',qualified=True,formal_rows=sum(x['case']==case and x['formal'] for x in rows));flush()
 w.save(R/'finished.json',dict(status='COMPLETED_BOUNDED_MATRIX',case_status=statuses,formal_processes_completed=sum(x['formal'] for x in rows),FPGA_auto_resume_allowed=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
except Exception as e:
 flush();w.save(R/'finished.json',dict(status='INFRASTRUCTURE_OR_GATE_FAILURE',reason=str(e),case_status=statuses,formal_processes_completed=sum(x['formal'] for x in rows),FPGA_auto_resume_allowed=False));raise
