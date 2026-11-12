"""Compare every cycle, full outputs and all reported traffic to a frozen RTL suite."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
variant, rtl = sys.argv[1:3]
d = r / 'model' / variant
out = d / (sys.argv[3] if len(sys.argv) > 3 else 'suite_calibration')
expected = int(sys.argv[4]) if len(sys.argv) > 4 else 97
references = []
for suffix in ['native_l60', 'fixtures_l60', 'stress,stress_random_l120',
               'external_nodes_65536,external_nodes_4194304_l60']:
    references.extend((r / 'rtl').glob(f'{rtl}_{suffix}/*/receipt.json'))
if len(references) != expected:
    raise RuntimeError(f'RTL suite incomplete: {len(references)} receipts, expected {expected}')
if any(json.loads(p.read_text())['returncode'] != 0 for p in references):
    raise RuntimeError('RTL suite contains failed reference executions')
out.mkdir(exist_ok=False)

def run(receipt):
    ref = json.loads(receipt.read_text())
    old = receipt.parent
    name = old.parent.name + '__' + old.name
    o = out / name
    o.mkdir()
    cmd = ref['command'].copy()
    cmd[0], cmd[4] = str(d / 'model'), str(o)
    with (o / 'console.log').open('w') as log:
        rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
    exact = (o / 'cycles.csv').exists() and (o / 'cycles.csv').read_bytes() == (old / 'cycles.csv').read_bytes()
    outputs = (o / 'output.bin').exists() and (o / 'output.bin').read_bytes() == (old / 'output.bin').read_bytes()
    summary_exact = False
    if (o / 'summary.json').exists():
        actual, reference = [json.loads((p / 'summary.json').read_text()) for p in [o, old]]
        for item in [actual, reference]:
            item.pop('scope', None)
        summary_exact = actual == reference
    result = {'case': name, 'command': cmd, 'returncode': rc,
              'cycle_log_exact': exact, 'outputs_exact': outputs,
              'all_traffic_histogram_phase_summary_exact': summary_exact,
              'reference': str(receipt)}
    (o / 'receipt.json').write_text(json.dumps(result, indent=2))
    print(name, rc, exact, summary_exact, flush=True)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(run, references))
passed = all(x['returncode'] == 0 and x['cycle_log_exact'] and x['outputs_exact']
             and x['all_traffic_histogram_phase_summary_exact'] for x in results)
(out / 'calibration.json').write_text(json.dumps({
    'scope': 'frozen complete topology, latency, backpressure and capacities in receipts; no extrapolation',
    'expected_cases': expected, 'all_pass': passed, 'results': results,
    'model_executable_sha256': hashlib.sha256((d / 'model').read_bytes()).hexdigest(),
}, indent=2))
sys.exit(not passed)
