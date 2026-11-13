"""Replay a completed node-state unit run with its exact compile parameters."""
from pathlib import Path
import hashlib, json, shlex, shutil, subprocess, sys

root = Path(__file__).resolve().parents[4]
s = root / 'accel/lookahead/fpga_sparse_stream_r2'
r = root / 'results/fpga_sparse_stream_r2_20261112/large_state'
rtl, name = sys.argv[1:3]
ref = r / rtl
receipt = json.loads((ref / 'receipt.json').read_text())
assert receipt['returncode'] == 0
cmd = receipt['build_command']
flags = shlex.split(cmd[cmd.index('-CFLAGS') + 1])
stage = next((int(x.split('=')[1]) for x in cmd if x.startswith('-GREQUEST_STAGE=')), 0)
assert stage in [0, 1]
assert 'REGISTERED_READY=1' in (ref / 'source/sync_fifo.sv').read_text()
out = r / name
out.mkdir(exist_ok=False)
f = out / 'source'
f.mkdir()
shutil.copy2(ref / 'source/node_state_driver.cpp', f / 'node_state_driver.cpp')
shutil.copy2(s / 'node_state_model.hpp', f / 'node_state_model.hpp')
shutil.copy2(s / 'owner_primitives_model.hpp', f / 'owner_model.hpp')
p = f / 'node_state_model.hpp'
p.write_text(p.read_text().replace('../fpga_sparse_stream/owner_model.hpp', 'owner_model.hpp'))
p = f / 'node_state_driver.cpp'
p.write_text(p.read_text().replace('#include "Vr2_node_state.h"\n#include "verilated.h"',
    '#include "node_state_model.hpp"\nusing Vr2_node_state=r2_model::NodeStateCycle;')
    .replace('Verilated::commandArgs(argc,argv);', ''))
command = ['g++', *flags, '-DINDEPENDENT_STATE_MODEL=1', '-DR2_REGISTERED_READY=1',
           *(['-DR2_REQUEST_STAGE=1'] if stage else []), str(p), '-o', str(out / 'model')]
with (out / 'build.log').open('w') as log:
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
with (out / 'run.log').open('w') as log:
    rc = subprocess.run([str(out / 'model'), str(out / 'cycles.csv')],
                        stdout=log, stderr=subprocess.STDOUT).returncode
exact = (out / 'cycles.csv').read_bytes() == (ref / 'cycles.csv').read_bytes()
result = {'scope': 'node-state finite4M backing, immutable nonzero batch base; all output records and full backing checked by independent scoreboard',
          'RTL_reference': rtl, 'returncode': rc, 'cycle_log_exact': exact,
          'all_pass': rc == 0 and exact, 'command': command,
          'reference_receipt_sha256': hashlib.sha256((ref / 'receipt.json').read_bytes()).hexdigest(),
          'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in f.iterdir()}}
(out / 'calibration.json').write_text(json.dumps(result, indent=2) + '\n')
print((out / 'run.log').read_text(), 'NODE_STATE_INDEPENDENT_EXACT', exact)
sys.exit(not result['all_pass'])
