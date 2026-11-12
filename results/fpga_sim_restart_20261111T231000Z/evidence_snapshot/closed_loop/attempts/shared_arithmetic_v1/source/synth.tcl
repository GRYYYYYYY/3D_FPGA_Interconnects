set root [file normalize [file join [file dirname [info script]] ../../../..]]
set owners [lindex $argv 0]
if {$owners ni {8 64}} {error {owners must be 8 or 64}}
set suffix ""
if {[info exists ::env(FPGA_OOC_SUFFIX)]} {set suffix $::env(FPGA_OOC_SUFFIX)}
set out $root/results/fpga_sim_restart_20261111T231000Z/closed_loop/ooc_${owners}${suffix}
file mkdir $out
create_project -in_memory -part xcu280-fsvh2892-2L-e
set_param general.maxThreads 4
foreach f [list rtl/owner_service.sv closed_loop/fp32_positive.sv closed_loop/graph_control.sv closed_loop/graph_top.sv] {read_verilog -sv $root/accel/lookahead/fpga_sim_restart/$f}
synth_design -top graph_top -part xcu280-fsvh2892-2L-e -mode out_of_context -generic OWNERS=$owners -flatten_hierarchy rebuilt
create_clock -period 5 -name core [get_ports clk]
set_clock_uncertainty 0.1 [get_clocks core]
set_input_delay -clock core -max 0.5 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock core -min 0.0 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core -max 0.5 [all_outputs]
set_output_delay -clock core -min 0.0 [all_outputs]
write_xdc -force $out/constraints.xdc
report_utilization -hierarchical -file $out/synth_utilization.rpt
write_checkpoint -force $out/synth.dcp
opt_design
place_design
phys_opt_design
route_design
report_utilization -hierarchical -file $out/routed_utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -max_paths 10 -file $out/timing.rpt
report_drc -file $out/drc.rpt
check_timing -verbose -file $out/check_timing.rpt
report_route_status -file $out/route_status.rpt
write_checkpoint -force $out/routed.dcp
create_clock -period 8 -name core [get_ports clk]
report_timing_summary -delay_type min_max -report_unconstrained -max_paths 10 -file $out/timing_125MHz.rpt
exit
