# R6.1 native software closure and compact gate

Software closure: **pass** on the declared cases; shift20 original-format CPU and live CUDA qualify with actual native inputs, complete maps and independent route checks.
Hardware candidate: **UNRESOLVED**, with no service-prototype eligibility for the single compact/64-owner-bank/finite-cache family.
Close this round and stop hardware escalation: achieved frequency, random-RMW service and a complete finite dependency/FIFO timing model are unsupported; software gains do not establish FPGA superiority.

Base `480ba6d5cc2b9d73696a44315777c0e658d8a7b4`; branch `accel/lookahead-round6_1-native-compact-20261109`. The original workspace, STRICT, old golden, main, untracked guides and historical evidence are preserved. No new HLS/RTL/OOC or blocking-heap replication ran.

## Functional and native meaning

COMPACT_RRG_V1 retains all CSR destinations/order, 64-bit rows and original FP32 cost words; node16 admission rejects unsupported fields. Direct shift20 uses 4096 headers and a hierarchical bitmap. Six small graphs, 509 historical fixtures and both full exports pass 2585 CPU configurations; compact CUDA passes 1030 small/fixture configurations and full inputs in the timing matrix. Lifecycle/numeric/capacity checks and the out-of-range cost-index rejection are recorded separately.

The eight R6 congestion counterexamples remain unchanged. tseng matches old golden; BNN offline sample outputs retain 133798 congestion-word differences, with zero delay/missing differences. CPU original/compact at shifts0/20 and direct at shift20 yield the same ALT pairs on these full inputs. Full-input compact CUDA is tested at shift20; shift0 compact CUDA validation is limited to the small/fixture set.

Actual native ALT20 versus ALT0 maps are identical. Versus STRICT/control, s38417 has 166 and BNN 24434 congestion-word differences; delay/missing differences are zero. These final-map counts are different objects from offline sample counts. Live CUDA consumes current BackendInput pointers, verifies all pairs against same-input CPU during qualification, and produces the same native map. It never imports historical outputs or falls back to CPU. Compact/direct native qualification is **not_run**; original-format qualification is not inherited.

All qualified routes use their own unchanged route-file hashes for independent FULL/STA readback, zero overuse and the declared CPD/wirelength +5% gate. Only two fixed native cases/seed 1 were screened. Passing QoR is not STRICT bit equivalence. The reused BNN RRG emits inherited CHANZ no-fanin diagnostics in every arm; the logs and counts are retained. This qualification covers candidate routes/FULL/STA/QoR, not a claim of a clean whole-RRG structural audit.

## Matched offline software

One H100 worker, eight selected physical cores on one NUMA pool, fixed legal 1/4/8 (tseng) and 4/8 (BNN) CPU choices; three fresh processes each, with first call and three warm complete batches. All timings are sequential and uninstrumented. Each row below is the best measured thread choice for that implementation; every legal configuration and raw sample remains in matched_software.json. Strict/early rows are standalone algorithm controls, not native C1. No cross-algorithm ratio is called hardware speedup.

| Complete input | Implementation | CPU workers | Warm E1 median (s) | First call (s) | Load (s) | Prepare including compact conversion (s) |
|---|---|---:|---:|---:|---:|---:|
| tseng_export | strict | 8 | 0.035819 | 0.036540 | 0.007576 | 0.002270 |
| tseng_export | early | 8 | 0.036701 | 0.036580 | 0.006662 | 0.002016 |
| tseng_export | alt_original | 8 | 0.013787 | 0.015315 | 0.007700 | 0.015119 |
| tseng_export | alt_compact | 8 | 0.012083 | 0.019915 | 0.007612 | 0.017558 |
| tseng_export | alt_direct | 8 | 0.012177 | 0.013427 | 0.008106 | 0.018550 |
| tseng_export | gpu_basic | GPU | 0.001812 | 0.048816 | 0.007831 | 0.530585 |
| tseng_export | gpu_original_refactor | GPU | 0.001808 | 0.060327 | 0.007677 | 0.394662 |
| tseng_export | gpu_compact | GPU | 0.001745 | 0.059981 | 0.007570 | 0.535939 |
| bnn_export | strict | 8 | 8.624623 | 8.600017 | 0.798620 | 0.337025 |
| bnn_export | early | 8 | 8.552252 | 8.473387 | 0.795709 | 0.317689 |
| bnn_export | alt_original | 8 | 7.156513 | 7.304519 | 0.800691 | 0.875234 |
| bnn_export | alt_compact | 8 | 6.055627 | 6.098448 | 0.802638 | 0.898095 |
| bnn_export | alt_direct | 8 | 6.050114 | 6.052581 | 0.829834 | 0.899691 |
| bnn_export | gpu_basic | GPU | 0.313920 | 0.361252 | 0.832083 | 0.768246 |
| bnn_export | gpu_original_refactor | GPU | 0.317253 | 0.375687 | 0.763958 | 0.800158 |
| bnn_export | gpu_compact | GPU | 0.309712 | 0.368674 | 0.793569 | 0.983338 |

