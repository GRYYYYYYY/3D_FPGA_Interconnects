set restart_root [file normalize [file join [file dirname [info script]] ../../../..]]
set restart_out $restart_root/results/fpga_sim_restart_20261111T231000Z/ooc_recovery
open_checkpoint $restart_out/routed.dcp
create_clock -period 8.000 -name core [get_ports clk]
report_timing -delay_type max -from [all_registers] -to [all_registers] -max_paths 10 -file $restart_out/internal_setup_125MHz.rpt
report_timing -delay_type min -from [all_registers] -to [all_registers] -max_paths 10 -file $restart_out/internal_hold_125MHz.rpt
report_route_status -file $restart_out/route_status.rpt
exit
