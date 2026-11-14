set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_integration_20261114_port_stress
create_project port_stress $out/project -part xcu280-fsvh2892-2L-e -force
add_files $root/accel/lookahead/fpga_enum_commit/canonical/ec_tagged_port.sv
add_files -fileset sim_1 $root/accel/lookahead/fpga_enum_commit/integration/tb_port_stress.sv
set_property top tb_port_stress [get_filesets sim_1]
set_property -dict [list xsim.simulate.xsim.more_options "-testplusarg REPLAY_DIR=$out"] [get_filesets sim_1]
set_property xsim.simulate.runtime 100us [get_filesets sim_1]
launch_simulation
close_sim
