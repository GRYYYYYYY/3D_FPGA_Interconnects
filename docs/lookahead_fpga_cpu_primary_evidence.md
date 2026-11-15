# CPU-primary round: reused software, native identity and mechanism evidence

This is the historical-evidence companion to the CPU-primary closure report. It
makes **no claim about the new complete core's fit, routed clock, calibrated
cycles or CPU speedup**. Those results must come from the new integration and
CPU receipts. The research goal is now `CPU_PRIMARY_GPU_COMPARATOR`; a GPU win
is not a prerequisite. The old LF performance/resource no-go receipts remain
unchanged.

The verifier is [reuse_evidence.py](../accel/lookahead/fpga_cpu_primary/delivery/reuse_evidence.py).
Its [machine-readable index](../results/fpga_cpu_primary_20261115/reused_evidence/index.json)
is bound to Git base `3c7f96e6037030949b729240977c2ced373843c6`.
It contains 1,082 raw-record entries and 26 external-file bindings, including
472 passed historical software receipts, six strongest-GPU process records,
source snapshots, retained executables, native import/QoR records, complete LF
ALT outputs, 80 samples' finite/queue/wave diagnostics and representative
contrasts. Compressed raw objects occupy about 7.5 MB including the index.
Large original inputs and prepared CSR files remain at their recorded paths;
their bytes were rehashed against their producer/model bindings. No GPU,
historical model, native VPR or old EDA job was rerun.

## Strongest retained GPU measurements

Both cases use the actual prepared-CSR valid-POP whole-pair FP32 CUDA algorithm,
compiled with `nvcc -O3 -std=c++17 --fmad=false`, on recorded H100 80 GB HBM3
workers (CUDA 12.8.61, driver 570.124.06). These are **different worker runs**,
not one artificially paired BNN/LSTM experiment. The BNN choice is the earlier
compact result; LSTM is the later unchanged prepared-POP control/basic arm.
The slower private-INF candidates and alternate representation measurements
are retained in the copied summaries and receipts.

| Full resident batch | BNN40 compact | LSTM40 basic |
|---|---:|---:|
| Mean of three process means, seconds | 0.15179996944444446 | 0.15949799988888888 |
| Median of three process means, seconds | 0.151800436 | 0.15968920233333334 |
| Sample SD of three process means, seconds | 0.00008353481051 | 0.00047436155610 |
| Pooled nine-repeat median, seconds | 0.151788273 | 0.158977815 |
| Historical pooled-repeat sample SD, seconds | 0.00009365109075 | 0.00104966176152 |
| CUDA batch wave rounds per repetition | 59 | 60 |
| Declared device bytes | 4,136,828,432 | 4,357,609,956 |

Each process executes one warmup and three formal repetitions. Process IDs
0/1/2 have means BNN 0.151800436/0.151883270/0.15171620233333333 seconds and
LSTM 0.15895787633333333/0.15968920233333334/0.159846921 seconds. All raw
formal values match the historical summaries as multisets; their original
JSONL process grouping and order remain available. Nine repeats are **three
independent process units**, not nine independent processes or nine circuits.
No confidence interval based on nine independent observations is claimed.

**Binary provenance limitation:** the earlier BNN `prepared_pop_gpu_b`
`binding.json` records source SHA and build commands, but omits an
execution-time binary SHA. Its original command names the retained executable;
that executable is now copied and hashed as
`4d6107d7313b9e71a55f8e6294e4481b9f67c71c87281db67bcb8b3a631fa9e0`.
This is a present-byte observation, not a retroactive measurement-time hash.
That earlier binding lists only its two translation units; common headers are
preserved from the later fully bound control cohort rather than falsely
backdated. The strongest result is retained with this caveat. The later
LSTM `gpu_control` executable matches its historical binding:
`61c3cf63c81d4f4eefc1f35e5fe6f688f400bf214acc51433ad4015db43e2807`.
The two binaries differ; they are not asserted byte-identical.

Both use CUDA source SHA
`fc38943e5d2e0bdec72799a5c49e956972bbb09479aeb9779f16c8709598312b`.
The already completed CUDA supplement supplies the missing source in the later
archive and matches its frozen binding. The private-INF supplement and all
listed later headers also match their historical source digests. The original
supplement and archived measurement files are not modified.

## Exact timing boundaries

The boundary was checked directly in the preserved
[cuda_prepared_pop.cu](../accel/lookahead/fpga_sparse_stream_r2/cuda_prepared_pop.cu),
not inferred from the label `RESIDENT_COMPLETE_BATCH_V2`.

