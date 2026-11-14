set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_integration_20261114_a/ooc_b
file mkdir $out
create_project -in_memory -part xcu280-fsvh2892-2L-e
set old $root/accel/lookahead/fpga_sparse_stream_r2/rtl
set ec $root/accel/lookahead/fpga_enum_commit
read_verilog -sv [list $old/sync_fifo.sv $old/inf_flat_bank.sv $old/inf_scratch_boundary.sv $old/pending17_service.sv $ec/enumerator/enum2_bank.sv $ec/enumerator/scratch_finalize.sv $ec/canonical/ec_pending_k8.sv $ec/canonical/ec_tagged_port.sv $ec/integration/ec_backend_owner.sv]
read_xdc $ec/integration/ooc.xdc
set_param general.maxThreads 8
synth_design -top ec_backend_owner -mode out_of_context -part xcu280-fsvh2892-2L-e -generic NEW=1 -flatten_hierarchy rebuilt
write_checkpoint -force $out/post_synth.dcp
report_utilization -file $out/synth_utilization.rpt
report_utilization -hierarchical -file $out/synth_hierarchical_utilization.rpt
opt_design
place_design
phys_opt_design
route_design
write_checkpoint -force $out/post_route.dcp
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 20 -report_unconstrained -file $out/timing_summary.rpt
report_utilization -file $out/utilization.rpt
report_utilization -hierarchical -file $out/hierarchical_utilization.rpt
report_methodology -file $out/methodology.rpt
report_drc -file $out/drc.rpt
report_clock_utilization -file $out/clocks.rpt
