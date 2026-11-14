source [file join [file dirname [info script]] setup.tcl]
set out $root/results/fpga_descriptor_front_20261114/backend/sim_ops_b
file mkdir $out
file mkdir $out/fixtures
foreach p [glob $root/results/fpga_descriptor_front_20261114/backend/fixtures/*.hex] {file copy $p $out/fixtures}
file copy $root/results/fpga_descriptor_front_20261114/backend/fixtures/cases.txt $out/fixtures
create_project context_sim $out/project -part xcu280-fsvh2892-2L-e
add_files $sources
add_files -fileset sim_1 $here/tb_context_ops_stages.sv
set_property top tb_context_ops [get_filesets sim_1]
set_property xsim.simulate.runtime 100ms [get_filesets sim_1]
set_property -dict [list xsim.simulate.xsim.more_options "-testplusarg REPLAY_DIR=$out/fixtures"] [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim
