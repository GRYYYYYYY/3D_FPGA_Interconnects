"""Create a compact, lossless evidence snapshot. Raw runs remain untouched."""
from pathlib import Path
import gzip,hashlib,json,shutil
root=Path(__file__).resolve().parents[3];r=root/'results/fpga_sparse_stream_20261112';dest=r/'evidence_snapshot'
dest.mkdir(exist_ok=True);catalog=[]
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def keep(p,relative=None,compress=False):
 if not p.is_file():return
 relative=Path(relative or p.relative_to(r));out=dest/relative
 if compress:out=out.with_name(out.name+'.gz')
 out.parent.mkdir(parents=True,exist_ok=True)
 if compress:
  with open(p,'rb') as i,open(out,'wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as o:shutil.copyfileobj(i,o)
 else:shutil.copy2(p,out)
 catalog.append({'local_source':str(p.relative_to(r)),'archived':str(out.relative_to(dest)),
                 'uncompressed_bytes':p.stat().st_size,'uncompressed_sha256':digest(p),'archive_sha256':digest(out)})
for name in ['analysis.json','optimistic_bound.json','prior_diagnosis.json','verification.json','batch_capacity_tests.json','config_initial.json','physical_audit.json']:
 keep(r/name)
for f in (r/'figures').glob('*'):keep(f)
cases=['native_d3_w8','native_d4_w8','bnn_export','lstm_s2','stress','stress_random','batch64','batch65']
for name in cases:
 d=r/name;functional=d/'functional' if (d/'functional').exists() else d
 for f in functional.iterdir():
  if f.suffix in ['.json','.csv','.log'] or f.name=='output.bin':keep(f,compress=f.suffix in ['.csv','.bin'])
 for f in d.glob('*.json'):keep(f)
 if name in ['stress','stress_random','batch64','batch65']:
  keep(d/'workload.bin',compress=True);keep(d/'reference.bin',compress=True)
  keep(functional/'prepared.bin',compress=True)
 elif name.startswith('native'):keep(functional/'prepared.bin',compress=True)
 for f in (r/'capacity_audit'/name).glob('*'):
  if f.suffix in ['.json','.log']:keep(f)
for f in (r/'capacity_audit').glob('*.json'):keep(f)
keep(r/'capacity_audit/source.cpp')
for name in ['batch_f1','f0_batch']:
 for record in (r/'calibration').glob(name+'_*.json'):keep(record)
 for d in (r/'calibration').glob(name+'_*'):
  if not d.is_dir():continue
  hashes={}
  for f in d.iterdir():
   if f.is_file():hashes[f.name]=digest(f)
   if f.suffix in ['.json','.log']:keep(f)
   if d.name.endswith('_rtl') and f.name in ['cycles.csv','commits.csv','output.bin']:keep(f,compress=f.suffix=='.csv')
  out=dest/d.relative_to(r)/'raw_artifact_sha256.json';out.write_text(json.dumps(hashes,indent=2)+'\n')
 for f in (r/(name+'_build')/'source').glob('*'):keep(f)
 keep(r/(name+'_build')/'source_binding.json')
 for f in (r/(name+'_model_source')).glob('*'):keep(f)
 keep(r/(name+'_build.log'),compress=True)
for d in ['batch_native_d3_w8_xsim','batch65/rejected']:
 for f in (r/d).rglob('*'):
  if f.suffix in ['.sv','.json','.txt','.hex'] or f.name in ['run.log','compile.log','elaborate.log']:keep(f,compress=f.suffix=='.hex')
for f in r.glob('owner*'):
 if f.is_file() and f.suffix in ['.log','.csv','.json']:keep(f,compress=f.suffix=='.csv')
for f in (r/'owner_changed_eviction').glob('*'):
 if f.is_file():keep(f,compress=f.suffix in ['.log','.csv'])
for f in (r/'owner_changed_eviction/source').glob('*'):keep(f)
# Retain all earlier summaries, failures and their source bindings without
# duplicating generated object files or enormous equal cycle streams.
historical=[]
for f in list(r.rglob('*')):
 if not f.is_file() or dest in f.parents:continue
 rel=f.relative_to(r)
 if any(x in rel.parts for x in ['plot_cache','.Xil','xsim.dir']):continue
 if f.suffix in ['.json','.log','.rpt','.stderr','.txt'] and f.name!='WORK_STATE.txt':
  if 'tile_ooc_resident_batch' in rel.parts:continue
  if 'source' not in rel.parts and f.stat().st_size<5_000_000:
   keep(f,Path('history')/rel,compress=f.suffix in ['.log','.stderr'])
 elif f.name in ['cycles.csv','commits.csv','waves.csv','output.bin','prepared.bin','workload.bin']:
  historical.append({'path':str(rel),'bytes':f.stat().st_size,'sha256':digest(f)})
for name in ['owner_ooc','tile_ooc_p1','tile_ooc_commit16','tile_ooc_resident_batch','p1_frozen','pre_batch_output_revision','attempts']:
 for f in (r/name).rglob('*'):
  if f.is_file() and f.suffix in ['.sv','.tcl','.hpp','.cpp','.py','.md','.json','.rpt','.txt','.log','.csv','.tsv','.jou']:
   if any(x in f.parts for x in ['.Xil','xsim.dir','build']):continue
   keep(f,compress=f.suffix in ['.log','.csv'])
checkpoints=[]
for f in r.glob('*ooc*/**/*.dcp'):
 checkpoints.append({'path':str(f.relative_to(r)),'bytes':f.stat().st_size,'sha256':digest(f),'local_only':True})
(dest/'local_raw_manifest.json').write_text(json.dumps(historical,indent=2)+'\n')
(dest/'checkpoint_manifest.json').write_text(json.dumps(checkpoints,indent=2)+'\n')
(dest/'archive_manifest.json').write_text(json.dumps(catalog,indent=2)+'\n')
print('archived_files',len(list(dest.rglob('*'))),'bytes',sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()))
