set src [lindex $argv 0]
set out [lindex $argv 1]
set top [lindex $argv 2]
file mkdir $out
set_param general.maxThreads 8
read_verilog -sv [glob $src/rtl/*.sv]
synth_design -top $top -part xcu280-fsvh2892-2L-e -mode out_of_context
create_clock -name clk -period 5 [get_ports clk]
set_input_delay -clock clk -max 0.5 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock clk -min 0.1 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock clk -max 0.5 [get_ports -filter {DIRECTION == OUT}]
set_output_delay -clock clk -min 0.1 [get_ports -filter {DIRECTION == OUT}]
report_utilization -hierarchical -file $out/synth_utilization.rpt
report_ram_utilization -file $out/ram_utilization.rpt
write_checkpoint -force $out/synth.dcp
opt_design
place_design
phys_opt_design
route_design
report_utilization -hierarchical -file $out/routed_utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file $out/timing_200.rpt
report_timing -delay_type max -max_paths 10 -file $out/setup_paths.rpt
report_timing -delay_type min -max_paths 10 -file $out/hold_paths.rpt
report_route_status -file $out/route_status.rpt
report_drc -file $out/drc.rpt
check_timing -verbose -file $out/check_timing.rpt
write_checkpoint -force $out/routed.dcp
exit
