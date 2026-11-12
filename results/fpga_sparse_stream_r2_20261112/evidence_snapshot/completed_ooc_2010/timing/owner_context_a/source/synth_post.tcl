if {[llength [get_clocks]] == 0} {read_xdc [file join [file dirname [info script]] tile_ooc.xdc]}
report_clocks -file synth_clocks.rpt
report_utilization -hierarchical -file synth_utilization.rpt
report_ram_utilization -file ram_utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file synth_timing.rpt
