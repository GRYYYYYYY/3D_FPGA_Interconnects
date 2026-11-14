source [file join [file dirname [info script]] setup.tcl]
set out $root/results/fpga_descriptor_front_20261114/backend/ooc_a
file mkdir $out
create_project -in_memory -part xcu280-fsvh2892-2L-e
read_verilog -sv $sources
read_xdc $here/context.xdc
set_param general.maxThreads 8
synth_design -top df_backend_context -mode out_of_context -part xcu280-fsvh2892-2L-e -flatten_hierarchy rebuilt
write_checkpoint -force $out/post_synth.dcp
report_utilization -file $out/synth_utilization.rpt
report_utilization -hierarchical -file $out/synth_hierarchical_utilization.rpt
opt_design
write_checkpoint -force $out/post_opt.dcp
place_design
write_checkpoint -force $out/post_place.dcp
phys_opt_design
write_checkpoint -force $out/post_physopt.dcp
route_design
write_checkpoint -force $out/post_route.dcp
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 20 -report_unconstrained -file $out/timing_summary.rpt
report_utilization -file $out/utilization.rpt
report_utilization -hierarchical -file $out/hierarchical_utilization.rpt
report_methodology -file $out/methodology.rpt
report_drc -file $out/drc.rpt
report_clock_utilization -file $out/clocks.rpt
report_route_status -file $out/route_status.rpt
check_timing -verbose -file $out/check_timing.rpt
write_xdc -force $out/effective_constraints.xdc
