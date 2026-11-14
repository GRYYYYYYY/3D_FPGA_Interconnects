# INF followup after5af9908

This continues the existing isolated R2 branch; original/main/STRICT/goldens remain
unchanged. All previous failed receipts and directories are retained.

## Execution repairs

The original queued `job-7977d112-86f2-42f0-9c4e-6481294f1e30` was confirmed to
reference the defective worker, never started, and was stopped under the followup
authorization. Replacement `job-b0b53982-9534-405e-a441-83c777b9e93d` uses a frozen
worker and all10 compile inputs, with both CPU sources compiled successfully before
submission. CUDA compile is the first allocated-node stage. The current binding is
`config/current_software_run.json`; watcher/observer/finalizer resolve this config.
The worker records failed builds rather than leaving ambiguous empty output.

Native publication now checks cleanliness BEFORE observation, then permits only
its exact hash-bound generated manifest; regression checks reject unrelated edits,
index changes and manifest tampering. Only the old supervisors were replaced.
The six original solver processes and original Vivado run were not restarted.

## Original OOC chain

The original P8/F0 run completed with source exit1 and
`route_design Complete, Failed Timing & Nets!`. Actual10ns setup/hold slacks are
−8.895/−0.112ns,263299 nets have resource conflicts and522787 node overlaps remain.
Resources:786905 LUT,504703 FF,1064 RAMB36,296 RAMB18,288 URAM.
This is a negative complete-candidate result, not clock qualification. The gate
stopped before the slower-period loop; no frequency was inferred from WNS.

## Pending17 and the one targeted combination

`pending17.hpp` transcribes old node_state operations and independently encodes
present+version.1,049,148 operation checks pass, including4095 constructed wraps;
version0 is not absence. Both complete native40 workloads pass207135879/210880424
state-operation comparisons. All output bytes, wave work rows and closure records
match the old private-INF oracle.91 additional fixtures pass. These are functional
experiments, not performance measurements or STRICT equivalence claims.

The combined two-subbank RTL has BRAM metadata, flat URAM sector payload, whole68bit
pending-word RMW,32B scratch, finite2048-entry spilled lists and resident-direct
unique line commits. Pending label writes must ACK before PV/event retirement;
a bank-wide reservation prevents mixed old/new state from being observed. This
is conservative pending throughput, not a claim of a fully pipelined pending bank.
The accumulator reserves all in-flight sets; independent-set acceptance reaches
II1. Same-set traffic stalls explicitly.

The finite testbench shares ONE32B physical request channel across both subbanks'
scratch and canonical clients, with bounded credits, variable delays and reverse
ACK completion. No graph-sized canonical mirror exists in RTL. Canonical labels
are external packed64; testbench backing is finite. Micro tests initialize the
external test memory outside the core loop; full model initialization is counted.

The initial multidimensional RAM declaration failed Vivado2022.2 elaboration.
Independent RAM declarations remove that representation problem; all cycle logs
and output rows remain identical. A later directory-event audit corrected POP's
append indication and added argument validation and explicit MAX_N rejection.
All attempts remain separately frozen. OOC is performed with5ns clock and explicit
input/output min0.2ns,max1ns delays; no bare unconstrained-I/O qualification.

The original derived0.143656/0.145130s values remain partial conditional bounds.
Finite event schedule A was deliberately conservative in source-order port
reservation and is retained as a serialization diagnostic, not an architecture
ceiling. Schedule B uses64 finite chronological front-end contexts and recalculates
replacement/spill traffic. Neither is RTL calibrated; FPGA seconds remain null.

## Completed local experiments

[Pending17 proof](lookahead_pending17_invariant.md) states the representation,
operation induction, whole-word lock and wave-fence assumptions. The independent
RTL transform also passes1,049,148 bit-level checks including4095 constructed
wraps; this is separate from the C++ and full native functional checks.

The final RTL is exercised by13 cases in `inf_combo_rtl_e` and the added concurrent
word test in `inf_combo_rtl_h`, with source hashes matching `inf_combo_c_5ns`.
The latter offers80,000 direct operations while20,000 candidates and24 unique
line commits execute; all24 row commits overlap the direct-operation stream.
36,537 reverse-order ACK completions pass. Client read/write counts are retained.
The physical port has32 bounded credits; each scratch client has one reserved
transaction. There is no claim of eight outstanding RTL scratch commands.

