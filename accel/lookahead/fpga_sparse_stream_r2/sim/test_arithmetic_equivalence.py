"""XSim new/legacy RTL lockstep, including numeric failures and backpressure."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys
root = Path(__file__).resolve().parents[4]
s = root / 'accel/lookahead/fpga_sparse_stream_r2'
r = root / 'results/fpga_sparse_stream_r2_20261112'
old = r / 'rtl/many32_bank_tree_a_build/source/fp32_positive.sv'
out = r / 'rtl' / sys.argv[1]
out.mkdir(exist_ok=False)
shutil.copy2(s / 'rtl/fp32_positive.sv', out / 'fp32_positive.sv')
shutil.copy2(s / 'sim/arithmetic_equivalence_tb.sv', out / 'arithmetic_equivalence_tb.sv')
(out / 'legacy.sv').write_text(old.read_text().replace('module pair_lane(', 'module legacy_pair_lane('))
bin = root.parent.parent / 'Xilinx/Vivado/2022.2/bin'
env = os.environ.copy()
env['LD_PRELOAD'] = '/usr/lib/x86_64-linux-gnu/libudev.so.1'
commands = [[str(bin / 'xvlog'), '--sv', 'legacy.sv', 'fp32_positive.sv', 'arithmetic_equivalence_tb.sv'],
            [str(bin / 'xelab'), 'arithmetic_equivalence_tb', '-s', 'arith_equivalence'],
            [str(bin / 'xsim'), 'arith_equivalence', '-runall']]
receipts = []
for i, cmd in enumerate(commands):
    with (out / f'stage{i}.log').open('w') as log:
        rc = subprocess.run(cmd, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    receipts.append({'command': cmd, 'returncode': rc})
    if rc:
        break
passed = len(receipts) == 3 and all(x['returncode'] == 0 for x in receipts) and 'ARITHMETIC_EQUIVALENCE_PASS' in (out / 'stage2.log').read_text()
(out / 'receipt.json').write_text(json.dumps({'all_pass': passed, 'results': receipts,
    'legacy_original': str(old), 'legacy_original_sha256': hashlib.sha256(old.read_bytes()).hexdigest(),
    'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.sv')}}, indent=2) + '\n')
print('ARITHMETIC_EQUIVALENCE', passed)
sys.exit(not passed)
