"""Verify an explicit append-only evidence snapshot and normally publish exact paths."""
from pathlib import Path
import datetime,fcntl,gzip,hashlib,json,os,subprocess,time
from publication_guard import clean_entry
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_sparse_stream_r2_20261112'
def publish(tag,roots,scope,receipt_dir):
 out=R/'evidence_snapshot'/tag;out.mkdir(exist_ok=False);records=[]
 for name in roots:
  base=R/name
  assert base.exists(),name
  files=[base] if base.is_file() else sorted(base.rglob('*'))
  for p in files:
   if not p.is_file() or any(x in p.parts for x in ['build','.git']):continue
   if p.suffix not in {'.json','.jsonl','.csv','.log','.stderr','.bin','.sv','.tcl','.xdc','.rpt','.py','.cpp','.hpp','.md','.yaml','.txt'}:continue
   if p.name in ['native_input.bin','workload.bin','prepared.bin','representative_wave.bin']:continue
   raw=p.read_bytes();dest=out/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);compressed=len(raw)>16384
   if compressed:dest=dest.with_name(dest.name+'.gz')
   dest.write_bytes(gzip.compress(raw,mtime=0) if compressed else raw)
   check=gzip.decompress(dest.read_bytes()) if compressed else dest.read_bytes();assert check==raw
   records.append({'raw_path':str(p.relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'archive':str(dest.relative_to(out))})
 manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':scope,'roots':roots,'files':records,'all_archived_bytes_verified':True}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 lock=(R/'supervision/independent_branch_publish.lock').open('a');fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
 clean_entry(ROOT)
 branch='accel/lookahead-sparse-stream-r2-20261112';assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==branch
 subprocess.run(['git','merge-base','--is-ancestor','5af99087a9d7055d468cc5269326d985b911919d','HEAD'],cwd=ROOT,check=True)
 files=[p for p in out.rglob('*') if p.is_file()];assert sum(p.stat().st_size for p in files)<800_000_000,'split snapshot required'
 spec=receipt_dir/'paths.nul';spec.write_bytes(b'\0'.join(str(p.relative_to(ROOT)).encode() for p in files)+b'\0')
 subprocess.run(['git','add','-f','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],cwd=ROOT,check=True)
 subprocess.run(['git','commit','-q','-m','Archive independent result chain: '+tag],cwd=ROOT,check=True)
 sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();env=os.environ.copy()
 for k in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy']:env.pop(k,None)
 with (receipt_dir/'push.log').open('x') as f:rc=subprocess.run(['git','-c','http.proxy=','-c','http.version=HTTP/1.1','-c','http.postBuffer=2147483647','push','origin','HEAD:refs/heads/'+branch],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
 remote=subprocess.check_output(['git','-c','http.proxy=','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,env=env,text=True).split()[0]
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'local_sha':sha,'remote_sha':remote,'verified':sha==remote,'push_returncode':rc,'snapshot':tag}
 (receipt_dir/'delivery.json').write_text(json.dumps(result,indent=2)+'\n');assert remote==sha;return result
