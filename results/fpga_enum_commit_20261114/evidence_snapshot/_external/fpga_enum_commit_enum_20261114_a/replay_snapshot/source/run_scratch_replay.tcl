set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_enum_20261114_a
catch {close_project}
create_project scratch_unit $out/scratch_replay_project -part xcu280-fsvh2892-2L-e -force
add_files [list $root/accel/lookahead/fpga_sparse_stream_r2/rtl/inf_scratch_boundary.sv $root/accel/lookahead/fpga_sparse_stream_r2/rtl/sync_fifo.sv $root/accel/lookahead/fpga_enum_commit/enumerator/scratch_finalize.sv]
add_files -fileset sim_1 $root/accel/lookahead/fpga_enum_commit/enumerator/scratch_replay_tb.sv
set_property top scratch_replay_tb [get_filesets sim_1]
set_property xsim.simulate.runtime 1250us [get_filesets sim_1]
launch_simulation
close_sim
