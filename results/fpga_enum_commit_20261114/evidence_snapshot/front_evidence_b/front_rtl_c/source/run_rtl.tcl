set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_20261114/front_rtl_c
create_project front_group $out/project -part xcu280-fsvh2892-2L-e -force
add_files $root/accel/lookahead/fpga_sparse_stream/rtl/fp32_positive.sv
add_files $root/accel/lookahead/fpga_enum_commit/front/frontend_group.sv
add_files -fileset sim_1 $root/accel/lookahead/fpga_enum_commit/front/frontend_group_tb.sv
add_files -fileset sim_1 [glob $out/*.hex]
set_property top frontend_group_tb [get_filesets sim_1]
set_property target_simulator XSim [current_project]
set_property xsim.simulate.runtime 200us [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim
