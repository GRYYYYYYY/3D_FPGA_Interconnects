# Original routed DCP kept unchanged. One predeclared conservative check, no sweep.
create_clock -name ap_clk -period 8.000 -waveform {0.000 4.000} [get_ports ap_clk]
report_timing_summary -file timing_summary.rpt
report_timing -max_paths 10 -file timing_paths.rpt
report_utilization -file utilization.rpt
report_route_status -file route_status.rpt
write_xdc constraints_125mhz.xdc
write_checkpoint design_125mhz.dcp
