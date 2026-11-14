# Local fabric, independent descriptor storage and publication pipeline

This round starts at `7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec` on
`accel/lookahead-local-fabric-20261115`, in the separate
`3D_FPGA_Interconnects_LOCAL_FABRIC` worktree. It implements the self-contained
[local-fabric instruction](CODEX_FPGA_LOCAL_FABRIC_AFTER_7DD79B2.md).
The source is [fpga_local_fabric](../accel/lookahead/fpga_local_fabric/).
All relative evidence paths below are under
`results/fpga_local_fabric_20261115/`. The final content-addressed archive is
`evidence_snapshot/manifest.json`; it preserves full outputs, raw reports,
source snapshots, failed attempts, simulation vectors and command logs.

The static legal network is much smaller than the old general network, but
still too large for the combined design. The permitted radix-4 fallback
reduces the **actual full 32-port network** to 360,844 LUT. The independent
frontend and real publication/backend contexts pass their local routed 5 ns
checks. Independent frontend storage removes the shared-lifetime penalty but
barely improves on F2. Publication pipelining improves representative sample
cycles, while its actual combined LUT budget still exceeds device capacity.
The selected feasible arithmetic composition is L1. Its complete batch and
software comparison are given in the generated results section below.

**Qualification boundary:** this is synthesizable local RTL plus a complete
finite architecture model, not a fully connected native-kernel RTL or board
measurement. Full kernel fit/clock qualification remains false. An arithmetic
module budget below capacity is only a screen: it excludes global integration
and does not establish placement/routing feasibility. All model seconds use
the explicit conditional 200 MHz, 80 ns external latency, 5 ns physical issue
interval contract. No different-frequency extrapolation is made.

## Legal network and actual resource decision

The generated `network/source_legality.json` and the actual SV/C++ adapters
encode this mapping. A physical line is 32 bytes.

| Source IDs | Service | Reachability |
|---|---|---|
| 0–15 | EDGE read | any of 32 physical ports |
| 16–31 | ROW/DESC read | any of 32 physical ports |
| 32–47 | META read | any of 32 physical ports |
| 48–111 | canonical | two banks per physical port |
| 112–175 | scratch | two banks per physical port |
| 176–207 | INIT/output/cost | its own physical port |

`bank(relative_line)=2*(relative_line&31)+((relative_line>>5)&1)` and
`port=bank>>1`. Every actual base is aligned to 32 lines. A base that is 32
modulo 64 can change the absolute subbank bit; the adapter only uses the
proved physical-port relation, not a false absolute-subbank equivalence.
`address_audit_a` checks all jobs/nodes of all four native inputs and the
highest line for each address class. BNN/LSTM cover 164,104,320/166,668,960
node/sample checks. Maximum valid lines are 90,173,858/91,589,922. The software
admission adapter rejects overflow, illegal kind/source and wrong local owner.
The RTL network's explicit address ABI is **32-bit line**, while front leaves
produce 64-bit lines: the proof applies to these bounded admitted workloads;
a complete 64-to-32 top adapter has not been qualified by a full-top run.

Request identity is source code 6 + kind 4 + generation 32 + local ID 32 =
74 bits. Local codes 48/49 (CAN), 50/51 (SCR), 52 (admin) are meaningful only
at their owning physical port. Full scratch generation and local identity
survive round trips; neither is narrowed to gen8. Front requests have no
256-bit write payload. CAN/SCR return data stays local. Writes have status
and identity ACKs with data forced to zero. Admin cost reads retain and check
actual 256-bit memory data. The adapters' high address inputs have no load
*inside the legality checker*; the full line is separately wired into the
actual request payload.

The first static network uses source-specific generated selectors and
registered arbitration, not tied-off copies of the old 208×128 payload
crossbar. Each port has only two local CAN, two local SCR and one admin source.
Full static synthesis (`network_synth_b`) completed with 605,113 LUT,
199,579 FF and 66,304 LUT-as-memory, with 5 ns specified before synthesis.
Its L1 composition needs 1,498,735 LUT, exceeding capacity by 195,055.
This is the specific evidence allowing the single radix fallback.

The fallback has separate request and return networks, each three stages of
16 four-by-four switches and 64 endpoints. The switches consume destination
bits [5:4], [3:2], [1:0]; shuffle is `((j<<2)&63)|(j>>4)`.
Every input FIFO has depth 4, each output has one held register. There is no
VOQ or scan past a blocked FIFO head. Request destination is `2*port+class`,
EDGE=0 and control=1. Returns target the original source 0–47; 48–63 are
invalid. The admin merge is a real RR2 and output register after the control
network. EDGE's final hold feeds its client FIFO directly. Local paths bypass
both global networks. Each physical port retains four client FIFO4s,
32 tagged credits, request hold, request/response FIFO2s, response FIFO4 and
client return registers. Tags are freed on actual accepted response and cannot
be reused at the same edge. The model **replaces** the old transport; it does
not cascade another hidden physical port or another credit pool.

`radix_synth_a` completes full synthesis/DCP/utilization at 5 ns:
360,844 LUT, 250,425 FF, 104,704 LUT-as-memory, no BRAM/URAM/DSP. This is
244,269 fewer LUT (40.37%) than the static specialization, at the cost of
extra stages, queue storage and modeled HOL blocking. The historical generic
network's 4,868,468-LUT optimistic lower bound remains a different incomplete
mapping result, not an exact utilization report or a routed design.

| Composition / actual module arithmetic | LUT | FF | BRAM36 equivalents | URAM | Decision |
|---|---:|---:|---:|---:|---|
| Static + L1 | 1,498,735 | 767,899 | 1,148 | 640 | area no-go |
| Radix + L1 | 1,254,466 | 818,745 | 1,148 | 640 | 49,214 LUT headroom, screen only |
| Radix + L2 before response specialization | 1,311,586 | 855,545 | 1,148 | 640 | 7,906 LUT over |
| Radix + L2 after response specialization | 1,305,474 | 861,241 | 1,148 | 640 | 1,794 LUT over |
| Device xcu280-fsvh2892-2L-e | 1,303,680 | 2,607,360 | 2,016 | 960 | capacity |

`resource_budget.json` contains every addition and subtraction and report
hash. For L2, 32 actual two-bank contexts include the new directory; the
replaced local fabric and physical FIFO2s are subtracted, and directory is
not counted again. Common old candidate routing, output RAM/ACK collector
and minimum collector retain their actual historical resource evidence.
The distinct whole F2 ROW/META controller was not synthesized here; Fdec's
area is not silently assigned to it. Therefore L1 is the full-batch selection.
There is no claim that either combined design was routed. The final 1,794
LUT overflow is retained, rather than rounded away or erased using utilization
from an unrelated module version.

## Independent frontend storage and service

`lf_front_group`/`lf_front_context` preserve the existing FP32 arithmetic leaf
and 8-byte descriptor ABI. There are 16 groups of four lanes. Per group:
T8, D8, ready8 and target8 are separate. Global E256 and beat512, K8/bank and
POP8 remain unchanged. This is not a capacity-balanced pure representation
comparison with the shared implementation: it deliberately restores separate
lifetimes and pays for that storage.

| Store | Raw declared bits per entry | Entries/group | Actual ownership |
|---|---:|---:|---|
| T | 122 | 8 | state2/gen8/node32/pair64/epoch16 |
| D | 446 | 8 | state3/gen8/node32/pair64/epoch16/raw128/begin32/end32/cell15/three branch flags/mode1/base64/bound32/cells16 |
| ready | 176 | 8 | immutable node/pair/begin/end/epoch |
| target | 95 | 8 | immutable cell/pair/D generation and slot |

