set d [file dirname [info script]]
set_param general.maxThreads 4
read_verilog -sv [glob [file join $d source *.sv]]
read_xdc [file join $d constraints.xdc]
synth_design -mode out_of_context -top inf_combo_owner -part xcu280-fsvh2892-2L-e
report_utilization -hierarchical -file [file join $d synthesized_utilization.rpt]
write_checkpoint [file join $d synthesized.dcp]
opt_design
place_design
write_checkpoint [file join $d placed.dcp]
route_design
report_route_status -file [file join $d route_status.rpt]
report_utilization -hierarchical -file [file join $d routed_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $d timing.rpt]
report_timing -delay_type max -max_paths 10 -file [file join $d setup_paths.rpt]
report_timing -delay_type min -max_paths 10 -file [file join $d hold_paths.rpt]
check_timing -verbose -file [file join $d check_timing.rpt]
report_methodology -file [file join $d methodology.rpt]
report_drc -file [file join $d drc.rpt]
write_checkpoint [file join $d routed.dcp]
puts INF_COMBO_OOC_COMPLETE
