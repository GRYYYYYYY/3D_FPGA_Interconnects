# R6: ALT bucket algorithm screen

Base commit: `ab0a4afce89c567cf30f24c8a813d78884872f05`.
Branch: `accel/lookahead-round6-screen-20261109`.
Evidence root: `results/lookahead_accel_round6_20261109T150000Z`.
**Decision: retain the alternative software algorithm; no-go for the screened
16-lane FPGA candidate.** Functional and limited native QoR gates pass, but the
measured coarse-bucket GPU beats even its optimistic edge-only throughput bound.

This round adds a separate ALT contract and software evidence. STRICT, its
old golden maps, main, historical archives and untracked task documents are
unchanged. No new HLS, RTL, OOC or blocking heap replication was launched.

## Scheduling erratum

The R5.1 model required the round-robin commit issue turn for both issuance and
retirement. Archived directed RTL accepts same-qid PUSHes at
406,414,422,430,438,454,462,470,478,486,494. Retirement should not consume a second
issue slot. The analysis-only replacement reproduces old values, then obtains
59,519→55,726; 377,587→329,634; 817,497→701,500 cycles. These are conditional
native model values, not measured native RTL. Existing zero/hold observer traces
retain finite FIFO occupancy ≤4, ordered PUSH ordinals, parent RAW/barrier checks,
operation enqueue/start/retire/feedback ordering and full draining. The supported
calibration scope is issue/retire separation only; deep-heap extrapolation,
reset/feedback coupling and complete native timing remain uncalibrated.

The old 59,519→54,030 comparison mixes PUSH/interface contracts and is not a
Floyd-only batch result. The task-package D-contract POP-only conditional point is 57,623.
The isolated 45-POP 967→861 result remains separate. R4 remains the measured
hardware baseline; no new frequency, FPGA microseconds or board result exists.

## Alternative algorithm and functional evidence

[Contract and implementation](../accel/lookahead/round6/README.md) define
ALT_BUCKET_FP32_V1 with fixed shifts 0 and 20. Delay is never quantized; shifted
bits only determine priority. Each wave reads committed snapshots, reduces whole
(delay,congestion) pairs, commits strict improvements, permits same-bucket
reopening and stops only after target closure. Source identity, input target
sets, original CSR order/SINK truncation, native sample merge order and native
interpolation remain intact. This is not a proof of global lexicographic path
optimality under FP32 rounding.

All six real small graphs and 509 archived fixtures pass C++/Python byte
comparison for both shifts (1,030 configurations), including immutable path
version checks recomputing every chosen edge addition and tying each output to
an IPIN version in its target cell. Six real small maps match old golden bytes.
Eight fixtures differ in exactly one congestion word each for each shift:
random_27,152,291,312,332,352,358,445. Delay and missing state have zero differences.
All failures/counterexamples remain. Twenty-one additional lifecycle/error
checks cover zero cycles, unreachable/empty targets, empty batch, truncated
input, numeric rejection/overflow and resource exhaustion without partial maps.

## Complete larger inputs

Both shifts complete all eight tseng and all forty BNN samples, with repeat
output equality. These are complete exports, not sampled old-HLS-sized graphs.
The original input paths/hashes are reused. tseng matches old golden bytes.
BNN has zero delay/missing differences and **133,798 congestion word differences**
for each shift across 819,544 covered cells. BNN therefore belongs exclusively
to the alternative semantic track.

| Complete batch | shift | raw edges | eligible edges | total waves | max qid waves | work-weighted frontier | peak active buckets | peak pending members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tseng | 0 | 6,002,438 | 5,782,726 | 224 | 30 | 5,416 | 2 | 11,847 |
| tseng | 20 | 6,022,458 | 5,802,746 | 192 | 25 | 6,678 | 2 | 11,847 |
| BNN | 0 | 1,327,111,961 | 1,282,443,890 | 19,691 | 627 | 16,061 | 36 | 217,230 |
| BNN | 20 | 1,331,605,857 | 1,286,937,147 | 2,161 | 59 | 106,780 | 6 | 214,711 |