These are declaration counts, not LUT or total context resource estimates.
Selectors, FIFO pointers, held requests/responses, output contexts, FP32
pipeline and EDGE contexts are additional and are included in synthesis.
T has reservation and POP-write updates plus one T→D copy per group/edge.
D has one allocation copy, one request selection, one return write and one
decode; graph/target copies each have one bounded enqueue port. State and
branch metadata are implemented in registers; no uncharged multiport RAM is
assumed. T frees only on actual immutable D copy (stale POP frees T without
D). D has its **own generation**, and frees only after both branches have
copied into their independent bounded destinations. Zero-degree graph work
requires no E slot. All reuse uses the next legal edge. The target FIFO and
outer target context are distinct; there is no hidden unbounded output list.

The actual context costs 9,913 LUT/8,897 FF synthesized per group,
158,608 LUT for 16 groups. The old shared F3 context was 150,208 LUT total:
the extra 8,400 LUT is reported explicitly. `front_context_a`, native BNN
and LSTM fixtures and `front_stress_a` validate both 8B/16B decoding, candidate
arithmetic, stale POP, target and generation transitions. The final directed
40-epoch target fixture (`front_target_stress_a`) fills T/D/ready/target to 8,
wraps T generation 17 times and D 16 times, and checks 79,480 candidates,
5,120 descriptor reads, 14,240 EDGE reads in 69,349 cycles. Its target metadata
is deliberately stressed and is not represented as an unmodified native
performance input. The real native batches use the original 8B ABI.

The finite model records per-group T and D residence, D copy→request,
request→return, return→both branch copies, ready→E, occupancy histograms and
T/D-full conditional observations. Stage counters are observations, not
additive wall-time stalls. In the representative BNN sample2, L1 T mean is
57.44 cycles and D mean 51.98; observed minimums are 36/43. Request→return
has minimum 38, while return→branch copies has minimum4 and maximum298.
Much D-full time coincides with E or ready pressure. T-full while D-free alone
is not proof that increasing T removes the critical full-batch wait. No extra
capacity point is selected. Complete-batch diagnostics and the conditional
GPU expansion budget are generated below; congested mean residence is never
used as an invariant latency to promise a faster configuration.

## Publication: enqueue is not retirement

`lf_pending_k8`, `lf_journal`, `lf_directory`, `lf_backend_owner` and their
actual contexts implement the new path. Journal capacity is eight records
per bank and at most32 reserved events. Records hold slot/gen, mask,
issued/ACK state and ordered cursor bookkeeping. Payload stays in the locked
immutable K8 transaction record. Enqueue changes it to PUB_QUEUED and releases
only the publication selector. It does not free the Tx or whole-word lock.
Events issue in FIFO record order into a strict FIFO32 ACK-to-record mapping.
Later records may issue after earlier records' commands are all accepted;
retirement remains FIFO and waits for all actual RAM ACKs. Zero-event records
cannot bypass earlier work. The actual df_ack_slice captures completion,
delivers immutable result/POP at the next edge, and only then returns the
core ACK; the word is reusable one edge after that ACK.

The directory holds8192 members and4096 buckets per bank. The single
next-pointer write port writes a new NIL and the old tail link on distinct
edges. Head/tail and bitmap forwarding handle A/A and A/B/A dependencies.
Member and response slots are reserved before acceptance. Four APPEND
positions plus responseFIFO8 are finite; backpressure holds valid/payload.
MIN/TAKE/RELEASE run only after APPEND pipeline and responses drain. Their
actual control commands/responses cross FIFO2 contexts. All final_done,
next-wave, export and sample-clear conditions wait for the real drain.

The first mapped L2 overflow led to one storage specialization with identical
service: APPEND consumers need only ordered success, so integrated owners
instantiate `ACK_METADATA=0`. APPEND has eight status-only reservations;
MIN/TAKE/RELEASE retain a separate full108-bit response hold. Standalone
`ACK_METADATA=1` also preserves APPEND pointer/bucket metadata for testing.
Identity is not discarded: journal's ordered mapping retains record, slot
generation and event index. The change removes unused response payload copies,
not capacity or acknowledgement edges. Actual backend synthesis falls from
20,507 to20,316 LUT per two-bank context. FF increases from21,081 to21,259;
this is measured, not assumed to be a universal area decrease.

