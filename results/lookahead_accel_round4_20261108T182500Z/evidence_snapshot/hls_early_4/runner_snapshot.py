"""Frozen-snapshot classic HLS 2022.2 flow for runtime-loaded on-chip kernels."""
import argparse,json,os,shutil,struct,subprocess,time
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
HLS=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--workload',type=Path,action='append');p.add_argument('--engines',type=int,choices=[1,4],default=1);p.add_argument('--early',type=int,choices=[0,1],default=0);p.add_argument('--period-ns',type=float,default=5);p.add_argument('--phases',nargs='+',choices=['csim','csynth','cosim','impl'],default=['csim','csynth','cosim']);p.add_argument('--resume',action='store_true');a=p.parse_args()
 o=a.output.resolve();binding=o/'binding.json';snapshot=o/'source_snapshot'
 if not a.resume:
  o.mkdir(parents=True,exist_ok=False);snapshot.mkdir();assert a.workload
  dimensions=dict(row=0,nodes=0,edges=0,costs=0,jobs=0,cells=0,output=0,stats=0);workloads=[]
  for path in a.workload:
   path=path.resolve()
   with path.open('rb') as f:_,n,e,j,k,c,g=struct.unpack('<7Q',f.read(56))
   dims=dict(row=n+1,nodes=n,edges=e,costs=k,jobs=j,cells=j*n,output=j*c,stats=j)
   for key,v in dims.items():dimensions[key]=max(dimensions[key],v)
   workloads.append(dict(path=str(path),sha256=sha256(path),dimensions=dict(n=n,e=e,j=j,k=k,c=c)))
  quantum=dict(row=8,nodes=4,edges=8,costs=8,jobs=8,cells=16,output=8,stats=4)
  dimensions={k:(v+quantum[k]-1)//quantum[k]*quantum[k] for k,v in dimensions.items()}
  files=[ROOT/'accel/lookahead/round4'/n for n in ['onchip4.cpp','onchip_api4.hpp','onchip_core4.hpp','onchip_types4.hpp','onchip_tb4.cpp','reference4.hpp']]+[ROOT/'accel/lookahead/include'/n for n in ['workload.hpp','io.hpp','strict_heap.hpp']]
  for f in files:shutil.copy2(f,snapshot/f.name)
  flags=f'-I{snapshot} -std=c++14 -ffp-contract=off -fno-fast-math -DLA4_ENGINES={a.engines} -DLA4_EARLY={a.early} '+' '.join(f'-DLA4_DEPTH_{k.upper()}={v}' for k,v in dimensions.items())
  argv=' '.join('{'+w['path']+'}' for w in workloads)
  tcl=f'''open_project project
set_top lookahead_onchip4
set flags {{{flags}}}
add_files {{{snapshot}/onchip4.cpp}} -cflags $flags
add_files -tb {{{snapshot}/onchip_tb4.cpp}} -cflags $flags
open_solution solution -flow_target vivado
set_part xcu280-fsvh2892-2L-e
create_clock -period {a.period_ns} -name default
set args [list {argv}]
set phase $::env(LA4_PHASE)
if {{$phase eq "csim"}} {{csim_design -argv $args}}
if {{$phase eq "csynth"}} {{csynth_design}}
if {{$phase eq "cosim"}} {{cosim_design -rtl verilog -tool xsim -trace_level none -argv $args}}
if {{$phase eq "impl"}} {{export_design -rtl verilog -format ip_catalog -flow impl}}
exit
'''
  (snapshot/'run_hls.tcl').write_text(tcl);shutil.copy2(__file__,o/'runner_snapshot.py')
  data=dict(top='lookahead_onchip4',engines=a.engines,early=bool(a.early),semantic_mode='MAP_EQUIVALENT_EARLY_STOP' if a.early else 'STRICT_FULL_FLOOD',clock_period_ns=a.period_ns,flags=flags,workloads=workloads,external_testbench_depths=dimensions,sources={f.name:sha256(f) for f in snapshot.iterdir() if f.is_file()},runtime_graph=True)
  binding.write_text(json.dumps(data,indent=2)+'\n')
 else:
  data=json.loads(binding.read_text())
  for name,digest in data['sources'].items():assert sha256(snapshot/name)==digest,'Frozen source changed'
  for w in data['workloads']:assert sha256(Path(w['path']))==w['sha256'],'Input changed'
 state={'active':None,'phases':{}}
 if (o/'supervisor.json').exists():state=json.loads((o/'supervisor.json').read_text())
 for phase in a.phases:
  previous={'csynth':'csim','cosim':'csynth','impl':'cosim'}.get(phase)
  if previous:assert json.loads((o/(previous+'.json')).read_text())['status']=='passed'
  log=o/(phase+'.log');assert not log.exists(),'Keep failed cohorts; retry in a fresh directory'
  state['active']=phase;(o/'supervisor.json').write_text(json.dumps(state,indent=2)+'\n')
  env=os.environ.copy();env.update(LA4_PHASE=phase,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
  command=[str(HLS),'-f',str(snapshot/'run_hls.tcl')];start=time.monotonic()
  with log.open('w') as f:run=subprocess.run(command,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT)
  text=log.read_text(errors='replace');marker={'csim':'CSim done with 0 errors','csynth':'Finished Command csynth_design','cosim':'C/RTL co-simulation finished: PASS','impl':'Finished Command export_design'}[phase]
  good=run.returncode==0 and marker in text and 'ERROR:' not in text
  result=dict(status='passed' if good else 'failed',returncode=run.returncode,host_elapsed_s=time.monotonic()-start,not_fpga_runtime=True,command=command,binding_sha256=sha256(binding),log_sha256=sha256(log))
  (o/(phase+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(phase,result['status'],flush=True);state['phases'][phase]=result['status']
  if not good:state['active']=None;state['status']='failed';(o/'supervisor.json').write_text(json.dumps(state,indent=2)+'\n');return 1
 state['active']=None;state['status']='completed';(o/'supervisor.json').write_text(json.dumps(state,indent=2)+'\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
