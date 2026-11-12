"""Validate exact archived bytes, including chunked complete-batch traces."""
from pathlib import Path
import gzip,hashlib,json,sys
root=Path(__file__).resolve().parents[4]
base=root/'results/fpga_sparse_stream_r2_20261112/evidence_snapshot'
seen=set();count=0
def verify(name):
 global count
 if name in seen:return
 seen.add(name);folder=base/name;m=json.loads((folder/'manifest.json').read_text())
 if m.get('predecessor'):verify(m['predecessor'])
 for record in m['files']:
  digest=hashlib.sha256();size=0
  parts=record.get('archive_parts',[{'archive':record.get('archive')}])
  for part in parts:
   p=folder/part['archive'];raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
   if 'offset' in part:
    assert part['offset']==size and len(raw)==part['bytes']
    assert hashlib.sha256(raw).hexdigest()==part['sha256']
   size+=len(raw);digest.update(raw)
  assert size==record['bytes'] and digest.hexdigest()==record['sha256'],record['raw_path']
  count+=1
verify(sys.argv[1]);print('VERIFIED',count,'files across',len(seen),'snapshots')