| Scope | Included | Excluded / interpretation |
|---|---|---|
| CUDA resident wall time | Start before CUDA event recording/error reset; mutable label/proposal/pending/output/meta initialization; all 40 jobs' wave kernels; per-wave launch/control and completion D2H; final error D2H; final event synchronization | Workload loading, eligible-CSR reconstruction and validation, host metadata preparation, device allocation and input H2D occur before start. Full output D2H, INF-to-MISSING normalization, golden comparison and file serialization occur after stop. |
| CUDA event timeline | Recorded GPU timeline spanning host-controlled waves | Includes host launch gaps; not a sum of isolated kernel durations and not a replacement for the reported resident wall timer. |
| LF historical finite batch | Every sample's required initialization/cost loading, all waves/canonical/scratch/publication, final output write and ACK drain; 40 sample cycles summed | Architectural prediction at assumed 200 MHz/80 ns latency/5 ns physical issue, not a board measurement or newly calibrated complete-core result. CPU worker concurrency only accelerated the simulator. |
| Construction E2 | Required input preparation, transfers, core service and required output postprocessing on the actual timeline | Research-only golden comparison/SHA/archive checks are distinguished from required production checks. Launch/control already in resident must not be counted twice. Overlap uses timeline span, not an unconditional sum. |
| Native VPR Process | Recorded native graph/setup/build/routing/FULL/STA process scope | Separate from resident and E2. Original pre-generated graph/placement costs and uncontrolled file-cache conditions remain as documented. |

CUDA numeric/semantic error collection is inside resident; complete host output
comparison is outside it. This distinction prevents interpreting “complete
batch” as “all deployment transfer and validation costs included.” FPGA output
ACK drain is core completion; no unmeasured board readback or launch cost is
invented. No board-measured FPGA value is supplied by this reuse index.

The separate new host-postprocessing cohort is complete; it is not part of the
historical reuse index. Its [delivery receipt](../results/fpga_cpu_primary_20261115/postprocess_final_g_a/delivery.json)
has SHA-256 `f5b5a073f9057f1be901edef378f23b8a1135c491754c595d15eb21bcd422719`.
CPU0 on the Xeon Gold6530 server ran BNN40 then LSTM40, each in three independent
processes with one warmup and three formal repeats. Complete-output conversion
means are1.561172/1.537052ms, with sample SDs of the three process means
0.055318/0.106717ms. All outputs match the actual selected g outputs. Input is
explicitly layout replay, not captured DMA. The timer covers swap32 within each
cost pair and removal of tail/stride padding from prefaulted buffers, with no
cache flush. Output allocation means0.011404/0.013816ms and first-touch means
8.745916/8.388458ms are separately recorded. File loading, validation, file output,
native map assembly and DMA are outside the conversion timer. The quiet-window
record documents suspended experiment work, not exclusive use of the machine.
This host-only observation neither measures board readback nor completes E2.
Packed CPU/CUDA conversion also occurs outside resident, so the cost must not be
added only to FPGA in a resident comparison. Reuse after a device-frequency
change requires unchanged actual output hashes, dimensions, layout, conversion
code and host boundary, with the original host environment retained.

The new CPU-thread scan and preparation measurements are owned by the new
software results. Historical Xeon 8462Y+ prepared-CPU and Xeon 6530 packed-CPU
cohorts remain separate; their cross-host differences cannot establish a pure
representation benefit. Neither an eight-thread historical run nor stock VPR
worker-seconds establish the strongest resident CPU baseline on the current
allocated machine.

## Native identity and ALT/STRICT limits

The unchanged `vpr_bridge.cpp` adapter has SHA
`afa1ee64b7d702210d9a637c32f451a19a1af481819cfc82099fbf197a987da7`.
The verifier rereads both workloads and the historical native captures,
compares header and every row/node/edge/cost/job/cell byte, checks each section
SHA against the archived identity receipt, and treats the embedded golden tail
separately from actual inputs. It also checks native import success,
`LA_IMPORT verified samples=40`, full-route-check receipts, wire-map bytes and
complete imported ALT output hashes. This is transitive identity reuse through
an unchanged adapter, **not a new VPR invocation or hardware execution**.

| Native import evidence | BNN | LSTM seed2 |
|---|---|---|
| Complete ALT SHA-256 | `a8ca4003a3b015145635a3f776bb62a3aec1ec2121a1fbfc8712d2a2dc1c8c3f` | `6b2acd7718d880075d653b3b83f1fa3abb5161f6f346ed39c3aa1285160a95cf` |
| Wire-map SHA-256 | `f9805a5660060b1b68e995120fa3009f449cbd46a6d39e39433c16b95595b82c` | `2f5746ca56a0581ee3ea45b6e67f9b1b4ec41f1f6aa501f174022b880394a57d` |
| Historical imported-route critical path | 11.0943 ns | 11.7483 ns |
| Historical imported-route wirelength | 1,537,866 | 1,712,223 |

