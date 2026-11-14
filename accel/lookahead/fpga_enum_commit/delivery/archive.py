"""Archive final new evidence without modifying prior archives or raw attempts."""
from pathlib import Path
import argparse,gzip,hashlib,json,datetime
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('snapshot');ap.add_argument('--verify',action='store_true');a=ap.parse_args();out=R/a.snapshot
 if a.verify:
  m=json.loads((out/'manifest.json').read_text())
  for x in m['files']:
   data=(out/x['archive']).read_bytes();data=gzip.decompress(data) if x['compression']=='gzip' else data
   assert hashlib.sha256(data).hexdigest()==x['sha256'] and len(data)==x['bytes'],x['raw_path']
  for name,expected in m['delivery_sources_sha256'].items():assert digest(ROOT/name)==expected,name
  print('ARCHIVE_VERIFIED',len(m['files']),'sources',len(m['delivery_sources_sha256']));return
 out.mkdir(exist_ok=False);rows=[]
 allowed={'.json','.jsonl','.csv','.log','.txt','.rpt','.tcl','.xdc','.cpp','.hpp','.h','.sv','.v','.py','.md','.prj','.hex','.mem','.coe','.candidate','.gz','.sh','.jou','.ini','.bin'}
 roots=sorted(q for q in (ROOT/'results').glob('fpga_enum_commit*') if q.is_dir())
 for p in sorted(p for root in roots for p in root.rglob('*')):
  if not p.is_file() or out in p.parents:continue
  rel=p.relative_to(R) if R in p.parents else Path('_external')/p.relative_to(ROOT/'results')
  if rel.parts[0]=='baseline' or any(t in rel.parts for t in ['obj_dir','build','xsim.dir','.Xil','__pycache__']):continue
  if p.suffix not in allowed and not p.name.endswith('output.bin') and not (rel.parts[0]=='native_projection_b' and p.suffix=='.bin'):continue
  data=p.read_bytes();compress=len(data)>16384 and p.suffix!='.gz';dest=str(rel)+('.gz' if compress else '');q=out/dest;assert not q.exists(),f'archive collision: {dest}';q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(data,mtime=0) if compress else data)
  rows.append({'raw_path':str(rel),'original_path':str(p.relative_to(ROOT)),'archive':dest,'compression':'gzip' if compress else 'identity','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 sources={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'accel/lookahead/fpga_enum_commit').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 for name in ['CODEX_FPGA_ENUM_COMMIT_AFTER_1E312D6.md','lookahead_fpga_enum_commit.md']:
  p=ROOT/'docs'/name;sources[str(p.relative_to(ROOT))]=digest(p)
 m={'base':'1e312d6e4ffc5ea96f25c0b97931ad028e710584','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows,'delivery_sources_sha256':sources,'reused_evidence_manifest':'1e312d6e:results/fpga_decoupled_front_20261114/evidence_snapshot/manifest.json','old_evidence_read_only':True,'board_measured':False}
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('ARCHIVED',len(rows))
if __name__=='__main__':main()
