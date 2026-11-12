# Read-only post-route resource/clock audit; no design optimization or rerouting.
set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_sim_restart_20261111T231000Z/closed_loop/ooc_64_fixed
set_param general.maxThreads 4
open_checkpoint $out/routed.dcp
report_utilization -slr -file $out/slr_utilization.rpt
set f [open $out/clock_source_audit.txt w]
puts $f "Vivado [version -short]"
foreach c [get_clocks] {puts $f "CLOCK $c PERIOD [get_property PERIOD $c]"}
puts $f "clk HD.CLK_SRC: [get_property HD.CLK_SRC [get_ports clk]]"
puts $f "OOC has no board/shell clock-source location; an empty HD.CLK_SRC is an integration timing limitation."
close $f
close_design
exit
