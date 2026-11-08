# STRICT_FP32 lookahead acceleration

This is a new experimental backend, independent of the archived CPU paper and
old online router / integer candidate-cost accelerator. Round 1 is frozen at `results/lookahead_accel_20261108T125500Z`.
The active continuation is `results/lookahead_accel_round2_20261108T122100Z`.
The objective is FPGA faster than each baseline; GPU/CPU relative ordering is
not a success criterion. GPU remains a supplementary baseline. Read its generated report for actual
completion status; source availability does not imply device validation.

## Contract

The authoritative workload is exported from the frozen native global job list.
The hook uses native RR accessors, `get_xy_deltas`, sample selection and flood to
capture ordered CSR, FP32 bits, descriptors and sample/group golden. Node IDs
are identity mapped. Node coordinates, direction, raw type and segment are
retained in `.nodes.tsv`. The first representation intentionally precomputes
an int32 `(qid,node)->IPIN cell` mapping; its O(samples*nodes) memory/transfer cost
is included in graph preparation. This is a functional first layout, not the
final compact geometry implementation.

All binary values are little endian, naturally packed fixed-width records:
`Header` (7 uint64), row_ptr (N+1 uint64), Node (N*16 bytes), Edge (E*8), Cost
(K*8), Job (J*24), cell mapping (J*N int32), golden (J*C*8). File magic and sizes
are checked by the loader. Missing output cells have two `0x7fc00000` values.
Original native valid FP32 values are preserved. Domain: finite nonnegative
normal costs or positive zero, round-to-nearest, no fast math/FMA contraction,
no overflow. Unsupported candidates fail explicitly. Negative zero is currently
outside this restricted domain. NaN is only an output sentinel, never a cost.

Heap equal-child choice follows libstdc++ `__adjust_heap` (right child on ties).
Equal-delay candidates are retained. Source cost is excluded, callback precedes
expansion, `expanded` is set only after adjacency commit. Eligible SINK terminates
the parent's adjacency loop after preceding static filters. Group reduction is
original sample order with strict `<`, preserving congestion from the selected
candidate. Interpolation and retained CPU lookahead stages remain native.

E1 `resident_flood_batch` includes resets, all queue/state/graph operations,
output initialization and IPIN recording, and completion. Allocation and graph
conversion/upload are separate. E2 includes the full native builder. Imported
precomputed maps are **offline correctness tests**, not accelerated E2 timing.
Never divide historical/different-host E2 seconds by resident E1 time.

## Build and run

```sh
cmake -S accel/lookahead -B /new/build -DCMAKE_BUILD_TYPE=Release
cmake --build /new/build -j8
ctest --test-dir /new/build --output-on-failure
python3 scripts/la_accel_preflight.py --output /new/preflight
python3 scripts/la_accel_build_vpr.py --output /new/native --tbb-include /path/to/tbb/include
python3 scripts/la_accel_export.py --binary /new/native/bin/vpr_flat --case tseng_2d --output /new/export
python3 scripts/la_accel_run.py --backend cpu --binary /new/build/cpu_reference --workload /new/export/workload.bin --workers 8 --output /new/cpu
.venv-report/bin/python scripts/la_accel_compare.py --workload /new/export/workload.bin --actual /new/cpu/output_0.bin --output /new/compare
```

Native inputs and link archives must be present. The builder copies the two
frozen translation units and archive, substitutes only those objects, and binds
source/binary hashes. No archived results are rewritten. Header-only TBB 2021.5
was unpacked locally for this machine; frozen runtime libraries remain unchanged.
The import adapter requires both `VPR_LA_IMPORT` and `VPR_LA_WORKLOAD`, verifies
static graph/cost/task identity and golden maps, then uses native ordered merge.

CUDA requires an actual device/toolkit: `-DLA_CUDA=ON` or
`nvcc -O2 -std=c++14 --fmad=false -Iaccel/lookahead/include accel/lookahead/cuda/lookahead_cuda.cu`.
The persistent CTA pool keeps a private heap/labels per active sample. Neighbors
are computed by 128 lanes and committed in adjacency order by the owner. Graph
uploads are one-time; CUDA events span every reset and the entire batch. Only
maps/status are downloaded. No CPU fallback. Queue capacity E+1 is conservative
(each expanded vertex scans each edge at most once), and may waste memory.

## FPGA

`la_accel_hls.py --phase csim/csynth/cosim/impl --output /new/hls` runs classic
2022.2 Tcl for xcu280-fsvh2892-2L-e at a **target** period of 5 ns. Each phase
requires its predecessor. `--workload` selects the real-workload testbench and
binds AXI simulation depths. `--source`, `--top`, `--contexts`, and `--define`
select experiments. Source hashes and snapshots are preserved; output logs cannot
be silently overwritten. `--frozen-flow` resumes a recorded Tcl flow after checking
synthesis sources and testbench are unchanged.

