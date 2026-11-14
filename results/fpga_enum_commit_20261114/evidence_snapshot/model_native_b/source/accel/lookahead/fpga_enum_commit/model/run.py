"""Freeze and execute the new continuous finite model. Completed samples are checkpoints.

Only sample state is independent: each sample performs physical canonical writes,
PV/directory/output/bitmap initialization and drains output ACKs. The explicit
sample-clear control edge resets arbiters, so separate CPU processes start at the
same hardware state. FPGA cycles are SUMMED in sample order, never CPU wall time.
"""
from pathlib import Path
import argparse,subprocess,json,hashlib,datetime,concurrent.futures,os,time
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'accel/lookahead/fpga_enum_commit/model';R=ROOT/'results/fpga_enum_commit_20261114';OUT=R/'model_native_b'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
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
 inp=d['inputs'][case];name=case+('_jitter' if stress else '');root=OUT/'runs'/name;root.mkdir(parents=True,exist_ok=True);rp=root/(f'receipt_{q}.json')
 if rp.exists():
  old=json.loads(rp.read_text())
  if old['returncode']==0 and old['output_exact']:
   assert sha(Path(old['output_path']))==old['output_sha256'];return old
 run=root;attempt=1
 while (run/f'sample_{q}').exists():attempt+=1;run=root/f'attempt_{attempt}'
 run.mkdir(exist_ok=True);cmd=[str(OUT/'bin/model'),inp['workload'],inp['golden'],str(run),str(q),str(q+1)]+(['jitter'] if stress else [])
 start=now();log=root/f'sample_{q}_attempt_{attempt}.log'
 with log.open('x') as f:
  p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);dump(root/f'running_{q}_attempt_{attempt}.json',{'pid':p.pid,'command':cmd,'start_utc':start,'binary_sha256':d['binary_sha256']});rc=p.wait()
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

def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['small','full']);ap.add_argument('--workers',type=int,default=12);a=ap.parse_args();d=prepare();tasks=[]
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
if __name__=='__main__':main()
