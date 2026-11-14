"""Freeze and execute the new continuous finite model. Completed samples are checkpoints.

Only sample state is independent: each sample performs physical canonical writes,
PV/directory/output/bitmap initialization and drains output ACKs. The explicit
sample-clear control edge resets arbiters, so separate CPU processes start at the
same hardware state. FPGA cycles are SUMMED in sample order, never CPU wall time.
"""
from pathlib import Path
import argparse,subprocess,json,hashlib,datetime,concurrent.futures,os,time,fcntl
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'accel/lookahead/fpga_enum_commit/model';R=ROOT/'results/fpga_enum_commit_20261114';OUT=R/'model_native_d'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def process_identity(pid):
 """Linux PID reuse-safe identity; None means absent or already a zombie."""
 proc=Path('/proc')/str(int(pid))
 try:
  stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
  command=[os.fsdecode(x) for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
  if stat[0]=='Z' or not command:return None
  start_ticks=int(stat[19]);boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  with Path('/proc/stat').open() as f:boot_seconds=next(int(x.split()[1]) for x in f if x.startswith('btime '))
  started=boot_seconds+start_ticks/os.sysconf('SC_CLK_TCK')
  return {'pid':int(pid),'command':command,'boot_id':boot_id,'start_ticks':start_ticks,'process_start_unix':started}
 except (FileNotFoundError,ProcessLookupError):return None

def guard_running_record(path,binary_sha256):
 """Refuse a matching live run (or ambiguous reuse), never launch a replacement."""
 try:record=json.loads(Path(path).read_text())
 except (ValueError,OSError) as exc:raise RuntimeError('Cannot verify running record; preserve and inspect '+str(path)) from exc
 try:live=process_identity(record['pid'])
 except (PermissionError,KeyError,ValueError,OSError) as exc:raise RuntimeError('Cannot verify original process identity in '+str(path)) from exc
 if live is None:return
 if live['command']!=record.get('command'):return # PID reused by a different executable/argument vector.
 saved=record.get('process_identity')
 if saved:
  same_start=all(live[k]==saved.get(k) for k in ['boot_id','start_ticks'])
 else:
  # Legacy receipts have UTC supervisor start but no kernel birth tick. Boot
  # seconds are integer-rounded, so tolerate 5s while always refusing a live
  # identical command even when this legacy start cannot be established.
  try:same_start=abs(live['process_start_unix']-datetime.datetime.fromisoformat(record['start_utc']).timestamp())<=5
  except (KeyError,ValueError):same_start=False
 reason='matching live process' if same_start else 'ambiguous PID/start identity with identical live command'
 if record.get('binary_sha256')!=binary_sha256:reason+='; source/binary binding differs'
 raise RuntimeError('Refusing duplicate launch: '+reason+' pid='+str(live['pid'])+' record='+str(path)+'; keep the original process and inspect its existing progress/receipt.')

def guard_live_sample(root,q,binary_sha256):
 for path in sorted(Path(root).glob(f'running_{q}_attempt_*.json')):guard_running_record(path,binary_sha256)

def guard_live_run(binary_sha256):
 # Check every existing identity before submitting ANY new sample, including a
 # legacy supervisor whose not-yet-started samples are still in its queue.
 for path in sorted((OUT/'runs').rglob('running_*.json')):guard_running_record(path,binary_sha256)
 binary=str(OUT/'bin/model')
 for proc in Path('/proc').glob('[0-9]*'):
  try:live=process_identity(int(proc.name))
  except (PermissionError,OSError,ValueError):continue
  if live and live['command'][0]==binary:raise RuntimeError('Refusing duplicate model supervisor: original frozen binary is active pid='+proc.name+'; inspect existing handles/receipts.')

@contextmanager
def exclusive_lock(path):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('a') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise RuntimeError('Another original supervisor/sample owns '+str(path)+'; do not duplicate it.')
  try:yield
  finally:fcntl.flock(lock,fcntl.LOCK_UN)

def prepare():
 if (OUT/'binding.json').exists():
  d=json.loads((OUT/'binding.json').read_text());assert sha(OUT/'bin/model')==d['binary_sha256'];return d
 OUT.mkdir(exist_ok=False);src=OUT/'source';src.mkdir();(OUT/'bin').mkdir()
 includes=[ROOT/'accel/lookahead/include',ROOT/'accel/lookahead/round6_1']
 depcmd=['g++','-std=c++17','-MM',*['-I'+str(p) for p in includes],str(S/'main.cpp')]
 files=subprocess.check_output(depcmd,text=True).replace('\\\n',' ').split(':',1)[1].split()
 paths={Path(x).resolve() for x in files}|{p for p in S.iterdir() if p.is_file()}
 for p in sorted(paths):
  dest=src/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 command=['g++','-O3','-std=c++17','-ffp-contract=off',*['-I'+str(src/p.relative_to(ROOT)) for p in includes],str(src/S.relative_to(ROOT)/'main.cpp'),'-o',str(OUT/'bin/model')]
 start=now()
 with (OUT/'build.log').open('x') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
 old=json.loads((R/'baseline/profile_a/reused_binding.json').read_text());inputs={}
 for x in old['input_receipts']:
  name=Path(x['command'][3]).name;w=Path(x['command'][1]);gold=Path(x['command'][2]);assert sha(w)==x['workload_sha256'] and sha(gold)==x['golden_sha256'];p=json.loads((R/'baseline/profile_a'/name/'physical_profile.json').read_text());inputs[name]={'workload':str(w),'workload_sha256':sha(w),'golden':str(gold),'golden_sha256':sha(gold),'jobs':p['jobs'],'cells':p['cells'],'baseline_profile_sha256':sha(R/'baseline/profile_a'/name/'physical_profile.json')}
 d={'base':'1e312d6e4ffc5ea96f25c0b97931ad028e710584','build_command':command,'build_start':start,'build_end':now(),'build_returncode':0,'compiler':subprocess.check_output(['g++','--version'],text=True),'binary_sha256':sha(OUT/'bin/model'),'source_sha256':{str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()},'inputs':inputs,'sample_independence':'Every sample starts with explicit sample_clear edge, deterministic arbiter reset, all canonical initialization requests, real PV16384/output4096/directory freepool8192/bitmap256 initialization costs. No cross-sample graph cache or mutable state. Output ACK drained. Sum cycles in hardware sample order.','calibration':'enum RAM/raw/FIFO scan/fragment cycle-exact; front/pending/scratch/top calibration incomplete','complete_kernel_clock_qualified':False,'board_measured':False}
 dump(OUT/'binding.json',d);return d

def execute(d,case,q,stress=False):
 name=case+('_jitter' if stress else '');root=OUT/'runs'/name
 with exclusive_lock(root/f'.sample_{q}.lock'):
  return _execute_locked(d,case,q,stress,root)

def _execute_locked(d,case,q,stress,root):
 inp=d['inputs'][case];rp=root/(f'receipt_{q}.json')
 if rp.exists():
  old=json.loads(rp.read_text())
  if old['returncode']==0 and old['output_exact']:
   assert sha(Path(old['output_path']))==old['output_sha256'];return old
 guard_live_sample(root,q,d['binary_sha256'])
 run=root;attempt=1
 while (run/f'sample_{q}').exists():attempt+=1;run=root/f'attempt_{attempt}'
 run.mkdir(exist_ok=True);cmd=[str(OUT/'bin/model'),inp['workload'],inp['golden'],str(run),str(q),str(q+1)]+(['jitter'] if stress else [])
 start=now();log=root/f'sample_{q}_attempt_{attempt}.log'
 with log.open('x') as f:
  p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);dump(root/f'running_{q}_attempt_{attempt}.json',{'pid':p.pid,'command':cmd,'start_utc':start,'binary_sha256':d['binary_sha256'],'process_identity':process_identity(p.pid)});rc=p.wait()
 sd=run/f'sample_{q}';term=json.loads((sd/'terminal.json').read_text()) if (sd/'terminal.json').exists() else {};output=sd/'output.bin'
 x={'case':case,'sample':q,'jitter':stress,'command':cmd,'start_utc':start,'end_utc':now(),'returncode':rc,'binary_sha256':d['binary_sha256'],'workload_sha256':inp['workload_sha256'],'golden_sha256':inp['golden_sha256'],'output_exact':rc==0 and term.get('output_exact',False),'output_path':str(output),'output_sha256':sha(output) if output.exists() else None,'finite_path':str(sd/'finite.json'),'progress_path':str(sd/'progress.jsonl'),'log':str(log)}
 dump(rp,x);print('TERMINAL',case,q,'jitter',stress,'rc',rc,flush=True);return x

