from pathlib import Path
import subprocess,json,hashlib,shutil,datetime
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'accel/lookahead/fpga_enum_commit/front';R=ROOT/'results/fpga_enum_commit_20261114';O=R/'front_bindings_a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);closure=set()
 for name in ['frontend_model.cpp','frontend_independent.cpp']:
  cmd=['g++','-std=c++17','-MM',*['-I'+str(ROOT/'accel/lookahead'/x) for x in ['include','round6_1','fpga_sparse_stream_r2']],str(S/name)]
  deps=subprocess.check_output(cmd,text=True).replace('\\\n',' ').split(':',1)[1].split();closure.update(Path(x).resolve() for x in deps)
 closure.update(S.glob('*.sv'));closure.add(ROOT/'accel/lookahead/fpga_sparse_stream/rtl/fp32_positive.sv')
 records={}
 for p in sorted(closure):
  rel=p.relative_to(ROOT);dest=O/'source_tree'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);records[str(rel)]=sha(p)
 (O/'source_closure.json').write_text(json.dumps({'base':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'sha256':records,'compiler':subprocess.check_output(['g++','--version'],text=True),'python':subprocess.check_output(['python3','--version'],text=True),'source_snapshots_for_earlier_versions':'each run/source/ retains exact earlier model; closure includes unchanged inherited graph/reference headers'},indent=2))
 rebuilds=[]
 for run,source in [('front_grouped_b','frontend_model.cpp'),('front_independent_a','frontend_independent.cpp')]:
  cmd=json.loads((R/run/'binding.json').read_text())['command'];assert Path(cmd[-3]).name==source;cmd[-1]=str(O/(run+'_rebuild'));start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with (O/(run+'_build.log')).open('x') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
  assert rc==0 and sha(Path(cmd[-1]))==sha(R/run/'front');rebuilds.append({'run':run,'command':cmd,'returncode':rc,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'binary_sha256':sha(Path(cmd[-1])),'identical':True})
 (O/'rebuild_receipts.json').write_text(json.dumps(rebuilds,indent=2));print('FRONT_BINDING_PASS sourceclosure',len(records),'identical_rebuilds=2')
if __name__=='__main__':main()
