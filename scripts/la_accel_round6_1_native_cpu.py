"""Bounded paired native ALT qualification, never change historical inputs."""
import os,json,sys,subprocess,time,shutil
from pathlib import Path
import run_native_flat_baseline as b
from scaling_common import metrics,vpr_command
from prepare import sha256
R=Path(__file__).resolve().parents[1];o=Path(sys.argv[1]).resolve();o.mkdir(exist_ok=False)
plan=b.read(R/'results/native_flat_baseline_20261105/plan.json');cases=b.read(R/'results/native_flat_baseline_20261105/summary.json')['cases']
binary=o.parent/'native_build/bin/vpr_flat';lib=o.parent/'libcpu61.so'
pools={};seen=set()
for cpu in sorted(os.sched_getaffinity(0)):
 d=Path(f'/sys/devices/system/cpu/cpu{cpu}');key=((d/'topology/physical_package_id').read_text(),(d/'topology/core_id').read_text())
 if key in seen:continue
 seen.add(key);node=sorted(d.glob('node*'))[0].name;pools.setdefault(node,[]).append(cpu)
cpus=sorted(pools.values(),key=lambda x:(-len(x),x))[0][:8];os.sched_setaffinity(0,cpus)
rows=[]
def run(cmd,d,env):
 start=time.monotonic()
 with (d/'process.log').open('w') as f:
  try:p=subprocess.run(cmd,cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600);rc=p.returncode
  except subprocess.TimeoutExpired:rc=124
 return dict(returncode=rc,elapsed_s=time.monotonic()-start,command=list(map(str,cmd)),metrics=metrics((d/'process.log').read_text(errors='replace')))
cases['s38417']={'case':{'path':str(R/'results/native_cpu_evidence_20261102/prepared/s38417_s1/vpr_case.json')}}
for case_name in (sys.argv[2:] or ['s38417','bnn']):
 case=b.read(cases[case_name]['case']['path'])
 for arm in ['control','alt_s0','alt_s20']:
  d=o/(case_name+'_'+arm);d.mkdir()
  for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],d/name)
  cmd=b.cpu_command(str(binary),case,d,{'router':'parallel'},8,iterations=200);b.set_option(cmd,'--write_router_lookahead',d/'wire_map.bin');b.set_option(cmd,'--generate_rr_node_overuse_report','off')
  env=b.environment(plan,'flat',d,False)
  for k in list(env):
   if k.startswith('VPR_LA_'):env.pop(k)
  if arm!='control':env.update(VPR_LA_BACKEND=str(lib),VPR_LA_CONTEXTS='8',VPR_LA_MODE='ALT_BUCKET_FP32_V1',VPR_LA_BUCKET_SHIFT='20' if arm=='alt_s20' else '0',R61_CAPTURE=str(d/'native_input'))
  rec=dict(case=case_name,arm=arm,affinity=cpus,binary_sha256=sha256(binary),library_sha256=sha256(lib),scope='one bounded paired qualification; not formal timing',input_bindings=case['inputs'])
  (d/'invocation.json').write_text(json.dumps(rec|dict(command=list(map(str,cmd)),alt_enabled=arm!='control'),indent=2))
  rec.update(run(cmd,d,env));wire=d/'wire_map.bin';rec['map_sha256']=sha256(wire) if wire.exists() else None
  log=(d/'process.log').read_text(errors='replace');rec['live_lines']=[x for x in log.splitlines() if 'LA_LIVE' in x]
  rec['backend_lines']=[x for x in log.splitlines() if 'R61_BACKEND' in x]
  rec['identity_lines']=[x for x in log.splitlines() if 'R61_IDENTITY' in x]
  rec['scope_lines']=[x for x in log.splitlines() if 'R61_NATIVE_BUILD' in x]
  rec['alt_dispatch_verified']=arm=='control' or (len(rec['live_lines'])==1 and len(rec['backend_lines'])==1 and ('shift=20' if arm=='alt_s20' else 'shift=0') in rec['backend_lines'][0])
  if not rec['alt_dispatch_verified']:
   rows.append(rec);(o/'runs.json').write_text(json.dumps(rows,indent=2));raise RuntimeError('ALT backend was not invoked')
  if rec['returncode']==0 and rec['metrics']['routing_success'] and rec['metrics']['full_check']:
   route=d/'routed.route';before=sha256(route);check=d/'independent';check.mkdir();ic=vpr_command(plan['binaries']['original']['path'],case,d,200,route=False);b.set_option(ic,'--num_workers',8)
   rec['independent']=run(ic,check,b.environment(plan,'stock',check));rec['readback_identity']=before==sha256(route);rec['candidate_route_sha256']=before
  rows.append(rec);(o/'runs.json').write_text(json.dumps(rows,indent=2));print(case_name,arm,rec['returncode'],rec['metrics'],flush=True)
