"""Production admin/output isolated XSim check, fresh evidence path required."""
from pathlib import Path
import argparse,json,subprocess,sys,hashlib,os,datetime
R=Path(__file__).resolve().parents[4];S=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('--mode',type=int,default=0);a=p.parse_args();out=(R/a.out).resolve();out.mkdir(parents=True,exist_ok=False);src=out/'source';src.mkdir()
files=[R/'accel/lookahead/fpga_cpu_primary/rtl/cp_admin.sv',S/'tb_admin.sv']+[R/'accel/lookahead/fpga_descriptor_front'/x for x in ['output/df_ack_collector.sv','output/df_output_service.sv','output/df_output_bank.sv','services/df_rr_router.sv']]
for f in files:(src/f.name).write_bytes(f.read_bytes())
(out/'binding.json').write_text(json.dumps({'sources':{str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in files},'mode':a.mode,'scope':'isolated admin/output, not full core','tool':'XSim2022.2'},indent=2)+'\n')
bin=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin');(out/'run.tcl').write_text('run all\nquit\n');cmds=[[str(bin/'xvlog'),'--sv',*[str(src/f.name)for f in files]],[str(bin/'xelab'),'tb_admin','-s','snapshot','--timescale','1ns/1ps'],[str(bin/'xsim'),'snapshot','-tclbatch','run.tcl','-testplusarg',f'MODE={a.mode}']];(out/'commands.json').write_text(json.dumps(cmds,indent=2)+'\n')
try:
 for i,cmd in enumerate(cmds):
  with (out/f'stage_{i}.log').open('w')as f:subprocess.run(cmd,cwd=out,env=dict(os.environ,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1'),stdout=f,stderr=subprocess.STDOUT,check=True)
 text=(out/'stage_2.log').read_text();assert 'TEST_PASS'in text and 'Fatal:'not in text and 'ERROR:'not in text,text[-2000:];status={'status':'PASS','result':[x for x in text.splitlines()if'TEST_PASS'in x]};print(text[-1500:])
except BaseException as e:status={'status':'FAIL','exception':str(e)};raise
finally:(out/'terminal.json').write_text(json.dumps(status,indent=2)+'\n')
