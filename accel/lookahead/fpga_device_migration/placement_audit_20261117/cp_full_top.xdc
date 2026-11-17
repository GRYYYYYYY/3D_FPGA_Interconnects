set_property SRC_FILE_INFO {cfile:/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_DEVICE_MIGRATION/results/fpga_device_migration_20261117/migration_a/clock.xdc rfile:clock.xdc id:1 rxprname:$PPRDIR/../clock.xdc} [current_design]
set_property src_info {type:XDC file:1 line:1 export:INPUT save:INPUT read:READ} [current_design]
create_clock -period 5.000 -name core_clock [get_ports clk]
set_property src_info {type:XDC file:1 line:2 export:INPUT save:INPUT read:READ} [current_design]
set_clock_uncertainty 0.100 [get_clocks core_clock]
set_property src_info {type:XDC file:1 line:3 export:INPUT save:INPUT read:READ} [current_design]
set _xlnx_shared_i0 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock core_clock -max 0.800 $_xlnx_shared_i0
set_property src_info {type:XDC file:1 line:4 export:INPUT save:INPUT read:READ} [current_design]
set_input_delay -clock core_clock -min 0.100 $_xlnx_shared_i0
set_property src_info {type:XDC file:1 line:5 export:INPUT save:INPUT read:READ} [current_design]
set _xlnx_shared_i1 [get_ports -filter {DIRECTION == OUT}]
set_output_delay -clock core_clock -max 0.800 $_xlnx_shared_i1
set_property src_info {type:XDC file:1 line:6 export:INPUT save:INPUT read:READ} [current_design]
set_output_delay -clock core_clock -min 0.100 $_xlnx_shared_i1
set_property src_info {type:XDC file:1 line:7 export:INPUT save:INPUT read:READ} [current_design]

