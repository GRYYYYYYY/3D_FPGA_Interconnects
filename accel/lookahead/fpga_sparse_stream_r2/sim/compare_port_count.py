"""Compare completed native batches whose only active design change is P.

Usage: OUTPUT.json P32_BINDING.json P8_BINDING.json (basenames below analysis).
Both bindings must already contain exact source/calibration/work/ACK audits.
This reports cycles and traffic only, independently of any clock qualification.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output')
parser.add_argument('p32')
parser.add_argument('p8')
a = parser.parse_args()
for name in [a.output, a.p32, a.p8]:
    if Path(name).name != name:
        raise ValueError('local analysis basenames required')
out = r / 'analysis' / a.output
if out.exists():
    raise RuntimeError('append-only output already exists')
hashes, cache = {}, {}


def sha(path):
    path = path.resolve()
    if path not in cache:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(8 << 20), b''):
                h.update(block)
        cache[path] = h.hexdigest()
    return cache[path]


def read(rel):
    path = r / rel
    hashes[str(rel)] = sha(path)
    return json.loads(path.read_text())


bindings = [read('analysis/' + n) for n in [a.p32, a.p8]]
assert [b['parameters']['PHYS'] for b in bindings] == [32, 8], 'expected ordered P32/P8 bindings'
cache_mode = bindings[0]['parameters']['CACHE_ENABLE']
assert cache_mode in [0, 1] and all(b['parameters']['CACHE_ENABLE'] == cache_mode for b in bindings), 'same F0/F1 cache choice required'
model_sources, macros, rtl_sources, indexed = [], [], [], []
for b, ports in zip(bindings, [32, 8]):
    assert b['complete97_fixed36_boundaries4_calibrated']
    assert b['parameters']['CACHE_ENABLE'] == cache_mode
    assert b['parameters']['L'] == 32 and b['parameters']['PHYS'] == ports
    for rel, expected in b['evidence_sha256'].items():
        assert sha(r / rel) == expected, 'changed binding evidence: ' + rel
    model = Path('model') / b['model']
    mb = read(model / 'source_binding.json')
    for name, expected in mb['source_sha256'].items():
        assert sha(r / model / 'source' / name) == expected, 'changed frozen model: ' + name
    model_sources.append(mb['source_sha256'])
    macros.append(dict(x[2:].split('=', 1) for x in mb['command'] if x.startswith('-D') and '=' in x))
    assert macros[-1]['TILE_CACHE'] == str(cache_mode) and macros[-1]['TILE_P'] == str(ports)
    # The sole historic source difference is inside methods of this unselected
    # F0 class. Bind the exact reviewed versions; do not waive arbitrary edits.
    source = r / model / 'source'
    assert 'std::conditional_t<CACHE,OwnerCycle,OwnerF0Cycle>' in (source / 'many_tile_model.hpp').read_text()
    assert 'ManyTileModel<TILE_L,TILE_P,TILE_MC,TILE_CC,TILE_CACHE>' in (source / 'many_tile_driver.cpp').read_text()
    rb_dir = Path('rtl') / (b['RTL'] + '_build')
    rb = read(rb_dir / 'source_binding.json')
    sv = {k: v for k, v in rb['source_sha256'].items() if k.endswith('.sv')}
    assert len(sv) == 27
    for name, expected in sv.items():
        assert sha(r / rb_dir / 'source' / name) == expected
    rtl_sources.append(sv)
    rows = {}
    for x in b['rows']:
        key = (x['case'], x['memory_base_latency_cycles'], x['memory_min_gap_cycles'])
        assert key not in rows, 'duplicate case/contract'
        folder = Path(x['run'])
        receipt = read(folder / 'receipt.json')
        summary = read(folder / 'summary.json')
        audit = read(x['full_work_capacity_ACK_audit'])
        assert audit['all_pass'] and receipt['status'] == 'passed' and receipt['returncode'] == 0
        work = next(w for w in audit['results'] if w['run'] == str(folder))
        assert work['all_pass'] and sha(r / folder / 'summary.json') == work['summary_sha256']
        assert receipt['executable_sha256'] == sha(r / model / 'model')
        assert summary['all_outputs_exact'] and summary['jobs'] == 40 and summary['batch_starts'] == 1
        assert summary['resident_cycles'] == x['resident_cycles'] and summary['physical_channels'] == ports
        assert summary['physical_outstanding_cap'] == 64
        assert not (r / folder / 'physical_time_contract.json').exists()
        command = receipt['command']
        identity = [sha(Path(command[i])) for i in [1, 2, 3]]
        assert identity[0] == receipt['workload_sha256']
        assert identity[2] == receipt['golden_sha256'] == receipt['output_sha256'] == x['output_sha256']
        assert sha(r / folder / 'output.bin') == identity[2] == work['output_sha256']
        if 'prepared_sha256' in receipt:
            assert identity[1] == receipt['prepared_sha256']
        for i in [1, 2, 3]:
            hashes[command[i]] = identity[i - 1]
        rows[key] = (x, summary, work, identity)
    indexed.append(rows)

assert rtl_sources[0] == rtl_sources[1], 'active RTL differs'
assert {k: v for k, v in bindings[0]['parameters'].items() if k != 'PHYS'} == {
    k: v for k, v in bindings[1]['parameters'].items() if k != 'PHYS'}
assert {k: v for k, v in macros[0].items() if k != 'TILE_P'} == {
    k: v for k, v in macros[1].items() if k != 'TILE_P'}
assert model_sources[0].keys() == model_sources[1].keys()
different = [k for k in model_sources[0] if model_sources[0][k] != model_sources[1][k]]
assert set(different) <= {'owner_f0_cycle_model.hpp'}
if different:
    assert cache_mode == 1, 'F0 requires identical active model sources'
    assert [s[different[0]] for s in model_sources] == [
        '2cc16bdf9456e93bb8b65d2f49cb88e8b3faff6edd38ccceea20cbfe9e9ac68f',
        'a3305758a2f42acf9385ad2537c4a4a4122f922db8f03be894782fa1120179ba']
common = sorted(set(indexed[0]) & set(indexed[1]))
assert common, 'no matched completed memory contract'
names = ['proposal_write', 'proposal_read', 'row', 'edge', 'cost',
         'cell_metadata', 'job', 'output', 'state_write', 'state_read']
rows = []
for key in common:
    lhs, rhs = indexed[0][key], indexed[1][key]
    assert lhs[3] == rhs[3], 'different input/preparation/golden'
    assert lhs[2]['work'] == rhs[2]['work']
    assert lhs[2]['per_wave_commit_sets_sha256'] == rhs[2]['per_wave_commit_sets_sha256']
    for field in ['lanes', 'seed', 'physical_outstanding_cap', 'jobs', 'batch_starts',
                  'latency_cycles', 'service_gap_cycles']:
        assert lhs[1][field] == rhs[1][field], field
    values = []
    for x, s, audit, identity in [lhs, rhs]:
        beats = s['array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read']
        assert len(beats) == len(names)
        assert sum(beats) == sum(c['reads'] + c['writes'] for c in s['channels'])
        values.append({'run': x['run'], 'ports': s['physical_channels'],
                       'resident_cycles': s['resident_cycles'], 'internal_bytes': 32 * sum(beats),
                       'array_bytes': dict(zip(names, [32 * n for n in beats])),
                       'phase_cycles': s['phase_cycles'], 'service_peaks': audit['service_peaks'],
                       'issue_per_resident_cycle': audit['work']['issue'] / s['resident_cycles'],
                       'commit_per_resident_cycle': audit['work']['commit'] / s['resident_cycles']})
    rows.append({'case': key[0], 'base_latency_cycles': key[1], 'service_gap_cycles': key[2],
                 'P32': values[0], 'P8': values[1],
                 'P8_over_P32_cycles': values[1]['resident_cycles'] / values[0]['resident_cycles'],
                 'P8_over_P32_bytes': values[1]['internal_bytes'] / values[0]['internal_bytes'],
                 'work': lhs[2]['work'], 'per_wave_commit_sets_sha256': lhs[2]['per_wave_commit_sets_sha256'],
                 'input_prepared_golden_sha256': lhs[3]})
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'all_pass': True, 'rows': rows, 'evidence_sha256': hashes,
          'common_RTL_files': 27, 'same_active_model_and_macros_except_ports': True,
          'inactive_model_source_difference': different,
          'cache_enabled': cache_mode,
          'inactive_source_reason': ('TILE_CACHE=1 instantiates OwnerCycle; the exact reviewed F0 method-only change is not instantiated' if different else 'all frozen model source files identical'),
          'unmatched_P32_contracts': sorted(set(indexed[0]) - set(indexed[1])),
          'unmatched_P8_contracts': sorted(set(indexed[1]) - set(indexed[0])),
          'scope': 'matched complete native40 cycle-domain simulations; each port retains64IDs so total physical credits also change with port count; routing/resource/clock evidence is separate',
          'clock_assigned_by_this_analysis': False, 'board_measured': False}
out.write_text(json.dumps(result, indent=2) + '\n')
for row in rows:
    print(row['case'], row['base_latency_cycles'], row['service_gap_cycles'],
          'P8/P32 cycles', row['P8_over_P32_cycles'], 'bytes', row['P8_over_P32_bytes'])
