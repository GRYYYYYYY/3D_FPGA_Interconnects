"""Conditional screening bound for the frozen one-candidate/lane datapath.

This uses audited complete work, not observed average throughput. The target
clock is explicitly hypothetical; results cannot fill a main performance cell.
"""
from pathlib import Path
import datetime, hashlib, json, math, sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
out = r / 'analysis' / sys.argv[1]
if out.exists():
    raise RuntimeError('append-only screening result already exists')
summary = r / 'analysis/completed_native_2349.json'
audit = r / 'analysis/complete_work_many32_request_model_c_large_l60_g2.json'
gpu = r / 'software/prepared_pop_gpu_b/summary.json'
rtl = r / 'rtl/many32_bank_tree_a_build/source/many_tile.sv'
assert json.loads(audit.read_text())['all_pass']
text = rtl.read_text()
assert 'assign issued=fv&fr;' in text
assert 'wire [L*96-1:0] candidate_input,candidate_output;' in text
assert '.I(L),.O(L),.W(96)' in text
software = json.loads(gpu.read_text())
rows = []
for item in json.loads(summary.read_text())['completed']:
    if item['version'] != 'many32_request_model_c' or item['latency_cycles'] != 60:
        continue
    assert item['lanes'] == 32 and item['jobs'] == 40
    candidates = item['issue']['total']
    assert candidates == item['accept']['total']
    case = item['case']
    comparators = {name: software['cases'][case + '_' + name]['mean_s']
                   for name in ['basic', 'compact']}
    best = min(comparators.values())
    bound = math.ceil(candidates / 32)
    rows.append({'case': case, 'complete_candidates': candidates,
                 'structural_maximum_candidates_per_cycle': 32,
                 'candidate_only_minimum_cycles': bound,
                 'hypothetical_target_mhz': 200,
                 'candidate_only_minimum_seconds_at_hypothetical_target': bound / 200e6,
                 'measured_software_V2_mean_seconds': comparators,
                 'necessary_clock_mhz_to_match_best_software_even_without_other_work': bound / best / 1e6,
                 'fixed_work_width_target_clock_can_match_best_software': bound / 200e6 <= best,
                 'actual_complete_model_cycles': item['resident_cycles'],
                 'actual_model_main_seconds': None})
assert len(rows) == 2
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'scope': 'conditional fixed-work32candidate issue bound only; not FPGA performance, resource proof, measured frequency or architecture-wide no-go',
          'clock_qualified': False, 'board_measured': False,
          'additional_nonnegative_work_omitted_from_bound': ['initialization', 'commit', 'control', 'memory stalls', 'output and drain'],
          'conditions_that_change_the_bound': ['actual candidate work', 'candidates per cycle', 'qualified kernel frequency'],
          'source_sha256': {str(p.relative_to(r)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in [summary, audit, gpu, rtl]}, 'results': rows}
out.write_text(json.dumps(result, indent=2) + '\n')
for row in rows:
    print(row['case'], row['candidate_only_minimum_cycles'], 'candidate-only cycles;',
          row['necessary_clock_mhz_to_match_best_software_even_without_other_work'],
          'MHz necessary, not achieved')
