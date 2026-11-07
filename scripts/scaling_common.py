"""Measurement helpers shared by the scaling runner and its regression tests."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from prepare import sha256, write_json


def metrics(text):
    result = {}
    for key, pattern, cast in (
        ('critical_path_ns', r'Final critical path delay \(least slack\):\s*([\d.eE+-]+)\s*ns', float),
        ('wirelength', r'Total wirelength:\s*(\d+)', int),
        ('routing_seconds', r'Routing took\s*([\d.eE+-]+)\s*seconds', float),
        ('iterations', r'Successfully routed after\s*(\d+)\s*routing iterations', int),
        ('heap_pushes', r'total_heap_pushes:\s*(\d+)', int),
        ('heap_pops', r'total_heap_pops:\s*(\d+)', int),
    ):
        matches = re.findall(pattern, text)
        result[key] = cast(matches[-1]) if matches else None
    # Parallel VPR prints one timer per SerialConnectionRouter instance. The
    # last line alone can describe a nearly idle worker, not all routing work.
    timers=[float(x) for x in re.findall(r'Time spent on path search:\s*([\d.eE+-]+)\s*seconds',text)]
    result['search_seconds']=sum(timers) if timers else None
    result['search_timer_seconds']=timers
    result['search_timer_max_seconds']=max(timers) if timers else None
    result['search_time_scope']='Sum of per-router elapsed search timers (worker-seconds, including waits); not parallel search wall time'
    result['full_check'] = 'Completed routing consistency check successfully' in text
    result['routing_success'] = 'Circuit successfully routed' in text
    return result


def run_process(command, directory, env, timeout, log_name='process.log'):
    directory = Path(directory)
    command = list(map(str, command))
    record = {'command':command, 'timeout_seconds':timeout, 'status':'running'}
    started = time.perf_counter()
    with (directory/log_name).open('w') as log:
        process = subprocess.Popen(command, cwd=directory, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = process.wait(timeout=timeout)
            record.update(returncode=rc, status='completed' if rc == 0 else 'failed')
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
            record.update(returncode=process.returncode, status='timeout')
    record['process_seconds'] = time.perf_counter()-started
    return record


def verified(record):
    path = Path(record['path']).resolve()
    if sha256(path) != record['sha256']:
        raise ValueError(f'Frozen input changed: {path}')
    return path


def vpr_environment(runtime):
    for lib in runtime['libraries']:
        verified(lib)
    env = {k:v for k,v in os.environ.items() if not k.startswith('VPR_H3D_')}
    env.update(OMP_NUM_THREADS='1', LC_ALL='C', LD_LIBRARY_PATH=runtime['library_directory'])
    return env


def vpr_command(binary, case, directory, iterations, route=True):
    files = {k:v['path'] for k,v in case['inputs'].items()}
    cmd = [binary, files['architecture'], files['circuit'],
           '--route_chan_width', str(case['route_chan_width']),
           '--device_width', str(case['device_width']),
           '--target_utilization', str(case['target_utilization']),
           '--seed', str(case['seed']), '--num_workers','1',
           '--router_algorithm','timing_driven','--flat_routing','off','--check_route','full',
           '--net_file', str(directory/'packed.net'), '--place_file', str(directory/'fixed.place'),
           '--route_file', str(directory/'routed.route'), '--read_rr_graph', files['rr_graph'],
           '--timing_report_npaths','10','--analysis']
    if route:
        cmd += ['--route','--routing_failure_predictor','off','--max_router_iterations',str(iterations),
                '--congested_routing_iteration_threshold','0.25']
    return list(map(str, cmd))


def quality_comparison(reference, candidate, budgets=(5,10,20)):
    # A failed, timed-out, or unchecked route is never a speedup datapoint.
    if not reference.get('success') or not candidate.get('success'):
        return {'eligible':False, 'reason':'both complete, FULL-checked solutions required'}
    cp = 100*(candidate['critical_path_ns']/reference['critical_path_ns']-1)
    wire = 100*(candidate['wirelength']/reference['wirelength']-1)
    return {'eligible':True, 'critical_path_change_percent':cp, 'wirelength_change_percent':wire,
            'process_speedup':reference['process_seconds']/candidate['process_seconds'],
            'workflow_speedup':reference['workflow_seconds']/candidate['workflow_seconds'],
            'routing_speedup':reference['routing_seconds']/candidate['routing_seconds'],
            'quality_bands':{str(b):cp<=b+1e-9 and wire<=b+1e-9 for b in budgets}}


def route_fingerprint(result):
    return hashlib.sha256(json.dumps(result['routes'],sort_keys=True).encode()).hexdigest()
