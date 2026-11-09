"""Freeze selected new R5 evidence, preserving previous archives in place."""
import argparse,json,shutil
from pathlib import Path
from prepare import sha256
from la_accel_round3_archive import omit_account_identity
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.experiment.resolve();o=a.output.resolve();o.mkdir(exist_ok=False);files=set()
def add(folder,patterns):
 for pattern in patterns:files.update(f for f in folder.glob(pattern) if f.is_file())
add(r,['*.json','*.jsonl','*.log','remote_before_push.txt','model/*','plots/*','profiles/*.jsonl','profiles/*.json','profiles/*.log','profiles_layers/*.jsonl','profiles_layers/*.json','profiles_layers/*.log'])
# Only small traces; large graphs have bounded per-qid summaries, not event text.
add(r/'profiles',['native_d3_w8.csv','native_d4_w8.csv','native_d5_w8.csv'])
for d in r.glob('native_*'):add(d,['*.json','architecture.xml','tiny.blif','tiny.net','tiny.place','workload.bin*','layers.bin','wire_map.bin','stdout.log'])
for d in r.glob('hls_*'):
 if not d.is_dir():continue
 add(d,['*.json','*.log','source_snapshot/*','runner_snapshot.py','project/solution/syn/report/*.rpt','project/solution/syn/report/*.xml','project/solution/.autopilot/db/*DISPATCH.verbose.sched.rpt','project/solution/sim/wrapc/cosim.tv.mk','project/solution/sim/wrapc/Makefile.rules','project/solution/syn/verilog/*DISPATCH.v'])
for d in r.glob('rtl_ctx*'):
 if not d.is_dir():continue
 add(d,['*.json','*.log','*.tcl','runner_snapshot.py','project/solution/sim/report/verilog/*.rpt','project/solution/sim/verilog/*.performance.result.transaction.xml','project/solution/sim/tv/rtldatafile/*.dat','project/solution/sim/tv/cdatafile/*.dat'])
for d in r.glob('monitor_ctx*'):
 if not d.is_dir():continue
 add(d,['*.json','*.log','runner_snapshot.py','sim/verilog/*.autotb.v','sim/verilog/*.performance.result.transaction.xml','sim/verilog/transactions.jsonl','sim/verilog/run_xsim.sh','sim/tv/rtldatafile/*.dat','sim/tv/cdatafile/*.dat'])
add(r/'heap_audit',['*.hpp','*.cpp','*.json','*.log'])
add(r/'gpu_worker_new',['*.json','*.log','source/round4/*','source/include/*'])
index={}
for f in sorted(files):
 if f.name=='index.json':continue
 assert f.stat().st_size<32*1024**2,f
 rel=f.relative_to(r);dest=o/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);entry=dict(source=str(f),source_sha256=sha256(f))
 if f.name.startswith('gpu_') and f.suffix=='.json':dest.write_text(json.dumps(omit_account_identity(json.loads(f.read_text())),indent=2)+'\n');entry['transform']='account identity omitted'
 entry.update(sha256=sha256(dest),bytes=dest.stat().st_size);index[str(rel)]=entry
(o/'index.json').write_text(json.dumps(dict(base_commit='fa07aefc86932e4b2da73d4d934b05836b673bdf',source=str(r),files=index,exclusions='Prior archives, full old inputs, large XML and layer binaries, binaries, tool builds, waves, credentials and untracked guidance.'),indent=2)+'\n');print(len(index),'files',sum(x['bytes'] for x in index.values()),'bytes')
