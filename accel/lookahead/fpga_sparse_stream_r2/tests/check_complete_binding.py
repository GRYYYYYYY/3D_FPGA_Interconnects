"""Reject real evidence from the wrong width, cache mode, run or unit clock."""
from pathlib import Path
import json, subprocess, sys

root = Path(__file__).resolve().parents[4]
s = root / 'accel/lookahead/fpga_sparse_stream_r2'
r = root / 'results/fpga_sparse_stream_r2_20261112'
out = r / 'analysis' / 'binding_guard_tests_0104.json'
if out.exists():
    raise RuntimeError('append-only test receipt already exists')
base = dict(rtl='many32_bank_tree_a', model='many32_request_model_c',
            calibration='bank_calibration', ooc='many32_bank_context_a',
            binding='timing/expression_bindings_2255.json',
            work_audit='analysis/complete_work_many32_request_model_c_large_l60_g2.json',
            native_binding='baselines/native_reuse/complete_model_outputs_2349.json')
cases = [
    ('wrong8width', dict(rtl='many8_bank_tree_a', ooc='many8_bank_context_a'),
     'small prototype cannot qualify'),
    ('wrongcache', dict(model='many32_request_f0_model_a'), 'model/RTL parameter mismatch'),
    ('wrongrun', dict(work_audit='analysis/complete_work_many32_reg_model_d_large_l60_g2.json'),
     'work audit belongs to another model'),
    ('wrongnativebinding', dict(native_binding='baselines/native_reuse/legacy_uncorrected_counter_outputs_0059.json'),
     'native ALT output identity missing/different'),
    ('unitclock', dict(ooc='pair_checked_context_a'), 'no exact RTL/OOC binding'),
]
records = []
for name, changes, expected in cases:
    args = base | changes
    cmd = [sys.executable, str(s / 'sim/bind_complete_candidate.py'), 'guard_rejected_' + name + '.json']
    for key, value in args.items():
        cmd += ['--' + key.replace('_', '-'), value]
    result = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    passed = result.returncode != 0 and expected in result.stderr
    records.append(dict(case=name, command=cmd, returncode=result.returncode,
                        expected_error=expected, stderr=result.stderr, passed=passed))
positive = json.loads((r / 'analysis/bank32_bound_0104.json').read_text())
null_clock = not positive['main_seconds_publishable'] and all(
    x['simulated_resident_seconds'] is None and x['memory_base_latency_ns'] is None
    for x in positive['rows'])
passed = null_clock and all(x['passed'] for x in records)
out.write_text(json.dumps(dict(all_pass=passed, missing_clock_keeps_seconds_null=null_clock,
                               cases=records), indent=2) + '\n')
print('COMPLETE_BINDING_GUARDS', passed, len(records))
sys.exit(not passed)
