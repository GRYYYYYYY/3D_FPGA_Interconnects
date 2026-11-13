"""Wait for the authorized six recovered native batches, archive and push normally.

Run only after an initial checkpoint is committed/pushed. Never restarts a batch,
changes a historical receipt, resets a branch, or stages unrelated changes.
"""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,os,subprocess,sys,time
from publication_guard import clean_entry,owned_exit
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';scripts=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('tag');ap.add_argument('predecessor');ap.add_argument('predecessor_verification');a=ap.parse_args()
d=r/'supervision'/a.tag;d.mkdir(exist_ok=False);branch='accel/lookahead-sparse-stream-r2-20261112'
lock=(r/'supervision/continuation_finalize.lock').open('a');fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def record(name,x):
 with (d/(name+'.json')).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def execute(name,cmd,env=None):
 with (d/(name+'.log')).open('x') as log:rc=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 record(name,{'command':cmd,'returncode':rc,'utc':utc()});assert rc==0,name
record('started',{'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().split()[21],'utc':utc(),'predecessor':a.predecessor,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'scope':'six already authorized full native40 runs only; append-only archive, independent branch push'})
try:
 while True:
  p=r/'supervision/p8_f0_recovered_native_2110b.json';state=json.loads(p.read_text())
  if state['status']=='completed_audited_bound':break
  if state['status']=='failed_preserved':raise RuntimeError('native stage failed; all existing outputs retained')
  time.sleep(30)
 assert len(state['runs'])==3 and all(x['status']=='completed_audited_bound' for x in state['runs'].values())
 # Revalidate complete recovery identity before accepting the terminal supervisor.
 from recovery_evidence import validate_recovery
 plan=json.loads((root/'accel/lookahead/fpga_sparse_stream_r2/config/p8_f0_recovery_plan.json').read_text());validate_recovery(plan['recovery_manifest'],plan)
 tag='checkpoint_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_recovered_native'
 observation_tag=a.tag+'_native_complete'
 publish_lock=(r/'supervision/independent_branch_publish.lock').open('a');fcntl.flock(publish_lock.fileno(),fcntl.LOCK_EX)
 clean_entry(root)
 record('clean_before_generation',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'utc':utc()})
 execute('observe',[sys.executable,str(scripts/'observe_continuation.py'),observation_tag])
 owned=r/'continuation_82860ce/current_manifest.json';owned_sha=hashlib.sha256(owned.read_bytes()).hexdigest()
 gpu_config=json.loads((root/'accel/lookahead/fpga_sparse_stream_r2/config/current_software_run.json').read_text())
 gpu=r/'software'/gpu_config['run_tag']
 if (gpu/'completed.json').exists() and not (gpu/'summary.json').exists():
  execute('analyze_GPU',[sys.executable,str(scripts/'analyze_private_inf_software.py'),gpu_config['run_tag']])
 execute('freeze',[sys.executable,str(scripts/'freeze_checkpoint.py'),tag,a.predecessor,'--defer-running-batches','--defer-running-rtl','--include-completed-recovery'])
 verification='supervision/'+a.tag+'/verified_delta.json'
 execute('verify',[sys.executable,str(scripts/'verify_snapshot_delta.py'),tag,a.predecessor_verification,verification])
 # Publish complete verified evidence in bounded packs. Refuse any user/index dirt.
 assert subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()==branch
 assert subprocess.run(['git','merge-base','--is-ancestor','82860ced203bde54f1fa267446b3d0edc521a293','HEAD'],cwd=root).returncode==0
 owned_exit(root,{str(owned.relative_to(root)):owned_sha})
 pointer=json.loads(owned.read_text());obs=r/pointer['authoritative_observation']
 assert obs.name=='observation_'+observation_tag+'.json' and hashlib.sha256(obs.read_bytes()).hexdigest()==pointer['observation_sha256']
 assert subprocess.run(['git','diff','--cached','--quiet'],cwd=root).returncode==0,'index changed; preserve results'
 folder=r/'evidence_snapshot'/tag;groups=[];group=[];size=0
 for p in sorted(folder.rglob('*')):
  if not p.is_file() or p.name=='manifest.json':continue
  n=p.stat().st_size
  if size+n>800_000_000 and group:groups.append(group);group=[];size=0
  group.append(p);size+=n
 if group:groups.append(group)
 groups[-1]+=[folder/'manifest.json',r/verification,r/'continuation_82860ce/current_manifest.json',r/'continuation_82860ce'/('observation_'+observation_tag+'.json')]
 env=os.environ.copy()
 for k in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy']:env.pop(k,None)
 for i,files in enumerate(groups):
  pathspec=d/f'paths_{i}.nul';pathspec.write_bytes(b'\0'.join(str(p.relative_to(root)).encode() for p in files)+b'\0')
  execute(f'add_{i}',['git','add','-f','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul'])
  execute(f'commit_{i}',['git','commit','-m',f'Archive recovered P8/F0 complete batch evidence ({i+1}/{len(groups)})'])
  sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
  cmd=['git','-c','http.proxy=','-c','http.version=HTTP/1.1','-c','http.postBuffer=2147483647','-c','pack.threads=4','push','origin','HEAD:refs/heads/'+branch]
  with (d/f'push_{i}.log').open('x') as log:rc=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
  remote=subprocess.check_output(['git','-c','http.proxy=','ls-remote','origin','refs/heads/'+branch],cwd=root,env=env,text=True).split()[0]
  record(f'push_{i}',{'local_sha':sha,'remote_sha':remote,'push_returncode':rc,'verified':remote==sha,'utc':utc()});assert remote==sha
 record('terminal',{'status':'completed_archived_remote_verified','utc':utc(),'snapshot':tag,'remote_sha':remote,'six_native_batches':True,'other_jobs_not_implied_complete':True})
except Exception as error:
 record('failed_preserved',{'utc':utc(),'error':repr(error),'no_history_deleted':True});raise
