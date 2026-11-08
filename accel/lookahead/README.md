# STRICT_FP32 lookahead acceleration

This is a new experimental backend, independent of the archived CPU paper and
old online router / integer candidate-cost accelerator. The active experiment
is `results/lookahead_accel_20261108T125500Z`. Read its generated report for actual
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
CUDA uses one warmup plus three measured batches; CPU currently measures one
batch per process, including OpenMP startup. This warmup difference is recorded.

Calibration of a bounded external-memory model, true shared-pipeline context
interleaving, small on-chip cost LUT, geometry-map compression, physical HBM
connectivity and large-graph FPGA projections remain separate work. Do not infer
these capabilities from the presence of independent AXI bundles or caches.
