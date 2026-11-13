"""Compare audited native40 runs of one executable under memory assumptions.

Usage: OUTPUT.json MODEL RUN [RUN ...]. The first run is the cycle/traffic
reference. Only latency and service gap may vary; no frequency is assigned.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('output')
p.add_argument('model')
p.add_argument('runs', nargs='+')
a = p.parse_args()
if len(a.runs) < 2 or len(set(a.runs)) != len(a.runs):
    raise ValueError('at least two distinct completed runs required')
for name in [a.output, a.model, *a.runs]:
    if Path(name).name != name:
        raise ValueError('local names required')
out = r / 'analysis' / a.output
if out.exists():
    raise RuntimeError('append-only output already exists')
hashes, digest_cache = {}, {}


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def digest(path):
    path = path.resolve()
    if path not in digest_cache:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(8 << 20), b''):
                h.update(block)
        digest_cache[path] = h.hexdigest()
    return digest_cache[path]


def read(rel):
    path = r / rel
    hashes[str(rel)] = digest(path)
    return json.loads(path.read_text())


model_dir = Path('model') / a.model
binding = read(model_dir / 'source_binding.json')
for name, expected in binding['source_sha256'].items():
    require(digest(r / model_dir / 'source' / name) == expected,
            'modified frozen model source: ' + name)
exe_sha = digest(r / model_dir / 'model')
audits = {}
for run in a.runs:
    audit = read(f'analysis/complete_work_{a.model}_{run}.json')
    require(audit['all_pass'] and len(audit['results']) == 2,
            'complete native work audit missing or failed: ' + run)
    audits[run] = {x['run']: x for x in audit['results']}

array_names = ['proposal_write', 'proposal_read', 'row', 'edge', 'cost',
               'cell_metadata', 'job', 'output', 'state_write', 'state_read']
rows = []
for case in ['bnn_export', 'lstm_s2']:
    reference_identity = reference_contract = reference_work = None
    reference_cycles = reference_bytes = None
    for run in a.runs:
        folder = model_dir / run / case
        audit = audits[run][str(folder)]
        receipt = read(folder / 'receipt.json')
        summary = read(folder / 'summary.json')
        require(audit['all_pass'] and receipt['status'] == 'passed'
                and receipt['returncode'] == 0, 'incomplete native batch')
        require(receipt['whole_native_batch'] and summary['jobs'] == 40
                and summary['batch_starts'] == 1 and summary['all_outputs_exact'],
                'not one complete native40 batch')
        require(receipt['executable_sha256'] == exe_sha, 'different executable')
        require(digest(r / folder / 'summary.json') == audit['summary_sha256'],
                'summary changed after work audit')
        require(not (r / folder / 'physical_time_contract.json').exists(),
                'this comparison requires the cycle-domain service contract')
        cmd = receipt['command']
        identity = {'workload': digest(Path(cmd[1])), 'prepared': digest(Path(cmd[2])),
                    'golden': digest(Path(cmd[3])), 'output': digest(r / folder / 'output.bin')}
        require(identity['workload'] == receipt['workload_sha256']
                and identity['golden'] == receipt['golden_sha256']
                and identity['output'] == identity['golden'] == audit['output_sha256']
                == receipt['output_sha256'], 'input/output identity mismatch')
        if 'prepared_sha256' in receipt:
            require(identity['prepared'] == receipt['prepared_sha256'],
                    'prepared input changed after launch')
        for index in [1, 2, 3]:
            hashes[cmd[index]] = digest(Path(cmd[index]))
        contract = {k: summary[k] for k in ['lanes', 'physical_channels', 'seed',
                                          'physical_outstanding_cap', 'jobs']}
        work = dict(audit['work'], per_wave_commit_sets_sha256=audit['per_wave_commit_sets_sha256'])
        if reference_identity is None:
            reference_identity, reference_contract, reference_work = identity, contract, work
        require(identity == reference_identity and contract == reference_contract
                and work == reference_work, 'comparison changed input, work or finite topology')
        beats = summary['array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read']
        require(len(beats) == len(array_names), 'unknown traffic layout')
        channels = summary['channels']
        counts = [x['reads'] + x['writes'] for x in channels]
        require(sum(counts) == sum(beats) and len(channels) == contract['physical_channels'],
                'physical traffic mismatch')
        cycles, total_bytes = summary['resident_cycles'], sum(beats) * 32
        if reference_cycles is None:
            reference_cycles, reference_bytes = cycles, total_bytes
        rows.append({'case': case, 'run': str(folder), 'identity': identity,
                     'finite_contract': contract, 'full_work': work,
                     'base_latency_cycles': summary['latency_cycles'],
                     'service_gap_cycles': summary['service_gap_cycles'],
                     'resident_cycles': cycles, 'internal_bytes': total_bytes,
                     'cycles_over_reference': cycles / reference_cycles,
                     'bytes_over_reference': total_bytes / reference_bytes,
                     'array_bytes': dict(zip(array_names, [x * 32 for x in beats])),
                     'issue_per_resident_cycle': work['issue'] / cycles,
                     'commit_per_resident_cycle': work['commit'] / cycles,
                     'physical_ID_peaks': [x['peak'] for x in channels],
                     'service_peaks': audit['service_peaks'],
                     'phase_cycles': summary['phase_cycles'],
                     'simulated_seconds': None})
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'all_pass': True, 'model': a.model, 'executable_sha256': exe_sha,
          'reference_run': a.runs[0], 'rows': rows, 'evidence_sha256': hashes,
          'clock_assigned': False, 'board_measured': False,
          'scope': 'complete exact-cycle architecture simulations; same executable/input/work/seed/finite topology; hypothetical shared synchronous32B ports,64IDs/port,6/7ready and0..12cycle jitter; only base latency and minimum gap vary; no FPGA seconds or measured speedup',
          'input_identity_scope': 'actual input files rehashed during this analysis; older receipts without startup hashes are not retroactively startup measurements'}
out.write_text(json.dumps(result, indent=2) + '\n')
for row in rows:
    print(row['run'], row['resident_cycles'], 'cycles', row['internal_bytes'], 'bytes')
