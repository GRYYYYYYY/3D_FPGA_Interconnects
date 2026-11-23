# DAC 2027 V3 · author final review

The seven-page manuscript omits the author byline and integrates three measured workloads. Section II-C compares FPGA routing lookahead construction, including the clustered-source estimator of Sharma and Hauck and the map-building pseudocode in AIR (Algorithm 3). The archived arm identifier for the CUDA implementation on the H100 is alt_cuda. The body ends on page six and the references occupy page seven. V2 is available at b0587c7e310073d04b1ba1e85e26a40ae0212389. Author approval and submission are pending.

| Workload | Frozen allocation | Formal runs | Stock/ALT GPU Lookahead Construction Speedup | Stock/ALT GPU End-to-End Process Speedup |
|---|---|---:|---:|---:|
| GEMM | B | 18 | 20.033 ± 0.237 | 1.795 ± 0.012 |
| BNN | B | 18 | 19.966 ± 0.375 | 1.879 ± 0.022 |
| LSTM | C | 18 | 28.057 ± 0.896 | 2.282 ± 0.050 |

Each workload has four full-process arms and two construction-only controls, each with three fresh processes. The two workers share the CPU/GPU model and resource configuration. The End-to-End Process Time includes routing and all launch-to-exit overhead. A speedup is the mean of three within-workload paired ratios. Each SD describes variation at one fixed input and seed. The paper covers two-layer graphs.

All 54 formal routes passed independent FULL/STA, zero-overuse checks and Stock-relative CPD/WL thresholds. Including the qualification invocations gives 65 unique emitted routes and 62 scored passes. A separate original-binary diagnostic also passed. The earlier LSTM Stock fault remains in the qualification record. FPGA migration was observed passively in PAUSED_BY_USER_BUDGET_DECISION_REQUIRED state during integration.

- [Manuscript](main.pdf) and [anonymous source](anonymous_source.zip)
- [Figure 2, execution schedules](figures/timeline.pdf) and [Figure 3, construction framework](figures/framework.pdf)
- [Figure 4, native times](figures/native_times.pdf) and [Figure 5, paired speedups](figures/paired_speedups.pdf)
- [Figure 1 Stock observations](review/stock_stages.csv) and [stage means and construction shares](review/motivation_shares.csv)
- [Raw seconds](review/raw_seconds.csv), [time statistics](review/seconds.csv) and [paired ratios](review/paired.csv)
- [Distinct route counts](review/route_counts.csv) and [invocation-level QoR](review/routes.csv)
- [Claim–evidence ledger](review/CLAIM_EVIDENCE.md), [Timing terminology audit](review/E1_AUDIT.md) and [LSTM fault investigation](review/ALLOCATION_B_AND_LSTM_STOCK.md)
- [Page-by-page visual review](review/VISUAL_REVIEW.md), [clean-directory rebuild](review/rebuild.json), [freeze manifest](paper_freeze.json) and [checksums](SHA256SUMS)

The supplied B03 and Main13 PDFs are preserved in figures/. The anonymous source uses vector publication copies exported with pdftocairo to remove document metadata and embed fonts. The framework artwork says “Up to K workers.” Its caption specifies the implementation: P workers and up to K live tokens. ALT CPU distributes samples across workers, and the GPU also parallelizes active nodes within each wave.

Figure 3 uses the revised Main13 artwork with an explicit two-candidate ALT wave. Candidate 2 prints 2.8 for both delay operands and 4.0 for their sum. The caption supplies the consistent predecessor pair (2.0, 0.2) and shared destination cost (2.0, 1.0) for the illustrated delay tie.
