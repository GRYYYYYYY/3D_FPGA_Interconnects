"""Bounded 2022.2 independent-service mechanism probe; never a batch benchmark."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess, time, signal
R=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--phases',nargs='+',default=['csim','csynth','cosim']);a=p.parse_args()
o=a.output.resolve();o.mkdir(parents=True,exist_ok=False);s=o/'source';s.mkdir()
files=[R/'accel/lookahead/round5_1'/f for f in ['api51.hpp','services51.cpp','services51.hpp','tb51.cpp']]+[R/'accel/lookahead/round4/onchip_types4.hpp',R/'accel/lookahead/include/workload.hpp',R/'accel/lookahead/include/strict_heap.hpp']
for f in files:shutil.copy2(f,s/f.name)
flags=f'-I{s} -std=c++14 -pthread -ffp-contract=off -fno-fast-math -DLA51_RTL_SHORT'
(s/'run.tcl').write_text(f'''open_project project
set_top lookahead_services51
add_files {{{s}/services51.cpp}} -cflags {{{flags}}}
add_files -tb {{{s}/tb51.cpp}} -cflags {{{flags}}}
open_solution solution -flow_target vivado
set_part xcu280-fsvh2892-2L-e
create_clock -period 5 -name default
set phase $::env(LA51_PHASE)
if {{$phase eq "csim"}} {{csim_design -ldflags "-pthread"}}
if {{$phase eq "csynth"}} {{csynth_design}}
if {{$phase eq "cosim"}} {{cosim_design -rtl verilog -tool xsim -trace_level all -ldflags "-pthread" -enable_dataflow_profiling}}
exit
''')
hash=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
(o/'binding.json').write_text(json.dumps({'sources':{f.name:hash(f) for f in s.iterdir()},'scope':'32-node capacity mechanism only, two calls','clock_ns_target_only':5,'board_measured':False},indent=2))
env=os.environ.copy();env.pop('DEBUG',None);env.update(LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
for phase in a.phases:
 env['LA51_PHASE']=phase;cmd=['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls','-f',str(s/'run.tcl')];start=time.monotonic()
 with (o/(phase+'.log')).open('w') as f:
  proc=subprocess.Popen(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:rc=proc.wait(timeout=900)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
   rc=124
 txt=(o/(phase+'.log')).read_text(errors='replace');marker={'csim':'CSim done with 0 errors','csynth':'Finished Command csynth_design','cosim':'C/RTL co-simulation finished: PASS'}[phase];ok=rc==0 and marker in txt and 'ERROR:' not in txt
 (o/(phase+'.json')).write_text(json.dumps({'command':cmd,'returncode':rc,'passed':ok,'host_elapsed_s':time.monotonic()-start,'log_sha256':hash(o/(phase+'.log'))},indent=2));print(phase,ok,flush=True)
 if not ok:raise SystemExit(1)