F0 has four AXI masters (graph/state/queue/result), no platform shell, and a complete
heap/CSR/label/callback/termination loop. The baseline reloads costs from external
memory. A kernel operation counter is never called a clock counter: cycles come
from per-transaction RTL reports. The automatic co-sim AXI model is **functional**,
not a bounded HBM model. Target/estimated clock frequencies do not establish fmax.
Report implemented setup/hold/constraint coverage before deriving FPGA time.

Experimental variants are individually identified:

- `lookahead_cached.cpp`: `LA_HEAP_TOP`, `LA_LABEL_LINES` and `LA_SHARED_PORT`.
  Labels use a direct-mapped write-through cache, invalidated each sample; the
  blocking owner finishes each update before another lookup, so no outstanding
  RAW request can observe stale data. Heap cache covers exact logical top indices,
  and count reset prevents reuse of stale entries. No spill entries are dropped.
- `lookahead_dual_ports.cpp`: two replicated complete engines in DATAFLOW, eight
  independent logical AXI masters. This is **not yet** an interleaved shared search
  pipeline or an integrated eight-HBM-channel platform. Physical mappings remain
  unimplemented. The rejected shared-bundle attempt is retained as evidence.
- `la_accel_eligible.py`: static filtering preserves node identity, parallel edges
  and original order, and removes edges after the first eligible SINK. Both CPU
  and FPGA consume the same transformed graph and unchanged golden outputs.
- `lookahead_resident.cpp`: combines configurable heap/label caches with an exact,
  tagged cost cache (`LA_COST_LINES`). Cost-cache fills are included in E1 and
  retained across jobs in a batch. The cache is reset between invocations.
- `lookahead_interleaved_v3.cpp`: shared round-robin microstate machine with private
  per-context heap/labels and one parent expansion per qid. `LA_CONTEXTS` selects
  the count. Explicit base registers work around a reproduced 2022.2 wrapping
  address strength-reduction failure. Earlier source versions are retained for
  that failure's provenance, not selected for use.
- `lookahead_interleaved_distance.cpp`: same algorithm, with **true** dependence
  distance equal to the context count for heap, context state and top cache.
  Each owner recurs every `LA_CONTEXTS` iterations; no false dependency is asserted.
  The heap must remain alone in its AXI bundle. Cosim and routed timing determine
  whether this helps; round-robin selection alone did not improve throughput.

For dual-port co-simulation, use `--top lookahead_dual --contexts 2
--aligned-depths`. Vitis HLS 2022.2 rounds adapter transfers to AXI beats; a
12-byte heap entry count that is not beat aligned can overrun the autogenerated
C adapter temporary even when the caller allocates extra space. The runner
aligns simulation depths to 64-byte multiples while leaving logical graph sizes
and queue capacities unchanged. Failed unaligned runs are retained.

`lookahead_dual_serial.cpp` is a retained negative control: omitting DATAFLOW did
not prevent HLS from overlapping independent calls. Use
`lookahead_dual_serial_dependency.cpp` for the actual serial control; engine 1
starts only after engine 0 returns a successful status. `la_accel_overlap.py`
replays the generated RTL and records both engines' idle/done transitions and
overlap cycles, comparing both result ports to freshly generated RTL output.

`la_accel_memory_probe.py` varies AXI request latency in a copied simulation.
It deletes copied observations and reads the fresh XSim transaction file,
not the HLS postprocessed report. It is a sensitivity test with independent
read/write service, not a calibrated HBM bandwidth/latency model.

The host suite includes 20,000 mixed heap operations against libstdc++, semantic
error/boundary cases, and 200 randomized differential graphs for each cache.
Run `la_accel_software_summary.py`, `la_accel_report.py` and `la_accel_plot.py`
to collect a completed cohort and produce evidence tables and exportable figures.
A final confirmation worker supplies both pinned E1 CPU/CUDA and valid native
E2 data. Earlier cohorts and the native affinity rejection remain separate.
Round-one CUDA uses one warmup plus three measured batches; CPU measures one
batch per process, including OpenMP startup. This warmup difference is recorded.

## Round-two bounded memory and live builder

```sh
python3 scripts/la_accel_bounded.py --hls /verified/hls --output /new/bounded \
  --latency 64 --banks 1 --period 4 --credits 2 --minimal-debug
python3 scripts/la_accel_live.py --binary /new/native/bin/vpr_flat \
  --library /new/build/liblookahead_cpu_backend.so --output /new/live_cpu \
  --workers 8 --contexts 8 --repeats 3
```

`bounded_axi.sv` is a verification interposer around generated AESL RAM. It bounds
shared read/write beat service and outstanding requests, has one finite read skid
slot per port, and checks bursts, credits, latency, held VALID and drain. A cross-port
backpressure test guards against bank-lock deadlock. It preserves fresh RTL output
files and compares all result ports bitwise; no copied performance report is used.
This is a synthetic sensitivity model. Calibration, refresh/row locality and actual
HBM placement are not supplied. A finite bank is not evidence of real-board bandwidth.

`VPR_LA_BACKEND=/absolute/library.so` activates a versioned in-process interface.
It receives the current native graph, global samples and geometry mapping. It cannot
accept golden outputs. The native bridge performs original ordered merging and
downstream construction. CPU and CUDA libraries execute real searches and return
compact maps and status. `RTLD_NODELETE` keeps OpenMP worker code mapped for process
lifetime. Offline import/export cannot be combined with this live path.

