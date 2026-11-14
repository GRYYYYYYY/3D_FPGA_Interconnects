# Reproduction only: invoke in a NEW output directory, one selected actual top.
# Resource-only synthesis, intentionally no clock/timing qualification.
set src [file dirname [file normalize [info script]]]
set top [lindex $argv 0]
if {$top ni {df_directory_bank df_candidate_network df_min_collect df_memory_network_full}} {error "Specify one supported service top"}
if {[file exists ${top}_utilization.rpt]} {error "Existing result: choose a NEW directory"}
set_param general.maxThreads 8
read_verilog -sv [glob [file join $src df_*.sv]]
synth_design -top $top -part xcu280-fsvh2892-2L-e -mode out_of_context
report_utilization -file ${top}_utilization.rpt
report_utilization -hierarchical -file ${top}_hierarchy.rpt
write_checkpoint ${top}_synth.dcp
exit
