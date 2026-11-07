"""One frozen H100 diagnostic job: compile/oracles, native pair/batch, true replay."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare import sha256,write_json
from scaling_common import run_process


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--suite',type=Path)
    p.add_argument('--cases',default='elliptic,gemm');p.add_argument('--variants',default='original_vpr,pair,batch')
    p.add_argument('--pair-stride',type=int,default=1);p.add_argument('--capture-limit',type=int,default=32);p.add_argument('--capture-stride',type=int,default=5)
    args=p.parse_args();bundle=args.bundle.resolve();out=args.output.resolve();out.mkdir(exist_ok=False)
    r={'status':'running','scope':'diagnostics only; no end-to-end speedup claim','bundle':str(bundle),'steps':[]}
    write_json(out/'summary.json',r)
    def run(name,cmd,timeout=600,env=None):
        result=run_process(cmd,out,env or os.environ.copy(),timeout,name+'.log');r['steps'].append({'name':name,**result});write_json(out/'summary.json',r)
        if result['returncode']:raise RuntimeError(name+' failed; see '+name+'.log')
    try:
        r['device']=subprocess.check_output(['nvidia-smi'],text=True)
        r['storage']={str(path):subprocess.check_output(['findmnt','-T',str(path)],text=True) for path in [bundle,out,bundle/'inputs']}
        run('library_oracle',[sys.executable,str(bundle/'scripts/run_native_replay.py'),'--source',str(bundle/'native'),'--resident','--cooperative-blocks','64','--capture',str(bundle/'legacy_oracle'),'--output',str(out/'library')])
        library=out/'library/libh3d_native_gpu.so'
        run('compile_takeover',['g++','-std=c++17','-O3','-ffp-contract=off',str(bundle/'native/takeover_replay.cpp'),'-ldl','-o',str(out/'takeover_replay')])
        env=os.environ.copy();env.update(H3D_GPU_TIMING='1',H3D_GPU_COOPERATIVE_BLOCKS='64')
        run('true_takeover_smoke',[str(out/'takeover_replay'),str(library),str(bundle/'takeover_oracle'),'3'],env=env)
        # Every case runs the untouched baseline, CPU-retaining pair and actual
        # GPU-committing batch under identical inputs and storage conditions.
        run('routing',[sys.executable,str(bundle/'scripts/run_native_hybrid.py'),'--binary',str(bundle/'vpr'),'--library',str(library),
                       '--suite',str(args.suite or bundle/'suite.json'),'--runtime',str(bundle/'runtime/runtime.json'),'--vpr-lock',str(bundle/'vpr.lock.json'),
                       '--output',str(out/'routing'),'--cases',args.cases,'--variants',args.variants,
                       '--budget','2048','--cooperative-blocks','64','--diagnostics','--capture-limit',str(args.capture_limit),'--capture-stride',str(args.capture_stride),'--pair-stride',str(args.pair_stride),'--native-repeats','3','--timeout','900'],timeout=6000)
        r['captures']=[]
        for directory in sorted((out/'routing').glob('*_pair/takeovers')):
            bindings={f.name:sha256(f) for f in sorted(directory.iterdir()) if f.is_file()}
            write_json(directory/'bindings.json',{'format':'H3DTAK2','scope':'actual native takeover; CPU continuation restored in-process','files':bindings})
            name=directory.parent.name+'_replay';run(name,[str(out/'takeover_replay'),str(library),str(directory),'3'],env=env)
            rows=list(csv.DictReader((out/(name+'.log')).open()))
            # stderr is mixed with stdout only on failure; fail closed above.
            if not rows or any(v['valid']!='1' for v in rows):raise RuntimeError('invalid/incomplete takeover replay')
            expected=4*len(list(directory.glob('takeover_*.native.csv')))
            if len(rows)!=expected:raise RuntimeError('missing takeover repeats')
            r['captures'].append({'directory':str(directory),'validated_gpu_paths':len(rows),'bindings':bindings})
            if any(sha256(directory/k)!=v for k,v in bindings.items()):raise RuntimeError('capture changed during replay')
        frozen=json.loads((bundle/'bindings.json').read_text())
        if any(sha256(bundle/k)!=v for k,v in frozen['files'].items()):raise RuntimeError('frozen source/input changed')
        r['status']='completed';r['routing_summary']=str(out/'routing/summary.json')
    except Exception as e:r['status']='failed';r['error']=repr(e);raise
    finally:write_json(out/'summary.json',r)


if __name__=='__main__':main()