The live runner measures three independent processes with no explicit warmup for
either backend, and verifies every final wire-map hash. E1 excludes allocation/upload;
the measured full-builder timer includes cold conversion, backend initialization,
upload, kernel, readback, merge and downstream work. The separate router timer also
includes source/OPIN lookahead. These cold E2 measurements are not a warm resident
FPGA service prediction. `la_accel_live_gpu_job.py` builds frozen source snapshots on
one real H100 worker and reruns native CPU controls on the same eight physical cores.

Use `la_accel_round2_report.py` and `.venv-report/bin/python
scripts/la_accel_round2_plot.py` for round-two reports and figures. Calibration of
large-graph FPGA predictions, asynchronous request/response context scheduling,
compact geometry and physical HBM connectivity remain unverified. FPGA superiority
over the software baselines remains a research target, not a measured conclusion.

## Round three: complete 3D spill and matched resident controls

See [the round-three record](../../docs/lookahead_accel_round3.md). The original
CPU/CUDA kernel algorithms are retained. `cpu_benchmark` and `cuda_benchmark`
accept `workload workers_or_CTAs warm_repeats`; the first invocation in each fresh
process is cold, subsequent batches reuse allocations while resetting search state
inside E1. `la_accel_round3_gpu_job.py` runs five independent processes per setting,
with CPU 1/2/4/8 workers (up to the actual job count) and basic CUDA up to eight CTAs.
The original/native E2 timers must not be substituted for this resident E1.

Generate a new complete native graph without cutting edges or selecting samples:

```bash
python3 scripts/la_accel_native3d.py --help
cmake -S accel/lookahead -B /new/round3_host -DCMAKE_BUILD_TYPE=Release
cmake --build /new/round3_host -j 8
ctest --test-dir /new/round3_host --output-on-failure
/new/round3_host/spill_profile /new/native/workload.bin /new/native/layers.bin 127
```

`layers.bin` records integer layers from native RRG `layer_low`, avoiding the old
text export's raw character formatting. The profiler counts actual cross-layer
traversals and logical external queue operations, never FPGA cycles.
`adjacent_pair_read_hits` counts consecutive reads to the same aligned index pair;
it is not a simulated heap-sibling cache hit rate and is not used for the chosen
label-cache ablation.

Run a fresh canonical single-engine cohort with the complete exported workload:

```bash
python3 scripts/la_accel_flow3.py --output /new/hls_single \
  --source accel/lookahead/hls/variants/lookahead_single_resident3.cpp \
  --workload /new/native/workload.bin \
  --define LA_HEAP_TOP=127 --define LA_LABEL_LINES=64 --define LA_COST_LINES=64
python3 scripts/la_accel_bounded3.py --hls /new/hls_single \
  --output /new/bounded_single --minimal-debug
```

For two complete engines, select `lookahead_dual_resident3.cpp`, `--top
lookahead_dual --contexts 2`; replay with `--top lookahead_dual --engines 2`.
Keep all three cache defines unchanged. The runner records engine idle signals,
overlap and activity intervals. The bounded model fixes one shared bank, one native
read/write beat every four clocks, 64-cycle minimum latency, two credits per port
per direction, and fixed global pools of eight read/eight write credits. Address
reservations count against the global pools; ports do not each get a separate bank.
This is a synthetic memory sensitivity model, not calibrated HBM bandwidth.
Overlap counts deasserted `ap_idle` intervals, including memory waits; it does not
count simultaneous useful arithmetic operations.

For the matched label-policy controls use `lookahead_packed_resident3.cpp`,
`--top lookahead_packed --testbench accel/lookahead/tests/packed_real3.cpp`, and
`--define LA_LABEL_WRITEBACK=0` or `=1` in separate output directories. Replay with
`--top lookahead_packed`. Both policies pack the exact FP32 visited bits and expanded
flag into 64 bits, retain 64 cache lines, and include final dirty flush in E1.
The host adapter also verifies external label coherence against the uncached core.

`la_accel_flow3.py` runs csim, synthesis, cosim and implementation in order, freezing
source/Tcl bindings. It accepts an explicit `--period-ns` for a fresh implementation
cohort. A successful tool exit is not proof of positive setup/hold slack. Reporting
uses only timing-clean OOC targets, adds any post-completion memory drain and never
uses C simulation elapsed time as FPGA time. Preserve failed cohorts when retrying.

Use `la_accel_round3_report.py`, `la_accel_round3_validate.py` and
`la_accel_round3_archive.py` with fresh output paths for reports, audits and the
small-input evidence bundle. Figures use `.venv-report/bin/python
scripts/la_accel_round3_plot.py --report /new/report/report.json --output /new/plots`.
The archive includes complete small native workloads, raw CPU/CUDA observations,
source snapshots, RTL counts and implementation reports; it excludes credentials,
build trees, waves and DCP binaries. Final scalability decisions must use matched
bounded RTL time at verified frequencies, not functional-cycle ratios alone.
