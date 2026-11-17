# GEMM/BNN native completion after independent V1 delivery

V1 was technically complete, frozen, pushed and delivered before any new metadata observer or GPU job. V1 commit: `4d0c4e88c1823ae554d6b4a891b53875b438cdec`. Its publication receipt is `accel/lookahead/gemm_bnn_native_completion/V1_publication.json` (20:04:35 UTC). No V1 artifact depends on this experiment.

The finite matrix ended at22:10:34 UTC on2026-11-17: **18/18 formal processes, eight qualification main processes,26 separate independent original-VPR FULL/STA readbacks, zero retries, zero excluded timing rows.** Two prior local metadata-only observers exited86 before search/route; they are not formal measurements. LSTM is historical; no new DLA or s38417 execution.

## Fixed inputs and resources

GEMM: original gemm_layer seed1, width100, N=9,595,752, E=84,213,916, J=40. BNN: original bnn_s1, width120, N=4,102,608, E=39,480,616, J=40. Both have two layers. All five original input hashes were verified. Actual exported metadata and native captures determine dimensions; stale historical case geometry is not used for admission.

One job `job-69d00d65-9971-4cf1-9876-58b8e9049460`, node qb-prod-gpu435, Xeon Platinum8462Y+, eight distinct physical cores0–7, inherited MPOL_BIND NUMA0,10-CPU quota,200GiB RAM, H10080GB UUID `GPU-5b68cf93-fadc-0517-0a0f-010db79b27ab`. Other tenants outside the allocation are not excluded. Exact worker contract, original ELF/library hashes, pre/post resource snapshots and source closures are archived.

Original ALT_BUCKET_FP32_V1, original representation, shift20. Actual live ABI admits the full GEMM graph; the historical offline STRICT23-bit envelope was not silently imposed or raised. No reduced graph/sample set, new algorithm, batching, prepared-POP or INF implementation.

## Direct paired statistics

Each new case rotates Stock→Pipeline→CUDA, Pipeline→CUDA→Stock, CUDA→Stock→Pipeline, n=3 fresh processes per arm. Entries below are mean±sample SD (n−1); ratios are means of within-repeat ratios. LSTM is its separate older cohort. No historical denominator or cross-workload multiplication.

### Complete native Process

|Case|Stock s|Pipeline s|CUDA s|Stock/Pipeline|Pipeline/CUDA|Stock/CUDA|
|---|---:|---:|---:|---:|---:|---:|
|gemm|338.737±0.434|194.331±0.697|176.354±0.351|1.743±0.004|1.102±0.004|1.921±0.003|
|bnn|134.237±1.020|75.337±0.333|68.597±0.854|1.782±0.012|1.098±0.009|1.957±0.018|
|lstm_s2 (historical)|137.395±4.839|81.727±1.986|74.703±1.100|1.681±0.044|1.094±0.010|1.839±0.049|

### Native construction E2

|Case|Stock s|Pipeline s|CUDA s|Stock/Pipeline|Pipeline/CUDA|Stock/CUDA|
|---|---:|---:|---:|---:|---:|---:|
|gemm|171.920±0.769|26.621±0.577|7.308±0.052|6.460±0.167|3.643±0.091|23.524±0.120|
|bnn|69.863±0.994|10.838±0.571|3.389±0.060|6.455±0.265|3.197±0.116|20.619±0.248|
|lstm_s2 (historical)|65.413±4.066|9.907±0.563|3.089±0.071|6.603±0.205|3.207±0.147|21.182±1.342|

Process includes loading, initialization, full routing/checking/STA and uniform serialization, but excludes pre-generated packing/placement/RRG and separate readback. E2 is the original native compute scope including conversion, preparation, transfer/readback, merge and interpolation; it is not resident/kernel timing. Stock E2 precision remains0.01s. Formal capture and CPU-reference verification are disabled.

## Complete qualification and semantic limits

|Case|Final map entries|Delay / congestion / missing word differences vs STRICT|Full ALT CPU/CUDA samples and maps|
|---|---:|---|---|
|gemm|1115136|0 / 50789 / 0|Equal|
|bnn|451584|0 / 24434 / 0|Equal|

All26 main routes pass zero final overuse and independent FULL/STA with their own route SHA unchanged by readback. Stock/Pipeline maps match; ALT CPU/CUDA captures cover the complete same input and all40 samples. Each formal map matches its qualification map. Route SHA equality across methods is not required. CPD/WL stays within the predeclared+5% gate against both paired CPU controls; this is not a universal zero-loss guarantee. Actual qualification CPD/WL is in `qualification.csv`; all process measurements are in `raw_seconds.csv`.

