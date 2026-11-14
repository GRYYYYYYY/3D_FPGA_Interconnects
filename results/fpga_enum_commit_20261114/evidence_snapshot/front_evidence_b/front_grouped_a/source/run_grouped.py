from run_compare import *
def main():
 out=ROOT/'results/fpga_enum_commit_20261114/front_grouped_a';out.mkdir(exist_ok=False);(out/'source').mkdir()
 for p in S.iterdir():
  if p.is_file():(out/'source'/p.name).write_bytes(p.read_bytes())
 cmd=['g++','-O3','-std=c++17','-ffp-contract=off',*['-I'+str(ROOT/'accel/lookahead'/x) for x in ['include','round6_1','fpga_sparse_stream_r2']],str(S/'frontend_model.cpp'),'-o',str(out/'front')]
 with (out/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 (out/'binding.json').write_text(json.dumps({'command':cmd,'sha256':{p.name:sha(p) for p in (out/'source').iterdir()},'binary_sha256':sha(out/'front')},indent=2))
 old=json.loads((R/'terminal.json').read_text());tasks=[]
 for rec in old['receipts']:
  cmd=rec['command']
  if cmd[-1]!='8':continue
  case=Path(cmd[2]).parent.name;d=out/case;d.mkdir(exist_ok=True);new=[str(out/'front'),*cmd[1:]];new[4]=str(d/Path(cmd[4]).name);new.append('grouped');tasks.append(new)
 def run(cmd):
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with Path(cmd[4]+'.log').open('x') as f:
   proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);Path(cmd[4]+'.running.json').write_text(json.dumps({'pid':proc.pid,'command':cmd}));rc=proc.wait()
  x={'command':cmd,'returncode':rc,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trace_sha256':sha(Path(cmd[2])),'binary_sha256':sha(out/'front')};Path(cmd[4]+'.receipt.json').write_text(json.dumps(x,indent=2));return x
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,tasks))
 assert len(rows)==38 and all(x['returncode']==0 for x in rows)
 (out/'terminal.json').write_text(json.dumps({'all_pass':True,'count':38,'receipts':rows,'scope':'same width8 plus finite one allocation per eight-lane group; frontend-only'},indent=2));print('GROUPED_PASS runs=38')
if __name__=='__main__':main()
