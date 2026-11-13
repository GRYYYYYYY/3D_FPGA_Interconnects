"""Assemble audited resident rows without assigning unqualified FPGA clocks.

Only exact complete-candidate bindings may supply simulated seconds. Software
measurements, architecture cycles and physical qualification remain separate.
Native E2/Process and board results are outside this resident comparison.
"""
from pathlib import Path
import argparse, csv, datetime, hashlib, json, math

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
p = argparse.ArgumentParser()
p.add_argument('output', help='new output basename below analysis, without extension')
p.add_argument('bindings', nargs='+', help='complete candidate JSON paths relative to results')
a = p.parse_args()
if Path(a.output).name != a.output or '.' in a.output:
    raise ValueError('output must be a local basename without extension')
out = r / 'analysis' / a.output
if any(out.with_suffix(ext).exists() for ext in ['.json', '.csv']):
    raise RuntimeError('append-only comparison already exists')
hashes = {}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read(rel):
    path = r / rel
    hashes[str(rel)] = sha(path)
    return json.loads(path.read_text())


software_path = 'software/prepared_pop_gpu_b/summary.json'
software = read(software_path)
assert software['all_receipts_pass'] and software['receipt_count'] == 218
software_rows = []
measured = {}
for case in ['bnn_export', 'lstm_s2']:
    for backend in ['cpu', 'basic', 'compact']:
        x = software['cases'][case + '_' + backend]
        assert x['n'] == len(x['raw_samples_s']) == 9
        assert all(t > 0 for t in x['raw_samples_s'])
        assert math.isclose(sum(x['raw_samples_s']) / x['n'], x['mean_s'], rel_tol=1e-12)
        measured[case, backend] = x['mean_s']
        software_rows.append(dict(case=case, backend=backend, **x,
                                  classification='measured_software_resident', source=software_path))

rows, seen = [], set()
for path in a.bindings:
    b = read(path)
    assert b['complete97_fixed36_boundaries4_calibrated']
    assert not b['board_measured'] and not b['shell_qualified']
    assert b['parameters']['L'] in [32, 64]
    # A stale comparison must fail rather than silently using modified inputs.
    for rel, expected in b['evidence_sha256'].items():
        assert sha(r / rel) == expected, 'changed binding evidence: ' + rel
    qualified = b['complete_kernel_clock_qualified']
    assert qualified == b['main_seconds_publishable']
    if qualified:
        assert b['qualified_period_ns'] > 0
        assert math.isclose(b['qualified_period_ns'] * b['qualified_clock_mhz'], 1000)
    else:
        assert b['qualified_period_ns'] is None and b['qualified_clock_mhz'] is None
    for x in b['rows']:
        identity = b['RTL'], b['OOC'], b.get('physical_qualification_tag', 'routed_sta_v2'), x['run']
        assert identity not in seen, 'duplicate candidate/run'
        seen.add(identity)
        s = read(x['run'] + '/summary.json')
        assert s['all_outputs_exact'] and s['jobs'] == 40 and s['batch_starts'] == 1
        assert s['resident_cycles'] == x['resident_cycles']
        assert s['physical_channels'] == b['parameters']['PHYS']
        assert s['lanes'] == b['parameters']['L']
        assert sha(r / x['run'] / 'output.bin') == x['output_sha256']
        seconds = x['simulated_resident_seconds']
        if qualified:
            assert seconds > 0 and math.isclose(seconds, s['resident_cycles'] * b['qualified_period_ns'] * 1e-9)
        else:
            assert seconds is None
        beats = s['array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read']
        assert sum(beats) == sum(c['reads'] + c['writes'] for c in s['channels'])
        work = {k: sum(i * n for i, n in enumerate(s[k + '_histogram']))
                for k in ['issue', 'accept', 'commit']}
        assert work['issue'] == work['accept']
        row = dict(case=x['case'], RTL=b['RTL'], model=b['model'], OOC=b['OOC'],
                   physical_qualification_tag=identity[2], run=x['run'], binding=path,
                   lanes=s['lanes'], shared_physical_channels=s['physical_channels'],
                   proposal_cache_enabled=b['parameters']['CACHE_ENABLE'], jobs=40,
                   memory_base_latency_cycles=x['memory_base_latency_cycles'],
                   memory_min_gap_cycles=x['memory_min_gap_cycles'],
                   memory_jitter_cycles=x['memory_jitter_cycles'],
                   memory_contract=b['memory_contract'], resident_cycles=s['resident_cycles'],
                   internal_bytes=sum(beats) * 32,
                   candidates_per_resident_cycle=work['issue'] / s['resident_cycles'],
                   commits_per_resident_cycle=work['commit'] / s['resident_cycles'],
                   complete_kernel_clock_qualified=qualified,
                   qualified_OOC_clock_mhz=b['qualified_clock_mhz'],
                   simulated_resident_seconds=seconds,
                   memory_base_latency_ns=x['memory_base_latency_ns'],
                   memory_min_gap_ns=x['memory_min_gap_ns'],
                   measured_FPGA_resident_seconds=None, board_measured=False,
                   classification='architecture_simulation_with_hypothetical_memory',
                   output_sha256=x['output_sha256'])
        for backend in ['cpu', 'basic', 'compact']:
            row['measured_' + backend + '_mean_seconds'] = measured[x['case'], backend]
            row[backend + '_over_simulated_FPGA_ratio'] = measured[x['case'], backend] / seconds if qualified else None
        rows.append(row)

result = dict(updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              comparison_contract='RESIDENT_COMPLETE_BATCH_V2',
              includes=['cost_load_once', 'mutable_initialization', 'all_internal_memory',
                        'required_control', 'conflicts', 'commit', 'sample_switch', 'output_ACK_and_drain'],
              excludes=['external_conversion', 'first_H2D', 'final_D2H'],
              software=software_rows, architecture=rows, evidence_sha256=hashes,
              no_board_or_shell_claim=True,
              scope_note='Each architecture row is one complete deterministic simulated batch, not an independent timing sample. Ratios require exact complete-kernel OOC qualification. Memory service remains hypothetical even after OOC qualification. Native E2/Process cannot supply these denominators.')
out.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
columns = ['case', 'RTL', 'OOC', 'lanes', 'shared_physical_channels', 'proposal_cache_enabled',
           'memory_base_latency_cycles', 'memory_min_gap_cycles', 'resident_cycles', 'internal_bytes',
           'candidates_per_resident_cycle', 'commits_per_resident_cycle', 'qualified_OOC_clock_mhz',
           'simulated_resident_seconds', 'measured_FPGA_resident_seconds',
           'measured_cpu_mean_seconds', 'measured_basic_mean_seconds', 'measured_compact_mean_seconds',
           'cpu_over_simulated_FPGA_ratio', 'basic_over_simulated_FPGA_ratio',
           'compact_over_simulated_FPGA_ratio', 'binding', 'run']
with out.with_suffix('.csv').open('w') as f:
    w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
    w.writeheader()
    w.writerows(rows)
print('RESIDENT_COMPARISON', len(rows), 'architecture rows;',
      sum(x['complete_kernel_clock_qualified'] for x in rows), 'with qualified full-kernel OOC clocks')
