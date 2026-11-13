"""Create append-only compact evidence snapshots; never rewrite raw run evidence."""
from pathlib import Path
import gzip,hashlib,json,shutil,sys,subprocess
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'evidence_snapshot'/sys.argv[1];out.mkdir(parents=True,exist_ok=False)
# Optional predecessor: retain an append-only delta instead of recopying every
# unchanged historical trace. The manifest explicitly binds the predecessor.
previous=sys.argv[2] if len(sys.argv)>2 else None
defer_running='--defer-running-batches' in sys.argv[3:]
defer_rtl='--defer-running-rtl' in sys.argv[3:]
running=[]
running_rtl=[]
completed_recovery_dirs=set()
if '--include-completed-recovery' in sys.argv:
 from recovery_evidence import validate_recovery
 for terminal in (r/'recovery').glob('*/terminal.json'):
  receipt=json.loads(terminal.read_text())
  if receipt.get('status')!='passed':continue
  qpath=terminal.parent/'qualification.json';q=json.loads(qpath.read_text())
  validate_recovery(str(qpath.relative_to(r)),q)
  for key in ['hot_summary','boundary_calibration','fixed10ns_calibration']:
   completed_recovery_dirs.add((r/q[key]).parent)

if defer_rtl:
 for receipt in (r/'rtl').glob('*_pipeline_receipt.json'):
  state=json.loads(receipt.read_text())
  if state.get('status')=='running':running_rtl.append(state['variant'])
if defer_running:
 for receipt in (r/'model').glob('*/large*/*/receipt.json'):
  if json.loads(receipt.read_text()).get('status')=='running':running.append(receipt.parent)
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
 # Running complete batches retain all raw evidence locally. Checkpoint only
 # their status/progress now; freeze their full traces after terminal receipts.
 if any(parent==p.parent for parent in running) and p.name not in ['receipt.json','progress.json']:continue
 rel=p.relative_to(r)
 # Large RTL traces are final only after their pipeline terminates. Keep
 # source/build bindings and JSON status now; preserve completed raw traces
 # in the next snapshot instead of repeatedly archiving growing prefixes.
 if (len(rel.parts)>2 and rel.parts[0]=='rtl' and
     any(rel.parts[1].startswith(v+'_') and rel.parts[1]!=v+'_build' for v in running_rtl)
     and p.suffix in ['.csv','.bin','.log']
     and not any(parent==p.parent or parent in p.parents for parent in completed_recovery_dirs)):continue
 # XSim unit runners freeze their SV directly inside rtl/<run>, unlike
 # Verilator runs which use source/. Preserve those exact unit test versions
 # too, while continuing to exclude generated C++ and simulator binaries.
 unit_sv=p.suffix=='.sv' and p.parent.parent==r/'rtl'
 if p.suffix in ['.json','.csv','.log'] or ('source' in p.parts and p.suffix in ['.sv','.cpp','.hpp']) or unit_sv:
  # Exclude generated compiler logs only when they are pure C++ build output;
  # Verilator diagnostics/build failures remain in the compact evidence.
  files.append(p)
 if p.name in ['output.bin','representative_wave.bin']:files.append(p)
 if p.suffix=='.jsonl' and rel.parts[0] in ['accumulator','software']:files.append(p)
manifest=[]
for p in sorted(set(files)):
 rel=p.relative_to(r);dest=out/rel
 if p.stat().st_size>16384:dest=dest.with_name(dest.name+'.gz')
 dest.parent.mkdir(parents=True,exist_ok=True)
 raw=p.read_bytes()
 if known.get(str(rel))==hashlib.sha256(raw).hexdigest():continue
 record={'raw_path':str(rel),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 # Complete-batch commit traces can exceed hosting single-file limits even
 # after compression. Preserve exact bytes in individually bounded chunks.
 if len(raw)>64*1024*1024:
  parts=[];folder=out/rel.parent/(rel.name+'.parts');folder.mkdir(exist_ok=True)
  for offset in range(0,len(raw),64*1024*1024):
   block=raw[offset:offset+64*1024*1024];part=folder/(f'{len(parts):06d}.gz')
   part.write_bytes(gzip.compress(block,compresslevel=6,mtime=0))
   parts.append({'archive':str(part.relative_to(out)),'offset':offset,'bytes':len(block),'sha256':hashlib.sha256(block).hexdigest()})
  record['archive_parts']=parts
 else:
  if dest.suffix=='.gz':dest.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
  else:dest.write_bytes(raw)
  record['archive']=str(dest.relative_to(out))
 manifest.append(record)
(out/'manifest.json').write_text(json.dumps({'scope':'checkpoint; raw evidence retained; active Vivado timing runs excluded until completed','predecessor':previous,'deferred_running_batches':[str(x.relative_to(r)) for x in running],'deferred_running_rtl_variants':running_rtl,'completed_recovery_dirs':[str(p.relative_to(r)) for p in sorted(completed_recovery_dirs)],'files':manifest,'source_base':'5651a34abb97939bee6402c5af585753ab07f64b'},indent=2)+'\n')
print('FROZEN',len(manifest),sum(x['bytes'] for x in manifest),'raw bytes',sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'archive bytes')
