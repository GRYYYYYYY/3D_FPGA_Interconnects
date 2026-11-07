# Vitis HLS 2022.2 Tcl flow (vitis-run/Unified IDE is not required).
set root [file normalize [file join [file dirname [info script]] ..]]
set phase csynth
if {[info exists ::env(H3D_HLS_PHASE)]} { set phase $::env(H3D_HLS_PHASE) }
set vectors ""
if {[info exists ::env(H3D_HLS_VECTORS)]} { set vectors [file normalize $::env(H3D_HLS_VECTORS)] }
if {$phase ni {csim csynth cosim}} { error "H3D_HLS_PHASE must be csim, csynth or cosim" }
file mkdir [file join $root build_hls]
cd [file join $root build_hls]
open_project candidate_cost
set_top evaluate_candidates
add_files [file join $root hardware candidate_cost.cpp] -cflags "-DH3D_HLS -I$root/hardware -std=c++14"
add_files -tb [file join $root tests test_cost.cpp] -cflags "-I$root/hardware -std=c++14"
open_solution solution -flow_target vivado
set_part xcu280-fsvh2892-2L-e
create_clock -period 5 -name default
if {$phase eq "cosim"} {
    if {![file exists [file join $root build_hls candidate_cost solution syn report evaluate_candidates_csynth.xml]]} {
        error "Run csynth before cosim"
    }
    cosim_design -rtl verilog -tool xsim -argv $vectors
} else {
    csim_design -argv $vectors
    if {$phase eq "csynth"} { csynth_design }
}
exit
