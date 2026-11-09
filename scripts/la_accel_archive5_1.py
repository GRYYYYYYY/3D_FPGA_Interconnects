"""Create a reviewed text-only evidence snapshot; never alter a historical cohort."""
import argparse, hashlib, json, shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);a=p.parse_args();r=a.experiment.resolve();o=r/'evidence_snapshot';o.mkdir(exist_ok=False)
files=set()
for name in ['provenance.json','report_final.json','background_audit.json','validation.json','plan_final.json']:
 f=r/name
 if f.exists():files.add(f)
for folder in ['audit','model']:
 files.update(f for f in (r/folder).rglob('*') if f.is_file() and f.suffix in ['.json','.py','.txt'])
for f in (r/'pq').glob('*'):
 if f.is_file() and f.suffix in ['.json','.jsonl','.csv','.log','.txt']:files.add(f)
for base in [r/'pq',r/'mechanism']:
 for d in base.iterdir():
  if not d.is_dir():
   if d.suffix in ['.json','.log']:files.add(d)
   continue
  for f in d.iterdir():
   if f.is_file() and f.suffix in ['.json','.jsonl','.log','.txt','.py']:files.add(f)
  for source in ['source','source_snapshot']:
   if (d/source).exists():files.update(f for f in (d/source).iterdir() if f.is_file())
  for sub in ['project/solution/syn/report','project/solution/sim/report','project/sol/syn/report','project/sol/sim/report']:
   if (d/sub).exists():files.update(f for f in (d/sub).rglob('*') if f.is_file() and f.suffix in ['.rpt','.xml','.json'])
  for sub in ['sim/verilog/events.csv','sim/verilog/lookahead_services51.performance.result.transaction.xml']:
   if (d/sub).exists():files.add(d/sub)
# Complete successful synthesized Verilog (plus primitive models) is reproducible.
for sub in ['mechanism/hls_d/project/solution/syn/verilog','pq/hls_path_cpp/project/solution/syn/verilog','pq/hls_baseline_cpp/project/solution/syn/verilog']:
 if (r/sub).exists():files.update(f for f in (r/sub).rglob('*') if f.is_file() and f.suffix in ['.v','.vh','.dat'])
for f in (r/'mechanism/debug_b').glob('*'):
 if f.is_file() and f.suffix in ['.txt','.c']:files.add(f)
index=[]
for f in sorted(files):
 assert f.stat().st_size<30_000_000, f
 dst=o/f.relative_to(r);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);data=dst.read_bytes();index.append(dict(path=str(dst.relative_to(o)),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(o/'index.json').write_text(json.dumps({'format':1,'files':index,'bytes':sum(x['bytes'] for x in index),'exclusions':['Compiled host executables, simulator binaries, .wdb waves and core dumps remain local; raw phase logs, frozen source, RTL, reports and handshake traces are archived.','Existing native workload binaries are referenced by hash rather than copied.']},indent=2)+'\n')
print('archived',len(index),'files',sum(x['bytes'] for x in index),'bytes')
