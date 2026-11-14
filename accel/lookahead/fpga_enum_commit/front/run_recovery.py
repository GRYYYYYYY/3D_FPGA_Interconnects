from pathlib import Path
import subprocess,os,json,datetime,hashlib
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'accel/lookahead/fpga_enum_commit/front';R=ROOT/'results/fpga_enum_commit_20261114/front_ooc_e'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 R.mkdir(exist_ok=False);preload=Path('/lib/x86_64-linux-gnu/libudev.so.1');assert preload.is_file();env=dict(os.environ);env['LD_PRELOAD']=str(preload)
 cmd=['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado','-mode','batch','-source',str(S/'recover_ooc.tcl'),'-notrace','-log',str(R/'vivado.log'),'-journal',str(R/'vivado.jou')];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 binding={'command':cmd,'cwd':str(R),'start_utc':start,'environment_override':{'LD_PRELOAD':str(preload)},'preload_sha256':sha(preload),'script_sha256':sha(S/'recover_ooc.tcl'),'input_synth_dcp_sha256':sha(ROOT/'results/fpga_enum_commit_20261114/front_ooc_d/synth.dcp'),'unchanged_design_source_sha256':sha(S/'frontend_group.sv'),'reason':'D SIGABRT libudev/FlexNet WebTalk host enumeration after router completed; per-process preload, no installed/global modification','primary_sources':['https://adaptivesupport.amd.com/s/article/000034450','https://community.revenera.com/s/question/0D5PL00000NwuKu0AJ/issues-when-running-xilinx-tools-or-other-vendor-tools-in-docker-environment']};(R/'binding.json').write_text(json.dumps(binding,indent=2))
 with (R/'console.log').open('x') as f:
  p=subprocess.Popen(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT);(R/'running.json').write_text(json.dumps({'pid':p.pid,**binding},indent=2));rc=p.wait()
 value={**binding,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':rc,'terminal_status':'COMPLETED' if rc==0 else 'FAILED_TOOL','has_completion_marker':'FRONT_OOC_E_COMPLETE' in (R/'vivado.log').read_text()};(R/'terminal.json').write_text(json.dumps(value,indent=2));assert rc==0 and value['has_completion_marker'];print('OOC_RECOVERY_COMPLETED')
if __name__=='__main__':main()
