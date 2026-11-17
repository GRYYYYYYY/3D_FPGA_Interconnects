create_project -in_memory migration_probe -part xcu250-figd2104-2L-e
read_verilog probe.sv
synth_design -top migration_probe -part xcu250-figd2104-2L-e -mode out_of_context
set fp [open probe_receipt.txt w]
puts $fp "PART [get_property PART [current_design]]"
foreach primitive {URAM288 RAMB36E2 RAMB18E2 RAMD64E FDRE BUFGCE} {
 set lib [get_lib_cells -quiet */$primitive]
 puts $fp "PRIMITIVE $primitive COUNT [llength $lib]"
 if {![llength $lib]} {error "Missing primitive $primitive"}
}
foreach type {SLICEL SLICEM RAMB180 RAMB181 RAMB36 URAM288 BUFGCE} {
 puts $fp "SITES $type [llength [get_sites -quiet -filter SITE_TYPE==$type]]"
}
puts $fp "SLRS [get_slrs]"
set sites [lsort -dictionary [get_sites -filter {SITE_TYPE == BUFGCE && IS_USED == 0}]]
set site [lindex $sites [expr {[llength $sites]/2}]]
puts $fp "SELECTED_CLOCK_SITE $site"
puts $fp "CLOCK_SLR [get_slrs -of_objects [get_sites $site]]"
close $fp
report_property -all -file selected_part.rpt [get_parts xcu250-figd2104-2L-e]
report_utilization -file probe_utilization.rpt
puts "MIGRATION_PROBE_PASS $site"
close_project
