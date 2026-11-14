from run_profile import *
import os

def main():
 out=R/'front_a';out.mkdir(exist_ok=False)
 cmd=['g++','-O3','-std=c++17','-ffp-contract=off',*['-I'+str(ROOT/'accel/lookahead'/p) for p in ['include','round6_1','fpga_sparse_stream_r2']],str(S/'frontend_model.cpp'),'-o',str(out/'front')]
 with (out/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 b=json.loads((R/'profile_a/reused_binding.json').read_text());manifest=json.loads(git_bytes('results/fpga_pending_stream_20261114/evidence_snapshot/manifest.json'));tasks=[]
 for old in b['input_receipts']:
  case=Path(old['command'][3]).name;d=out/case;d.mkdir()
  for rec in manifest['files']:
   raw=rec['raw_path']
   if not raw.startswith('capture_a/'+case+'/wave_') or not raw.endswith('.bin'):continue
   blob=git_bytes('results/fpga_pending_stream_20261114/evidence_snapshot/'+rec['archive']);data=gzip.decompress(blob) if rec['archive'].endswith('.gz') else blob
   assert hashlib.sha256(data).hexdigest()==rec['sha256'];p=d/Path(raw).name;p.write_bytes(data)
   for v in 'ABC':tasks.append((case,p,old['command'][1],v))
 def run(task):
  case,trace,workload,v=task;d=out/case;prefix=trace.stem+'_'+v;cmd=[str(out/'front'),workload,str(trace),v,str(d/(prefix+'.json'))];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with (d/(prefix+'.log')).open('x') as f:
   p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);(d/(prefix+'.running.json')).write_text(json.dumps({'pid':p.pid,'command':cmd,'start':start}));rc=p.wait()
  x={'command':cmd,'returncode':rc,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trace_sha256':sha(trace),'binary_sha256':sha(out/'front')};(d/(prefix+'.receipt.json')).write_text(json.dumps(x,indent=2));return x
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,tasks))
 (out/'terminal.json').write_text(json.dumps({'all_pass':all(x['returncode']==0 for x in rows),'results':rows},indent=2));assert all(x['returncode']==0 for x in rows)
if __name__=='__main__':main()