These critical paths are **routed application QoR**, not FPGA accelerator clock
periods. Native whole-output equality supports only the original ALT shift20
whole-pair contract. STRICT is preserved. The old BNN offline sample comparison
has 133,798 congestion-word differences with zero delay/missing differences;
the BNN native map has 24,434 congestion differences. These are different
objects and must not be combined. The LSTM held-out native map has 23,111
congestion differences versus Flat over 459,684 entries, zero delay/missing
differences, and zero ALT CPU/CUDA differences. Native stock/Flat/Pipeline maps
match each other in that LSTM test.

The raw `holdout_results.json` and `targeted_optimization_results.json` are
copied and checked against archived source hashes. The held-out LSTM was
predeclared before algorithm timing, within the same workload family, fixed
seed2 and geometry; it is not evidence for unseen families or all placements.
Its historical qualification uses FULL/STA, zero overuse and the predeclared
+5% CPD/WL gate against its own stock/Flat cohort. Native compact/direct
qualification is not inherited from original-format ALT. The old negative
small-circuit CUDA result also remains valid.

For scope orientation only, historical LSTM same-worker medians are:

| Native backend | MapLookahead E2 seconds | Whole Process seconds |
|---|---:|---:|
| stock | 67.360000 | 139.827246 |
| Flat | 9.965118 | 80.966792 |
| Pipeline | 9.848020 | 80.866670 |
| original ALT CPU | 9.805994 | 80.815870 |
| original ALT CUDA | 3.083965 | 74.304932 |

Each row is three native processes in the historical cohort. The native CUDA
row is the original live backend, **not** the later prepared-POP resident
microbenchmark. No number in this table is used as a resident denominator.
Native stock/Flat/Pipeline did not record a comparable resident complete-batch
wall timer. New core resident speedup cannot be inserted into these E2 or
Process rows. See the preserved
[R6.2 closeout](lookahead_accel_round6_2_closeout.md) for paired statistics,
original launch/input/binary/library bindings and stage nesting.

## Quantitative GPU organization explanation

The actual CUDA launches `grid=(ceil(nodes/256), jobs)`; `blockIdx.y` exposes all
40 samples, with separate per-job label/proposal/pending/output/meta. An
eligible node/thread scans its CSR neighbors and uses 64-bit `atomicMin` for
whole-pair proposal/output merges. Device initialization is performed every
repetition. CUDA's 59/60 batch wave rounds include host completion polling;
the LF model executes samples serially and sums 2,161/2,200 sample waves.
These wave counts are different organizational units, not contradictory work
counts or permission to force CUDA into serial sample execution.

The selected historical L1 has finite T128/D128, ready/target/E/beat, 64
candidate lanes, POP8, per-bank K8, finite radix FIFOs and 32 physical tagged
ports. Its observed throughput is limited by the connected services and
backpressure, not just nominal lane arithmetic capacity.

| Historical LF L1 full model | BNN40 | LSTM40 |
|---|---:|---:|
| Total cycles | 72,317,544 | 73,419,021 |
| init / export / other cycles | 1,284,240 / 126,640 / 35,675 | 1,304,280 / 128,920 / 36,261 |
| pop+expand cycles | 48,862,467 | 49,650,643 |
| finalize cycles | 22,008,522 | 22,298,917 |
| Expand fraction | 67.57% | 67.63% |
| Finalize fraction | 30.43% | 30.37% |
| Candidates | 1,286,937,147 | 1,309,512,712 |
| Candidates / expand cycle | 26.338 | 26.375 |
| Fraction of 64-lane II1 peak | 41.15% | 41.21% |
| Conditional seconds at 200 MHz | 0.361587720 | 0.367095105 |
| Conditional LF / measured GPU time | 2.3820× | 2.3016× |

The complete outputs were reconstructed in sample order from all 80 archived
sample outputs and matched against both aggregate output and frozen ALT golden.
Source/include snapshots match the model binding; the retained model executable
matches SHA `bd21e8196aaaadf78f31437bb4eb951a2aec2d9e260441a8d9650f53b5e1575b`.
These historical cycles do not include the newly integrated dispatch/admin
handshake changes; the new complete-core calibration must account for them.

The fixed representative controls retain identical network, lane/E/beat/K/POP
and physical-port resources:

