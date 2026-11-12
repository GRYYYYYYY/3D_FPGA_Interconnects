#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../../.." && pwd)
src=$root/accel/lookahead/fpga_sim_restart
v=/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin
run=$(realpath "$1"); owners=${2:-8}; latency=${3:-60}
mkdir -p "$run/build"
cd "$run/build"
"$v/xvlog" --sv "$src/rtl/owner_service.sv" "$src/closed_loop/fp32_positive.sv" "$src/closed_loop/graph_control.sv" "$src/closed_loop/graph_top.sv" "$src/closed_loop/graph_tb.sv" >compile.log 2>&1
"$v/xelab" graph_tb -s graph_run --mt 4 -generic_top "OWNERS=$owners" >elaborate.log 2>&1
"$v/xsim" graph_run -runall -testplusarg "DIR=$run" -testplusarg "LATENCY=$latency" -log "$run/simulate.log" >console.log 2>&1
python3 "$src/closed_loop/check.py" "$run"
