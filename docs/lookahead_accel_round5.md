# Lookahead acceleration: round five

Base `fa07aefc86932e4b2da73d4d934b05836b673bdf`; independent branch
`accel/lookahead-round5-20261109`. Main is not merged. Historical archives and
untracked execution guidance remain unchanged.

The finite-context closed-loop prototype completes the original native batches
with exact maps and operation counts. It exposes staged heap feedback and
cross-qid HLS iteration overlap, but it does **not** meet the C1 CPU budget.
The shared micro-operation dispatcher still serializes too much work. No new
candidate is submitted to OOC; no new implemented frequency or FPGA seconds are
claimed. `board_measured=false`. Fourth-round 125 MHz results remain frozen
controls and are not called Fmax.

## Scope, task supply and representation

The primary metric is one real complete native sample batch, warm E1. It includes
label/output reset, search, writeout and completion synchronization. Static graph
loading and input-only target preparation are separate. Native complete lookahead
E2, RRG construction, and host-to-device service are distinct unmeasured ranges.
Native E2 is never divided by FPGA E1.

All inputs preserve the original full native global sample list and CSR edge
order. Existing 3×3/4×4/5×5/tseng/BNN exports were located and SHA-256 checked
against fourth-round worker manifests. The large files were not copied or
regenerated. New complete Hecate graphs are 6×6, 8×8, and 6×6 with the existing
single-layer Hecate architecture already used by
`prepare_native_cpu_arch_cases.py`. The extension `la_accel_native5.py` accepts
that existing XML explicitly; it adds no synthetic layer or sample generator.
8×8 was declared held out before kernel tuning; 5×5 is a regression input.
6×6 and 8×8 exceed N4096 and remain software-only. No 12×12 scan occurred.

No sustained application arrival stream of distinct topology/cost versions was
found in the inspected manifests and experiment drivers. The new area/layer
points are an experiment sweep, not evidence of repeated application demand.
Identical graph/cost/mapping inputs can reuse lookahead. Accordingly true
multi-build throughput and saturation microbenchmarks are **unmeasured**; neither
is used to replace single-build latency. Seven-qid replication appears only in
semantic unit tests, never in formal performance workloads.

No eligible-CSR compression or cost predecode is used in the formal candidate.
All backends receive the same original representation. Thus actual edge-memory
reads equal original logical edge visits. The separate `static_eligible_candidates`
field records eligible candidates before expanded filtering; it is not compressed
memory traffic. The legacy profiler field `actual_candidates` has this same
explicit meaning. Preparation is separately measured, with no golden-data prepass.

## Measured workload profile

These are C++ logical counts, **measured**, not FPGA cycles. Full and early modes
are profiled per qid; this table shows early mode. Small graphs have event traces;
large graphs have bounded per-qid aggregates and depth histograms, not hundreds
of millions of text rows. Node layers were read once from existing native XML,
then the actual search/counting ran in C++.

| Input | N / E / J / G | Pops / pushes | Original edge reads / eligible candidates | Peak heap | Cross-layer edge visits |
|---|---|---|---|---:|---:|
| native_d3_w8 | 654 / 1,570 / 8 / 10 | 583 / 1,902 | 2,259 / 2,136 | 268 | 712 |
| native_d4_w8 | 1,592 / 4,176 / 12 / 10 | 4,234 / 9,576 | 16,102 / 14,917 | 683 | 4,992 |
| native_d5_w8 | 2,862 / 7,922 / 12 / 10 | 9,348 / 19,094 | 38,258 / 35,285 | 1,248 | 11,962 |
| native_d6_w8 | 4,464 / 12,808 / 12 / 10 | 14,053 / 26,230 | 55,735 / 49,333 | 1,772 | 16,516 |
| native_d8_w8 | 8,664 / 26,000 / 12 / 10 | 38,241 / 57,645 | 175,326 / 157,727 | 3,099 | 51,016 |
| native_d6_w8_l1 | 2,188 / 3,688 / 4 / 4 | 425 / 809 | 1,172 / 821 | 169 | 0 |
| tseng_export | 93,276 / 860,020 / 8 / 2 | 1,531,278 / 1,544,244 | 6,001,551 / 5,782,726 | 33,613 | 0 |
| bnn_export | 4,102,608 / 39,480,616 / 40 / 10 | 272,531,146 / 272,826,780 | 1,327,099,655 / 1,282,443,890 | 607,409 | 94,581,342 |

