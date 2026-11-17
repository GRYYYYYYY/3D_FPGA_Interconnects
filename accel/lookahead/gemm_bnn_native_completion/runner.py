"""Finite post-V1 runner. No imports of historical orchestration scripts."""
from pathlib import Path
import os,sys,json,time,subprocess,shutil,fcntl,socket,re,hashlib,datetime
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from scaling_common import metrics,vpr_command
from report_native_joint import log_evidence
# Avoid ambiguous prepare import from repository scripts: local helpers below.
def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def option(c,k,v):
 if k in c:c[c.index(k)+1]=str(v)
 else:c.extend([k,str(v)])
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  s=(p/'stat').read_text().rsplit(') ',1)[1].split();return dict(pid=pid,start_ticks=int(s[19]),pgid=int(s[2]),session=int(s[3]),state=s[0],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),cmdline=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),cwd=os.readlink(p/'cwd'))
 except OSError:return None
plan=read(H/'experiment_plan.json');R=Path(plan['run']);inputs=read(H/'input_manifest.json');binding=read(H/'source_binding.json');bins=binding['binary'];runtime=read(H/'runtime.json')
def environment(arm,d,capture=False):
 env={k:v for k,v in os.environ.items() if not k.startswith(('VPR_','H3D_GPU_','R61_','R62_','OMP_'))}
 env.update(LC_ALL='C',LD_LIBRARY_PATH=runtime['library_directory'],VPR_HYBRID_LOOKAHEAD_TASKS='0' if arm=='stock' else '1',VPR_HYBRID_LOOKAHEAD_PARALLEL='0' if arm=='stock' else '1')
 if arm!='stock':env['VPR_CPU_GLOBAL_SCHEDULER']='pipeline' if arm=='pipeline' else 'flat'
 if arm in ['alt_cpu','alt_cuda','metadata']:
  env.update(VPR_LA_MODE=plan['mode'],VPR_LA_CONTEXTS='8',VPR_LA_BUCKET_SHIFT='20',VPR_LA_BACKEND=str(H/'metadata_backend.so') if arm=='metadata' else bins[arm]['path'])
  if arm=='metadata':env['GEMM_BNN_METADATA']=str(d/'metadata.json')
  if capture:env['R61_CAPTURE']=str(d/'native_input')
  if capture and arm=='alt_cuda':env['R61_VERIFY_CPU']='1'
 return env
def execute(c,d,env,timeout):
 begin=time.monotonic()
 with (d/'process.log').open('w') as f:
  actual=c
  p=subprocess.Popen(actual,cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);time.sleep(.02);save(d/'process_identity.json',identity(p.pid))
  try:rc=p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:p.kill();p.wait();rc=124
 elapsed=time.monotonic()-begin
 text=(d/'process.log').read_text(errors='replace');return dict(returncode=rc,Process_wall_s=elapsed,metrics=metrics(text),command=c,executed_command=actual)
