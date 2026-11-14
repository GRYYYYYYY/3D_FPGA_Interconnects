set root [file normalize [file join [file dirname [info script]] ../../../..]]
foreach spec {{front_leaf_final4_g 4 tb_leaf} {front_leaf_final8_g 8 tb_leaf} {front_context_final4_g 4 tb_context} {front_native_bnn_d 4 tb_native} {front_native_lstm_d 4 tb_native} {front_targets_bnn_d 4 tb_native} {front_targets_lstm_d 8 tb_native}} {
 lassign $spec df_out df_lanes df_tb
 source $root/accel/lookahead/fpga_descriptor_front/front/sim_leaf.tcl
}
