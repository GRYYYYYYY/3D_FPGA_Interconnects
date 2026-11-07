#!/usr/bin/env python3
"""Run the installed HLS 2022.2 with this host's libudev compatibility setting."""
import argparse
import os
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
DEFAULT='/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=('csim','csynth','cosim'))
    p.add_argument('--binary',type=Path,default=Path(os.environ.get('H3D_HLS_BIN',DEFAULT)))
    p.add_argument('--vectors',type=Path)
    p.add_argument('--log',type=Path)
    a=p.parse_args()
    env=os.environ.copy();env['H3D_HLS_PHASE']=a.phase
    if a.vectors:env['H3D_HLS_VECTORS']=str(a.vectors.resolve())
    else:env.pop('H3D_HLS_VECTORS',None)
    # The neighboring, previously validated 2022.2 flow uses this preload.
    # Apply to the child only; do not change installation or system libraries.
    lib=Path('/lib/x86_64-linux-gnu/libudev.so.1')
    if lib.exists():env['LD_PRELOAD']=str(lib)+(':'+env['LD_PRELOAD'] if env.get('LD_PRELOAD') else '')
    log=a.log or ROOT/'build'/f'hls_{a.phase}.log'
    log.parent.mkdir(parents=True,exist_ok=True)
    print(f'HLS {a.phase}; log={log}',flush=True)
    with log.open('w') as out:
        run=subprocess.run([str(a.binary.resolve()),'-f',str(ROOT/'hardware/run_hls.tcl')],
                           cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
    text=log.read_text(errors='replace')
    marker={'csim':'CSim done with 0 errors','csynth':'Finished Command csynth_design',
            'cosim':'C/RTL co-simulation finished: PASS'}[a.phase]
    if run.returncode or marker not in text or 'ERROR:' in text:
        print(text[-5000:]);return 1
    print(f'{a.phase}: PASS');return 0


if __name__=='__main__':raise SystemExit(main())
