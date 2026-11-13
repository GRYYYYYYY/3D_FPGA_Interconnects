set d [file dirname [info script]]
set_param general.maxThreads 1
open_checkpoint {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/wave_inf_micro_ram_d_5ns_recovery1/placed.dcp}
route_design -directive Quick -timing_summary
report_route_status -file [file join $d route_status.rpt]
report_utilization -hierarchical -file [file join $d routed_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $d routed_timing.rpt]
report_methodology -file [file join $d methodology.rpt]
report_drc -file [file join $d drc.rpt]
write_checkpoint [file join $d routed.dcp]