BNN original ALT CPU/basic CUDA implementation ratio is 22.80x for warm complete E1 only. Compact CUDA/basic CUDA ratio is 1.014x; the same refactored solver original/compact ratio is 1.024x. The refactored solver allocates host output inside E1; unchanged G-basic prepares that buffer before its repeats. The original-refactor/compact pair shares the new scope and isolates representation effects. These measurements do not establish sustained application throughput or native-process speedup.

Fresh-first/load/prepare columns are separate observations, not summands for a synthetic E2. Preparation includes initial CUDA context creation when triggered. CPU/GPU compile with strict FP32 addition; comparisons and profiling remain outside formal E1.

## Native paired E2 and process

Each row is the median of three independent processes on the same worker, fixed graph/netlist/placement/seed/8-core affinity, with arm order rotated. Filesystem cache was not flushed. R6_1_NATIVE_BUILD_V1 spans MapLookahead::compute entry to exit, including graph conversion, service, ordered merge/interpolation and remaining native lookahead work. RR XML loading/RRG initialization and later serialization belong to Process, outside E2. LA_LIVE.total_s is a nested subset. Stock VPR prints the equivalent outer scope at 0.01 s precision; optimized/ALT uses a direct high-resolution timer. Native first-context cost is included. Audit captures and CPU pair verification are absent from this formal cohort.

| Case | Native arm (original format) | E1 wall (s) | E2 wall (s) | Process wall (s) | CPD (ns) | Wirelength | Iterations | QoR |
|---|---|---:|---:|---:|---|---|---|---|
| s38417 | stock | — | 1.070000 | 5.972889 | 7.05387 | 87356 | 49 | pass |
| s38417 | optimized | — | 0.180202 | 6.323985 | 6.96051 | 87893 | 68 | pass |
| s38417 | alt_cpu | 0.049890 | 0.118949 | 6.224944 | 6.96051 | 87893 | 68 | pass |
| s38417 | alt_cuda | 0.052666 | 0.627551 | 6.873816 | 6.96051 | 87893 | 68 | pass |
| bnn | stock | — | 63.030000 | 125.577600 | 11.0943 | 1536814 | 19 | pass |
| bnn | optimized | — | 10.393390 | 73.061830 | 11.0943 | 1538209 | 19 | pass |
| bnn | alt_cpu | 6.920779 | 9.751707 | 72.823986 | 11.0943 | 1537866 | 19 | pass |
| bnn | alt_cuda | 0.363795 | 3.104360 | 66.725848 | 11.0943 | 1537866 | 19 | pass |

s38417: optimized-native CPU/ALT CUDA E2 ratio 0.287x and Process ratio 0.920x are final-scheme comparisons including algorithm differences. Same-ALT CPU/CUDA E1 ratio 0.947x and E2 ratio 0.190x remain separately scoped.

bnn: optimized-native CPU/ALT CUDA E2 ratio 3.348x and Process ratio 1.095x are final-scheme comparisons including algorithm differences. Same-ALT CPU/CUDA E1 ratio 19.024x and E2 ratio 3.141x remain separately scoped.

## Phase and capacity diagnosis

Four separate instrumented runs cover tseng/BNN shifts0/20. Named initialize,expand,commit/min scan,confirm,advance CUDA event intervals plus host completion-copy wait and final D2H/unpack are retained in phase_profile.json. Stage synchronization changes scheduling; these are diagnostic measurements, not table timings. GPU global waves/launch count must not be replaced by the sum of per-qid waves. BNN measured global waves fall 627→59; the preserved R6 summed-qid counts 19691→2161 are a different quantity (the shift20 total 2161 is independently reproduced by this round’s full replay).

