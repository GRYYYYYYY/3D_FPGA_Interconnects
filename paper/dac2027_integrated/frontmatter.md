# Exposing Inter-Sample and Intra-Search Parallelism in Layer-Aware Lookahead Construction for 3D FPGA Routing

Layer-aware lookahead construction can dominate multicore FPGA routing workflows. We expose two levels of parallelism through separate execution contracts: STRICT schedules independent samples with private workspaces and ordered reduction, while ALT uses whole-pair FP32 bucket waves within each search. The native integration preserves layer and source identity while explicitly separating semantic guarantees. Existing eight-core GEMM measurements show 1.638-fold process acceleration for STRICT Pipeline. On a preselected same-family LSTM case, ALT CUDA accelerates native construction by 3.207-fold and the complete process by 1.094-fold against Pipeline. We report congestion differences, checked routing quality, and small-input slowdowns; FPGA hardware superiority remains unverified.

1. STRICT: independent sample floods, reusable private state and native-order reduction, with a scoped wire-map equivalence argument.
2. ALT: an independent whole-pair FP32 bucket/wave contract and CPU/CUDA implementations under the native task interface.
3. Native validation: paired construction and Process measurements, explicit semantic differences and QoR gates, same-family tuning holdout and size-dependent negative results.
