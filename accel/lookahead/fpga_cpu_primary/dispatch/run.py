"""Reproduce standalone dispatcher protocol tests in a fresh output directory."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,datetime
S=Path(__file__).resolve().parent
BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('out',type=Path);args=a.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
 env=dict(os.environ,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
 for top in ['tb_pop_dispatch','tb_dispatch_reject']:
  d=out/top;d.mkdir();files=['cp_pop_dispatch.sv',top+'.sv']
  for name in files:(d/name).write_bytes((S/name).read_bytes())
  (d/'run.tcl').write_text('run all\nquit\n')
  commands=[[str(BIN/'xvlog'),'--sv',*files],[str(BIN/'xelab'),top,'-s','snapshot','-mt','2','--timescale','1ns/1ps'],[str(BIN/'xsim'),'snapshot','-tclbatch','run.tcl']]
  binding={'tool':'Vivado XSim2022.2','sources_sha256':{name:sha(d/name)for name in files},'commands':commands,'environment':{'LD_PRELOAD':env['LD_PRELOAD']},'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  (d/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
  try:
   for i,cmd in enumerate(commands):
    with (d/f'stage_{i}.log').open('w')as f:subprocess.run(cmd,cwd=d,stdout=f,stderr=subprocess.STDOUT,env=env,check=True)
   text=(d/'stage_2.log').read_text();assert 'TEST_PASS'in text and 'Fatal:'not in text and 'ERROR:'not in text
   result={'status':'PASS','marker':[x for x in text.splitlines()if 'TEST_PASS'in x]}
  except BaseException as e:
   (d/'terminal.json').write_text(json.dumps({'status':'FAIL','exception':str(e)},indent=2)+'\n');raise
  (d/'terminal.json').write_text(json.dumps(result,indent=2)+'\n');print(top,result)
if __name__=='__main__':main()
