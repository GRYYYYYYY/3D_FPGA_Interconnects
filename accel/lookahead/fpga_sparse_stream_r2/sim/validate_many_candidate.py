"""Build and independently calibrate an immutable complete-tile candidate.

Existing outputs are never overwritten. A 32-lane run can require a completed
8-lane calibration with --gate; failing any step stops dependent work.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, subprocess, sys
from topology_limits import validate_many_topology

root = Path(__file__).resolve().parents[4]
s = root / 'accel/lookahead/fpga_sparse_stream_r2'
r = root / 'results/fpga_sparse_stream_r2_20261112'
p = argparse.ArgumentParser()
p.add_argument('variant')
p.add_argument('model')
p.add_argument('calibration')
p.add_argument('--lanes', type=int, choices=[8, 32], default=8)
p.add_argument('--ports', type=int, help='shared physical channels; defaults to lane count')
p.add_argument('--cache', type=int, choices=[0, 1], default=1)
p.add_argument('--gate', help='completed calibration JSON relative to results')
a = p.parse_args()
ports = a.ports if a.ports is not None else a.lanes
validate_many_topology(a.lanes, ports)
out = r / 'rtl' / (a.variant + '_pipeline_receipt.json')
if out.exists():
    raise RuntimeError('append-only candidate already exists')
gate = None
if a.gate:
    f = r / a.gate
    if not json.loads(f.read_text())['all_pass']:
        raise RuntimeError('prior functional gate not passed')
    gate = {'path': a.gate, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
large = a.lanes == 32
cmds = [
    ['sim/build_many.py', a.variant, str(a.lanes), str(ports),
     '-GMEMBER_CAP=' + ('8192' if large else '1024'),
     '-GCHANGED_LIMIT=' + ('8192' if large else '512'),
     '-GUSE_URAM=' + str(int(large)), '-GREQUEST_STAGE=1', '-GCACHE_ENABLE=' + str(a.cache)],
    ['sim/run_many.py', a.variant, '60', 'native'],
    ['sim/run_many.py', a.variant, '60', 'fixtures'],
    ['sim/run_many.py', a.variant, '120', 'stress,stress_random'],
    ['sim/run_many.py', a.variant, '60', 'external_nodes_65536,external_nodes_4194304'],
    ['sim/calibrate_many_suites.py', a.model, a.variant, a.calibration],
    ['sim/sweep_fixed_time.py', a.variant, a.model],
    ['tests/batch_capacity.py', a.variant],
]
if large:
    cmds += [['tests/many_hot_capacity.py', a.variant, a.model],
             ['sim/calibrate_many_boundaries.py', a.model, a.variant]]
state = {'variant': a.variant, 'model': a.model, 'lanes': a.lanes,
         'physical_channels': ports, 'cache': a.cache, 'gate': gate, 'status': 'running', 'steps': [],
         'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save():
    out.write_text(json.dumps(state, indent=2) + '\n')
save()
with out.with_suffix('.log').open('w') as log:
    for cmd in cmds:
        command = [sys.executable, str(s / cmd[0]), *cmd[1:]]
        print('RUN', command, flush=True)
        rc = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT).returncode
        state['steps'].append({'command': command, 'returncode': rc})
        if rc:
            state['status'] = 'failed'
            break
        save()
    else:
        state['status'] = 'passed'
state['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
save()
print('COMPLETE_CANDIDATE', a.variant, state['status'], flush=True)
sys.exit(state['status'] != 'passed')
