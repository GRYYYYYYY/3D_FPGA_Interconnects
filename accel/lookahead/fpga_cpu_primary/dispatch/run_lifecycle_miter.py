"""Additional full-state cycle miter, preserving prior completed test receipts."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess
S=Path(__file__).resolve().parent
BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 old=S/'cp_pop_dispatch.sv';assert sha(old)=='b1f566c826593388b06d73c3733446a3918bc449db98fb5f5264b2287e0bade4'
 names=['cp_pop_dispatch.sv','cp_pop_dispatch_restructured.sv','tb_dispatch_lifecycle_miter.sv','run_lifecycle_miter.py']
 for n in names:(out/n).write_bytes((S/n).read_bytes())
 (out/'cp_pop_dispatch_reference.sv').write_text(old.read_text().replace('module cp_pop_dispatch(','module cp_pop_dispatch_reference(',1))
 (out/'run.tcl').write_text('run all\nquit\n')
 env=dict(os.environ,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
 commands=[[str(BIN/'xvlog'),'--sv','cp_pop_dispatch_reference.sv','cp_pop_dispatch_restructured.sv','tb_dispatch_lifecycle_miter.sv'],[str(BIN/'xelab'),'tb_dispatch_lifecycle_miter','-s','snapshot','-mt','2','--timescale','1ns/1ps'],[str(BIN/'xsim'),'snapshot','-tclbatch','run.tcl']]
 binding={'source_sha256':{n:sha(out/n) for n in names+['cp_pop_dispatch_reference.sv']},'commands':commands,'tool':'XSim2022.2','scope':'reset-reachable protocol, defined valid payloads, bounded behavioral comparison; no arbitrary-X or formal-equivalence claim','start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 (out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
 try:
  for i,cmd in enumerate(commands):
   with (out/f'stage_{i}.log').open('w') as f:subprocess.run(cmd,cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
  logs=[(out/f'stage_{i}.log').read_text() for i in range(3)]
  assert 'TEST_PASS' in logs[2] and all('ERROR:' not in x and 'Fatal:' not in x for x in logs)
  for n in names:assert sha(S/n)==binding['source_sha256'][n]
  result={'status':'PASS','markers':[x for x in logs[2].splitlines() if 'TEST_PASS' in x or 'MITER_EDGES' in x],'log_sha256':{f'stage_{i}.log':sha(out/f'stage_{i}.log') for i in range(3)}}
 except BaseException as e:
  (out/'terminal.json').write_text(json.dumps({'status':'FAIL','exception':str(e)},indent=2)+'\n');raise
 (out/'terminal.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
