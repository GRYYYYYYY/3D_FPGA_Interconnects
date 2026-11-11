#!/usr/bin/env bash
set -euo pipefail
code_root=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$code_root"
scripts=accel/lookahead/fpga_sim_restart/scripts
result=results/fpga_sim_restart_20261111T231000Z
bash "$scripts/run_xsim.sh" "$result/real_waves" 60 60
bash "$scripts/run_xsim.sh" "$result/directed_ii1" 600 800
bash "$scripts/run_xsim.sh" "$result/directed_latency60" 60 60
bash "$scripts/run_xsim.sh" "$result/directed_owner64" 600 800 6 65536
bash "$scripts/run_xsim.sh" "$result/real_waves_d4" 60 60
bash "$scripts/run_rejection.sh" "$result/rejection"
