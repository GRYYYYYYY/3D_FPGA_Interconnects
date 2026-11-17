# Continuation after db1d7e454

This continuation follows [the user's current instruction](lookahead_fpga_cpu_primary_next_after_db1d7e454.md)
on the existing `accel/lookahead-cpu-primary-closure-20261115` worktree.
The 2026-11-16 publication snapshot remains frozen. New observations below are
timestamped; they are not a claim of an achieved FPGA speedup.

Current recovery point: **h SSI replay started2026-11-16 21:58:41UTC**;
see the final section. Earlier timestamped observations below are historical.

## Verified continuation at 2026-11-16 18:04:24 UTC

The existing SSI route is active. Phase3.5 Update Timing completed, and Phase3.6
Update Timing began. MCP reports an active command, no completed return code,
and no queued command. The interpreter PID is2502597, start_ticks164305949,
boot ID2c285022-7829-4b21-84d8-176f6732a754. Its process started on2026-11-15
at09:38:12UTC; the SSI flow started on2026-11-16 at10:53:05UTC and route began
at14:14:28UTC. These are different timestamps, not conflicting launch identities.

The run is a **non-project** replay of the verified original f post-opt DCP.
There is no new `.xpr` or project `impl_1` associated with this SSI command.
The original f project retains its failed default implementation and completed
synthesis. The reused interpreter's old log directory is named `full_synth_c`;
that directory name does not identify the currently executing experiment.

Actual working directory:
`results/fpga_cpu_primary_20261115/full_impl_f_ssi_spreadslls_a/run_a`.
MCP session: `vivado-20261115-093812-64020b62`.
Actual log: `results/fpga_cpu_primary_20261115/full_synth_c/.vivado-ai/vivado_35492608_fa722168.log`.
SSI-only log starts at byte45235. Launch identity, frozen scripts and receipt
are under `full_impl_f_ssi_spreadslls_a`; new immutable resume evidence is under
`continuation_after_db1d7e454_a` in the same raw results root.

## Subsequent route failure at 2026-11-16 18:42:24 UTC

Phase3.6 completed, then Route35-3 reported global congestion7. The command
returned1 after16,076,514ms. Its trial summary has5,795,346 node overlaps and
zero failed nets, which does not establish legal routing. South/east local
congestion peaks are104.861%/108.021%. The existing replay subsequently saved the error
DCP and began collecting all21 report groups. The minimal revision and
collection progress are recorded in the later status section below. Initial failure evidence is
preserved under `full_impl_f_ssi_spreadslls_a/route_failure_observed_a`.

## Actual full-core resource comparison

| Stage | LUT | Logic LUT | LUTRAM | SRL | FF | BRAM36 equivalent | URAM | DSP | BUFGCE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| f synthesis / before opt | 1244096 | 956040 | 286776 | 1280 | 749617 | 1148 | 640 | 0 | 0 |
| f standard opt | 1241143 | 953343 | 286776 | 1024 | 749073 | 1148 | 640 | 0 | 1 |
| f default placement / error DCP | 1233715 | 946587 | 286232 | 896 | 749174 | 1148 | 640 | 0 | 1 |
| f SSI placement | 1232534 | 945406 | 286232 | 896 | 749226 | 1148 | 640 | 0 | 2 |

LUTRAM plus SRL equals the report's `LUT as Memory`; these are not additional
LUTs to add to the global count. Standard opt reduces total LUTs by2953,
including2697 logic LUTs and256 SRLs, and reduces FF by544. LUTRAM, BRAM, URAM
and DSP are unchanged by opt. BRAM comprises1016 RAMB36 and264 RAMB18. All
register-as-latch counts are zero. The source-bound comparison JSON under
`resource_comparison_after_db1d7e454_a` identifies each actual full-core report;
no local-module estimates or nonadditive hierarchy sums enter this table.

## Current claim ledger

| Claim | Status and scope |
|---|---|
| Complete core synthesized and standard opt completed | Verified, same31-source f closure |
| Complete core globally fits bare U280 resource counts | Supported at opt and placement; platform shell excluded |
| Original default f implementation routed legally | False: terminal global congestion and node overlaps |
| SSI placement and default phys_opt completed | Verified; phys_opt gave no cell or timing improvement |
| SSI routing completed | Command returned1: global congestion7, illegal trial overlaps; terminal report collection pending |
| Qualified complete-core routed frequency | Unavailable |
| Frequency-qualified BNN40/LSTM40 time and CPU speedup | Unavailable; no formal conversion allowed yet |
| Existing52 RTL calibrations and160 model samples | Verified at the unchanged source/service point;200MHz remains conditional |
| FPGA faster than optimized64-worker CPU | Not established |
| FPGA board measurement | None claimed |

## Recovery procedure

1. Verify the current branch, worktree, PID **and** `/proc` start_ticks plus boot
   ID against `full_impl_f_ssi_spreadslls_a/launch_identity.json`. Verify the
   process cwd and actual log; a reused PID or stale marker is insufficient.
2. Query the existing MCP session with `vivado_status action=session`; read
   `run_a/run_receipt.txt` and the new tail after the saved SSI log offset.
   Do not use the known-broken `action=runs` result for this non-project flow.
3. While the command is active, do not issue `vivado_execute` to that session,
   reset/relaunch synthesis, start another SSI run or restart the interpreter.
4. On success, the frozen replay writes `cp_full_top_routed.dcp` and collects
   `post_route`. On failure, it writes `cp_full_top_route_design_error.dcp`
   and collects `route_design_failure_reports`. Wait for the collection too.
   The interpreter stays alive after completion; process existence is not the
   terminal authority. Inspect final receipt return codes and MCP completion.
5. Bind the actual DCP, receipt, log, scripts and31-source closure; audit all21
   report groups. Report-only failures require a new collection directory from
   the completed DCP, not a repeated physical run. Distinguish router trial
   metrics from serialized checkpoint status. Check legal routing, setup,
   hold, pulse width, unconstrained paths, actual core/reset clock connectivity
   and the retained external boundary-context limitations.
6. If SSI fails, preserve its complete failure evidence before selecting one
   evidence-based minimal modification. The current instruction permits this
   new bounded candidate; it does not permit more lanes, broader parallelism
   or simultaneous architecture candidates. New RTL needs a new configuration,
   functional/model verification and actual implementation evidence.
7. Only after a qualified actual clock, follow `continuation_model_readiness_a`
   and `continuation_fixture_readiness_a`: recompute nanosecond memory timing
   at that period, calibrate where needed and run complete BNN40/LSTM40 base
   and conservative cases. Never divide old cycles by an arbitrary new MHz.
8. Update the main report and this ledger, archive and verify all sources and
   evidence, run protection checks, push this independent branch, and compare
   the full remote SHA with local HEAD. Do not alter prior frozen snapshots.

The existing [main report](lookahead_fpga_cpu_primary_closure.md) retains CPU,
GPU, complete output and phase evidence. No unchanged CPU/GPU benchmark was
rerun during continuation.

## Single minimal revision: status at 2026-11-16 19:02 UTC

The failure evidence and decision were committed and pushed as9547aa799 before
the RTL change. Error DCP saving returned0 at18:45:34UTC; its627,280,835bytes
have SHA256`0bd512a2622439528b1802a398530385473c85bb6c5ac4cf5858ffc47316568f`.
The actual error-state utilization and hierarchy reports have completed and
match the SSI placed global resources and98,661-LUT dispatcher count. The
remaining21-group collection, including timing, remains active in the original
session. No error-state timing value is inferred from the placed report.

`dispatch/return_wordmux/cp_pop_dispatch_restructured.sv` is an isolated
alternate source with SHA256
`2651ce650dfaf8d62d09d4bc015a79f47a784ba9a6e7a54d06b0cdbc9aae0d74`.
Its only change replaces the repeated masked-OR116-bit return payload with an
indexed word selection using the existing one-hot winner. No new register,
stage, lane, capacity, clock or memory assumption is introduced. The sequential
RTL is byte-identical, and all other30 DUT files match f. The original f file
and default source closure remain unchanged; the new explicit31-file closure
is used by the candidate configuration `full_synth_h_return_wordmux`.

All existing local protocol/rejection/selector/lifecycle regressions pass on
the new source. Evidence includes1236 output/state comparison edges,3waves,
508POPs,121generation wraps,8192assignment cases,640return cases and the
directed no-fallback case. These checks use the same original reference that
validated f; they are bounded behavioral evidence, not direct formal f
equivalence, arbitrary-X equivalence or timing qualification.

New complete-core RTL runs `fixtures_return_wordmux_a` and
`fixtures_return_wordmux_conservative_a` are active, with separate saved process
identities. Both first complete8-sample native batches passed; the12-sample
batches are running. The full plan covers52native executions and11configuration
rejects, including deterministic jitter/backpressure. New-source synthesis
has not started. The g model and its full160 outputs may be reused only after
the new calibration audit passes; no new reuse verdict or CPU speedup is yet
granted to this candidate at that observation.

## Calibration complete and h synthesis launched at 19:12:06 UTC

All52native executions and11reject cases completed successfully. Full binary
outputs and accepted event/cycle/phase traces match f exactly. The independent
g-model audit also verifies all19phase totals,3772ordered phase intervals and
72917requests/returns with zero cycle correction. Base native totals are
157312/268916cycles, stress276758; conservative totals are162025/282252.
Measured RTL service gaps/latencies are1/16cycles for base and2/32cycles for
conservative, at the unchanged5ns **simulation** period. The stress case
retains its explicit jitter/backpressure.

The new reuse contract is
`model_calibration_h_return_wordmux_a/calibration_reuse_contract.json`, SHA256
`2b1b4cca0d651e4b5e1f35a622e067ecb8bd47470f6966d690727d68e2584987`.
It binds the new31-DUT source to the unchanged g model and reverified160full
model samples. Those model batches, CPU benchmarks and GPU benchmarks were
not rerun. Conditional200MHz predictions remain conditional; there is no
qualified actual h frequency or formal FPGA time conversion.

Actual h synthesis was launched once at2026-11-16 19:12:06UTC after calibration.
The project is `full_synth_h_return_wordmux/project/cp_full.xpr`, run`synth_1`.
Its child PID is1914551, start_ticks176389453, with the same recorded boot ID.
Parent MCP session`vivado-20261115-113226-a1b5e8eb` reuses the idle diagnostic
interpreter PID1165972/start_ticks164991348 after closing its read-only old
error-DCP project. No original f/SSI synthesis or implementation was restarted.
The actual project verifies all31source hashes, U280,8threads, default synthesis
strategy, rebuilt hierarchy and identical f clock XDC. Vivado12-7122 explicitly
reports no incremental reference checkpoint and use of the standard flow.

`wait_on_run synth_1` was issued once. Recover through the existing session and
`full_synth_h_return_wordmux/launch_identity.json`, its actual generated run log
and markers; do not launch the run again. Synthesis has not completed, so no h
resource or timing result is available yet. `prepare_eda.py --sources-list`
supports the isolated alternative closure; its default discovery was verified
to still resolve the original f closure.

At h launch, SSI session PID2502597 was separately collecting its21error-report
groups. That collection has now completed; the terminal update below supersedes
the active-collection status. Its actual error DCP and reports remain bound to f.
Current qualification fields now refer only to h; previous f and SSI records
are retained in explicit historical sections and immutable pre-transition
snapshots. A completed synthesis alone will not qualify fit or frequency.

## SSI terminal delivery at19:44:55UTC

The original SSI command is now idle, return1 from route failure. All21report
groups returned0; checkpoint writing succeeded. Do not restart SSI or invoke
its collector again. `full_impl_f_ssi_spreadslls_a/terminal_audit_a` contains
the complete replay log, receipts, stable DCP rehash,31source bindings,
30report-artifact hashes, parsed audit and manual review. There are no missing
audit fields. Main closure report now includes actual terminal resources,
timing, routing legality, clock/control-buffer separation and warning classes.

The full failure review does not qualify a clock. h remains the only active
candidate and its existing synth_1 must be supervised, not relaunched. At
19:47UTC it is in Timing Optimization, PID1914551/start_ticks176389453.
The new `synthesis_collection_a/collect.tcl` and `impl_context_connected_a`
under h are prepared but have NOT run. After actual synthesis completion,
verify project/run/status and DCP/source hashes, run the report collection,
review full resources/warnings, then standard opt-only. The cloned hooks use
real clock connectivity and only the external core clock context. Physical
implementation still requires the actual post-opt resource/clock gate.

The latest pushed code/calibration snapshot before this terminal audit is
`eca17e1f39342477050eb7471cde6498127ee46a`, remote SHA verified. Later evidence
will be archived/pushed separately; large local DCP binaries are not in Git.

## h synthesis terminal and active collector,20:59UTC

The h synthesis child1914551 exited normally at20:44:25UTC. Parent
`wait_on_run synth_1` completed0 at20:44:37UTC. Live Tcl confirms the h project,
U280/cp_full_top, synth_design Complete!/100%, NEEDS_REFRESH0 and impl_1 Not
started. All31current/frozen source hashes match. Terminal DCP is681,084,349bytes,
SHA256`700ef698aa190e59140650c34a9cb2fcb2dbccfe069dec9504786becca9e76a8`.
The child terminal has8654warnings,0critical warnings and0errors.

Actual full-core synthesis resources:

| Resource | f | h | h−f |
|---|---:|---:|---:|
| Global LUT |1,244,096|1,223,270|−20,826|
| Logic LUT |956,040|935,214|−20,826|
| LUTRAM |286,776|286,776|0|
| SRL |1,280|1,280|0|
| FF |749,617|749,607|−10|
| BRAM36-equivalent |1,148|1,148|0|
| URAM |640|640|0|
| DSP |0|0|0|
| BUFGCE |0|0|0|

Dispatch hierarchy LUT99,304→80,254 andFF15,221→15,185. Other hierarchy rows
also shift during mapping; hierarchy LUTs are not an additive global budget.
No physical fit/frequency is inferred from this synthesis reduction.

The existing MCP session`vivado-20261115-113226-a1b5e8eb`, parent1165972/
start_ticks164991348, is executing the already prepared `synthesis_collection_a/
collect.tcl`. Do NOT repeat it or send another Tcl command while busy. The
function-call wait handed off after300s; the command continues in Vivado.
`collection_live_identity.json` binds its live log at byte offset3641653.
At20:59UTC global/hierarchy reports are complete and timing_summary is active.

Current warning review rechecks all8654diagnostics. Of499entries needing manual
source interpretation,361have documented source explanations and138generated
constant aliases remain unproven (2lane,4edge,123output,9admin). Nothing is waived;
old142-alias identities are not copied onto this new netlist. A packaged CSV
helper had a seven-column/six-column schema mismatch; its unchanged parser output
is retained and a documented six-column input adapter yields8654correctly grouped
warnings. This auxiliary issue does not alter RTL, logs or EDA execution.

When collector is terminal, verify all reports/DCP/census and finalize the warning
report. Then use the prepared h standard opt-only hooks after the actual source/
resource gate. No opt or physical run has yet launched. Previous f/SSI failures
and protected references remain unchanged.

## h full synthesis review complete; standard opt-only active

The full synthesis collector completed0. Its terminal audit is
`full_synth_h_return_wordmux/synthesis_collection_a/terminal_review.json`.
Actual64banks/16fronts/32ports survive;9681outputs have nonconstant primitive
drivers,0zero-driver outputs,0blackboxes. DRC0,all12check_timing counts0.
Methodology2024 = SYNTH5(1024)+TIMING16(1000). At5ns, unplaced WNS−5.098ns,
TNS−48,686.059ns,WHS−0.091ns,THS−10,814.053ns. This is not routed frequency.
All8654warnings are covered once in the report with CSV serial references;
303actual source locations are retained. The138unproven generated aliases
remain explicit. Portable report copies are outside the excluded vendor tree.

Before implementation, the read-only h clock query returned0: all/core/direct
name sets equal at1,238,191clock pins,0clock-capable buffers, external source
siteBUFGCE_X0Y144available. No synthetic core clock was assigned to reset/enable.
`pre_impl_clock_review_a` retains actual outputs. `opt_only_gate.json` binds the
source/resource/clock review and full synthesized DCP; it is not timing signoff.

Standard opt-only launched once at2026-11-16 21:11:59UTC in the same h project,
run`impl_1`, stop step`opt_design`. Actual childPID235989/start_ticks177108880,
boot`2c285022-7829-4b21-84d8-176f6732a754`; parent session remains
`vivado-20261115-113226-a1b5e8eb`,PID1165972/start_ticks164991348.
`impl_context_connected_a/launch_identity.json` and `launch_tool_result.json`
bind the launch. `wait_on_run impl_1` has been issued once. Do not reset or
relaunch. Current child log is`project/cp_full.runs/impl_1/runme.log` under h.

The init hook rechecks actual clk topology and applies the declared external
OOC core source only to clk. Post-opt hook separately inventories actual buffers
and clock loads. Hooks are external to Vivado utils_1 (Runs36-537); their exact
scripts/hashes are explicitly archived by this delivery flow. The warning does
not mean a hook is missing. No physical placement/route has started for h.

Next: collect actual opt terminal, DCP, global/hierarchy resource delta and
clock/control-buffer classification. If those pass the resource/context gate,
continue this single h candidate to full physical implementation. Preserve the
original f and SSI terminal failures and all protected histories.

## h standard opt complete; h SSI replay active at21:58:41UTC

The original opt-only child235989/start177108880 exited at21:55:09UTC.
The already-issued parent wait returned0. Actual project query at21:56:09UTC
reports synth complete, impl`Not started place_design`,40%,NEEDS_REFRESH0:
this is the terminal opt-only state, not a failed or active placement. All
init/opt/wrapper end markers are present. Do not relaunch or reset that run.
`full_synth_h_return_wordmux/opt_terminal_a` retains actual tool results,
process terminal, generated Tcl, log, markers and complete report review.

| Resource | h pre-opt | h post-opt | Change |
|---|---:|---:|---:|
| LUT |1223270|1220068|−3202|
| LUT logic |935214|932268|−2946|
| LUTRAM |286776|286776|0|
| SRL |1280|1024|−256|
| FF |749607|748933|−674|
| BRAM36-equivalent |1148|1148|0|
| URAM |640|640|0|
| DSP |0|0|0|
| BUFGCE |0|1|+1|

Post-opt all/core/direct clock pin name sets are identical at1,237,261.
The sole BUFG is`dispatch/core_reset_BUFG_inst`:99,097loads,0clock pins.
Only real clk retains external OOC sourceBUFGCE_X0Y144. The run has two empty-
blackbox-query warnings and oneTiming38-242 for reset's upstream OOC context;
all are classified, none waived. No fake clock context was assigned to reset.
DRC0;12check_timing checks0;methodology2024(SYNTH5=1024,TIMING16=1000).
Unplaced WNS−5.106/TNS−48,440.133ns,WHS−0.091/THS−13,166.243ns.
64banks/16fronts/32ports and9681nonconstant-driven outputs survive;0blackboxes.
These observations are not formal equivalence or routed timing qualification.
The138unproven generated synthesis aliases remain explicit.

Actual new opt DCP:402149724bytes, SHA256
`832f257f83d47575d9ea4bfb448b19f49be489ce93d18938a0a1b4f29ab0e3d5`.
The new physical root is`full_impl_h_ssi_spreadslls_a`; frozen replay binds
this h DCP, not the old f hash. Its frozen clock/census helpers and report
collector are bound by`freeze.json`;`launch.tcl` is the exact entry point.
The strategy is unchanged SSI_SpreadSLLs/ultrathreads,8threads,default phys_opt
and route,5ns target. This tests the one h RTL revision without adding candidates.

The existing idle h MCP session was reused after closing its completed project:
`vivado-20261115-113226-a1b5e8eb`,PID1165972,start_ticks164991348,
boot2c285022-7829-4b21-84d8-176f6732a754. h replay began21:58:41UTC and is
opening the verified input checkpoint. It is **non-project**: no new project run
or child PID. The parent log is`dispatch_synth_a/.vivado-ai/
vivado_42346525_14d7ac8e.log`, h-only byte offset4219527. Actual working/output
directory is`full_impl_h_ssi_spreadslls_a/run_a`. Use its receipt and the
parent birth identity; do not infer the active candidate from the old log folder.
Do not re-source the launch script while active. The replay saves each stage
DCP and collects terminal failure evidence on error. Preserve old f/SSI history.

Next: supervise this existing h replay, collect real placed/route resources and
all/internal setup/hold, clock/connectivity, congestion, DCP and complete warning
classification. Only after qualified routed frequency perform ns-memory-aware
calibration/full BNN40/LSTM40 conversion and CPU64 comparison. Current formal
FPGA time/frequency/speedup remain unavailable;200MHz model values stay conditional.

### h physical progress at2026-11-16 22:22UTC

Input DCP open and actual-clock/connectivity both completed0; the latter again
confirms1237261all/core/direct clock pins and reset BUFG99097loads/0clockloads.
`place_design` began22:11:42UTC. Placer initialization completed and global
placement/floorplanning is active; no placed checkpoint or route result yet.
`placement_floorplanning_a` retains the partial log/receipt and context hashes.

A read-only observer started22:18:09UTC, PID1602804/start_ticks177505615,
same boot. `monitor.py` writes`monitor_snapshots.jsonl` every60seconds; it
never invokes EDA, resets, kills or relaunches anything, and exits when the
replay terminal receipt appears or the bound Vivado process identity disappears.
Do not start another observer over its exclusive output files. Confirm its
birth identity and existing log before resuming supervision. The observer's
terminal receipt is not a substitute for final MCP/run/DCP/report auditing.

## User-requested publication at2026-11-17 00:00:59UTC

See [the new frozen completed/in-flight summary](lookahead_fpga_cpu_primary_progress_20261117.md).
`github_progress_snapshot_20261117_a` binds the actual MCP running/queue0 state,
parentPID1165972/start164991348/sameboot, partial replay log, receipt and monitor
records. Global placement completed; current detail placement isPhase3.6 Small
Shape DP, after splitSLRCrossingNets. No place terminal/placed DCP/route start yet.
The existing h replay remains active; do not re-source launch.tcl or reset runs.
Old f default/SSI failures, new h functional/synth/opt results and all CPU/GPU/model
reuse evidence are distinguished in this snapshot. Formal clock/FPGA time/CPU
speedup remain unavailable. The user requested a publication update, not an EDA
restart; continue supervising the existing task after publication.
