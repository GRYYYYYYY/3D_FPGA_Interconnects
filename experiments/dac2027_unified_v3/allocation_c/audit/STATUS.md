# LSTM checkpoint recovery result

Job `job-15ae04fd-dbec-40f7-8ddd-d2ad30cc016b` resumed from frozen allocation B at commit `671a31e1c9fd18d2242a5c32c4d53ac5f50ec992`. Allocation C used a single Xeon Platinum 8462Y+ / H100 80GB worker with eight physical cores on NUMA 0, a ten-CPU quota and 200 GiB memory. The GPU UUID was `GPU-7b8e076e-926a-6ba2-f8da-19706eb2cf9e`. Inspire recorded successful completion at 19:35:53 UTC after 4,121 seconds. The worker verified the checkpoint, the four LSTM qualification receipts, the workload inputs and the pinned binary and runtime hashes.

LSTM completed all 18 pending formal cells with no overlaps. Every configuration has three valid repeats. All 18 wire-map digests matched the frozen expectations. Every emitted route passed independent FULL/STA and the repeat-matched Stock QoR thresholds. CPD remained 11.7483 ns, maximum signed wirelength increase was 0.040%, and overuse was zero. The original Stock binary also completed the separate untimed diagnostic and passed route readback. The previously observed routing fault did not recur in the three timed Stock repeats or the separate diagnostic.

| Numerator / denominator | E2 ratio | Process ratio |
|---|---:|---:|
| Stock / ALT CUDA | 28.057 ± 0.896 | 2.282 ± 0.050 |
| Stock / STRICT Pipeline | 6.580 ± 0.092 | 1.978 ± 0.051 |
| ALT CPU / ALT CUDA | 3.810 ± 0.183 | 1.113 ± 0.033 |

Ratios use the mean and sample SD of three matched repeats within allocation C. Raw nanosecond observations, original route/map SHA256 and per-invocation readback records are in this directory. The complete LSTM matrix supplements the GEMM/BNN primary evaluation of allocation B. Each allocation provides its own matched statistics. Elapsed time from the original failed LSTM qualification and from the recovery diagnostic supplies no formal observations.
