# Lookahead round 3 — matched resident experiments

Goal remains unverified. CPU wall times, CUDA event times, and RTL cycle-derived times are identified separately. C simulation host elapsed time is never a hardware timing datum.

## Measured software E1

| Workload | Backend | Workers / CTAs | Cold first E1 μs | Warm E1 μs | Cold service μs |
|---|---|---:|---:|---:|---:|
| native_d3_w8 | cpu | 1 | 171.651 | 139.436 | 175.932 |
| native_d3_w8 | cpu | 2 | 222.075 | 148.671 | 228.515 |
| native_d3_w8 | cpu | 4 | 199.724 | 61.716 | 209.252 |
| native_d3_w8 | cpu | 8 | 268.275 | 68.033 | 285.935 |
| native_d3_w8 | cuda | 8 | 42937.183 | 917.024 | 508434.194 |
| native_d4_w8 | cpu | 1 | 871.871 | 813.733 | 877.866 |
| native_d4_w8 | cpu | 2 | 500.773 | 416.775 | 512.142 |
| native_d4_w8 | cpu | 4 | 499.213 | 377.890 | 518.266 |
| native_d4_w8 | cpu | 8 | 418.675 | 201.099 | 449.823 |
| native_d4_w8 | cuda | 12 | 43632.961 | 2425.664 | 433336.252 |
| tiny_native | cpu | 1 | 54.369 | 28.632 | 58.629 |
| tiny_native | cpu | 2 | 97.152 | 38.180 | 104.527 |
| tiny_native | cpu | 4 | 143.971 | 21.642 | 159.497 |
| tiny_native | cuda | 4 | 42352.192 | 360.416 | 452800.036 |

Five fresh processes per configuration. Cold is the first measured kernel invocation, with no warmup. Warm is the median of five subsequent complete batches per process, then the median over five processes. Allocations/uploads persist within a process; labels, queue counts and outputs reset inside every E1. Cold service adds preparation and compact readback, excludes workload file I/O and golden comparison, and is not full native E2. CUDA first E1 includes first-launch/lazy-module overhead between the event timestamps. CPU is the independent compact-CSR std::priority_queue/OpenMP baseline, not a substituted native-builder E2 measurement.

## Complete native workloads: functional RTL and OOC implementation

| Core | Workload SHA prefix | Functional cycles | Routed setup / hold ns | Verified MHz | LUT / FF / DSP / BRAM18 |
|---|---|---:|---|---:|---|
| hls_dual | 50b8cedc8f36 | 630600 | +0.562 / +0.019 | 200.0 | 53367 / 61100 / 8 / 98 |
| hls_dual_d4 | d28970a7ec64 | 3488728 | +0.562 / +0.019 | 200.0 | 53367 / 61100 / 8 / 98 |
| hls_packed_wb | 50b8cedc8f36 | 1216708 | +0.265 / +0.009 | 200.0 | 25549 / 30869 / 4 / 51 |
| hls_packed_wt | 50b8cedc8f36 | 1196996 | +0.364 / +0.020 | 200.0 | 25498 / 30449 / 4 / 51 |
| hls_quad | 50b8cedc8f36 | 418606 | +0.010 / +0.019 | 200.0 | 105529 / 122163 / 16 / 196 |
| hls_quad_d4 | d28970a7ec64 | 1799906 | not completed | — | — / — / — / — |
| hls_single | 50b8cedc8f36 | 1260676 | +0.441 / +0.019 | 200.0 | 27154 / 31004 / 4 / 49 |
| hls_single_family | 50b8cedc8f36 | 1260676 | +0.569 / +0.023 | 200.0 | 26854 / 31327 / 4 / 49 |

No time is derived at the target frequency when routed setup/hold fails. Verified MHz is the timing-clean implementation target, not an inferred fmax; core OOC does not establish shell or board timing.

## Bounded synthetic memory

| Run | Status | Cycles | RTL time at verified OOC period, ms | Cycles needed to beat strongest measured warm E1 |
|---|---|---:|---:|---:|
| bounded_dual | passed | 2247992 | 11.239960 | 12343 |
| bounded_packed_wb | passed | 4018356 | 20.091780 | 12343 |
| bounded_packed_wt | passed | 3971796 | 19.858980 | 12343 |
| bounded_quad | passed | 1481556 | 7.407780 | 12343 |
| bounded_single | passed | 4483179 | 22.415895 | 12343 |
| bounded_single_family | passed | 4483179 | 22.415895 | 12343 |

## Controlled comparisons

| Change | Baseline → candidate | Matching input/cache/memory controls | Time speedup at verified frequencies |
|---|---|---|---:|
| replicated resident engines | bounded_single_family → bounded_dual | True | 1.9943x |
| packed-label layout | bounded_single_family → bounded_packed_wt | True | 1.1288x |
| label write-back policy | bounded_packed_wt → bounded_packed_wb | True | 0.9884x |
| four-engine scaling | bounded_dual → bounded_quad | True | 1.5173x |

## Memory traffic and engine overlap

| Run | Port | Data bits | Read / write requests | Read / write beats | Peak reads / writes |
|---|---|---:|---|---|---|
| bounded_dual | graph0 | 256 | 9900 / 0 | 9900 / 0 | 2 / 0 |
| bounded_dual | graph1 | 256 | 9900 / 0 | 9900 / 0 | 2 / 0 |
| bounded_dual | queue0 | 128 | 7872 / 5541 | 7872 / 5541 | 2 / 2 |
| bounded_dual | queue1 | 128 | 7887 / 5550 | 7887 / 5550 | 2 / 2 |
| bounded_dual | result0 | 512 | 288 / 364 | 288 / 366 | 1 / 2 |
| bounded_dual | result1 | 512 | 288 / 364 | 288 / 366 | 1 / 2 |
| bounded_dual | state0 | 32 | 4199 / 7498 | 4199 / 7498 | 2 / 2 |
| bounded_dual | state1 | 32 | 4191 / 7498 | 4191 / 7498 | 2 / 2 |
| bounded_packed_wb | graph | 256 | 19796 / 0 | 19796 / 0 | 2 / 0 |
| bounded_packed_wb | queue | 128 | 15759 / 11091 | 15759 / 11091 | 2 / 2 |
| bounded_packed_wb | result | 512 | 576 / 728 | 576 / 732 | 1 / 2 |
| bounded_packed_wb | state | 64 | 4276 / 2968 | 4276 / 7872 | 1 / 2 |
| bounded_packed_wt | graph | 256 | 19796 / 0 | 19796 / 0 | 2 / 0 |
| bounded_packed_wt | queue | 128 | 15759 / 11091 | 15759 / 11091 | 2 / 2 |
| bounded_packed_wt | result | 512 | 576 / 728 | 576 / 732 | 1 / 2 |
| bounded_packed_wt | state | 64 | 4276 / 4860 | 4276 / 9764 | 1 / 2 |
| bounded_quad | graph0 | 256 | 3306 / 0 | 3306 / 0 | 2 / 0 |
| bounded_quad | graph1 | 256 | 6598 / 0 | 6598 / 0 | 2 / 0 |
| bounded_quad | graph2 | 256 | 3306 / 0 | 3306 / 0 | 2 / 0 |
| bounded_quad | graph3 | 256 | 6598 / 0 | 6598 / 0 | 2 / 0 |
| bounded_quad | queue0 | 128 | 2487 / 1716 | 2487 / 1716 | 2 / 2 |
| bounded_quad | queue1 | 128 | 5385 / 3825 | 5385 / 3825 | 2 / 2 |
| bounded_quad | queue2 | 128 | 2487 / 1716 | 2487 / 1716 | 2 / 2 |
| bounded_quad | queue3 | 128 | 5400 / 3834 | 5400 / 3834 | 2 / 2 |
| bounded_quad | result0 | 512 | 96 / 134 | 96 / 135 | 1 / 2 |
| bounded_quad | result1 | 512 | 192 / 230 | 192 / 231 | 1 / 2 |
| bounded_quad | result2 | 512 | 96 / 134 | 96 / 135 | 1 / 2 |
| bounded_quad | result3 | 512 | 192 / 230 | 192 / 231 | 1 / 2 |
| bounded_quad | state0 | 32 | 1343 / 3377 | 1343 / 3377 | 2 / 2 |
| bounded_quad | state1 | 32 | 2856 / 4121 | 2856 / 4121 | 2 / 2 |
| bounded_quad | state2 | 32 | 1343 / 3377 | 1343 / 3377 | 2 / 2 |
| bounded_quad | state3 | 32 | 2848 / 4121 | 2848 / 4121 | 2 / 2 |
| bounded_single | graph | see RTL | 19796 / 0 | 19796 / 0 | 2 / 0 |
| bounded_single | queue | see RTL | 15759 / 11091 | 15759 / 11091 | 2 / 2 |
| bounded_single | result | see RTL | 576 / 728 | 576 / 732 | 1 / 2 |
| bounded_single | state | see RTL | 8390 / 14996 | 8390 / 14996 | 2 / 2 |
| bounded_single_family | graph | 256 | 19796 / 0 | 19796 / 0 | 2 / 0 |
| bounded_single_family | queue | 128 | 15759 / 11091 | 15759 / 11091 | 2 / 2 |
| bounded_single_family | result | 512 | 576 / 728 | 576 / 732 | 1 / 2 |
| bounded_single_family | state | 32 | 8390 / 14996 | 8390 / 14996 | 2 / 2 |

