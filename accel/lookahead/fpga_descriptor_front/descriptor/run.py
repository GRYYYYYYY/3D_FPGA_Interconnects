"""Bound, restart-safe descriptor conversion and packed CPU functional runs.

No formal software timing is launched here. All these wall times may contend.
"""
from pathlib import Path
import concurrent.futures,datetime,fcntl,hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
S=ROOT/'accel/lookahead/fpga_descriptor_front'
R=ROOT/'results/fpga_descriptor_front_20261114'
OUT=R/'descriptor_a'
OLD=ROOT.parent/'3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_20261114/model_native_d/binding.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def identity(pid):
 try:
  p=Path('/proc')/str(pid);s=(p/'stat').read_text().rsplit(')',1)[1].split()
  return {'pid':pid,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'start_ticks':int(s[19]),'argv':[os.fsdecode(x) for x in (p/'cmdline').read_bytes().split(b'\0') if x]}
 except OSError:return None
def execute(cmd,receipt,log,extra=None):
 receipt=Path(receipt);log=Path(log);running=receipt.with_suffix('.running.json')
 if receipt.exists():
  d=json.loads(receipt.read_text());assert d['command']==cmd and d['returncode']==0,(receipt,d.get('returncode'))
  for p,h in d.get('output_sha256',{}).items():assert sha(p)==h,p
  return d
 if running.exists():
  old=json.loads(running.read_text());live=identity(old['process_identity']['pid'])
  if live and live['start_ticks']==old['process_identity']['start_ticks'] and live['boot_id']==old['process_identity']['boot_id']:raise RuntimeError('Original task active: '+str(running))
  raise RuntimeError('Unfinished attempt retained; choose a new result root: '+str(running))
 log.parent.mkdir(parents=True,exist_ok=True);start=now()
 with log.open('x') as f:
  p=subprocess.Popen(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT);save(running,{'start_utc':start,'command':cmd,'process_identity':identity(p.pid)});rc=p.wait()
 d={'command':cmd,'cwd':str(ROOT),'start_utc':start,'end_utc':now(),'returncode':rc,'binary_sha256':sha(cmd[0]),'timing_contention_qualified':False,**(extra or {})};save(receipt,d)
 if rc:raise RuntimeError('Failed; preserve '+str(receipt))
 return d
def prepare():
 if (OUT/'binding.json').exists():
  d=json.loads((OUT/'binding.json').read_text())
  for p,h in d['source_sha256'].items():assert sha(OUT/'source'/p)==h,p
  for p,h in d['binary_sha256'].items():assert sha(OUT/'bin'/p)==h,p
  return d
 OUT.mkdir(parents=True,exist_ok=False);(OUT/'bin').mkdir();src=OUT/'source'
 paths=set();includes=[ROOT/'accel/lookahead/include',ROOT/'accel/lookahead/round6_1']
 builds={}
 for name,p in [('convert',S/'descriptor/convert.cpp'),('test',S/'descriptor/test.cpp'),('cpu',S/'software/cpu.cpp')]:
  dep=subprocess.check_output(['g++','-std=c++17','-MM',*['-I'+str(i) for i in includes],str(p)],text=True).replace('\\\n',' ').split(':',1)[1].split()
  paths.update(Path(x).resolve() for x in dep)
  builds[name]=p
 paths.update(p for d in ['descriptor','software'] for p in (S/d).iterdir() if p.is_file())
 for p in paths:
  dest=src/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 commands={}
 for name,p in builds.items():
  cmd=['g++','-O3','-std=c++17','-ffp-contract=off','-fopenmp',*['-I'+str(src/i.relative_to(ROOT)) for i in includes],str(src/p.relative_to(ROOT)),'-o',str(OUT/'bin'/name)]
  with (OUT/(name+'_build.log')).open('x') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
  save(OUT/(name+'_build_receipt.json'),{'command':cmd,'returncode':rc,'utc':now()});assert rc==0,name
  commands[name]=cmd
 inputs=json.loads(OLD.read_text())['inputs']
 for case,inp in inputs.items():
  assert sha(inp['workload'])==inp['workload_sha256'];assert sha(inp['golden'])==inp['golden_sha256']
 d={'base':'ccec3da64b4c5be643809c2bdda94145c4bb8187','source_sha256':{str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()},'build_commands':commands,'binary_sha256':{p.name:sha(p) for p in (OUT/'bin').iterdir()},'compiler':subprocess.check_output(['g++','--version'],text=True),'inputs':inputs,'input_binding_path':str(OLD),'input_binding_sha256':sha(OLD)}
 save(OUT/'binding.json',d);return d
def convert(case,inp,fmt=None):
 name=case+('_format16' if fmt else '');dest=OUT/'cases'/name
 cmd=[str(OUT/'bin/convert'),inp['workload'],str(dest)]+([str(fmt)] if fmt else [])
 receipt=OUT/'receipts'/(name+'_conversion.json')
 d=execute(cmd,receipt,OUT/'logs'/(name+'_conversion.log'),{'case':case,'workload_sha256':inp['workload_sha256']})
 a=json.loads((dest/'admission.json').read_text());assert a['eligible_sequence_exact'];assert a['independently_decoded_records']==a['nodes']*a['samples'];assert a['descriptor_bytes']==(dest/'descriptors.bin').stat().st_size
 d['output_sha256']={str(p):sha(p) for p in dest.iterdir() if p.is_file()};d['full_input_admission']=a;save(receipt,d);return dest,a
def functional(case,inp,dest,a):
 name=dest.name;out=R/'software_functional_a'/name
 cmd=[str(OUT/'bin/cpu'),inp['workload'],inp['golden'],str(dest),str(a['actual_format_bytes']),'4','1','1',str(out),'functional_contention_unqualified']
 receipt=OUT/'receipts'/(name+'_cpu.json')
 d=execute(cmd,receipt,OUT/'logs'/(name+'_cpu.log'),{'case':case,'workload_sha256':inp['workload_sha256'],'golden_sha256':inp['golden_sha256'],'scope':'functional complete batch, construction/cache validation measured separately; not formal CPU timing'})
 assert sha(out/'output.bin')==inp['golden_sha256']
 d['output_exact']=True;d['output_sha256']={str(p):sha(p) for p in out.iterdir() if p.is_file()};save(receipt,d);return d
def main():
 R.mkdir(parents=True,exist_ok=True)
 with (R/'.descriptor_a.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);binding=prepare()
  execute([str(OUT/'bin/test')],OUT/'boundary_receipt.json',OUT/'boundary.json')
  results=[]
  for case,inp in binding['inputs'].items():
   dest,a=convert(case,inp);results.append(functional(case,inp,dest,a))
   if case in ['native_d3_w8','native_d4_w8']:
    dest,a=convert(case,inp,16);results.append(functional(case,inp,dest,a))
  save(OUT/'terminal.json',{'utc':now(),'status':'FUSION_FUNCTIONALLY_VERIFIED','all_pass':True,'native_graphs':4,'native_samples':100,'extra_fallback_sample_runs':20,'functional_receipts':results,'formal_cpu_timing':False,'gpu_runs':0})
if __name__=='__main__':main()