def run(case,arm,label,metadata=False,capture=False,formal=False):
 cse=inputs[case]['case'];d=R/('formal' if formal else 'qualification')/case/label/arm;d.mkdir(parents=True,exist_ok=False)
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(cse['inputs'][role]['path'],d/name)
 exe=bins['stock' if arm=='stock' else 'pipeline'];assert sha(exe['path'])==exe['sha256']
 if arm.startswith('alt'):assert sha(bins[arm]['path'])==bins[arm]['sha256']
 cmd=vpr_command(exe['path'],cse,d,200);option(cmd,'--num_workers',8);option(cmd,'--router_algorithm','parallel');option(cmd,'--router_lookahead','map');option(cmd,'--write_router_lookahead',d/'wire_map.bin');option(cmd,'--generate_rr_node_overuse_report','off')
 env=environment(arm,d,capture)
 rec=dict(case=case,arm=arm,label=label,formal=formal,cohort_id=socket.gethostname()+'_post_V1_a',affinity=sorted(os.sched_getaffinity(0)),binary_sha256=exe['sha256'],input_bindings=cse['inputs'],library_sha256=bins[arm]['sha256'] if arm.startswith('alt') else None,environment={k:v for k,v in env.items() if k.startswith(('VPR_','R61_'))},start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 save(d/'invocation.json',rec|dict(command=cmd));rec.update(execute(cmd,d,env,plan['timeout_seconds'][case]));text=(d/'process.log').read_text(errors='replace')
 if metadata:
  rec['metadata_observer_passed']=rec['returncode']==86 and (d/'metadata.json').exists()
  if rec['metadata_observer_passed']:rec['metadata']=read(d/'metadata.json')
 else:
  hi=re.findall(r'R61_NATIVE_BUILD scope_version=R6_1_NATIVE_BUILD_V1 E2_wall_s=([\d.]+)',text);stock=re.findall(r'Computing router lookahead map took ([\d.]+) seconds',text)
  rec['E2_s']=float(hi[0]) if len(hi)==1 else float(stock[0]) if arm=='stock' and len(stock)==1 else None
  rec['E2_precision_s']=1e-9 if hi else .01;rec['map_sha256']=sha(d/'wire_map.bin') if (d/'wire_map.bin').exists() else None
  rec['backend_lines']=[x for x in text.splitlines() if x.startswith('R61_BACKEND')];rec['live_lines']=[x for x in text.splitlines() if x.startswith('LA_LIVE')];rec['pair_verify_lines']=[x for x in text.splitlines() if x.startswith('R61_NATIVE_PAIR_VERIFY')]
  rec['dispatch_verified']=('CPU_GLOBAL_SCHEDULER=pipeline' in text and not rec['live_lines']) if arm=='pipeline' else (not rec['live_lines']) if arm=='stock' else (len(rec['backend_lines'])==len(rec['live_lines'])==1 and ('backend=CPU' if arm=='alt_cpu' else 'backend=CUDA') in rec['backend_lines'][0] and 'fallback=0' in rec['backend_lines'][0])
  rec['zero_overuse']=log_evidence(d).get('last_observed_overused_nodes')==0
  if rec['returncode']==0 and rec['metrics']['routing_success'] and rec['metrics']['full_check']:
   route=d/'routed.route';before=sha(route);ind=d/'independent';ind.mkdir();ic=vpr_command(bins['stock']['path'],cse,d,200,route=False);option(ic,'--num_workers',8)
   rec['independent']=execute(ic,ind,environment('stock',ind),plan['timeout_seconds'][case]);rec['route_sha256']=before;rec['readback_identity']=sha(route)==before
  rec['qualified']=bool(rec['returncode']==0 and rec['metrics']['full_check'] and rec['zero_overuse'] and rec['dispatch_verified'] and rec.get('readback_identity') and rec['independent']['returncode']==0 and rec['independent']['metrics']['full_check'] and all(rec['metrics'][k]==rec['independent']['metrics'][k] for k in ['critical_path_ns','wirelength']))
  if capture and (d/'native_input.bin').exists():rec['native_capture']=dict(path=str(d/'native_input.bin'),bytes=(d/'native_input.bin').stat().st_size,sha256=sha(d/'native_input.bin'))
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:assert sha(d/name)==cse['inputs'][role]['sha256']
 save(d/'measurement.json',rec);print(case,arm,label,rec.get('metadata_observer_passed',rec.get('qualified')),flush=True);return rec
if __name__=='__main__':
 lock=(R/'runner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 gate=read(R/'receipts/V1_publication.json');assert gate['new_experiments_allowed']
 os.sched_setaffinity(0,plan['resources']['affinity']);save(R/'runner_identity.json',identity(os.getpid()))
 phase=sys.argv[1]
 if phase=='metadata':
  for case in plan['metadata_order']:
   row=run(case,'metadata','metadata',metadata=True);assert row['metadata_observer_passed']
 elif phase=='cpu-qualification':
  for case in plan['case_order']:
   meta=read(R/'qualification'/case/'metadata/metadata/metadata.json')
   if meta['N']>=2**32 or meta['E']>=2**32-1 or meta['invalid_admitted_cost_nodes']:
    save(R/'receipts'/(case+'_input_gate.json'),dict(status='UNSUPPORTED_INPUT',reason='outside actual native ABI or numeric admission',metadata=meta));continue
   rows={arm:run(case,arm,'cpu_qualification',capture=arm=='alt_cpu') for arm in ['stock','pipeline','alt_cpu']}
   for arm,x in rows.items():x['qor_passed']=x['qualified'] and all(x['metrics'][k]<=1.05*rows[control]['metrics'][k] for control in ['stock','pipeline'] for k in ['critical_path_ns','wirelength'])
   save(R/'receipts'/(case+'_cpu_gate.json'),dict(rows=rows,strict_map_equal=rows['stock']['map_sha256']==rows['pipeline']['map_sha256'],gpu_qualification='RESOURCE_BLOCKED',formal=False))
 else:raise SystemExit('Formal phase requires a separate verified GPU resource freeze and complete qualification; never run CPU-only formal fragments')
 save(R/'receipts'/(phase+'_complete.json'),dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),formal_processes_completed=0))
