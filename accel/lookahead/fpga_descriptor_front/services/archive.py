#!/usr/bin/env python3
"""Compact immutable service evidence; DCP/ELF/WDB remain bound at original paths."""
import argparse,gzip,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[4];results=root/'results/fpga_descriptor_front_20261114';out=results/'services_evidence'
sha=lambda b:hashlib.sha256(b).hexdigest()
if a.verify:
 m=json.loads((out/'manifest.json').read_text())
 for x in m['files']:
  b=(out/x['archive']).read_bytes();b=gzip.decompress(b) if x['compression']=='gzip' else b
  assert len(b)==x['bytes'] and sha(b)==x['sha256'],x['source']
 for x,h in m['live_sources'].items():assert sha((root/x).read_bytes())==h,x
 print('SERVICE_ARCHIVE_VERIFIED',len(m['files']),'sources',len(m['live_sources']));raise SystemExit
if out.exists():raise SystemExit('Immutable archive already exists; verify or use a separately named revision')
assert json.loads((results/'services_b/terminal.json').read_text())['status']=='PASS'
assert (results/'services_memory_synth/terminal.json').exists(),'Wait for real full-network synthesis terminal'
out.mkdir();manifest={'files':[],'live_sources':{},'scope':'source, tests, original failures, synthesis reports; not complete vendor projects or routed full kernel'}
allowed={'.json','.log','.rpt','.txt','.tcl','.jou','.vec','.hpp','.cpp','.sv','.py','.md','.prj','.sh'}
paths=[]
for name in ['services_a','services_b','services_payload_c','services_payload_d','services_dest_probe','services_memory_synth']:
 for f in (results/name).rglob('*'):
  if not f.is_file() or f.suffix not in allowed:continue
  if '.Xil' in f.parts or '__pycache__' in f.parts:continue
  if '.vivado-ai' in f.parts and f.suffix not in {'.log','.jou'}:continue
  paths.append(f)
for f in (root/'accel/lookahead/fpga_descriptor_front/services').iterdir():
 if f.is_file() and f.suffix in allowed:paths.append(f);manifest['live_sources'][str(f.relative_to(root))]=sha(f.read_bytes())
for i,f in enumerate(sorted(set(paths))):
 b=f.read_bytes();rel=str(f.relative_to(root));name=f'files/{i:05d}_{f.name}';compressed=len(b)>8192
 if compressed:name+='.gz'
 target=out/name;target.parent.mkdir(exist_ok=True);target.write_bytes(gzip.compress(b,mtime=0) if compressed else b)
 manifest['files'].append({'source':rel,'archive':name,'compression':'gzip' if compressed else 'identity','bytes':len(b),'sha256':sha(b)})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('SERVICE_ARCHIVE_CREATED',len(manifest['files']))
