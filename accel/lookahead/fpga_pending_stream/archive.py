"""Append-only compact evidence archive. No publication side effects."""
from pathlib import Path
import gzip,hashlib,json,subprocess,datetime
ROOT=Path(__file__).resolve().parents[3];R=ROOT/'results/fpga_pending_stream_20261114'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 out=R/'evidence_snapshot';out.mkdir(exist_ok=False);records=[]
 for tag in ['stage_a','stage_a_v2','capture_a','screen_a','analysis_a','worktree_recovery']:
  for p in sorted((R/tag).rglob('*')):
   if not p.is_file() or p.suffix not in {'.json','.csv','.log','.txt','.bin','.cu','.empty'}:continue
   raw=p.read_bytes();dest=out/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True)
   compressed=len(raw)>16384
   if compressed:dest=dest.with_name(dest.name+'.gz')
   dest.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0) if compressed else raw)
   assert (gzip.decompress(dest.read_bytes()) if compressed else dest.read_bytes())==raw
   records.append({'raw_path':str(p.relative_to(R)),'archive':str(dest.relative_to(out)),'bytes':len(raw),'sha256':sha(raw)})
 files=[p for p in (ROOT/'accel/lookahead/fpga_pending_stream').glob('*') if p.is_file()]
 files+=[ROOT/'docs/lookahead_fpga_pending_stream.md',ROOT/'docs/lookahead_fpga_inf_followup.md',ROOT/'accel/lookahead/fpga_sparse_stream_r2/sim/publish_evidence_subset.py']
 manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_sha':'a64c934956be6514a27f66fd1a46f09ef4a2fab9','scope':'initial frontend necessary-bound rejection; partial finite POP/frontend screening; not new RTL or complete finite architecture','source_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in files},'files':records,'all_archived_bytes_verified':True,'fpga_seconds':None,'board_measured':False}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('ARCHIVED',len(records),'files',sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'bytes')
if __name__=='__main__':main()
