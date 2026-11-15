# CPU_PRIMARY runtime fixtures

`generate.py` independently parses the frozen workload binary, applies the exact
eligible-edge filtering rule, and emits two complete small native graphs with
all8/all12 samples. It does not run a model. It writes all runtime memory before
reading the external ALT golden. `validate.cpp` separately uses the production
`Graph`, `dfdesc::Admission` and packed descriptor implementation to compare
every emitted input byte, address, source/target count and expected output
packing. Golden data never belongs to the runtime input directory or loader.

The result root is `results/fpga_cpu_primary_20261115/fixtures_a/`.
Each case has `config.json`, `config.hex`, `samples.hex`, `input/` and
`validation/`. Exact input/golden and all generated file hashes are in the
manifest. `coverage_sources.json` reuses source-bound historical L1 observations;
these observations are not a new core simulation result.

Physical addresses are32-byte **lines**, not bytes. Port is `line&31`, local row
is `line>>5`. All bases are aligned to32 lines. Sparse per-port `$readmemh`
files have `@local_row` followed by a64-hex-digit256-bit word. Element0 is at the
least significant bits. Matching `_valid.hex` files initialize only existing
input rows, not mutable device state. `input/lines.txt` is an equivalent flat
list of full physical line and256-bit data for simulator loaders.

`config.hex` contains22 successive32-bit words. Ordered field names are in
`config.json/config_fields`: magic, version, nodes, prepared_edges, costs, cells,
jobs, groups, row_base_line, edge_base_line, meta_base_line, meta_stride_lines,
descriptor_base_line, descriptor_stride_lines, label_base_line, scratch_base_line,
output_base_line, output_stride_lines, cost_base_line, maximum_line, port_rows,
descriptor_bytes. Magic is0x43504631 and version1. Groups here is the native
workload's sampling-group count, **not** the16 hardware frontend groups.

`samples.hex` contains one128-bit word/sample:
`{sample32, target_count32, source_node32, seed_required32}`. Target count is the
number of unique cells reachable as *eligible target metadata*, not the number
of IPIN nodes and not a golden-derived count. Seed required is target_count>0.
Hardware must initialize canonical labels/PV/directory/output itself and issue
the actual seed operation; no seeded mutable memory is preloaded.

Rows are64-bit CSR offsets, edges32-bit `{destination_cost_index4,destination28}`,
costs64-bit `{delay_FP32,congestion_FP32}`. A descriptor is
`{valid1,cell15,degree16,begin32}`. Descriptors occupy independent per-sample
ranges, starting at descriptor_base_line + sample*descriptor_stride_lines.
The old META region remains reserved but uninitialized: L1 uses DESC and does
not read META. Unused trailing input lanes are zero. Canonical, scratch and
all output ranges are absent from input memory until the DUT writes them.

`validation/sample_Q_pairs.hex` is one64-bit whole pair per actual output cell;
`sample_Q_beats.hex` is the expected complete32-byte export beat, with partial
final-beat padding0x7fc000007fc00000. `validation/output.bin` is the untouched
frozen ALT golden in host `Cost{float delay,float congestion}` order, distinct
from the physical whole-pair bit ordering. The checker must compare all cells
and output ACK/drain; it must not install validation files into external memory.

`cp_sparse_memory.sv` is a TB-only external service model with32 physical ports,
32 tags/port, bounded pending commands, held OOO responses and configurable
latency/issue/backpressure. Interface is the LF physical bus (mv/mr/mw/ml/mtag/md,
sv/sr/stag/sd) plus2-bit status/port. Call `memory.load_native(case_directory)`
while idle/reset, once per graph; it reads only config and `input/lines.txt`.
With PORT_ROWS=512 both native inputs fit (129 and379 used address rows/port).
This compact TB allocation is not a reduced hardware configuration: the same
full core runs; larger legal backing can use a larger PORT_ROWS.