Width is weighted by eligible edge work, not max frontier. Full per-qid wave
arrays, width/edge histograms, repeated node processing, updates, directory
operations, stale/migration/dedup counts and bank/destination conflicts are in
`profile_summary.json` and the raw profiles. BNN same-destination duplicate
candidate counts are 740,528,191 / 951,170,650; maximum wave fan-in is 67 / 68.
A simple dst%16 bank assignment inflates sum-of-wave bank service over uniform
ideal by 1.04684 / 1.02719. This aggregate is not a measured bank port schedule.
Shift 20 records 5,886 migrations/stale entries and 1,284,087 deduplications.
The CPU performs about 102.7M / 102.9M directory insertion lookups; directory
selection and balanced tree operations cannot be replaced by free hardware.
No radix redistribution is implemented or credited.

The BNN original export is roughly 1.1 GB, including 656,417,280 bytes of source
cell mapping. Labels alone require 32,820,864 bytes per qid. Fixed software
scratch reserves approximately 58*N bytes per worker, plus dynamic directory and
members. Input/preparation, peak RSS and capacity limits are recorded separately.
These observations cannot establish safe hardware capacities from small graphs.

## Matched timing, native qualification and decision

All 186 predeclared process/configuration runs passed. CPU/CUDA outputs match
for all 509 fixtures, six small real graphs and complete tseng/BNN batches in
both shifts. Timings use the same H100 worker, 8 distinct physical cores in one
NUMA pool, no concurrent solver timing, and the best tested legal CPU thread
count. Each entry is the median of three process medians, each from three warm
complete batches. Repeats are timing samples, not additional application jobs.

| Input | shift | CPU threads | CPU E1 µs | basic CUDA E1 µs |
|---|---:|---:|---:|---:|
| bnn_export | 0 | 8 | 7304299.887 | 2830302.942 |
| bnn_export | 20 | 8 | 7065944.795 | 314170.320 |
| native_d3_w8 | 0 | 8 | 15.201 | 329.576 |
| native_d3_w8 | 20 | 8 | 17.034 | 328.615 |
| native_d4_w8 | 0 | 8 | 53.550 | 520.441 |
| native_d4_w8 | 20 | 8 | 54.643 | 497.650 |
| native_d5_w8 | 0 | 8 | 108.198 | 575.304 |
| native_d5_w8 | 20 | 8 | 108.774 | 489.227 |
| native_d6_w8 | 0 | 8 | 146.659 | 626.501 |
| native_d6_w8 | 20 | 8 | 160.748 | 550.346 |
| native_d6_w8_l1 | 0 | 4 | 15.049 | 355.796 |
| native_d6_w8_l1 | 20 | 4 | 15.624 | 357.155 |
| native_d8_w8 | 0 | 8 | 392.245 | 1087.300 |
| native_d8_w8 | 20 | 8 | 374.145 | 735.610 |
| tseng_export | 0 | 8 | 13485.117 | 2148.995 |
| tseng_export | 20 | 8 | 13692.755 | 1812.717 |

All thread configurations and process-median ranges are retained in
`matched_timing.json`; no historical host timings enter these ratios. First-call
E1, file load and preparation are separate in each raw row. Cold means first
call in a fresh process, not flushed filesystem caches. Witnesses and work
profiling are disabled during this matrix.

| Complete larger input | shift | CPU load / prepare / first E1 s | CUDA load / prepare / first E1 s |
|---|---:|---:|---:|
| bnn_export | 0 | 0.798511 / 0.844623 / 7.430051 | 0.812800 / 0.856953 / 2.883211 |
| bnn_export | 20 | 0.798798 / 0.834912 / 7.141659 | 0.788409 / 0.804315 / 0.361014 |
| tseng_export | 0 | 0.012819 / 0.014830 / 0.018075 | 0.007834 / 0.404552 / 0.049404 |
| tseng_export | 20 | 0.007507 / 0.014801 / 0.014984 | 0.008116 / 0.403251 / 0.049117 |

The live native entry is default-off and requires both the explicit ALT mode and
the R6 shared library. The successful qualification uses the existing R2
`native_live_build_v2` executable and checks for exactly one `LA_LIVE` record.
The first attempted executable was export/import-only and did not dispatch ALT;
those results are explicitly invalidated and excluded. Its oversized DLA control
also exhausted a 600-second limit; that failure and the stopped dependent arm
are retained. The required smaller dual-layer circuit is frozen s38417 seed1.

