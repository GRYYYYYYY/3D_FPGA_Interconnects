"""Freeze selected fourth-round evidence without changing prior evidence or guidance."""
import argparse,json,shutil
from pathlib import Path
from prepare import sha256
from la_accel_round3_archive import omit_account_identity

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=a.experiment.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);selected=set()
 def add(folder,patterns):
  for pattern in patterns:selected.update(p for p in folder.glob(pattern) if p.is_file())
 add(root,['plan.json','remote_before_push.txt','engineering_notes.json','inputs_manifest.json','package_replay.json','*audit*.json','*diagnosis*.json','*profile*.json','*gate*.json','report_final.json','*validation*.json','*provenance*.json',
  'mcp_*.json','onchip_full1_ram_synth.rpt','*_monitor_driver.log','ctest.log','cmake.log','build.log','*semantics.log','early_tests.log','heap_test4.log','onchip_host_full.log','*diff.log','native_audits/*',
  'gpu_job_*.json','gpu_validate_*.json','gpu_submit_*.json','gpu_status_*.json','followup_supervisor.*','plots/*'])
 for folder in root.glob('native_*'):
  add(folder,['manifest.json','invocation.json','result.json','architecture.xml','tiny.blif','tiny.net','tiny.place','rr.xml','workload.bin*','layers.bin','wire_map.bin','stdout.log'])
 add(root/'semantic_fixtures',['*.bin'])
 add(root/'cross_layer_trace_verified',['*.json','*.jsonl','*.cpp','*.hpp','build.log'])
 for folder in root.glob('hls_*'):
  if not folder.is_dir():continue
  add(folder,['*.json','*.log','runner_snapshot.py','source_snapshot/*',
   'project/solution/syn/report/*_csynth.rpt','project/solution/syn/report/*_csynth.xml',
   'project/solution/.autopilot/db/*HEAP*.verbose.sched.rpt',
   'project/solution/sim/report/verilog/*.rpt','project/solution/sim/verilog/*.performance.result.transaction.xml',
   'project/solution/sim/tv/rtldatafile/rtl.*autotvout_*.dat','project/solution/sim/tv/cdatafile/c.*autotvout_*.dat',
   'project/solution/impl/report/verilog/export_impl.*','project/solution/impl/verilog/report/*_routed.rpt',
   'project/solution/syn/verilog/lookahead_onchip4.v','project/solution/syn/verilog/*pop*.v',
   'project/solution/syn/verilog/*search*.v','project/solution/syn/verilog/*engine*_s.v',
   'project/solution/syn/verilog/*RAM*.v'])
 for folder in root.glob('monitor_*'):
  if not (folder/'result.json').exists() and not (folder/'verification_v2.json').exists():continue
  add(folder,['*.json','*.log','runner_snapshot.py','sim/verilog/*.autotb.v','sim/verilog/run_xsim.sh',
   'sim/verilog/transactions.jsonl','sim/verilog/*.performance.result.transaction.xml',
   'sim/tv/rtldatafile/rtl.*autotvout_*.dat','sim/tv/cdatafile/c.*autotvout_*.dat'])
 for timing in root.glob('timing125_*'):
  add(timing,['*.json','*.rpt','*.tcl','*.xdc'])
 for worker in root.glob('gpu_worker_*'):
  add(worker,['*.json','*.log','source/round4/*','source/include/*'])
 manifest={}
 for source in sorted(selected):
  assert source.stat().st_size<32*1024*1024,'Unexpected large evidence file'
  rel=source.relative_to(root);dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
  entry=dict(sha256=sha256(dest),bytes=dest.stat().st_size,source=str(source))
  if source.name.startswith('gpu_') and source.suffix=='.json':
   original=sha256(source);dest.write_text(json.dumps(omit_account_identity(json.loads(source.read_text())),indent=2)+'\n')
   entry.update(sha256=sha256(dest),bytes=dest.stat().st_size,source_sha256=original,archive_transform='Account identity omitted; commands/resource/status evidence retained.')
  manifest[str(rel)]=entry
 index=dict(base_commit='96629a57511080a95c4d5e5050365fc2ada0fb4c',source_experiment=str(root),files=manifest,exclusions='Tools, credentials, untracked guidance/package, builds, executables, waves and DCPs. Prior round evidence is referenced in place. Full tseng/BNN input hashes refer to existing immutable exports.')
 (out/'index.json').write_text(json.dumps(index,indent=2)+'\n');print(len(manifest),'files;',sum(x['bytes'] for x in manifest.values()),'bytes')
if __name__=='__main__':main()