Increasing area from 5×5 to 8×8 leaves J=12; the layer variation has J=4. The
measured task supply does not justify assuming unlimited independent searches.
Per-qid provenance includes source/group/ordinal/layer/segment/channel, target
coverage, last target completion pop, queue depth distribution, push/pop levels,
FP32 additions, label reads/commits, resets, outputs and cross-layer pushes.
Unreachable target completion remains null; no precomputed reachability removes
those targets. Graph/cell/dynamic safe-capacity byte estimates accompany N/E/J/G.
CPU cycle attribution and scheduler waits are unknown where not instrumented.

## Matched measured software

The three new complete graphs use unchanged round-four early CPU/CUDA sources.
One H100 80GB worker, Xeon Platinum 8462Y+, CUDA 12.8, eight/ten physical core
controls on one NUMA node; `cpu.max=1000000 100000` permits ten CPU core-seconds
per second. The driver selects distinct physical cores within affinity and quota,
not all 128 logical CPUs. CPU1/2/4/8/10 are tested where J permits; J=4 tests
1/2/4. GPU launches one 128-thread CTA per real qid. CPU/GPU timing runs sequentially
on this worker, without a concurrent formal performance task.

Five fresh processes per configuration, each one cold and five warm calls, give
80 processes / 480 checked calls. The estimator is the median of process warm
medians, with their min/max range. Map validation and trace output are outside E1;
mandatory per-call reset, output and synchronization stay inside. Cold CUDA
includes first-kernel runtime startup and is not matched to FPGA device-memory
load-and-run. There is no CPU fallback in the CUDA measurement.

| New input / configuration | Cold E1 μs | Warm E1 μs, median [process range] | Total preparation μs / target preparation μs |
|---|---:|---|---|
| native_d6_w8 / cpu8 | 599.248 | 337.519 [329.083, 359.047] | 135.864 / 48.024 |
| native_d6_w8 / cpu10 | 590.364 | 321.558 [307.539, 332.892] | 148.454 / 48.290 |
| native_d6_w8 / cuda12 | 77,180.801 | 4,815.680 [4,810.976, 4,818.336] | 434,363.804 / 51.006 |
| native_d6_w8_l1 / cpu4 | 127.898 | 17.245 [15.547, 18.767] | 32.972 / 13.337 |
| native_d6_w8_l1 / cuda4 | 72,381.859 | 342.720 [342.496, 343.104] | 423,346.960 / 15.972 |
| native_d8_w8 / cpu8 | 1,307.493 | 877.427 [875.213, 1,124.155] | 263.493 / 90.398 |
| native_d8_w8 / cpu10 | 1,133.246 | 829.097 [773.583, 845.983] | 278.866 / 86.560 |
| native_d8_w8 / cuda12 | 85,205.917 | 12,846.496 [12,791.296, 12,919.264] | 428,891.664 / 92.866 |

Old input/software configurations retain fourth-round measured CPU8 and CUDA
results, plus the previous best tested CPU count. No representation/algorithm
change requires rerunning the old 996 calls. Large tseng/BNN profiling is not a
replacement timing cohort. CPU/GPU work counts agree with the new C++ profiles.
No exclusive physical CPU ownership is claimed.

## Finite-context model and calibration

`la_accel_model5.py` replays the actual per-qid small-graph event order. It is a
bounded screening model, not a general simulator. It limits live qids to 2/4,
edge lanes to 1/2, PQ service partitions to 1/2 and never exceeds native J.
A qid waits for its enqueue feedback before advancing its CSR ordinal or parent.
PQ partitions are held through feedback; bank/partition conflicts cause explicit
waiting. One edge pipe accepts at II1 with 7-cycle eligible / 3-cycle discard
feedback, representing metadata, FP32, labels and commit. Heap read/compare/write
costs three stages per measured traversed level plus fixed launch/finish.
Reset, output and drain are added; graph reload is not silently overlapped.
These latency choices are **model-estimated assumptions**, not measurements.

The fixed serial approximation uses measured heap levels and operation counts:
`reset + 2*heap_levels + 8*pops + 4*pushes + 6*edges + output`.
It underestimates old single-engine RTL by 20.8–25.6% across full/early 3×3/4×4/5×5.
This reproduces operation counts and cycle scale, not cycle-exact scheduling.
No fit to the held-out input is used. The model does not include the new global
map read-modify-write recurrence; synthesis/RTL refinement accounts for it.
The model table contains 48 bounded candidates. None is labeled RTL time.

## Closed-loop mechanism and correctness