| Live shift=0 prescreen | control → ALT CPD ns | control → ALT wirelength | iterations | control / ALT routing s |
|---|---:|---:|---:|---:|
| s38417, dual layer | 6.96051 → 6.96051 | 87,893 → 87,893 | 68 / 68 | 7.28 / 6.65 |
| BNN, 3D | 11.0943 → 11.0943 | 1,538,209 → 1,537,866 | 19 / 19 | 14.90 / 15.42 |

Both live pairs pass native FULL, zero final overuse and independent FULL/STA.
The independent executable reads the candidate's own route, with its hash bound
before/after; it does not reroute or substitute the control route. Fixed netlist
and placement hashes are checked. Both CPD and wirelength stay within +5%.
These are **one paired qualification per circuit**, not a repeated native speed
study. Shift20 native routing was not run and does not inherit the shift0 flag.

Final native wire maps are decoded with the frozen generated Cap'n Proto schema:
s38417 has 166 changed congestion words out of 14,400 entries; BNN has 24,434 out
of 451,584. Both have zero delay-word or missing-state differences. This checks
native group merging and interpolation, separately from the offline sample-map
comparison. Both native maps are non-equivalent despite passing this QoR screen.

## Remaining native hotspot

The original eight-core GEMM paper cohort retains 149.563 s stock lookahead,
20.950 s pipeline lookahead and 202.068 s pipeline process means. Halving the
optimized lookahead gives only about 1.055x ideal process speedup. The roughly
49.363 s RR timer is **loading an existing graph**, nested inside 52.030 s Create
Device; it is not RRG generation and these timers must not be added.

The locked local build identifies itself as `9.0.0-dev+unknown`; source/binary
hashes, rather than an invented VTR revision, bind the diagnostic. Its existing
Cap'n Proto `.bin` mmap reader is compiled in (`VTR_ENABLE_CAPNPROTO=ON`). The XML
loader already counts and reserves nodes/edges. Before proposing hardware for
this stage, a same-input binary-format/cache CPU control is still required.

Two bounded one-iteration native diagnostics use an isolated RR-reader object
and leave vendor, frozen executables and their archives unchanged. Both reproduce
the frozen final wire map. Timings below are attribution only, on this host and
these circuits, not the original GEMM cohort. The parser combines filesystem IO,
XML parsing and DOM allocation; those components are **not** individually measured.
The serializer node/edge measurements also include their allocations. OS caches
were not dropped; shared GPFS storage/cache state is uncontrolled. This is not a
cold-storage bandwidth benchmark. Diagnostics and formal CPU/GPU timing run on
different hosts; native qualification wall times are not formal speed statistics.

| RR-load phase (seconds) | tseng, 72.1 MB XML | BNN, 3,385.8 MB XML |
|---|---:|---:|
| File read + XML parse + DOM allocation | 0.41820 | 7.99539 |
| Node decode/construction | 0.10195 | 4.06644 |
| Edge decode/construction | 0.12101 | 5.83967 |
| Edge partition | 0.02453 | 1.54774 |
| Node indices | 0.00655 | 0.20682 |
| Fan-in | 0.00056 | 0.03209 |
| Indexed costs | 0.01236 | 0.70891 |
| RR checks | 0.03024 | 1.45558 |
| Finish-load inclusive subtotal | 0.04978 | 2.40351 |

The last row contains the preceding four finish phases; do not add it again.
Other root/schema work and deallocation remain a residual. Priority is to measure
existing binary loading/cache reuse, then parser/construction allocation and
memory traffic; there is no new “RRG generation accelerator” recommendation.

## Reproduction and evidence boundaries

`la_accel_round6_validate.py` performs the small C++/Python/witness checks;
`la_accel_round6_lifecycle.py` checks errors and exhaustion;
`la_accel_round6_large.py` reuses the full existing exports;
`la_accel_round6_gpu_job.py` freezes source and measures CPU/CUDA sequentially on
one quota-aware physical-core NUMA pool; `la_accel_round6_native.py` performs the
opt-in paired native checks; the RR diagnostic scripts build only a new isolated
CPU attribution executable. `la_accel_round6_report.py` reduces completed results.
No Python/profiling time is used as a platform speed denominator.

