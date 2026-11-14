from pathlib import Path
import subprocess,json,hashlib,concurrent.futures,datetime,gzip
ROOT=Path(__file__).resolve().parents[3];S=ROOT/'accel/lookahead/fpga_decoupled_front';R=ROOT/'results/fpga_decoupled_front_20261114';BASE='059ec4cc7c7c3793398016c0713c29a0e0c6d46a'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def git_bytes(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
def main():
 out=R/'profile_a';out.mkdir(parents=True,exist_ok=False);src=out/'source';src.mkdir()
 files=[S/'profile_reference.cpp',S/'physical_profile.hpp',ROOT/'accel/lookahead/fpga_sparse_stream_r2/pending17.hpp',*(ROOT/'accel/lookahead/include').glob('*.hpp'),*(ROOT/'accel/lookahead/round6_1').glob('*.hpp')]
 for p in files:(src/p.name).write_bytes(p.read_bytes())
 cmd=['g++','-O3','-std=c++17','-ffp-contract=off','-DPROFILE_PRIVATE_INF=1','-I'+str(src),str(src/'profile_reference.cpp'),'-o',str(out/'profile')]
 with (out/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 b=json.loads(git_bytes('results/fpga_pending_stream_20261114/evidence_snapshot/stage_a_v2/binding.json'));(out/'reused_binding.json').write_text(json.dumps(b,indent=2))
 (out/'source_binding.json').write_text(json.dumps({'command':cmd,'sha256':{p.name:sha(p) for p in src.iterdir()},'binary_sha256':sha(out/'profile'),'base':BASE},indent=2))
 def run(old):
  case=Path(old['command'][3]).name;d=out/case;d.mkdir();cmd=[str(out/'profile'),*old['command'][1:3],str(d),'524288','524288','--no-prepared-export'];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  assert sha(Path(cmd[1]))==old['workload_sha256']
  with (d/'console.log').open('x') as f:
   p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);(d/'running.json').write_text(json.dumps({'pid':p.pid,'start_utc':start,'command':cmd},indent=2));rc=p.wait()
  x={'command':cmd,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':rc,'input_sha256':old['workload_sha256'],'output_sha256':sha(d/'output.bin') if rc==0 else None,'expected_output_sha256':old['output_sha256']};x['output_exact']=rc==0 and x['output_sha256']==x['expected_output_sha256'];(d/'receipt.json').write_text(json.dumps(x,indent=2));return x
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,b['input_receipts']))
 (out/'terminal.json').write_text(json.dumps({'all_pass':all(x['output_exact'] for x in rows),'results':rows},indent=2));assert all(x['output_exact'] for x in rows)
if __name__=='__main__':main()
