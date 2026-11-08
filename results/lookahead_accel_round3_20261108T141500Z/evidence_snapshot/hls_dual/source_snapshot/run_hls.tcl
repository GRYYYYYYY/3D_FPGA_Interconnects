set root $::env(LA_ROOT)
set out $::env(LA_HLS_OUT)
set phase $::env(LA_PHASE)
cd $out
open_project project
set_top $::env(LA_TOP)
set flags "-I$root/accel/lookahead/include -std=c++14 -ffp-contract=off -fno-fast-math $::env(LA_EXTRA_FLAGS)"
add_files $::env(LA_SOURCE) -cflags $flags
add_files -tb $::env(LA_TESTBENCH) -cflags $flags
open_solution solution -flow_target vivado
set_part xcu280-fsvh2892-2L-e
set period 5
if {[info exists ::env(LA_PERIOD_NS)]} {set period $::env(LA_PERIOD_NS)}
create_clock -period $period -name default

if {$phase eq "csim"} {csim_design -argv $::env(LA_WORKLOAD)}
if {$phase eq "csynth"} {csynth_design}
set trace all
if {[info exists ::env(LA_TRACE_LEVEL)]} {set trace $::env(LA_TRACE_LEVEL)}
if {$phase eq "cosim"} {cosim_design -rtl verilog -tool xsim -trace_level $trace -argv $::env(LA_WORKLOAD)}
if {$phase eq "impl"} {export_design -rtl verilog -format ip_catalog -flow impl}
exit
