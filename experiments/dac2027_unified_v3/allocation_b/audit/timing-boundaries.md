# Fixed-input GEMM timing denominators

The figure adds the separate medians of construction (148.83 s, repeat 2) and routing (30.57 s, repeat 0). Their sum is 179.40 s. Construction is 82.9599% of this sum, which rounds to 83.0% at one decimal. The supplied 82.9% truncates the result.

The introduction uses the mean of three construction observations (149.5633 s) over mean measured Process (331.0480 s), giving 45.18%. Both calculations use the same original machine cohort, input, RRG, seed, binary and stage timers. Both omit packing, placement and RR generation. Process includes reading the RR XML (median 49.96 s), loading the circuit, packed netlist and placement, initialization, routing, checking, STA and output. Some internal native timers nest. Adding them can double count. Independent readback increases workflow time and falls outside Process.

Each row of the parent audit/motivation_raw.csv links the native log, its SHA, and elapsed Process from its adjacent measurement.json. Report figures for a fixed-input routing evaluation. Architecture exploration as a whole was never timed here.

## Reservation B fixed-input GEMM

All three Stock formal processes on worker B reached native exit and emitted a route. Their mean high-resolution construction time was 140.18 s and their mean Process was 300.61 s. The construction share for the stacked mean-duration figure is 46.63%. The lengths of the other segments are 44.76 s for RR XML loading, 26.78 s for routing and 88.89 s for the rest of Process. The last segment is obtained by subtraction. It includes initialization, checking, STA and serialization. RR XML loading and routing use the original internal stage timers.

The new figure draws every component from the same three complete processes. The workload, width, seed and full RR XML are bound in the input manifest. Historical observations have separate denominators and remain outside the primary timing table. Packing, placement, RRG generation and independent route readback fall outside the present fixed-input measurement.

| Repeat | E2 (s) | Process (s) | E2 / Process |
|---:|---:|---:|---:|
| 0 | 138.849233 | 298.486009 | 46.518% |
| 1 | 140.992564 | 302.578573 | 46.597% |
| 2 | 140.705118 | 300.764921 | 46.782% |
