set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_integration_20261114_ooc_c/physopt_a
file mkdir $out
# The live design is the completedC routed checkpoint. Supported2022.2
# directive includes critical fanout/placement/routing and aggressive hold buffers;
# it does NOT request retiming or extra pipeline cycles.
phys_opt_design -directive ExploreWithAggressiveHoldFix
write_checkpoint -force $out/post_physopt.dcp
route_design
write_checkpoint -force $out/post_route.dcp
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 20 -report_unconstrained -file $out/timing_summary.rpt
report_utilization -file $out/utilization.rpt
report_utilization -hierarchical -file $out/hierarchical_utilization.rpt
report_methodology -file $out/methodology.rpt
report_drc -file $out/drc.rpt
report_route_status -file $out/route_status.rpt
check_timing -verbose -file $out/check_timing.rpt
write_xdc -force $out/effective_constraints.xdc
