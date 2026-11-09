"""A3 live qualification then A4 bounded same-worker native matrix."""
import os,json,sys,time,subprocess,shutil,re,socket
from pathlib import Path
import run_native_flat_baseline as b
from scaling_common import metrics,vpr_command
from report_native_joint import log_evidence
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();o=Path(sys.argv[2]).resolve();o.mkdir(exist_ok=False);plan=b.read(R/'results/native_flat_baseline_20261105/plan.json');cases=b.read(R/'results/native_flat_baseline_20261105/summary.json')['cases'];cases['s38417']={'case':{'path':str(R/'results/native_cpu_evidence_20261102/prepared/s38417_s1/vpr_case.json')}}
binary=r/'native_build/bin/vpr_flat';libs={'alt_cpu':r/'libcpu61.so','alt_cuda':o.parent/'libcuda61.so'};rows=[]
def execute(cmd,d,env,timeout=600):
 begin=time.monotonic()
 with (d/'process.log').open('w') as f:
  try:p=subprocess.run(list(map(str,cmd)),cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout);rc=p.returncode
  except subprocess.TimeoutExpired:rc=124
 return dict(command=list(map(str,cmd)),returncode=rc,Process_wall_s=time.monotonic()-begin,metrics=metrics((d/'process.log').read_text(errors='replace')))
def run(case_name,arm,repeat,qualification=False):
 case=b.read(cases[case_name]['case']['path']);d=o/f'{case_name}_{arm}_{repeat}';d.mkdir()
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],d/name)
 exe=plan['binaries']['original']['path'] if arm=='stock' else str(binary)
 cmd=b.cpu_command(exe,case,d,{'router':'parallel'},8,iterations=200);b.set_option(cmd,'--write_router_lookahead',d/'wire_map.bin');b.set_option(cmd,'--generate_rr_node_overuse_report','off');env=b.environment(plan,'stock' if arm=='stock' else 'flat',d,False)
 for k in list(env):
  if k.startswith(('OMP_','VPR_LA_','R61_')):env.pop(k)
 if arm.startswith('alt'):
  env.update(VPR_LA_BACKEND=str(libs[arm]),VPR_LA_CONTEXTS='8',VPR_LA_MODE='ALT_BUCKET_FP32_V1',VPR_LA_BUCKET_SHIFT='20')
  if qualification:env.update(R61_CAPTURE=str(d/'native_input'),R61_VERIFY_CPU='1')
 rec=dict(case=case_name,backend=arm,shift=20 if arm.startswith('alt') else None,representation='original',repeat=repeat,qualification_diagnostic=qualification,hostname=socket.gethostname(),affinity=sorted(os.sched_getaffinity(0)),scope_version='R6_1_NATIVE_BUILD_V1',binary_sha256=sha256(exe),library_sha256=sha256(libs[arm]) if arm.startswith('alt') else None,input_bindings=case['inputs'])
 (d/'invocation.json').write_text(json.dumps(rec|dict(command=cmd),indent=2));rec.update(execute(cmd,d,env));log=(d/'process.log').read_text(errors='replace');rec['backend_lines']=[x for x in log.splitlines() if x.startswith('R61_BACKEND')];rec['identity_lines']=[x for x in log.splitlines() if x.startswith('R61_IDENTITY')];rec['pair_verify_lines']=[x for x in log.splitlines() if x.startswith('R61_NATIVE_PAIR_VERIFY')];rec['live_lines']=[x for x in log.splitlines() if x.startswith('LA_LIVE')]
 scope=re.findall(r'R61_NATIVE_BUILD scope_version=R6_1_NATIVE_BUILD_V1 E2_wall_s=([\d.]+)',log);native=re.findall(r'Computing router lookahead map took ([\d.]+) seconds',log);rec['E2_s']=float(scope[0]) if len(scope)==1 else float(native[0]) if arm=='stock' and len(native)==1 else None;rec['E2_precision_s']=1e-9 if scope else .01
 e1=re.findall(r'R61_BACKEND .*?E1_wall_s=([\d.]+)',log);rec['E1_wall_s']=float(e1[0]) if len(e1)==1 else None
 rec['dispatch_verified']=('CPU_GLOBAL_SCHEDULER=flat' in log) if arm=='optimized' else bool(len(rec['backend_lines'])==1 and ('backend=CUDA' if arm=='alt_cuda' else 'backend=CPU') in rec['backend_lines'][0] and 'shift=20' in rec['backend_lines'][0]) if arm.startswith('alt') else 'LA_LIVE' not in log
 if qualification and arm=='alt_cuda':rec['dispatch_verified'] &=len(rec['pair_verify_lines'])==1
 wire=d/'wire_map.bin';rec['map_sha256']=sha256(wire) if wire.exists() else None;rec['zero_overuse']=log_evidence(d)['last_observed_overused_nodes']==0
 if rec['returncode']==0 and rec['metrics']['routing_success'] and rec['metrics']['full_check']:
  route=d/'routed.route';before=sha256(route);check=d/'independent';check.mkdir();ic=vpr_command(plan['binaries']['original']['path'],case,d,200,route=False);b.set_option(ic,'--num_workers',8);rec['independent']=execute(ic,check,env);rec['readback_identity']=before==sha256(route);rec['route_sha256']=before
 rec['qualified']=bool(rec['returncode']==0 and rec['metrics']['full_check'] and rec['zero_overuse'] and rec['dispatch_verified'] and rec.get('readback_identity') and rec['independent']['returncode']==0 and rec['independent']['metrics']['full_check'] and all(rec['metrics'][k]==rec['independent']['metrics'][k] for k in ['critical_path_ns','wirelength']))
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:assert sha256(d/name)==case['inputs'][role]['sha256']
 cap=d/'native_input.bin'
 if cap.exists():rec['native_capture']=dict(path=str(cap),sha256=sha256(cap))
 rows.append(rec);(o/'rows.json').write_text(json.dumps(rows,indent=2));print(case_name,arm,repeat,rec['qualified'],rec['E2_s'],flush=True);return rec
