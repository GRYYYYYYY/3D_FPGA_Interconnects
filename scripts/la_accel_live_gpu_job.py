"""Build live CPU/CUDA adapters and measure complete builders on one GPU worker."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from prepare import sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--experiment', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    initial = sorted(os.sched_getaffinity(0))
    pools, seen = {}, set()
    for cpu in initial:
        d = Path(f'/sys/devices/system/cpu/cpu{cpu}')
        key = ((d/'topology/physical_package_id').read_text(), (d/'topology/core_id').read_text())
        if key in seen:
            continue
        seen.add(key)
        node = sorted(d.glob('node*'))[0].name
        pools.setdefault(node, []).append(cpu)
    chosen = sorted(pools.values(), key=lambda x: (-len(x), x))[0][:8]
    assert len(chosen) == 8
    os.sched_setaffinity(0, chosen)
    src = out/'source'
    shutil.copytree(ROOT/'accel/lookahead', src)
    (out/'worker.json').write_text(json.dumps(dict(hostname=socket.gethostname(), initial_affinity=initial,
        affinity=chosen, physical_cores=8, cgroup={n:Path('/sys/fs/cgroup'/Path(n)).read_text() for n in ['cpu.max','memory.max']},
        native_sha256=sha256(a.native), sources={str(p.relative_to(src)):sha256(p) for p in src.rglob('*') if p.is_file()}), indent=2))
    records = []

    def run(name, cmd, timeout=1200):
        start=time.time()
        env=os.environ.copy()
        env.pop('OMP_PROC_BIND',None);env.pop('OMP_PLACES',None)
        with (out/(name+'.log')).open('w') as log:
            proc=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        records.append(dict(name=name,command=cmd,returncode=proc.returncode,host_elapsed_s=time.time()-start))
        (out/'commands.json').write_text(json.dumps(records,indent=2))
        if proc.returncode:
            raise RuntimeError(name+' failed')

    try:
        for name,cmd in [('gpu',['nvidia-smi']),('nvcc',['nvcc','--version']),('cpu',['lscpu']),('compiler',['c++','--version'])]:run(name,cmd)
        inc='-I'+str(src/'include')
        cpu=out/'liblookahead_cpu_backend.so';gpu=out/'liblookahead_cuda_backend.so';replay=out/'backend_replay'
        run('build_cpu',['c++','-O2','-std=c++14','-fopenmp','-ffp-contract=off','-fno-fast-math','-shared','-fPIC',inc,str(src/'cpu_backend.cpp'),'-o',str(cpu)])
        run('build_gpu',['nvcc','-O2','-std=c++14','--fmad=false','-shared','-Xcompiler=-fPIC',inc,str(src/'cuda/cuda_backend.cu'),'-o',str(gpu)])
        run('build_replay',['c++','-O2','-std=c++14','-ffp-contract=off','-fno-fast-math',inc,str(src/'backend_replay.cpp'),'-ldl','-o',str(replay)])
        for case,contexts in [('tiny_native',4),('tseng_export',8),('bnn_export',40)]:
            for kind,lib in [('cpu',cpu),('cuda',gpu)]:
                run(f'replay_{kind}_{case}',[str(replay),str(a.experiment.resolve()/case/'workload.bin'),str(lib),str(contexts if kind=='cuda' else 8)])
        for kind,lib in [('cpu',cpu),('cuda',gpu)]:
            run('live_'+kind,[sys.executable,str(ROOT/'scripts/la_accel_live.py'),'--binary',str(a.native.resolve()),
                '--library',str(lib),'--output',str(out/('live_'+kind)),'--repeats','3','--workers','8','--contexts','8'])
        run('native_controls',[sys.executable,str(ROOT/'scripts/reproduce_native_lookahead.py'),
            '--output',str(out/'native_controls'),'--case','tseng_2d','--workers','8','--repeats','3','--include-stock','--execute'])
        (out/'finished.json').write_text(json.dumps(dict(status='passed',all_commands_successful=True)))
        return 0
    except Exception as exc:
        (out/'finished.json').write_text(json.dumps(dict(status='failed',reason=str(exc))))
        raise


if __name__=='__main__':
    raise SystemExit(main())
