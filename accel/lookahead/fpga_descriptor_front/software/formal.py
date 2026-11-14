"""Run only in a parent-selected quiet window; does not request or launch GPUs.

Example (parent coordination required, existing experiments must finish first):
 python3 accel/lookahead/fpga_descriptor_front/software/formal.py --isolated-window
Three independent processes/case, each one warm-up + three retained repetitions.
"""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,os,socket,statistics,subprocess,time
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_descriptor_front_20261114';D=R/'descriptor_a'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def activity():
 rows={}
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   name=(p/'comm').read_text().strip()
   if name not in ['model','vivado','xsim','xelab','xvlog','cpu','cc1plus','g++','convert','vpr_flat','vpr']:continue
   stat=(p/'stat').read_text().rsplit(')',1)[1].split()
   rows[int(p.name)]={'name':name,'ticks':int(stat[11])+int(stat[12]),'start_ticks':int(stat[19]),'argv':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')}
  except OSError:pass
 return rows
def changed(a,b,exclude=()):
 return [{**v,'pid':pid,'cpu_seconds':(v['ticks']-a.get(pid,{}).get('ticks',v['ticks']))/os.sysconf('SC_CLK_TCK')} for pid,v in b.items() if pid not in exclude and v['ticks']-a.get(pid,{}).get('ticks',v['ticks'])>2]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--isolated-window',action='store_true',required=True);ap.add_argument('--out',default='software_formal_a');args=ap.parse_args()
 assert args.out.startswith('software_formal_') and '/' not in args.out
 with (R/'.software_formal.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out=R/args.out;assert not out.exists();out.mkdir()
  bind=json.loads((D/'binding.json').read_text());binary=D/'bin/cpu';assert sha(binary)==bind['binary_sha256']['cpu']
  cpus=[];seen=set()
  for cpu in sorted(os.sched_getaffinity(0)):
   p=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology');key=((p/'physical_package_id').read_text(),(p/'core_id').read_text())
   if key not in seen:seen.add(key);cpus.append(cpu)
   if len(cpus)==8:break
  assert len(cpus)==8
  initial=activity();time.sleep(1);idle=activity();busy=changed(initial,idle)
  environment={'utc':now(),'hostname':socket.gethostname(),'affinity':cpus,'OMP_NUM_THREADS':8,'OMP_PROC_BIND':'close','OMP_PLACES':'cores','lscpu':subprocess.check_output(['lscpu'],text=True),'before_processes':idle,'before_active_competitors':busy,'binary_sha256':sha(binary),'binding_sha256':sha(D/'binding.json'),'parent_selected_isolated_window':True,'independent_processes_per_case':3,'warmup_repetitions_per_process':1,'formal_repetitions_per_process':3,'measurement_scope':'RESIDENT_COMPLETE_BATCH_V2; prepared packed backing already resident; each sample state initialization, search and output memory stores included; filesystem output export excluded'}
  dump(out/'environment.json',environment)
  if busy:raise RuntimeError('Active competing model/EDA/software workload; preserve rejected window, schedule later')
  env={**os.environ,'OMP_NUM_THREADS':'8','OMP_PROC_BIND':'close','OMP_PLACES':'cores'};rows=[]
  for case in ['bnn_export','lstm_s2']:
   inp=bind['inputs'][case];conv=D/'cases'/case;cr=json.loads((D/'receipts'/(case+'_conversion.json')).read_text());a=json.loads((conv/'admission.json').read_text())
   for file in ['descriptors.bin','edges.bin']:assert sha(conv/file)==cr['output_sha256'][str(conv/file)]
   for process in range(3):
    dest=out/f'{case}_p{process}';cmd=['taskset','-c',','.join(map(str,cpus)),str(binary),inp['workload'],inp['golden'],str(conv),str(a['actual_format_bytes']),'8','4','0',str(dest),str(process)]
    start=now();observed=[];last=activity()
    with (out/(dest.name+'.log')).open('x') as log:
     p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT);dump(out/(dest.name+'.running.json'),{'pid':p.pid,'command':cmd,'start_utc':start})
     while p.poll() is None:
      time.sleep(1);current=activity();observed.extend(changed(last,current,[p.pid]));last=current
     rc=p.returncode
    d={'command':cmd,'start_utc':start,'end_utc':now(),'returncode':rc,'observed_active_competitors':observed,'timing_contention_qualified':not observed,'source_binding_sha256':sha(D/'binding.json'),'binary_sha256':sha(binary),'workload_sha256':inp['workload_sha256'],'golden_sha256':inp['golden_sha256'],'output_sha256':sha(dest/'output.bin') if (dest/'output.bin').exists() else None}
    d['output_exact']=d['output_sha256']==inp['golden_sha256'];dump(out/(dest.name+'.receipt.json'),d);assert rc==0 and d['output_exact']
    metrics=[json.loads(line) for line in (dest/'metrics.jsonl').read_text().splitlines()];vals=[v['resident_seconds'] for v in metrics if not v['warmup']];assert len(vals)==3
    rows.append({'case':case,'process':process,'retained_seconds':vals,'process_mean_seconds':statistics.mean(vals),'process_median_seconds':statistics.median(vals),'timing_contention_qualified':not observed,'receipt':str(out/(dest.name+'.receipt.json'))})
    print('CPU_PROCESS_DONE',case,process,vals,flush=True)
  summary={'utc':now(),'all_output_exact':True,'all_processes_isolated':all(r['timing_contention_qualified'] for r in rows),'rows':rows,'cases':{}}
  for case in ['bnn_export','lstm_s2']:
   x=[r for r in rows if r['case']==case];summary['cases'][case]={'independent_processes':3,'within_process_repetitions':3,'mean_of_process_means_seconds':statistics.mean(r['process_mean_seconds'] for r in x),'median_of_process_medians_seconds':statistics.median(r['process_median_seconds'] for r in x),'not_nine_independent_processes':True}
  dump(out/'terminal.json',summary)
if __name__=='__main__':main()
