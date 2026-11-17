#!/usr/bin/env python3
"""Publication protection checks. Read-only for inputs, FPGA and frozen papers."""
from pathlib import Path
import argparse,json,hashlib,subprocess,datetime,time,os
H=Path(__file__).resolve().parent;ROOT=H.parents[2];BASE=ROOT.parent
V1=BASE/'3D_FPGA_Interconnects_PAPER_CPU_GPU_V1';MIG=BASE/'3D_FPGA_Interconnects_DEVICE_MIGRATION';PAUSE=MIG/'accel/lookahead/fpga_device_migration/pause_20261117';RAW=MIG/'results/fpga_device_migration_20261117/migration_a'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def stamp(p):
 s=p.stat();return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,inode=s.st_ino,device=s.st_dev)
def ident(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text().rsplit(') ',1)[1].split();return dict(pid=pid,start_ticks=int(s[19]),pgid=int(s[2]),state=s[0],cpu_ticks=int(s[11])+int(s[12]))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);ap.add_argument('--light',action='store_true');a=ap.parse_args()
 baseline=read(V1/'paper/dac2027_cpu_gpu_algorithm_first/evidence/protection_baseline.json');refs=baseline['refs']|{'paper/dac2027-cpu-gpu-algorithm-first-20261117':'4d0c4e88c1823ae554d6b4a891b53875b438cdec'}
 for ref,h in refs.items():assert subprocess.check_output(['git','rev-parse',ref],cwd=ROOT,text=True).strip()==h,ref
 files={V1/p:h for p,h in baseline['files'].items()}
 files.update({V1/p:h for p,h in read(V1/'paper/dac2027_cpu_gpu_algorithm_first/evidence/prior_submission_hashes.json').items()})
 for n,h in {'main.pdf':'907bf83496b1a3c546180e569dbff88f122bc9ea6427c809337accdd5381ba62','submission_source.zip':'42b3838328d7a217b8c8c5806d3d88a6ff1cbd285370d79205b34033039c5d04'}.items():files[V1/'paper/dac2027_cpu_gpu_algorithm_first'/n]=h
 files.update({RAW/p:h for p,h in read(PAUSE/'protected_before.json').items()})
 for x in read(PAUSE/'verification.json')['complete_dcps']:files[Path(x['path'])]=x['sha256']
 for c in read(H/'input_manifest.json').values():
  for x in c['case']['inputs'].values():files[Path(x['path'])]=x['sha256']
 for x in read(H/'source_binding.json')['binary'].values():files[Path(x['path'])]=x['sha256']
 for x in read(H/'runtime.json')['libraries']:files[Path(x['path'])]=x['sha256']
 prior=read(H/'receipts/deep_protection.json')['files'] if a.light else {}
 checked={}
 for p,h in files.items():
  before=stamp(p)
  if a.light:assert prior[str(p)]['sha256']==h and prior[str(p)]['stat']==before,str(p)
  else:assert sha(p)==h,str(p)
  assert stamp(p)==before,str(p)
  checked[str(p)]=dict(sha256=h,stat=before)
 beat=read(RAW/'pause_heartbeat.json');assert time.time()-datetime.datetime.fromisoformat(beat['utc']).timestamp()<100
 assert beat['state'].startswith('PAUSED_BY_USER') and not beat['auto_resume_allowed'] and not beat['budget_signals_allowed'] and not beat['terminal_publication_allowed']
 assert sha(PAUSE/'pause_control.py')==beat['loaded_code_sha256']=='e62b6da35d4e81857bd5d1ea46ed8e5ed8095c97b8c1e626ad8ba70d9d94bb90'
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='2c285022-7829-4b21-84d8-176f6732a754'
 members=[];thread_count=0
 for old in beat['snapshot']['members']:
  now=ident(old['pid']);assert now['start_ticks']==old['start_ticks'] and now['pgid']==1144478 and now['state']=='T' and now['cpu_ticks']==old['cpu_ticks']
  for task in (Path('/proc')/str(old['pid'])/'task').iterdir():
   assert (task/'stat').read_text().rsplit(') ',1)[1].split()[0]=='T';thread_count+=1
  members.append(now)
 found=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   x=ident(int(p.name))
   if x['pgid']==1144478:found.append(x['pid'])
  except (OSError,ValueError):pass
 assert set(found)=={x['pid'] for x in members};assert sum(x['cpu_ticks'] for x in members)==6168669
 owner=ident(3982419);assert owner['start_ticks']==185273769
 locks=[l for l in Path('/proc/locks').read_text().splitlines() if len(l.split())>4 and l.split()[4]=='3982419'];assert len(locks)>=2
 report=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',mode='metadata recheck against prior full hashes' if a.light else 'full hashes',refs=refs,files=checked,FPGA=dict(state=beat['state'],members=members,stopped_threads=thread_count,cpu_ticks=6168669,observer=owner,observer_locks=locks,automatic_resume=False,original_budget_immutable=True),V1_unchanged=True)
 target=H/'receipts'/(a.label+'.json');target.write_text(json.dumps(report,indent=2)+'\n')
 if not a.light:(H/'receipts/deep_protection.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(status='PASS',protected_files=len(files),FPGA_state=beat['state'],stopped_threads=thread_count,receipt=str(target))))
if __name__=='__main__':main()