The model rejects wrong owner, range, duplicate/reused tags, writes to readonly
input and reads before input load or DUT write. Mutable data is committed only
at actual write-response handshake; write responses have zero data. The core
must serialize same-address hazards. Reset clears transport state only;
backing memory persists so canonical initialization cannot be skipped between
samples. It does not load expected output or choose responses from the golden.
An accepted command at edgeC is eligible for handshake no earlier than
C+LATENCY_CYCLES; ISSUE_CYCLES is the minimum accepted-edge gap. Jitter is
additional deterministic latency. A held response cannot change when sr stalls.

Native d3 samples1/5 have zero targets; d3 nodes654/cells18 exercise partial
canonical/output words and descriptor tails. Both graphs require multiple
waves. d4 sample10 is a useful stress case (historical13 waves,2339 candidates,
6420 same-word stall observations and K8 peak6). These do not exhaust8192
members or2048 scratch IDs. Integration must retain prior capacity proofs and
add actual admission-overflow tests, rather than claiming small-graph coverage
of every production limit.

After the isolated CPU timing window is released:

```sh
python3 accel/lookahead/fpga_cpu_primary/fixtures/validate.py \
  results/fpga_cpu_primary_20261115/fixtures_a \
  results/fpga_cpu_primary_20261115/fixtures_validation_a
```

The validator freezes its compile closure and compiler/binary hash. The memory
agent is verification infrastructure and must pass its own bounded XSim test
before being used to support a complete-core claim.

The independent validator has passed in `fixtures_validation_a`: all1649/5627
runtime lines, all20 jobs and144/384 expected output pairs. The initial
`fixtures_memory_a` attempt failed at testbench file loading: XSim2022.2 did not
interpret inline string concatenation as the intended filename. The existing
repository's temporary `$sformatf` string pattern fixed this; the failed
attempt remains. `fixtures_memory_b` passed the32-port credit/OOO/hold/write-read
checks and all five explicit illegal-memory rejections. `fixtures_memory_c`
adds actual cost-load reads, including the highest loaded physical line and
the partial final cost beat, using the same unchanged memory-agent RTL.

```sh
python3 accel/lookahead/fpga_cpu_primary/fixtures/test_memory.py \
  results/fpga_cpu_primary_20261115/fixtures_a \
  results/fpga_cpu_primary_20261115/fixtures_memory_NEW
```

Read that run's `terminal.json` before treating it as passing. Negative cases
must terminate at their particular expected assertion; a timeout, unrelated
fatal or a normal return is not accepted as rejection proof. These are memory
agent admission tests, **not** DUT full-core configuration-overflow tests.

`run_full_core.py` freezes the complete30-file production source closure plus
`tb_full_core.sv` and the memory model. `--frozen DIR` uses an existing synthesis
source snapshot, ensuring the functional/timing artifact bindings can be
compared. No DUT parameters are overridden. All native jobs execute within one
runtime-configured graph/batch, including between-sample initialization. The
normal16-cycle memory service and deterministic jitter/request-stall profile
share one elaboration via `memory.configure_service`, called only while idle.

The full-core checker compares every exported256-bit beat including padding,
checks write uniqueness and complete drain, then reconstructs the complete
host binary for byte comparison. It checks source/response accounting per
kind, candidates accepted/emitted, operation retirement and physical held
request/response stability. The20 native fixtures happen to have one finite
output for every eligible target cell; `recorded==target_count` is an explicit
property of these fixtures, not a general reachability guarantee. Empty-frontier
termination can be legal when other graphs have unreachable target metadata.

Per-run `events.csv` records real handshakes: logical requests/returns, physical
issues/ACKs, canonical retirement, external completion and phase transitions.
`analyze_full.py RUN_DIRECTORY` independently checks live identity/tag ownership,
transaction conservation, phase-cycle sums and retirement trace counts, producing
latency distributions and measured occupancy for calibration. These are measured
behavioral RTL cycles, not achieved hardware frequency. `samples.csv` and
`phase_cycles.csv` retain all sample breakdowns; actual exported beats and
`output.bin` retain the full output. Full-core admission negatives cover excess
nodes/cells/costs/jobs, high/misaligned/overflowing descriptor address, insufficient
stride, invalid source/target count and missing job. No malformed cost-nibble
hardware rejection is claimed; native input admission validates that field.

