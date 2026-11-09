# ALT_BUCKET_FP32_V1 — R6 software screen

This is an explicit alternative, never STRICT. Compile `cpu6.cpp` with C++14,
OpenMP, `-O3 -ffp-contract=off -fno-fast-math` and `-Iaccel/lookahead/include`.
The CLI is `cpu6 workload shift workers repeats output profile [edge_budget]
[member_budget]`. Shift is exactly 0 or 20. Profile 2 enables immutable path
version witnesses; profiling/witnesses are excluded from timing runs. Output is
J*C pairs in the frozen workload order; it is not a serialized native wire map.
`cuda6.cu` takes `workload shift repeats cpp_reference output` and uses
`nvcc -O3 -std=c++14 --fmad=false` with the same include path.

Every source retains its own labels, cell mapping and targets. The key is the
unsigned FP32 delay bits shifted by the chosen amount. All additions are FP32
round-to-nearest-even; admissible costs are positive normal finite floats or +0.
Negative, negative zero, subnormal and nonfinite eligible costs are rejected.
Each addition is checked; overflow returns UNSUPPORTED_NUMERIC, never a map.
Noneligible SOURCE/SINK cost fields need not be numeric. Internal unreachable
labels are +infinity; canonical NaN missing values exist only in the output.

Select the smallest pending bucket. All active nodes read the same wave-start
label snapshot. Compute candidate (delay,congestion) pairs along single edges;
reduce whole pairs lexicographically against the old label. Commit after the
wave, and enqueue only strictly improved pairs. Equal pairs never re-enqueue.
A node appears at most once in a particular pending bucket. Moving to a smaller
bucket leaves an explicit stale entry in the old vector, filtered by its pending
key. Each active node may reopen in the same bucket; no permanent expanded bit
prunes zero-cost cycles. Closure requires no pending work in the current bucket
and a completed commit barrier. All IPINs processed since that bucket began
contribute their final label to their cell with lexicographic pair min. Only
then can covered targets terminate the sample. Unreachable targets exhaust the
queue. Empty target sets/batches return canonical empty output. This iterative
FP32 rule is not a proof of globally lexicographic optimal paths.

The CPU uses dense proposals and generation marks with a vector of touched
nodes, vector bucket members, and a balanced ordered directory. The GPU uses
packed 64-bit pair atomicMin, separate committed/proposal arrays, a dense pending
key directory, and separate expansion, commit/min-reduction, target-confirmation
and advance kernels. Nodes/edges within each frontier run in parallel; jobs
remain distinct grid rows. Whole-kernel boundaries enforce snapshots and closure.
The GPU directory scans and host completion copy are included in E1. It is a
basic GPU baseline, not a claim that dense directory scans are optimal.

CPU budget: 500 million raw edge visits and 180 seconds per qid, fewer than one
million wave iterations, at most 4*N+1 queued members. Debug witness capacity is
2 million versions. CUDA: 180 seconds and 100,000 global wave iterations per
batch, with device allocation admission. Budget/capacity/numeric failure returns
nonzero without publishing an output file. There is no CPU fallback. Fresh calls
reset labels, pending state, target outputs, directory and closure state within
E1. Graph/cost changes rebuild immutable preparation; no cache/version reuse is
implemented. Callers must keep input pointers immutable for a call.

Compile `backend6.cpp` as a shared OpenMP library to use the existing live native
ABI. Set both `VPR_LA_BACKEND=/absolute/libbucket6.so` and
`VPR_LA_MODE=ALT_BUCKET_FP32_V1`; optional `VPR_LA_BUCKET_SHIFT=20` selects the
fixed coarse control. Without the explicit mode, this library rejects the call.
The existing native bridge supplies current graph/source identities, merges
samples in frozen group order and invokes existing interpolation. It reads no
golden output. The native default and all old backends remain unchanged.

E1 includes state reset, search, closure, target output and synchronization.
Input validation, allocation, target preparation and graph loading are separately
reported; native E2 also includes graph conversion and ordered group merge.
Debug, profiled, native E2 and historical timings are never E1 speed denominators.
