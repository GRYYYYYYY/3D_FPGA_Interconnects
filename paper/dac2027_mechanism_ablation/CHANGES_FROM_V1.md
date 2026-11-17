# V2 changes from frozen V1

Parent V1: `4d0c4e88c1823ae554d6b4a891b53875b438cdec`, delivered at20:04 UTC before post-V1 metadata or GPU execution. Its PDF/source ZIP and prior commits remain unchanged.

- Added only qualified new original-input GEMM/BNN measurements: four qualification arms per case, three rotated independent processes per Stock/Pipeline/ALT CUDA arm, both E2 and Process in each run, and separate original-VPR FULL/STA readback for all26 main runs.
- Added complete Process/E2 tables with three directly paired ratios. LSTM is reused from its own historical cohort; its full five-arm table remains. No new LSTM, DLA or s38417 runs.
- Preserved the historical GEMM CPU1.638x result, BNN/DLA scheduling controls, shift0/20 work profiles, historical BNN Flat comparison, s38417 slowdown, cache applicability and separate64-worker resident scope.
- Extended empirical ALT applicability to the original9,595,752-node GEMM, without changing the original live binary, ABI, representation, shift or samples. C1/C2 algorithms and conditional guarantees are unchanged; no prepared-POP/INF or global optimality theorem is introduced.
- Updated result interpretation, abstract/conclusion numbers and qualification table. No FPGA-based acceleration content was reintroduced.
- Made the new Platinum8462Y+ allocation and historical Gold6530 cohorts explicit. Recorded successful CPU/NUMA0 memory binding, fixed GPU UUID, full output identities and per-run QoR.
- Retained RRG no-fanin diagnostics in controls and ALT. Host peak RSS is observed; device payload footprint is source-derived. The platform metrics API failed, so total device/driver peak is not claimed as measured.

Author approval and external submission remain outstanding. FPGA remains paused; software completion does not authorize resume.
