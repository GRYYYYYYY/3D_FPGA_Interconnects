open_project project
set_top lookahead_onchip4
set flags {-I/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round4_20261108T182500Z/hls_full_1/source_snapshot -std=c++14 -ffp-contract=off -fno-fast-math -DLA4_ENGINES=1 -DLA4_EARLY=0 -DLA4_DEPTH_ROW=2864 -DLA4_DEPTH_NODES=2864 -DLA4_DEPTH_EDGES=7928 -DLA4_DEPTH_COSTS=16 -DLA4_DEPTH_JOBS=16 -DLA4_DEPTH_CELLS=34352 -DLA4_DEPTH_OUTPUT=600 -DLA4_DEPTH_STATS=12}
add_files {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round4_20261108T182500Z/hls_full_1/source_snapshot/onchip4.cpp} -cflags $flags
add_files -tb {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round4_20261108T182500Z/hls_full_1/source_snapshot/onchip_tb4.cpp} -cflags $flags
open_solution solution -flow_target vivado
set_part xcu280-fsvh2892-2L-e
create_clock -period 5 -name default
set args [list {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round3_20261108T141500Z/native_d3_w8/workload.bin} {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round3_20261108T141500Z/native_d4_w8/workload.bin} {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round4_20261108T182500Z/native_d5_w8/workload.bin}]
set phase $::env(LA4_PHASE)
if {$phase eq "csim"} {csim_design -argv $args}
if {$phase eq "csynth"} {csynth_design}
if {$phase eq "cosim"} {cosim_design -rtl verilog -tool xsim -trace_level none -argv $args}
if {$phase eq "impl"} {export_design -rtl verilog -format ip_catalog -flow impl}
exit
