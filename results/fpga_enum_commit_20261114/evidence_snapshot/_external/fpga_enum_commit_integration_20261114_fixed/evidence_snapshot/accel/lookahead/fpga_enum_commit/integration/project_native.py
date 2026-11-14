"""Project frozen native candidate/whole-line oracles for matched backend replays.
Offline fixture transformation only. No timing or precomputed arithmetic in the full model.
"""
from pathlib import Path
import subprocess,json,gzip,hashlib,struct
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114/native_projection_b';BASE='1e312d6e4ffc5ea96f25c0b97931ad028e710584'
def git(p):return subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
def main():
 R.mkdir(exist_ok=False);prefix='results/fpga_pending_stream_20261114/evidence_snapshot/';manifest=json.loads(git(prefix+'manifest.json'));receipts=[]
 select={'bnn_export':['wave_2_38','wave_19_32'],'lstm_s2':['wave_7_36','wave_19_30'],'native_d3_w8':None,'native_d4_w8':None}
 for rec in manifest['files']:
  raw=rec['raw_path'];parts=raw.split('/')
  if len(parts)!=3 or parts[0]!='capture_a' or parts[1] not in select or not parts[2].startswith('wave_') or not raw.endswith('.bin'):continue
  if select[parts[1]] is not None and Path(parts[2]).stem not in select[parts[1]]:continue
  data=git(prefix+rec['archive']);data=gzip.decompress(data) if rec['archive'].endswith('.gz') else data
  assert hashlib.sha256(data).hexdigest()==rec['sha256'];h=struct.unpack_from('<8Q',data);assert h[0]==0x5053545241434531;off=64+h[4]*32;events=[]
  for i in range(h[5]):
   n,degree,pair=struct.unpack_from('<IIQ',data,off);off+=16
   for j in range(degree):
    n,pair=struct.unpack_from('<IQ',data,off);off+=12
    if n//4%32==0:events.append((n,pair))
  lines=[]
  for i in range(h[7]):
   l=struct.unpack_from('<I',data,off)[0];before=struct.unpack_from('<4Q',data,off+4);pv=struct.unpack_from('<4I',data,off+36);after=struct.unpack_from('<4Q',data,off+52);off+=84
   if l%32==0:lines.append((l,before,pv,after))
  assert off==len(data)
  p=R/(parts[1]+'_'+Path(parts[2]).stem+'.bin')
  # Existing backend-driver format: magic,sample,wave,bucket,edges,lines.
  with p.open('wb') as f:
   f.write(struct.pack('<6Q',0x5741564541434331,*h[1:4],len(events),len(lines)))
   for n,pair in events:f.write(struct.pack('<IQ',n,pair))
   for l,before,pv,after in lines:f.write(struct.pack('<II8Q',l,sum((a!=b)<<k for k,(a,b) in enumerate(zip(before,after))),*before,*after))
  receipts.append({'source_commit':BASE,'source_path':raw,'source_sha256':rec['sha256'],'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'candidates':len(events),'lines':len(lines),'scope':'owner0 candidate/final canonical projection; pending snapshot is not injected through hidden RAM writes'})
 (R/'manifest.json').write_text(json.dumps(receipts,indent=2)+'\n');print('native projections',len(receipts))
if __name__=='__main__':main()
