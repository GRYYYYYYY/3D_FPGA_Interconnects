set d [file dirname [info script]]
set_param general.maxThreads 4
read_verilog -sv [file join $d source wave_inf_bank.sv]
synth_design -top wave_inf_owner -part xcu280-fsvh2892-2L-e -mode out_of_context
create_clock -name clk -period 5.000 [get_ports clk]
report_utilization -hierarchical -file [file join $d synthesis_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $d synthesis_timing.rpt]
write_checkpoint [file join $d synthesized.dcp]
opt_design
place_design
phys_opt_design
route_design
report_route_status -file [file join $d route_status.rpt]
report_utilization -hierarchical -file [file join $d routed_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $d routed_timing.rpt]
report_methodology -file [file join $d methodology.rpt]
report_drc -file [file join $d drc.rpt]
write_checkpoint [file join $d routed.dcp]
