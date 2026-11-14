set root [file normalize [file join [file dirname [info script]] ../../../..]]
open_project $root/results/fpga_enum_commit_integration_20261114_fixed/project/backend_fixed.xpr
set_property -dict [list xsim.simulate.xsim.more_options "-testplusarg REPLAY_DIR=$root/results/fpga_enum_commit_integration_20261114_a/fixtures -testplusarg FIXED_LATENCY"] [get_filesets sim_1]
launch_simulation
close_sim
