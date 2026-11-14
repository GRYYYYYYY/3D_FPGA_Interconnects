set root [file normalize [file join [file dirname [info script]] ../../../..]]
set src $root/accel/lookahead/fpga_enum_commit/canonical
set out $root/results/fpga_enum_commit_canonical_20261114_f
if {[file exists $out/project]} {error "Existing result project; use a unique result directory"}
create_project canonical_k8 $out/project -part xcu280-fsvh2892-2L-e -force
add_files [list $root/accel/lookahead/fpga_sparse_stream_r2/rtl/pending17_service.sv $src/ec_pending_k8.sv $src/ec_tagged_port.sv $src/ec_canonical_owner.sv]
add_files -fileset sim_1 $out/canonical_tb.sv
set_property top canonical_tb [get_filesets sim_1]
set_property xsim.simulate.runtime 3ms [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim
