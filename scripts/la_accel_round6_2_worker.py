"""Single owner, finite frozen native holdout plus Pipeline supplement and one profile."""
import os,json,sys,time,subprocess,shutil,re,socket
from pathlib import Path
import run_native_flat_baseline as b
from scaling_common import metrics,vpr_command
from report_native_joint import log_evidence
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();o=r/'worker';o.mkdir(exist_ok=False)
old=R/'results/lookahead_accel_round6_1_20261109T160000Z'
plan=b.read(R/'results/native_flat_baseline_20261105/plan.json');frozen=b.read(r/'holdout_plan.json');cases=b.read(R/'results/native_flat_baseline_20261105/summary.json')['cases'];cases['s38417']={'case':{'path':str(R/'results/native_cpu_evidence_20261102/prepared/s38417_s1/vpr_case.json')}};cases['lstm_s2']={'case':{'path':frozen['holdout_case_file']}}
binary=old/'native_build/bin/vpr_flat';libs={'alt_cpu':old/'libcpu61.so','alt_cuda':old/'gpu_worker/libcuda61.so'};rows=[]
pools={};seen=set()
for cpu in sorted(os.sched_getaffinity(0)):
 d=Path(f'/sys/devices/system/cpu/cpu{cpu}');key=((d/'topology/physical_package_id').read_text(),(d/'topology/core_id').read_text())
 if key in seen:continue
 seen.add(key);pools.setdefault(sorted(d.glob('node*'))[0].name,[]).append(cpu)
cpus=sorted(pools.values(),key=lambda x:(-len(x),x))[0][:8];quota=Path('/sys/fs/cgroup/cpu.max').read_text().split();assert len(cpus)==8 and (quota[0]=='max' or int(quota[0])/int(quota[1])>=8);os.sched_setaffinity(0,cpus)
(o/'worker.json').write_text(json.dumps(dict(host=socket.gethostname(),affinity=cpus,cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text(),runner_sha256=sha256(__file__),holdout_plan_sha256=sha256(r/'holdout_plan.json'),cohort='R6.2 new worker; historical Pipeline supplement is not a cross-worker speed comparison'),indent=2))
for name,cmd in [('gpu',['nvidia-smi']),('cpu',['lscpu']),('nvcc',['nvcc','--version'])]:
 with (o/(name+'.log')).open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
def execute(cmd,d,env,timeout=600):
 begin=time.monotonic()
 with (d/'process.log').open('w') as f:
  try:p=subprocess.run(list(map(str,cmd)),cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout);rc=p.returncode
  except subprocess.TimeoutExpired:rc=124
 return dict(command=list(map(str,cmd)),returncode=rc,Process_wall_s=time.monotonic()-begin,metrics=metrics((d/'process.log').read_text(errors='replace')))
def run(case_name,arm,repeat,qualification=False,exe_override=None,lib_override=None):
 case=b.read(cases[case_name]['case']['path']);d=o/f'{case_name}_{arm}_{repeat}';d.mkdir()
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],d/name)
 exe=exe_override or (plan['binaries']['original']['path'] if arm=='stock' else str(binary));lib=lib_override or libs.get(arm)
 cmd=b.cpu_command(exe,case,d,{'router':'parallel'},8,iterations=200);b.set_option(cmd,'--write_router_lookahead',d/'wire_map.bin');b.set_option(cmd,'--generate_rr_node_overuse_report','off');env=b.environment(plan,'stock' if arm=='stock' else 'pipeline' if arm=='pipeline' else 'flat',d,False)
 for k in list(env):
  if k.startswith(('OMP_','VPR_LA_','R61_')):env.pop(k)
 if arm.startswith('alt'):
  env.update(VPR_LA_BACKEND=str(lib),VPR_LA_CONTEXTS='8',VPR_LA_MODE='ALT_BUCKET_FP32_V1',VPR_LA_BUCKET_SHIFT='20')
  if qualification:env.update(R61_CAPTURE=str(d/'native_input'),R61_VERIFY_CPU='1')
 rec=dict(case=case_name,backend=arm,shift=20 if arm.startswith('alt') else None,representation='original',repeat=repeat,qualification_diagnostic=qualification,hostname=socket.gethostname(),affinity=sorted(os.sched_getaffinity(0)),scope_version='R6_1_NATIVE_BUILD_V1',binary_sha256=sha256(exe),library_sha256=sha256(lib) if arm.startswith('alt') else None,input_bindings=case['inputs'])
 (d/'invocation.json').write_text(json.dumps(rec|dict(command=cmd),indent=2));rec['effective_env']={k:v for k,v in env.items() if k.startswith(('VPR_','R61_','OMP_'))};rec.update(execute(cmd,d,env));log=(d/'process.log').read_text(errors='replace');rec['backend_lines']=[x for x in log.splitlines() if x.startswith('R61_BACKEND')];rec['identity_lines']=[x for x in log.splitlines() if x.startswith('R61_IDENTITY')];rec['pair_verify_lines']=[x for x in log.splitlines() if x.startswith('R61_NATIVE_PAIR_VERIFY')];rec['live_lines']=[x for x in log.splitlines() if x.startswith('LA_LIVE')]
 scope=re.findall(r'R61_NATIVE_BUILD scope_version=R6_1_NATIVE_BUILD_V1 E2_wall_s=([\d.]+)',log);native=re.findall(r'Computing router lookahead map took ([\d.]+) seconds',log);rec['E2_s']=float(scope[0]) if len(scope)==1 else float(native[0]) if arm=='stock' and len(native)==1 else None;rec['E2_precision_s']=1e-9 if scope else .01
 e1=re.findall(r'R61_BACKEND .*?E1_wall_s=([\d.]+)',log);rec['E1_wall_s']=float(e1[0]) if len(e1)==1 else None
 rec['dispatch_verified']=('CPU_GLOBAL_SCHEDULER='+arm in log) if arm in ['flat','pipeline'] else bool(len(rec['backend_lines'])==1 and ('backend=CUDA' if arm.startswith('alt_cuda') else 'backend=CPU') in rec['backend_lines'][0] and 'shift=20' in rec['backend_lines'][0]) if arm.startswith('alt') else 'LA_LIVE' not in log
 if qualification and arm.startswith('alt_cuda'):rec['dispatch_verified'] &=len(rec['pair_verify_lines'])==1
 wire=d/'wire_map.bin';rec['map_sha256']=sha256(wire) if wire.exists() else None;rec['zero_overuse']=log_evidence(d)['last_observed_overused_nodes']==0
 if rec['returncode']==0 and rec['metrics']['routing_success'] and rec['metrics']['full_check']:
  route=d/'routed.route';before=sha256(route);check=d/'independent';check.mkdir();ic=vpr_command(plan['binaries']['original']['path'],case,d,200,route=False);b.set_option(ic,'--num_workers',8);rec['independent']=execute(ic,check,env);rec['readback_identity']=before==sha256(route);rec['route_sha256']=before
 rec['diagnostics']=[x for x in log.splitlines() if 'no fanin' in x];rec['qualified']=bool(rec['returncode']==0 and rec['metrics']['full_check'] and rec['zero_overuse'] and rec['dispatch_verified'] and rec.get('readback_identity') and rec['independent']['returncode']==0 and rec['independent']['metrics']['full_check'] and all(rec['metrics'][k]==rec['independent']['metrics'][k] for k in ['critical_path_ns','wirelength']))
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:assert sha256(d/name)==case['inputs'][role]['sha256']
 cap=d/'native_input.bin'
 if cap.exists():rec['native_capture']=dict(path=str(cap),sha256=sha256(cap))
 rows.append(rec);(o/'rows.json').write_text(json.dumps(rows,indent=2));print(case_name,arm,repeat,rec['qualified'],rec['E2_s'],flush=True);return rec

def qos(x,base):
 return bool(x['qualified'] and base['qualified'] and all(x['metrics'][k]<=1.05*base['metrics'][k] for k in ['critical_path_ns','wirelength']))
def flush(): (o/'rows.json').write_text(json.dumps(rows,indent=2))
try:
 # Reused frozen native binaries; no representation/kernel qualification matrix rerun.
 hist=b.read(old/'evidence_snapshot/native_e2.json')['rows']
 for rep in range(3):
  for case in ['s38417','bnn']:
   x=run(case,'pipeline',rep);base=next(v for v in hist if v['case']==case and v['backend']=='optimized' and v['repeat']==rep)
   x['frozen_Flat_map_equal']=x['map_sha256']==base['map_sha256'];x['frozen_Flat_qor_passed']=qos(x,base);flush()
   assert x['qualified'] and x['frozen_Flat_map_equal'] and x['frozen_Flat_qor_passed'],'Pipeline qualification'
 qual={arm:run('lstm_s2',arm,'qualification',True) for arm in frozen['qualifications']}
 gates={arm:qos(x,qual['flat']) and qos(x,qual['stock']) for arm,x in qual.items()}
 maps=qual['stock']['map_sha256']==qual['flat']['map_sha256']==qual['pipeline']['map_sha256'] and qual['alt_cpu']['map_sha256']==qual['alt_cuda']['map_sha256']
 (o/'qualification_gate.json').write_text(json.dumps(dict(qor=gates,map_families_equal=maps),indent=2))
 if all(gates.values()) and maps:
  for rep in range(3):
   order=frozen['formal_order_rotation'];order=order[rep:]+order[:rep];group={arm:run('lstm_s2',arm,rep) for arm in order}
   for arm,x in group.items():x['paired_qor_passed']=qos(x,group['flat']) and qos(x,group['stock']);x['qualification_map_equal']=x['map_sha256']==qual[arm]['map_sha256']
   flush()
   assert all(x['paired_qor_passed'] and x['qualification_map_equal'] for x in group.values()),'holdout formal gate failure'
 else: (o/'holdout_skipped.json').write_text(json.dumps(dict(reason='qualification gate failed; negative preserved, no configuration/seed replacement')))
 # Exactly one directed native BNN profile, outside every formal speed row.
 src=r/'profile_cuda_source';lib=o/'libcuda_profile.so'
 cmd=['nvcc','-O3','-std=c++14','--fmad=false','-shared','-Xcompiler=-fPIC,-fopenmp','-I'+str(src/'include'),str(src/'round6_1/cuda_backend61.cu'),'-o',str(lib)]
 with (o/'profile_compile.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
 x=run('bnn','alt_cuda','profile',False,str(r/'profile_build/bin/vpr_flat'),str(lib));x['profile_diagnostic']=True;flush()
 assert x['qualified'] and x['map_sha256']==next(v for v in hist if v['case']=='bnn' and v['backend']=='alt_cuda')['map_sha256']
 (o/'profile_ready.json').write_text(json.dumps(dict(status='complete',path=str(o/'bnn_alt_cuda_profile/process.log'))))
 # Finite supervised decision window; no unmanaged queue or implicit optimization.
 deadline=time.monotonic()+900
 while not (r/'targeted_optimization.json').exists() and time.monotonic()<deadline:time.sleep(5)
 if not (r/'targeted_optimization.json').exists():raise RuntimeError('finite P2 decision window expired; no implicit continuation')
 decision=b.read(r/'targeted_optimization.json')
 if decision['status']=='run_one_reserve_candidate':
  new=decision['binary'];libs['alt_cuda_reserve']=libs['alt_cuda']
  for case in ['s38417','bnn']:
   for arm in ['alt_cpu','alt_cuda']:
    x=run(case,arm,'reserve_qualification',True,new);base=next(v for v in hist if v['case']==case and v['backend']==arm)
    assert x['qualified'] and x['map_sha256']==base['map_sha256'] and qos(x,base),'reserve affected qualification'
  for rep in range(3):
   for case in ['s38417','bnn']:
    for arm in (['alt_cuda','alt_cuda_reserve'] if rep%2==0 else ['alt_cuda_reserve','alt_cuda']):
     x=run(case,arm,'reserve_pair'+str(rep),False,new if arm.endswith('reserve') else None);x['optimization_repeat']=rep
     base=next(v for v in hist if v['case']==case and v['backend']=='alt_cuda');assert x['qualified'] and x['map_sha256']==base['map_sha256'] and qos(x,base)
    flush()
 (o/'finished.json').write_text(json.dumps(dict(status='completed',rows=len(rows),holdout_qualification_passed=all(gates.values()) and maps),indent=2))
except Exception as e:
 (o/'finished.json').write_text(json.dumps(dict(status='failed',reason=str(e),rows=len(rows)),indent=2));raise
