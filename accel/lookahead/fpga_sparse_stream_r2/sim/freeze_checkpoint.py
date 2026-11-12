"""Create append-only compact evidence snapshots; never rewrite raw run evidence."""
from pathlib import Path
import gzip,hashlib,json,shutil,sys,subprocess
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'evidence_snapshot'/sys.argv[1];out.mkdir(parents=True,exist_ok=False)
# Optional predecessor: retain an append-only delta instead of recopying every
# unchanged historical trace. The manifest explicitly binds the predecessor.
previous=sys.argv[2] if len(sys.argv)>2 else None
known={}
if previous:
 def inherit(name):
  m=json.loads((r/'evidence_snapshot'/name/'manifest.json').read_text())
  if m.get('predecessor'):inherit(m['predecessor'])
  known.update({x['raw_path']:x['sha256'] for x in m['files']})
 inherit(previous)
files=[]
for p in r.rglob('*'):
 if not p.is_file() or 'evidence_snapshot' in p.parts or 'timing' in p.relative_to(r).parts:continue
 rel=p.relative_to(r)
 if p.suffix in ['.json','.csv','.log'] or ('source' in p.parts and p.suffix in ['.sv','.cpp','.hpp']):
  # Exclude generated compiler logs only when they are pure C++ build output;
  # Verilator diagnostics/build failures remain in the compact evidence.
  files.append(p)
 if p.name=='output.bin':files.append(p)
manifest=[]
for p in sorted(set(files)):
 rel=p.relative_to(r);dest=out/rel
 if p.stat().st_size>16384:dest=dest.with_name(dest.name+'.gz')
 dest.parent.mkdir(parents=True,exist_ok=True)
 raw=p.read_bytes()
 if known.get(str(rel))==hashlib.sha256(raw).hexdigest():continue
 if dest.suffix=='.gz':dest.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
 else:dest.write_bytes(raw)
 manifest.append({'raw_path':str(rel),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'archive':str(dest.relative_to(out))})
(out/'manifest.json').write_text(json.dumps({'scope':'checkpoint; raw evidence retained; active Vivado timing runs excluded until completed','predecessor':previous,'files':manifest,'source_base':'5651a34abb97939bee6402c5af585753ab07f64b'},indent=2)+'\n')
print('FROZEN',len(manifest),sum(x['bytes'] for x in manifest),'raw bytes',sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'archive bytes')
