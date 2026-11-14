set root [file normalize [file join [file dirname [info script]] ../../..]]
set out $root/results/fpga_decoupled_front_20261114/enum_rtl_a
create_project enum_witness $out/project -part xcu280-fsvh2892-2L-e -force
add_files $root/accel/lookahead/fpga_sparse_stream_r2/rtl/inf_flat_bank.sv
add_files -fileset sim_1 $root/accel/lookahead/fpga_decoupled_front/enum_interval_tb.sv
set_property top enum_interval_tb [get_filesets sim_1]
set_property xsim.simulate.runtime 100us [get_filesets sim_1]
launch_simulation
close_sim
