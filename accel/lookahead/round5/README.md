# Finite-context strict lookahead prototype

`interleave5.cpp` is an independent runtime-loaded, on-chip backend. It shares
one read-only graph and schedules 2 or 4 private dynamic contexts through a
single micro-operation dispatcher. Native qids are assigned in original order
as slots finish; no qid is duplicated. Original output offsets are retained.
It is a mechanism prototype, not a claimed high-throughput edge-per-cycle design.

`search5.hpp` carries qid, original CSR ordinal, parent and candidate in each
context token. The phase table is the readiness/wait table. Heap read, select,
write and control use separate visits. Its exact down-then-up heap retains
right-child tie selection. One uncommitted neighbor per qid is a conservative
RAW interlock; repeated destinations cannot observe stale labels. All pushes of
a parent finish before its next pop. SINK truncation and early completion have
no speculative suffix to flush. Slots are reassigned only after FINISH.

The HLS DISPATCH pipeline can overlap micro-operations from different qids;
it is not a network of independently firing stage FIFOs. Round-robin revisits
and the shared dispatcher remain bottlenecks. Increasing contexts does not
increase total micro-operation issue bandwidth. No DEPENDENCE false is used.
The two FP32 additions (delay and congestion) belong to one candidate lane.

Capacity and admission are inherited from round four: N4096/E16384/J32/C128/K64,
finite nonnegative normal/+0 costs and conservative no-overflow admission. Each
context has E+1 complete 96-bit entries (even/odd dual-port BRAM banks), N 32-bit
labels and N expanded bits. Read-only row/node/edge/cost arrays are shared. Cell
maps for every real qid remain resident; the output RAM is shared by qid offset.
Observed heap peaks do not shrink the safe queue capacity.

Commands 0/1/2 mean load-only/warm/load-and-run. The unchanged loader validates
all runtime inputs, invalidates old contents on failed reload, and never reads
external graph arrays during warm search. Warm E1 contains reset, complete
search, map/statistics writeout and 64 diagnostic words. Diagnostics add 512
bytes versus round four; this is explicitly retained as prototype overhead.
Preparation and host service latency are separate ranges. Load-only does not
write metrics. Status must be checked before consuming results.

`LA4_EARLY=0/1` selects the unchanged STRICT_FULL_FLOOD or
MAP_EQUIVALENT_EARLY_STOP contract. The profiler and CPU/CUDA use the original
CSR representation. There is no eligible-CSR compression in this candidate:
`original_edges` is also the actual edge-memory reads; profiler
`actual_candidates` counts static-eligible candidates before expanded filtering,
not compressed memory traffic. Target preparation is input-only, outside warm
E1; seen/output and label reset remain inside E1.

Diagnostic words 0..23 count retired state visits in Phase order; 31 is total
visits; 32 sums heap-store feedback in dispatcher visits; 33 counts heap stores.
These are logical counters until cross-checked against RTL. Do not call one
visit one FPGA cycle. The external RTL observer measures actual issue intervals,
feedback and simultaneous pipeline iteration occupancy, and verifies AXI drain.

`mechanism_tests5.cpp` creates seven qids from semantic fixtures only to test
interleaving. This is never a formal performance workload. `la_accel_heap_audit5.py`
instruments an exact source copy to compare the entire heap arrangement after
every completed push/pop with the original strict heap. It is host correctness
only. The native testbench checks complete maps and every reference statistic,
loads three graphs and poisons external costs during repeated warm calls.
