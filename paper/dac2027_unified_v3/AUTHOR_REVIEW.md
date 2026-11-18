# V3 internal author review

**Measured subset.** The six-page draft uses 36 formal invocations from one Xeon Platinum 8462Y+/H100 allocation. GEMM and BNN each completed the six configurations, three repeats per configuration. The counts are 24 full processes and 12 construction controls. LSTM has four qualification attempts and zero formal invocations. All 18 planned LSTM timing observations are missing. The title page identifies the partial cohort. V2 and the complete fallback at 2f43d7147904ec498bd944af127c2c4a463a8b63 remain available for the author's submission decision.

## Claims and supporting records

- The timed worker used eight physical cores on NUMA 0, a ten-CPU quota and 200 GiB. All formal intervals are disjoint. The worker, GPU, preflight and binary bindings, raw nanosecond records, sample SDs and ratios are archived on experiment/dac2027-unified-v3-20261118 at 671a31e1c9fd18d2242a5c32c4d53ac5f50ec992, under experiments/dac2027_unified_v3/allocation_b/audit.
- All 36 raw timing rows were checked against the original processes. All 20 mean/SD time rows and 26 mean/SD paired-ratio rows were independently recomputed. The three repeats per cell describe process variation for a fixed input and seed.
- In GEMM and BNN order, Stock/ALT CUDA construction ratios are 20.03 and 19.97. Corresponding Process ratios are 1.80 and 1.88. Figure 1 uses the new GEMM records. Mean Stock E2 was 140.18 s out of 300.61 s, a 46.63% share. The archive reconciles the older 82.96% two-stage subtotal with the 45.18% historical Process denominator.
- The three original XML files all have two layers. All 40 contexts were retained per case. Stock and STRICT maps agreed on all three workloads. ALT CPU/CUDA captures and maps agreed on each workload, with changed congestion representatives relative to STRICT.
- The LSTM Stock qualification wrote the expected wire map and exited with signal 11 during routing. Its formal repeats and proposed original-binary diagnostic had not run when the reservation stopped. The cause remains open. The three LSTM candidate routes passed independent checks. They lack a matched Stock CPD/WL reference. LSTM contributes no measured speedup.
- All 47 emitted routes passed independent FULL/STA. The 44 scored invocations met the same +5% CPD/WL thresholds with zero overuse. The original worker performed 45 readbacks. The last two GEMM readbacks ran on the editing host after termination. Their elapsed times are excluded from performance comparisons.
- Inspire recorded job_stopped at 16:43:50 UTC. Container events identify termination without naming the initiating actor. Reservation A remains separately archived at 37d0193538344f0117317eb76d9be530e91f0a66. Its times do not enter this cohort.

## Build and review

The anonymous source ZIP rebuilds the PDF byte for byte in a clean directory with TeX Live 2026. The page images and page-by-page review are under review/. All fonts are embedded. The manuscript has no unresolved references or overfull boxes. The experiment heartbeat at closeout records PAUSED_BY_USER_BUDGET_DECISION_REQUIRED for the FPGA migration. Author approval and external submission remain pending.
