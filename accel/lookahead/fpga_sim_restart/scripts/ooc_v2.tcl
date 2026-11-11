set restart_root [file normalize [file join [file dirname [info script]] ../../../..]]
set restart_out $restart_root/results/fpga_sim_restart_20261111T231000Z/ooc_v2
file mkdir $restart_out
catch {close_sim -force}
if {[llength [get_projects]]} {close_project}
create_project -in_memory -part xcu280-fsvh2892-2L-e
set_param general.maxThreads 4
read_verilog -sv $restart_root/accel/lookahead/fpga_sim_restart/rtl/owner_service.sv
synth_design -top owner_service -part xcu280-fsvh2892-2L-e -mode out_of_context
create_clock -period 5.000 -name core [get_ports clk]
set_clock_uncertainty 0.100 [get_clocks core]
set_input_delay -clock core -max 0.500 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock core -min 0.000 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core -max 0.500 [all_outputs]
set_output_delay -clock core -min 0.000 [all_outputs]
write_xdc -force $restart_out/constraints.xdc
report_utilization -hierarchical -file $restart_out/synth_utilization.rpt
write_checkpoint -force $restart_out/synth.dcp
opt_design
place_design
write_checkpoint -force $restart_out/placed.dcp
phys_opt_design
route_design
report_utilization -hierarchical -file $restart_out/routed_utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -max_paths 10 -file $restart_out/timing.rpt
report_drc -file $restart_out/drc.rpt
check_timing -verbose -file $restart_out/check_timing.rpt
write_checkpoint -force $restart_out/routed.dcp

# One declared fallback on the same route; retain original timing failures.
create_clock -period 8.000 -name core [get_ports clk]
report_timing_summary -delay_type min_max -report_unconstrained -max_paths 10 -file $restart_out/timing_125MHz.rpt
report_timing -delay_type max -from [all_registers] -to [all_registers] -max_paths 10 -file $restart_out/internal_setup_125MHz.rpt
report_timing -delay_type min -from [all_registers] -to [all_registers] -max_paths 10 -file $restart_out/internal_hold_125MHz.rpt
report_route_status -file $restart_out/route_status.rpt
write_xdc -force $restart_out/constraints_125MHz.xdc
exit