The initial prototype has two active qids, one candidate lane and shared readonly
graph memories; the same structure with four contexts is the mechanism control.
Each context retains qid and original edge ordinal, an explicit phase/wait table,
heap, labels, parent/candidate token and statistics. Heap RAM read, select and
write are separate phases. A parent enters CSR only after its exact pop restores
the heap; its next pop waits for every necessary ordered push. Duplicate dst uses
one-uncommitted-neighbor-per-qid stalling. SINK truncation and early termination
have no speculative suffix to cancel. Context assignment preserves original qid
output placement, and FINISH precedes slot reuse. Numerical admission, sequential
RN FP32 adds, right-child ties and both old semantic modes remain unchanged.

This is a shared micro-operation pipeline with cross-qid iteration overlap, not
an implemented network of independently firing CSR/heap/FP32 stage queues.
Neighbors of the same qid are deliberately serialized. The prototype establishes
a correct feedback/interlock control, but does not deliver one edge every cycle.
No unsupported DEPENDENCE false or unlimited RAM ports are assumed.

Each context allocates the safe E+1 complete 96-bit heap, split into even/odd
BRAM banks with two ports, N 32-bit labels and N expanded bits. Row/node/edge/cost
memories are shared. All real-qid cell mappings and outputs are resident. Native
maps/statistics pass for complete 3×3/4×4/5×5 batches, changed graphs and repeated
warm external-cost poisoning. No external graph miss path exists in search.

The 509 existing corner/random fixtures additionally run with seven interleaved
semantic-only qids. A host instrumented source copy verifies complete heap
arrangement after every push/pop and exact popped entries in full and early
modes. Oversize reload invalidates residency. CTest passes 21/21 tests. These are
functional measurements; their wall time is never FPGA time.

## Schedule, RTL scope and stop gate

Both 2/4-context HLS schedules request DISPATCH II1 and achieve **II3, depth5**.
The raw HLS 200-880 warning identifies shared output-map read/modify/write
recurrence, not graph AXI bandwidth. The schedule has map RAM reads across ST3/4;
FP32 adds span ST2–ST5, with arithmetic core II1 and latency3. Metadata BRAM
latency is one. Local operator II1 does not imply whole-edge or whole-pop II1.
The detailed schedule and generated dispatcher RTL are archived.

| Contexts | HLS estimated BRAM18 / DSP / FF / LUT | 3×3 / 4×4 / 5×5 logical dispatcher visits | New post-route frequency |
|---|---|---|---|
| 2 | 351 / 2 / 32,992 / 47,027 | 42,417 / 276,528 / 612,675 | unmeasured |
| 4 | 597 / 2 / 34,211 / 47,165 | 52,822 / 323,051 / 649,533 | unmeasured |

These resource figures are HLS estimates, not implementation utilization. The
same 3×3 CPU budget is only 3,239 cycles at the frozen old 125 MHz reference.
Even ideal II1 needs 1.636 GHz for the two-context 3×3 candidate; larger regression
inputs need 2.186/2.896 GHz. These are conditional required-frequency calculations,
not Fmax predictions. Thus no OOC or 8/12-context expansion has budget support.
Increasing context count adds private state but not micro-operation bandwidth.
Splitting the map recurrence alone could at most change II3 to II1 while leaving
the large state-visit count; it is insufficient to reach C1.

Initial cosim failed before RTL due to the host's `DEBUG=release` leaking into
HLS Makefile compiler flags. The driver now removes that unrelated variable;
original logs remain. Fresh three-graph runs entered RTL but were stopped by the
scope gate. Their partial results are not called PASS. Isolated 3×3 probes reuse
identical synthesized RTL (hashes checked) and execute load-and-run, two warm
calls and load-only. Wider graph functionality is host/csim evidence only.

Both bounded probes and both external observer replays pass all four transactions.
Observer cycle counts equal the original cosim counts exactly. Warm graph AXI
requests are zero; all 216 output requests receive responses before completion.
Output/stats/diagnostics total 2,048 bytes. All output and status traces match.
The observer counts every retired phase and matches all Csim counters exactly.

| 3×3 complete batch | Warm cycles (RTL-derived) | First device-memory call / load-only cycles | Actual dispatch gap | Pop feedback mean [min,max] | Push feedback mean [min,max] |
|---|---:|---|---:|---|---|
| 2 contexts | 128,468 | 143,908 / 15,394 | 3 cycles | 143.403 [6,210] | 26.601 [18,78] |
| 4 contexts | 159,683 | 175,123 / 15,394 | 3 cycles | 286.806 [12,420] | 53.203 [36,156] |