| Configuration | BNN4 cycles | LSTM3 cycles | Interpretation |
|---|---:|---:|---|
| L0: F2 frontend | 7,310,933 | 5,542,918 | Baseline with radix network |
| FS: shared lifetime | 9,259,951 | 7,036,046 | Shared token/storage lifetime penalty |
| L1: independent T/D/ready | 7,308,619 | 5,540,660 | Selected historical arithmetic-fit candidate |
| L2: L1 + publication journal | 6,611,954 | 5,014,153 | Unqualified resource-failing representative candidate |

Shared FS needs 26.70%/26.99% more time than L1. L1 improves over F2 by only
0.03165%/0.04074%, so decoupling removes a shared-lifetime penalty without
establishing a large standalone fusion gain. L2 reduces total representative
time by 9.532%/9.503% and finalize by 32.594%/32.872%; pop+expand rises slightly
with changed ordering. Real spill counts are recomputed. L2 is **not** a full
40-sample result and that percentage is not extrapolated to a full batch.

Actual full-network synthesis falls from static specialization 605,113 LUT to
radix 360,844 LUT (40.37% fewer). The radix L1 module sum is 1,254,466 LUT;
final compact-response L2 is 1,305,474, exceeding U280's 1,303,680 by 1,794.
These are historical module arithmetic sums, not complete-top physical fit.
Compared to older F2 full cycles 71,238,001/72,236,324, L1 costs 1.515%/1.637%
more cycles; the smaller network adds real stages/HOL and is not free speed.
The archived historical qualification remains false for complete-core clock.
Local 5 ns frontend/backend route success does not promote it to a full-core
200 MHz result. L2's already counted 6,112-LUT response specialization must
not be counted again as a new saving.

For the fixed 64-II1-lane, 200 MHz structure only, candidate work implies
`N_candidate/(64*200e6)` = 100.542/102.306 ms. Both are **below** the measured
GPU times, so this bound does not prove that FPGA must be slower. Concurrent
POP/edge lower bounds combine by maximum, not automatic addition. Holding
current finalize/init/export/other fixed leaves only 6.905/8.131 million
expand cycles to match CUDA and demands about 186.38/161.05 candidates/cycle,
above 64. That is a diagnosis conditional on unchanged other phases, not a
bound on a different architecture, clock, memory service or jointly optimized
backend.

Publication-held occupies 79.63%/79.84% of critical-bank finalize observations.
It is state occupancy, not fully removable pure stall. T/D/E/ready-full counters
overlap across groups; they are not additive batch wall-time losses. An
observed minimum D residence of 43 cycles is not a universal service lower
bound. The local RTL publication tests and representative L2 simulations give
a concrete opportunity with a measured area cost, not a promise to erase all
finalize time. Even subtracting all historical finalize cycles diagnostically
leaves 251.545/255.601 ms at assumed 200 MHz, above these GPU results; that
subtraction is not a simulated alternative design.

## Reproduction and claim ledger

The verifier performs no experiment execution:

```sh
python3 accel/lookahead/fpga_cpu_primary/delivery/reuse_evidence.py --verify
# To independently reconstruct the audit, use a fresh destination:
python3 accel/lookahead/fpga_cpu_primary/delivery/reuse_evidence.py --out /path/to/new/reused_evidence
```

`index.json.files` maps each original evidence name to an object, raw SHA-256,
byte count, compression and Git/manifest provenance. `external_files` records
exact paths, observed hashes and whether there is a prior expected digest.
An object with compression `gzip` decodes using `gzip.decompress`; `identity`
objects are already raw. Completed `index.json` is immutable; `--verify`
rechecks stored objects, external hashes and verifier source SHA. Input
availability on the shared filesystem is required for this external-hash pass.
The pinned LF/descriptor manifests are copied from the fixed Git tree and each
selected object is checked before reuse. This is a selected evidence audit,
not a claim that every vendor work directory in every archive was revalidated.

| Claim | Status and limit |
|---|---|
| Strongest preserved measured GPU resident baseline | Supported by original 3×3 process records, full output equality and source/representation boundary; earlier BNN binary-binding gap explicitly retained |
| Historical complete L1 ALT functional/model result | Supported; 80 sample outputs plus source/binary/input closure rechecked |
| Historical native import/QoR identity | Supported transitively for frozen ALT input/output/adapter; no new VPR run |
| ALT equals STRICT | False; congestion counterexamples retained |
| Local mechanism improvements explain some GPU gap | Supported quantitatively within the tested configurations and resource contracts |
| Any FPGA can never beat this GPU | Unsupported; fixed lane-work lower bound is below GPU time |
| New complete-core routed clock / calibrated speedup | Outside this document; requires new full-core results |
| Resident improvement proves E2 or Process improvement | Unsupported without deployment timeline and matching native scope |
| Board-measured FPGA performance | Not measured |
