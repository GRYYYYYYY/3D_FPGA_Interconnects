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
