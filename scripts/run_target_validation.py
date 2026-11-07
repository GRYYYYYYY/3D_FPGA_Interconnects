#!/usr/bin/env python3
"""Same-worker baseline/legacy/target routing with native STA feedback."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import time

from audit import audit
from prepare import sha256, write_json
from scaling_common import metrics, run_process, route_fingerprint, verified, vpr_command, vpr_environment
from target_pipeline import pipeline
from vpr_validate import export


def baseline(binary,item,vpr,env,output,variant,timeout):
    output.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    case=json.loads(Path(item['vpr_case']).read_text());projection=Path(item['projection'])
    for role,file in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],output/file)
    if variant=='vpr':
        row=run_process(vpr_command(vpr,case,output,200),output,env,timeout)
        native=metrics((output/'process.log').read_text(errors='replace'));row.update(native)
        row['success']=row['returncode']==0 and native['full_check'] and native['routing_success']
    else:
        result=output/'result.json'
        row=run_process([binary,projection/'graph.rrg',projection/'nets.txt',result,'--backend','cuda','--threads','1','--batch','8','--iterations','200'],output,os.environ.copy(),timeout)
        row['success']=False
        if result.exists() and row['returncode'] in (0,2):
            raw=json.loads(result.read_text());row.update(routing_seconds=raw['routing_seconds'],gpu_metrics=raw['gpu_metrics'],search_seconds=raw['gpu_metrics']['search_seconds'],
                result_sha256=sha256(result),route_fingerprint=route_fingerprint(raw),iterations=len(raw['iterations']),last_iteration=raw['iterations'][-1])
            t=time.perf_counter();row['audit']=audit(projection/'graph.rrg',projection/'nets.txt',result);row['audit_seconds']=time.perf_counter()-t
            if row['audit']['legal_in_projection']:
                cm=json.loads((projection/'manifest.json').read_text());t=time.perf_counter()
                export(cm['source']['path'],case['reference']['route']['path'],raw,output/'routed.route');row['export_seconds']=time.perf_counter()-t
                check=run_process(vpr_command(vpr,case,output,200,route=False),output,env,timeout,'vpr_check.log');row['validation']=check
                native=metrics((output/'vpr_check.log').read_text(errors='replace'));row.update({k:native[k] for k in ['full_check','critical_path_ns','wirelength']})
                row['success']=row['returncode']==0 and check['returncode']==0 and native['full_check']
    if row['status']=='completed' and not row['success']:row['status']='invalid_route'
    row['workflow_seconds']=time.perf_counter()-started;write_json(output/'measurement.json',row);return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--suite',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--vpr-lock',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--cases',nargs='+');p.add_argument('--repeats',type=int,default=1)
    p.add_argument('--epochs',type=int,default=2);p.add_argument('--timeout',type=float,default=600);p.add_argument('--cpu-reference',action='store_true')
    p.add_argument('--reference-binary',type=Path);p.add_argument('--reference-sha256')
    p.add_argument('--skip-legacy',action='store_true',help='Compare native VPR and target without repeating the legacy CUDA control')
    p.add_argument('--incremental',action='store_true',help='Keep target process/context and refine selected critical connections between own-STA epochs')
    p.add_argument('--refine-threshold',type=int,default=700);p.add_argument('--refine-connections',type=int,default=2048)
    p.add_argument('--congestion-mode',choices=['full','subtree'],help='Explicit target congestion repair policy; reference binary retains its frozen default')
    p.add_argument('--refine-mode',choices=['legal','negotiate'],default='legal')
    a=p.parse_args();root=Path(__file__).resolve().parents[1];out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    suite=json.loads(a.suite.read_text());assert suite['status']=='prepared'
    cases=[c for c in suite['cases'] if not a.cases or c['id'] in a.cases]
    if not cases or a.cases and set(a.cases)!={c['id'] for c in cases}:raise ValueError('Missing target cases')
    if a.repeats<1 or a.epochs<1:raise ValueError('Positive repeats and epochs required')
    if not 0<=a.refine_threshold<=990 or a.refine_connections<1:raise ValueError('Invalid refinement budget')
    if bool(a.reference_binary)!=bool(a.reference_sha256):raise ValueError('Reference binary and SHA256 must be supplied together')
    source={str(f.relative_to(root)):sha256(f) for d in ['src','include','scripts','hardware','tests'] for f in (root/d).glob('*') if f.is_file()}
    source['CMakeLists.txt']=sha256(root/'CMakeLists.txt')
    summary={'status':'running','rows':[],'cases':cases,'hostname':platform.node(),'cpu_affinity':sorted(os.sched_getaffinity(0)),
        'source_sha256':source,'suite_sha256':sha256(a.suite),'runtime_sha256':sha256(a.runtime),
        'protocol':{'repeats':a.repeats,'epochs':a.epochs,'route_timeout':a.timeout,'iteration_limit':200,
            'incremental_target':a.incremental,'refine_threshold':a.refine_threshold,'refine_connections':a.refine_connections,
            'congestion_mode':a.congestion_mode,
            'refine_mode':a.refine_mode,
            'bootstrap':'uniform 0.5, no baseline slack or intermediate route warm start',
            'feedback':'own legal epoch -> native FULL/STA CSV -> per-connection normalized slack',
            'selection':('incremental target: minimum CPD then wirelength; full-reroute reference: minimum CPD*wirelength' if a.incremental else 'minimum CPD*wirelength legal checkpoint')+'; all attempted epochs included in online time',
            'failed_pilots':'not repeated; all failures retained','scope':'fixed-endpoint routing through FULL/STA; offline projection and hashing separate'}}
    write_json(out/'summary.json',summary)
    try:
        env=vpr_environment(json.loads(a.runtime.read_text()));vpr=verified(json.loads(a.vpr_lock.read_text())['binary']);summary['vpr_binary_sha256']=sha256(vpr)
        for name,cmd in [('device',['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv']),('vpr_runtime',[vpr,'--version']),
                         ('configure',['cmake','-S',root,'-B',out/'build','-DH3D_CUDA=ON','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CUDA_ARCHITECTURES=90']),
                         ('build',['cmake','--build',out/'build','-j4']),('oracle',['ctest','--test-dir',out/'build','--output-on-failure','--timeout','180'])]:
            result=run_process(cmd,out,env if name=='vpr_runtime' else os.environ.copy(),600,name+'.log')
            if result['returncode']!=0:raise RuntimeError(name+' failed')
        binary=out/'build/h3d_route';summary['router_binary_sha256']=sha256(binary)
        if a.incremental:
            test_env=os.environ.copy();test_env['H3D_TEST_BINARY']=str(binary)
            result=run_process(['python3','-m','unittest','discover','-s',root/'tests','-p','test_*.py','-v'],out,test_env,120,'python.log')
            if result['returncode']!=0:raise RuntimeError('Python/session validation failed')
        if a.reference_binary:
            reference=verified({'path':str(a.reference_binary),'sha256':a.reference_sha256})
            summary['reference_binary']={'path':str(reference),'sha256':a.reference_sha256}
        inputs={}
        for item in cases:
            cm=json.loads((Path(item['projection'])/'manifest.json').read_text());case=json.loads(Path(item['vpr_case']).read_text())
            for file,h in cm['files'].items():inputs[str(Path(item['projection'])/file)]=h
            for rec in [*case['inputs'].values(),case['reference']['route'],cm['source']]:inputs[rec['path']]=rec['sha256']
            inputs[item['delays']]=item['delays_sha256'];inputs[item['connections']]=item['connections_sha256']
        for file,h in inputs.items():
            if sha256(file)!=h:raise ValueError('Frozen target input changed: '+file)
        summary['input_sha256']=inputs;write_json(out/'summary.json',summary)
        for item in cases:
            variants=['vpr','legacy_cuda','target'];pilots={}
            if a.skip_legacy:variants.remove('legacy_cuda')
            if a.reference_binary:variants.insert(2,'target_reference')
            if a.cpu_reference and item==cases[0]:variants.append('cpu_target')
            for repeat in range(a.repeats):
                for variant in variants[repeat%len(variants):]+variants[:repeat%len(variants)]:
                    row={'case':item['id'],'variant':variant,'repeat':repeat,'status':'running','success':False};summary['rows'].append(row)
                    if repeat and not pilots[variant]:row.update(status='not_attempted_after_failed_pilot',success=None);write_json(out/'summary.json',summary);continue
                    write_json(out/'summary.json',summary);directory=out/f"{item['id']}_{variant}_{repeat}"
                    print(item['id'],variant,repeat,'started',flush=True)
                    try:
                        if variant in ('target','cpu_target','target_reference'):result=pipeline(reference if variant=='target_reference' else binary,item,vpr,env,directory,backend='cpu_target' if variant=='cpu_target' else 'cuda_target',epochs=a.epochs,timeout=a.timeout,incremental=a.incremental and variant!='target_reference',refine_threshold=a.refine_threshold,refine_connections=a.refine_connections,incremental_congestion=(a.congestion_mode=='subtree') if a.congestion_mode and variant!='target_reference' else None,refine_mode=a.refine_mode)
                        else:result=baseline(binary,item,vpr,env,directory,variant,a.timeout)
                        row.update(result)
                    except (OSError,ValueError,KeyError) as exc:row.update(status='error',error=str(exc),success=False)
                    if not repeat:pilots[variant]=row['success']
                    write_json(out/'summary.json',summary);print(item['id'],variant,repeat,row['status'],row.get('workflow_seconds'),flush=True)
        summary['source_unchanged']=all(sha256(root/f)==h for f,h in source.items())
        summary['inputs_unchanged']=all(sha256(f)==h for f,h in inputs.items())
        if a.reference_binary:summary['inputs_unchanged'] &= sha256(reference)==a.reference_sha256
        summary['status']='completed' if summary['source_unchanged'] and summary['inputs_unchanged'] else 'provenance_changed'
        write_json(out/'summary.json',summary)
    except Exception as exc:
        summary.update(status='infrastructure_error',error=str(exc));write_json(out/'summary.json',summary);raise


if __name__=='__main__':main()
