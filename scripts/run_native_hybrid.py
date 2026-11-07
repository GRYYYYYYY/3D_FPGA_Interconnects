"""Same-worker native VPR controls, paired-query diagnostics and hybrid routing.

Every variant performs its own in-process FULL/STA, followed by an independent
locked-original-VPR readback. Both times are retained, with no hidden fallback.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

from prepare import sha256,write_json
from scaling_common import metrics,run_process,verified,vpr_command,vpr_environment


def route_body(path):
    lines=Path(path).read_text().splitlines()
    start=next(i for i,line in enumerate(lines) if line.startswith('Net '))
    return hashlib.sha256(('\n'.join(lines[start:])+'\n').encode()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--binary',type=Path,required=True)
    p.add_argument('--library',type=Path)
    p.add_argument('--suite',type=Path,required=True)
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--vpr-lock',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',default='ex5p')
    p.add_argument('--variants',default='original_vpr,native_cpu,pair,hybrid')
    p.add_argument('--budget',type=int,default=2048)
    p.add_argument('--max-offloads',type=int)
    p.add_argument('--pair-limit',type=int)
    p.add_argument('--pair-stride',type=int,default=1)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--batch-size',type=int,default=4)
    p.add_argument('--batch-wait-us',type=int,default=50)
    p.add_argument('--cooperative-blocks',type=int,default=0)
    p.add_argument('--verify-state',action='store_true')
    p.add_argument('--diagnostics',action='store_true')
    p.add_argument('--capture-limit',type=int,default=0)
    p.add_argument('--capture-stride',type=int,default=5)
    p.add_argument('--native-repeats',type=int,default=3)
    p.add_argument('--timeout',type=float,default=900)
    p.add_argument('--repeats',type=int,default=1)
    p.add_argument('--repeat-start',type=int,default=0)
    p.add_argument('--cpu-cores',type=int,default=0)
    p.add_argument('--prewarm-inputs',action='store_true')
    p.add_argument('--overuse-report',action='store_true')
    p.add_argument('--parallel-lookahead',action='store_true',help='Parallel deterministic wire sampling for candidate variants only; original controls unchanged')
    args=p.parse_args();output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    run=run_process;cpu_budget=None
    if args.cpu_cores:
        from native_cpu_budget import pin_budget,audited_process
        cpu_budget=pin_budget(args.cpu_cores);run=audited_process
        write_json(output/'cpu_budget.json',cpu_budget)
    binary=args.binary.resolve();library=args.library.resolve() if args.library else None;lock=json.loads(args.vpr_lock.read_text());original=verified(lock['binary'])
    bindings={str(f):sha256(f) for f in [binary,*([library] if library else []),args.suite.resolve(),args.runtime.resolve(),args.vpr_lock.resolve()]}
    env=vpr_environment(json.loads(args.runtime.read_text()));env={k:v for k,v in env.items() if not k.startswith(('VPR_HYBRID_','H3D_GPU_'))}
    requested=args.cases.split(',');suite=json.loads(args.suite.read_text())['cases'];assert set(requested)<={c['id'] for c in suite}
    variants=args.variants.split(',');assert set(variants)<={'original_vpr','native_cpu','pair','hybrid','original_parallel','native_parallel','batch','guard','capture'}
    if set(variants)&{'pair','hybrid','batch'} and not library:raise ValueError('GPU variants require --library')
    record={'status':'running','binary':str(binary),'library':str(library),'bindings':bindings,'measurements':[],
            'pop_budget':args.budget,'max_offloads':args.max_offloads,'pair_stride':args.pair_stride,'workers':args.workers,'batch_size':args.batch_size,'batch_wait_us':args.batch_wait_us,'cooperative_blocks':args.cooperative_blocks,
            'time_scope':'native_process_seconds includes in-process RRG load, routing, FULL/STA; workflow_seconds additionally includes locked-original independent readback for every variant; compilation and input hashing excluded',
            'diagnostic_instrumentation':args.diagnostics,'capture_limit':args.capture_limit,'capture_stride':args.capture_stride,'native_repeats':args.native_repeats,'pair_is_diagnostic':True,'state_audit_is_diagnostic':args.verify_state,
            'cpu_budget':cpu_budget,'repeat_start':args.repeat_start,'repeats':args.repeats,'prewarm_inputs':args.prewarm_inputs,'overuse_report':args.overuse_report,'parallel_lookahead':args.parallel_lookahead}
    write_json(output/'summary.json',record)
    try:
        for item in suite:
            if item['id'] not in requested:continue
            case=json.loads(Path(item['vpr_case']).read_text())
            for r in case['inputs'].values():verified(r)
            for repeat in range(args.repeat_start,args.repeat_start+args.repeats):
                order=variants[repeat%len(variants):]+variants[:repeat%len(variants)]
                for variant in order:
                    directory=output/f'{item["id"]}_{repeat}_{variant}';directory.mkdir()
                    row={'case':item['id'],'repeat':repeat,'variant':variant,'directory':str(directory),'success':False,'diagnostic':variant in ['pair','capture'] or args.verify_state or args.diagnostics or args.max_offloads is not None or args.capture_limit>0}
                    record['measurements'].append(row);write_json(output/'summary.json',record)
                    if args.prewarm_inputs:
                        warm_start=time.perf_counter();warm_bytes=0
                        for entry in case['inputs'].values():
                            with Path(entry['path']).open('rb') as f:
                                while chunk:=f.read(8*1024*1024):warm_bytes+=len(chunk)
                        row['input_prewarm']={'bytes':warm_bytes,'seconds':time.perf_counter()-warm_start,'scope':'Sequential read before measured workflow; all variants, no global cache flushing'}
                    tick=time.perf_counter()
                    for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],directory/name)
                    run_env=env.copy()
                    if args.parallel_lookahead and variant not in ['original_vpr','original_parallel']:
                        run_env['VPR_HYBRID_LOOKAHEAD_PARALLEL']='1'
                    if variant in ['pair','hybrid','batch','guard','capture']:
                        run_env.update(VPR_HYBRID_MODE={'pair':'pair','hybrid':'select','batch':'batch','guard':'guard','capture':'capture'}[variant],
                                       VPR_HYBRID_POP_BUDGET=str(args.budget),VPR_HYBRID_REPORT=str(directory/'hybrid.json'))
                        if variant not in ['guard','capture']:run_env['VPR_HYBRID_LIBRARY']=str(library)
                        if variant=='batch':run_env.update(VPR_HYBRID_BATCH_SIZE=str(args.batch_size),VPR_HYBRID_BATCH_WAIT_US=str(args.batch_wait_us))
                        run_env.update(H3D_GPU_COOPERATIVE_BLOCKS=str(args.cooperative_blocks),H3D_GPU_DEVICE_REPORT=str(directory/'device.json'))
                        if args.diagnostics:run_env.update(VPR_HYBRID_DIAGNOSTICS='1',H3D_GPU_TIMING='1')
                        if args.capture_limit and variant in ['pair','capture']:
                            run_env.update(VPR_HYBRID_CAPTURE=str(directory/'takeovers'),VPR_HYBRID_CAPTURE_LIMIT=str(args.capture_limit),
                                           VPR_HYBRID_CAPTURE_STRIDE=str(args.capture_stride),VPR_HYBRID_NATIVE_REPEATS=str(args.native_repeats))
                        if args.verify_state:run_env['VPR_HYBRID_VERIFY_STATE']='1'
                        if args.max_offloads is not None:run_env['VPR_HYBRID_MAX_OFFLOADS']=str(args.max_offloads)
                        if variant=='pair' and args.pair_limit is not None:run_env['VPR_HYBRID_MAX_OFFLOADS']=str(args.pair_limit)
                        if variant=='pair':run_env['VPR_HYBRID_PAIR_STRIDE']=str(args.pair_stride)
                    executable=original if variant in ['original_vpr','original_parallel'] else binary
                    command=vpr_command(executable,case,directory,200)
                    if args.overuse_report:command+=['--generate_rr_node_overuse_report','on']
                    if variant in ['original_parallel','native_parallel','batch','guard']:
                        command[command.index('--router_algorithm')+1]='parallel'
                        command[command.index('--num_workers')+1]=str(args.workers)
                    row['execution_settings']={'gpu_timing':run_env.get('H3D_GPU_TIMING','0'),'diagnostics':run_env.get('VPR_HYBRID_DIAGNOSTICS','0'),'capture':bool(run_env.get('VPR_HYBRID_CAPTURE')),'cpu_affinity':sorted(os.sched_getaffinity(0)),'parallel_lookahead':run_env.get('VPR_HYBRID_LOOKAHEAD_PARALLEL','0')}
                    proc=run(command,directory,run_env,args.timeout)
                    native=metrics((directory/'process.log').read_text(errors='replace'));row.update(proc);row.update(native)
                    row['native_process_seconds']=proc['process_seconds'];row['inputs']=case['inputs']
                    if (directory/'hybrid.json').exists():row['hybrid']=json.loads((directory/'hybrid.json').read_text())
                    if (directory/'device.json').exists():row['device']=json.loads((directory/'device.json').read_text())
                    if proc['returncode']==0 and native['full_check'] and native['routing_success']:
                        row['route_body_sha256']=route_body(directory/'routed.route');row['route_sha256']=sha256(directory/'routed.route')
                        check=run(vpr_command(original,case,directory,200,route=False),directory,env,args.timeout,'independent_check.log')
                        checked=metrics((directory/'independent_check.log').read_text(errors='replace'));row['independent_check']=check;row['independent_metrics']=checked
                        row['success']=check['returncode']==0 and checked['full_check'] and checked['critical_path_ns']==native['critical_path_ns'] and checked['wirelength']==native['wirelength']
                        if sha256(directory/'routed.route')!=row['route_sha256']:raise RuntimeError('readback changed native route')
                    row['workflow_seconds']=time.perf_counter()-tick
                    write_json(directory/'measurement.json',row);write_json(output/'summary.json',record)
                    print(item['id'],variant,repeat,row['success'],row.get('critical_path_ns'),row.get('hybrid',{}),flush=True)
                    # A routing failure/timeout is an experimental outcome. Keep
                    # subsequent controls and cases; final summary fails closed.
                    if row.get('hybrid',{}).get('errors'):raise RuntimeError(f'{item["id"]}/{variant} reported GPU errors')
                rows={r['variant']:r for r in record['measurements'] if r['case']==item['id'] and r['repeat']==repeat}
                if all(rows.get(v,{}).get('success') for v in ['original_vpr','pair']):
                    if rows['original_vpr']['route_body_sha256']!=rows['pair']['route_body_sha256']:
                        raise RuntimeError(f'{item["id"]}: pair changed original CPU route')
                if 'native_cpu' in rows:
                    for control in ['original_vpr','pair','capture']:
                        if control in rows and rows[control].get('success') and rows['native_cpu'].get('success') and rows[control]['route_body_sha256']!=rows['native_cpu']['route_body_sha256']:
                            raise RuntimeError(f'{item["id"]}: {control} changed the original CPU route')
                if all(rows.get(v,{}).get('success') for v in ['original_parallel','native_parallel']):
                    # Parallel VPR can change paths with scheduling (observed
                    # with the identical original binary on elliptic). Retain
                    # the discrepancy and require repeated controls for claims;
                    # exact equality remains mandatory for serial CPU/pair.
                    record.setdefault('parallel_controls',[]).append({
                        'case':item['id'],'repeat':repeat,
                        'route_equal':rows['original_parallel']['route_body_sha256']==rows['native_parallel']['route_body_sha256'],
                        'original_cpd_ns':rows['original_parallel']['critical_path_ns'],
                        'native_cpd_ns':rows['native_parallel']['critical_path_ns']})
        if any(sha256(Path(k))!=v for k,v in bindings.items()):raise RuntimeError('hybrid experiment binding changed')
        record['status']='completed'
        record['all_routes_successful']=all(r['success'] for r in record['measurements'])
    except Exception as exc:
        record['status']='failed';record['error']=repr(exc);raise
    finally:write_json(output/'summary.json',record)


if __name__=='__main__':main()
