# Continuous finite enum/commit model

The final candidate is `results/fpga_enum_commit_20261114/model_native_d/`.
It executes the native ALT algorithm using bounded services and produces complete
outputs. It remains a **conditional model**, with no full-kernel frequency or full
RTL cycle-calibration qualification. Current timing totals must not be called a
conservative upper bound, lower bound, measured FPGA runtime or FPGA-wide no-go.

## Performance and functional path

`main.cpp` loads native input, rebuilds the frozen eligible prepared CSR, then runs
`finite.hpp` continuously through every wave in a sample. It never uses old parent
traces, golden candidates or old spill counts to schedule work. The golden is read
only for the final complete-output comparison. No map, dynamically growing per-wave
candidate store or ideal backend sink is used.

* Directory: 64 banks, each 8192 member slots (524288 total), 4096 bucket heads and
  tails; actual versions and stale entries consume slots. One append and one release
  service per bank/cycle; these are phase-separated in this algorithm. Full hardware
  directory RAM latency, forwarding and global min-selection routing remain uncalibrated.
* POP/SEED/COMMIT: eight whole-word reservations/subbank; one synchronous PV read,
  one APPLY and one PV write per subbank/cycle; separate grant cursors. All four
  sectors share a lock. Frozen `pending17::old_op` and `packed_op` are checked
  together. Label writes require actual physical ACK before PV/publication.
* Publication: exactly one held result register/subbank. All append bits of that
  bundle reach the finite directory before its completion. The last append edge
  precedes completion by at least one edge. Zero-event lines and stale POP cannot
  bypass a held bundle. At most one completion/bank/cycle; slot/word reuse is only
  possible next edge. Valid POP has a pre-reserved fork token; stale POP releases it.
* Front: eight groups, each fork16/H16/M16/ready16, eight physical pair lanes,
  E4/lane and beat slots8/lane; D1. Fork reservations skip full groups with persistent
  group RR; successes advance the cursor, including tokens later found stale.
  Reservation/publication and graph/meta/ready/E admissions are at most one/group/cycle.
  Per-group lane RR advances only on successful nonempty E allocation. Zero degree
  parents retain row/meta/output work and do not write E state.
* Row/edge/meta requests use actual physical line addresses. Row start/end are two
  lines when node%4=3; edge beats respect absolute CSR alignment and partial tails.
  Slot reservation precedes request; credit release is physical response acceptance,
  slot release is last descriptor consumption. Pair values are actual FP32 additions
  of immutable parent and cost operands, with contraction disabled.
* Each lane has a two-entry pair pipeline. A real bounded owner router accepts at
  most one candidate/destination-bank/cycle into FIFO16. Four-way/1024-set accumulator
  state and masks hold the actual minimum pairs. Same-set reservation is five clocks.
  New replacement order generates its own spilled payloads, IDs and traffic.
* Expand scratch is one RMW/subbank. There is no imported eight-request concurrency.
  First spill writes; repeats read/merge/write. Finalize waits all expand spill ACKs.
* Enum uses the same `enum_clock()` as the calibration executable: four elastic
  valid stages, one raw register, a synchronous fragment FIFO16 and II2 on enabled
  clocks. It has seven clocks from scan to fragment acceptance without backpressure.
* Finalize scratch has one held query, mergeFIFO16 + one read, and a common
  commitFIFO16. No independent fastFIFO16 is hidden in this version. Fair fast/merge
  selection, atomic consumed OR at one update/bank/cycle, resident/spilled de-dup and
  residual spill scan are explicit. All spilled/consumed words are cleared every
  wave, including consumed bits of never-spilled resident lines.
* Canonical mutation follows full wave reduction. Metadata/output may continue
  across waves of the same bucket; bucket close/target decision and sample export
  wait for that branch. Output whole-pair state is persistent across a sample.
