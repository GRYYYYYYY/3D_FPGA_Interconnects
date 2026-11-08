"""Copy a small, hashed evidence bundle; exclude workloads, credentials, caches and wave databases."""
import argparse,json,shutil,subprocess
from pathlib import Path
from prepare import sha256

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.experiment.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);files=[]
 patterns=['preflight_v2/preflight.json','preservation_audit.json','source_binding_audit.json','final_validation.json','heap_ii_diagnosis.json','memory_layout.json','operation_counts.json','software_summary*.json','ctest*regression.log','ctest_verified.log','dual_overlap/result.json','dual_overlap/config.json','dual_postcheck_diagnosis.json','memory64_*/result*.json','memory64_*/config.json','*_mcp_*timing*.rpt','*_mcp_route_status.rpt','tseng_import/result.json','tseng_hls_comparison/comparison.json','*_export/manifest.json','*/workload_layout.json','*_eligible/manifest.json','native_env_fix_local/summary.json']
 for pattern in patterns:files.extend(root.glob(pattern))
 for d in root.glob('hls_*'):
  if not d.is_dir():continue
  files.extend(d.glob('*.json'))
  files.extend(d.glob('csynth.log'))
  files.extend((d/'project/solution/sim/report/verilog').glob('*.rpt'))
  files.extend((d/'project/solution/impl/report/verilog').glob('export_impl.xml'))
  files.extend((d/'project/solution/impl/verilog/report').glob('*_timing_routed.rpt'))
  files.extend((d/'project/solution/impl/verilog/report').glob('*_utilization_routed.rpt'))
  if any(json.loads(p.read_text()).get('status')=='failed' for p in d.glob('*.json') if p.stem in ['csim','csynth','cosim','impl']):files.extend(d.glob('*.log'))
 for name in ['gpu_worker','gpu_worker_pinned','gpu_worker_confirm']:
  d=root/name
  for pattern in ['commands.json','finished.json','worker.json','device.log','compiler.log','cpu_topology.log','cpu_compiler.log','build.log','cpu_build.log','native_controls.log','*/runs.json','native_controls/summary.json']:
   files.extend(d.glob(pattern))
 manifest={}
 for src in sorted(set(files)):
  if not src.is_file():continue
  rel=src.relative_to(root);dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);manifest[str(rel)]=dict(sha256=sha256(dst),bytes=dst.stat().st_size,source=str(src))
 (out/'index.json').write_text(json.dumps(dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_experiment=str(root),files=manifest,exclusions='Large binary workloads, output maps, RTL build trees, auth/CLI state and wave databases remain outside this bundle.'),indent=2));print(f'{len(manifest)} evidence files; {sum(v["bytes"] for v in manifest.values())} bytes')
if __name__=='__main__':main()