The runtime-configurable memory revision passed `fixtures_memory_d` (2 native
positive protocol tests and5 specific rejection tests). The full-core execution
command is:

```sh
python3 accel/lookahead/fpga_cpu_primary/fixtures/run_full_core.py \
  results/fpga_cpu_primary_20261115/fixtures_a \
  results/fpga_cpu_primary_20261115/fixtures_full_NEW \
  --frozen results/fpga_cpu_primary_20261115/full_synth_b/source
python3 accel/lookahead/fpga_cpu_primary/fixtures/summarize_full.py \
  results/fpga_cpu_primary_20261115/fixtures_full_NEW \
  results/fpga_cpu_primary_20261115/fixtures_a
```

The first complete-core attempt is `fixtures_full_a`. Every invocation writes a
new result directory; never overwrite a previous attempt. `summary.json` is
created only after all3 positive batches and11 configuration rejections pass,
including independent trace audits. `calibration_partial.json` is explicitly a
partial-run diagnostic and is never a substitute for terminal complete-batch
proof. Runtime cost-table values are validated fixture data; no hardware
cost-index admission check beyond the configured table-count bound is implied.

`fixtures_full_a/summary.json` is now terminal PASS: both normal native batches,
all12 d4 jobs under deterministic backpressure/jitter, and all11 specified
configuration rejections completed. Measured totals are:

| Batch | Jobs | Output pairs | Cycles | Physical requests/ACKs |
|---|---:|---:|---:|---:|
| d3 normal | 8 | 144 | 157312 | 4192 |
| d4 normal | 12 | 384 | 268916 | 21511 |
| d4 backpressure/jitter | 12 | 384 | 276758 | 21511 |

All actual outputs are bit-identical to the unchanged historical golden. Every
sample's waves, parents, candidates and publication events also match the
source-bound historical L1 finite model. The actual cycle totals differ:
full-capacity initialization is16384 cycles/sample, accounting for83.32% of d3
normal and73.11% of d4 normal. Baseline physical memory latency is16 cycles;
logical roundtrips include network/front pipeline overhead (minimum25 cycles
for ordinary sources,34 for EDGE and35 for DESC). Use the per-sample/per-kind
measured distributions and phase CSVs for calibration; do not replace complete
batch time with expansion-only time or assume these cycles prove200MHz timing.
The complete30-file DUT source hashes exactly match `full_synth_b/binding.json`.

The harness now accepts `--period-ns` (default5), `--latency-ns` (80),
`--issue-ns` (5), and an explicit `--scenario` label. Decimal text is preserved;
exact integer ratios of those Decimal values implement mathematical ceiling,
without binary-float rounding. Binding/service_config.json record requested
nanoseconds, actual even-integer-picosecond period, service cycles and implemented
nanoseconds. A period must be exactly representable with an even number of
picoseconds; it must also exceed200ps because existing stimulus uses100ps
settling delays. This is a TB stimulus constraint, not a claimed hardware limit.

`--skip-negatives` reuses prior configuration rejection evidence without claiming
new negative runs. `--skip-stress` selects only the two normal native batches for
one declared service scenario. Otherwise the old3-positive/11-negative selection
remains. Stress jitter and request-stall windows retain **core-edge** units and
are labeled explicitly; the scenario label never silently changes parameters.
`--check-config` prints converted values and test selection, creates no output
directory and starts no tools. For example, this is an unqualified arithmetic
check, not an8ns hardware result:

```sh
python3 accel/lookahead/fpga_cpu_primary/fixtures/run_full_core.py \
  UNUSED_INPUT UNUSED_OUTPUT --check-config --period-ns 8 \
  --latency-ns 160 --issue-ns 10 --scenario conservative \
  --skip-negatives --skip-stress
```

