"""Relink a new bounded-memory driver against immutable compiled RTL.

The original RTL/archive and executable are never changed. Bind all reused
artifacts by SHA; this does not resynthesize or replace any hardware logic.
"""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys

root = Path(__file__).resolve().parents[4]
s = root / 'accel/lookahead/fpga_sparse_stream_r2'
r = root / 'results/fpga_sparse_stream_r2_20261112/rtl'
original, version, lanes, ports = sys.argv[1:5]
old, out = r / (original + '_build'), r / (version + '_build')
out.mkdir(exist_ok=False)
source = out / 'source'
shutil.copytree(old / 'source', source)
shutil.copy2(s / 'sim/many_tile_driver.cpp', source / 'many_tile_driver.cpp')
include = root.parent / '3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr/share/verilator/include'
artifacts = [old / 'Vr2_many_tile__ALL.a', old / 'verilated.o', *old.glob('*.h')]
cmd = ['g++', '-O3', '-std=c++17', '-DVM_TRACE=0', '-DVM_COVERAGE=0', '-DVM_SC=0',
       '-DTILE_L=' + lanes, '-DTILE_P=' + ports, '-I' + str(old), '-I' + str(include),
       '-I' + str(include / 'vltstd'), '-I' + str(root / 'accel/lookahead/include'),
       str(source / 'many_tile_driver.cpp'), str(artifacts[0]), str(artifacts[1]),
       '-o', str(out / 'Vr2_many_tile')]
with (out / 'build.log').open('w') as log:
    rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
(out / 'source_binding.json').write_text(json.dumps({
    'command': cmd, 'returncode': rc, 'immutable_RTL_build': str(old),
    'reused_artifact_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
    'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()},
}, indent=2))
print('RELINK', rc, out)
sys.exit(rc)
