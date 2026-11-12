# Read-only reports on the completed route. 125 MHz is a constraint recheck,
# not a second place/route, and does not rescale architecture simulation cycles.
set out [lindex $argv 0]
set_param general.maxThreads 8
open_checkpoint $out/routed.dcp
report_utilization -file $out/utilization_flat.rpt
report_timing -delay_type max -from [all_registers] -to [all_registers] -max_paths 10 -file $out/internal_setup_200.rpt
report_timing -delay_type min -from [all_registers] -to [all_registers] -max_paths 10 -file $out/internal_hold_200.rpt
report_high_fanout_nets -max_nets 20 -file $out/high_fanout.rpt
set f [open $out/timing_metrics.tsv w]
puts $f "period_ns\tsetup_wns_ns\thold_whs_ns"
foreach period {5 8} {
    if {$period == 8} {
        create_clock -name clk -period 8 [get_ports clk]
        report_timing_summary -delay_type min_max -report_unconstrained -file $out/timing_125_same_route.rpt
        report_timing -delay_type max -from [all_registers] -to [all_registers] -max_paths 10 -file $out/internal_setup_125_same_route.rpt
        report_timing -delay_type min -from [all_registers] -to [all_registers] -max_paths 10 -file $out/internal_hold_125_same_route.rpt
    }
    set setup [get_timing_paths -delay_type max -max_paths 1]
    set hold [get_timing_paths -delay_type min -max_paths 1]
    if {[llength $setup] == 0 || [llength $hold] == 0} {error "missing timed paths"}
    puts $f "$period\t[get_property SLACK $setup]\t[get_property SLACK $hold]"
}
close $f
close_design
exit
