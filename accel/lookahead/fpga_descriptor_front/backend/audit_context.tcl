if {![info exists df_audit_out]} {error {set df_audit_out before sourcing}}
set ec_audit_out $df_audit_out
source [file join [file dirname [info script]] ../../fpga_enum_commit/integration/classify_ooc_nets.tcl]
set f [open $df_audit_out/context_cells.csv w]
puts $f {cell,primitive}
foreach c [get_cells -hier -filter {NAME =~ *context_bank* || NAME =~ request/* || NAME =~ response/*}] {
 set ref [get_property REF_NAME $c]
 if {[regexp {^FD|^RAM|^SRL} $ref]} {puts $f "$c,$ref"}
}
close $f
report_timing -from [all_registers] -to [all_registers] -delay_type min -max_paths 20 -file $df_audit_out/internal_hold.rpt
report_timing -from [all_registers] -to [all_registers] -delay_type max -max_paths 20 -file $df_audit_out/internal_setup.rpt
