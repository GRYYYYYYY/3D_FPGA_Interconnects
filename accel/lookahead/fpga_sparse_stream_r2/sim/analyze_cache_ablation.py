"""Compare complete F0/F1 model cycles under one explicit service contract.

Requires full work/capacity audits, identical inputs and hardware parameters
apart from the cache choice. Ratios are cycle ratios, not FPGA/GPU speedups.
Usage: OUTPUT.json F0_MODEL F1_MODEL RUN (e.g. large_l60_g2).
"""
from pathlib import Path
import datetime, hashlib, json, sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
output, f0, f1, run = sys.argv[1:5]
out = r / 'analysis' / output
assert not out.exists(), 'append-only analysis already exists'
hashes = {}

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()

def read(rel):
    p = r / rel
    hashes[str(rel)] = digest(p)
    return json.loads(p.read_text())

parameters, audits = [], []
for cache, model in enumerate([f0, f1]):
    binding = read(Path('model') / model / 'source_binding.json')
    macros = dict(x[2:].split('=', 1) for x in binding['command']
                  if x.startswith('-D') and '=' in x)
    assert int(macros['TILE_CACHE']) == cache
    keys = ['TILE_L', 'TILE_P', 'TILE_MC', 'TILE_CC', 'R2_REGISTERED_READY', 'R2_REQUEST_STAGE']
    parameters.append({k: int(macros.get(k, 0)) for k in keys})
    audit = read(f'analysis/complete_work_{model}_{run}.json')
    assert audit['all_pass'] and len(audit['results']) == 2
    audits.append({x['run']: x for x in audit['results']})
assert parameters[0] == parameters[1], 'different hardware/service configurations'

rows = []
for case in ['bnn_export', 'lstm_s2']:
    summaries, receipts, beats = [], [], []
    for model, audit in zip([f0, f1], audits):
        folder = Path('model') / model / run / case
        receipt = read(folder / 'receipt.json')
        summary = read(folder / 'summary.json')
        assert receipt['status'] == 'passed' and receipt['returncode'] == 0
        assert receipt['whole_native_batch'] and summary['all_outputs_exact']
        assert summary['jobs'] == 40 and summary['batch_starts'] == 1
        assert audit[str(folder)]['all_pass']
        assert digest(r / folder / 'summary.json') == audit[str(folder)]['summary_sha256']
        assert digest(r / folder / 'output.bin') == audit[str(folder)]['output_sha256'] == receipt['output_sha256']
        assert digest(r / 'model' / model / 'model') == receipt['executable_sha256']
        summaries.append(summary)
        receipts.append(receipt)
        beats.append(summary['array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read'])
    a, b = summaries
    for key in ['latency_cycles', 'service_gap_cycles', 'seed', 'lanes', 'physical_channels', 'jobs']:
        assert a[key] == b[key], key
    for key in ['workload_sha256', 'golden_sha256', 'output_sha256']:
        assert receipts[0][key] == receipts[1][key], key
    # The same prepared representation is used; its transformation is not a
    # cache benefit. This hash is calculated from actual bytes, not a pathname.
    prepared = [Path(x['command'][2]) for x in receipts]
    assert digest(prepared[0]) == digest(prepared[1])
    hashes[str(prepared[0])] = digest(prepared[0])
    counts = {}
    for name in ['issue', 'accept', 'commit']:
        totals = [sum(i * n for i, n in enumerate(s[name + '_histogram'])) for s in summaries]
        assert totals[0] == totals[1], 'different complete work: ' + name
        counts[name] = totals[0]
    rows.append(dict(case=case, F0_cycles=a['resident_cycles'], F1_cycles=b['resident_cycles'],
                     F0_over_F1_cycle_ratio=a['resident_cycles'] / b['resident_cycles'],
                     F1_cycle_reduction_fraction=1 - b['resident_cycles'] / a['resident_cycles'],
                     F0_internal_bytes=sum(beats[0]) * 32, F1_internal_bytes=sum(beats[1]) * 32,
                     F1_traffic_reduction_fraction=1 - sum(beats[1]) / sum(beats[0]),
                     full_work=counts, latency_cycles=a['latency_cycles'],
                     service_gap_cycles=a['service_gap_cycles'], seed=a['seed'],
                     simulated_seconds=None, board_measured=False))
result = dict(updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              all_pass=True, F0=f0, F1=f1, run=run, hardware_parameters_except_cache=parameters[0],
              rows=rows, evidence_sha256=hashes, clock_assigned=False,
              scope='complete audited native40 model cycles under identical hypothetical memory; F0 retains finite requests/ACK and node-state cache, F1 adds proposal owner cache/merge; no OOC or board time assigned',
              stall_counter_caution='F0 owner stall counts same-node collisions; F1 counts all blocked dispatches. Do not compare those counters as identical definitions.')
out.write_text(json.dumps(result, indent=2) + '\n')
for row in rows:
    print(row['case'], 'F0/F1 cycles', row['F0_over_F1_cycle_ratio'],
          'traffic reduction', row['F1_traffic_reduction_fraction'])
