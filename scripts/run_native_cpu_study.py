"""Frozen CPU ablations with shared lookahead artifacts and independent checks.

Each lane owns its cases and CPU pool. Measurements within a lane are sequential;
different lanes may overlap, and that limitation is recorded rather than hidden.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import socket
import time

from native_cpu_budget import audited_process, pin_budget
from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_hybrid import route_body
from scaling_common import metrics, verified, vpr_command, vpr_environment


def set_option(command, name, value):
    if name in command:
        command[command.index(name) + 1] = str(value)
    else:
        command.extend([name, str(value)])


def cpu_command(binary, case, directory, variant, workers, cache=None, iterations=200):
    command = vpr_command(binary, case, directory, iterations)
    set_option(command, '--num_workers', workers)
    set_option(command, '--router_algorithm', variant.get('router', 'parallel'))
    set_option(command, '--router_lookahead', variant.get('lookahead', 'map'))
    set_option(command, '--generate_rr_node_overuse_report', 'on')
    if cache:
        set_option(command, '--read_router_lookahead', cache)
    return command


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--lane', required=True)
    args = p.parse_args()
    plan_path = args.plan.resolve()
    plan = json.loads(plan_path.read_text())
    for entry in plan.get('runner_bindings', {}).values():
        verified(entry)
    lane = plan['lanes'][args.lane]
    root = Path(plan['output']) / args.lane
    root.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_AS, (64 * 1024**3, 64 * 1024**3))
    binaries = {name: verified(entry) for name, entry in plan['binaries'].items()}
    env = vpr_environment(json.loads(Path(plan['runtime']).read_text()))
    env = {k: v for k, v in env.items() if not k.startswith(('VPR_HYBRID_', 'H3D_GPU_'))}
    pool = lane['cpu_pool']
    record = {'status': 'running', 'plan': str(plan_path), 'plan_sha256': sha256(plan_path),
              'lane': args.lane, 'hostname': socket.gethostname(), 'cpu_pool': pool,
              'started_utc': datetime.now(timezone.utc).isoformat(), 'measurements': [],
              'cache_qualifications': [], 'skipped': [], 'resource_limits': {'address_space_gib': 64, 'core_mib': 512},
              'concurrency_scope': plan['concurrency_scope']}
    write_json(root / 'summary.json', record)
    current_budget = None
    lease_active = False

    def admission(workers=0):
        """Bound total measured CPU concurrency without changing another task."""
        nonlocal lease_active
        state_path = Path(plan['output']) / 'admission.json'
        while True:
            with state_path.with_suffix('.lock').open('a+') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                state = json.loads(state_path.read_text()) if state_path.exists() else {}
                state = {pid: item for pid, item in state.items() if Path('/proc', pid).exists()}
                state.pop(str(os.getpid()), None)
                if not workers or sum(x['workers'] for x in state.values()) + workers <= plan['max_active_cpu_cores']:
                    if workers:
                        state[str(os.getpid())] = {'lane': args.lane, 'workers': workers}
                    write_json(state_path, state)
                    lease_active = bool(workers)
                    return
            time.sleep(1)

    def budget(workers):
        nonlocal current_budget
        os.sched_setaffinity(0, pool)
        current_budget = pin_budget(workers)
        return current_budget

    def prepare_directory(directory, case):
        directory.mkdir()
        for role, filename in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]:
            shutil.copyfile(case['inputs'][role]['path'], directory / filename)

    def warm_inputs(case, cache=None):
        start = time.perf_counter()
        total = 0
        for path in [Path(x['path']) for x in case['inputs'].values()] + ([cache] if cache else []):
            with path.open('rb') as f:
                while chunk := f.read(8 * 1024**2):
                    total += len(chunk)
        return {'seconds': time.perf_counter() - start, 'bytes': total,
                'scope': 'Equal sequential pre-read before timing; no filesystem cold-cache claim.'}

    def qualify_cache(case_id, case, workers):
        admission(workers)
        entry = {'case': case_id, 'status': 'running', 'builders': []}
        record['cache_qualifications'].append(entry)
        write_json(root / 'summary.json', record)
        for label, binary, parallel in [('original', binaries['original'], False),
                                        ('optimized', binaries['cpu'], True)]:
            directory = root / f'{case_id}_cache_{label}'
            prepare_directory(directory, case)
            local_env = env.copy()
            if parallel:
                local_env['VPR_HYBRID_LOOKAHEAD_PARALLEL'] = '1'
            command = cpu_command(binary, case, directory, {}, workers, iterations=1)
            set_option(command, '--write_router_lookahead', directory / 'lookahead.bin')
            outcome = audited_process(command, directory, local_env, plan['timeout_seconds'])
            text = (directory / 'process.log').read_text(errors='replace')
            cache = directory / 'lookahead.bin'
            # VPR returns UNIMPLEMENTABLE_EXIT_CODE (2) when the deliberate
            # one-iteration setup cannot converge; generic errors (1) are rejected.
            valid = (outcome['returncode'] in [0, 2] and cache.is_file() and cache.stat().st_size > 0
                     and 'Computing router lookahead map took' in text
                     and outcome['cpu_budget_audit']['verified']
                     and 'Assertion' not in text and 'Aborted' not in text)
            item = {'builder': label, **outcome, 'cache_written': valid,
                    'note': 'One-iteration cache setup; routing convergence is not required and this is not a performance sample.'}
            if valid:
                item.update(cache=str(cache), sha256=sha256(cache), bytes=cache.stat().st_size)
            entry['builders'].append(item)
            write_json(root / 'summary.json', record)
            if not valid:
                entry['status'] = 'failed'
                raise RuntimeError(f'{case_id}: {label} cache qualification failed')
        first, second = entry['builders']
        if first['sha256'] != second['sha256']:
            entry['status'] = 'mismatch'
            raise RuntimeError(f'{case_id}: serial/parallel lookahead bytes differ')
        entry.update(status='passed', shared_cache=first['cache'], sha256=first['sha256'],
                     inputs={k: v['sha256'] for k, v in case['inputs'].items()})
        write_json(root / 'summary.json', record)
        admission()
        return Path(first['cache']), first['sha256']

    try:
        for case_entry in lane['cases']:
            case_id = case_entry['id']
            case = json.loads(Path(case_entry['vpr_case']).read_text())
            for entry in case['inputs'].values():
                verified(entry)
            budget(4)
            shared_cache, cache_hash = qualify_cache(case_id, case, 4)
            failed_original = set()
            for phase in case_entry['phases']:
                variants = [plan['variants'][v] | {'id': v} for v in phase['variants']]
                for workers in phase['workers']:
                    budget(workers)
                    jobs = [(v, mode) for mode in phase['cache_modes'] for v in variants]
                    for repeat in range(phase.get('repeat_start', 0), phase.get('repeat_start', 0) + phase['repeats']):
                        shift = repeat % len(jobs)
                        for variant, cache_mode in jobs[shift:] + jobs[:shift]:
                            key = f'{case_id}_{phase["name"]}_w{workers}_r{repeat}_{variant["id"]}_{cache_mode}'
                            if (workers, cache_mode) in failed_original and variant['id'] == 'original':
                                record['skipped'].append({'key': key, 'reason': 'Original failed an earlier repeat at this CPU/cache setting; corrected controls continue.'})
                                write_json(root / 'summary.json', record)
                                continue
                            cache = shared_cache if cache_mode == 'reuse' else None
                            admission(workers)
                            directory = root / key
                            row = {'key': key, 'case': case_id, 'phase': phase['name'], 'variant': variant['id'],
                                   'repeat': repeat, 'workers': workers, 'cache_mode': cache_mode,
                                   'status': 'running', 'success': False, 'directory': str(directory),
                                   'cpu_budget': current_budget, 'inputs': case['inputs'],
                                   'lookahead_cache_sha256': cache_hash if cache else None,
                                   'execution_settings': {'parallel_lookahead': variant['parallel'],
                                                          'router': variant.get('router', 'parallel'),
                                                          'lookahead': variant.get('lookahead', 'map'),
                                                          'gpu_enabled': False, 'diagnostics': False}}
                            record['measurements'].append(row)
                            row['input_prewarm'] = warm_inputs(case, cache)
                            write_json(root / 'summary.json', record)
                            tick = time.perf_counter()
                            prepare_directory(directory, case)
                            local_env = env.copy()
                            if variant['parallel']:
                                local_env['VPR_HYBRID_LOOKAHEAD_PARALLEL'] = '1'
                            binary = binaries[variant['binary']]
                            row['binary_sha256'] = plan['binaries'][variant['binary']]['sha256']
                            command = cpu_command(binary, case, directory, variant, workers, cache)
                            outcome = audited_process(command, directory, local_env, plan['timeout_seconds'])
                            native = metrics((directory / 'process.log').read_text(errors='replace'))
                            row.update(outcome)
                            row.update(native)
                            row['native_process_seconds'] = outcome['process_seconds']
                            if outcome['returncode'] == 0 and native['routing_success'] and native['full_check']:
                                row['route_sha256'] = sha256(directory / 'routed.route')
                                row['route_body_sha256'] = route_body(directory / 'routed.route')
                                check = audited_process(vpr_command(binaries['original'], case, directory, 200, route=False),
                                                        directory, env, plan['timeout_seconds'], 'independent_check.log')
                                checked = metrics((directory / 'independent_check.log').read_text(errors='replace'))
                                row.update(independent_check=check, independent_metrics=checked)
                                row['success'] = (check['returncode'] == 0 and checked['full_check']
                                                  and all(native[k] == checked[k] for k in ['critical_path_ns', 'wirelength'])
                                                  and outcome['cpu_budget_audit']['verified']
                                                  and check['cpu_budget_audit']['verified'])
                                if sha256(directory / 'routed.route') != row['route_sha256']:
                                    raise RuntimeError('Independent readback changed route bytes')
                            row['workflow_seconds'] = time.perf_counter() - tick
                            row['finished_utc'] = datetime.now(timezone.utc).isoformat()
                            write_json(directory / 'measurement.json', row)
                            row['log_evidence'] = log_evidence(directory)
                            row['success'] = bool(row['success'] and row['log_evidence']['final_overused_nodes'] == 0
                                                  and row['critical_path_ns'] is not None and row['wirelength'] is not None)
                            if cache and sha256(shared_cache) != cache_hash:
                                raise RuntimeError('Shared lookahead cache changed')
                            if not row['success'] and variant['id'] == 'original':
                                failed_original.add((workers, cache_mode))
                            write_json(directory / 'measurement.json', row)
                            write_json(root / 'summary.json', record)
                            admission()
                            print(json.dumps({k: row.get(k) for k in ['key', 'success', 'native_process_seconds', 'critical_path_ns', 'wirelength']}), flush=True)
            for entry in case['inputs'].values():
                verified(entry)
        for entry in plan['binaries'].values():
            verified(entry)
        for entry in plan.get('runner_bindings', {}).values():
            verified(entry)
        if sha256(plan_path) != record['plan_sha256']:
            raise RuntimeError('Frozen plan changed')
        record.update(status='completed', all_routes_successful=all(x['success'] for x in record['measurements']))
    except Exception as exc:
        record.update(status='failed', error=repr(exc))
        raise
    finally:
        if lease_active:
            admission()
        record['finished_utc'] = datetime.now(timezone.utc).isoformat()
        write_json(root / 'summary.json', record)


if __name__ == '__main__':
    main()