`directory_compact_rtl_a` matches the independent C++ service oracle on all
163,057 edges, including two full8192-member fill/free/reuse cycles. All four
native trace/metrics/transaction/calibration files from
`native_backend_compact_a` are **byte-identical** to `native_backend_context_b`
(`equivalence.json`). ModelD's original status-only semantic consumer is
therefore unchanged; its frozen binary is reused, not rebuilt under the same
receipt. Controls retain actual payloads and are checked by ordered MIN,
TAKE chain and RELEASE traversal after the native waves.

| Local evidence | Observed result |
|---|---|
| Same APPEND stream, old directory leaf | accept interval6 |
| Same stream, explicit old deferred-wrapper contract reconstruction | accept interval8 |
| New actual RAM APPEND pipeline | accept and RAM-ACK interval2 |
| `publication_context_f` | 1,472 transactions,500 commands/actual RAM completions/event ACKs,1,472 true core retirements |
| Same-word/protocol pressure | 85,830 same-word stall observations,32 credits reached,975 out-of-order responses |
| Native backend final context | 16 cases/19 waves,318,715 candidates,25,873 canonical completions,23,844 directory events,75,868 physical requests |

The interval8 test is explicitly a reconstruction of the old model wrapper
contract, not a newly measured historic end-to-end RTL chain. The final native
context checks an independent canonical/PV/directory oracle and actual RAM
readback; it does not inject the expected PV result into the implementation.
Trace `publication_context_f/publication_trace.csv` distinguishes enqueue,
command accept, RAM-visible completion, event ACK, external completion and
**actual core retire ACK**. External completion→core retire is exactly1 edge
for all1,472 operations. Enqueue→true retirement means for0/1/4-event records
are4.011/10.641/94.483 cycles (ranges3–23/9–26/15–302); the large4-event mean
includes long forced backpressure. These are response latencies, not claimed
sustained II2 whole-word retirement. The native full-context metrics also
retain per-bank commit and retirement spans. Earlier context_e trace named
external completion “retire”; it is preserved but superseded by context_f.

## Protocol, model and actual physical checks

The adapter/transport independent tests include distinct non-echo memory
payload, cost-read data, write ACK, long response blockage, wrong owner/kind,
full generation, credit reuse and OOO delivery. Static transport's383,129
transactions were compared against the composed old primitives, but that
static intermediate is not used for final performance. The fallback's4096
source/destination combinations are exhaustively reachable. Its independent
8,192-packet test is matched to RTL on all1,357 edges; the full network test
uses208 sources/32 ports and19,968 requests, checks held request/return
stability, and finishes in1,503 cycles with2,905 local advances while front
returns are blocked. Internal tagged credits reach32 (external FIFO observation
peaks30); these are different observation points. HOL is retained and counted.

ModelD executes the real finite algorithm, actual initialization/cost loads,
new request order, spill allocation, all waves, target work, directory/PV,
output backing and ACK drains. Frozen golden bytes are read for validation
only and are not used to drive its work. ModelsA/B are intermediate static
network contracts; C is radix with control FIFO2s; D adds diagnostics. All160
small normal+jitter executions of D pass, and are cycle/output-identical toC
(`observation_equivalence.json`). Final comparisons use only frozenD. Native
source/binary/compiler/include closure and input/golden hashes are in
`model_d/binding.json`, each full sample has its own receipt and complete
output. Each sample performs explicit initialization/sample clear and ends
fully drained. CPU parallel execution reduces experiment wall time only;
hardware batch cycles are summed in original sample order.

The new local RTL is calibrated at primitive/front/backend context scope.
A fully connected frontend→global network→all backend banks→controller RTL
chain is not calibrated. `finite.json` explicitly retains that qualification
limit. The following are actual routed contexts, not a substituted full-kernel
frequency:

