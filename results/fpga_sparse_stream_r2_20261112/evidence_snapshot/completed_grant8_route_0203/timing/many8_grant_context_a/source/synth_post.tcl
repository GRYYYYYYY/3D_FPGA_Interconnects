if {[llength [get_clocks]]==0} {read_xdc {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many8_grant_context_a/source/tile_ooc.xdc}}
report_clocks -file synth_clocks.rpt
report_utilization -hierarchical -file synth_utilization.rpt
report_ram_utilization -file ram_utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file synth_timing.rpt
