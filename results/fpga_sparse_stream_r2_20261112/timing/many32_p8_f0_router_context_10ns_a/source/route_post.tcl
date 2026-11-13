report_utilization -hierarchical -file routed_utilization.rpt
report_ram_utilization -file routed_ram.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file routed_timing.rpt
report_timing -delay_type max -max_paths 20 -file setup_paths.rpt
report_timing -delay_type min -max_paths 20 -file hold_paths.rpt
report_route_status -file route_status.rpt
report_drc -file drc.rpt
check_timing -verbose -file check_timing.rpt
report_methodology -file methodology.rpt
