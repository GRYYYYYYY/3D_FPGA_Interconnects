# Run only with the actual synthesized/implemented complete core open.
# Caller sets cp_report_dir. These observations corroborate source/RTL proof;
# they are not a formal equivalence check.
set cp_cells [get_cells -hierarchical -filter {IS_PRIMITIVE == 1}]
set cp_names [get_property NAME $cp_cells]
set cp_refs [get_property REF_NAME $cp_cells]
set cp_counts [dict create]
set cp_global [dict create]
foreach n $cp_names r $cp_refs {
    dict incr cp_global $r
    set group OTHER
    if {[regexp {^(banks\[[0-9]+\]\.bank|fronts\[[0-9]+\]\.front)/} $n match group]} {
    } elseif {[regexp {^(fabric/port[0-9]+)[./]} $n match group]} {
    } elseif {[regexp {^([^/]+)/} $n match group]} {
    }
    set key "$group,$r"
    dict incr cp_counts $key
}
set fp [open [file join $cp_report_dir primitive_census.csv] w]
puts $fp {scope,primitive,count}
foreach k [lsort [dict keys $cp_counts]] {puts $fp "$k,[dict get $cp_counts $k]"}
foreach k [lsort [dict keys $cp_global]] {puts $fp "TOTAL,$k,[dict get $cp_global $k]"}
close $fp
set fp [open [file join $cp_report_dir surviving_hierarchy.txt] w]
puts $fp [join [get_property NAME [get_cells -hierarchical -filter {IS_PRIMITIVE == 0}]] "\n"]
close $fp
set fp [open [file join $cp_report_dir output_connectivity.csv] w]
puts $fp {port,leaf_driver_count,driver_refs}
foreach p [get_ports -filter {DIRECTION == OUT}] {
    set nets [get_nets -quiet -segments -of_objects $p]
    set pins [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
    set cells [get_cells -quiet -of_objects $pins]
    set refs {}
    if {[llength $cells] != 0} {set refs [get_property REF_NAME $cells]}
    puts $fp "[get_property NAME $p],[llength $pins],[join $refs |]"
}
close $fp
unset cp_cells cp_names cp_refs cp_counts cp_global
