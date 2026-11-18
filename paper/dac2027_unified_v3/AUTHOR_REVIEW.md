# V3 internal author review

**Primary evaluation.** GEMM and BNN each completed all six configurations with three matched repeats on one Xeon Platinum 8462Y+/H100 worker. The 36 formal invocations comprise 24 full processes and 12 construction controls. The original plan included 18 additional LSTM runs. LSTM reached auxiliary qualification. V2 and the complete fallback at 2f43d7147904ec498bd944af127c2c4a463a8b63 remain available for the author's submission decision.

## Claims and supporting records

- The timed worker used eight physical cores on NUMA 0, a ten-CPU quota and 200 GiB. All formal intervals are disjoint. The worker, GPU, preflight and binary bindings, raw nanosecond records, sample SDs and ratios are archived on experiment/dac2027-unified-v3-20261118 at 671a31e1c9fd18d2242a5c32c4d53ac5f50ec992, under experiments/dac2027_unified_v3/allocation_b/audit.
- All 36 raw timing rows were checked against the original processes. All 20 mean/SD time rows and 26 mean/SD paired-ratio rows were independently recomputed. The three repeats per cell describe process variation for a fixed input and seed.
- In GEMM and BNN order, Stock/ALT CUDA construction ratios are 20.03 and 19.97. Corresponding Process ratios are 1.80 and 1.88. Figure 1 uses the new GEMM records. Mean Stock E2 was 140.18 s out of 300.61 s, a 46.63% share. The archive reconciles the older 82.96% two-stage subtotal with the 45.18% historical Process denominator.
- The three original XML files all have two layers. All 40 contexts were retained per case. Stock and STRICT maps agreed on all three workloads. ALT CPU/CUDA captures and maps agreed on each workload, with changed congestion representatives relative to STRICT.
- LSTM Stock wrote the expected wire map, then faulted in native parallel route-tree construction when the predecessor edge was invalid. Historical Stock completed the same inputs. The origin of the invalid predecessor remains open. The three LSTM candidate routes passed independent checks and lack a matched Stock CPD/WL reference.
- All 47 emitted routes passed independent FULL/STA. The 44 scored invocations met the same +5% CPD/WL thresholds with zero overuse. The original worker performed 45 readbacks. The last two GEMM readbacks ran on the editing host after termination. Their elapsed times are excluded from performance comparisons.
- Inspire automatically recycled allocation B at 16:43:50 UTC under the workspace utilization rules. The current GPU rule specifies three hours and a threshold of 40%. Reservation A is archived at 37d0193538344f0117317eb76d9be530e91f0a66. [Investigation and source receipts](review/ALLOCATION_B_AND_LSTM_STOCK.md)

## Build and review

The anonymous source ZIP rebuilds the PDF byte for byte in a clean directory with TeX Live 2026. The page images and page-by-page review are under review/. All fonts are embedded. The manuscript has no unresolved references or overfull boxes. The experiment heartbeat at closeout records PAUSED_BY_USER_BUDGET_DECISION_REQUIRED for the FPGA migration. Author approval and external submission remain pending.
