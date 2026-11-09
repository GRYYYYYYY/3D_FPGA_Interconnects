# R6.1 native/compact gate

This independent software round is based on R6 commit `480ba6d5cc2b9d73696a44315777c0e658d8a7b4`. Read [compact_contract.md](compact_contract.md) before using a result. ALT remains a separate algorithm with known congestion differences from STRICT. No HLS/RTL/OOC runs or hardware speed claims are authorized by a software pass.

`cpu61.cpp` supplies original, COMPACT_RRG_V1 and shift20 direct-directory CPU controls. `strict61.cpp` is a timing wrapper around the unchanged R4 strict/early reference. `cuda_solver61.cuh` factors the R6 basic CUDA control into a reusable solver with original/compact field loading. `cuda61.cu` is its offline comparator. `cuda_backend61.cu` accepts current native ABI pointers and is default off; it does not read an offline reference. The original R6 CUDA source/executable remains a separate baseline. `backend61.cpp` is the CPU native qualification backend.

`cache61.cpp` and `replay61.hpp` are bounded functional proposal/chunk diagnostics. They do not establish a complete finite timed architecture. A passing cache replay cannot enable the next hardware phase.

Typical local builds (from repository root, use a new result directory):

```bash
c++ -O3 -std=c++14 -fopenmp -ffp-contract=off -fno-fast-math -Iaccel/lookahead/include accel/lookahead/round6_1/cpu61.cpp -o RESULT/cpu61
c++ -O3 -std=c++14 -fopenmp -ffp-contract=off -fno-fast-math -Iaccel/lookahead/include -shared -fPIC accel/lookahead/round6_1/backend61.cpp -o RESULT/libcpu61.so
c++ -O3 -std=c++14 -ffp-contract=off -fno-fast-math -Iaccel/lookahead/include accel/lookahead/round6_1/cache61.cpp -o RESULT/cache61
```

Offline CLI:

```text
cpu61 workload shift workers warm_repeats output profile original|compact|direct [edge_budget] [member_budget]
cuda61 workload shift warm_repeats reference output original|compact profile
strict61 workload workers warm_repeats full|early|diff
cache61 workload 16|32|64|128 sample|full
```

The optional CPU edge/member overrides apply to diagnostic profile modes; normal runs retain the fixed default finite budgets.

The GPU worker script records the actual optimized compiler commands, source hashes, CUDA/tool/CPU versions, NUMA affinity, resource quota, all warm/first measurements and command return codes. It serializes timings and separate profiling, then invokes the native runner only after A2 qualification receipts exist. Native runs use fixed historical inputs, a private copy of the proven R2 live builder with the outer scope timer, and the existing project scheduler. The script does not submit itself; use the existing resource query/validate/submit flow and its finite timeout.

`R61_CAPTURE` and `R61_VERIFY_CPU` are qualification-only diagnostics. Formal native runs clear them. Runtime selection requires explicit `VPR_LA_MODE=ALT_BUCKET_FP32_V1`, backend library path and `VPR_LA_BUCKET_SHIFT=20`; the live CUDA library rejects other shifts. The native CPU backend also supports shift0 for comparison. Native failures propagate and must not be advertised as completed maps.

`la_accel_round6_1_collect.py` refuses to collect a successful software closure before the worker completes. It separates per-case/backend/shift/representation qualification, retains raw timings and never adds component medians to manufacture E2. Raw large maps, graphs, captures and executables remain at the indexed server paths; the committed evidence snapshot contains logs, commands, hashes, comparison records and failures. Reproduction requires the same historical input files and native build dependencies; it is not a standalone replacement VPR distribution.