tseng_export shift0: 30 global waves; instrumented fresh E1 0.062625s versus uninstrumented diagnostic 0.061357s. Expand/commit/confirm/advance intervals 0.000521/0.000373/0.000255/0.000982s; commit+advance account for 63.6% of these four intervals. Initialize 0.058722s includes first-launch host/runtime gaps; it is not isolated reset-kernel time. The fresh-call difference includes clock/run variation as well as instrumentation, not an isolated overhead estimate.
tseng_export shift20: 25 global waves; instrumented fresh E1 0.063540s versus uninstrumented diagnostic 0.060339s. Expand/commit/confirm/advance intervals 0.000545/0.000387/0.000292/0.000896s; commit+advance account for 60.5% of these four intervals. Initialize 0.059591s includes first-launch host/runtime gaps; it is not isolated reset-kernel time. The fresh-call difference includes clock/run variation as well as instrumentation, not an isolated overhead estimate.
bnn_export shift0: 627 global waves; instrumented fresh E1 2.937046s versus uninstrumented diagnostic 2.903619s. Expand/commit/confirm/advance intervals 0.340133/1.026021/0.260729/1.195909s; commit+advance account for 78.7% of these four intervals. Initialize 0.059625s includes first-launch host/runtime gaps; it is not isolated reset-kernel time. The fresh-call difference includes clock/run variation as well as instrumentation, not an isolated overhead estimate.
bnn_export shift20: 59 global waves; instrumented fresh E1 0.379855s versus uninstrumented diagnostic 0.376256s. Expand/commit/confirm/advance intervals 0.055225/0.125369/0.025391/0.104827s; commit+advance account for 74.1% of these four intervals. Initialize 0.060290s includes first-launch host/runtime gaps; it is not isolated reset-kernel time. The fresh-call difference includes clock/run variation as well as instrumentation, not an isolated overhead estimate.

tseng_export: N=93,276,E=860,020,J=8; read-only row/node/edge/cost representation 9,118,848→4,372,904 B, excluding jobs/mapping and mutable state. Packing time is independently recorded. The CLI retains original host input plus packed arrays (BNN adds 166127680 B); this is not a host peak-memory reduction. Compact CUDA still retains per-qid dense state; graph compression does not imply the same reduction in total device capacity or actual memory traffic.
bnn_export: N=4,102,608,E=39,480,616,J=40; read-only row/node/edge/cost representation 414,307,608→198,948,632 B, excluding jobs/mapping and mutable state. Packing time is independently recorded. The CLI retains original host input plus packed arrays (BNN adds 166127680 B); this is not a host peak-memory reduction. Compact CUDA still retains per-qid dense state; graph compression does not imply the same reduction in total device capacity or actual memory traffic.

## Single bounded hardware family

The updated fastest BNN offline complete-E1 target is 0.309712337s, including strict/early and all finite representation controls. The 16/32/64-lane and 125/200 MHz arithmetic remains sensitivity only. No achieved new-kernel frequency or measured random-RMW service is available.

BNN ideal eligible-edge arithmetic:16 lanes@200MHz=0.402168s;32@125MHz=0.321734s, both above 0.309712s even before other work.64@200MHz=0.100542s requires at least 40.58% effective utilization for 20% margin before nonoverlap and memory/metadata constraints. These reference clocks are not achieved-frequency evidence.

Window capacities16/32/64/128 were each capped at 5M cache observations and 120 s, using qid 0 waves 1,10,30,50,59; bootstrap CPU traversal of qid 0 is additional (bounded), not a four-capacity full-batch sweep. The fixed selection rule chose 128 entries per owner bank; only this capacity received the full tseng/BNN replay.
Window 16: 1,118,639 candidates, hit rate 12.7768%.
Window 32: 1,118,639 candidates, hit rate 14.4079%.
Window 64: 1,118,639 candidates, hit rate 16.6941%.
Window 128: 1,118,639 candidates, hit rate 20.2679%.

