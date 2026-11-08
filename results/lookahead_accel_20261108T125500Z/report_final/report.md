# Lookahead acceleration experiment evidence

Generated: 2026-11-08T11:52:31.330435+00:00

Target ordering FPGA > basic GPU > optimized CPU > original VPR remains **unverified**. CPU wall times, CUDA event times and RTL functional cycles are kept separate. No board measurement or calibrated large-graph FPGA prediction is reported.

## Native workload correctness

| Workload | Nodes | Edges | Samples | Final native wire map |
|---|---:|---:|---:|---|
| tseng_export | 93276 | 860020 | 8 | True |
| bnn_export | 4102608 | 39480616 | 40 | True |
| tiny_native | 552 | 802 | 4 | not a frozen-map comparison |
| tseng_eligible | 93276 | 831056 | 8 | not a frozen-map comparison |
| tiny_eligible | 552 | 592 | 4 | not a frozen-map comparison |

tseng CPU and HLS C replay match native sample/group bits. tseng HLS output imported through the native adapter reproduces the final wire map. BNN CPU and HLS C replay match all 40 native sample maps. These are correctness checks, not FPGA time measurements. One-iteration component routing is not a route-success claim.

## RTL and OOC

| Variant | csim / synth / cosim / impl | Functional cycles (transaction 0) | Verified target clock MHz | LUT / FF / DSP / BRAM18 equivalents / URAM |
|---|---|---:|---:|---|
| hls_cache_off | passed / passed / passed / passed | 378002 | 200.0 | 23193 / 29192 / 4 / 49 / 0 |
| hls_dual | passed / failed / not_run / not_run | — | — | — |
| hls_dual_ports | passed / passed / failed / not_run | — | — | HLS est: 130374 / 62782 / 8 / 0 / 0 |
| hls_dual_ports_v2 | passed / passed / failed / not_run | — | — | HLS est: 130374 / 62782 / 8 / 0 / 0 |
| hls_dual_ports_v3 | passed / passed / passed / passed | 208948 | 200.0 | 41974 / 50686 / 8 / 98 / 0 |
| hls_dual_serial | passed / passed / passed / not_run | 208948 | — | HLS est: 130642 / 64190 / 8 / 0 / 0 |
| hls_dual_serial_dependency | passed / passed / passed / passed | 410772 | 200.0 | 42689 / 51949 / 4 / 98 / 0 |
| hls_eligible | passed / passed / passed / passed | 397195 | 200.0 | 20973 / 26009 / 4 / 49 / 0 |
| hls_f0 | failed / not_run / not_run / not_run | — | — | — |
| hls_f0_v2 | failed / not_run / not_run / not_run | — | — | — |
| hls_f0_v3 | passed / passed / passed / passed | 4665 | 200.0 | 20972 / 26010 / 4 / 49 / 0 |
| hls_heap31 | passed / passed / passed / passed | 293852 | 200.0 | 25027 / 30176 / 4 / 49 / 0 |
| hls_label64 | passed / passed / passed / passed | 363926 | 200.0 | 24264 / 30172 / 4 / 49 / 0 |
| hls_one_port | passed / passed / passed / passed | 379651 | 200.0 | 33612 / 45045 / 4 / 31 / 0 |
| hls_tiny | passed / passed / passed / passed | 410625 | 200.0 | 20973 / 26009 / 4 / 49 / 0 |

| Implemented core | Setup WNS ns | Hold WHS ns | Internal endpoints unconstrained |
|---|---:|---:|---:|
| hls_cache_off | 0.72 | 0.033 | 0 |
| hls_dual_ports_v3 | 0.474 | 0.019 | 0 |
| hls_dual_serial_dependency | 0.494 | 0.019 | 0 |
| hls_eligible | 0.986 | 0.019 | 0 |
| hls_f0_v3 | 0.517 | 0.023 | 0 |
| hls_heap31 | 0.733 | 0.019 | 0 |
| hls_label64 | 0.856 | 0.009 | 0 |
| hls_one_port | 0.132 | 0.04 | 0 |
| hls_tiny | 0.986 | 0.019 | 0 |

Automatic HLS co-sim memory is functional. Cycles include initialization, heap/CSR/labels, IPIN recording and drain, but do not establish real HBM service time. The first adversarial transaction contains three samples; tiny-native transactions contain four. Do not compare these as the same workload. Empty/error transactions are kept separately. OOC target frequency is reported only when place/route met that constraint, never the reciprocal of an estimated critical path.

## Resident software measurements

| Record | Evidence | Workers / contexts | Scope | Seconds | Matches native |
|---|---|---|---|---:|---|
| tseng_eligible_hls/runs.json | host_c_functional_check | None / 1 | resident_flood_batch | — | True |
| bnn_cpu_pilot/runs.json | cpu_measured | 1 / 1 | resident_flood_batch | 58.9406 | True |
| gpu_worker/bnn_export_B40/runs.json | gpu_measured | None / 40 | resident_flood_batch | 36.3063 | True |
| gpu_worker/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 9.88834 | True |
| gpu_worker/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 10.1362 | True |
| gpu_worker/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 9.9875 | True |
| gpu_worker/tiny_native_B4/runs.json | gpu_measured | None / 4 | resident_flood_batch | 0.00036224 | True |
| gpu_worker/tseng_export_B2/runs.json | gpu_measured | None / 2 | resident_flood_batch | 2.59562 | True |
| gpu_worker/tseng_export_B1/runs.json | gpu_measured | None / 1 | resident_flood_batch | 5.16531 | True |
| gpu_worker/tseng_export_B4/runs.json | gpu_measured | None / 4 | resident_flood_batch | 1.29948 | True |
| gpu_worker/tiny_native_B1/runs.json | gpu_measured | None / 1 | resident_flood_batch | 0.00131821 | True |
| gpu_worker/tseng_export_B8/runs.json | gpu_measured | None / 8 | resident_flood_batch | 0.648511 | True |
| gpu_worker/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0385214 | True |
| gpu_worker/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0394571 | True |
| gpu_worker/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0371441 | True |
| gpu_worker/tiny_native_B2/runs.json | gpu_measured | None / 2 | resident_flood_batch | 0.000685504 | True |
| gpu_worker/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0358487 | True |
| gpu_worker/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0367892 | True |
| gpu_worker/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.037564 | True |
| gpu_worker_confirm/bnn_export_B40/runs.json | gpu_measured | None / 40 | resident_flood_batch | 36.5854 | True |
| gpu_worker_confirm/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 9.56334 | True |
| gpu_worker_confirm/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 9.82417 | True |
| gpu_worker_confirm/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 9.99194 | True |
| gpu_worker_confirm/tiny_native_B4/runs.json | gpu_measured | None / 4 | resident_flood_batch | 0.000361856 | True |
| gpu_worker_confirm/tseng_export_B8/runs.json | gpu_measured | None / 8 | resident_flood_batch | 0.647027 | True |
| gpu_worker_confirm/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0364298 | True |
| gpu_worker_confirm/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0350896 | True |
| gpu_worker_confirm/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0354896 | True |
| gpu_worker_confirm/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0379755 | True |
| gpu_worker_confirm/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0359295 | True |
| gpu_worker_confirm/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0354826 | True |
| gpu_worker_pinned/bnn_export_B40/runs.json | gpu_measured | None / 40 | resident_flood_batch | 36.4328 | True |
| gpu_worker_pinned/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 10.1181 | True |
| gpu_worker_pinned/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 9.7517 | True |
| gpu_worker_pinned/cpu_bnn_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 9.5306 | True |
| gpu_worker_pinned/tiny_native_B4/runs.json | gpu_measured | None / 4 | resident_flood_batch | 0.000361696 | True |
| gpu_worker_pinned/tseng_export_B8/runs.json | gpu_measured | None / 8 | resident_flood_batch | 0.645411 | True |
| gpu_worker_pinned/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0355807 | True |
| gpu_worker_pinned/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0352987 | True |
| gpu_worker_pinned/cpu_tseng_eligible/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0369064 | True |
| gpu_worker_pinned/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0357647 | True |
| gpu_worker_pinned/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0369789 | True |
| gpu_worker_pinned/cpu_tseng_export/runs.json | cpu_measured | 8 / 1 | resident_flood_batch | 0.0380334 | True |
| bnn_hls/runs.json | host_c_functional_check | None / 1 | resident_flood_batch | — | True |
| tiny_cpu/runs.json | cpu_measured | 1 / 1 | resident_flood_batch | 0.000183983 | True |

## Preferred E1 cohort: same worker and eight physical cores

