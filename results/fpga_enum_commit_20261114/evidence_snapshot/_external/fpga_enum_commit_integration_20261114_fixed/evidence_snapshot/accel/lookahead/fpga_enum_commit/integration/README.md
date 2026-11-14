# Two-subbank backend integration

This directory owns the actual old/new owner wrappers, shared-port calibration,
and the local matched native/stress replay. `budget.py` and `project_native.py`
are main-agent artifacts and were preserved.

`ec_backend_owner.sv` combines either the actual old `inf_flat_bank` enum5,
`inf_scratch_boundary`, and bank-serial `pending17_service`, or the new
`enum2_bank`, `scratch_finalize`, and `ec_pending_k8`. Both variants use the same
synthesizable `ec_tagged_port` with four clients, one physical 32B port, 32 total
credits, four request entries/client, four physical return entries, and one
registered response/client. Scratch addresses add `0x100000` lines and preserve
the physical owner stripe. All canonical and scratch traffic is charged.

A canonical PUB bundle remains stable while the adapter sends each directory
event at most once. The adapter asserts canonical `ordy` only after every event
has actually handshaken and the completion/POP-token consumer is ready. Thus
whole-word reservation covers ACK, PV write, directory retirement, and valid
POP publication. The K8 transaction records themselves reserve 8x4=32 event
slots/bank. There is no outer FIFO-admission shortcut for word release.

The owner joins core/scratch done, canonical idle, directory retirement and
fabric idle. The baseline resets only its pending service on a drained sample
boundary and performs the actual 16384-cycle PV clear; the candidate uses its
real `sample_clear`. Neither variant freely resets between waves. The scratch
bitmap's actual 256-cycle clear is allowed to complete between waves.

## Final fixed-contract evidence

The final main run is
`results/fpga_enum_commit_integration_20261114_fixed/sim_d/`.
Its exact compiled source closure is in `receipt.json` and `source/` (nine DUT
files, the testbench, and the invoking Tcl). Every one of 75868 physical
responses per variant occurs exactly 16 clock edges after its request. This is
the 80 ns/5 ns condition at an assumed 200 MHz. Response acceptance would wait
for `sr` if backpressured; the main run has no injected external stalls.

Sixteen fixtures comprise all 13 frozen owner0 native projections and three
stress fixtures; the latter each run two waves. There are 19 wave runs/variant,
38 matched wave runs total. Native fixtures preload their real canonical wave
prestate and freshly clear PV. They do not inject historical PV state through
hidden RAM writes. All accepted candidates build an independent proposal;
every line enters canonical commit exactly once; all final 32B canonical lines
match the native after-image. Transaction status/old pair/mask/all four event
arguments and new whole68-bit PV are checked against the frozen transform.
Every directory event is checked for exact node/argument, no duplicate, and
presence before reservation release. Request/tag/response/ACK conservation and
all relevant done/fence conditions are asserted.

| Native owner projection | Old cycles | New cycles | Old/new |
|---|---:|---:|---:|
| BNN wave19_32 | 201847 | 94408 | 2.138 |
| BNN wave2_38 | 175665 | 79107 | 2.221 |
| LSTM wave19_30 | 188854 | 81476 | 2.318 |
| LSTM wave7_36 | 175468 | 77586 | 2.262 |

The hot-set spill fixture is almost unchanged (92331/92096 and 92103/92073),
consistent with retained serial expand spill RMW. Empty waves take 6/7 cycles;
one small native wave takes 64/70 cycles. These negative cases are retained.
The faster backend does not establish full-graph performance.

`transactions_{0,1}.csv` and `analysis.json` distinguish enum fragment emission,
canonical acceptance interval, transaction feedback latency, and final
ACK+PV+directory retirement interval. For the four large projections, mean
per-bank retirement intervals fall from roughly33-36 to6.0-7.3 cycles, while
per-transaction feedback latency increases due to the registered concurrent
pipeline. They are different metrics. `phase_analysis.json` uses wall-clock
boundaries and never sums overlapping busy/context time: the interval after the
last accepted candidate falls from ~100k-119k to~18.5k-24.7k cycles; retained
expand costs still matter.

