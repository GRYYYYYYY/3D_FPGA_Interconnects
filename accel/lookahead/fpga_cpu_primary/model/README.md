# CPU-primary finite L1 model

Current revision g explicitly registers the complete frontend pre-edge idle
predicate before the EXPAND barrier can observe it. The RTL drain probe found
front_idle[11] to be the sole blocker at conservative d3 q2 cycle21538 after
all raw frontend state was empty. g reproduces that registered visibility;
it does not add a constant cycle to each wave. The snapshot covers T/D,
ready/target storage, edge contexts/beat slots/FP activity and all actual
frontend reserve/pop/request/return/target/candidate slices. Reset clears the
register; LOAD samples the empty frontend and INIT creates no frontend work.

The source-bound contract at
`results/fpga_cpu_primary_20261115/model_calibration_g/` verifies52 complete
native samples:20 base,12 continuous-clock stress and20 conservative-memory.
All outputs,19 phase counters, request/retirement counts and72917 logical
requests match RTL exactly including cycle/source/kind/line/id/generation.
This is finite observed calibration, not a universal graph error bound or
formal equivalence. Old f snapshots and its complete80-sample conditional
results are preserved. Actual frequency qualification remains separate.

When request tracing is enabled, `frontend_idle_preedge` diagnostic events
encode the visible mask in `kind` and the next sampled mask in `line`; these
are not memory requests. Existing request comparisons filter event names.

This is a derived, separate model of the production64-lane/16-group core.
Historical LF sources and receipts remain unchanged. The new default is L1
only: independent T128/D128/ready128/target128, E256, beat512, K8 per bank,
64 banks,32 physical ports,32 credits per port. Complete native algorithm
execution determines requests, spill/order, directory events and outputs;
golden bytes are used only after execution for validation.

The model accounts for the new full-core structure explicitly:

- L1 directory commandFIFO2 and responseFIFO2, a64-bank TAKE barrier,
  registered RELEASE launch and actual minimum reduction;
- dispatcher launch, frontend reserve launch/capture, bounded token capture,
  eight actual global command holds and one actual return hold per group;
- canonical32-bit generations, local wire IDs distinct from internal C++
  indices, actual deferred completion/retirement, and whole-word locks;
- all32 independent INIT address cursors, PV16384 initialization, directory8192
  initialization and output4096 initialization; one outstanding cost beat,
  four64-bit configuration writes per full beat and final register settling;
- enum RUN/DRAIN/ENUM/FINISH transitions, direct internal finalize commit to
  canonical pending, scratch RESIDUAL/END/done and256 bitmap-clear edges;
- complete output export, both ACK collection slots and registered completion.

`core_phases.json` and `phase_trace.csv` use the same19 phase numbers as
`cp_full_top`. They are structural predictions, not measured RTL counts.
`compare.py` independently reads the full RTL's phase/counter/output files;
it reports phase and request differences without applying a correction factor.
All sum checks and functional conservation checks remain enabled.

Memory latency and physical issue interval are specified in nanoseconds and
independently converted with `ceil(ns*MHz/1000)`. The physical service enforces
that interval at actual external issue; FIFO waits and return backpressure
are additional. Changing MHz re-executes the algorithm under the changed
service; it never divides historical cycles by a different frequency.

The diagnostic `--jitter` matches `cp_sparse_memory`'s stress contract:
additional `(tag*7+port*3)%17` cycles and a19-edge issue window with14 open
edges. An eligible newest request is selected, and a blocked response holds
its identity. Stress executes samples in order with a continuous physical
clock offset. The default initial offset `jobs+2` comes from the testbench's
job-loading and start/reset edges; every later sample uses the previous
model's complete cycles. `--memory-offset` can specify a different testbench
launch contract. This is not an observed-HBM timing model.

Example small-graph run (both complete8/12-sample graphs):

```sh
python3 accel/lookahead/fpga_cpu_primary/model/run.py model_NEW \
  --mhz 200 --trace --workers 2
```

The runner freezes its compile closure, binary/compiler identity, input hashes,
parameters and every sample output. A live PID/birth lock prevents duplicate
runs; completed receipts are reused only with matching sources/options/output.
A partial output is preserved and requires a new run ID rather than overwrite.
`--reuse-build PATH` reuses a byte-verified binary only when the entire frozen
source closure matches. It does not reuse samples across changed parameters.

Default scenarios come from `experiment_config.json`: base80ns/5ns and
conservative_diagnostic160ns/10ns. Full40 cases require the explicit
`--full-authorized` switch and coordinator selection. The coordinator has
separately authorized base and conservative g full batches at the current
conditional200MHz target, recorded in each run's decision.json. This does not
qualify that frequency; a different eventual selected MHz requires a real
rerun under re-discretized nanosecond service, not rescaling these cycles.
Actual achieved MHz remains a separate qualification field, initially null.

`test_transport.cpp` independently checks nonintegral cycle conversion, issue
spacing, response latency, stress issue windows, full32-bit identity/generation,
finite backpressure, duplicate protection and credit/request conservation at
125/200/333MHz. These are service tests, not a frequency sweep of hardware.

Qualification remains limited until the complete RTL comparison is reviewed.
Historical front/enum/scratch micro-calibration is retained; integration timing
must be checked against the new full-core trace. Exact outputs and total
cycles close to RTL do not by themselves justify a full calibration claim:
phase discrepancies can cancel. No board or routed-frequency result is
produced by this model directory.
