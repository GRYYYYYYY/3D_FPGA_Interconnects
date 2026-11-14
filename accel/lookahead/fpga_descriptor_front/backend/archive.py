#!/usr/bin/env python3
"""Content-addressed compact evidence; no binary project rebuild products/DCPs.
Repeated fixtures/logs retain path entries but store identical bytes only once.
"""
from pathlib import Path
import json,gzip,hashlib,sys
root=Path(__file__).resolve().parents[4];base=root/'results/fpga_descriptor_front_20261114/backend';dest=base/'evidence_snapshot'
def sha(b):return hashlib.sha256(b).hexdigest()
if '--verify' in sys.argv:
 m=json.loads((dest/'manifest.json').read_text())
 for e in m['files']:
  b=(dest/e['stored']).read_bytes();raw=gzip.decompress(b) if e['compression']=='gzip' else b
  assert sha(raw)==e['sha256'] and len(raw)==e['bytes'],e['path']
 for e in m['sources']:
  assert sha((root/e['path']).read_bytes())==e['sha256'],e['path']
 print('BACKEND_ARCHIVE_VERIFIED',len(m['files']),'paths',len({e['stored'] for e in m['files']}),'blobs',len(m['sources']),'sources');raise SystemExit
assert not dest.exists(),'immutable archive already exists'
# Final experimental receipts required before freezing.
for run in ['sim_reg_fixed','sim_reg_jitter','sim_reg_ops','sim_reg_port','ooc_a','ooc_b']:assert (base/run/'terminal.json').exists(),run
files=[]
for p in base.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(base);parts=rel.parts
 if any(x in parts for x in ('xsim.dir','.Xil','.cache','.gen','.hw','.ip_user_files')):continue
 if p.name.startswith('hs_err') or p.suffix in ('.rpt','.log','.jou','.tcl','.sv','.v','.xdc','.csv','.json','.md','.txt','.hex','.mem','.prj','.sh','.ini'):
  # Checkpoint hashes are included in terminal receipts; full binaries remain server-side.
  files.append(p)
source=[]
for p in (root/'accel/lookahead/fpga_descriptor_front/backend').glob('*'):
 if p.is_file() and p.suffix in ('.py','.sv','.tcl','.xdc','.md'):source.append(p);files.append(p)
for p in [root/'accel/lookahead/fpga_descriptor_front/coordination/backend_interface.md']:source.append(p);files.append(p)
# Include frozen historical RTL used in final PRJ binding, not old experiment trees.
for run in ('sim_reg_fixed','sim_reg_ops','sim_reg_port'):
 for name in json.loads((base/run/'source_binding.json').read_text()):
  p=root/name
  if p.suffix in ('.sv','.v') and p.exists():files.append(p)
(dest/'blobs').mkdir(parents=True)
entries=[]
for p in sorted(set(files)):
 b=p.read_bytes();h=sha(b);compression='gzip' if len(b)>4096 else 'identity';stored='blobs/'+h+('.gz' if compression=='gzip' else '')
 target=dest/stored
 if not target.exists():target.write_bytes(gzip.compress(b,mtime=0) if compression=='gzip' else b)
 entries.append({'path':str(p.relative_to(root)),'sha256':h,'bytes':len(b),'stored':stored,'compression':compression})
m={'schema':1,'scope':'new backend context raw evidence; immutable historical RTL dependencies only, no full projects/DCPs','files':entries,'sources':[{'path':str(p.relative_to(root)),'sha256':sha(p.read_bytes())} for p in source]}
(dest/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('BACKEND_ARCHIVE_CREATED',len(entries),'paths',len({e['stored'] for e in entries}),'blobs',sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()),'bytes')
