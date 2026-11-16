# Continuation after db1d7e454

This continuation follows [the user's current instruction](lookahead_fpga_cpu_primary_next_after_db1d7e454.md)
on the existing `accel/lookahead-cpu-primary-closure-20261115` worktree.
The 2026-11-16 publication snapshot remains frozen. New observations below are
timestamped; they are not a claim of an achieved FPGA speedup.

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
congestion peaks are104.861%/108.021%. The existing replay is saving the error
DCP and will collect all21 report groups; those terminal artifacts remain
pending. One minimal return-payload wordmux revision is selected, not yet implemented
or tested. Initial failure evidence is
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
