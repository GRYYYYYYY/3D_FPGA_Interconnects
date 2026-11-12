# Complete graph prototype and bounded scan-controller model

This extends the first owner delivery. `graph_control.sv` consumes runtime CSR,
node/cost/job/cell arrays; generates FP32 pairs through `pair_lane`; drains all
owners; commits labels; closes buckets; and writes every real sample output.
The d3/d4 inputs are complete batches, not precomputed frontier or proposal traces.
`export_graph.cpp` only changes memory layout and computes an independent original
ALT oracle. Native `{delay,congestion}` pairs are explicitly packed with delay in
the high word for unsigned lexicographic comparison. The output checker reverses
that packing before comparing native byte output.

The selected implementation has Q=1 and 64 `pair_lane` instances / 64 real owner
services. An 8-owner parameterization is also exercised. The graph front end has
**one blocking request outstanding**, emits a candidate to the next lane, and uses
a registered, round-robin shared candidate bus. It does not sustain 64 edges per
cycle. This is a material implementation bottleneck, not a free parallel front end.
Each lane owns operand registers and an elastic arithmetic/output stage; independent
registered operands make independent arithmetic state explicit, correcting the
first prototype's shared-operand structure.
The global fence waits for both input and output stages. `verify_lanes.py` requires
64 material lane modules in actual synthesis/routed utilization, including private
state and FP32 logic. The graph source remains serial; physical lane count does
not establish sustained 64-edge throughput.
All 32 memory channels are shared by graph/control traffic and proposal owners.
Each channel has a registered request buffer, rotating arbitration, and response
routing with at most one accepted response per owner per cycle. Proposal base must
be aligned to 32 physical lines. Owners 0/32, 1/33, ... then share each channel.
For the tile, each owner can access four of the 32 channels; response arbitration
therefore matters. Runtime configuration rejects a misaligned proposal base.

Immutable job target counts are prepared during external input conversion, as in
the software baseline Prepared phase. Runtime target reads, closure flags, output
updates and completion checks are timed.

Directory membership is represented by external `pending[N]` words, with keys
below 4096 and a checked 524288 live-member limit. This deliberately simple finite
layout uses full scans, not a linked chunk allocator; the template's proposed
16384 chunk pool is not allocated. `closed[N]` words hold the closure set. There
is no free map lookup or free copying of N labels/proposals: the controller
initializes the homes and scans/reads/writes them through the same bounded memory
interface. This choice makes the complete graph prototype slow, especially on
large N, and its negative results must be retained. Wave-start labels are immutable
until global fence. Proposal home persists monotonically; every cache is flushed
and invalidated each wave. Sample initialization overwrites labels, proposal,
pending, closure flags, and output. No epoch counter can alias.

The testbench models 32 channels with 64 outstanding each, 16 abstract banks,
32-byte transfers, bank reissue gap 8 cycles and direction-change gap 4 cycles.
Read/write bandwidth is shared. Central latency is 60 cycles at an **assumed**
200 MHz (300 ns). Integer-cycle link gaps conservatively quantize the requested
64/128/192 GB/s to 51.2/102.4/102.4 GB/s. The last two therefore coincide in this
model; they are not claims of measured HBM bandwidth. No CDC is present.

`model.cpp` executes the same finite pending-scan algorithm from graph inputs.
Golden output is read only by its checker, never to supply active vertices or
memory responses. Complete non-improving scans are aggregated only when their
serial request interval, no-live-transaction condition, bank gap and link bounds
allow exact aggregation. Reads/writes of every node still count as actual 32-byte
transactions. Cache/memory actions are scheduled as finite events; dirty slots
are capped at 16, outstanding at 64/channel, and every fence waits for write acks.
Owner request scheduling is an event approximation validated against the RTL:
covered workloads have at most one active miss per owner and zero modeled front
backpressure. This does not qualify arbitrary saturated request streams; the
separate single-owner cycle model/tests cover the 32-MSHR/64-FIFO stress domain.
All phase errors, including the fence approximation, are reported. CPU model
execution time is never called FPGA time. With no full OOC-supported clock, the
200MHz conversions remain **projected** despite RTL cycle calibration.

`attempts/shared_arithmetic_v1/` preserves the earlier shared-input prototype,
all its completed full-batch runs, RTL/calibration, source, and the deliberately
stopped OOC. The independent-operand revision adds one cycle to candidate arrival
and fence bookkeeping in the model and reruns every full scenario; no cache/lane/
context parameter search is performed. Native bridge/QoR may be reused only after
the new complete output bytes match the actual prior imported model bytes exactly.

Reproduction (repository root, original input paths in `config/inputs.json`):

