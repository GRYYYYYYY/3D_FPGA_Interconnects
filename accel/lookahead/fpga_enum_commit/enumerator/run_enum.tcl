set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_enum_20261114_a
catch {close_project}
create_project enum_unit $out/enum_project_e -part xcu280-fsvh2892-2L-e -force
add_files [list $root/accel/lookahead/fpga_sparse_stream_r2/rtl/inf_flat_bank.sv $root/accel/lookahead/fpga_sparse_stream_r2/rtl/sync_fifo.sv $root/accel/lookahead/fpga_enum_commit/enumerator/enum2_bank.sv]
add_files -fileset sim_1 $root/accel/lookahead/fpga_enum_commit/enumerator/enum_tb.sv
set_property top enum_tb [get_filesets sim_1]
set_property xsim.simulate.runtime 150us [get_filesets sim_1]
launch_simulation
close_sim
