#!/usr/bin/env python3
"""Check recorded target measurements against immutable candidates/native logs."""
import argparse
import json
import math
from pathlib import Path

from prepare import sha256, write_json
from scaling_common import metrics, route_fingerprint


def verify_fixed_inputs(baseline, validation):
    """Compare the actual native-check inputs with the paired baseline inputs."""
    if validation[:3] != baseline[:3]:
        raise ValueError('Native binary, architecture, or circuit differs from paired VPR')
    def value(command, flag):
        if command.count(flag) != 1 or command.index(flag) + 1 == len(command):
            raise ValueError('Missing or ambiguous fixed constraint: ' + flag)
        return command[command.index(flag) + 1]
    for flag in ('--seed', '--route_chan_width', '--device_width', '--num_workers',
                 '--target_utilization', '--flat_routing'):
        if value(validation, flag) != value(baseline, flag):
            raise ValueError('Native constraint differs from paired VPR: ' + flag)
    if Path(value(validation, '--read_rr_graph')).resolve() != Path(value(baseline, '--read_rr_graph')).resolve():
        raise ValueError('Native resource graph differs from paired VPR')
    hashes = {}
    for flag in ('--net_file', '--place_file'):
        original, candidate = Path(value(baseline, flag)), Path(value(validation, flag))
        original_hash, candidate_hash = sha256(original), sha256(candidate)
        if original_hash != candidate_hash:
            raise ValueError('Actual native input differs from paired VPR: ' + flag)
        hashes[flag] = candidate_hash
    return hashes


def verify(run):
    run=Path(run).resolve();summary=json.loads((run/'summary.json').read_text())
    if summary['status']!='completed' or not summary['source_unchanged'] or not summary['inputs_unchanged']:
        raise ValueError('Experiment incomplete or provenance checks failed')
    checked=[];failures=[];rollbacks=[];native_logs=0;fixed_pairs=[]
    baselines={(row['case'],row['repeat']):row for row in summary['rows'] if row['variant']=='vpr'}
    def same(a,b):
        if a is None or b is None:
            if a is not b:raise ValueError('Missing timer mismatch')
        elif not math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-7):raise ValueError(f'Measurement mismatch: {a} != {b}')
    for row in summary['rows']:
        directory=run/f"{row['case']}_{row['variant']}_{row['repeat']}"
        if row['status'].startswith('not_attempted'):continue
        if row['variant']=='vpr':
            native=metrics((directory/'process.log').read_text(errors='replace'));native_logs+=1
            if row['success']:
                if not native['full_check'] or not native['routing_success']:raise ValueError('Native baseline not legal')
                for k in ('critical_path_ns','wirelength'):same(native[k],row[k])
            else:failures.append(str(directory))
            continue
        epochs=row.get('epochs',[row]);legal=[]
        for e in epochs:
            path=directory/f"epoch_{e['epoch']}" if 'epochs' in row else directory
            if not e.get('success'):
                failures.append(str(path));continue
            result=path/'result.json';raw=json.loads(result.read_text())
            if sha256(result)!=e['result_sha256'] or route_fingerprint(raw)!=e['route_fingerprint']:
                raise ValueError('Candidate changed: '+str(result))
            if not raw['success'] or raw['iterations'][-1]['overflow'] or raw['iterations'][-1]['unrouted']:
                raise ValueError('Illegal candidate reported as successful')
            if not e['audit']['legal_in_projection']:raise ValueError('Missing projection audit')
            native=metrics((path/'vpr_check.log').read_text(errors='replace'));native_logs+=1
            if not native['full_check'] or e['validation']['returncode']!=0:raise ValueError('Missing native FULL check')
            baseline=baselines.get((row['case'],row['repeat']))
            if baseline is None or 'command' not in baseline:raise ValueError('Missing paired native baseline command')
            fixed_hashes=verify_fixed_inputs(baseline['command'],e['validation']['command'])
            fixed_pairs.append({'candidate':str(path),'fixed_copied_input_sha256':fixed_hashes})
            for k in ('critical_path_ns','wirelength'):same(native[k],e[k])
            same(raw['routing_seconds'],e['routing_seconds'])
            if raw['gpu_metrics']!=e['gpu_metrics']:raise ValueError('GPU metric mismatch')
            if e.get('incremental_refinement') and raw['gpu_metrics']['spatial_index_bytes']!=0:
                raise ValueError('Incremental epoch re-uploaded static spatial index')
            if raw.get('refinement_converged') is False:
                if not legal or e['route_fingerprint']!=legal[-1]['route_fingerprint']:
                    raise ValueError('Failed refinement did not restore the preceding legal forest')
                if raw['refinement_accepted'] or not (raw['refinement_failed_overflow'] or raw['refinement_failed_unrouted']):
                    raise ValueError('Rollback failure/acceptance counters inconsistent')
                rollbacks.append(str(path))
            checked.append({'candidate':str(result),'sha256':e['result_sha256'],
                'native_route_sha256':sha256(path/'routed.route'),'native_log_sha256':sha256(path/'vpr_check.log')})
            legal.append(e)
        if 'epochs' not in row:continue
        complete=all('routing_seconds' in e for e in epochs)
        same(row['routing_seconds'],sum(e['routing_seconds'] for e in epochs) if complete else None)
        same(row['process_seconds'],sum(e['process_seconds'] for e in epochs))
        if row['workflow_seconds']+1e-6<sum(e['workflow_seconds'] for e in epochs):raise ValueError('Feedback epoch time omitted')
        if bool(legal)!=row['success']:raise ValueError('Workflow success mismatch')
        if legal:
            key=(lambda e:(e['critical_path_ns'],e['wirelength'],e['epoch'])) if row.get('incremental_refinement') else (lambda e:(e['critical_path_ns']*e['wirelength'],e['critical_path_ns'],e['epoch']))
            best=min(legal,key=key)
            if best['epoch']!=row['selected_epoch'] or best['route_fingerprint']!=row['route_fingerprint']:raise ValueError('Checkpoint selection changed')
            for k in ('critical_path_ns','wirelength'):same(row[k],best[k])
        if row.get('incremental_refinement'):
            pids={e['session_pid'] for e in epochs if 'session_pid' in e}
            if len(pids)!=1:raise ValueError('STA feedback restarted routing process')
            if (directory/'session.log').read_text().count('route_phase=graph_read_begin')!=1:raise ValueError('Unexpected graph reload')
            if all(e['success'] for e in epochs) and row['session_exit']['returncode']!=0:raise ValueError('Persistent session failed on exit')
    record=dict(status='verified',summary_sha256=sha256(run/'summary.json'),native_logs=native_logs,
                candidates=checked,failed_attempts_retained=failures,
                failed_refinements_rolled_back=rollbacks,
                fixed_input_pairs=fixed_pairs,
                scope='candidate hashes, native FULL/STA, paired native constraints and copied inputs, checkpoint selection, all-epoch timing, persistent process reuse; full original input hash checks are from runner')
    write_json(run/'artifact_verification.json',record)
    return record


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
    r=verify(a.run);print(json.dumps({k:v for k,v in r.items() if k not in ('candidates','failed_attempts_retained')}))
