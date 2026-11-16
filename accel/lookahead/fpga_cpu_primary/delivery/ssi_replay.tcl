# Vivado 2022.2 / Tcl 8.5. Source defines procedures only.
# Single selected implementation strategy; never synthesizes or resets a run.
proc cp_ssi_command {receipt kind label script} {
    puts $receipt [list BEGIN $kind $label UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}] SCRIPT $script]
    flush $receipt
    set started [clock milliseconds]
    set code [catch {uplevel 1 $script} result options]
    puts $receipt [list END $kind $label RETURN_CODE $code ELAPSED_MS [expr {[clock milliseconds]-$started}] RESULT $result OPTIONS $options]
    flush $receipt
    return $code
}

proc cp_ssi_require {receipt label script} {
    set code [cp_ssi_command $receipt REQUIRED $label [list uplevel 1 $script]]
    if {$code} {error "Required step failed: $label; see run_receipt.txt"}
}

proc cp_ssi_replay {input_dcp new_out collector_script clock_script post_place_script} {
    if {[file exists $new_out]} {error "Output must be a new directory: $new_out"}
    if {[current_design -quiet] ne ""} {error "Close the preceding design before replay"}
    if {[version -short] ne "2022.2"} {error "This replay is bound to Vivado2022.2"}
    set expected_sha 3781ee752bae928c4993e5f148247f9b118b85f97d20f452e861c00cb4779ada
    set actual_sha [lindex [exec sha256sum -- $input_dcp] 0]
    if {$actual_sha ne $expected_sha || [file size $input_dcp] != 402895145} {error "Input is not the verified unplaced f post-opt DCP"}
    foreach p [list $collector_script $clock_script $post_place_script] {
        if {![file isfile $p]} {error "Missing frozen script: $p"}
    }
    # Collector source has no EDA side effects; Tcl8.5-compatible revision only.
    source -notrace $collector_script
    source -notrace $clock_script
    file mkdir $new_out
    set out [file normalize $new_out]
    set previous_pwd [pwd]
    cd $out
    set receipt [open [file join $out run_receipt.txt] {WRONLY CREAT EXCL}]
    set failed_stage ""
    set report_failures 0
    set checkpoint_failures 0
    set overall_code [catch {
        puts $receipt [list CONFIG TOOL [version -short] TCL [info patchlevel] INPUT_DCP [file normalize $input_dcp] INPUT_SHA256 $actual_sha DIRECTIVE SSI_SpreadSLLs ULTRATHREADS 1 THREADS 8 PERIOD_NS 5]
        puts $receipt {SCOPE Independent non-project implementation from terminal unplaced f opt DCP. Original project/run is never reset or changed. No synthesis, opt_design, incremental reuse, source or constraint changes.}
        puts $receipt {QUALIFICATION Route command completion is not timing, legal-routing, interface or board qualification. Reports retain all port paths and OOC limitations.}
        foreach p [list $collector_script $clock_script $post_place_script] {puts $receipt [list SCRIPT_INPUT $p SHA256 [lindex [exec sha256sum -- $p] 0]]}
        flush $receipt
        set_param general.maxThreads 8
        # Same parameters emitted by the original f physical project script.
        set_param power.enableLutRouteBelPower 1
        set_param power.enableCarry8RouteBelPower 1
        set_param power.enableUnconnectedCarry8PinPower 1
        set_param chipscope.maxJobs 7
        set_param power.BramSDPPropagationFix 1
        set_param messaging.defaultLimit 10000000
        cp_ssi_require $receipt open_input {open_checkpoint $input_dcp}
        if {[get_property TOP [current_design]] ne "cp_full_top" || [get_property PART [current_design]] ne "xcu280-fsvh2892-2L-e"} {error "Unexpected input TOP/PART"}
        set clocks [get_clocks]
        if {[llength $clocks] != 1 || [get_property NAME $clocks] ne "core_clock" || [get_property PERIOD $clocks] != 5.0} {error "Unexpected actual clock constraint"}
        if {[get_property HD.CLK_SRC [get_ports clk]] ne "BUFGCE_X0Y144"} {error "Input lost actual core clock context"}
        cp_ssi_require $receipt input_clock_connectivity {cp_clock_context_connected [file join $out pre_context] 0}
        foreach {stage command checkpoint} {
            place_design {place_design -directive SSI_SpreadSLLs -ultrathreads} cp_full_top_placed.dcp
            phys_opt_design {phys_opt_design} cp_full_top_physopt.dcp
            route_design {route_design} cp_full_top_routed.dcp
        } {
            set stage_code [cp_ssi_command $receipt EDA $stage $command]
            if {$stage_code} {
                set failed_stage $stage
                set error_dcp [file join $out "cp_full_top_${stage}_error.dcp"]
                incr checkpoint_failures [expr {[cp_ssi_command $receipt CHECKPOINT ${stage}_error {write_checkpoint $error_dcp}] != 0}]
                # Keep the failure state and collect its real reports before returning.
                incr report_failures [expr {[cp_ssi_command $receipt REPORT ${stage}_failure_reports {cp_collect_route_terminal [file join $out "${stage}_failure_reports"]}] != 0}]
                break
            }
            set checkpoint_path [file join $out $checkpoint]
            cp_ssi_require $receipt ${stage}_checkpoint {write_checkpoint $checkpoint_path}
            if {$stage eq "place_design"} {
                # This frozen hook accepts the caller's new cp_report_dir.
                set cp_report_dir [file join $out post_place]
                incr report_failures [expr {[cp_ssi_command $receipt REPORT post_place {source -notrace $post_place_script}] != 0}]
            }
            if {$stage eq "route_design"} {
                incr report_failures [expr {[cp_ssi_command $receipt REPORT post_route {cp_collect_route_terminal [file join $out post_route]}] != 0}]
            }
        }
        puts $receipt [list TERMINAL FAILED_EDA_STAGE $failed_stage REPORT_FAILURES $report_failures ERROR_CHECKPOINT_FAILURES $checkpoint_failures UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}]]
        flush $receipt
        if {$failed_stage ne ""} {error "Implementation failed at $failed_stage; failure DCP/reports retained"}
        if {$report_failures || $checkpoint_failures} {error "Implementation commands completed but delivery has report/checkpoint failures"}
    } overall_result overall_options]
    puts $receipt [list RETURN_CODE $overall_code RESULT $overall_result OPTIONS $overall_options]
    flush $receipt
    close $receipt
    cd $previous_pwd
    return -options $overall_options $overall_result
}
