set root [file normalize [file join [file dirname [info script]] ../../../..]]
set df_out front_pair_h
source $root/accel/lookahead/fpga_descriptor_front/front/sim_pair_again.tcl
foreach spec {{front_leaf_final4_h 4 tb_leaf} {front_leaf_final8_h 8 tb_leaf} {front_context_final4_h 4 tb_context} {front_native_bnn_h 4 tb_native} {front_native_lstm_h 4 tb_native} {front_targets_bnn_h 4 tb_native} {front_targets_lstm_h 8 tb_native} {front_reject_h 4 tb_reject}} {
 lassign $spec df_out df_lanes df_tb
 source $root/accel/lookahead/fpga_descriptor_front/front/sim_leaf.tcl
}
