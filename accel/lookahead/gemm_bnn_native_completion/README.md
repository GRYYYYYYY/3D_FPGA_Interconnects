# Post-V1 GEMM / BNN native evidence

V1 was delivered and its remote SHA verified before this directory's metadata
invocations or GPU submission. Its immutable commit is
`4d0c4e88c1823ae554d6b4a891b53875b438cdec`; see `V1_publication.json`.
This work does not resume FPGA or change a solver, RTL, original budget, old
paper, STRICT reference, or golden result.

## Frozen execution

`input_manifest.json` binds the original GEMM seed1/width100 cohort and BNN
seed1/width120 cohort by all five input hashes. `source_binding.json` binds the
existing Stock ELF, native Pipeline/ALT host ELF, CPU library and CUDA library
to original source snapshots; no solver was rebuilt. `metadata_backend.cpp`
is a separate observer that returns exit86 before search/route. The full input
metadata covers all40 sample identities, not a smaller replacement problem.

`experiment_plan.json` is the initial local/pre-authentication plan and is
retained as history. The actual resource contract, written on the GPU worker
before any qualification, is `receipts/actual_worker_experiment_plan.json`.
It fixes one H10080GB, eight distinct physical CPU cores0–7 on NUMA0 with
successful inherited MPOL_BIND, a10-CPU cgroup quota and200GiB RAM. The node
is Xeon Platinum8462Y+, not the historical Gold6530 worker. Other tenants
outside the allocation are not excluded; before/after GPU and cgroup snapshots
are retained. Hosts/cohorts are never pooled.

The original live ALT ABI uses32-bit node IDs and signed cell indices. The
historical offline STRICT envelope N<2^23 is not a check in the frozen live
ALT implementation. GEMM exceeds that historical envelope but is admitted by
the actual unchanged ABI and must still pass complete numerical qualification.
Exact allocated-state estimates are10,519,587,872B for GEMM and4,524,945,536B
for BNN, subject to the original CUDA free-memory80% admission. No sample
trimming, batching, new representation, algorithm change or parameter search.

`worker_freeze.json` binds all code/configuration consumed by the worker.
`runner.py` launches one fresh native process per arm, removes inherited
lookahead/capture settings, uses eight workers, writes each map uniformly,
records both native E2 and launch-to-exit Process, then independently reads
the unchanged route through original-VPR FULL/STA outside Process.
`gpu_worker.py` qualifies Stock/Pipeline/ALT CPU/ALT CUDA, including full
CPU/CUDA sample outputs, before nine rotated formal processes per case.
BNN and GEMM are sequential and independently gated; no automatic retries.
Timeouts are600s BNN and900s GEMM, selected from historical freezes before
new measurements. Capture and CPU-reference verification are off formally.

## Evidence and recomputation

Raw run: `results/gemm_bnn_native_completion_20261117/gpu_matched_a`.
The finite job identifier and reviewed manifest are in `receipts/submitted_job.json`.
The earlier image-ID submission was explicitly rejected without creating a
job. The successful request uses the same verified official image's registry
address; the rejected receipt remains under the local preflight run.

After the worker ends, run `analyze.py RUN --historical V1_EVIDENCE/holdout_results.json
--map-diff FROZEN_NATIVE_MAP_DECODER`. This invokes only a map decoder and
archived statistics, never a solver. It requires complete qualifications,
unique cohort/case/repeat keys, consistent inputs/resources, fresh maps,
independent readback, positive finite times and per-repeat ratio identities.
Failed or incomplete cases remain explicit exclusions. `tables/` contains
CSV/JSON/TeX, full raw seconds, three direct paired ratios with sample SD,
qualification/map differences and claim limits. LSTM is reused with its
separate historical cohort; DLA and s38417 are not rerun.

Large original RRG/ELF/capture/map/route files remain on the server with hashes;
only source, small manifests, original logs and reviewable measurements are
published. Never rerun `prepare.py` or a worker into an existing run directory.
The FPGA resume policy remains the separate pause branch's `RESUME.md` and
requires new user authorization plus process identity/budget checks.
