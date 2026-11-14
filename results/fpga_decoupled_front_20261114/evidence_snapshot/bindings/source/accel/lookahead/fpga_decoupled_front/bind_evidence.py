"""Freeze final source/tool/input/output bindings without rerunning old experiments."""
from run_profile import *
import shutil

def main():
 out=R/'bindings';out.mkdir(exist_ok=True)
 source=out/'source';source.mkdir(exist_ok=False)
 closure=json.loads((out/'source_closure.json').read_text())
 files=set(closure['sha256'])|{str(p.relative_to(ROOT)) for p in S.iterdir() if p.is_file()}
 files|={'accel/lookahead/fpga_sparse_stream_r2/'+x for x in ['inf_finite_service.hpp','inf_finite_reference.cpp','rtl/fp32_positive.sv'] if (ROOT/'accel/lookahead/fpga_sparse_stream_r2'/x).exists()}
 for rel in sorted(files):
  p=source/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,p)
 # Rebuild exact current frontend sources to establish source->binary identity.
 cmd=['g++','-O3','-std=c++17','-ffp-contract=off',*['-I'+str(ROOT/'accel/lookahead'/p) for p in ['include','round6_1','fpga_sparse_stream_r2']],str(S/'frontend_model.cpp'),'-o',str(out/'rebuild_front')]
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (out/'rebuild_front.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert sha(out/'rebuild_front')==sha(R/'front_b/front')
 original_cmd=[*cmd[:-1],str(R/'front_b/front')]
 receipt={'command':cmd,'original_build_command':original_cmd,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':0,'binary_sha256':sha(R/'front_b/front'),'rebuild_identical':True,'sources':{str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}}
 (out/'final_source_binding.json').write_text(json.dumps(receipt,indent=2)+'\n')
 check=subprocess.run(['python3',str(S/'verify_evidence.py')],capture_output=True,text=True)
 (out/'verification.log').write_text(check.stdout+check.stderr);assert check.returncode==0
 sim=R/'enum_rtl_a/project/enum_witness.sim/sim_1/behav/xsim';enum=out/'enum';enum.mkdir()
 for name in ['enum_interval_tb_vlog.prj','enum_interval_tb.tcl','glbl.v']:shutil.copy2(sim/name,enum/name)
 log=R/'enum_rtl_a/.vivado-ai/vivado_43013240_efb8b4c3.log';shutil.copy2(log,enum/'vivado.log')
 raw=log.read_text();assert 'VSCEND:0' in raw and 'TEST_PASS two_waves=2 lines=128' in raw
 (enum/'receipt.json').write_text(json.dumps({'tool':'Vivado 2022.2 build 3671981 / XSim','part':'xcu280-fsvh2892-2L-e','session':'vivado-20261114-075653-d2ee6465','command':'source '+str(S/'run_enum.tcl'),'session_start_UTC':'2026-11-14T07:56:55+00:00','end_evidence':'MCP_CMD_END:wxb18l3r2pk2:0 in vivado.log; exact wall completion timestamp not captured','log_last_modified_utc':datetime.datetime.fromtimestamp(log.stat().st_mtime,datetime.timezone.utc).isoformat(),'returncode':0,'test_pass':True,'simulation_finish_ns':9095,'scope':'retained enumeration witness, not new frontend qualification','input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [S/'run_enum.tcl',S/'enum_interval_tb.sv',ROOT/'accel/lookahead/fpga_sparse_stream_r2/rtl/inf_flat_bank.sv']},'log_sha256':sha(log)},indent=2))
 # Validate all reused software/source hashes, without running software benchmarks.
 reused=json.loads((out/'reused_evidence.json').read_text())
 for ref in reused['references']:
  p=ref.get('path') or ref['manifest'].rsplit('/',1)[0]+'/'+ref['archive']
  assert hashlib.sha256(git_bytes(p)).hexdigest()==ref['sha256']
 (out/'qualification.json').write_text(json.dumps({'status':'NO_GO_CONFIGURATION','front_b_cases':51,'front_stress_b_cases':6,'complete_functional_profiles':4,'all_pass':True,'final_source_binary_identical':True,'reused_hashes_verified':True,'new_GPU_runs':0,'new_old_model_runs':0,'new_frontend_RTL':False,'new_frontend_OOC':False,'complete_new_finite_model':False,'complete_kernel_clock_qualified':False,'fpga_seconds':None,'board_measured':False},indent=2))
 print('BINDING_PASS: identical frontend rebuild, full new source closure, reused evidence checks, independent verifier')
if __name__=='__main__':main()
