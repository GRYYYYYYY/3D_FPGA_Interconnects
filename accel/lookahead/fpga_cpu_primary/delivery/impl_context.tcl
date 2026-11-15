# Implementation-only hook after init_design. Upstream clock buffer is outside
# this complete-core OOC scope. Site support was queried on the installed part.
set_param general.maxThreads 8
set cp_clkbuf [get_cells -quiet -hierarchical -filter {REF_NAME =~ BUFG*}]
if {[llength $cp_clkbuf] == 0} {
    set cp_site [get_sites BUFGCE_X0Y144]
    if {[llength $cp_site] != 1} {error {Declared OOC clock source site unavailable}}
    set_property HD.CLK_SRC BUFGCE_X0Y144 [get_ports clk]
}
# No boundary constants, false paths or arbitrary min-delay relaxation.
