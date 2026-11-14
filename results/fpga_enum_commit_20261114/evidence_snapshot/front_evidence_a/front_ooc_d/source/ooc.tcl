set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_20261114/front_ooc_d
file mkdir $out
catch {close_project}
create_project -in_memory -part xcu280-fsvh2892-2L-e
read_verilog -sv $root/accel/lookahead/fpga_sparse_stream/rtl/fp32_positive.sv
read_verilog -sv $root/accel/lookahead/fpga_enum_commit/front/frontend_group.sv
set_param general.maxThreads 8
synth_design -mode out_of_context -top frontend_group -part xcu280-fsvh2892-2L-e
create_clock -name core -period 5 [get_ports clk]
set_input_delay -clock core 0.5 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core 0.5 [get_ports -filter {DIRECTION == OUT}]
report_utilization -file $out/util_synth.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file $out/timing_synth.rpt
write_checkpoint -force $out/synth.dcp
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file $out/timing_route.rpt
report_timing -delay_type max -max_paths 10 -file $out/setup_paths.rpt
report_timing -delay_type min -max_paths 10 -file $out/hold_paths.rpt
report_utilization -file $out/util_route.rpt
report_methodology -file $out/methodology.rpt
write_checkpoint -force $out/route.dcp
