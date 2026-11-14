source [file join [file dirname [info script]] setup.tcl]
set out $root/results/fpga_descriptor_front_20261114/backend/sim_b
file mkdir $out
create_project context_sim $out/project -part xcu280-fsvh2892-2L-e
add_files $sources
add_files -fileset sim_1 $here/tb_backend_context.sv
set_property top tb_backend_context [get_filesets sim_1]
set_property xsim.simulate.runtime 100ms [get_filesets sim_1]
set_property -dict [list xsim.simulate.xsim.more_options "-testplusarg REPLAY_DIR=$root/results/fpga_descriptor_front_20261114/backend/fixtures -testplusarg FIXED_LATENCY"] [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim
