"""Prepare one unique local result directory; do not overwrite prior evidence."""
from pathlib import Path
import argparse,subprocess,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[4];SRC=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 command=['g++','-O2','-std=c++17','-I'+str(ROOT/'accel/lookahead/fpga_sparse_stream_r2'),str(SRC/'gen_vectors.cpp'),'-o',str(out/'gen_vectors')]
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (out/'vector_build.log').open('x') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
 run=[str(out/'gen_vectors'),str(out)]
 with (out/'vector_generate.log').open('x') as log:subprocess.run(run,stdout=log,stderr=subprocess.STDOUT,check=True)
 (out/'canonical_tb.sv').write_text((SRC/'canonical_tb.sv').read_text().replace('@VEC_DIR@',str(out)))
 tcl=f'''set root {{{ROOT}}}
set src {{{SRC}}}
set out {{{out}}}
if {{[file exists $out/project]}} {{error "Existing result project"}}
create_project canonical_k8 $out/project -part xcu280-fsvh2892-2L-e
add_files [list $root/accel/lookahead/fpga_sparse_stream_r2/rtl/pending17_service.sv $src/ec_pending_k8.sv $src/ec_tagged_port.sv $src/ec_canonical_owner.sv]
add_files -fileset sim_1 $out/canonical_tb.sv
set_property top canonical_tb [get_filesets sim_1]
set_property xsim.simulate.runtime 3ms [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim
'''
 (out/'run_sim.tcl').write_text(tcl)
 (out/'vector_receipt.json').write_text(json.dumps({'build_command':command,'run_command':run,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':0,'binary_sha256':sha(out/'gen_vectors'),'sources':{str(p.relative_to(ROOT)):sha(p) for p in [SRC/'gen_vectors.cpp',ROOT/'accel/lookahead/fpga_sparse_stream_r2/pending17.hpp']},'outputs':{p.name:sha(p) for p in out.glob('*.mem')},'g++':subprocess.check_output(['g++','--version'],text=True)},indent=2)+'\n')
 print('Prepared',out/'run_sim.tcl')
if __name__=='__main__':main()