tseng_export full functional replay: 5,802,746 eligible candidates, 11,605,492 FP32 additions, cache hit 50.3958%, 2,194,479 evictions, 578,981 dirty whole-pair writes; member/pending-set writes including source seeds578,989, chunk publishes24,041, empty→nonempty200, min selections192. Peak chunks per qid426/16384, queued members11,847/524288; all final home pairs match CPU labels. Modeled proposal read/write bytes are 92,109,056/18,527,392 using an assumed 32 B granule, not measured HBM traffic.

bnn_export full functional replay: 1,286,937,147 eligible candidates, 2,573,874,294 FP32 additions, cache hit 20.8723%, 1,006,229,726 evictions, 123,735,458 dirty whole-pair writes; member/pending-set writes including source seeds102,926,941, chunk publishes3,282,907, empty→nonempty2,181, min selections2,161. Peak chunks per qid6,813/16384, queued members214,711/524288; all final home pairs match CPU labels. Modeled proposal read/write bytes are 32,586,355,616/3,959,534,656 using an assumed 32 B granule, not measured HBM traffic.

At the diagnostic 32 B granule, proposal traffic alone requires 147.50GB/s to fit 80% of the measured best E1, before the omitted/other traffic and nonoverlap. This is a conditional arithmetic requirement, not supported effective bandwidth or a physical lower bound. Wave duplicate ratio 73.91% is not finite-cache locality. Directory batching reduces publication counts but does not eliminate member/pending writes or address allocation. Early target stop also leaves future-bucket storage to reclaim; its timed reset/drain service is not modeled.

With 128 entries/bank and a 24 B per-entry logical budget, the explicit header/bitmap/member/chunk/cache/cost ledger totals 23,113,792B (22.043MiB), excluding unmodeled FIFOs and ports. The BNN external-layout sensitivity separately counts 820,521,600B for eight qids of labels/proposals/pending/seen/flags, and 656,417,280B for all 40 mappings, plus graph/output. This is a storage budget, not physical-fit evidence.

Shared headers 512 KiB, leaf bitmaps 4096 B plus top words, member pool 16 MiB and sparse chunk metadata 4 MiB cover eight resident qids. Cache tags/pairs/replacement state and external label/proposal/pending/seen/mapping storage are additional. Headers are not replicated 64 times. Logical finite counts do not prove ports or placement.

The replay preserves sequential qid/CPU-CSR generation order and drains proposals at every wave. It is a functional transaction diagnostic, not the complete finite timed model required for a positive gate. Physical issued/retired timestamps, concurrent-qid critical path, actual burst/RMW/outstanding behavior, bank arbitration, RAW latency, finite FIFO backpressure and reset/output/drain timing remain unknown. Pending clears/seen and complete label traffic are omitted. The 32 B/channel stripe assumptions cannot establish bandwidth. Full-replay distinct-distance arrays are uncollected, not zero distances.

Decision **UNRESOLVED**: `finite_full_batch_model_complete=false`, memory service and physical resource support unknown, `eligible_for_service_prototype=false`, `fpga_superiority_verified=false`, `board_measured=false`. The next evidence needed is a supported memory/owner-service contract and complete dependency/FIFO replay, then a justified frequency/capacity bound with20% margin. This round stops without launching that work or searching another candidate.

## Evidence and failures

All deliverables: [evidence snapshot](../results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot), [compact contract](../accel/lookahead/round6_1/compact_contract.md), [decision](../results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/decision.json), [raw timing matrix](../results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/matched_software.json), [native qualification](../results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/native_qualification.json), [native E2](../results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/native_e2.json), [transaction model](../results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/transaction_model.json).

The initial native CPU attempt failed before execution because the new worktree lacked an ignored historical-case link; its log is preserved, and the complete qualified attempt has a separate directory. An initial CPU compilation exposed an iterator/pointer mismatch and was fixed before validation; the command-side error is recorded as an implementation attempt, not a measured failed algorithm. Expected invalid-input/capacity failures remain in lifecycle records. Source/binary/input hashes, native timer source and command logs are archived. Large raw artifacts stay at indexed server paths; no old evidence is rewritten.

GPU job job-e24071bf-822b-4d50-8221-26c5fc26650c succeeded and released all nodes. The terminal receipt and local experiment audit are archived; final commit/remote SHA verification is provided in the completion response and retained server publication receipt.
