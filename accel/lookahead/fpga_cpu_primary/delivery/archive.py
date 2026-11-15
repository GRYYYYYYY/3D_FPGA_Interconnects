#!/usr/bin/env python3
"""Content-addressed evidence archive; raw historical worktrees remain read-only."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,os
ROOT=Path(__file__).resolve().parents[4]
RAW=ROOT/'results/fpga_cpu_primary_20261115'
DEST=ROOT/'accel/lookahead/fpga_cpu_primary/evidence_snapshot'
SRC=ROOT/'accel/lookahead/fpga_cpu_primary'
def sha(b):return hashlib.sha256(b).hexdigest()
def excluded(p):
 rel=p.relative_to(RAW)
 return any(x in {'project','xsim.dir','.Xil','.vivado-ai','__pycache__'} or x.startswith('.check') for x in rel.parts) or p.suffix in {'.wdb','.pb','.str','.jou','.dcp','.rtd','.sdb'}
def main():
 ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group();g.add_argument('--verify',action='store_true');g.add_argument('--restore',type=Path,help='new empty destination for the raw CPU_PRIMARY subtree');a=ap.parse_args()
 if a.restore:
  target=a.restore.resolve();target.mkdir(parents=True,exist_ok=False)
  m=json.loads((DEST/'manifest.json').read_text())
  for r in m['files']:
   rel=Path(r['path']).relative_to('results/fpga_cpu_primary_20261115');out=(target/rel).resolve();out.relative_to(target)
   b=gzip.decompress((DEST/'objects'/r['sha256'][:2]/(r['sha256']+'.gz')).read_bytes());assert len(b)==r['bytes'] and sha(b)==r['sha256']
   out.parent.mkdir(exist_ok=True,parents=True);out.write_bytes(b);out.chmod(r.get('mode',0o644))
  print('ARCHIVE_RESTORED',len(m['files']),'files to',target);return
 if a.verify:
  m=json.loads((DEST/'manifest.json').read_text());checked={}
  for r in m['files']:
   h=r['sha256']
   if h not in checked:
    b=gzip.decompress((DEST/'objects'/h[:2]/(h+'.gz')).read_bytes());assert sha(b)==h;checked[h]=len(b)
   assert checked[h]==r['bytes']
  for name,h in m['source_binding'].items():assert sha((ROOT/name).read_bytes())==h,name
  print('ARCHIVE_VERIFIED',len(m['files']),'records',len(checked),'objects',len(m['source_binding']),'source bindings');return
 DEST.mkdir(exist_ok=True,parents=True);records=[];omitted=[]
 for p in sorted(RAW.rglob('*')):
  if not p.is_file() or p.is_symlink():continue
  if excluded(p):
   # Large regenerated vendor trees are not represented as complete captured evidence.
   if p.suffix=='.dcp':omitted.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'reason':'regenerable vendor checkpoint; retained in raw workspace, not Git artifact'})
   continue
  b=p.read_bytes();h=sha(b);obj=DEST/'objects'/h[:2]/(h+'.gz');obj.parent.mkdir(exist_ok=True,parents=True)
  if not obj.exists():obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0))
  records.append({'path':str(p.relative_to(ROOT)),'sha256':h,'bytes':len(b),'mode':p.stat().st_mode&0o777})
 sources={}
 for p in sorted(SRC.rglob('*')):
  if not p.is_file() or DEST in p.parents or '__pycache__' in p.parts or any(x.startswith('.check') for x in p.parts):continue
  if p.suffix in {'.py','.cpp','.hpp','.h','.sv','.md','.json','.tcl','.xdc'}:sources[str(p.relative_to(ROOT))]=sha(p.read_bytes())
 for p in sorted((ROOT/'docs').glob('*cpu_primary*')):sources[str(p.relative_to(ROOT))]=sha(p.read_bytes())
 guide=ROOT/'docs/CODEX_FPGA_CPU_PRIMARY_AFTER_3C7F96E.md';sources[str(guide.relative_to(ROOT))]=sha(guide.read_bytes())
 m={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':'3c7f96e6037030949b729240977c2ced373843c6','raw_root':str(RAW),'files':records,'source_binding':sources,'excluded_regenerable_checkpoints':omitted,'vendor_tree_exclusions':['project','xsim.dir','.Xil','.vivado-ai','*.wdb','*.pb'],'scope':'new raw evidence plus explicit source/output/reference bindings; prior archives linked by hashes, no historical mutation'}
 (DEST/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('ARCHIVED',len(records),'records',len(sources),'source files')
if __name__=='__main__':main()