def aggregate(d,case,receipts):
 inp=d['inputs'][case];rows=sorted([x for x in receipts if x['case']==case and not x['jitter']],key=lambda x:x['sample']);assert len(rows)==inp['jobs'];passed=all(x['returncode']==0 and x['output_exact'] for x in rows)
 value={'case':case,'scope':'complete continuous finite conditional model; samples independently simulated from identical explicitly initialized states, hardware cycles sequential sum','samples':rows,'all_pass':passed,'source_binding':'binding.json','complete_kernel_clock_qualified':False,'RTL_calibration_complete':False,'board_measured':False,'fpga_seconds':None}
 if passed:
  data=b''.join(Path(x['output_path']).read_bytes() for x in rows);out=OUT/(case+'_output.bin');out.write_bytes(data);assert sha(out)==inp['golden_sha256'];fs=[json.loads(Path(x['finite_path']).read_text()) for x in rows];cycles=sum(x['cycles'] for x in fs);traffic=[[sum(x['traffic'][k][p] for x in fs) for p in range(32)] for k in range(11)]
  fields=['parents','candidates','waves','zero_degree','spills','scratch_final_reads','canonical_lines','changed_lines','events','pop_transactions','stale'];counts={k:sum(x[k] for x in fs) for k in fields};baseline=json.loads((R/'baseline/profile_a'/case/'physical_profile.json').read_text());expected={'parents':baseline['parents'],'candidates':baseline['candidates'],'canonical_lines':sum(baseline['requests_by_kind_port'][5]),'changed_lines':sum(baseline['requests_by_kind_port'][6])}
  value.update({'cycles':cycles,'assumed_frequency_hz':200000000,'memory_contract':{'latency_ns':80,'gap_ns':5},'conditional_predicted_seconds':cycles/200000000,'counts':counts,'traffic':traffic,'functional_work_counts_match_frozen_profile':all(counts[k]==v for k,v in expected.items()),'expected_semantic_counts':expected,'full_output_sha256':sha(out),'golden_sha256':inp['golden_sha256'],'per_sample_cycles':[x['cycles'] for x in fs],'directory_peak_per_bank':max(max(x['directory_bank_peaks']) for x in fs),'spill_id_peak_per_bank':max(b['spill_id_peak'] for x in fs for b in x['bank_stats'])})
 dump(OUT/(case+'_summary.json'),value);return value

def _main_locked():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['small','full']);ap.add_argument('--workers',type=int,default=12);a=ap.parse_args();d=prepare();guard_live_run(d['binary_sha256']);tasks=[]
 for case,inp in d['inputs'].items():
  if (case in ['bnn_export','lstm_s2'])!=(a.mode=='full'):continue
  for q in range(inp['jobs']):tasks.append((case,q,False))
  if a.mode=='small':
   for q in range(inp['jobs']):tasks.append((case,q,True))
 start=now()
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:receipts=list(pool.map(lambda x:execute(d,*x),tasks))
 summaries=[]
 for case in sorted({x[0] for x in tasks}):summaries.append(aggregate(d,case,receipts))
 term={'mode':a.mode,'start_utc':start,'end_utc':now(),'all_pass':all(x['returncode']==0 and x['output_exact'] for x in receipts),'sample_runs':len(receipts),'results':receipts,'summaries':[case+'_summary.json' for case in sorted({x[0] for x in tasks})]};dump(OUT/(a.mode+'_terminal.json'),term)
 assert term['all_pass']
def main():
 with exclusive_lock(OUT.parent/('.'+OUT.name+'_run.lock')):
  return _main_locked()
if __name__=='__main__':main()
