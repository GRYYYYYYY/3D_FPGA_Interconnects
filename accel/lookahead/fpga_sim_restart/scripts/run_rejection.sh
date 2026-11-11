#!/usr/bin/env bash
set -euo pipefail
code_root=$(cd "$(dirname "$0")/../../../.." && pwd)
vivado_bin=${VIVADO_BIN:-/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin}
mkdir -p "$1"
cd "$1"
"$vivado_bin/xvlog" --sv "$code_root/accel/lookahead/fpga_sim_restart/rtl/owner_service.sv" "$code_root/accel/lookahead/fpga_sim_restart/tb/rejection_tb.sv" > compile.log 2>&1
"$vivado_bin/xelab" rejection_tb -s rejection --mt 4 > elaborate.log 2>&1
"$vivado_bin/xsim" rejection -runall -log simulate.log > console.log 2>&1
python3 - <<'PY'
from pathlib import Path
s=Path('simulate.log').read_text()
assert 'TEST_PASS numeric rejection' in s and 'Fatal:' not in s
print('PASS five invalid numeric domains; no successful fence')
PY
