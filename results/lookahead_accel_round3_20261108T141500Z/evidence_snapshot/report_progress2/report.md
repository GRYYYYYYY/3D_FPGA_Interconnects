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
| tiny_native | cpu | 1 | 54.369 | 28.632 | 58.629 |
| tiny_native | cpu | 2 | 97.152 | 38.180 | 104.527 |
| tiny_native | cpu | 4 | 143.971 | 21.642 | 159.497 |
| tiny_native | cuda | 4 | 42352.192 | 360.416 | 452800.036 |

Five fresh processes per configuration. Cold is the first measured kernel invocation, with no warmup. Warm is the median of five subsequent complete batches per process, then the median over five processes. Allocations/uploads persist within a process; labels, queue counts and outputs reset inside every E1. Cold service adds preparation and compact readback, excludes workload file I/O and golden comparison, and is not full native E2. CUDA first E1 includes first-launch/lazy-module overhead between the event timestamps. CPU is the independent compact-CSR std::priority_queue/OpenMP baseline, not a substituted native-builder E2 measurement.

## Complete native workloads: functional RTL and OOC implementation

| Core | Workload SHA prefix | Functional cycles | Routed setup / hold ns | Verified MHz | LUT / FF / DSP / BRAM18 |
|---|---|---:|---|---:|---|
| hls_dual | 50b8cedc8f36 | 630600 | not completed | — | — / — / — / — |
| hls_packed_wb | 50b8cedc8f36 | 1216708 | not completed | — | — / — / — / — |
| hls_packed_wt | 50b8cedc8f36 | 1196996 | not completed | — | — / — / — / — |
| hls_single | 50b8cedc8f36 | 1260676 | +0.441 / +0.019 | 200.0 | 27154 / 31004 / 4 / 49 |
| hls_single_family | 50b8cedc8f36 | 1260676 | not completed | — | — / — / — / — |

No time is derived at the target frequency when routed setup/hold fails. Verified MHz is the timing-clean implementation target, not an inferred fmax; core OOC does not establish shell or board timing.

## Bounded synthetic memory

| Run | Status | Cycles | RTL time at verified OOC period, ms | Cycles needed to beat strongest measured warm E1 |
|---|---|---:|---:|---:|
| bounded_single | passed | 4483179 | 22.415895 | 12343 |

## Controlled comparisons

| Change | Baseline → candidate | Matching input/cache/memory controls | Time speedup at verified frequencies |
|---|---|---|---:|

## Memory traffic and engine overlap

| Run | Port | Data bits | Read / write requests | Read / write beats | Peak reads / writes |
|---|---|---:|---|---|---|
| bounded_single | graph | see RTL | 19796 / 0 | 19796 / 0 | 2 / 0 |
| bounded_single | queue | see RTL | 15759 / 11091 | 15759 / 11091 | 2 / 2 |
| bounded_single | result | see RTL | 576 / 728 | 576 / 732 | 1 / 2 |
| bounded_single | state | see RTL | 8390 / 14996 | 8390 / 14996 | 2 / 2 |

bounded_single: total peak outstanding R/W = 2/4; shared bank slot utilization = 6.37%; post-completion drain = 0 cycles.

Primary controls: 64-cycle minimum request latency; one shared bank; one R/W native beat every four clocks; two outstanding requests per direction per port; fixed global pools of eight read and eight write credits. A held address reserves a global credit. Each return port has one finite skid slot. Port widths, actual peak outstanding, stalls, beat counts and engine overlap are retained in JSON. This is a synthetic sensitivity model, not measured HBM.

At 200 MHz the shared bank supplies at most 50 million native beats/s (at most 3.2 GB/s for exclusively 512-bit beats); effective transferred bytes depend on each recorded port width and byte strobes. Replication does not increase this beat budget or the global credit pools. E1 adds any post-completion drain recorded by the model.

The cycle budget uses the strongest warm CPU/CUDA configuration actually measured on this exact workload. It is a necessary target for this cohort, not evidence of superiority over every original/native software implementation. FPGA large-graph prediction and complete lookahead E2 remain outside this phase.