It yields20 latency cycles and2 issue cycles (implemented160ns/16ns).
At8ns, the80ns/5ns baseline yields10/1 cycles (80ns/8ns), conservatively rounding
issue spacing upward. Future runs must use `--frozen` for the actually selected
DUT source snapshot; it is copied and hashed independently for each new run.
Clock/plusargs changes affect only the TB and driver, never the30-file DUT.
The old `fixtures_full_a` results remain immutable. Frequency-parameterized
harness changes have Python/CLI and `xvlog` syntax checks only; no new behavioral
or timing result exists until authorized reruns at the selected clock complete.

`compare_full.py OLD_RUN NEW_RUN` audits a semantics-preserving source repair at
the same clock/service: every actual output beat/binary, sample/phase/kind CSV,
complete accepted transaction/retirement/completion trace, and absolute
simulation finish time must match. It writes only the new run's
`comparison_full_a.json`. `--allow-partial` compares completed cases only and
labels its output separately; it is not a final full-regression verdict.
The absolute-time check specifically covers the default5ns clock-driver change.
For intentional frequency/service changes use calibration and qualification,
rather than expecting cycle/time identity with the old run.

`fixtures_full_b` reruns all32 samples and11 rejections after the frozen
`full_synth_c` admin combinational-loop repair. All30 DUT files match that
snapshot; the only DUT change from the previous snapshot is `cp_admin.sv`
(SHA256 `007bbb62dc914cb7a40e11eae0b943aef65b756fd0688d41d6996082538f313c`).
`summary.json` is PASS and `comparison_full_a.json` is IDENTICAL for all14 test
invocations: every output, complete event trace, cycle/phase/kind CSV and
absolute simulated finish time matches `full_a`. This also validates the
parameterized TB's default5000ps/16/1 behavior. `process_identity.json` and
`process_completion.json` preserve the experiment's start identity and terminal
receipt. The original `full_a` proof files remain unchanged. This repair
regression still does not establish an achieved5ns hardware clock.

`fixtures_conservative_a` is terminal PASS for both complete native graphs at
conditional5ns and the predeclared160ns latency/10ns issue contract (32/2 core
cycles), using exactly the same30 DUT +2 TB source hashes as `fixtures_full_b`.
It deliberately skips stress and configuration negatives, reusing their prior
proof. d3 completes in162025 cycles (+4713, +2.996% vs baseline), d4 in282252
(+13336, +4.959%); all output bytes and waves/parents/candidates/commits/retire/
event/physical-traffic counts match the baseline.

`audit_service.py NEW_RUN --baseline BASE_RUN` audits actual physical handshakes
and writes `service_audit.json` only in NEW_RUN. This run observed exactly32
cycles for every one of4192/21511 physical ACKs and minimum issue gap2 on both
graphs. The audit includes per-sample cycle and phase deltas, counter deltas,
output hashes and source bindings. Per-case `calibration.json` retains the
complete logical service distributions (minimum ordinary/EDGE/DESC41/50/51
cycles). `process_completion.json` records terminal hashes and process identity.
These are behavioral cycles under explicit simulated memory assumptions;
5ns is not a qualified complete-core hardware clock.

`fixtures_drain_probe_a` adds only `drain_probe.svh` observation logic to a copy
of the already-passing TB. `run_drain_probe.py` freezes the30 unchanged c DUT
sources, the unpatched TB and the exact patch, then runs the complete conservative
d3 batch. All8 samples pass; complete outputs, event traces, cycle/phase/kind
CSVs and absolute finish time are identical to the original conservative run.
Three CSVs sample q2 relative21520..21545 at each posedge **before NBA updates**:
all global drain gates/T-D live summaries and detailed front10/front11 state.

