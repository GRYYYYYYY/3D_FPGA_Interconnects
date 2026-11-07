#!/usr/bin/env python3
"""Same-worker, sequential native VPR/CUDA experiments with FULL/STA completion.

Route failures are data, not infrastructure failures. Each variant gets a pilot;
successful pilots get two confirmation repeats. Failed pilots remain visible,
with unattempted confirmations explicitly marked. No success-only time averages.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time

from audit import audit
from prepare import sha256, write_json
from scaling_common import (metrics, quality_comparison, route_fingerprint, run_process,
                            verified, vpr_command, vpr_environment)
from vpr_validate import export


def main():
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--suite', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cases', nargs='+')
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--timeout', type=float, default=600)
    p.add_argument('--validation-timeout', type=float, default=600)
    p.add_argument('--binary', type=Path)
    p.add_argument('--cpu-only', action='store_true', help='Local integration smoke with CPU in place of CUDA; not GPU evidence')
    a = p.parse_args()
    if a.repeats < 1 or a.timeout <= 0:
        p.error('positive repeats and timeout required')
    output = a.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    suite = json.loads(a.suite.read_text())
    if suite['status'] != 'prepared':
        raise ValueError('Only a fully prepared suite may run')
    runtime = json.loads(a.runtime.read_text()); vpr_env = vpr_environment(runtime)
    lock = json.loads(Path(suite['vpr_lock']).read_text()); vpr = verified(lock['binary'])
    selected = [c for c in suite['cases'] if a.cases is None or c['id'] in a.cases]
    if not selected or a.cases and set(a.cases) != {c['id'] for c in selected}:
        raise ValueError('Missing requested cases')
    report = {'status':'running', 'cpu_only':a.cpu_only, 'rows':[], 'comparisons':[],
              'machine':platform.platform(), 'hostname':platform.node(),
              'cpu_affinity':sorted(os.sched_getaffinity(0)),
              'suite_sha256':sha256(a.suite), 'runtime_sha256':sha256(a.runtime),
              'vpr_binary_sha256':sha256(vpr), 'cases':selected,
              'protocol':{'repeats':a.repeats, 'timeout_seconds':a.timeout,
                          'iteration_limit':suite['max_router_iterations'],
                          'failed_pilots':'Retained; confirmation runs not attempted after failed pilot.',
                          'timing':suite['timing_scope'],
                          'process_comparison':'Diagnostic only: GPU route process excludes audit/export/FULL/STA; workflow comparison includes them.',
                          'preparation':'Offline immutable projection excluded from online timing; preparation_seconds recorded per case.',
                          'search_timing':'GPU synchronized host wall time, includes launches/transfers; VPR native path-search timer; not pure kernel equivalence.',
                          'quality_bands_percent':suite['quality_budgets_percent'],
                          'variants':{'unit':'Unchanged incremental integer hop/congestion router',
                                      'delay_proxy':'1 + rounded switch delay in ps; source-rooted shortest-path tree under each congestion snapshot. Not STA criticality-driven.'}},
              'source_sha256':{str(f.relative_to(root)):sha256(f)
                               for directory in ('src','include','scripts','tests','hardware')
                               for f in (root/directory).glob('*') if f.is_file()}}
    write_json(output/'summary.json', report)
    report['source_sha256']['CMakeLists.txt'] = sha256(root/'CMakeLists.txt')
    # Runtime smoke runs on the actual CUDA worker before a long case is started.
    smoke = run_process([vpr,'--version'], output, vpr_env, 30, 'vpr_runtime.log')
    if smoke['returncode'] != 0:
        raise RuntimeError('VPR runtime smoke failed; inspect vpr_runtime.log')
    if not a.cpu_only:
        device = run_process(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv'],
                             output, os.environ.copy(), 30, 'device.log')
        if device['returncode'] != 0:
            raise RuntimeError('CUDA device query failed')
    if a.binary:
        binary = a.binary.resolve()
    else:
        build = output/'build'
        commands = [('configure',['cmake','-S',root,'-B',build,'-DCMAKE_BUILD_TYPE=Release',
                                   '-DH3D_CUDA='+('OFF' if a.cpu_only else 'ON'),
                                   '-DCMAKE_CUDA_ARCHITECTURES=90']),
                    ('build',['cmake','--build',build,'-j4']),
                    ('oracle',['ctest','--test-dir',build,'--output-on-failure','--timeout','180'])]
        for name, command in commands:
            result = run_process(command,output,os.environ.copy(),600,name+'.log')
            if result['returncode'] != 0:
                raise RuntimeError(name+' failed')
        binary = build/'h3d_route'
    report['router_binary_sha256'] = sha256(binary)
    # Check frozen provenance before, rather than inside, the timed route workflows.
    case_records = {}
    for item in selected:
        frozen = json.loads(Path(item['vpr_case']).read_text())
        for record in [*frozen['inputs'].values(), frozen['reference']['route']]:
            verified(record)
        cms = {}
        for cost, directory in item['projection'].items():
            directory = Path(directory)
            cm = json.loads((directory/'manifest.json').read_text())
            for filename, digest in cm['files'].items():
                if sha256(directory/filename) != digest:
                    raise ValueError('Projection input changed')
            verified(cm['source'])
            if cm['subset'] or cm['endpoint_route']['sha256'] != frozen['reference']['route']['sha256']:
                raise ValueError('Incomplete or mismatched endpoint projection')
            cms[cost] = cm
        case_records[item['id']] = frozen, cms
    write_json(output/'summary.json', report)
    for item in selected:
        case, cms = case_records[item['id']]
        prepared = json.loads(Path(item['prepared']).read_text())
        variants = ['vpr','unit','delay_proxy']
        pilots = {}
        for repeat in range(a.repeats):
            order = variants[repeat % 3:]+variants[:repeat % 3]
            for variant in order:
                row = {'case':item['id'],'category':item['category'], 'variant':variant,'repeat':repeat,
                       'success':False,'status':'running'}
                if repeat and not pilots[variant]:
                    row.update(status='not_attempted_after_failed_pilot',success=None)
                    report['rows'].append(row); write_json(output/'summary.json',report)
                    continue
                directory = output/f'{item["id"]}_{variant}_{repeat}'
                directory.mkdir()
                report['rows'].append(row); write_json(output/'summary.json',report)
                print(item['id'],variant,repeat,'started',flush=True)
                start = time.perf_counter()
                try:
                    # Same fixed netlist and placement, in private writable output dirs.
                    for role, filename in [('packed_netlist','packed.net'),('placement','fixed.place')]:
                        shutil.copyfile(case['inputs'][role]['path'],directory/filename)
                    if variant == 'vpr':
                        proc = run_process(vpr_command(vpr,case,directory,suite['max_router_iterations']),
                                           directory,vpr_env,a.timeout)
                        row.update(proc)
                        native = metrics((directory/'process.log').read_text(errors='replace'))
                        row.update(native)
                        row['success'] = proc['returncode'] == 0 and native['full_check'] and native['routing_success']
                    else:
                        projection = Path(item['projection'][variant]); result = directory/'result.json'
                        command = [binary,projection/'graph.rrg',projection/'nets.txt',result,
                                   '--backend','cpu' if a.cpu_only else 'cuda','--threads','1','--batch','8',
                                   '--iterations',str(suite['max_router_iterations']),
                                   '--tree-objective','source' if variant=='delay_proxy' else 'incremental']
                        proc = run_process(command,directory,os.environ.copy(),a.timeout)
                        row.update(proc)
                        if result.exists() and proc['returncode'] in (0,2):
                            raw = json.loads(result.read_text())
                            row.update(routing_seconds=raw['routing_seconds'], gpu_metrics=raw.get('gpu_metrics'),
                                       iterations=len(raw['iterations']), last_iteration=raw['iterations'][-1],
                                       route_fingerprint=route_fingerprint(raw), result_sha256=sha256(result))
                            row['search_seconds'] = (raw.get('gpu_metrics') or {}).get('search_seconds')
                            tick = time.perf_counter()
                            row['audit'] = audit(projection/'graph.rrg',projection/'nets.txt',result)
                            row['audit_seconds'] = time.perf_counter()-tick
                            if row['audit']['legal_in_projection']:
                                tick = time.perf_counter()
                                export(cms[variant]['source']['path'],case['reference']['route']['path'],raw,directory/'routed.route')
                                row['export_seconds'] = time.perf_counter()-tick
                                check = run_process(vpr_command(vpr,case,directory,suite['max_router_iterations'],route=False),
                                                    directory,vpr_env,a.validation_timeout,'vpr_check.log')
                                row['native_validation'] = check
                                native = metrics((directory/'vpr_check.log').read_text(errors='replace'))
                                row.update({k:native[k] for k in ('full_check','critical_path_ns','wirelength')})
                                row['success'] = proc['returncode']==0 and check['returncode']==0 and native['full_check']
                    if row['status'] == 'completed' and not row['success']:
                        row['status'] = 'invalid_route'
                except (OSError, ValueError, KeyError) as exc:
                    row.update(status='error',error=str(exc))
                row['workflow_seconds'] = time.perf_counter()-start
                row['offline_preparation_seconds'] = prepared['preparation_seconds']
                if not repeat:
                    pilots[variant] = row['success']
                write_json(directory/'measurement.json',row)
                write_json(output/'summary.json',report)
                print(item['id'],variant,repeat,row['status'],'success='+str(row['success']),
                      round(row['workflow_seconds'],3),flush=True)
        for repeat in range(a.repeats):
            paired = {r['variant']:r for r in report['rows'] if r['case']==item['id'] and r['repeat']==repeat}
            for variant in ('unit','delay_proxy'):
                report['comparisons'].append({'case':item['id'],'repeat':repeat,'variant':variant,
                                              **quality_comparison(paired['vpr'],paired[variant])})
        write_json(output/'summary.json',report)
    report['source_unchanged'] = all(sha256(root/p)==h for p,h in report['source_sha256'].items())
    # Recheck immutable inputs once at completion. A drift invalidates comparisons.
    for item in selected:
        case, cms = case_records[item['id']]
        for record in [*case['inputs'].values(),case['reference']['route']]: verified(record)
        for cost, cm in cms.items():
            for filename,digest in cm['files'].items():
                if sha256(Path(item['projection'][cost])/filename)!=digest:raise ValueError('Projection drift')
    report['inputs_unchanged'] = True
    report['status'] = 'completed' if report['source_unchanged'] else 'source_changed'
    write_json(output/'summary.json',report)
    return 0 if report['status']=='completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
