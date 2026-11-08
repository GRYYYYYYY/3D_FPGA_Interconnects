"""Run the opt-in native global-job exporter on a frozen complete RRG in a fresh directory."""
import argparse,json,os,subprocess,shutil,struct,time
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--case',default='tseng_2d',choices=['tseng_2d','bnn','dla_like.medium']);p.add_argument('--timeout',type=int,default=600);a=p.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
 import run_native_flat_baseline as base
 s=json.loads((ROOT/'results/native_flat_baseline_20261105/summary.json').read_text());plan=json.loads((ROOT/'results/native_flat_baseline_20261105/plan.json').read_text());entry=s['cases'][a.case];case=json.loads(Path(entry['case']['path']).read_text())
 for name,target in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][name]['path'],o/target)
 cmd=base.cpu_command(str(a.binary.resolve()),case,o,{'router':'parallel'},8,iterations=1);base.set_option(cmd,'--write_router_lookahead',o/'wire_map.bin');base.set_option(cmd,'--generate_rr_node_overuse_report','off');cmd.remove('--analysis')
 env=base.environment(plan,'flat',o,False);env['VPR_LA_EXPORT']=str(o/'workload.bin')
 # Eight distinct physical cores, one NUMA node, same policy as the CPU controls.
 cores={}
 for cpu in sorted(os.sched_getaffinity(0)):
  path=Path(f'/sys/devices/system/cpu/cpu{cpu}');key=((path/'topology/physical_package_id').read_text(),(path/'topology/core_id').read_text());cores.setdefault(key,cpu)
 pool=list(cores.values())[:8];os.sched_setaffinity(0,pool)
 rec=dict(command=cmd,environment={k:v for k,v in env.items() if k.startswith(('VPR_','OMP_','LD_'))},affinity=pool,case=a.case,binary_sha256=sha256(a.binary),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),diagnostic=True,timing_eligible=False)
 (o/'invocation.json').write_text(json.dumps(rec,indent=2));start=time.time()
 try:
  with (o/'stdout.log').open('w') as f:r=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=a.timeout)
  rec['returncode']=r.returncode
 except subprocess.TimeoutExpired:rec['returncode']=None;rec['failure_reason']='timeout'
 rec['elapsed_host_s']=time.time()-start
 path=o/'workload.bin';rec['export_exists']=path.exists()
 if path.exists():
  h=struct.unpack('<7Q',path.open('rb').read(56));rec.update(schema_version='la_accel_v1',semantic_mode='STRICT_FP32',graph_kind='complete_native_RRG',dimensions=dict(zip(['magic','nodes','edges','jobs','costs','cells','groups'],h)),workload_sha256=sha256(path),artifacts={p.name:sha256(p) for p in o.iterdir() if p.name.startswith(('workload','wire_map'))},reference_wire_map=entry['reference_map'],wire_map_matches_reference=(o/'wire_map.bin').exists() and sha256(o/'wire_map.bin')==entry['reference_map']['sha256'])
 rec['status']='exported' if path.exists() and rec.get('returncode') in (0,2) else 'failed';rec['route_success']=False
 (o/'manifest.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec.get('dimensions',rec),indent=2));return 0 if rec['status']=='exported' else 1
if __name__=='__main__':raise SystemExit(main())
