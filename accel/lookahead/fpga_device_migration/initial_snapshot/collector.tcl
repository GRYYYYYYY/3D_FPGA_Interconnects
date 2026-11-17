# Tcl8.5-compatible finally semantics. Both scripts run in caller scope.
proc cp_rtca_finally {body cleanup} {
    set code [catch {uplevel 1 $body} value options]
    set clean_code [catch {uplevel 1 $cleanup} clean_value clean_options]
    if {$clean_code} {return -options $clean_options $clean_value}
    return -options $options $value
}

# Vivado 2022.2. SOURCE DEFINES PROCEDURES ONLY; no EDA executes at source time.
# Parent binds/opens the actual completed terminal checkpoint before calling.
proc cp_rtca_report {receipt label script expected} {
    puts $receipt [list BEGIN $label UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}] SCRIPT $script]
    flush $receipt
    set start [clock milliseconds]
    set code [catch {uplevel 1 $script} result options]
    puts $receipt [list END $label RETURN_CODE $code ELAPSED_MS [expr {[clock milliseconds]-$start}] RESULT $result OPTIONS $options]
    set missing 0
    foreach path $expected {
        if {[file isfile $path]} {
            puts $receipt [list ARTIFACT $label PATH $path BYTES [file size $path] COMMAND_RETURN_CODE $code CONTENT_VALIDATED 0]
        } else {
            incr missing
            puts $receipt [list ARTIFACT $label PATH $path MISSING 1 COMMAND_RETURN_CODE $code]
        }
    }
    flush $receipt
    return [expr {$code != 0 || $missing != 0}]
}

# Isolate census.tcl temporary variables (including fp) from the collector.
proc cp_rtca_census {out census_source} {
    set cp_report_dir $out
    cp_rtca_finally {
        source $census_source
    } {
        if {[info exists fp] && [lsearch -exact [chan names] $fp] >= 0} {close $fp}
    }
}

# Source the unchanged helper into an isolated Tcl namespace at CALL time.
proc cp_rtca_clock_context {out clock_source} {
    namespace eval ::cp_rtca_clock_runtime [list source $clock_source]
    ::cp_rtca_clock_runtime::cp_clock_context_connected $out 0
}

