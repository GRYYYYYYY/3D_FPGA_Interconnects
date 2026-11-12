"""Summarize completed native RTL/model batches without assigning a clock.

Host elapsed time is deliberately absent. Partial batches remain pending and
cannot contribute output, throughput or a speedup denominator.
"""
from pathlib import Path
import csv, datetime, hashlib, json, sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
out = r / 'analysis' / sys.argv[1]
out.parent.mkdir(exist_ok=True)
if out.exists():
    raise RuntimeError('append-only summary already exists')
rows, pending = [], []
arrays = ['proposal_write', 'proposal_read', 'CSR_row', 'CSR_edge', 'cost',
          'cell_metadata', 'job', 'output', 'state_write', 'state_read']
for spec in sys.argv[2:]:
    kind, version = spec.split(':')
    if kind not in ['rtl', 'model']:
        raise ValueError(kind)
    folders = (sorted((r / 'rtl' / (version + '_native_l60')).glob('*/receipt.json'))
               if kind == 'rtl' else sorted((r / 'model' / version).glob('large*/*/receipt.json')))
    for receipt in folders:
        entry = json.loads(receipt.read_text())
        if entry.get('returncode') != 0 or entry.get('status', 'passed') != 'passed':
            pending.append({'run': str(receipt.parent.relative_to(r)),
                            'status': entry.get('status', 'failed_or_incomplete')})
            continue
        summary = receipt.parent / 'summary.json'
        s = json.loads(summary.read_text())
        if not s['all_outputs_exact'] or s['batch_starts'] != 1:
            raise RuntimeError('nonqualifying batch ' + str(receipt))
        cycles = s['resident_cycles']
        traffic = s['array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read']
        row = {'version': version, 'kind': kind, 'case': receipt.parent.name,
               'run': str(receipt.parent.relative_to(r)), 'jobs': s['jobs'],
               'lanes': s['lanes'], 'physical_channels': s['physical_channels'],
               'resident_cycles': cycles, 'latency_cycles': s['latency_cycles'],
               'service_gap_cycles': s['service_gap_cycles'], 'seed': s['seed'],
               'array_32byte_transactions': dict(zip(arrays, traffic)),
               'internal_traffic_bytes': sum(traffic) * 32,
               'physical_outstanding_peak_per_channel': [x['peak'] for x in s['channels']],
               'phase_cycles': s['phase_cycles'],
               'output_sha256': hashlib.sha256((receipt.parent / 'output.bin').read_bytes()).hexdigest(),
               'summary_sha256': hashlib.sha256(summary.read_bytes()).hexdigest(),
               'clock_qualified_mhz': None, 'board_measured': False,
               'scope': s['scope']}
        for name in ['issue', 'accept', 'commit']:
            hist = s[name + '_histogram']
            total = sum(i * n for i, n in enumerate(hist))
            row[name] = {'total': total, 'per_resident_cycle': total / cycles,
                         'peak_per_cycle': max(i for i, n in enumerate(hist) if n),
                         'cycles_with_multiple': sum(hist[2:]),
                         'histogram': hist}
        physical = receipt.parent / 'physical_time_contract.json'
        if physical.exists():
            row['hypothetical_physical_time_contract'] = json.loads(physical.read_text())
        metrics_file = receipt.parent / 'service_metrics.csv'
        if metrics_file.exists():
            metrics = list(csv.DictReader(metrics_file.open()))
            if [int(x['sample']) for x in metrics] != list(range(s['jobs'])):
                raise RuntimeError('missing or unordered sample metrics: ' + str(metrics_file))
            fields = [k for k in metrics[0] if k != 'sample']
            peaks = {k: max(int(x[k]) for x in metrics) for k in fields if k.endswith('_peak')}
            totals = {k: sum(int(x[k]) for x in metrics) for k in fields if not k.endswith('_peak')}
            row['service_metrics'] = {
                'totals': totals, 'maximum_per_owner_across_samples': peaks,
                'source_sha256': hashlib.sha256(metrics_file.read_bytes()).hexdigest(),
                'request_stall_units': 'sum of per-owner blocked-request cycles; overlaps between owners and services, not additive global elapsed time',
            }
            source_binding = r / 'model' / version / 'source_binding.json'
            command = json.loads(source_binding.read_text())['command']
            row['service_metrics']['owner_stall_definition'] = (
                'F0 counter records same-node in-flight collisions only; not all blocked requests'
                if '-DTILE_CACHE=0' in command else
                'F1 counter records a nonempty owner request output that cannot dispatch')
            row['service_metrics']['state_stall_definition'] = (
                'nonempty state request output that cannot dispatch')
            row['service_metrics']['owner_hit_merge_miss_partition_exact'] = (
                totals['owner_hits'] + totals['owner_misses'] + totals['owner_merges']
                == totals['owner_accepted'] == totals['owner_retired'])
            row['service_metrics']['state_hit_miss_partition_exact'] = (
                totals['state_hits'] + totals['state_misses']
                == totals['state_accepted'] == totals['state_retired'])
        # These are mutually exclusive controller states, not an attribution of
        # all simultaneous lane stalls to one physical cause. Raw states remain.
        phase_groups = {
            'batch_entry': [0], 'cost_load_once': [1, 2, 3], 'job_read': [4, 5],
            'neutral_handshake': [6], 'sample_reset': [7],
            'mutable_initialization_and_seed': [8, 9], 'bucket_minimum': [10, 11],
            'active_POP_with_overlapped_edge_services': [12, 13],
            'edge_and_router_drain': [14, 15], 'owner_state_write_fence': [16, 17],
            'changed_commit': [18, 19], 'original_bucket_closure_and_POP_reduce_drain': [23, 24],
            'output_and_ACK_drain': [30, 31, 32, 33, 34, 35, 37],
        }
        named = {i for group in phase_groups.values() for i in group}
        row['controller_phase_groups'] = {
            name: {'cycles': sum(s['phase_cycles'][i] for i in indices),
                   'fraction_of_resident_cycles': sum(s['phase_cycles'][i] for i in indices) / cycles}
            for name, indices in phase_groups.items()}
        row['controller_phase_groups']['other_raw_states'] = {
            str(i): n for i, n in enumerate(s['phase_cycles']) if i not in named and n}
        row['phase_accounting_boundary_cycles'] = cycles - sum(s['phase_cycles'])
        rows.append(row)
out.write_text(json.dumps({'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          'scope': 'completed full-output batches; no OOC clock or board-performance transfer',
                          'completed': rows, 'pending_or_failed': pending}, indent=2) + '\n')
print('COMPLETED', len(rows), 'PENDING_OR_FAILED', len(pending))
for row in rows:
    print(row['version'], row['case'], row['resident_cycles'],
          'issue/cycle', round(row['issue']['per_resident_cycle'], 6),
          'commit/cycle', round(row['commit']['per_resident_cycle'], 6))
