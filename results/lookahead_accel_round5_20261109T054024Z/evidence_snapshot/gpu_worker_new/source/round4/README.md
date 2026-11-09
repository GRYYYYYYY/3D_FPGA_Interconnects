# Round-four independent backends

`STRICT_FULL_FLOOD` keeps the original queue order, statistics and complete
search. `MAP_EQUIVALENT_EARLY_STOP` keeps the complete output map bit for bit in
the admitted domain, but intentionally changes statistics, final workspace and
the timing of errors in a skipped suffix. The old backends are unchanged.

`reference4.hpp` is the independent C++ implementation; `cpu4` uses
`std::priority_queue`, persistent per-worker allocations and dynamic OpenMP qid
assignment. `cuda4` is a basic 128-thread CTA implementation with an atomic qid
worklist. Both accept `workload.bin parallelism warm_repeats full|early`.
`cpu4 ... diff` checks every native sample against its native golden and emits
functional diagnostics, not the official performance measurements.

The target set is deduplicated from **all** input IPIN/cell pairs, including
unreachable or otherwise ineligible nodes. Preparation never reads golden maps
or executes a preliminary reachability search. A NaN output denotes an unseen
cell; output/label reset and discarded leftover-queue reset occur inside E1.
The first legal callback records a cell. Nonnegative delay extensions and exact
heap order ensure no later callback can improve its delay; equal delay never
overwrites congestion. Empty target sets finish after required state/output
reset; unreachable targets force heap exhaustion.

Input-only numeric admission requires eligible costs to be finite, nonnegative
normal FP32 or positive zero. The CPU/CUDA preflight conservatively proves no
path-sum overflow using `2*N*max_cost <= FLT_MAX` with `N < 2^23`. Hardware uses
the more conservative exponent bound 240 at `MAX_N=4096`. Queue capacity is
`E+1`; every node expands at most once, so this bounds all pushes. Overflow or
unsupported input is an error, never an implicit external-memory fallback.

`lookahead_onchip4` is a runtime-loaded hardware API with fixed capacity
`N<=4096, E<=16384, J<=32, C<=128, K<=64`. Commands are:

* `0`: invalidate the previous image, validate and load the new graph/tasks;
* `1`: run on the loaded image, requiring matching dimensions;
* `2`: load and run in one transaction.

Graphs with equal dimensions can still differ: callers must issue LOAD when
contents change. RUN intentionally ignores external graph contents. A failed
LOAD invalidates the old image. A RUN shape mismatch returns an error.
The four-engine API returns four status values: a batch is valid only when all
are OK. There is no cross-engine rollback transaction; after a rejected batch,
reload a valid image before reuse and do not consume partial results.
`search<ID>` has only on-chip RAM interfaces. There is no external queue,
label, cost or CSR fallback inside its hot loops. Output and statistics are
flushed to device memory before completion.

Single and four-engine builds use the same generic capacity constants and
search code. Each engine has a private graph replica and workspace. Four-engine
task assignment is currently static round-robin by original qid, and output
addresses retain original qid order. It is not a dynamic ready-task scheduler;
the report quantifies load imbalance and separates any unimplemented scheduler
opportunity from measured performance. No tasks are duplicated to increase J.

The heap uses complete 96-bit entries and independent even/odd sibling banks.
Delay comparisons use unsigned **bit patterns**, not numeric conversion; FP32
additions and all delay/congestion bits are preserved. Pop uses libstdc++'s
down-then-up algorithm and chooses the right child on equal delay. The requested
heap II is 2; use synthesis/RTL evidence for achieved II and pop service time.

`scripts/la_accel_hls4.py` freezes source and input hashes before running classic
Vitis HLS 2022.2 phases. `scripts/la_accel_monitor4.py` replays verified RTL and
checks every result/status port, graph AXI inactivity during warm E1, transaction
drain, heap-pop latency and engine overlap. Functional AESL memory is not a
calibrated HBM or board model. Only timing-clean implemented clocks may convert
verified cycles into FPGA time. C simulation wall time is never FPGA time.

Optional CMake `LA_HLS_INCLUDE` enables ap_int heap/admission host checks;
`LA_CUDA=ON` enables the real CUDA executable. The software-only semantic tests
do not require an AMD installation.
