"""Append completed micro OOC successes/tool failures, preserving exact bytes."""
from pathlib import Path
import gzip,hashlib,json,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'evidence_snapshot'/sys.argv[1];out.mkdir(exist_ok=False);records=[];stages=[]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
for name in sys.argv[2:]:
 d=r/'timing'/name;terminal=d/'terminal.json'
 if not terminal.exists():terminal=d/'parent_abort_review.json'
 assert terminal.exists(),'active OOC cannot be frozen as completed'
 stages.append({'variant':name,'terminal':json.loads(terminal.read_text()),'local_DCP_sha256':{str(p.relative_to(r)):digest(p) for p in d.rglob('*.dcp')}})
 for p in sorted(d.rglob('*')):
  if not p.is_file() or p.suffix not in ['.sv','.tcl','.xdc','.json','.log','.rpt','.md','.csv','.rst']:continue
  raw=p.read_bytes();dest=out/p.relative_to(r);dest.parent.mkdir(parents=True,exist_ok=True)
  if len(raw)>16384:dest=dest.with_name(dest.name+'.gz');dest.write_bytes(gzip.compress(raw,mtime=0))
  else:dest.write_bytes(raw)
  restored=gzip.decompress(dest.read_bytes()) if dest.suffix=='.gz' else dest.read_bytes();assert restored==raw
  records.append({'raw_path':str(p.relative_to(r)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'archive':str(dest.relative_to(out))})
(out/'manifest.json').write_text(json.dumps({'scope':'actual terminal micro OOC stages including failures; DCPs remain local, identified by hash; no full-kernel timing inference','stages':stages,'files':records,'all_archived_bytes_verified':True},indent=2)+'\n');print('FROZEN_MICRO_OOC',len(records))
