# One bounded same-RTL implementation. No old checkpoint inputs.
set receipt [open [file join $out stages.txt] {WRONLY CREAT EXCL}]
proc mark {stage status message} {
 global receipt out
 puts $receipt [list UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}] STAGE $stage STATUS $status MESSAGE $message];flush $receipt
 set f [open [file join $out stage.txt] w];puts $f "$stage $status";close $f
}
proc checkpoint {stage} {
 global out target_part
 if {[get_property PART [current_design]] ne $target_part || [get_property TOP [current_design]] ne "cp_full_top"} {error "SOURCE_OR_CONSTRAINT_MISMATCH"}
 set p [file join $out "$stage.dcp"]
 write_checkpoint $p
 set f [open "$p.sha256" w];puts $f "[lindex [exec sha256sum -- $p] 0] [file size $p] $p";close $f
}
proc basic {stage} {
 global out
 set dir [file join $out $stage];file mkdir $dir
 report_utilization -file [file join $dir utilization.rpt]
 report_utilization -hierarchical -hierarchical_depth 4 -file [file join $dir hierarchy.rpt]
 report_drc -file [file join $dir drc.rpt]
 set f [open [file join $dir blackboxes.txt] w];set bb [get_cells -hierarchical -filter {IS_BLACKBOX == 1}];puts $f $bb;close $f
 if {[llength $bb]} {error "SOURCE_OR_CONSTRAINT_MISMATCH blackboxes"}
 set f [open [file join $dir ports.tsv] w]
 foreach p [get_ports] {puts $f "[get_property NAME $p]\t[get_property DIRECTION $p]"};close $f
 exec python3 [file join $out gate.py] $dir
}
source [file join $out collector.tcl]
set state SOURCE_OR_CONSTRAINT_MISMATCH
set current_stage synth
set result [catch {
 mark synth START {}
 synth_design -top cp_full_top -part $target_part -mode out_of_context -flatten_hierarchy rebuilt
 mark synth COMPLETE {}
 checkpoint synth
 basic synth
 set cp_report_dir [file join $out synth]
 cp_rtca_census $cp_report_dir [file join $out census.tcl]
 exec python3 [file join $out gate.py] $cp_report_dir census
 read_xdc [file join $out context.xdc]
 source [file join $out clock_context.tcl]
 cp_clock_context_connected [file join $out initial_clock_context] 1
 foreach {current_stage command} {
  opt {opt_design}
  place {place_design -directive SSI_SpreadSLLs -ultrathreads}
  phys_opt {phys_opt_design}
  route {route_design}
 } {
  mark $current_stage START $command
  uplevel #0 $command
  mark $current_stage COMPLETE {}
  checkpoint $current_stage
  basic $current_stage
 }
 set state ROUTED_REQUIRES_AUDIT
} message options]
if {$result} {
 mark $current_stage FAILED $message
 if {[string match *RESOURCE_FAIL* $message]} {set state RESOURCE_FAIL} elseif {$current_stage eq "place" || $current_stage eq "phys_opt"} {set state PLACE_FAIL} elseif {$current_stage eq "route"} {set state ROUTE_FAIL}
 if {[current_design -quiet] ne ""} {catch {checkpoint "${current_stage}_error"} e;mark error_checkpoint COLLECTED_OR_FAILED $e}
}
set collect_code [catch {cp_collect_route_terminal [file join $out terminal_reports]} collect_message]
mark collection $collect_code $collect_message
set f [open [file join $out terminal_state.txt] w];puts $f $state;puts $f "flow_return_code=$result collection_return_code=$collect_code";puts $f $message;close $f
close $receipt
exit $result
