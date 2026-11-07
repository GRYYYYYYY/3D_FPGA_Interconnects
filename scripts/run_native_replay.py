"""GPU snapshot replay diagnostics, not an end-to-end routing benchmark."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import time

from prepare import sha256, write_json
from scaling_common import run_process


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--capture',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--resident',action='store_true')
    p.add_argument('--cooperative-blocks',type=int,default=0)
    args=p.parse_args();source=args.source.resolve();output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    record={'status':'running','scope':'diagnostic native-query replay; no VPR end-to-end acceleration claim',
            'source':{str(f):sha256(f) for f in sorted(source.glob('*')) if f.is_file()},'cases':[]}
    write_json(output/'summary.json',record)
    try:
        if args.resident:record['scope']='Resident native-cost engine and sparse state replay; batch copies are isolation oracles, not independent-net throughput measurements'
        for name,command in [('device',['nvidia-smi']),('compiler',['nvcc','--version'])]:
            record[name]=subprocess.check_output(command,text=True)
        cmd=['nvcc','-std=c++17','-O3','--fmad=false','--ftz=false','-arch=sm_90']
        if args.resident:
            cmd+=['--shared','-Xcompiler','-fPIC',str(source/'gpu_engine.cu'),'-o',str(output/'libh3d_native_gpu.so')]
        else:cmd+=[str(source/'replay_cuda.cu'),'-o',str(output/'replay_cuda')]
        record['compile']=run_process(cmd,output,os.environ.copy(),600,'compile.log')
        if record['compile']['returncode']:raise RuntimeError('CUDA compile failed')
        if args.resident:
            host=['g++','-std=c++17','-O3','-ffp-contract=off',str(source/'resident_replay.cpp'),'-ldl','-o',str(output/'resident_replay')]
            record['host_compile']=run_process(host,output,os.environ.copy(),120,'host_compile.log')
            if record['host_compile']['returncode']:raise RuntimeError('resident host compile failed')
        for capture in args.capture:
            capture=capture.resolve();queries=sorted(capture.glob('query_*.bin'),key=lambda f:int(f.stem.split('_')[1]))
            if not queries:raise RuntimeError(f'No native query snapshots in {capture}')
            graph=capture/'graph.bin'
            case={'capture':str(capture),'graph_sha256':sha256(graph),
                  'queries':{f.name:sha256(f) for f in queries},'batches':[]}
            record['cases'].append(case)
            if args.resident:
                case['state_and_model_sha256']={f.name:sha256(f) for f in [capture/'model.bin',*sorted(capture.glob('state_*.bin'))]}
            for batch in ([1,4] if args.resident else [1,8]):
                prefix=f'case_{len(record["cases"])-1}_batch_{batch}'
                command=([str(output/'resident_replay'),str(output/'libh3d_native_gpu.so'),str(capture),str(batch)] if args.resident
                         else [str(output/'replay_cuda'),str(batch),str(graph),*map(str,queries)])
                tick=time.perf_counter()
                with (output/(prefix+'.csv')).open('w') as out,(output/(prefix+'.log')).open('w') as err:
                    env=os.environ.copy()
                    if args.cooperative_blocks:
                        env.update(H3D_GPU_COOPERATIVE_BLOCKS=str(args.cooperative_blocks),H3D_GPU_COOPERATIVE_MIN_SEEDS='0',
                                   H3D_GPU_DEVICE_REPORT=str(output/(prefix+'.device.json')))
                    proc=subprocess.run(command,stdout=out,stderr=err,timeout=600,env=env)
                row={'batch':batch,'returncode':proc.returncode,'wall_seconds':time.perf_counter()-tick,'csv':prefix+'.csv','log':prefix+'.log','command':command}
                if args.cooperative_blocks:row['device']=json.loads((output/(prefix+'.device.json')).read_text())
                case['batches'].append(row);write_json(output/'summary.json',record)
                if proc.returncode:raise RuntimeError(f'{prefix} failed')
                rows=list(csv.DictReader((output/(prefix+'.csv')).open()))
                expected=3*len(queries)*(batch if args.resident else 1)
                if len(rows)!=expected or any(r['valid']!='1' for r in rows):raise RuntimeError('Incomplete replay validation')
                row['validated_queries']=len(rows)
                print(prefix,'validated',len(rows),flush=True)
            if sha256(graph)!=case['graph_sha256'] or any(sha256(capture/k)!=v for k,v in case['queries'].items()):raise RuntimeError('capture changed')
            if args.resident and any(sha256(capture/k)!=v for k,v in case['state_and_model_sha256'].items()):raise RuntimeError('state/model changed')
        if any(sha256(Path(k))!=v for k,v in record['source'].items()):raise RuntimeError('source changed')
        record['built_artifacts']={f.name:sha256(f) for f in output.iterdir() if f.name in ['libh3d_native_gpu.so','resident_replay','replay_cuda']}
        record['status']='completed'
    except Exception as exc:
        record['status']='failed';record['error']=repr(exc)
        raise
    finally:write_json(output/'summary.json',record)


if __name__=='__main__':main()
