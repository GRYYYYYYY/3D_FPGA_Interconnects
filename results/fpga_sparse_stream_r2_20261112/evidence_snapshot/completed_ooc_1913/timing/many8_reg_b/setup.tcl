create_project r2_many8_reg_b {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many8_reg_b/project} -part xcu280-fsvh2892-2L-e
add_files [glob {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many8_reg_b/source/*.sv}]
set_property top r2_many_tile [current_fileset]
set_property generic {L=8 PHYS=8 MEMBER_CAP=1024 CHANGED_LIMIT=512 USE_URAM=0} [current_fileset]
add_files -fileset constrs_1 {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many8_reg_b/source/tile_ooc.xdc}
set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]
set_property STEPS.SYNTH_DESIGN.TCL.PRE {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many8_reg_b/source/synth_pre.tcl} [get_runs synth_1]
set_property STEPS.SYNTH_DESIGN.TCL.POST {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many8_reg_b/source/synth_post.tcl} [get_runs synth_1]
set_property STEPS.ROUTE_DESIGN.TCL.POST {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/many8_reg_b/source/route_post.tcl} [get_runs impl_1]
update_compile_order -fileset sources_1
