#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../../.." && pwd)
result=$root/results/fpga_sim_restart_20261111T231000Z
owners=${1:-8}
export VERILATOR_ROOT=$result/tools/verilator_local/usr/share/verilator
v=$result/tools/verilator_local/usr/bin/verilator
src=$root/accel/lookahead/fpga_sim_restart
build=$result/closed_loop/verilator_${owners}${2:-}
mkdir -p "$build"
"$v" --cc --exe --build -j 4 --top-module graph_top -GOWNERS="$owners" --Mdir "$build" -Wno-fatal -O3 -CFLAGS '-O3 -std=c++17' "$src/rtl/owner_service.sv" "$src/closed_loop/fp32_positive.sv" "$src/closed_loop/graph_control.sv" "$src/closed_loop/graph_top.sv" "$src/closed_loop/graph_driver.cpp" > "$build/build.log" 2>&1
