#!/usr/bin/env python3
"""Bounded XSim2022.2 memory-agent protocol and rejection regression."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess
S=Path(__file__).resolve().parent;BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('fixtures',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();a.out=a.out.resolve();a.fixtures=a.fixtures.resolve();a.out.mkdir(parents=True,exist_ok=False);source=a.out/'source';source.mkdir();names=['cp_sparse_memory.sv','tb_sparse_memory.sv'];env=dict(os.environ,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1');commands=[];rows=[]
 for n in names:(source/n).write_bytes((S/n).read_bytes())
 def execute(cmd,log):
  commands.append(cmd)
  with (a.out/log).open('w')as f:return subprocess.run(cmd,cwd=a.out,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
 try:
  assert execute([str(BIN/'xvlog'),'--sv',*[str(source/n)for n in names]],'compile.log')==0
  assert execute([str(BIN/'xelab'),'tb_sparse_memory','-s','snapshot','--timescale','1ns/1ps','-mt','4'],'elaborate.log')==0
  modes=[('native_d3_w8','none',None),('native_d4_w8','none',None)]+[('native_d3_w8',name,marker)for name,marker in [('range','MEM_ADDRESS_OWNER_RANGE'),('owner','MEM_ADDRESS_OWNER_RANGE'),('uninitialized','MEM_READ_UNINITIALIZED'),('readonly','MEM_WRITE_READONLY'),('reuse','MEM_TAG_REUSE_OR_CREDIT')]]
  for case,mode,marker in modes:
   name=case+'_'+mode;rc=execute([str(BIN/'xsim'),'snapshot','-runall','-testplusarg','DIR='+str(a.fixtures/case),'-testplusarg','NEG='+mode,'-log',name+'.xsim.log'],name+'.log');text=(a.out/(name+'.log')).read_text();ok=(rc==0 and'TEST_PASS'in text and'Fatal:'not in text and'ERROR:'not in text)if marker is None else('Fatal:'in text and marker in text and'NEGATIVE_NOT_REJECTED'not in text);rows.append({'case':case,'mode':mode,'returncode':rc,'expected_fatal':marker,'pass':ok,'log_sha256':sha(a.out/(name+'.log'))});print(name,'PASS'if ok else'FAIL',flush=True);assert ok,text[-2000:]
 except BaseException as e:
  (a.out/'failure.json').write_text(json.dumps({'exception':str(e),'results':rows},indent=2)+'\n');raise
 finally:
  (a.out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  (a.out/'binding.json').write_text(json.dumps({'tool':'Vivado XSim2022.2','sources':{n:sha(source/n)for n in names},'fixture_manifest_sha256':sha(a.fixtures/'manifest.json')},indent=2)+'\n')
 (a.out/'terminal.json').write_text(json.dumps({'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':rows,'full_core_functional_verified':False,'scope':'TB external memory agent only; no DUT top'},indent=2)+'\n')
if __name__=='__main__':main()