* Output export reads eight BRAM banks (one pair/bank/cycle), forms at most two
  32B beats/cycle through two packing clocks and 16 bounded reservations, writes to
  distinct aligned per-sample device-output ranges, and drains every ACK. Complete
  observed output comes from this packed device-output backing.

All services share 32 physical 32B ports, each 32 credits, shared FIFO64 and return
FIFO4; one physical issue/return per port/cycle. The fixed 80ns/5ns contract gives
16/1 cycles at the assumed200MHz. The model's global FIFO64/tag-at-enqueue/rotating
class scheduling differs from the actual local owner's four FIFO4 queues,
request-register tag allocation and per-client return registers. This difference has
no proven aggregate timing error bound in either direction. Fixed-latency operation
is in-order per port; jitter stress is also in-order even if younger nominal due
points are earlier.

## Complete-sample initialization and parallel CPU execution

Each sample has a charged sample-clear edge resetting the chosen control/arbiter
state, all canonical32B initialization writes and ACKs, PV clear16384 clocks,
output clear4096, directory/free-pool8192, accumulator metadata1024 and bitmap256.
Independent RAM initializations overlap canonical writes; the maximum completion
is charged. Every sample loads **all ten cost pairs with three32B reads**, at an
address after all40 output ranges. Input admission checks every used native cost
index, descriptor encoding,32-bit edge offsets and disjoint physical regions.

Sample state is independent only after these explicit initialization and final ACK
conditions. CPU sample processes can run concurrently, but hardware cycles are
**summed in sample order**. No CPU wall-time parallelism is FPGA speedup. Per-wave
JSONL/CSV records progress; full sample terminal receipts are restart checkpoints.
An interrupted sample is rerun from its real initialization in a new attempt path,
not resumed from an unrecorded partial hardware state. Existing live processes are
never duplicated by the runner.

## Evidence and calibration

* `model_native_d/binding.json`: source closure, exact compiler command/version,
  frozen binary, four native inputs and golden hashes.
* `small_terminal.json`:40 sample runs, d3 eight and d4 twelve samples, each normal
  and response-jitter.
* `full_terminal.json`: BNN40 and LSTM40 normal runs. Each sample has native full
  output, finite counters, wave phase endpoints, progress and a command/start/end/exit
  receipt. Aggregates concatenate outputs in sample order and compare full SHA256.
* `model_enum_calibration_c/calibration.json`:258 cycle-exact scan/fragment events
  for64 no-stall,64 stalled and one singleton. Recorded FR is an external input;
  expected outputs never drive the model. Boundary begins at first eligible scan,
  so reset/DRAIN/flush transition is outside this calibration. Unchanged shared
  `enum_clock`/FIFO source is checked for final-source reuse.
* `model_publication_test_b/receipt.json`: frozen corrected-source fixture, a four-event
  held bundle followed by two zero-event bundles; retire1005/1006/1007, no bypass,
  one completion/cycle and next-edge word reuse. This is a model property fixture,
  not full RTL timing calibration.
* `model_admission_a/terminal.json`: all four inputs' used cost descriptors, address
  ranges and output/cost non-alias checks against the final frozen model source.
* `independent_verification.json`: recomputed complete hashes, phase wall-cycle
  partition, traffic and capacity conservation, three cost requests/sample, aligned
  row/edge counts and full native semantic counts.
* `model_logical_ledger_d.json`: named field bits/counts and external backing.
  It never substitutes `sizeof(C++)` for hardware resources. Full LUT/FF/BRAM/URAM/DSP
  totals remain null. Actual local RTL synthesis belongs to the integration worker.

`fifo_peaks[2]` in the raw model JSON is the configured four enum pipeline stages,
**not a measured occupied-stage peak**; the other FIFO entries are observed bounded
queue/reservation peaks. The independent verifier labels this explicitly.

Early versions are retained: A had over-wide output export and unbounded/bypassable
zero-event publication; B fixed export only and ran small inputs; C fixed publication
and ran full inputs but still loaded only two cost beats at a potentially aliased
address. They are intermediate implementation evidence, not the final timing basis.
D reruns all affected inputs after all known fixes. Compiler/test bringup failures
are implementation failures and do not establish an architecture no-go.