`analyze_drain_probe.py` validates all26 rows and the registered-idle recurrence.
Measured sequence: front10 DESC input21531, launch21532, D empty/idle0 high21537,
registered idle high21538; front11 corresponding cycles21532/21533/21538/21539.
At21538 all T/D slots are free and every other EXPAND drain condition is true,
but registered front_idle[11] is still0. At21539 that final bit becomes1 and the
complete guard becomes true; FLUSH is visible at21540. This directly confirms
one context-idle register visibility edge in this tail, consistent with the
reported model FLUSH21539 discrepancy. It does not assign every other model
error to that cause. No model or DUT is changed. `probe_analysis.json` contains
source-bound measurements and distinguishes this inference from measured values.

`run_full_core.py --sources-list FILE` now accepts an explicit30-file closure,
which it copies into each run's `sources.json` and hashes. Use the closure that
matches `--frozen`, particularly when replaying historical runs after the
selected dispatcher changes; the live delivery list may refer to a different
module. The restructured dispatcher run uses
`fixtures_restructured_source_a/sources.json`, whose30 source hashes exactly
match `full_synth_e_restructured/binding.json`. Only the dispatcher file and
the complete top's dispatcher module reference differ from the previous DUT.
`compare_full.py --report-name comparison_previous.json` records explicit old
and new run paths, along with removed/added source names, for those comparisons.

The selected `cp_pop_dispatch_restructured` integration is now fully verified:
`fixtures_restructured_source_a/verification.json` records terminal PASS for
52 native samples (base20, stress12, conservative20) plus11 configuration
rejections. `fixtures_restructured_a/comparison_previous.json` is IDENTICAL
against `fixtures_full_b` for all14 invocations;
`fixtures_restructured_conservative_a/comparison_previous.json` is IDENTICAL
against `fixtures_conservative_a` for both complete batches. Every actual
output, complete transaction/retirement/completion trace,19-phase/sample/kind
CSV and absolute simulation finish time is unchanged. Measured cycles remain
157312/268916/276758 for base d3/base d4/stress d4 and162025/282252 for the two
conservative batches. Each run retains terminal, source/service bindings,
process identity/completion, calibration and physical service audits. Their30
DUT hashes exactly equal `full_synth_e_restructured`; no DUT was edited by the
fixture workflow, and no old experiment or result was restarted or overwritten.
This is still5ns conditional functional evidence, not achieved-clock proof.

The wordmux candidate has31 DUT source files: `cp_candidate_wordmux_router.sv`
is added and `cp_candidate_network.sv` selects it. `df_rr_router.sv` remains
required by the output service. The fixture runner now validates a nonempty,
unique explicit source closure and records its actual source count rather than
assuming30 files. This changes source-list handling only; no production DUT
parameter or interface is reduced. `fixtures_wordmux_source_a` freezes the
current31-file closure, verified against both the parent's integration manifest
and `full_synth_f_wordmux/binding.json`; its `eda_source_match.json` records that
exact match. New result directories are `fixtures_wordmux_a` and
`fixtures_wordmux_conservative_a`; old evidence remains untouched.

Wordmux full integration is now terminal PASS:
`fixtures_wordmux_source_a/verification.json` records52 complete native samples
(base20, stress12, conservative20) and11 configuration rejections. Both new
`comparison_previous.json` reports are IDENTICAL against their restructured
predecessors, including every output byte/beat, full accepted event trace,
19-phase/sample/kind CSV and absolute simulation finish time. Totals remain
157312/268916/276758 base/stress cycles and162025/282252 conservative cycles.
Physical service audits observe16-cycle baseline ACKs (stress16..37),32-cycle
conservative ACKs, and minimum issue gaps1/2 respectively. Each run retains
source/service binding, process identity/completion, terminal, summary and
calibration. All31 DUT source hashes match `full_synth_f_wordmux` exactly.
The fixture agent changed no DUT or old results and made no commits; the source
list count accommodation is verification infrastructure only. Achieved clock
qualification remains null and is owned by the parent EDA workflow.
