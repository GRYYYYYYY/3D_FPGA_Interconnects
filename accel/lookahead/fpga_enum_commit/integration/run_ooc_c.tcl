set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_integration_20261114_ooc_c
set recovered $root/results/fpga_enum_commit_integration_20261114_a/ooc_b/post_synth.dcp
set_param general.maxThreads 8
open_checkpoint $recovered
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 10 -report_unconstrained -file $out/synth_timing_summary.rpt
opt_design
write_checkpoint -force $out/post_opt.dcp
place_design
write_checkpoint -force $out/post_place.dcp
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 10 -report_unconstrained -file $out/place_timing_summary.rpt
phys_opt_design
write_checkpoint -force $out/post_physopt.dcp
route_design
write_checkpoint -force $out/post_route.dcp
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 20 -report_unconstrained -file $out/timing_summary.rpt
report_utilization -file $out/utilization.rpt
report_utilization -hierarchical -file $out/hierarchical_utilization.rpt
report_methodology -file $out/methodology.rpt
report_drc -file $out/drc.rpt
report_route_status -file $out/route_status.rpt
report_clock_utilization -file $out/clocks.rpt
check_timing -verbose -file $out/check_timing.rpt
write_xdc -force $out/effective_constraints.xdc