Feedback is observer-measured POP_READ→PARENT and COMMIT→ADVANCE for the same
qid, including round-robin waits. Push feedback excludes six source seeds.
Both modes perform 583 pops, 1,902 pushes and 2,259 original edge reads. Dispatch
II=3 is not a pop service interval. The 2-context complete batch delivers
0.01934 heap operations/cycle and 0.01758 original edges/cycle. No ops/s rate is
assigned without an implemented clock.

Two live pipeline iterations overlap for 84,834 / 105,644 cycles. This confirms
iteration overlap, not concurrent utilization of every intended service stage.
The phase-at-a-time structure has not achieved sustained independent CSR,
FP32/label and heap service. 2→4 contexts leaves all productive phase counts
unchanged; ASSIGN adds two visits and DEAD adds 10,403 visits. DEAD consumes
1.235% / 20.686% of visits. Thus the exact 31,215-cycle regression equals
10,405 extra visits × observed II3. Same-qid feedback also doubles because
round-robin revisits double. This is concrete scheduler/feedback evidence.

The phase visits × II3 schedule refinement predicts 127,251 / 158,466 search
cycles. Total measured E1 exceeds that product by 1,217 cycles in both cases;
that residual is not arbitrarily split into reset, output or memory stalls.
Reset is already present in the counted phases. The earlier independent-service
model is optimistic relative to this global dispatcher; it must not be presented
as a prediction of the implemented scheduler.

| Single-batch early comparison | CPU measured μs | Basic GPU measured μs | R4 FPGA μs, RTL at verified old 125 MHz | R5 FPGA |
|---|---:|---:|---:|---|
| 3×3 | 25.920 | 357.312 | 189.768 | 128,468 / 159,683 RTL cycles; frequency/time unmeasured |
| 4×4 | 126.522 | 1,632.320 | 990.568 | complete-batch host/csim passed; RTL unmeasured |
| 5×5 | 211.585 | 2,901.952 | 2,107.136 | complete-batch host/csim passed; RTL unmeasured |

Relative to the **old 125 MHz reference cycle budget**, the measured new 3×3
cycles require 39.65× / 49.28× reduction to equal C1 latency. These are budget
ratios, not new FPGA speed measurements. No new clock has passed implementation;
200 MHz remains a synthesis target only. All baseline superiority claims for
the new candidates remain unverified.


The prototype writes 64 diagnostic words (512 bytes) in addition to maps and
statistics. This extra E1 overhead is disclosed; no timing excludes it. Warm
graph traffic and output drain are checked by the external observer. Direct
bank-conflict counters are not implemented; unobserved bank stalls remain
unknown, not assigned zero or inferred from residual runtime.

## Conclusions, remaining scope and reproduction

No fifth-round candidate has demonstrated superiority over C1, basic CUDA or
B0/B1. The stopping decision is supported by the finite dispatcher-work budget;
it does not prove all strict hardware architectures impossible. B0/B1 same-scope
E1 awaits a candidate approaching C1. Native E2, physical device frequency,
board performance, 8×8 hardware and genuine multi-build throughput are unmeasured.

The next useful change is replacing the shared phase-at-a-time dispatcher with
independently scheduled finite heap/edge/commit services, shortening per-edge
feedback while preserving ordered commit and RAW forwarding. It requires a new
budgeted prototype, not merely more copies/contexts, cache sizes or a clock sweep.
No relaxed-priority/canonical semantic substitution or new RRG hotspot study is
performed in this round.

Build host tests with the existing CMake entry and `LA_HLS_INCLUDE` pointing to
Vitis HLS 2022.2/include. `la_accel_hls5.py --help` documents frozen fresh runs;
`--engines` here means context count, not replicated complete engines.
`la_accel_cosim5_probe.py` safely clones a synthesized project into a fresh probe
folder. `la_accel_monitor5.py` runs an observer copy and compares original cycles,
all map/stat/status/metric outputs and AXI completions. Classic 2022.2 Tcl is used;
new unified-IDE skill commands are not silently substituted.

All source/input hashes, commands, return codes and evidence classifications are
in the linked artifacts. The original execute document and auxiliary package
remain untracked. No historical archive is copied to inflate validation counts.

[Machine-readable report](../results/lookahead_accel_round5_20261109T054024Z/evidence_snapshot/report_final.json), [per-qid statistics](../results/lookahead_accel_round5_20261109T054024Z/evidence_snapshot/per_sample_stats.jsonl), [software](../results/lookahead_accel_round5_20261109T054024Z/evidence_snapshot/software_latency_throughput.json), [model](../results/lookahead_accel_round5_20261109T054024Z/evidence_snapshot/model/dependency_service_model.json), [evidence index](../results/lookahead_accel_round5_20261109T054024Z/evidence_snapshot/index.json).
