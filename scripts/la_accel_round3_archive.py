"""Freeze round-three inputs, reports and raw observations; omit tools, builds and auth."""
import argparse,json,shutil,subprocess
from pathlib import Path
from prepare import sha256

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=a.experiment.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);selected=set()
 def add(folder,patterns):
  for pattern in patterns:selected.update(p for p in folder.glob(pattern) if p.is_file())
 add(root,['plan.json','*decision*.json','*gate*.json','*audit*.json','*validation*.json','*manifest*.json','*derivation*.json',
  'host_*.log','gpu_job.json','gpu_validate.json','gpu_submit.json','gpu_status.json',
  'report_*/*','plot_*/*','engineering_notes.json'])
 for folder in root.glob('native_d*'):
  add(folder,['manifest.json','invocation.json','spill*.json','architecture.xml','tiny.blif','tiny.net','tiny.place',
   'rr.xml','workload.bin*','layers.bin','wire_map.bin','stdout.log'])
 add(root/'native_stock_correctness',['result.json','stdout.log','wire_map.bin'])
 for name in ['memory_selftest','monitor_selftest']:
  add(root/name,['**/simulate.log','**/compile.log','**/elaborate.log','**/bounded_memory.json','*.sv','*.log','test.json'])
 for folder in root.glob('hls_*'):
  if not folder.is_dir():continue
  add(folder,['*.json','*.log','*.rpt','source_snapshot/*',
   'project/solution/syn/report/*_csynth.xml','project/solution/syn/report/*_csynth.rpt',
   'project/solution/sim/report/verilog/*.rpt','project/solution/sim/verilog/*.performance.result.transaction.xml',
   'project/solution/sim/tv/rtldatafile/rtl.*autotvout_result*.dat',
   'project/solution/sim/tv/cdatafile/c.*autotvout_result*.dat',
   'project/solution/impl/report/verilog/export_impl.xml',
   'project/solution/impl/verilog/report/*_timing_routed.rpt',
   'project/solution/impl/verilog/report/*_timing_paths_routed.rpt',
   'project/solution/impl/verilog/report/*_utilization_routed.rpt',
   'project/solution/impl/verilog/report/*_status_routed.rpt'])
 for folder in root.glob('bounded_*'):
  add(folder,['*.json','*.log','runner_snapshot.py','sim/verilog/bounded_axi3.sv',
   'sim/verilog/*.autotb.v','sim/verilog/run_xsim.sh','sim/verilog/xsim.log',
   'sim/verilog/bounded_memory.json','sim/verilog/engine_overlap.json',
   'sim/verilog/*.performance.result.transaction.xml',
   'sim/tv/cdatafile/c.*autotvout_result*.dat','sim/tv/rtldatafile/rtl.*autotvout_result*.dat'])
 add(root/'gpu_worker',['*.json','*.log','source/**/*.cpp','source/**/*.cu','source/**/*.hpp','source/CMakeLists.txt'])
 manifest={}
 for source in sorted(selected):
  if source.stat().st_size>32*1024*1024:raise ValueError('Unexpected large evidence file: '+str(source))
  rel=source.relative_to(root);dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
  manifest[str(rel)]={'sha256':sha256(dest),'bytes':dest.stat().st_size,'source':str(source)}
 index=dict(base_commit='d6b2ea285fbf6b6c64571d908ce366629c457be9',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_experiment=str(root),files=manifest,
  exclusions='Builds, DCPs, waves, executable binaries, credentials and CLI state remain outside this bundle. Complete small native graph/workload inputs are included.')
 (out/'index.json').write_text(json.dumps(index,indent=2)+'\n');print(f'{len(manifest)} files; {sum(v["bytes"] for v in manifest.values())} bytes')
if __name__=='__main__':main()
