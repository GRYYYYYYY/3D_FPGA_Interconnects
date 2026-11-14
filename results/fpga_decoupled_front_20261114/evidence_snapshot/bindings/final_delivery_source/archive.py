"""Compact immutable archive; verify or restore into a new directory."""
from run_profile import *
import argparse

def verify(root):
 m=json.loads((root/'manifest.json').read_text())
 for x in m['files']:
  data=(root/x['archive']).read_bytes()
  if x['archive'].endswith('.gz'):data=gzip.decompress(data)
  assert len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256'],x['raw_path']
 return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');ap.add_argument('--restore',type=Path);ap.add_argument('--archive',type=Path,default=R/'evidence_snapshot');a=ap.parse_args();out=a.archive
 if a.verify or a.restore:
  m=verify(out)
  if a.restore:
   a.restore.mkdir(parents=True,exist_ok=False)
   for x in m['files']:
    data=(out/x['archive']).read_bytes()
    if x['archive'].endswith('.gz'):data=gzip.decompress(data)
    p=a.restore/x['raw_path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  print('ARCHIVE_PASS',len(m['files']));return
 out.mkdir(exist_ok=False)
 allowed={'.json','.log','.csv','.cpp','.hpp','.py','.sv','.v','.tcl','.prj','.txt','.md'};rows=[]
 for name in ['profile_a','front_a','front_stress_a','analysis_a','front_b','front_stress_b','analysis_b','bindings']:
  for p in sorted((R/name).rglob('*')):
   if not p.is_file():continue
   if p.suffix not in allowed and not (p.name=='output.bin' or (name.startswith('front_stress') and p.suffix=='.bin')):continue
   data=p.read_bytes();raw=str(p.relative_to(R));dest=raw+'.gz' if len(data)>16384 else raw;q=out/dest;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(data,mtime=0) if dest.endswith('.gz') else data)
   rows.append({'raw_path':raw,'archive':dest,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 m={'base_commit':BASE,'status':'NO_GO_CONFIGURATION','scope':'complete native functional profile, final frontend-only A/B/C, retained enum RTL witness; no new complete FPGA model','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows,'omitted_reproducible_native_traces':{'base_commit':BASE,'manifest':'results/fpga_pending_stream_20261114/evidence_snapshot/manifest.json','prefix':'capture_a/','reason':'unchanged frozen trace hashes are in each run receipt; no duplicate large trace archive'},'old_GPU_and_models':'bindings/reused_evidence.json','fpga_seconds':None,'board_measured':False}
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');verify(out)
 print('ARCHIVE_PASS',len(rows),'compressed_bytes',sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
if __name__=='__main__':main()
