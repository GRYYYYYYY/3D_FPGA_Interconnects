# Explicit OOC-only assumption. The containing shell/global clock is not built.
# Site existence and clock region were queried on xcu280 with Vivado2022.2.
# The external clock route is estimated from central region X4Y6, not measured.
set r2_clocks [get_clocks -quiet clk]
if {[llength $r2_clocks] != 1} {error "OOC clock missing before physical source assumption"}
set r2_site [get_sites -quiet BUFGCE_X0Y144]
if {[llength $r2_site] != 1} {error "OOC assumed clock site absent"}
set_property HD.CLK_SRC BUFGCE_X0Y144 [get_ports clk]
puts "R2_OOC_ASSUMPTION clk source=[get_property HD.CLK_SRC [get_ports clk]] region=[get_clock_regions -of_objects $r2_site] period=[get_property PERIOD $r2_clocks]"