`capacity4096` accepts8192 candidates over4096 active cycles across two banks.
Conflicting `directed` accepts20,000 over319584 cycles. These are actual RTL
service rates, not a claim of64 independent conflict-free lanes in a full router.
Capacity+1,2048/2049 spill IDs, same-set/victim conflicts, same-word operations,
backpressure, native owner0 representative waves and two waves without reset pass.
All accept/retire and unique commit checks are enforced in the finite testbench.
The initially misclassified concurrent test failed with `magic` in F; it is kept,
then fixed by selecting the directed-input constructor, with no RTL change.

Actual C OOC:5ns, setup+0.635ns, hold+0.041ns, pulse+1.800ns;10184 fully routed
nets,0 route errors. Resources5676LUT,6311FF,16RAMB36,4RAMB18,16URAM.
All12 check_timing categories are0. Input/output max1ns,min0.2ns are explicit
assumed interface budgets.32 replacement-table LUTRAM methodology warnings,
4 identical-clock redefinition warnings and one no-routable-loads OOC warning
remain documented, not waived. Repeated module declarations use final C source
paths. This is local OOC qualification only; no full-kernel or board frequency.

## Complete-input finite schedules and resource reservation

Every row below passes complete native40 output comparison. Times divide event
cycles by an **assumed** clock; these uncalibrated schedules include initialization,
CSR/POP, scratch, label/pending, directory, finite ports/credits and final drain.
They remain conservative incomplete integration models, not FPGA predictions.
External latency stays80ns; a5ns issue gap at125MHz rounds to one8ns cycle.

| Schedule | Assumed clock | External issue gap | BNN conditional s | LSTM conditional s |
|---|---:|---:|---:|---:|
| A, source-order diagnostic |200MHz|5ns|15.012545|15.383295|
| B,64 chronological contexts |200MHz|5ns|1.720855|1.744055|
| C, same finite contexts |200MHz|10ns|1.824970|1.847886|
| D, fixed external ns contract |125MHz|5ns requested,8ns realizable|1.956127|1.982049|

Full explicit reservation is864/960URAM and1888/2016BRAM36-equivalent, including
active-parent storage, finite request/response FIFOs, directory/free lists,
spill IDs/bitmaps, occupied lists and output buffers. Payload/pending mapping is
supported by actual micro synthesis; remaining topology allocations are a budget,
not synthesis proof. Old128bit mirrors and changed lists are removed, not counted
alongside the new representation. Global LUT/FF, router and directory timing are
not qualified. Whole-bank pending serialization and conservative frontend/finalize
scheduling leave a large throughput deficit. This stops direct full replication
of this combination; it does not prove all future INF structures impossible.

`analyze_inf_followup.py finite_budget_<newtag>.json` rebuilds this reservation and
four schedule comparisons. `analyze_inf_combo.py <newtag>.json` derives handshake
rates and client traffic from raw cycle logs. Keep output tags new (append-only).

## Independent result-chain status at2026-11-13 23:03UTC

- Original P8/F0 OOC: terminal negative, raw reports and frozen-source review
  archived and remote-verified at `e5ea6c6cdd687684b7a9d0ea947e0c0bbf903697`.
- Six original P8/F0 native models: still running, unchanged PIDs/start ticks;
  current samples8–15 of40. Native finalizer1187993 waits for all audited outputs,
  then verifies/freezes/pushes under a shared publication lock. No restart.
- Replacement GPU `job-b0b53982-9534-405e-a441-83c777b9e93d`: still queued at
  23:00UTC. No new GPU timing claimed. Watcher1145001 and independent software
  finalizer1653677 wait for the frozen worker. All254 successful receipts are
  required; software target is min(historical qualified,new qualified CUDA).
  The analyzer retains process pairs and appends budget views for all old partial
  bounds and new schedules. Its synthetic regression is explicitly not a GPU run.

New INF correctness, finite schedules, RTL and local OOC have completed. Native
and software terminal audits/archive/push remain pending their actual completion.
Their finalizers preserve failures and use independent append-only receipts.
`fpga_seconds=null` and `board_measured=false` throughout; the historical partial
0.143656/0.145130s values remain partial arithmetic budgets only.

## Current terminal entry: 2026-11-14

The old GPU chain (254 successful receipts) and all six P8/F0 native batches are
terminal in fixed evidence base `a64c934956be6514a27f66fd1a46f09ef4a2fab9`.
The earlier queued/running section is a historical snapshot, not current state.
The independent pending-stream followup and its initial-frontend necessary-bound
no-go are documented in [lookahead_fpga_pending_stream.md](lookahead_fpga_pending_stream.md).
The new work does not rerun or supersede the old measurements.