| Actual5ns OOC | Setup WNS ns | Hold WHS ns | Pulse WPWS ns | Methodology |
|---|---:|---:|---:|---|
| Independent frontend | +0.251 | +0.019 | +1.968 | 0 violations |
| Publication + real directory/control context, pre-compaction | +0.012 | +0.020 | +1.800 | 0 violations |
| Full local backend/context, pre-compaction | +0.033 | +0.009 | +1.800 | 32 SYNTH-5 warnings |
| Full local backend/context, final compact responses | +0.007 | +0.009 | +1.800 | 32 SYNTH-5 warnings |

All use input/output min0.100/max0.800ns; no relaxed min-delay or internal
false paths were introduced. All12 check_timing coverage categories are zero.
Final backend all43,395 routable nets route without errors. The32 methodology
warnings are scratch replacement storage mapped to distributed RAM; actual
LUT RAM is in the budget. The final RTSTAT-10 lists1,794 output-only nets:
`rtstat10_connectivity.csv` verifies all are HIERPORT, no leaf input sinks and
one output port, not missing internal consumers. This1,794 is independently
coincident with the LUT overflow; the two counts are unrelated.

Vivado2022.2's OOC warnings about missing HD.CLK_SRC/HD.PARTPIN_LOCS remain:
upstream clock placement/skew and external physical port wiring are not
qualified. Internal launch/capture and ready/valid fanout are real; these
reports do not establish an integrated device clock or board timing. The
full network has synthesis-only 5ns constraints and unconstrained external
IO; it is not given a routed-clock certificate. Detailed warning categories,
including accepted generate syntax, discarded dead destination bits, actual
register mappings and inherited harmless stage0 placeholders, are in
`warnings_analysis.json`. Original warning-summary parsing failures and
compilation/testbench corrections remain in the archive.

## Fixed representative comparison and gates

The predeclared samples are BNN2/19/35/31 and LSTM7/19/18. All28 runs pass the
same complete ALT output checks from actual initialization. FS is the shared
F3 lifetime; L0 is F2, L1 independent T/D/ready, L2 L1 plus journal/APPEND.
All share the same radix network, lane/E/beat/K/POP and physical resources.
No unfavorable sample or long tail was removed.

| Configuration | BNN4 cycles | LSTM3 cycles | Scope |
|---|---:|---:|---|
| L0 | 7,310,933 | 5,542,918 | new-network F2 comparison |
| FS | 9,259,951 | 7,036,046 | shared-lifetime control |
| L1 | 7,308,619 | 5,540,660 | selected feasible arithmetic composition |
| L2 | 6,611,954 | 5,014,153 | area-failing conditional representative only |

L1 reduces L0 time by0.03165%/0.04074%, while shared FS takes26.70%/26.99%
more than L1. Thus separate lifetimes matter, but these results do not show
fusion materially beating F2. The extra storage cannot be justified as a
large speedup over F2. L2 reduces L1 total time by9.532%/9.503%; finalize
falls32.594%/32.872%, while pop+expand rises slightly due to changed service
ordering. Real spills are recomputed (BNN4 L1/L2:1,257,277/1,254,701;
LSTM3:957,552/957,453). No trace-derived speedup is substituted for this run.

L2 did not qualify for full batch because its actual resource screen fails.
L1 qualifies for the full diagnostic batch under instruction7.3 because the
new full-size network has decisive actual area improvement and L1 has a
feasible module arithmetic budget plus correct local RTL. Seven identical
completed representative samples are reused; only73 new samples are launched.
Whether full top is entered is determined from this complete batch, not from
extrapolating four representatives or dividing old cycles by a new clock.

## Reused software and native identity

`reused_evidence.json` verifies254 GPU receipts, six historical P8/F0 batches,
the CUDA supplement/source closure and the old descriptor archive's complete
hash chain. No GPU or old-model job was rerun. The strongest qualified
resident CUDA means remain BNN0.15179996944444446s and
LSTM0.15949799988888888s, based on three independent processes with three
formal repetitions each; nine repeats are not nine independent processes.

