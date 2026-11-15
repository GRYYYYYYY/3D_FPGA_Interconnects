#!/usr/bin/env python3
"""Frozen CPU-primary structural model runs. No full batch by default."""
from pathlib import Path
import argparse,concurrent.futures,datetime,hashlib,json,os,subprocess,shutil
ROOT=Path(__file__).resolve().parents[4]
S=Path(__file__).resolve().parent
CFG=S.parent/'experiment_config.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def save(p,x):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def birth(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except OSError:return None
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('run_id');ap.add_argument('--mhz',type=float,required=True);ap.add_argument('--scenario',choices=['base','conservative_diagnostic'],default='base');ap.add_argument('--jitter',action='store_true');ap.add_argument('--trace',action='store_true');ap.add_argument('--cases',nargs='+',default=['native_d3_w8','native_d4_w8']);ap.add_argument('--samples',type=int,nargs='+');ap.add_argument('--workers',type=int,default=2);ap.add_argument('--memory-offset',type=int);ap.add_argument('--reuse-build',type=Path);ap.add_argument('--full-authorized',action='store_true',help='Only after final frequency selection and explicit coordinator go')
 a=ap.parse_args();assert '/' not in a.run_id and a.run_id.startswith('model_');assert a.mhz>0 and a.workers>0
 config=json.loads(CFG.read_text());scenario=next(s for s in config['memory_scenarios']if s['name']==a.scenario)
 if any(config['inputs'][c]['jobs']==40 for c in a.cases):assert a.full_authorized,'FULL_BATCH_NOT_AUTHORIZED_BEFORE_FREQUENCY_SELECTION'
 out=ROOT/'results/fpga_cpu_primary_20261115'/a.run_id;out.mkdir(parents=True,exist_ok=True)
 lock=out/'runner.lock'
 if lock.exists():
  old=json.loads(lock.read_text());assert birth(old['pid'])!=old['birth'],'RUNNER_ALREADY_LIVE';lock.unlink()
 with lock.open('x')as f:json.dump({'pid':os.getpid(),'birth':birth(os.getpid()),'utc':now()},f)
 try:
  inc=[ROOT/'accel/lookahead/include',ROOT/'accel/lookahead/round6_1'];deps=subprocess.check_output(['g++','-std=c++17','-MM',*['-I'+str(p)for p in inc],str(S/'main.cpp')],text=True).replace('\\\n',' ').split(':',1)[1].split()
  paths={Path(p).resolve() for p in deps}|{S/'run.py',CFG};current={str(p.relative_to(ROOT)):sha(p)for p in sorted(paths)}
  options={'frequency_mhz':a.mhz,'scenario':scenario,'jitter':a.jitter,'trace':a.trace,'cases':a.cases,'samples':a.samples,'memory_offset':a.memory_offset}
  binding_path=out/'binding.json'
  if binding_path.exists():
   binding=json.loads(binding_path.read_text());assert binding['source_sha256']==current,'SOURCE_CHANGED_NEW_RUN_ID_REQUIRED';assert binding['options']==options,'OPTIONS_CHANGED_NEW_RUN_ID_REQUIRED';assert sha(out/'model')==binding['binary_sha256']
  else:
   src=out/'source'
   for p in paths:
    dst=src/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(p.read_bytes())
   cmd=['g++','-O3','-std=c++17','-ffp-contract=off',*['-I'+str(src/p.relative_to(ROOT))for p in inc],str(src/S.relative_to(ROOT)/'main.cpp'),'-o',str(out/'model')]
   if a.reuse_build:
    reused=json.loads((a.reuse_build/'binding.json').read_text());assert reused['source_sha256']==current,'REUSE_SOURCE_MISMATCH';assert sha(a.reuse_build/'model')==reused['binary_sha256'];shutil.copyfile(a.reuse_build/'model',out/'model');(out/'model').chmod(0o755);cmd=reused['compile_command']
    save(out/'reused_build.json',{'path':str(a.reuse_build.resolve()),'binding_sha256':sha(a.reuse_build/'binding.json')})
   else:
    with (out/'compile.log').open('w')as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
   binding={'base':'3c7f96e6037030949b729240977c2ced373843c6','utc':now(),'compile_command':cmd,'compiler':subprocess.check_output(['g++','--version'],text=True),'source_sha256':current,'binary_sha256':sha(out/'model'),'options':options,'rtl_model_calibrated':False,'complete_kernel_clock_qualified':False,'qualified_clock_mhz':None,'board_measured':False,'scope':'CPU_PRIMARY finite structural L1 model; full-top cycle calibration pending; no average correction'};save(binding_path,binding)
  work=[]
  for case in a.cases:
   inp=config['inputs'][case];assert sha(Path(inp['workload']))==inp['workload_sha256'];assert sha(Path(inp['golden']))==inp['golden_sha256']
   for q in a.samples if a.samples is not None else range(inp['jobs']):
    assert 0<=q<inp['jobs'];work.append((case,q,inp))
  offsets={case:(a.memory_offset if a.memory_offset is not None else config['inputs'][case]['jobs']+2)for case in a.cases}
  def one(item):
   case,q,inp=item;d=out/case;d.mkdir(exist_ok=True);receipt=d/f'receipt_{q}.json';sample=d/f'sample_{q}'
   if receipt.exists():
    x=json.loads(receipt.read_text());assert x['returncode']==0 and x['output_exact'];assert x['binary_sha256']==binding['binary_sha256'];assert sha(sample/'output.bin')==x['output_sha256'];
    if a.jitter:assert x['memory_cycle_offset']==offsets[case];offsets[case]+=x['cycles']
    return x
   assert not sample.exists(),'PARTIAL_SAMPLE_NEEDS_NEW_RUN_ID'
   cmd=[str(out/'model'),inp['workload'],inp['golden'],str(d),str(q),str(q+1),'L1',str(a.mhz),str(scenario['latency_ns']),str(scenario['issue_interval_ns'])]
   if a.jitter:cmd.append('jitter')
   start=now()
   with (d/f'sample_{q}.log').open('w')as log:
    env=os.environ.copy();env.update({'CP_MODEL_TRACE':'1'}if a.trace else{});env['CP_MEM_OFFSET']=str(offsets[case]if a.jitter else(a.memory_offset or 0));p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);save(d/f'process_{q}.json',{'pid':p.pid,'birth':birth(p.pid),'command':cmd,'start':start});rc=p.wait()
   x={'case':case,'sample':q,'command':cmd,'start':start,'end':now(),'returncode':rc,'binary_sha256':binding['binary_sha256'],'workload_sha256':inp['workload_sha256'],'golden_sha256':inp['golden_sha256'],'output_exact':False,'memory_cycle_offset':offsets[case]if a.jitter else(a.memory_offset or 0)}
   if rc==0:
    term=json.loads((sample/'terminal.json').read_text());assert term['output_exact'];data=(sample/'output.bin').read_bytes();gold=Path(inp['golden']).read_bytes();assert data==gold[q*inp['cells']*8:(q+1)*inp['cells']*8]
    finite=json.loads((sample/'finite.json').read_text());phase=json.loads((sample/'core_phases.json').read_text());assert sum(phase['phase_cycles'])==finite['cycles'];x.update(output_exact=True,output_sha256=sha(sample/'output.bin'),cycles=finite['cycles'],phase_cycles=phase['phase_cycles'])
   save(receipt,x);
   if a.jitter and rc==0:offsets[case]+=x['cycles']
   print(case,q,'PASS'if rc==0 else'FAIL',flush=True);return x
  if a.jitter:rows=[one(item)for item in work]
  else:
   with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers)as pool:rows=list(pool.map(one,work))
  groups={}
  for case in a.cases:
   selected=sorted([x for x in rows if x['case']==case],key=lambda x:x['sample']);groups[case]={'samples':len(selected),'all_pass':all(x['output_exact']for x in selected),'cycles':sum(x.get('cycles',0)for x in selected)}
  terminal={'utc':now(),'all_pass':all(x['returncode']==0 and x['output_exact']for x in rows),'samples':len(rows),'results':rows,'cases':groups,'rtl_model_calibrated':False,'board_measured':False,'qualified_clock_mhz':None};save(out/'terminal.json',terminal)
  if not terminal['all_pass']:raise SystemExit(1)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':main()
