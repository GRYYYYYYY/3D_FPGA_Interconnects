"""Independent RTL/model calibration at explicitly hypothetical fixed ns memory.

Kernel periods are sensitivity assumptions, not OOC-qualified operating clocks.
Every request/response and all output are evaluated with the same seeded TB.
"""
from pathlib import Path
import concurrent.futures, hashlib, itertools, json, os, subprocess, sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
rtl, model = sys.argv[1:3]
out = r / 'rtl' / (rtl + '_fixed_time')
out.mkdir(exist_ok=False)
native = json.loads((r / 'semantics/native_complete.json').read_text())[:2]
cases = list(itertools.product(native, [5000, 8000], [80000, 300000, 600000], [5000, 10000, 20000]))

def run(case):
    item, period, latency, gap = case
    c = item['command']
    name = Path(c[3]).name + f'_p{period}_l{latency}_g{gap}'
    d = out / name
    d.mkdir()
    env = os.environ.copy()
    env.update(R2_KERNEL_PERIOD_PS=str(period), R2_MEMORY_BASE_PS=str(latency),
               R2_MEMORY_GAP_PS=str(gap), R2_MEMORY_JITTER_STEP_PS='5000')
    receipts = []
    for kind, exe in [('rtl', r / 'rtl' / (rtl + '_build') / 'Vr2_many_tile'),
                      ('model', r / 'model' / model / 'model')]:
        target = d / kind
        target.mkdir()
        cmd = [str(exe), c[1], str(Path(c[3]) / 'prepared.bin'), c[2], str(target), '60', '1729', '2']
        with (target / 'console.log').open('w') as log:
            rc = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        receipts.append({'command': cmd, 'returncode': rc, 'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest()})
    exact = all(x['returncode'] == 0 for x in receipts)
    for file in ['cycles.csv', 'output.bin', 'physical_time_contract.json']:
        exact &= (d / 'rtl' / file).exists() and (d / 'model' / file).exists()
        if exact:
            exact &= (d / 'rtl' / file).read_bytes() == (d / 'model' / file).read_bytes()
    if exact:
        summaries = [json.loads((d / kind / 'summary.json').read_text()) for kind in ['rtl', 'model']]
        for x in summaries:
            x.pop('scope', None)
        exact &= summaries[0] == summaries[1]
    receipt = {'case': name, 'all_pass': bool(exact), 'results': receipts,
               'physical_time_env': {k: v for k, v in env.items() if k.startswith('R2_')},
               'scope': 'hypothetical frequency and memory; synchronous integer-cycle ports; no CDC/board qualification'}
    (d / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    print(name, exact, flush=True)
    return receipt

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(run, cases))
passed = all(x['all_pass'] for x in results)
(out / 'calibration.json').write_text(json.dumps({'all_pass': passed, 'cases': len(results), 'results': results}, indent=2))
sys.exit(not passed)