## Reproduction

From a fresh result directory on this server:

```
python3 accel/lookahead/fpga_enum_commit/model/safe_run.py small --workers 4
python3 accel/lookahead/fpga_enum_commit/model/safe_run.py full --workers 12
python3 accel/lookahead/fpga_enum_commit/model/verify.py
python3 accel/lookahead/fpga_enum_commit/model/ledger.py
```

The runner reuses only completed source-bound sample receipts and refuses a new
build over an existing partial result directory. Frozen source is in the result
root. No new GPU runs, old-model runs or CUDA source supplement are performed.

## Final D result (conditional, not hardware qualification)

| Complete resident batch | BNN40 | LSTM40 |
|---|---:|---:|
| Hardware-ordered summed cycles | 52,265,602 | 52,888,942 |
| Conditional seconds @assumed200MHz | 0.26132801 | 0.26444471 |
| Strong GPU target seconds | 0.151799969444 | 0.15949799988888888 |
| Sample init wall cycles | 1,283,840 | 1,303,880 |
| POP+expand wall cycles | 39,827,941 | 40,289,728 |
| Finalize including bitmap clear wall cycles | 11,025,461 | 11,164,694 |
| Output export wall cycles | 126,320 | 128,600 |
| Other seed/bucket-drain wall cycles | 2,040 | 2,040 |
| Fresh actual expand spill fragments | 9,231,456 | 9,426,716 |
| Final scratch reads | 6,986,159 | 7,142,555 |
| Directory members peak/bank of8192 | 3,495 | 3,531 |
| Spill IDs peak/bank of2048 | 880 | 834 |
| Actual pending live peak/bank of8 | 8 | 8 |
| Shared physical credit peak/port of32 | 32 | 32 |

All80 full sample outputs and40 small regular/jitter outputs passed. Both full
concatenated outputs match frozen golden bytes; parents, candidates, waves,
semantic touched/changed line counts and real aligned row/edge requests match the
complete frozen profiles. Source/binary/input checks and independent output/ACK,
transaction, event, directory-member, traffic and capacity identities passed.

POP+expand is the largest **wall-time phase**. It combines real POP, finite fork,
header/metadata/edge access, arithmetic, router/set conflicts and expand spill RMW;
it does not isolate a unique causal module. Giving the entire finalize phase zero
cost would still leave206.200705/208.62124ms in this conditional schedule. This is a
diagnostic subtraction of a measured disjoint phase, **not a necessary bound on
another architecture**. Expandscratch1 could contribute to its own phase, but
fresh traffic and overlapping/full-FIFO counts alone do not establish that it is
the decisive wall dependency. No2/4 scratch-concurrency sweep was started.

The final conditional model misses both GPU targets. Known global arbitration,
directory/RAM/route and frequency calibration gaps can change timing in either
direction. Therefore no qualified FPGA speed, speedup, conservative timing bound
or universal architecture rejection is claimed. Intermediate A/B/C errors were
fixed and rerun rather than called architecture failures.

## Post-run duplicate-launch guard

The delivery `run.py` now checks all original running receipts before submitting
any work, matching Linux PID, full command, boot ID and process birth ticks (or
legacy UTC start). A matching live process or ambiguous same-command start causes
a clear refusal; an unrelated reused PID is not treated as the original process.
It records exact process identity for all future launches. Nonblocking whole-run
and per-sample `flock` locks also close the two-fresh-supervisors race. Completed
hash-verified samples remain reusable checkpoints.

`model_runner_guard_a/receipt.json` records ten cheap self-process sentinel checks,
zero model launches and unchanged frozen D binary hash. This repair changes only
the delivery launcher, not the model or its outputs. The original execution
launcher remains frozen under the D source binding; the repaired delivery helper
is separately bound in `model_runner_guard_a/source_binding.json`.
