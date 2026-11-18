# Fixed-input GEMM timing denominators

The figure adds the separate medians of construction (148.83 s, repeat 2) and routing (30.57 s, repeat 0). Their sum is 179.40 s. Construction is 82.9599% of this sum, which rounds to 83.0% at one decimal. The supplied 82.9% truncates the result.

The introduction uses the mean of three construction observations (149.5633 s) over mean measured Process (331.0480 s), giving 45.18%. Both calculations use the same original machine cohort, input, RRG, seed, binary and stage timers. Both omit packing, placement and RR generation. Process includes reading the RR XML (median 49.96 s), loading the circuit, packed netlist and placement, initialization, routing, checking, STA and output. Some internal native timers nest. Adding them can double count. Independent readback increases workflow time and falls outside Process.

Each row of motivation_raw.csv links the native log, its SHA, and elapsed Process from its adjacent measurement.json. Report figures for a fixed-input routing evaluation. Architecture exploration as a whole was never timed here.