The original input arrays, unchanged8B descriptor conversion/arithmetic,
frozen ALT golden, imported native output and wire maps retain the previously
qualified transitive native identity. Identical new complete ALT outputs
support that reuse; this is not a new native VPR run. ALT is not bitwise STRICT.
Existing STRICT differences and both historic positive/negative results remain.
CPU cohorts stay separate: H100-worker Xeon8462Y+ prepared8-thread
3.654426308/3.669705272s; FPGA-server Xeon6530 packed8-thread
2.842626751333/2.933218058s. No cross-host format attribution is made.

Resident scope includes necessary device initialization, all memory work and
output ACKs. E2 includes the deployment's construction/check, transfers,
execution and readback; native VPR Process is a third separate measurement.
No board transfer, new E2, new VPR Process or amortized construction time is
invented, and no resident ratio is spliced into those scopes. Publication and
network changes do not justify repeating unrelated CUDA work. The fusion
candidate is not close to the resident target or qualified as a complete
kernel, so no additional same-representation CUDA optimization is triggered.

## Reproduction and preservation

The complete binding/commands for each XSim run are saved beside its frozen
source. Invoke `delivery/simulate.py` with a **new** result directory and those
source/data lists; it runs xvlog, xelab and xsim through the installed2022.2
tools and demands explicit TEST_PASS with no fatal/error. Synth/OOC `run.tcl`
files and `context.xdc` are frozen. Reuse an idle MCP Tcl session and source
the appropriate script in a new directory; never rerun into an immutable
receipt directory. There is no requirement for a GUI or a new tool version.
The Ross RTL-simulation and timing-methodology skills guided the local flows.

The finite runner command is:

```sh
LF_MODEL_RUN=model_d python3 accel/lookahead/fpga_local_fabric/model/run.py full --configs L1 --workers 16
python3 accel/lookahead/fpga_local_fabric/delivery/resource_budget.py
python3 accel/lookahead/fpga_local_fabric/delivery/analyze.py
python3 accel/lookahead/fpga_local_fabric/delivery/evidence_summary.py
python3 accel/lookahead/fpga_local_fabric/delivery/archive.py evidence_snapshot --verify
```

On this workspace the first command reuses all completed receipts, checks
output and frozen source hashes and refuses duplicate live runs via process
birth identity and locks. On a new checkout, restore archive evidence first;
shared input/old-evidence paths remain explicit in receipts. To re-execute a
changed model choose a new LF_MODEL_RUN name. Source derivation scripts depend
only on immutable base-tree modules and the tracked new source; do not rerun
derivation during a source-bound experiment.

Compiler/EDA executables, large regenerable vendor trees and DCPs are kept on
the shared filesystem with hashes/paths, not embedded in Git. Full output
bytes, reports and test vectors **are** archived. Read-only connectivity audit
initially failed without report_drc; the successful corrected audit is kept
alongside its original log. Historical files are referenced rather than
repacked. Final protection checks compare all19 original branch heads and
require no modified pre-existing tracked path. The normal commit and push
change only this independent branch; remote full-SHA verification is recorded
outside the immutable archive to avoid a self-referential commit receipt.

## Complete selected L1 batch and final decision

Both full40-sample outputs pass. The7 already completed, source-identical
representatives were reused. The80-sample terminal receipt is
`model_d/full_L1_terminal.json`; no performance run remains active.

| Metric | BNN40 | LSTM40 |
|---|---:|---:|
| Total cycles | 72,317,544 | 73,419,021 |
| Conditional seconds at200MHz | 0.361587720 | 0.367095105 |
| Strong resident CUDA seconds | 0.151799969 | 0.159498000 |
| Conditional FPGA/GPU time ratio | 2.382001270 | 2.301565570 |
| init cycles | 1,284,240 | 1,304,280 |
| pop_expand cycles | 48,862,467 | 49,650,643 |
| finalize cycles | 22,008,522 | 22,298,917 |
| export cycles | 126,640 | 128,920 |
| other cycles | 35,675 | 36,261 |
| parents | 102,918,965 | 104,730,480 |
| candidates | 1,286,937,147 | 1,309,512,712 |
| waves | 2,161 | 2,200 |
| spills | 9,115,590 | 9,301,986 |
| scratch_final_reads | 6,948,998 | 7,103,262 |
| events | 102,926,941 | 104,741,797 |
| pop_transactions | 102,924,851 | 104,739,179 |
| stale | 5,886 | 8,699 |