| Workload/backend | Median seconds | Range |
|---|---:|---|
| bnn_export_B40 | 36.5854 | [36.3429, 36.6056] |
| cpu_bnn_export | 9.82417 | [9.56334, 9.99194] |
| cpu_tseng_eligible | 0.0354896 | [0.0350896, 0.0364298] |
| cpu_tseng_export | 0.0359295 | [0.0354826, 0.0379755] |
| tiny_native_B4 | 0.000361856 | [0.00036144, 0.000366272] |
| tseng_export_B8 | 0.647027 | [0.638639, 0.651995] |

Same physical core set, one NUMA node, same job quota; shared host, no exclusivity claim.

## Full native lookahead builder E2 (cohort identified in report.json)

| Native variant, 8 physical cores | Median seconds | Range |
|---|---:|---|
| flat | 0.04 | [0.04, 0.06] |
| per_group | 0.06 | [0.06, 0.06] |
| pipeline | 0.04 | [0.04, 0.05] |
| stock | 0.21 | [0.21, 0.21] |

E2 log timer resolution is 0.01 s; these small differences require caution. Same physical core set, one NUMA node, same job quota; shared host, no exclusivity claim.

## Matched tiny-native ablations

| Change | Control | Cycles before → after | Cycle reduction |
|---|---|---:|---:|
| eligible CSR | hls_tiny | 410625 → 397195 | 3.27% |
| label cache 64 | hls_cache_off | 378002 → 363926 | 3.72% |
| heap top 31 | hls_cache_off | 378002 → 293852 | 22.26% |
| four AXI masters vs one | hls_one_port | 379651 → 378002 | 0.43% |
| parallel dual engines | hls_dual_serial_dependency | 410772 → 208948 | 49.13% |

Removing DATAFLOW alone did not serialize independent calls (`hls_dual_serial`: 208948 cycles). The valid serial control uses the first engine completion status to gate the second. The serial dependency also lets HLS share arithmetic (4 DSP estimated versus 8 in the parallel version); report this as parallel engine replication, not isolated scheduler benefit or proof of shared-pipeline latency hiding.

## Request-latency sensitivity (uncalibrated)

| Variant | Request latency | Functional cycles | Output ports match |
|---|---:|---:|---|
| memory64_cache_off | 64 | [1955466] | True |
| memory64_f0 | 64 | [2007435] | True |
| memory64_heap31 | 64 | [1129300] | True |

The memory probe changes request latency only. Read/write service remains independent; there is no calibrated shared-bandwidth arbitration. Original stale-report parser outputs are retained and superseded by result_corrected.json from fresh XSim records. No cycles are extrapolated to large graphs.

Heap recurrence diagnosis: `heap_ii_diagnosis.json`, csynth.log lines 100–115 and the authoritative verbose schedule. Automatic heap sift-down achieved II=29; dependent AXI queue requests/responses constrain the recurrence. This is not a demonstrated memory-port shortage.

CUDA uses one warmup and three measured batches per process; CPU measures one batch per process with OpenMP startup included. Preserve this methodological difference. CPU formal comparisons require the same host, worker/NUMA budget and scope; use the preferred completed worker cohort for same-host GPU comparisons. Local pilot measurements overlapped development/tool flows and are diagnostic. Native B0/B1 component records are E2; C1 and CUDA are E1, so no cross-scope speedup is calculated.

## Boundaries and outstanding work

- Pinned E1 CPU/CUDA measurements all passed. The pinned job failed its native-control affinity audit because OMP_PROC_BIND pinned the native main thread; that E2 cohort is excluded. The first worker retains valid E2 results; when present, the repaired confirmation cohort is preferred for both E1 and E2. The future runner clears binding variables for native controls; all four local native controls passed the repaired environment audit. A separate confirmation job records CPU topology/compiler and rechecks E1/E2 together; its success is determined from its receipt and command records, not inferred from this text.
- Two-context prototype duplicates complete engines and uses eight logical AXI masters; it is not yet a shared-pipeline interleaver. Shared-bundle synthesis failure and the first adapter-padding cosim failure are retained.
- Top-cache, label-cache, CSR and port studies use the same tiny complete native RRG and functional memory assumptions. Their benefits must be compared to the matching cache-off control.
- Physical HBM mapping, bounded latency/bandwidth/backpressure modeling, calibrated large-graph prediction, cost LUT residency and compact geometry mapping remain unimplemented.
- GPU/FPGA E2 online service integration and representative full downstream FULL/STA validation remain outstanding. Offline map import is only a correctness bridge.
- Existing results/native_* and CPU paper files remain frozen.

Reproduction and format: `accel/lookahead/README.md`. Logs, commands, return codes, input/source/binary hashes and phase snapshots are under the experiment directory.
