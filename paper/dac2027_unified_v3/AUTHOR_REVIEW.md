# DAC 2027 V3 · author final review

The seven-page anonymous manuscript integrates three measured workloads. The paper branch descends from 7050936c06dcfc3a19af5593168dc795e1202b20, the verified HEAD of the preceding V3 primary paper. Its predecessor d999a250f8e9358b264c713095a050b8f8467819 and the complete fallback at 2f43d7147904ec498bd944af127c2c4a463a8b63 remain archived. V2 is available at b0587c7e310073d04b1ba1e85e26a40ae0212389. Author approval and submission are pending.

| Workload | Frozen allocation | Formal runs | Stock/ALT CUDA E2 | Stock/ALT CUDA Process |
|---|---|---:|---:|---:|
| GEMM | B | 18 | 20.033 ± 0.237 | 1.795 ± 0.012 |
| BNN | B | 18 | 19.966 ± 0.375 | 1.879 ± 0.022 |
| LSTM | C | 18 | 28.057 ± 0.896 | 2.282 ± 0.050 |

Each workload has four full-process arms and two E2-only controls, each with three fresh processes. The two workers share the CPU/GPU model and resource configuration. The full-process time includes routing and all launch-to-exit overhead. A speedup is the mean of three within-workload paired ratios. Each SD describes variation at one fixed input and seed. The paper covers two-layer graphs.

All 54 formal routes passed independent FULL/STA, zero-overuse checks and Stock-relative CPD/WL thresholds. Including the qualification invocations gives 65 unique emitted routes and 62 scored passes. A separate original-binary diagnostic also passed. The earlier LSTM Stock fault remains in the qualification record. FPGA migration was observed passively in PAUSED_BY_USER_BUDGET_DECISION_REQUIRED state during integration.

- [Manuscript](main.pdf) and [anonymous source](anonymous_source.zip)
- [Raw seconds](review/raw_seconds.csv), [time statistics](review/seconds.csv) and [paired ratios](review/paired.csv)
- [Distinct route counts](review/route_counts.csv) and [invocation-level QoR](review/routes.csv)
- [Claim–evidence ledger](review/CLAIM_EVIDENCE.md), [E1 scope audit](review/E1_AUDIT.md) and [LSTM fault investigation](review/ALLOCATION_B_AND_LSTM_STOCK.md)
- [Page-by-page visual review](review/VISUAL_REVIEW.md), [clean-directory rebuild](review/rebuild.json), [freeze manifest](paper_freeze.json) and [checksums](SHA256SUMS)