bounded_dual: total peak outstanding R/W = 4/8; shared bank slot utilization = 12.69%; post-completion drain = 0 cycles.
At least two engines overlap for 2247172 cycles; per-engine active cycles [2247172, 2247718], max/min = 1.000243. Exact first/last activity is retained in JSON.
Each active interval is verified continuous from its observed count and endpoints: all engines overlap for 2247172 cycles; average active engines = 1.9995, finish spread = 546 cycles. Pairwise intersections are derived from these RTL intervals in JSON.
With these observed beat counts unchanged, bank service alone needs at least 285373 cycles, even with perfect compute overlap. This is a small-input model bound, not a hardware measurement or a large-graph forecast.

bounded_packed_wb: total peak outstanding R/W = 2/3; shared bank slot utilization = 5.98%; post-completion drain = 0 cycles.
With these observed beat counts unchanged, bank service alone needs at least 240405 cycles, even with perfect compute overlap. This is a small-input model bound, not a hardware measurement or a large-graph forecast.

bounded_packed_wt: total peak outstanding R/W = 2/3; shared bank slot utilization = 6.24%; post-completion drain = 0 cycles.
With these observed beat counts unchanged, bank service alone needs at least 247973 cycles, even with perfect compute overlap. This is a small-input model bound, not a hardware measurement or a large-graph forecast.

bounded_quad: total peak outstanding R/W = 8/8; shared bank slot utilization = 19.26%; post-completion drain = 0 cycles.
At least two engines overlap for 1480042 cycles; per-engine active cycles [769435, 1480042, 769703, 1481048], max/min = 1.924851. Exact first/last activity is retained in JSON.
Each active interval is verified continuous from its observed count and endpoints: all engines overlap for 769435 cycles; average active engines = 3.0375, finish spread = 711613 cycles. Pairwise intersections are derived from these RTL intervals in JSON.
With these observed beat counts unchanged, bank service alone needs at least 285405 cycles, even with perfect compute overlap. This is a small-input model bound, not a hardware measurement or a large-graph forecast.

bounded_single: total peak outstanding R/W = 2/4; shared bank slot utilization = 6.37%; post-completion drain = 0 cycles.
With these observed beat counts unchanged, bank service alone needs at least 285357 cycles, even with perfect compute overlap. This is a small-input model bound, not a hardware measurement or a large-graph forecast.

bounded_single_family: total peak outstanding R/W = 2/4; shared bank slot utilization = 6.37%; post-completion drain = 0 cycles.
With these observed beat counts unchanged, bank service alone needs at least 285357 cycles, even with perfect compute overlap. This is a small-input model bound, not a hardware measurement or a large-graph forecast.

hls_dual: 8 generated AXI masters provision 128/128 total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.

hls_dual_d4: 8 generated AXI masters provision 128/128 total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.

hls_packed_wb: 4 generated AXI masters provision 64/64 total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.

hls_packed_wt: 4 generated AXI masters provision 64/64 total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.

hls_quad: 16 generated AXI masters provision 256/256 total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.

hls_quad_d4: 16 generated AXI masters provision 256/256 total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.

hls_single: 4 generated AXI masters provision 64/64 total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.

hls_single_family: 4 generated AXI masters provision 64/64 total internal read/write outstanding slots. The external bounded model still admits only the fixed global 8/8 requests, with 2/2 per port. Full per-port RTL parameters are retained in JSON.

Primary controls: 64-cycle minimum request latency; one shared bank; one R/W native beat every four clocks; two outstanding requests per direction per port; fixed global pools of eight read and eight write credits. A held address reserves a global credit. Each return port has one finite skid slot. Port widths, actual peak outstanding, stalls, beat counts and engine overlap are retained in JSON. This is a synthetic sensitivity model, not measured HBM.

At 200 MHz the shared bank supplies at most 50 million native beats/s (at most 3.2 GB/s for exclusively 512-bit beats); effective transferred bytes depend on each recorded port width and byte strobes. Replication does not increase this beat budget or the global credit pools. E1 adds any post-completion drain recorded by the model.

Engine overlap measures deasserted ap_idle intervals and includes AXI waits. It proves concurrent in-flight searches, not simultaneous useful arithmetic on every counted cycle.

The cycle budget uses the strongest warm CPU/CUDA configuration actually measured on this exact workload. It is a necessary target for this cohort, not evidence of superiority over every original/native software implementation. FPGA large-graph prediction and complete lookahead E2 remain outside this phase.
