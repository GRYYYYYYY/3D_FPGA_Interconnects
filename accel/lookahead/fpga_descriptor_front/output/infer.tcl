set root [file normalize [file join [file dirname [info script]] ../../../..]]
set src $root/accel/lookahead/fpga_descriptor_front
set out [pwd]
create_project output_ram $out/project -part xcu280-fsvh2892-2L-e -force
set_param general.maxThreads 8
add_files [list $src/services/df_rr_router.sv $src/output/df_output_bank.sv $src/output/df_output_service.sv $src/output/df_ack_collector.sv $src/output/df_output_context.sv]
set_property top df_output_context [get_filesets sources_1]
update_compile_order -fileset sources_1
synth_design -top df_output_context -part xcu280-fsvh2892-2L-e -mode out_of_context -flatten_hierarchy rebuilt
create_clock -name clk -period 5 [get_ports clk]
report_utilization -file $out/utilization.rpt
report_utilization -hierarchical -file $out/utilization_hierarchical.rpt
write_checkpoint -force $out/synth.dcp
set f [open $out/ram_cells.csv w]
puts $f "instance,primitive,READ_WIDTH_A,READ_WIDTH_B,WRITE_WIDTH_A,WRITE_WIDTH_B,DOA_REG,DOB_REG"
foreach c [get_cells -hier -filter {REF_NAME =~ RAMB* || REF_NAME =~ URAM*}] {
 set row [list $c [get_property REF_NAME $c]]
 foreach property {READ_WIDTH_A READ_WIDTH_B WRITE_WIDTH_A WRITE_WIDTH_B DOA_REG DOB_REG} {
  if {[lsearch -exact [list_property $c] $property]>=0} {lappend row [get_property $property $c]} else {lappend row NA}
 }
 puts $f [join $row ,]
}
close $f
set f [open $out/terminal.txt w]
puts $f "RAM_INFERENCE_COMPLETED version=[version -short] top=df_output_context groups=16 banks=8 cells=32768 rows_per_bank=4096 ack_sources=32 ack_holders=2"
puts $f "NO_ROUTED_CLOCK_QUALIFICATION"
close $f
