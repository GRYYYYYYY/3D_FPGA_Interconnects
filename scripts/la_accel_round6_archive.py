"""Archive compact, reviewable R6 receipts; retain raw failed attempts in place."""
import json,sys,tarfile,gzip,io,shutil,subprocess
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();out=r/'evidence_snapshot';out.mkdir(exist_ok=False)
selected=[]
for p in r.glob('*.json'):
 if p.name.startswith(('gpu_resources','gpu_doctor','gpu_status','gpu_submit')):continue
 selected.append(p)
selected+=list(r.glob('*.log'))
for folder in ['large','lifecycle','native','native_required','native_live_verified']:
 for p in (r/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.json','.log']:selected.append(p)
for name in ['measurements.json','binding.json','commands.json','build.log']:
 p=r/'rr_diagnostic'/name
 if p.exists():selected.append(p)
selected+=list((r/'rr_diagnostic').glob('*/process.log'))
for name in ['commands.json','measurements.json','worker.json','inputs.json','finished.json','gpu.log','lscpu.log','nvcc.log','compiler.log','build_cpu.log','build_cuda.log']:
 p=r/'gpu_worker'/name
 if p.exists():selected.append(p)
# Preserve every CUDA functional/failure log in a compact archive; measured logs too.
def bundle(name,paths):
 with (out/name).open('wb') as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as gz:
   with tarfile.open(fileobj=gz,mode='w|') as tf:
    for p in sorted(paths):
     info=tf.gettarinfo(str(p),arcname=str(p.relative_to(r)));info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';
     with p.open('rb') as source:tf.addfile(info,source)
bundle('validation_logs.tar.gz',list((r/'validation').glob('*.log')))
bundle('gpu_logs.tar.gz',list((r/'gpu_worker').glob('*.log')))
selected.append(r/'validation/validation.json')
for p in selected:
 d=out/p.relative_to(r);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
# Include all new source bindings and published outputs, without large RRG duplication.
output_bindings=[]
for directory in [r/'validation',r/'large',r/'native_live_verified',r/'gpu_worker']:
 for p in directory.rglob('*'):
  if p.is_file() and p.suffix in ['.bin','.route','.so'] and 'source' not in p.parts:output_bindings.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha256(p)))
source_paths=list((R/'accel/lookahead/round6').glob('*'))+list((R/'scripts').glob('la_accel_round6_*.py'))+[R/'docs/lookahead_accel_round6_screen.md']
sources={str(p.relative_to(R)):sha256(p) for p in source_paths if p.is_file()}
(out/'source_bindings.json').write_text(json.dumps(sources,indent=2))
(out/'output_bindings.json').write_text(json.dumps(output_bindings,indent=2))
status=json.load(open(r/'gpu_status_final.json'));s=status['Result'];(out/'gpu_terminal_receipt.json').write_text(json.dumps({k:s.get(k) for k in ['job_id','name','status','timeline','gpu_count','logic_compute_group_id','max_running_time_ms']},indent=2))
manifest=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha256(p)) for p in sorted(out.rglob('*')) if p.is_file()]
(out/'index.json').write_text(json.dumps(dict(base_commit='ab0a4afce89c567cf30f24c8a813d78884872f05',files=manifest,exclusions='Raw binaries, large input RRG/export copies, node images, credentials, vendor copies, route files: retained in place and/or SHA-bound. No old evidence changed.'),indent=2))
print(len(manifest),'files',sum(x['bytes'] for x in manifest),'bytes')
