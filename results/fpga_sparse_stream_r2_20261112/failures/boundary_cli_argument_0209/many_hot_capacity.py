"""Exact-capacity and one-over-capacity changed/commit tests on owner zero.

All destinations share a physical port and a finite owner. Both tests use more
than one million node addresses; no full-node state is placed in the RTL.
"""
from pathlib import Path
from array import array
import json, struct, subprocess, sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
variant, model = sys.argv[1:3]
out = r / 'rtl' / (variant + '_hot_capacity8192')
out.mkdir(exist_ok=False)
receipts = []
for count in [8192, 8193]:
    d = out / str(count)
    d.mkdir()
    n = count * 128 + 1
    with (d / 'workload.bin').open('wb') as f:
        f.write(struct.pack('<7Q', 0x31414c5443495254, n, count, 1, 2, 1, 1))
        array('Q', [0] + [count] * n).tofile(f)
        for i in range(n):
            f.write(struct.pack('<IIIi', int(i == n-1), int(i == n-1), 1, -1))
        for i in range(1, count+1):
            f.write(struct.pack('<II', i*128, 0))
        f.write(struct.pack('<4f', 0, 0, 1, 0))
        f.write(struct.pack('<6I', 0, 0, 0, 0, 0, 0))
        array('i', [-1] * (n-1) + [0]).tofile(f)
        f.write(struct.pack('<2I', 0x7fc00000, 0x7fc00000))
    commands = [
        [str(r/'semantics/original_ALT'), str(d/'workload.bin'), str(d/'golden.bin')],
        [str(r/'semantics/reference_pop_reduce'), str(d/'workload.bin'), str(d/'golden.bin'),
         str(d/'pop'), '524288', '524288'],
    ]
    for kind, exe in [('rtl', r/f'rtl/{variant}_build/Vr2_many_tile'),
                      ('model', r/f'model/{model}/model')]:
        commands.append([str(exe), str(d/'workload.bin'), str(d/'pop/prepared.bin'),
                         str(d/'golden.bin'), str(d/kind), '120', '1729', '4'])
    results = []
    for i, command in enumerate(commands):
        with (d/f'run{i}.log').open('w') as log:
            rc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode
        results.append({'command': command, 'returncode': rc})
        if i < 2 and rc:
            raise RuntimeError((d/f'run{i}.log').read_text())
    exact = (d/'rtl/cycles.csv').read_bytes() == (d/'model/cycles.csv').read_bytes()
    if count == 8192:
        passed = all(x['returncode'] == 0 for x in results) and exact
        passed &= (d/'rtl/output.bin').read_bytes() == (d/'model/output.bin').read_bytes() == (d/'golden.bin').read_bytes()
    else:
        passed = exact
        for i, kind in [(2, 'rtl'), (3, 'model')]:
            text = (d/f'run{i}.log').read_text()
            passed &= results[i]['returncode'] != 0 and 'DUT error' in text and 'bank=' in text
            passed &= not (d/kind/'output.bin').exists()
    receipt = {'unique_changes_on_owner0': count, 'node_count': n, 'physical_port_hotspot': 0,
               'capacity_per_owner': 8192, 'cycle_log_exact': exact,
               'expected_result': 'complete' if count == 8192 else 'explicit rejection without output',
               'passed': passed, 'results': results}
    receipts.append(receipt)
    (d/'receipt.json').write_text(json.dumps(receipt, indent=2))
    print(count, passed, flush=True)
    if not passed:
        raise RuntimeError('capacity/RTL-model check failed')
(out/'summary.json').write_text(json.dumps({'all_pass': True, 'results': receipts}, indent=2))
