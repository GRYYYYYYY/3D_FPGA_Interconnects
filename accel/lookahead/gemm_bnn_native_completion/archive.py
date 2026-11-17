#!/usr/bin/env python3
"""Archive small completed-run evidence and bind large artifacts; no execution."""
from pathlib import Path
import argparse,json,hashlib,shutil,re
H=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('run',type=Path);a=ap.parse_args();r=a.run
 assert (r/'finished.json').exists(),'Do not archive an active partial run as final'
 dest=H/'evidence';dest.mkdir(exist_ok=False);small=[];large=[]
 for p in sorted(r.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(r)
  if p.suffix=='.json' or p.name=='process.log':
   assert p.stat().st_size<10*1024**2,str(p)
   q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
   small.append(dict(snapshot=str(q.relative_to(H)),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
  elif p.name in ['native_input.bin','wire_map.bin','routed.route']:
   large.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
 mem=[];diagnostics=[]
 for p in sorted(r.glob('*/*/*/*/process.log')):
  txt=p.read_text(errors='replace');hits=re.findall(r'max_rss ([\d.]+) MiB',txt)
  mem.append(dict(log=str(p),max_rss_MiB=float(hits[-1]) if hits else None,scope='native process OS maximum resident set, includes setup/route',device_peak='NOT_MEASURED; exact array allocation estimate and actual free-memory admission retained'))
  messages=[s for s in txt.splitlines() if s.startswith('Error ')];diagnostics.append(dict(log=str(p),error_diagnostic_count=len(messages),no_fanin_count=sum('has no fanin' in s for s in messages),other_messages=[s for s in messages if 'has no fanin' not in s],scope='RRG diagnostics preserved, not silently suppressed; native route FULL/STA is a separate check'))
 (H/'evidence_manifest.json').write_text(json.dumps(dict(small_files=small,large_artifacts=large,host_memory=mem,graph_diagnostics=diagnostics,device_peak_not_measured=True),indent=2)+'\n')
 print(json.dumps(dict(small=len(small),large=len(large),evidence=str(dest))))
if __name__=='__main__':main()
