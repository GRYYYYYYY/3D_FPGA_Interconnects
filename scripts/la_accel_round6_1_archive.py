"""Archive lightweight evidence and bind retained raw files without staging dependencies."""
import sys,json,hashlib,tarfile,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();e=r/'evidence_snapshot';assert e.exists()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(n,x):(e/n).write_text(json.dumps(x,indent=2)+'\n')
files=[];raw=[]
for p in sorted(r.rglob('*')):
 if not p.is_file() or p.is_symlink() or e in p.parents:continue
 rel=p.relative_to(r);parts=rel.parts
 if parts[:2]==('gpu_worker','source'):continue # bound by worker source hashes
 if p.name in ['gpu_resources.json','gpu_status.json','gpu_doctor.json','gpu_submit.json']:continue # account API responses stay local
 if p.suffix in ['.log','.json','.py'] or (parts[0]=='native_build' and len(parts)>1 and parts[1]=='source') or (parts[0] in ['compact_errors','direct_errors'] and p.suffix=='.bin'):
  if p.stat().st_size<16*1024*1024:files.append(p)
 if p.suffix in ['.bin','.so','.route','.out'] or p.name in ['cpu61','strict61','cuda61','cuda6','cache61','vpr_flat']:
  raw.append(dict(path=str(p),relative_path=str(rel),size_bytes=p.stat().st_size,sha256=sha(p)))
with tarfile.open(e/'run_logs.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(r)),recursive=False)
write('raw_artifacts.json',raw)
write('archived_files.json',[dict(path=str(p.relative_to(r)),size_bytes=p.stat().st_size,sha256=sha(p)) for p in files])
binding=json.loads((r/'gpu_worker/native/runner_binding.json').read_text());assert sha(R/'scripts/la_accel_round6_1_native_worker.py')==binding['sha256'],'native runner changed after start'
source_files=list((R/'accel/lookahead/round6_1').glob('*'))+list((R/'scripts').glob('la_accel_round6_1_*.py'))
write('source_binding.json',{str(p.relative_to(R)):sha(p) for p in source_files if p.is_file()})
compiled=[]
for p in (r/'gpu_worker/source/round6_1').glob('*'):
 if p.suffix not in ['.cpp','.cu','.hpp','.cuh','.h']:continue
 current=R/'accel/lookahead/round6_1'/p.name
 normalized=lambda x:'\n'.join(z.rstrip() for z in x.read_text().splitlines())
 assert normalized(p)==normalized(current),'compiled source semantics changed'
 compiled.append(dict(path=str(current.relative_to(R)),worker_sha256=sha(p),committed_sha256=sha(current),equal_after_trailing_whitespace_normalization=True))
write('compiled_source_binding.json',dict(files=compiled,note='cpu61.cpp blank-line trailing whitespace removed after measurements; no token changes; frozen worker source hashes retained'))

orig=R.parent/'3D_FPGA_Interconnects';tracked=subprocess.check_output(['git','diff','--name-only','480ba6d5cc2b9d73696a44315777c0e658d8a7b4'],cwd=R,text=True).splitlines()
assert all(x.startswith(('accel/lookahead/round6_1/','scripts/la_accel_round6_1_','docs/lookahead_accel_round6_1_','results/lookahead_accel_round6_1_')) for x in tracked)
assert not subprocess.check_output(['git','diff','--name-only'],cwd=orig,text=True).strip()
write('preservation.json',dict(original_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=orig,text=True).strip(),main=subprocess.check_output(['git','rev-parse','refs/heads/main'],cwd=R,text=True).strip(),base='480ba6d5cc2b9d73696a44315777c0e658d8a7b4',original_tracked_unchanged=True,original_untracked_guides={str(p.relative_to(orig)):sha(p) for p in list((orig/'docs').glob('CODEX*'))+list((orig/'CODEX_LOOKAHEAD_ROUND6_1_NATIVE_COMPACT_PACKAGE').glob('*')) if p.is_file()},scope='new R6.1 files only; dependency symlinks excluded from commit'))
write('attempts.json',[dict(attempt='CPU first compilation',status='failed_then_fixed',reason='Compact span construction used iterator where raw pointer required; changed to data() before all validation',evidence='initial tool output; no claim of a retained compiler log'),dict(attempt='native_cpu_qualification',status='failed_before_solver',reason='missing ignored historical s38417 case link in isolated worktree',log='native_cpu_qualification.log'),dict(attempt='native_cpu_qualification_b',status='complete',receipt='native_cpu_qualification_b/runs.json'),dict(attempt='GPU worker',receipt='gpu_worker/finished.json'),dict(attempt='cache screen',receipt='cache_screen/finished.json'),dict(attempt='invalid input/lifecycle cases',status='expected_rejection_results_retained')])
write('archive_sha256.json',{p.name:sha(p) for p in e.iterdir() if p.is_file() and p.name!='archive_sha256.json'})
print('archived',len(files),'small records;',len(raw),'raw bindings')