| Full ALT output | SHA-256 |
|---|---|
| L1 bnn_export | `a8ca4003a3b015145635a3f776bb62a3aec1ec2121a1fbfc8712d2a2dc1c8c3f` |
| L1 lstm_s2 | `6b2acd7718d880075d653b3b83f1fa3abb5161f6f346ed39c3aa1285160a95cf` |

Both cases remain slower than the strongest resident GPU, so the instruction7.3
full-top gate is **not entered**. This is a performance no-go for this selected
configuration under its stated simulated memory contract. L2 has a separate
actual resource no-go. No full-kernel timing, smaller-graph full-top stand-in,
board timing or same-representation GPU rerun is claimed. This does not rule
out other FPGA architectures.

The old F2 full totals were71,238,001/72,236,324 cycles. The new L1 totals are
1.515%/1.637% higher; reducing area by adding real radix stages was not a free
latency improvement. Old generic-network F2 did not have implementable whole
network area, so its speed cannot establish hardware feasibility either.

With measured L1 initialization/finalize/export/other held fixed, matching GPU
would leave only6,904,916.89/8,131,221.98 expand cycles. Required valid-parent
rates would be14.905/12.880 per cycle, compared with observed2.1063/2.1093.
Including stale POP makes required T rates14.906/12.881, beyond unchanged
POP8. Required candidate rates likewise exceed64 lanes. Using only observed
minimum T/D residence gives diagnostic Q≈rL counts537/641 for BNN and464/554
for LSTM, already above128; congested means are explicitly not used to size
a new design. These calculations hold other phases fixed and are not a bound
on an alternative algorithm or a simultaneously changed backend.

BNN/LSTM complete-run D-full observations include E-full227,636,280/234,027,069
and ready-full193,879,549/199,271,403 group-cycles. These categories overlap;
they are not additive wall-time losses. D-full with every downstream pool
free still occurs106,708,126/108,904,691 group-cycles, but does not isolate a
single sufficient capacity repair. T-full/D-free alone is also insufficient.
No additional T/D/ready point is selected. The fixed whole-batch expansion
budget and the long downstream waits do not support claiming a single pool
increase closes the gap.

Critical-final observers select the last genuinely busy bank for each wave,
then retain its mutually exclusive priority labels. Publication-held occupies
17,525,818/17,803,739 of22,008,522/22,298,917 final cycles (79.63%/79.84%).
That is state occupancy, not removable pure stall. The actual journal RTL and
L2 representative finalize improvement substantiate a publication opportunity;
they do not justify deleting all publication-held cycles. Even subtracting
all L1 finalize cycles as a diagnostic leaves251.545110/255.600520ms, above
GPU. This subtraction is not a new simulated design.

The full stage, pool, per-port traffic, dynamic peaks, new spill counts,
exclusive tail histograms and per-stage radix HOL/link counters are available
in `full_pool_bnn_export.json`, `full_pool_lstm_s2.json`, per-sample
`finite.json`, `pool_service.json`, `radix_service.json`, `capacity.csv` and
`waves.csv`. Raw `finite.json` never calls its conditional result board time.

The network area problem is materially reduced and the local mechanisms are
implemented and tested. Independent storage recovers the shared-token penalty;
publication improves actual retirement behavior while preserving whole-word
and directory correctness. The selected full composition still misses the
GPU goal and the more performant L2 representative composition still fails
area. These are the completed round's results, not a promised FPGA win.
