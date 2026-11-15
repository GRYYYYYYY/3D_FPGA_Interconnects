# Vivado 2022.2: implementation-only OOC clock context, verified by connectivity.
# Keep bulk collections native. No per-pin get_nets/segments expansion.
proc cp_clock_context_connected {out apply_context} {
    file mkdir $out
    set fp [open [file join $out connectivity.txt] {WRONLY CREAT EXCL}]
    puts $fp "UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}]"
    puts $fp "TOP [get_property TOP [current_design]] PART [get_property PART [current_design]]"
    if {[get_property TOP [current_design]] ne "cp_full_top" || [get_property PART [current_design]] ne "xcu280-fsvh2892-2L-e"} {error "Unexpected full-core design"}
    set clocks [get_clocks]
    if {[llength $clocks] != 1 || [get_property NAME $clocks] ne "core_clock" || [get_property PERIOD $clocks] != 5.0} {error "Unexpected clock definition"}
    set port [get_ports clk]
    set root [get_nets -of_objects $port]
    if {[llength $port] != 1 || [llength $root] != 1} {error "Ambiguous clk root"}
    set all_pins [all_registers -clock_pins]
    set core_pins [all_registers -clock core_clock -clock_pins]
    set all_names [lsort -unique [get_property NAME $all_pins]]
    set core_names [lsort -unique [get_property NAME $core_pins]]
    set direct_pins [get_pins -quiet -leaf -of_objects $root -filter {IS_CLOCK == 1}]
    set direct_names {}
    if {[llength $direct_pins]} {set direct_names [lsort -unique [get_property NAME $direct_pins]]}
    set associated_equal [expr {$all_names eq $core_names}]
    set direct_equal [expr {$all_names eq $direct_names}]
    puts $fp "ALL_CLOCK_PINS [llength $all_names] CORE_CLOCK_PINS [llength $core_names] DIRECT_CLK_PINS [llength $direct_names]"
    puts $fp "ALL_CORE_NAMESETS_EQUAL $associated_equal ALL_DIRECT_NAMESETS_EQUAL $direct_equal"
    flush $fp
    if {![llength $all_names] || !$associated_equal} {error "Unaccounted sequential clock pins"}
    # Identify buffers by their real output loads, never merely by their presence.
    set buffers [get_cells -quiet -hierarchical -filter {REF_NAME =~ BUFG* || REF_NAME =~ MMCME* || REF_NAME =~ PLLE*}]
    puts $fp "CLOCK_CAPABLE_BUFFER_COUNT [llength $buffers]"
    foreach b $buffers {
        puts $fp "BUFFER [get_property NAME $b] REF [get_property REF_NAME $b]"
        foreach pin [get_pins -of_objects $b] {
            set net [get_nets -quiet -of_objects $pin]
            puts $fp " PIN $pin DIR [get_property DIRECTION $pin] NET $net"
            if {[get_property DIRECTION $pin] eq "OUT" && [llength $net]} {
                set loads [get_pins -quiet -leaf -of_objects $net -filter {DIRECTION == IN}]
                set clocks_on_net [get_pins -quiet -leaf -of_objects $net -filter {IS_CLOCK == 1}]
                puts $fp " OUTPUT_LOADS [llength $loads] SEQUENTIAL_CLOCK_LOADS [llength $clocks_on_net]"
                if {![llength $clocks_on_net]} {
                    puts $fp " CLASS nonclock_control_buffer"
                    report_timing -through $pin -delay_type max -max_paths 20 -file [file join $out "control_buffer_[string map {/ _} $b]_max.rpt"]
                    report_timing -through $pin -delay_type min -max_paths 20 -file [file join $out "control_buffer_[string map {/ _} $b]_min.rpt"]
                } else {puts $fp " CLASS clock_load_buffer"}
            }
        }
        flush $fp
    }
    puts $fp "HD_CLK_SRC_BEFORE [get_property HD.CLK_SRC $port]"
    if {$apply_context} {
        if {!$direct_equal} {error "Initial core clock is not directly connected to all sequential clock pins; review topology"}
        set site [get_sites -quiet BUFGCE_X0Y144]
        if {[llength $site] != 1 || [get_property SITE_TYPE $site] ne "BUFGCE" || [get_property IS_USED $site]} {error "Declared external OOC clock source site unavailable"}
        set_property HD.CLK_SRC BUFGCE_X0Y144 $port
        puts $fp "ASSUMPTION External OOC core clock source at BUFGCE_X0Y144; not a board measurement"
    }
    puts $fp "HD_CLK_SRC_AFTER [get_property HD.CLK_SRC $port]"
    close $fp
    report_clocks -file [file join $out clocks.rpt]
    report_clock_networks -file [file join $out networks.rpt]
    write_xdc -force [file join $out actual_constraints.xdc]
}
