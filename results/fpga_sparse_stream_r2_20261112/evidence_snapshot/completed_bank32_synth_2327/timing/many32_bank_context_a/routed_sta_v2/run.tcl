wait_on_run impl_1
set r2_sta_run_status [get_property STATUS [get_runs impl_1]]
if {$r2_sta_run_status ne "route_design Complete!" && $r2_sta_run_status ne "route_design Complete, Failed Timing!"} {error "route did not complete: $r2_sta_run_status"}
open_run impl_1
if {[get_property TOP [current_fileset]] ne {r2_many32_context}} {error "wrong project/top"}
report_route_status -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/route_status.rpt}
report_utilization -hierarchical -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/routed_utilization.rpt}
report_ram_utilization -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/routed_ram.rpt}
set r2_sta_fd [open {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/tested_periods.csv} w]
puts $r2_sta_fd "period_ns,setup_slack_ns,hold_slack_ns,qualification"
create_clock -name clk -period 5.000000 [get_ports clk]
report_clocks -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps_clocks.rpt}
report_timing_summary -delay_type min_max -report_unconstrained -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps_timing.rpt}
report_timing -delay_type max -max_paths 20 -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps_setup.rpt}
report_timing -delay_type min -max_paths 20 -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps_hold.rpt}
check_timing -verbose -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps_check_timing.rpt}
report_methodology -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps_methodology.rpt}
report_drc -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps_drc.rpt}
set r2_sta_setup [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]
set r2_sta_hold [get_property SLACK [lindex [get_timing_paths -delay_type min -max_paths 1] 0]]
puts $r2_sta_fd "5.0,$r2_sta_setup,$r2_sta_hold,pending_report_review"
flush $r2_sta_fd
write_checkpoint {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps.dcp}
write_xdc {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p5000ps.xdc}
create_clock -name clk -period 8.000000 [get_ports clk]
report_clocks -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps_clocks.rpt}
report_timing_summary -delay_type min_max -report_unconstrained -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps_timing.rpt}
report_timing -delay_type max -max_paths 20 -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps_setup.rpt}
report_timing -delay_type min -max_paths 20 -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps_hold.rpt}
check_timing -verbose -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps_check_timing.rpt}
report_methodology -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps_methodology.rpt}
report_drc -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps_drc.rpt}
set r2_sta_setup [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]
set r2_sta_hold [get_property SLACK [lindex [get_timing_paths -delay_type min -max_paths 1] 0]]
puts $r2_sta_fd "8.0,$r2_sta_setup,$r2_sta_hold,pending_report_review"
flush $r2_sta_fd
write_checkpoint {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps.dcp}
write_xdc {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p8000ps.xdc}
create_clock -name clk -period 10.000000 [get_ports clk]
report_clocks -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps_clocks.rpt}
report_timing_summary -delay_type min_max -report_unconstrained -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps_timing.rpt}
report_timing -delay_type max -max_paths 20 -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps_setup.rpt}
report_timing -delay_type min -max_paths 20 -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps_hold.rpt}
check_timing -verbose -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps_check_timing.rpt}
report_methodology -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps_methodology.rpt}
report_drc -file {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps_drc.rpt}
set r2_sta_setup [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]
set r2_sta_hold [get_property SLACK [lindex [get_timing_paths -delay_type min -max_paths 1] 0]]
puts $r2_sta_fd "10.0,$r2_sta_setup,$r2_sta_hold,pending_report_review"
flush $r2_sta_fd
write_checkpoint {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps.dcp}
write_xdc {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many32_bank_context_a/routed_sta_v2/p10000ps.xdc}
close $r2_sta_fd
puts R2_ROUTED_STA_COMPLETE_PENDING_REVIEW
