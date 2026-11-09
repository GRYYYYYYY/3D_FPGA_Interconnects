"""Frozen classic HLS 2022.2 standalone POP comparison; never invokes OOC."""
import argparse, hashlib, json, os, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HLS = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--baseline',action='store_true');a=p.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    snap=out/'source_snapshot';snap.mkdir()
    files=[ROOT/'accel/lookahead/round5_1'/n for n in ['heap51.hpp','heap_hls51.cpp','heap_hls_tb51.cpp']]
    files += [ROOT/'accel/lookahead/round4/onchip_types4.hpp']
    files += [ROOT/'accel/lookahead/include'/n for n in ['workload.hpp','strict_heap.hpp']]
    for f in files:shutil.copy2(f,snap/f.name)
    flags=f'-I{snap} -std=c++14 -ffp-contract=off -fno-fast-math'+(' -DHEAP51_BASELINE' if a.baseline else '')
    tcl=f'''open_project project
set_top heap_pop51
set flags {{{flags}}}
add_files {{{snap}/heap_hls51.cpp}} -cflags $flags
add_files -tb {{{snap}/heap_hls_tb51.cpp}} -cflags $flags
open_solution solution -flow_target vivado
set_part xcu280-fsvh2892-2L-e
create_clock -period 5 -name default
set phase $::env(HEAP51_PHASE)
if {{$phase eq "csim"}} {{csim_design}}
if {{$phase eq "csynth"}} {{csynth_design}}
if {{$phase eq "cosim"}} {{cosim_design -rtl verilog -tool xsim -trace_level none}}
exit
'''
    (snap/'run_hls.tcl').write_text(tcl);shutil.copy2(__file__,out/'runner_snapshot.py')
    binding=dict(top='heap_pop51',capacity=16385,baseline=a.baseline,target_period_ns=5,
                 tool='Vitis HLS 2022.2 classic Tcl',sources={f.name:digest(f) for f in snap.iterdir()},
                 ports='two independent 96-bit T2P memories, read latency 1',
                 board_measured=False,implemented_frequency=None)
    (out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    env=os.environ.copy();env.pop('DEBUG',None);env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1'
    state=dict(status='running',active=None,phases={})
    for phase,marker in [('csim','CSim done with 0 errors'),('csynth','Finished Command csynth_design'),('cosim','C/RTL co-simulation finished: PASS')]:
        if phase=='cosim':assert (out/'project/solution/syn').is_dir()
        state['active']=phase;(out/'supervisor.json').write_text(json.dumps(state,indent=2))
        env['HEAP51_PHASE']=phase;start=time.monotonic();log=out/(phase+'.log')
        cmd=[str(HLS),'-f',str(snap/'run_hls.tcl')]
        with log.open('w') as f:r=subprocess.run(cmd,cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
        content=log.read_text(errors='replace');ok=r.returncode==0 and marker in content and 'ERROR:' not in content
        result=dict(status='passed' if ok else 'failed',returncode=r.returncode,command=cmd,
                    host_elapsed_seconds=time.monotonic()-start,not_fpga_runtime=True,log_sha256=digest(log))
        (out/(phase+'.json')).write_text(json.dumps(result,indent=2)+'\n');state['phases'][phase]=result['status']
        print(phase,result['status'],flush=True)
        if not ok:state.update(status='failed',active=None);break
    else:state.update(status='completed',active=None)
    (out/'supervisor.json').write_text(json.dumps(state,indent=2)+'\n')
    return 0 if state['status']=='completed' else 1
if __name__=='__main__':raise SystemExit(main())
