"""Audit completed native batches against M1 work and bounded service evidence.

Usage: OUTPUT.json MEMBER_CAP CHANGED_CAP RUN=SEMANTIC_CASE [...]
RUN is relative to this experiment's result directory. This checks complete
work, per-wave commit uniqueness/counts and final output; it assigns no clock.
The capacities must separately match the frozen model/RTL configuration.
"""
from pathlib import Path
import csv, datetime, hashlib, json, sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
out = r / 'analysis' / sys.argv[1]
out.parent.mkdir(exist_ok=True)
if out.exists():
    raise RuntimeError('append-only audit already exists')
members, changed = map(int, sys.argv[2:4])

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()

rows = []
for spec in sys.argv[4:]:
    run, case = spec.split('=')
    d, ref = r / run, r / 'semantics' / case
    receipt = json.loads((d / 'receipt.json').read_text())
    if receipt.get('returncode') != 0 or receipt.get('status', 'passed') != 'passed':
        raise RuntimeError('not a completed passing batch: ' + run)
    s = json.loads((d / 'summary.json').read_text())
    oracle = json.loads((ref / 'summary.json').read_text())
    trace = json.loads((d / 'trace_mode.json').read_text())
    metrics = list(csv.DictReader((d / 'service_metrics.csv').open()))
    waves = {(int(x['sample']), int(x['wave'])): int(x['changed'])
             for x in csv.DictReader((ref / 'waves.csv').open())}
    totals = {k: sum(i * n for i, n in enumerate(s[k + '_histogram']))
              for k in ['issue', 'accept', 'commit']}
    checks = {
        'all_output_bytes_match_M1': sha(d / 'output.bin') == sha(ref / 'output.bin'),
        'one_complete_batch_start': s['all_outputs_exact'] and s['batch_starts'] == 1 and s['jobs'] == oracle['jobs'],
        'all_sample_metrics_in_order': [int(x['sample']) for x in metrics] == list(range(s['jobs'])),
        'candidate_work_exact': totals['issue'] == totals['accept'] == oracle['candidates'],
        'changed_work_exact': totals['commit'] == oracle['changed'],
        'all_wave_invariants_checked': s['wave_invariant_checks'] == 2 * oracle['waves'],
        'every_clock_accounted': sum(s['phase_cycles']) == s['resident_cycles'] - 1 == trace['cycle_rows'] and all(sum(s[k + '_histogram']) == s['resident_cycles'] - 1 for k in totals),
        'no_cycle_or_event_sampling': trace['exact_clock_evaluation'] is True and trace['event_skipping'] is False,
        'owner_accept_retire_exact': sum(int(x['owner_accepted']) for x in metrics) == sum(int(x['owner_retired']) for x in metrics) == oracle['candidates'],
        'state_commands_drained': all(int(x['state_accepted']) == int(x['state_retired']) for x in metrics),
        'physical_ID_capacity': max(x['peak'] for x in s['channels']) <= s['physical_outstanding_cap'] == 64,
    }
    peaks = {}
    for name, capacity in [('members_peak', members), ('changed_peak', changed),
                           ('owner_mshr_peak', 32), ('owner_dirty_peak', 16),
                           ('state_mshr_peak', 32), ('state_dirty_peak', 16)]:
        peak = max(int(x[name]) for x in metrics)
        peaks[name] = {'observed': peak, 'capacity': capacity}
        checks[name + '_within_capacity'] = peak <= capacity
    traffic = s['array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read']
    cells = (ref / 'output.bin').stat().st_size // (8 * oracle['jobs'])
    checks['physical_traffic_matches_arrays'] = sum(traffic) == sum(x['reads'] + x['writes'] for x in s['channels'])
    checks['proposal_initialization_not_free'] = traffic[0] >= ((oracle['nodes'] + 3) // 4) * oracle['jobs']
    checks['state_initialization_not_free'] = traffic[8] >= ((oracle['nodes'] + 1) // 2) * oracle['jobs']
    checks['one_job_read_per_sample'] = traffic[6] == oracle['jobs']
    checks['complete_output_lines'] = traffic[7] == ((cells + 3) // 4) * oracle['jobs']
    # The testbench independently checks the exact changed set before commit.
    # This additional streaming audit rejects duplicate/missing commit events.
    seen_groups, ids, current = {}, set(), None
    duplicate = invalid_node = False
    set_digest = hashlib.sha256()

    def finish_group():
        if current is not None:
            if current in seen_groups:
                raise RuntimeError('noncontiguous commit group')
            seen_groups[current] = len(ids)
            set_digest.update(f'{current[0]},{current[1]}:'.encode())
            for node in sorted(ids):
                set_digest.update(node.to_bytes(4, 'little'))

    with (d / 'commits.csv').open() as f:
        if next(f).strip() != 'sample,wave,node':
            raise RuntimeError('unexpected commit format')
        for line in f:
            sample, wave, node = map(int, line.split(','))
            key = sample, wave
            if key != current:
                finish_group()
                current, ids = key, set()
            duplicate |= node in ids
            invalid_node |= not (0 <= node < oracle['nodes'])
            ids.add(node)
        finish_group()
    checks['no_duplicate_commit_per_wave'] = not duplicate
    checks['all_commit_nodes_in_range'] = not invalid_node
    checks['per_wave_commit_counts_exact'] = seen_groups == {k: v for k, v in waves.items() if v}
    rows.append({'run': run, 'semantic_reference': case, 'all_pass': all(checks.values()),
                 'checks': checks, 'work': totals, 'service_peaks': peaks,
                 'per_wave_commit_sets_sha256': set_digest.hexdigest(),
                 'output_sha256': sha(d / 'output.bin'),
                 'summary_sha256': sha(d / 'summary.json'),
                 'reference_summary_sha256': sha(ref / 'summary.json')})
    print(run, 'PASS' if rows[-1]['all_pass'] else 'FAIL',
          [k for k, v in checks.items() if not v], flush=True)
out.write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'all_pass': all(x['all_pass'] for x in rows), 'clock_assigned': False,
    'scope': 'completed native work/output/capacity audit; separate RTL/OOC/source qualification required',
    'results': rows}, indent=2) + '\n')
sys.exit(not all(x['all_pass'] for x in rows))
