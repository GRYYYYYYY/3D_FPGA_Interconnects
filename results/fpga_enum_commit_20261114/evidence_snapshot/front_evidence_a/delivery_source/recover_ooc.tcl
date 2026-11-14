set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_20261114/front_ooc_e
file mkdir $out
set_param general.maxThreads 8
open_checkpoint $root/results/fpga_enum_commit_20261114/front_ooc_d/synth.dcp
report_clocks -file $out/clocks.rpt
write_checkpoint -force $out/input_synth.dcp
opt_design
write_checkpoint -force $out/opt.dcp
place_design
write_checkpoint -force $out/place.dcp
phys_opt_design
write_checkpoint -force $out/physopt.dcp
route_design
write_checkpoint -force $out/route.dcp
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file $out/timing_route.rpt
report_timing -delay_type max -max_paths 10 -file $out/setup_paths.rpt
report_timing -delay_type min -max_paths 10 -file $out/hold_paths.rpt
report_utilization -file $out/util_route.rpt
report_methodology -file $out/methodology.rpt
report_drc -file $out/drc.rpt
redirect -file $out/check_timing.rpt {check_timing -verbose}
write_xdc -force -exclude_physical $out/constraints.xdc
puts FRONT_OOC_E_COMPLETE
