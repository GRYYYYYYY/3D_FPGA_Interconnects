#!/usr/bin/env python3
"""Bounded plain-RTL XSim flow; exact source freeze, full logs, explicit PASS."""
import argparse,subprocess,json,hashlib,os,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--data');p.add_argument('out');p.add_argument('top');p.add_argument('sources',nargs='+');a=p.parse_args()
out=Path(a.out).resolve();out.mkdir(exist_ok=False,parents=True);src=out/'source';src.mkdir()
dump=lambda name,x:(out/name).write_text(json.dumps(x,indent=2)+'\n')
files=[Path(x).resolve() for x in a.sources]
if a.data:
 for x in (p for p in Path(a.data).iterdir() if (p.suffix in ('.hex','.mem','.vec') or p.name=='cases.txt')):(out/x.name).write_bytes(x.read_bytes())
 dump('data_binding.json',{str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest() for x in (p for p in Path(a.data).iterdir() if (p.suffix in ('.hex','.mem','.vec') or p.name=='cases.txt'))})
assert len({x.name for x in files})==len(files),'duplicate basename'
for x in files:(src/x.name).write_bytes(x.read_bytes())
dump=lambda name,x:(out/name).write_text(json.dumps(x,indent=2)+'\n')
dump('binding.json',{'sources':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in files},'pid':os.getpid(),'top':a.top,'tool':'Vivado XSim 2022.2','mode':'behavioral'})
bin=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
env=dict(os.environ,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
(out/'run.tcl').write_text('run all\nquit\n')
commands=[[str(bin/'xvlog'),'--sv',*[str(src/x.name)for x in files]], [str(bin/'xelab'),a.top,'-s','snapshot','--timescale','1ns/1ps'],[str(bin/'xsim'),'snapshot','-tclbatch','run.tcl']]
dump('commands.json',commands)
try:
 for i,cmd in enumerate(commands):
  with (out/f'stage_{i}.log').open('w')as log:subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
 text=(out/'stage_2.log').read_text();assert 'TEST_PASS' in text and 'Fatal:'not in text and 'ERROR:'not in text,text[-2000:]
 dump('terminal.json',{'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':[x for x in text.splitlines()if 'TEST_PASS'in x]})
 print(text[-1500:])
except BaseException as e:
 dump('terminal.json',{'status':'FAIL','exception':str(e)});raise
