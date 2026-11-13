set d [file dirname [info script]]
set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]
set_param general.maxThreads 4
launch_runs synth_1 -jobs 4
wait_on_run synth_1
open_run synth_1
report_utilization -hierarchical -file [file join $d synthesis_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $d synthesis_timing.rpt]
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
open_run impl_1
report_route_status -file [file join $d route_status.rpt]
report_utilization -hierarchical -file [file join $d routed_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $d routed_timing.rpt]
report_methodology -file [file join $d methodology.rpt]
report_drc -file [file join $d drc.rpt]
write_checkpoint [file join $d routed.dcp]
