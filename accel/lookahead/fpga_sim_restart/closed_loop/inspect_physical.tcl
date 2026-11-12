# Read-only examination of the final route, including paths wholly inside the RTL.
# Added after simulation freeze; no RTL, synthesis, placement, or routing changes.
set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_sim_restart_20261111T231000Z/closed_loop/ooc_64_fixed
set_param general.maxThreads 4
open_checkpoint $out/routed.dcp
report_utilization -slr -file $out/slr_utilization.rpt
set f [open $out/clock_source_audit.txt w]
puts $f "Vivado [version -short]"
foreach c [get_clocks] {puts $f "CLOCK $c PERIOD [get_property PERIOD $c]"}
puts $f "clk HD.CLK_SRC: [get_property HD.CLK_SRC [get_ports clk]]"
set pins 0
foreach p [get_ports] {
    if {[get_property HD.PARTPIN_LOCS $p] ne ""} {incr pins}
}
puts $f "Ports with HD.PARTPIN_LOCS: $pins / [llength [get_ports]]"
puts $f "OOC does not establish board/shell clock-source or boundary routing timing."
close $f
foreach setting {{200 5} {125 8}} {
    lassign $setting mhz period
    create_clock -period $period -name core [get_ports clk]
    report_timing -from [all_registers] -to [all_registers] -delay_type max -max_paths 10 -file $out/internal_setup_${mhz}MHz.rpt
    report_timing -from [all_registers] -to [all_registers] -delay_type min -max_paths 10 -file $out/internal_hold_${mhz}MHz.rpt
}
close_design
exit
