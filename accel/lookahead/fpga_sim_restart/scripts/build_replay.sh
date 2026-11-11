#!/usr/bin/env bash
set -euo pipefail
code_root=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$code_root"
result=results/fpga_sim_restart_20261111T231000Z
mkdir -p "$result"
for target in cache_replay real_wave; do
 g++ -O3 -std=c++17 -ffp-contract=off -fno-fast-math \
  -Iaccel/lookahead/round6_1 -Iaccel/lookahead/include \
  "accel/lookahead/fpga_sim_restart/scripts/$target.cpp" -o "$result/$target"
done
