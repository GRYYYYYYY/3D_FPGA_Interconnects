#!/usr/bin/env bash
set -euo pipefail
code_root=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$code_root"
# Per-process loader ordering; no vendor-library edits, stubs, or global settings.
# hls4ml issue 81 links AMD AR 000034450 for this exact libudev/realloc signature.
mkdir -p results/fpga_sim_restart_20261111T231000Z/ooc_v2
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libudev.so.1 \
 /inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado \
 -mode batch -source accel/lookahead/fpga_sim_restart/scripts/ooc_v2.tcl \
 -log results/fpga_sim_restart_20261111T231000Z/ooc_v2/vivado.log \
 -journal results/fpga_sim_restart_20261111T231000Z/ooc_v2/vivado.jou
