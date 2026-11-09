"""Re-use an unchanged synthesized mechanism for bounded extended protocol tests."""
import argparse, hashlib, json, os, shutil, signal, subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--hls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();h=a.hls.resolve();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
assert json.loads((h/'csynth.json').read_text())['passed']
shutil.copytree(h/'source',o/'source');shutil.copytree(h/'project',o/'project',ignore=shutil.ignore_patterns('sim','csim','*.wdb','core.*'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=o/'source';shutil.copy2(Path(__file__).resolve().parents[1]/'accel/lookahead/round5_1/tb51.cpp',s/'tb51.cpp');hashes={p.name:sha(p) for p in (o/'project/solution/syn/verilog').glob('*.v')}
flags=f'-I{s} -std=c++14 -pthread -ffp-contract=off -fno-fast-math'
app=o/'project/hls.app';app.write_text(app.read_text().replace(str(h/'source'),str(s)).replace(' -DLA51_RTL_SHORT',''))
(s/'run.tcl').write_text(f'''open_project project
set_top lookahead_services51
add_files {{{s}/services51.cpp}} -cflags {{{flags}}}
add_files -tb {{{s}/tb51.cpp}} -cflags {{{flags}}}
open_solution solution -flow_target vivado
set phase $::env(LA51_PHASE)
if {{$phase eq "csim"}} {{csim_design -ldflags "-pthread"}}
if {{$phase eq "cosim"}} {{cosim_design -rtl verilog -tool xsim -trace_level none -ldflags "-pthread" -enable_dataflow_profiling}}
exit
''')
(o/'binding.json').write_text(json.dumps({'source_binding':str(h/'binding.json'),'source_binding_sha256':sha(h/'binding.json'),'scope':'extended bounded protocol, same synthesized RTL','rtl_sha256':hashes,'sources':{p.name:sha(p) for p in s.iterdir()}},indent=2))
shutil.copy2(h/'csynth.json',o/'csynth.json')
env=os.environ.copy();env.pop('DEBUG',None);env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1'
for phase in ['csim','cosim']:
 env['LA51_PHASE']=phase;cmd=['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls','-f',str(s/'run.tcl')]
 with (o/(phase+'.log')).open('w') as f:
  proc=subprocess.Popen(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:rc=proc.wait(timeout=600)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
   rc=124
 text=(o/(phase+'.log')).read_text();marker={'csim':'CSim done with 0 errors','cosim':'C/RTL co-simulation finished: PASS'}[phase];ok=rc==0 and marker in text and 'ERROR:' not in text
 assert hashes=={p.name:sha(p) for p in (o/'project/solution/syn/verilog').glob('*.v')}
 (o/(phase+'.json')).write_text(json.dumps({'passed':ok,'returncode':rc,'command':cmd,'rtl_unchanged':True,'log_sha256':sha(o/(phase+'.log'))},indent=2));print(phase,ok,flush=True)
 if not ok:raise SystemExit(1)
