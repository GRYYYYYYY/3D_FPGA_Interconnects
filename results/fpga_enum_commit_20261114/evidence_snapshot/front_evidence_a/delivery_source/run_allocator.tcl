set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_20261114/front_allocator_rtl_a
create_project allocator $out/project -part xcu280-fsvh2892-2L-e -force
add_files $root/accel/lookahead/fpga_enum_commit/front/allocator_grouped.sv
add_files -fileset sim_1 $root/accel/lookahead/fpga_enum_commit/front/allocator_tb.sv
set_property top allocator_tb [get_filesets sim_1]
set_property xsim.simulate.runtime 20us [get_filesets sim_1]
launch_simulation
close_sim
