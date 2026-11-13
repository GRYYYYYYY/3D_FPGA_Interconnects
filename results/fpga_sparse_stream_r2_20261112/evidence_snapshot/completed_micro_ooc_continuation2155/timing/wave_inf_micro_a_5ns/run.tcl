set d [file dirname [info script]]
create_project wave_inf_micro [file join $d project] -part xcu280-fsvh2892-2L-e
add_files [file join $d source wave_inf_bank.sv]
add_files -fileset constrs_1 [file join $d clock.xdc]
set_property top wave_inf_owner [current_fileset]
set_property STEPS.SYNTH_DESIGN.ARGS.MODE out_of_context [get_runs synth_1]
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
