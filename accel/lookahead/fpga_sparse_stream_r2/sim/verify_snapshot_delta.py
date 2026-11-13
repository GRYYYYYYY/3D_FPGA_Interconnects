"""Verify every new archive byte and bind a previously verified predecessor."""
from pathlib import Path
import datetime,gzip,hashlib,json,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';name,prev,receipt=sys.argv[1:4];out=r/'evidence_snapshot'/name;m=json.loads((out/'manifest.json').read_text());p=r/prev;v=json.loads(p.read_text());assert v['snapshot']==m['predecessor'] and v['all_new_files_verified']
count=total=0
for record in m['files']:
 h=hashlib.sha256();size=0
 for part in record.get('archive_parts',[{'archive':record.get('archive')}]):
  f=out/part['archive'];raw=gzip.decompress(f.read_bytes()) if f.suffix=='.gz' else f.read_bytes()
  if 'offset' in part:assert part['offset']==size and len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256']
  size+=len(raw);h.update(raw)
 assert size==record['bytes'] and h.hexdigest()==record['sha256'],record['raw_path']
 count+=1;total+=size
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot':name,'manifest_sha256':hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest(),'all_new_files_verified':True,'new_file_count':count,'new_raw_bytes':total,'predecessor':m['predecessor'],'predecessor_verification':prev,'predecessor_verification_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'exact new delta bytes; prior chain relies on identified verification receipt, not reexecuted experiments'}
with (r/receipt).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('VERIFIED_DELTA',count,total,flush=True)
