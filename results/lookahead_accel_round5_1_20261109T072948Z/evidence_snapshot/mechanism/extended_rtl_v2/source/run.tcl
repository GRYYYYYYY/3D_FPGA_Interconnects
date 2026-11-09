open_project project
set_top lookahead_services51
add_files {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/mechanism/extended_rtl_v2/source/services51.cpp} -cflags {-I/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/mechanism/extended_rtl_v2/source -std=c++14 -pthread -ffp-contract=off -fno-fast-math}
add_files -tb {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/mechanism/extended_rtl_v2/source/tb51.cpp} -cflags {-I/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/mechanism/extended_rtl_v2/source -std=c++14 -pthread -ffp-contract=off -fno-fast-math}
open_solution solution -flow_target vivado
set phase $::env(LA51_PHASE)
if {$phase eq "csim"} {csim_design -ldflags "-pthread"}
if {$phase eq "cosim"} {cosim_design -rtl verilog -tool xsim -trace_level none -ldflags "-pthread" -enable_dataflow_profiling}
exit