# One uninstrumented fresh-call diagnostic per A5 case/shift; not formal speed rows.
phase_controls=[]
for case in ['tseng_export','bnn_export']:
 for shift in [0,20]:
  path=R/'results/lookahead_accel_20261108T125500Z'/case/'workload.bin';cmd=[o.parent/'cuda61',path,shift,0,o.parent/f'{case}_s{shift}_reference.bin',o/'phase_control_output.bin','original',0]
  with (o/f'phase_control_{case}_{shift}.log').open('w') as f:
   proc=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,timeout=300)
  assert proc.returncode==0
  z=[json.loads(x) for x in (o/f'phase_control_{case}_{shift}.log').read_text().splitlines() if x.startswith('{')]
  phase_controls.append(dict(case=case,shift=shift,measurements=z,command=list(map(str,cmd))))
(o/'phase_controls.json').write_text(json.dumps(phase_controls,indent=2))

# Directed compact CUDA lifecycle/admission checks, outside formal timing.
error_rows=[]
for case in ['zero_cycle','empty_targets','empty_batch','unreachable','overflow','negative','nan','subnormal','truncated','cost2048']:
 for shift in [0,20]:
  path=r/'cost2048.bin' if case=='cost2048' else r/'compact_errors'/f'{case}.bin'
  ref=r/'compact_errors'/f'{case}_s{shift}.out';dest=o/f'error_{case}_{shift}.out'
  cmd=[o.parent/'cuda61',path,shift,0,ref,dest,'compact',0]
  with (o/f'error_{case}_{shift}.log').open('w') as f:
   proc=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,timeout=30)
  expected=0 if case in ['zero_cycle','empty_targets','empty_batch','unreachable'] else 10
  error_rows.append(dict(case=case,shift=shift,expected=expected,returncode=proc.returncode,output_published=dest.exists(),command=list(map(str,cmd))))
  (o/'cuda_errors.json').write_text(json.dumps(error_rows,indent=2))
  assert proc.returncode==expected and (expected==0 or not dest.exists()),'CUDA error contract'

# Representation isolation: same reusable solver, original fields versus compact.
# This small additional control is separate from unchanged R6 G-basic.
representation_control=[]
for case in ['tseng_export','bnn_export']:
 for rep in range(3):
  path=R/'results/lookahead_accel_20261108T125500Z'/case/'workload.bin';cmd=[o.parent/'cuda61',path,20,3,o.parent/f'{case}_s20_reference.bin',o/'refactor_output.bin','original',0]
  with (o/f'{case}_original_solver_p{rep}.log').open('w') as f:
   p=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,timeout=300)
  assert p.returncode==0
  lines=[json.loads(x) for x in (o/f'{case}_original_solver_p{rep}.log').read_text().splitlines() if x.startswith('{')]
  representation_control.append(dict(case=case,process=rep,kind='gpu_original_refactor',measurements=lines,command=list(map(str,cmd))))
(o/'representation_control.json').write_text(json.dumps(representation_control,indent=2))
(o/'runner_binding.json').write_text(json.dumps(dict(path=str(Path(__file__).resolve()),sha256=sha256(Path(__file__))),indent=2))

# A3 only follows actual A2 passes. The caller verifies the complete A2 receipt.
for case in ['s38417','bnn']:
 q=run(case,'alt_cuda','qualification',True)
 assert q['qualified'],'native CUDA qualification failed'
 a2=next(x for x in json.load(open(r/'native_cpu_qualification_b/runs.json')) if x['case']==case and x['arm']=='alt_s20')
 assert q['map_sha256']==a2['map_sha256'],'live same-input CPU/CUDA native map differs'
 assert q['metrics']['critical_path_ns']<=a2['metrics']['critical_path_ns']*1.05 and q['metrics']['wirelength']<=a2['metrics']['wirelength']*1.05
for rep in range(3):
 for case in ['s38417','bnn']:
  group={}
  order=['stock','optimized','alt_cpu','alt_cuda'];order=order[rep:]+order[:rep]
  for arm in order:group[arm]=run(case,arm,rep)
  control=group['optimized']
  for arm,x in group.items():
   x['paired_qor_passed']=bool(x['qualified'] and control['qualified'] and x['metrics']['critical_path_ns']<=1.05*control['metrics']['critical_path_ns'] and x['metrics']['wirelength']<=1.05*control['metrics']['wirelength'])
  (o/'rows.json').write_text(json.dumps(rows,indent=2))
(o/'finished.json').write_text(json.dumps(dict(status='completed',rows=len(rows),all_full_checks=all(x['qualified'] for x in rows))))
