open_project project
set_top heap_pop51
set flags {-I/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/pq/hls_path/source_snapshot -std=c++14 -ffp-contract=off -fno-fast-math}
add_files {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/pq/hls_path/source_snapshot/heap_hls51.cpp} -cflags $flags
add_files -tb {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_1_20261109T072948Z/pq/hls_path/source_snapshot/heap_hls_tb51.cpp} -cflags $flags
open_solution solution -flow_target vivado
set_part xcu280-fsvh2892-2L-e
create_clock -period 5 -name default
set phase $::env(HEAP51_PHASE)
if {$phase eq "csim"} {csim_design}
if {$phase eq "csynth"} {csynth_design}
if {$phase eq "cosim"} {cosim_design -rtl verilog -tool xsim -trace_level none}
exit
