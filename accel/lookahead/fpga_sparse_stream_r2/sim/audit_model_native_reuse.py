"""Bind completed architecture output to the already qualified native ALT map.

Usage: OUTPUT.json MODEL/RUN [...]. This assigns no clock, performs no new
native timing and never promotes ALT output to STRICT equivalence.
"""
from pathlib import Path
import datetime
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
prior = r / 'baselines/native_reuse/audit.json'
identity = json.loads(prior.read_text())
assert identity['all_inputs_and_outputs_exact']
out = r / 'baselines/native_reuse' / sys.argv[1]
if out.exists():
    raise RuntimeError('append-only native binding already exists')
results = []
for run in sys.argv[2:]:
    for expected in identity['native_identity']:
        d = r / 'model' / run / expected['case']
        receipt = json.loads((d / 'receipt.json').read_text())
        summary = json.loads((d / 'summary.json').read_text())
        output = d / 'output.bin'
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        checks = {
            'completed': receipt['status'] == 'passed' and receipt['returncode'] == 0,
            'same_bound_workload': receipt['workload_sha256'] == expected['R2_input']['file_sha256'],
            'one_complete40_batch': summary['jobs'] == 40 and summary['batch_starts'] == 1 and summary['all_outputs_exact'],
            'all_bytes_native_ALT_equal': digest == receipt['output_sha256'] == receipt['golden_sha256'] == expected['qualified_native_capture']['sample_output_sha256'],
            'complete_output_size': output.stat().st_size == expected['qualified_native_capture']['sample_output_bytes'],
        }
        results.append({'run': str(d.relative_to(r)), 'all_pass': all(checks.values()),
                        'checks': checks, 'output_sha256': digest,
                        'receipt_sha256': hashlib.sha256((d / 'receipt.json').read_bytes()).hexdigest(),
                        'model_executable_sha256': receipt['executable_sha256']})
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'all_pass': all(x['all_pass'] for x in results), 'results': results,
          'native_identity_audit_sha256': hashlib.sha256(prior.read_bytes()).hexdigest(),
          'scope': 'reuse existing ALT native QoR identity only; no new E2/Process time, FPGA clock, shell, board or STRICT equivalence',
          'board_measured': False, 'STRICT_equivalent': False,
          'historical_map_differences': identity['map_differences']}
out.write_text(json.dumps(result, indent=2) + '\n')
print('COMPLETE_MODEL_NATIVE_ALT_IDENTITY', result['all_pass'], len(results))
sys.exit(not result['all_pass'])