`calibrate_port.py` is an executable finite-cycle port model. Starting from an
empty fabric, it consumes only external boundary inputs (valid payloads, client
ready, physical request ready and response). It predicts all DUT client-ready,
request arbitration, tag assignment, registered payload issue, physical-return
ready and registered client-return outputs. Exact replay passes 8335 baseline
and 2974 candidate cycles, not merely equal aggregate completion time. Canonical
stage replay is separately supplied by `canonical/verify_trace.py` and its F
receipt; enum pin/cycle and scratch handoff replay are supplied by the enumerator
worker. This composition is local service calibration, not a calibrated full
64-lane/64-subbank architecture model.

## Preserved intermediate evidence

`results/fpga_enum_commit_integration_20261114_a/sim_b/` retains the earlier
jitter/backpressure passing run. Its memory fixture was conservative by one
edge (nominal eligible-response latency17..29 cycles; acceptance can be later under pressure), so it is stress evidence only. The
original fixed `sim_a`/`sim_b` are explicitly marked superseded: a clock-boundary
audit found all physical responses accepted at17, not16 cycles. The corrected
`sim_c` fixes negedge response preparation and independently verifies
histogram `{16:75868}` for both variants; final `sim_d` retains that exact
contract and complete native/stress interface traces. No performance claim uses the
superseded fixed runs.

`failure_01_no_progress/` preserves the original source/logs from a TB filename
construction failure. Portable formatted strings replaced the problematic
`$readmemh` filename expressions and the same fixtures then passed. This was a
verification setup error, not an architecture negative result.

The first OOC used an unfortunate PV RAM coding style that produced 121556 LUTs
for the local chain. Its source, synthesized DCP and resource report are frozen
under `...integration_20261114_a/ooc_a/`. It was explicitly controlled-stopped
as `CANCELLED_SUPERSEDED_RAM_INFERENCE_FIX`, not reported as timing PASS/FAIL.
The canonical worker proved the single-write-site PV repair exactly
cycle-equivalent and inferred 4 URAM/bank; the enumerator worker proved the
explicit-width isolated occupied RAM template pin/cycle-identical and inferred
BRAM. Both repaired sources are in the final main simulation.

## OOC and limits

`run_ooc_b.tcl` implements the complete local chain, including the actual
shared arbiter, full14-bit PV and SET_BITS10 accumulator, on
`xcu280-fsvh2892-2L-e`. `ooc.xdc` specifies 5 ns, 0.1 ns uncertainty, explicit
input/output max0.8/min0.1 ns delays, and no false-path/multicycle exceptions.
Vivado OOC ports have no parent-context `HD.PARTPIN_LOCS`; their external route stubs and board routes are unverified. The explicit I/O delays are a declared interface budget, not a routed board/interface closure claim.
The B tool-crash receipt is in `ooc_b/terminal.json`; the final routed result is
the distinct OOCd described below. Synthesis after the RAM coding fixes measured16410 LUT,
14860 FF,12 BRAM36+4 BRAM18=14 BRAM36-equivalent,16 URAM,0 DSP for two subbanks
and one shared port; hierarchical reports separate core/pending/scratch/fabric.
Thirty-two times this number is only a ledger term: it excludes front FP32,
global routing, init, full directory/output and controller, and provides no
full-kernel placement or timing qualification.

The local fixture preloads canonical wave prestate externally and separately
performs real PV clear. It does not time a full canonical sample initialization,
full native POP/graph/FP32 expansion, or whole wire-map export. External directory
ready is a finite-rate consumer boundary, not the complete graph directory
implementation. The backend accepts real pair operands from its boundary; this
prototype contains no front FP32 lanes. `board_measured=false`, and it reports
no FPGA complete-batch seconds or complete-kernel frequency qualification.

