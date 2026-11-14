# Read-only audit of the currently-open fully-routed local owner.
if {![info exists ec_audit_out]} {error {set ec_audit_out before sourcing}}
set ec_f [open $ec_audit_out/net_connectivity.csv w]
puts $ec_f {net,route_status,driver_pins,internal_sink_pins,top_ports,classification}
set ec_totals [dict create]
set ec_nets [get_nets -of_objects [get_drc_violations RTSTAT-10*]]
foreach ec_n $ec_nets {
 set ec_segments [get_nets -segments $ec_n]
 set ec_drivers [get_pins -quiet -leaf -of_objects $ec_segments -filter {DIRECTION == OUT}]
 set ec_sinks [get_pins -quiet -leaf -of_objects $ec_segments -filter {DIRECTION == IN}]
 set ec_ports [get_ports -quiet -of_objects $ec_segments]
 if {[llength $ec_sinks]} {set ec_kind HAS_INTERNAL_SINK_INSPECT} elseif {[llength $ec_ports]} {set ec_kind EXTERNAL_OUTPUT_ONLY} else {set ec_kind UNUSED_DRIVER_OUTPUT}
 dict incr ec_totals $ec_kind
 puts $ec_f [join [list $ec_n [get_property ROUTE_STATUS $ec_n] [join $ec_drivers {;}] [join $ec_sinks {;}] [join $ec_ports {;}] $ec_kind] ,]
}
close $ec_f
set ec_f [open $ec_audit_out/hold_failure_classification.csv w]
puts $ec_f {startpoint,endpoint,slack_ns,classification}
set ec_hold_totals [dict create]
set ec_paths [get_timing_paths -delay_type min -slack_lesser_than 0 -max_paths 10000 -nworst 1]
foreach ec_p $ec_paths {
 set ec_sp [get_property STARTPOINT_PIN $ec_p];set ec_ep [get_property ENDPOINT_PIN $ec_p]
 if {[string first / $ec_sp]<0} {set ec_kind INPUT_INTERFACE} elseif {[string first / $ec_ep]<0} {set ec_kind OUTPUT_INTERFACE} else {set ec_kind INTERNAL}
 dict incr ec_hold_totals $ec_kind
 puts $ec_f [join [list $ec_sp $ec_ep [get_property SLACK $ec_p] $ec_kind] ,]
}
close $ec_f
set ec_f [open $ec_audit_out/connectivity_summary.txt w]
puts $ec_f "affected_nets [llength $ec_nets]"
puts $ec_f "net_categories $ec_totals"
puts $ec_f "negative_hold_paths [llength $ec_paths]"
puts $ec_f "hold_categories $ec_hold_totals"
close $ec_f
puts "NET_AUDIT affected=[llength $ec_nets] classes=$ec_totals negativeHold=[llength $ec_paths] holdClasses=$ec_hold_totals"
