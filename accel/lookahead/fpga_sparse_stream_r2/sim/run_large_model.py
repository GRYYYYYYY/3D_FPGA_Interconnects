"""Complete native resident batches; no sample loop or sampled work in the host.

The DUT's finite job controller executes all 40 samples after one start.
Compact trace suppresses text rows only; every clock, response and counter is
still evaluated. Phase/commit logs, per-cycle digest and full output are saved.
No frequency or board performance is inferred by this runner.
"""
from pathlib import Path
import concurrent.futures, hashlib, json, os, subprocess, sys, time

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
version = sys.argv[1]
latency = sys.argv[2] if len(sys.argv) > 2 else '60'
gap = sys.argv[3] if len(sys.argv) > 3 else '2'
physical = dict(zip(['R2_KERNEL_PERIOD_PS', 'R2_MEMORY_BASE_PS', 'R2_MEMORY_GAP_PS'], sys.argv[4:7]))
if physical and (len(physical) != 3 or any(int(x) <= 0 for x in physical.values())):
    raise ValueError('fixed physical time requires positive period_ps base_ps gap_ps')
exe = r / 'model' / version / 'model'
tag = ('large_ps' + '_'.join(physical.values())) if physical else ('large_l' + latency + '_g' + gap)
out = r / 'model' / version / tag
out.mkdir(exist_ok=False)
env = os.environ.copy()
env.update(R2_MAX_CYCLES='5000000000', R2_COMPACT_TRACE='1')
env.update(physical)
items = json.loads((r / 'semantics/native_complete.json').read_text())[2:]

def run(item):
    c = item['command']
    name = Path(c[3]).name
    d = out / name
    d.mkdir()
    cmd = [str(exe), c[1], str(r / 'semantics/large_prepared' / (name + '.bin')),
           c[2], str(d), latency, '1729', gap]
    receipt = {'command': cmd, 'status': 'running', 'whole_native_batch': True,
               'scope': 'exact cycle architecture model; hypothetical physical memory; no qualified clock',
               'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
               'workload_sha256': item['workload_sha256'],
               'golden_sha256': item['golden_sha256'],
               'env': {k: v for k, v in env.items() if k.startswith('R2_')},
               'started_unix': time.time()}
    with (d / 'console.log').open('w') as log:
        p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        receipt['pid'] = p.pid
        (d / 'receipt.json').write_text(json.dumps(receipt, indent=2))
        rc = p.wait()
    receipt.update(returncode=rc, status='passed' if rc == 0 else 'failed',
                   ended_unix=time.time())
    if rc == 0:
        receipt['output_sha256'] = hashlib.sha256((d / 'output.bin').read_bytes()).hexdigest()
        if receipt['output_sha256'] != receipt['golden_sha256']:
            receipt['status'] = 'failed_output_hash'
    (d / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    print(name, receipt['status'], flush=True)
    return receipt

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    receipts = list(pool.map(run, items))
passed = all(x['status'] == 'passed' for x in receipts)
(out / 'receipts.json').write_text(json.dumps({'all_pass': passed, 'results': receipts}, indent=2))
sys.exit(not passed)
