# Recovery from saved synthesis: same RTL, no vendor patch or global preferences.
set restart_root [file normalize [file join [file dirname [info script]] ../../../..]]
set restart_out $restart_root/results/fpga_sim_restart_20261111T231000Z/ooc_recovery
file mkdir $restart_out
set_param general.maxThreads 4
open_checkpoint $restart_root/results/fpga_sim_restart_20261111T231000Z/ooc_owner/synth.dcp
# Synth DCP was saved with the original 5ns constraints; retain the failed target.
opt_design
place_design
write_checkpoint -force $restart_out/placed.dcp
report_timing_summary -delay_type min_max -report_unconstrained -file $restart_out/placed_timing.rpt
phys_opt_design
route_design
write_checkpoint -force $restart_out/routed.dcp
report_utilization -file $restart_out/utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -max_paths 10 -file $restart_out/timing_200MHz.rpt
report_drc -file $restart_out/drc.rpt
check_timing -verbose -file $restart_out/check_timing.rpt
# Single explicit fallback, not a clock sweep. This does not repair hold failures.
create_clock -period 8.000 -name core [get_ports clk]
report_timing_summary -delay_type min_max -report_unconstrained -max_paths 10 -file $restart_out/timing_125MHz.rpt
write_xdc -force $restart_out/constraints_125MHz.xdc
exit
