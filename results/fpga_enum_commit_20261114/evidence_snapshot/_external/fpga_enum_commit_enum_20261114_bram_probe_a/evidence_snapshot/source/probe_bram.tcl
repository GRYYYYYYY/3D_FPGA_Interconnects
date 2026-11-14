set root [file normalize [file join [file dirname [info script]] ../../../..]]
set out $root/results/fpga_enum_commit_enum_20261114_bram_probe_a
create_project -in_memory -part xcu280-fsvh2892-2L-e
read_verilog -sv [list $root/accel/lookahead/fpga_sparse_stream_r2/rtl/sync_fifo.sv $root/accel/lookahead/fpga_enum_commit/enumerator/enum2_bank_bram_candidate.sv.candidate]
synth_design -mode out_of_context -top enum2_bank -part xcu280-fsvh2892-2L-e -flatten_hierarchy none
create_clock -period 5 [get_ports clk]
report_utilization -hierarchical -file $out/util_hier.rpt
report_utilization -file $out/util.rpt
write_checkpoint $out/synth.dcp
set occupied_cells [get_cells -hier -filter {NAME =~ *occupied*}]
set f [open $out/occupied_cells.txt w]
foreach c $occupied_cells {puts $f "$c [get_property REF_NAME $c]"}
close $f
