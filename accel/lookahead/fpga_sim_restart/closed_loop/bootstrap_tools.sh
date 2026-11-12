#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../../.." && pwd)
target=$root/results/fpga_sim_restart_20261111T231000Z/tools
mkdir -p "$target"
cd "$target"
# Extract into the isolated run only; do not change system packages.
apt-get download verilator=4.038-1 libtbb12=2021.5.0-7ubuntu2 libtbbmalloc2=2021.5.0-7ubuntu2
dpkg-deb -x verilator_4.038-1_amd64.deb verilator_local
ln -sfn ../../bin/verilator_bin verilator_local/usr/share/verilator/verilator_bin
for package in libtbb12_*.deb libtbbmalloc2_*.deb; do dpkg-deb -x "$package" tbb_local; done
curl -fsSL https://bootstrap.pypa.io/pip/pip.pyz -o pip.pyz
python3 pip.pyz install --target python_plot -r "$root/accel/lookahead/fpga_sim_restart/closed_loop/plot_requirements.txt"
