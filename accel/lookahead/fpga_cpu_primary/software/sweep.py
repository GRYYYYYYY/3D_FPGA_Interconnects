"""Bounded, sequential and source-bound CPU sweep. Never launches GPU/EDA work."""
from pathlib import Path
import argparse,collections,datetime,fcntl,hashlib,json,os,socket,statistics,subprocess,time
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'accel/lookahead/fpga_cpu_primary/software';R=ROOT/'results/fpga_cpu_primary_20261115/software_a';OLD=ROOT.parent/'3D_FPGA_Interconnects_DESCRIPTOR_FRONT/results/fpga_descriptor_front_20261114';D=OLD/'descriptor_a'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def activity():
 rows={}
 for p in Path('/proc').glob('[0-9]*'):
  try:
   name=(p/'comm').read_text().strip();st=(p/'stat').read_text().rsplit(')',1)[1].split()
   if st[0]=='Z':continue
   rows[int(p.name)]={'name':name,'ticks':int(st[11])+int(st[12]),'birth':int(st[19]),'argv':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')}
  except (OSError,ValueError):pass
 return rows
def changed(a,b,exclude=()):
 out=[]
 for pid,x in b.items():
  if pid in exclude or pid not in a or a[pid]['birth']!=x['birth']:continue
  delta=x['ticks']-a[pid]['ticks']
  if delta>2 and x['name']in ['model','vivado','xsim','xelab','xvlog','cpu','cp_cpu','cc1plus','g++','convert','vpr_flat','vpr']:
   out.append({**x,'pid':pid,'cpu_seconds':delta/os.sysconf('SC_CLK_TCK')})
 return out
def cg():return Path('/sys/fs/cgroup/cpu.stat').read_text()
def prepare():
 R.mkdir(parents=True,exist_ok=True)
 if (R/'binding.json').exists():
  b=json.loads((R/'binding.json').read_text());assert sha(R/'bin/cp_cpu')==b['binary_sha256']
  for p,h in b['source_sha256'].items():assert sha(ROOT/p)==h
  return b
 old=json.loads((D/'binding.json').read_text());includes=[ROOT/'accel/lookahead/include',ROOT/'accel/lookahead/round6_1'];depcmd=['g++','-std=c++17','-MM',*['-I'+str(x)for x in includes],str(S/'cpu.cpp')];files=subprocess.check_output(depcmd,text=True).replace('\\\n',' ').split(':',1)[1].split();src=R/'source'
 for p in sorted({Path(x).resolve()for x in files}|{S/'sweep.py'}):
  dest=src/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 (R/'bin').mkdir(exist_ok=True);command=['g++','-O3','-std=c++17','-ffp-contract=off','-fopenmp',*['-I'+str(src/x.relative_to(ROOT))for x in includes],str(src/S.relative_to(ROOT)/'cpu.cpp'),'-o',str(R/'bin/cp_cpu')]
 with (R/'build.log').open('w')as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
 inputs={}
 for case in ['bnn_export','lstm_s2']:
  x=old['inputs'][case];conv=D/'cases'/case;cr=json.loads((D/'receipts'/(case+'_conversion.json')).read_text());files={str(conv/f):sha(conv/f)for f in ['descriptors.bin','edges.bin']}
  assert all(cr['output_sha256'][p]==h for p,h in files.items());assert sha(x['workload'])==x['workload_sha256'];assert sha(x['golden'])==x['golden_sha256'];inputs[case]={**x,'conversion_dir':str(conv),'backing_sha256':files}
 b={'base':'3c7f96e6037030949b729240977c2ced373843c6','build_command':command,'dependency_command':depcmd,'compiler':subprocess.check_output(['g++','--version'],text=True),'binary_sha256':sha(R/'bin/cp_cpu'),'source_sha256':{str(p.relative_to(src)):sha(p)for p in src.rglob('*')if p.is_file()},'original_cpu_source_sha256':sha(ROOT/'accel/lookahead/fpga_descriptor_front/software/cpu.cpp'),'old_binding_sha256':sha(D/'binding.json'),'inputs':inputs}
 dump(R/'binding.json',b);return b
def main():
 with (R.parent/'.software_sweep.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);b=prepare();physical=[];seen=set();top=[]
  for cpu in sorted(os.sched_getaffinity(0)):
   p=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology');socketid=int((p/'physical_package_id').read_text());core=int((p/'core_id').read_text());top.append({'cpu':cpu,'socket':socketid,'core':core})
   if (socketid,core)not in seen:seen.add((socketid,core));physical.append(cpu)
  assert len(physical)==64;thread_points=[8,32,64]
  configuration={'created_utc':now(),'research_goal':'CPU_PRIMARY_GPU_COMPARATOR','hostname':socket.gethostname(),'lscpu':subprocess.check_output(['lscpu'],text=True),'allowed_affinity':sorted(os.sched_getaffinity(0)),'physical_representatives':physical,'topology':top,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'thread_points':thread_points,'selection_rule':'best mean of 3 independent process means per case; retain all points; compare historical qualified8 separately','binding_rule':'one logical CPU per physical core; first8/32 on socket0;64 across both sockets; no SMT','memory_rule':'shared immutable input MPOL_INTERLEAVE over selected sockets; private scratch first-touch MPOL_LOCAL by bound worker; actual maps saved','schedule':'dynamic complete samples;40 jobs limits active solve threads to40 even with64 workers','OMP_WAIT_POLICY':'PASSIVE','GOMP_SPINCOUNT':'0','independent_processes':3,'repetitions_per_process':4,'warmups_per_process':1,'formal_repetitions_per_process':3,'scope':'RESIDENT_COMPLETE_BATCH_V2; sample resets/search/FP32/whole-pair merges/all waves/output memory writes+thread join included; graph load/packing/strict persisted-image validation/scratch allocation outside; output golden comparison/filesystem export outside','no_claim':'not unlimited-host strongest CPU, no board FPGA result','binary_sha256':b['binary_sha256']}
  if (R/'experiment_config.json').exists():assert json.loads((R/'experiment_config.json').read_text())['binary_sha256']==b['binary_sha256']
  else:dump(R/'experiment_config.json',configuration)
  # Refuse any existing source-bound active executable rather than duplicate it.
  assert not any(str(R/'bin/cp_cpu')in x['argv']for x in activity().values())
  a=activity();time.sleep(1);busy=changed(a,activity());dump(R/'initial_activity.json',{'utc':now(),'active_competitors':busy});assert not busy,busy
  rows=[]
  for threads in thread_points:
   cpus=physical[:threads];nodes={x['socket']for x in top if x['cpu']in cpus};mask=sum(1<<n for n in nodes)
   env={**os.environ,'OMP_NUM_THREADS':str(threads),'OMP_PROC_BIND':'close','OMP_PLACES':','.join('{'+str(c)+'}'for c in cpus),'OMP_DYNAMIC':'FALSE','OMP_WAIT_POLICY':'PASSIVE','GOMP_SPINCOUNT':'0','CP_SHARED_NODEMASK':str(mask)}
   for case in ['bnn_export','lstm_s2']:
    inp=b['inputs'][case]
    for process in range(3):
     stem=f'{case}_t{threads}_p{process}';dest=R/stem;receipt=R/(stem+'.receipt.json')
     if receipt.exists():
      x=json.loads(receipt.read_text());assert x['output_exact']and x['binary_sha256']==b['binary_sha256']and x['timing_contention_qualified'];rows.append(x);continue
     assert not dest.exists(),'preserve failed/incomplete run, inspect before retry'
     cmd=['taskset','-c',','.join(map(str,cpus)),str(R/'bin/cp_cpu'),inp['workload'],inp['golden'],inp['conversion_dir'],'8',str(threads),'4','0',str(dest),str(process)]
     start=now();before=cg();observed=[];last=activity();resource_log=[]
     with (R/(stem+'.log')).open('x')as log:
      p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT);ident=activity().get(p.pid);dump(R/(stem+'.running.json'),{'pid':p.pid,'birth':ident,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'command':cmd,'utc':start})
      while p.poll()is None:
       time.sleep(1);cur=activity();observed.extend(changed(last,cur,[p.pid]));last=cur
       try:resource_log.append({'utc':now(),'status':Path(f'/proc/{p.pid}/status').read_text(),'cgroup_cpu_stat':cg()})
       except FileNotFoundError:pass
      rc=p.returncode
     exact=(dest/'output.bin').exists()and sha(dest/'output.bin')==inp['golden_sha256'];metrics=[json.loads(l)for l in (dest/'metrics.jsonl').read_text().splitlines()]if(dest/'metrics.jsonl').exists()else[];vals=[v['resident_seconds']for v in metrics if not v['warmup']]
     x={'case':case,'threads':threads,'process':process,'command':cmd,'start_utc':start,'end_utc':now(),'returncode':rc,'cpu_affinity':cpus,'shared_numa_mask':mask,'binary_sha256':b['binary_sha256'],'workload_sha256':inp['workload_sha256'],'golden_sha256':inp['golden_sha256'],'output_sha256':sha(dest/'output.bin')if exact else None,'output_exact':exact,'observed_active_competitors':observed,'timing_contention_qualified':not observed,'cgroup_cpu_stat_before':before,'cgroup_cpu_stat_after':cg(),'retained_seconds':vals,'process_mean_seconds':statistics.mean(vals)if vals else None,'process_median_seconds':statistics.median(vals)if vals else None,'all_repetitions_exact':all(m['full_output_exact']for m in metrics),'receipt_path':str(receipt)}
     dump(receipt,x);dump(R/(stem+'.resource_samples.json'),resource_log);print('PROCESS_DONE',case,threads,process,vals,'contention',len(observed),flush=True);assert rc==0 and exact and len(vals)==3 and not observed
     rows.append(x)
  summary={'created_utc':now(),'scope':'RESIDENT_COMPLETE_BATCH_V2','all_outputs_exact':all(x['output_exact']for x in rows),'all_timing_contention_qualified':all(x['timing_contention_qualified']for x in rows),'statistical_unit':'3 independent processes per config/case,3 formal within each; not9 independent samples','rows':rows,'configurations':[],'selected':{}}
  for case in ['bnn_export','lstm_s2']:
   configs=[]
   for threads in thread_points:
    xs=[x for x in rows if x['case']==case and x['threads']==threads];means=[x['process_mean_seconds']for x in xs];v={'case':case,'threads':threads,'process_means':means,'mean_of_process_means_seconds':statistics.mean(means),'sample_sd_of_process_means_seconds':statistics.stdev(means),'min_process_mean_seconds':min(means),'max_process_mean_seconds':max(means),'median_of_process_medians_seconds':statistics.median(x['process_median_seconds']for x in xs),'retained_seconds_by_process':[x['retained_seconds']for x in xs],'all_output_exact':True};configs.append(v);summary['configurations'].append(v)
   summary['selected'][case]=min(configs,key=lambda x:x['mean_of_process_means_seconds'])
  dump(R/'terminal.json',summary);print('SWEEP_COMPLETE',summary['selected'],flush=True)
if __name__=='__main__':main()