```bash
# Generate complete runtime image and independent expected sample output.
g++ -O2 -std=c++17 -Iaccel/lookahead/round6_1 -Iaccel/lookahead/include \
 accel/lookahead/fpga_sim_restart/closed_loop/export_graph.cpp -o /tmp/export_graph
/tmp/export_graph INPUT.bin RUN_DIR
bash accel/lookahead/fpga_sim_restart/closed_loop/run.sh RUN_DIR 8 60
# Verilator is extracted under this run's tools directory, not installed globally.
bash accel/lookahead/fpga_sim_restart/closed_loop/build_verilator.sh 64 _final
python3 accel/lookahead/fpga_sim_restart/closed_loop/run_rtl_final.py
python3 accel/lookahead/fpga_sim_restart/closed_loop/calibrate.py
# Reproduce in a separate result copy to preserve the original evidence.
FPGA_OOC_SUFFIX=_fixed LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libudev.so.1 \
 /inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado \
 -mode batch -source accel/lookahead/fpga_sim_restart/closed_loop/synth.tcl -tclargs 64
# After routed.dcp exists, inspect_physical.tcl reports SLR/clock/boundary properties
# and separate internal-register setup/hold at 200/125MHz, without changing the route.
```

The executable model takes `INPUT EXPECTED_NATIVE_OUTPUT OUTPUT_PREFIX OWNERS
F0|F1 LATENCY_CYCLES BANDWIDTH_BYTES_PER_SECOND`; it writes all native output pairs,
per-qid completion receipts, traffic per array, cycle phases, and high water marks.
Build it with the frozen floating-point flags:

```bash
g++ -O3 -std=c++17 -ffp-contract=off -fno-fast-math \
 -Iaccel/lookahead/round6_1 -Iaccel/lookahead/include \
 accel/lookahead/fpga_sim_restart/closed_loop/model.cpp -o /tmp/owner_graph_model
/tmp/owner_graph_model BNN_INPUT.bin EXPECTED_NATIVE.bin OUTPUT_PREFIX \
 64 F1 60 128000000000
```

The output prefix must be in an existing directory. Actual input paths and hashes
are in `config/inputs.json`; the expected native outputs are the full F1 replay
outputs under this run's `replay/`. The expected file is used only by the final
checker. `compiled_model_cpu_binding.json` binds the delivered executable hashes
and exact compiler/flags; host model elapsed time has no hardware-time meaning.
F0 is a modeled explicit line RMW control. The complete graph RTL is F1; F0 is not
claimed to have its own complete RTL/OOC calibration. `run_large.py` queues the
predeclared full BNN/LSTM cases after the initial BNN central F1 passes.

`native_roundtrip.py` uses the actual model output, the independently qualified
original ALT native input capture, and the existing native import bridge. It
checks exact full sample output before invoking VPR, then exact final wire-map
SHA after the run. Old STRICT or golden files are never changed. This is an
**offline correctness round trip**, not live FPGA execution or device timing.

`collect_baselines.py` preserves historical raw data and extracts only valid
resident timer boundaries. Basic CUDA6's old event and E1 interval include final
D2H, so neither is relabeled. `gpu_worker.py` prepares a timer-only CUDA6 variant
plus the existing compact CUDA61 benchmark, three fresh processes × one warmup
and three complete measurements. It has not run when Inspire authentication is
unavailable. Original VPR E2 remains a separate, unmatched baseline.
Existing native original ALT CUDA `LA_LIVE.resident_s` is also retained for BNN
and LSTM: three independent first solves, explicitly separate from nine warm
compact measurements and from legacy CUDA6. Recorded GPU intervals include host
output-vector construction; no unmeasured subtraction is applied.

The CPU main cohort is repeated after pinning owned Vivado threads to socket0
and the benchmark to socket1, cores32–39. Earlier samples with unrestricted tool
affinity are preserved under `attempts/cpu_before_tool_affinity`. Other users and
the shared memory fabric remain uncontrolled. `execution_deviations.json` records
the earlier overlap of up to three Vivado jobs despite a planned maximum of one.
`audit_bindings.py` verifies frozen functional sources, OOC/RTL source hashes,
the final simulation executable, all 12 actual native output files, and calibration.
`reject_config.py` uses that unchanged final RTL executable to check five invalid
runtime configurations: zero nodes/jobs/cells, excessive node count, and a
misaligned proposal base. Every case must raise the DUT error and publish no
complete output. This admission test does not cover dynamic member-pool overflow.

`cold_supplement.py` records explicit nonoverlapping cold-call assumptions, real K=1,
same-invocation historical native module shares, and a deliberately optimistic
non-proposal transaction lower bound for this particular serial front end. It
does not turn transfer assumptions into FPGA measurements or change the main scope.

## GPU V2 supplement after authorization recovery

The successful H100 job `job-0afcca08-4376-45b4-9711-61940a922bad` runs `gpu_worker.py`: four complete inputs, basic/compact CUDA, three processes per configuration, one warmup and three measured batches per process. All 96 batches must match. No original CUDA algorithm file is modified; generated timer-only variants retain their source and binary hashes in the supplement.

Run `collect_gpu_v2.py` to verify all process receipts, all output bytes and all raw measurements. After refreshing the authoritative platform status into `closed_loop/gpu_v2/latest_status.json`, run `publish_gpu_v2.py` **after** the earlier `finalize.py`/`archive.py` workflow. This updates the report/configuration and writes a separate `gpu_v2_supplement` archive and SHA index. The original evidence snapshot remains the immutable delivery at `cde531d0fb54a54e76e97aa6108fd4f237a1b847`; its source/report hashes describe that commit. The supplement binds the current files and supersedes only the expired-authentication/pending-GPU status. CPU and GPU measurements are not paired on the same host.
