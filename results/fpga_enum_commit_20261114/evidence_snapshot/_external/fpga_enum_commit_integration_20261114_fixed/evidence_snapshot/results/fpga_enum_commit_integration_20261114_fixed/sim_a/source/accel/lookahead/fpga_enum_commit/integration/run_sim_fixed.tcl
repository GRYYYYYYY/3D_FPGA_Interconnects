set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_integration_20261114_fixed
create_project backend_fixed $out/project -part xcu280-fsvh2892-2L-e -force
set old $root/accel/lookahead/fpga_sparse_stream_r2/rtl
set ec $root/accel/lookahead/fpga_enum_commit
add_files [list $old/sync_fifo.sv $old/inf_flat_bank.sv $old/inf_scratch_boundary.sv $old/pending17_service.sv $ec/enumerator/enum2_bank.sv $ec/enumerator/scratch_finalize.sv $ec/canonical/ec_pending_k8.sv $ec/canonical/ec_tagged_port.sv $ec/integration/ec_backend_owner.sv]
add_files -fileset sim_1 $ec/integration/tb_backend.sv
set_property top tb_backend [get_filesets sim_1]
set_property xsim.simulate.runtime 100ms [get_filesets sim_1]
set_property -dict [list xsim.simulate.xsim.more_options "-testplusarg REPLAY_DIR=$root/results/fpga_enum_commit_integration_20261114_a/fixtures -testplusarg FIXED_LATENCY"] [get_filesets sim_1]
launch_simulation
close_sim
