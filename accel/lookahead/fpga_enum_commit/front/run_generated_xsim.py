"""Replay Vivado-generated XSim scripts while all task MCP sessions are implementing."""
from pathlib import Path
import shutil,subprocess,os,json,datetime,hashlib
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114';S=ROOT/'accel/lookahead/fpga_enum_commit/front'
def main():
 old=R/'front_rtl_c/project/front_group.sim/sim_1/behav/xsim';out=R/'front_rtl_d/project/front_group.sim/sim_1/behav/xsim';out.mkdir(parents=True,exist_ok=False)
 for name in ['compile.sh','elaborate.sh','simulate.sh','frontend_group_tb_vlog.prj','frontend_group_tb.tcl','glbl.v']:shutil.copy2(old/name,out/name)
 for p in (R/'front_rtl_d').glob('*.hex'):shutil.copy2(p,out/p.name)
 env=dict(os.environ);env['PATH']='/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin:'+env.get('PATH','');rows=[]
 for name in ['compile.sh','elaborate.sh','simulate.sh']:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat();cmd=['bash',name]
  with (out/(name+'.console.log')).open('x') as f:rc=subprocess.run(cmd,cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
  row={'command':cmd,'cwd':str(out),'generated_by':'Vivado2022.2 run_rtl.tcl,front_rtl_c project; no inferred simulator switches','returncode':rc,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()};rows.append(row)
  (R/'front_rtl_d/run_receipts.json').write_text(json.dumps(rows,indent=2));assert rc==0,name
 raw=(out/'simulate.log').read_text();assert 'TEST_PASS frontend_group' in raw and 'Fatal:' not in raw;print('GENERATED_XSIM_PASS D')
if __name__=='__main__':main()
