"""Conditional transfer screening, never a full-kernel performance result.

Usage: CANDIDATE_BINDING.json NEW_OUTPUT.json
The observed traffic and mapping are fixed. A future cache, layout, algorithm,
port contract or clock domain changes the premise and must be evaluated anew.
"""
from pathlib import Path
import datetime
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
binding_path = r / 'analysis' / sys.argv[1]
output = r / 'analysis' / sys.argv[2]
if output.exists():
    raise RuntimeError('analysis output already exists')
binding = json.loads(binding_path.read_text())
assert binding['complete97_fixed36_boundaries4_calibrated']
software_path = r / 'software/prepared_pop_gpu_b/summary.json'
software = json.loads(software_path.read_text())
assert software['all_receipts_pass'] and software['receipt_count'] == 218
evidence = {}


def record(path):
    evidence[str(path.relative_to(r))] = hashlib.sha256(path.read_bytes()).hexdigest()


record(binding_path)
record(software_path)
rows = []
for bound in binding['rows']:
    run = r / bound['run']
    s = json.loads((run / 'summary.json').read_text())
    assert s['all_outputs_exact'] and s['jobs'] == 40 and s['batch_starts'] == 1
    assert s['resident_cycles'] == bound['resident_cycles']
    assert hashlib.sha256((run / 'output.bin').read_bytes()).hexdigest() == bound['output_sha256']
    channels = [c['reads'] + c['writes'] for c in s['channels']]
    beats = s['array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read']
    assert len(channels) == binding['parameters']['PHYS'] and sum(channels) == sum(beats)
    gap = s['service_gap_cycles']
    # Earliest possible last acceptance on the busiest physical port. This
    # ignores latency, arbitration, initialization ordering and final drain.
    minimum_cycles = max(1 + (count - 1) * gap if count else 0 for count in channels)
    assert 0 < minimum_cycles <= s['resident_cycles']
    gpu = {}
    for kind in ['basic', 'compact']:
        sample = software['cases'][bound['case'] + '_' + kind]
        assert sample['n'] == 9 and len(sample['raw_samples_s']) == 9
        seconds = sample['mean_s']
        gpu[kind] = {
            'measured_resident_mean_seconds': seconds,
            'necessary_kernel_MHz_if_observed_traffic_mapping_and_cycle_gap_unchanged': minimum_cycles / seconds / 1e6,
            'necessary_aggregate_GB_per_second_if_observed_bytes_unchanged': sum(beats) * 32 / seconds / 1e9,
        }
    rows.append({'run': bound['run'], 'memory_base_latency_cycles': s['latency_cycles'],
                 'memory_min_gap_cycles': gap, 'observed_internal_bytes': sum(beats) * 32,
                 'trace_conditional_minimum_transfer_cycles': minimum_cycles,
                 'GPU_comparisons': gpu, 'FPGA_performance_seconds': None})
    record(run / 'summary.json')
    record(run / 'output.bin')
    record(r / bound['full_work_capacity_ACK_audit'])

result = {'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'classification': 'conditional_screening_only_not_FPGA_performance_or_global_no_go',
          'premises': ['same observed per-port traffic and mapping', 'same finite synchronous cycle-gap port contract'],
          'omitted_costs': ['response latency', 'arbitration', 'dependency stalls', 'required control', 'final drain'],
          'scope_limit': 'Changes to traffic, layout, workload or physical service invalidate this screening; no measured HBM claim.',
          'clock_qualified_by_this_analysis': False, 'board_measured': False,
          'rows': rows, 'evidence_sha256': evidence}
output.write_text(json.dumps(result, indent=2) + '\n')
for row in rows:
    print(row['run'], row['trace_conditional_minimum_transfer_cycles'],
          'conditional cycles;', {k: round(v['necessary_kernel_MHz_if_observed_traffic_mapping_and_cycle_gap_unchanged'], 3)
                                  for k, v in row['GPU_comparisons'].items()}, 'necessary MHz; no FPGA seconds')