- gemm: {"critical_path_ns": {"min_percent": 0.0, "max_percent": 0.0}, "wirelength": {"min_percent": -0.06634384375768798, "max_percent": -0.06261022109417258}}
- bnn: {"critical_path_ns": {"min_percent": 0.0, "max_percent": 0.0}, "wirelength": {"min_percent": -0.022298660325092978, "max_percent": 0.06845330664608795}}

The native RRG loader emits1314 no-fanin diagnostics for BNN and2082 for GEMM in both controls and ALT; no other numbered graph errors appear. They are retained in full logs. FULL/STA checks the actual routed design, not every graph-generation choice.

## Memory evidence and limitation

Native primary-process maximum RSS is16,013.1MiB. Exact simultaneously live original CUDA buffer payloads are10,519,587,872B (GEMM) and4,524,945,536B (BNN), from source allocations and actual dimensions. The original runtime80%-of-free-memory admission and checked allocations succeeded. These payloads exclude driver/context overhead and are not a sampled total-device high-water mark. The platform GetTaskMetric API returned InternalError at supported intervals; raw requests/responses are retained. **Total device peak is NOT_MEASURED**, not invented or substituted by the payload formula.

## Protection, publication and stopping boundary

126 original files passed full-hash validation: original inputs/runtime/binaries, previous paper artifacts, V1 PDF/ZIP, FPGA frozen RTL/bindings/budget, and all three completed DCPs. Main, STRICT, previous paper refs and V1 remain unchanged. FPGA PGID1144478 stays stopped, with159 stopped threads and cumulative6168669 CPU ticks. Actual Vivado PID1144514 birth ticks182228751; boot ID2c285022-7829-4b21-84d8-176f6732a754. Read-only observer PID3982419 birth ticks185273769 holds both controller locks. No automatic deadline signal, terminal publication or resume. Last completed DCP is place.dcp SHA256 `9000c97d4f40506eeb4a7f5dc4127f814136cfdf84713512c4c0b4ee0cb25fa7`.

FPGA pause branch: `accel/lookahead-h-device-migration-20261117`, frozen control SHA `2fa63e3f2effc7392cbe3edecc06d42e52a0e44c`. Resume entry: `accel/lookahead/fpga_device_migration/pause_20261117/RESUME.md` on that branch. New user authorization, birth/lock/license/budget checks are required; this software delivery never resumes it.

V2 is a separate descendant of V1. Qualified new tables/interpretation and empirical ALT domain coverage are added; the algorithm/source correspondence, historical controls, LSTM five-arm comparison, s38417 negative case, semantic/QoR caveats, cache limits and separate resident cohort remain. Author approval and external submission are not performed. Final full remote SHAs and artifact hashes are recorded in publication receipts and the user delivery.

## Reviewable artifacts

- `accel/lookahead/gemm_bnn_native_completion/tables/`: CSV/JSON/TeX, raw seconds, all direct ratios, qualification and claim limits.
- `analyze.py`, `archive.py`, `validate.py`: completed-data analysis,180 small evidence snapshots and56 large-artifact SHA bindings, full protection checks.
- `source_binding.json`, `worker_freeze.json`, `receipts/actual_worker_experiment_plan.json`: exact unchanged code and actual resource freeze.
- `preflight_evidence/`: two metadata observers and submission/authentication-stage records, kept distinct from formal data.
- `evidence/`: full invocation/log/identity/measurement/readback records. Large RRG/capture/map/route/DCP files stay at bound server paths.
- Independent paper branch `paper/dac2027-cpu-gpu-matched-v2-20261117`, directory `paper/dac2027_cpu_gpu_algorithm_v2/`.

Software completion does not mark FPGA physical completion. No automatic next research stage is scheduled.

## Published successor and final state

V2 was frozen and published at full remote commit
`b0587c7e310073d04b1ba1e85e26a40ae0212389`. It binds completed experiment
evidence commit `30bc11372b173165c0b7bf2574b21c8fddaa8eff`. Both full remote
SHAs were verified; final publication details and both versions' artifact
hashes are in `accel/lookahead/gemm_bnn_native_completion/receipts/final_publication.json`.
The V1 ZIP is also mirrored byte-for-byte under `releases/V1/` for convenient
remote download; its already delivered original is unchanged.
All software work is complete, with FPGA still paused, author approval false
and no external submission or next research stage.
