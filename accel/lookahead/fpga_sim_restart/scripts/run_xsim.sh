#!/usr/bin/env bash
set -euo pipefail
# Standalone 2022.2 fallback/reproduction, same source and testbench as MCP project.
code_root=$(cd "$(dirname "$0")/../../../.." && pwd)
vivado_bin=${VIVADO_BIN:-/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin}
run_dir=$(realpath "$1")
read_cycles=${2:-60}
write_cycles=${3:-60}
owner_bits=${4:-0}
lines=${5:-2048}
mkdir -p "$run_dir/build"
cd "$run_dir/build"
"$vivado_bin/xvlog" --sv "$code_root/accel/lookahead/fpga_sim_restart/rtl/owner_service.sv" "$code_root/accel/lookahead/fpga_sim_restart/tb/owner_tb.sv" > compile.log 2>&1
"$vivado_bin/xelab" owner_tb -s owner_tb_run --mt 4 -generic_top "OWNER_BITS=$owner_bits" -generic_top "N=$lines" > elaborate.log 2>&1
"$vivado_bin/xsim" owner_tb_run -runall -testplusarg "DIR=$run_dir" -testplusarg "READ_CYCLES=$read_cycles" -testplusarg "WRITE_CYCLES=$write_cycles" -log "$run_dir/simulate.log" > console.log 2>&1
python3 "$code_root/accel/lookahead/fpga_sim_restart/scripts/check_rtl.py" "$run_dir"