proc cp_collect_route_terminal {NEW_OUT} {
    # No process/terminal/DCP identity is inferred from current_design.
    if {[file exists $NEW_OUT]} {error "Use a NEW output directory: $NEW_OUT"}
    set design [current_design]
    if {[get_property TOP $design] ne "cp_full_top" ||
        [get_property PART $design] ne "xcu250-figd2104-2L-e"} {
        error "Unexpected full-core TOP/PART; nothing collected"
    }
    set repo {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_CPU_PRIMARY}
    set census_source {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_DEVICE_MIGRATION/results/fpga_device_migration_20261117/migration_a/census.tcl}
    set clock_source {/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_DEVICE_MIGRATION/results/fpga_device_migration_20261117/migration_a/clock_context.tcl}
    file mkdir $NEW_OUT
    set out [file normalize $NEW_OUT]
    set receipt [open [file join $out collection_receipt.txt] {WRONLY CREAT EXCL}]
    set failures 0
    cp_rtca_finally {
        puts $receipt [list UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}] TOOL [version -short] DESIGN $design TOP [get_property TOP $design] PART [get_property PART $design] OUTPUT $out]
        puts $receipt {SCOPE Parent-selected terminal snapshot, possibly route_error. Parent must bind DCP SHA/path/open transcript. Collector neither verifies process terminal nor opens/writes checkpoints.}
        puts $receipt {QUALIFICATION None. Command return 0 is report execution only, not DRC/timing/routing pass. No report overrides real port timing or OOC limits.}
        puts $receipt [list SOURCES CENSUS $census_source CLOCK_CONTEXT $clock_source APPLY_CONTEXT 0]
        flush $receipt
        foreach {label script names} {
            design_properties {report_property -all -file [file join $out design_properties.rpt] $design} {design_properties.rpt}
            utilization {report_utilization -file [file join $out utilization.rpt]} {utilization.rpt}
            hierarchy {report_utilization -hierarchical -hierarchical_depth 0 -file [file join $out hierarchy.rpt]} {hierarchy.rpt}
            timing_summary {report_timing_summary -delay_type min_max -report_unconstrained -max_paths 20 -file [file join $out timing.rpt]} {timing.rpt}
            check_timing {check_timing -verbose -file [file join $out check_timing.rpt]} {check_timing.rpt}
            drc {report_drc -file [file join $out drc.rpt]} {drc.rpt}
            methodology {report_methodology -file [file join $out methodology.rpt]} {methodology.rpt}
            clocks {report_clocks -file [file join $out clocks.rpt]} {clocks.rpt}
            exceptions {report_exceptions -file [file join $out exceptions.rpt]} {exceptions.rpt}
            constraints {write_xdc [file join $out actual_constraints.xdc]} {actual_constraints.xdc}
            route_status {report_route_status -file [file join $out route_status.rpt]} {route_status.rpt}
            all_setup {report_timing -delay_type max -max_paths 20 -path_type full_clock_expanded -file [file join $out setup_paths.rpt]} {setup_paths.rpt}
            all_hold {report_timing -delay_type min -max_paths 20 -path_type full_clock_expanded -file [file join $out hold_paths.rpt]} {hold_paths.rpt}
            register_collection {
                set cp_regs [all_registers]
                if {![llength $cp_regs]} {error "No sequential register cells returned; internal scope unavailable"}
                llength $cp_regs
            } {}
            internal_setup {if {![info exists cp_regs] || ![llength $cp_regs]} {error "Internal register scope unavailable"}; report_timing -delay_type max -from $cp_regs -to $cp_regs -max_paths 20 -path_type full_clock_expanded -file [file join $out internal_setup.rpt]} {internal_setup.rpt}
            internal_hold {if {![info exists cp_regs] || ![llength $cp_regs]} {error "Internal register scope unavailable"}; report_timing -delay_type min -from $cp_regs -to $cp_regs -max_paths 20 -path_type full_clock_expanded -file [file join $out internal_hold.rpt]} {internal_hold.rpt}
            census {cp_rtca_census $out $census_source} {primitive_census.csv surviving_hierarchy.txt output_connectivity.csv}
            blackboxes {
                set bb [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]
                set bfp [open [file join $out blackboxes.txt] {WRONLY CREAT EXCL}]
                cp_rtca_finally {puts $bfp [join $bb "\n"]} {close $bfp}
            } {blackboxes.txt}
            clock_context {cp_rtca_clock_context [file join $out clock_context] $clock_source} {clock_context/connectivity.txt clock_context/clocks.rpt clock_context/networks.rpt clock_context/actual_constraints.xdc}
            buffer_locations {
                set bfp [open [file join $out buffer_locations.txt] {WRONLY CREAT EXCL}]
                cp_rtca_finally {
                    set hd [get_property HD.CLK_SRC [get_ports clk]]
                    puts $bfp "CORE_HD_CLK_SRC $hd"
                    if {$hd eq ""} {error "clk has no declared HD.CLK_SRC"}
                    set site [get_sites $hd]
                    if {[llength $site] != 1} {error "Declared clock source site not unique"}
                    puts $bfp "CORE_HD_SITE_IS_USED [get_property IS_USED $site]"
                    puts $bfp "CELLS_AT_CORE_HD_SITE [get_cells -quiet -of_objects $site]"
                    foreach b [get_cells -hierarchical -filter {REF_NAME =~ BUFG* || REF_NAME =~ MMCME* || REF_NAME =~ PLLE*}] {
                        puts $bfp "BUFFER $b REF [get_property REF_NAME $b] LOC [get_property LOC $b] BEL [get_property BEL $b]"
                        foreach pin [get_pins -of_objects $b] {
                            puts $bfp " PIN $pin DIRECTION [get_property DIRECTION $pin] NET [get_nets -quiet -of_objects $pin]"
                        }
                    }
                } {close $bfp}
            } {buffer_locations.txt}
            congestion {report_design_analysis -congestion -min_congestion_level 3 -file [file join $out congestion_level3.rpt]} {congestion_level3.rpt}
        } {
            set expected {}
            foreach name $names {lappend expected [file join $out $name]}
            incr failures [cp_rtca_report $receipt $label $script $expected]
        }
        # Helper-generated control-buffer paths vary with the actual netlist.
        # A failed helper leaves all its outputs partial/unvalidated regardless
        # of whether individual files exist. Never infer PASS from file presence.
        foreach p [glob -nocomplain [file join $out clock_context control_buffer_*.rpt]] {
            puts $receipt [list HELPER_ARTIFACT PATH $p BYTES [file size $p] CONTENT_VALIDATED 0]
        }
        puts $receipt [list STATUS [expr {$failures ? "COLLECTION_HAS_FAILURES" : "COLLECTION_COMMANDS_COMPLETED_NOT_SIGNOFF"}] FAILED_GROUPS $failures UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}]]
        flush $receipt
    } {
        close $receipt
    }
    if {$failures} {error "Terminal collection has $failures failed report/helper groups; inspect $out/collection_receipt.txt"}
    return $out
}
