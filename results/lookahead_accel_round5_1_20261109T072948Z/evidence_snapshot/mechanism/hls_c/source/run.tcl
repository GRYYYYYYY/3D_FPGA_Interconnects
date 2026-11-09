open_project project
set_top lookahead_services51
add_files {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/mechanism/hls_c/source/services51.cpp} -cflags {-I/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/mechanism/hls_c/source -std=c++14 -pthread -ffp-contract=off -fno-fast-math -DLA51_RTL_SHORT}
add_files -tb {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/mechanism/hls_c/source/tb51.cpp} -cflags {-I/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/mechanism/hls_c/source -std=c++14 -pthread -ffp-contract=off -fno-fast-math -DLA51_RTL_SHORT}
open_solution solution -flow_target vivado
set_part xcu280-fsvh2892-2L-e
create_clock -period 5 -name default
set phase $::env(LA51_PHASE)
if {$phase eq "csim"} {csim_design -ldflags "-pthread"}
if {$phase eq "csynth"} {csynth_design}
if {$phase eq "cosim"} {cosim_design -rtl verilog -tool xsim -trace_level all -ldflags "-pthread" -enable_dataflow_profiling}
exit