CUDA E1 includes reset, dense directory scans, packed-pair reductions, closure,
host completion control, output decoding/readback and synchronization. Its event
timeline includes host gaps and is not a pure kernel-time metric. Individual
kernel/control phases are not separately timed in this screen; they are not
assumed free. CPU E1 uses dense touched proposals and vector members with an
ordered tree directory, O3 and no debug witnesses; tested thread choices and all
negative configurations remain in the timing receipt. Large witnesses are
replayable complete outputs and source/input bindings; exhaustive immutable path
versions are limited to the small corpus.


## Finite hardware screen and stopping decision

The single screened shape is eight source contexts, sixteen FP32 edge lanes,
sixteen dst-modulo label banks, one shared directory update per cycle and external
HBM storage. These are **assumptions**, with a reference 200 MHz/II1 scenario and
100 MHz / lower effective bandwidth sensitivity, not an implemented contract.
For BNN, graph/mapping/output input is 1,078,754,064 bytes; eight label sets need
262,566,912 bytes, and a bounded 4*N+1 member allocation across eight contexts
needs another 525,133,856 bytes before proposals, directory, FIFOs or caches.
No BRAM-only residency claim is made. No LUT/DSP fit or random-HBM throughput
claim is established.

Under the already optimistic sixteen-lane 200 MHz II1 assumption, BNN shift20
needs at least **0.402168 seconds for eligible edges alone**, versus measured
CUDA **0.314170 seconds**. Thus it fails before reset, directory operations,
bank conflicts, same-destination merge, closure barriers, output or draining.
A strict equality would already require about 256 MHz with all other costs free;
a 20% time reserve requires about 320 MHz. Neither is a demonstrated frequency.
The same narrow model also fails the tseng GPU budget once its shared directory
cost is included. The observed small-bank conflict inflation is not permission
to ignore forwarding/FIFO timing.

The exact-key BNN conditional model has arithmetic margin against its own slower
exact-key CPU/GPU controls. That does not establish a hardware win over the
available coarse GPU alternative, whose complete tested tseng/BNN output is
byte-identical to shift0. General algorithm equivalence is not inferred from
those inputs. Increasing lanes, scanning more directory architectures or
starting new OOC to seek a favorable ordering is outside this completed screen.
The detailed bounds keep overlapping compute/bandwidth/directory service as a
maximum, and add the explicitly nonoverlapping barrier assumption. The 25%
engineering allowance is a scenario, not a confidence interval. Unknown hardware
costs remain listed rather than silently set to zero.

**Stop this hardware candidate.** This is not an impossibility proof for every
FPGA algorithm or larger design. The new software track and its counterexamples
are retained; STRICT and the CPU paper mainline remain unchanged. No new HLS,
RTL, OOC, frequency or board campaign was performed or left queued.

| Report flag | Scope/result |
|---|---|
| model_schedule_calibrated | issue/retire separation: true; complete native cycles: false |
| alternative_contract_defined | ALT_BUCKET_FP32_V1 shifts 0/20: true |
| native_bitwise_equivalent_on_tested_inputs | small real graphs and tseng exports: true; fixture cohort, BNN exports and both final native maps: false |
| same_algorithm_cpu_gpu_verified | all 509 fixtures, six small graphs, full tseng and BNN, both shifts: true |
| large_3d_complete_batch_verified | BNN 40 real qids, both shifts, CPU and CUDA: true |
| native_qor_gate_passed | s38417 and BNN, one live shift0 pair each: true; shift20: not run |
| hardware_candidate_budget_supported | false; 16-lane candidate rejected |
| fpga_superiority_verified | false |
| new_implemented_frequency_hz | null |
| board_measured | false |

[Machine-readable decision](../results/lookahead_accel_round6_20261109T150000Z/evidence_snapshot/report_final.json),
[matched timing](../results/lookahead_accel_round6_20261109T150000Z/evidence_snapshot/matched_timing.json),
[native qualification](../results/lookahead_accel_round6_20261109T150000Z/evidence_snapshot/native_qualification.json),
[immutable evidence index](../results/lookahead_accel_round6_20261109T150000Z/evidence_snapshot/index.json).
