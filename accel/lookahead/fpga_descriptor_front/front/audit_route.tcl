# Read-only actual net/path audit; set df_audit_out for currently-open DCP.
report_drc -checks [get_drc_checks RTSTAT*] -file $df_audit_out/route_drc.rpt
set f [open $df_audit_out/net_connectivity.csv w]
puts $f {net,route_status,driver_pins,internal_sink_pins,top_ports,classification}
set totals [dict create]
foreach n [get_nets -of_objects [get_drc_violations RTSTAT-10*]] {
 set segments [get_nets -segments $n]
 set drivers [get_pins -quiet -leaf -of_objects $segments -filter {DIRECTION == OUT}]
 set sinks [get_pins -quiet -leaf -of_objects $segments -filter {DIRECTION == IN}]
 set ports [get_ports -quiet -of_objects $segments]
 if {[llength $sinks]} {set kind HAS_INTERNAL_SINK_INSPECT} elseif {[llength $ports]} {set kind EXTERNAL_OUTPUT_ONLY} else {set kind UNUSED_DRIVER_OUTPUT}
 dict incr totals $kind
 puts $f [join [list $n [get_property ROUTE_STATUS $n] [join $drivers {;}] [join $sinks {;}] [join $ports {;}] $kind] ,]
}
close $f
set tf [open $df_audit_out/path_classification_summary.txt w]
puts $tf "RTSTAT10_net_categories $totals"
foreach dtype {min max} {
 set f [open $df_audit_out/${dtype}_failures.csv w]
 puts $f {startpoint,endpoint,slack_ns,classification}
 set totals [dict create]
 foreach p [get_timing_paths -delay_type $dtype -slack_lesser_than 0 -max_paths 10000 -nworst 1] {
  set sp [get_property STARTPOINT_PIN $p];set ep [get_property ENDPOINT_PIN $p]
  if {[string first / $sp]<0} {set kind INPUT_INTERFACE} elseif {[string first / $ep]<0} {set kind OUTPUT_INTERFACE} else {set kind INTERNAL}
  dict incr totals $kind
  puts $f [join [list $sp $ep [get_property SLACK $p] $kind] ,]
 }
 close $f
 puts $tf "${dtype}_negative_path_categories $totals"
}
close $tf