The additional `...integration_20261114_port_stress/` run saturates all four
request queues (4 each), the physical return queue (4), and all32 credits,
then recovers under out-of-order returns and client backpressure. It checks
2048 unique request/response payloads and complete drain. The independent port
model predicts every boundary signal for all2905 observed nonreset cycles,
including saturated states (peak32/4/4). This stress is separately labeled and
is not used for native throughput estimates.

The final bounded control-path fix uses the frozen transform's change predicate
instead of comparing the min-selected256-bit line again. Opcode3 changes its
label exactly when status!=8; opcode7 ORs that predicate across its four
sectors; POP never changes label; SEED changes it only if the selected old pair
is nonzero; unsupported opcodes leave labels unchanged. This alters no register,
RAM, arbitration or pipeline cycle. The canonical worker checked73728 cases
across all8opcodes and17620 complete stage/interface events. Final `sim_d` then
reran all38 matched wave cases: both metrics, full physical traces, transaction
timing and representative exact-calibration CSVs are byte-identical to `sim_c`
(`cycle_equivalence_to_sim_c.json`). The exact final canonical SHA256 is
`6564246dab33833a537f470507a4ba671e924430a3971d1a9685f44eaaaa4255`.

OOCb crashed in systemlibudev/FlexNet host enumeration after route completion,
before it could save a routed DCP; the SIGABRT stack is preserved. OOCc
recovered the exact synthesized design using process-scoped preload of the
existing systemlibudev (no vendor/global settings changed), and successfully
wrote the routed DCP and allreports. See its `KNOWN_ISSUE_RESEARCH.md` and
`workaround.json`, including primary-source links and verification limits.
C's actual pre-control-fix200MHz result is WNS-0.413ns/WHS-0.135ns/pulse+1.8ns,
all12check_timing categories zero; all33089 routable nets fully routed. Its
negative result is retained separately from tool-crash recovery. The final
control-fix OOC is the distinct `...integration_20261114_ooc_d/` run; its terminal
reports determine the final scope. The original I/O min/max budget and clock
are preserved throughout, and no path waiver is used.

Final D completed synthesis/opt/place/physopt/route and reports with toolcode0.
Its actual local setup WNS is **+0.024 ns**, TNS0/zero failures; hold WHS is
**-0.135 ns**, THS-71.713 ns/669 failures; pulse+1.8 ns. Overall status remains
`ROUTED_LOCAL_TIMING_FAIL`, not a qualified200MHz interface or whole kernel.
All12check_timing categories are zero; all33000 routable nets are fully routed.
The exact net audit classifies all674 RTSTAT-10 affected nets as public output
only, zero internal input-pin consumers. Every one of669 negativeholdpaths
starts at a declared top input, matching the report endpoint count. These
limitations are retained under the unchanged min0.1ns budget, without waiver.
The32SYNTH-5 instances are enumerator replacement arrays implemented as LUTRAM.
Full dispositions, exact CSV audits, raw reports and source bindings are under
`results/fpga_enum_commit_integration_20261114_ooc_d/`, including
`METHODOLOGY_RESOLUTION_REPORT.md`, `connectivity_audit.json`, `terminal.json`
and `mcp_history.json` with raw command timestamps/elapsed/code0 receipts.

Final routed local resources are16024 LUT,14853 FF,12 BRAM36+4 BRAM18
(14 BRAM36-equivalent),16 URAM,0 DSP. `resource_ledger.json` records both the
actual two-subbank owner and32x arithmetic, explicitly excluding frontend,
complete directory/output and global/controller costs. The final compiled
simulation PRJ/glbl/snapshot ELF hashes are bound in
`...integration_20261114_fixed/sim_d/compiled_snapshot_binding.json`.
No full kernel timing flow was launched: the independently calibrated full
finite model remains conditional on200MHz and does not beat the retained GPU
reference. This local result cannot change that frequency qualification.
