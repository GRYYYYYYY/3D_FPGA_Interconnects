#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$root"
mkdir -p results/fpga_sim_restart_20261111T231000Z/closed_loop/ooc_64_fixed
FPGA_OOC_SUFFIX=_fixed LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libudev.so.1 \
 /inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado \
 -mode batch -source accel/lookahead/fpga_sim_restart/closed_loop/synth.tcl \
 -tclargs 64 -log results/fpga_sim_restart_20261111T231000Z/closed_loop/ooc_64_fixed/vivado.log \
 -journal results/fpga_sim_restart_20261111T231000Z/closed_loop/ooc_64_fixed/vivado.jou
