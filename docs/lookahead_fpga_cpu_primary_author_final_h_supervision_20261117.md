# Author-final paper closed; h supervision remains open

Paper branch `paper/dac2027-dependency-revision-20261117` has verified remote SHA
`c8933bac394a1c177725bec6d9a0ccb6af3437a6`. This is the requested two-edit
follow-up to author-review base `bffa5626ac7e984f3018b5e9be9f4b95ac18541b`.
It retains six content pages plus one reference page, the same performance
numbers/boundaries/holdout, and an independently rebuilt anonymous source ZIP.
No further paper edits or research experiments are scheduled by this task.

## Actual h state and ownership (2026-11-17 03:02:07 UTC)

h is NOT terminal. Last actual log phase is `Phase 3.2 Update Timing`;
log last written 02:33:51 UTC. Latest observed heartbeat was03:01:24UTC.
Absence of a fresh log line is not termination; CPU ticks continue increasing.
The existing run receipt has `BEGIN EDA route_design` and no top-level
`RETURN_CODE` yet. MCP reports command active, queue zero, no completion code.

- Vivado PID1165972, start_ticks164991348, started2026-11-15 11:32:26UTC.
- Observer PID1602804, start_ticks177505615, started2026-11-16 22:18:09UTC.
- Both match boot `2c285022-7829-4b21-84d8-176f6732a754` in live `/proc`.
- Session `vivado-20261115-113226-a1b5e8eb` is the original non-project replay.
- Source project remains `full_synth_h_return_wordmux/project/cp_full.xpr`;
  the active replay is not a new project run.

The independent `monitor.py` is a **read-only observer**, not a complete
terminal supervisor. It records status each60seconds and exits upon terminal
receipt or birth mismatch. It does not audit reports, archive, commit or push.
The frozen in-flight Tcl already writes the routed/error DCP and invokes the
terminal report collector when route returns. **Current Codex conversation
owns final audit, archive and publication.** No independent automatic
publisher has been verified or created. Do not state that the observer alone
will finish these responsibilities after the conversation ends.

Verified snapshot and flow hashes:
`accel/lookahead/fpga_cpu_primary/author_final_h_supervision_20261117/`.
These are independent new observations, not changes to the frozen paper or h inputs.

## Resume the same chain, never launch again

Workspace: existing `3D_FPGA_Interconnects_CPU_PRIMARY`, branch
`accel/lookahead-cpu-primary-closure-20261115`.
Raw root: `results/fpga_cpu_primary_20261115/full_impl_h_ssi_spreadslls_a`.

1. Revalidate boot/PID/start_ticks, actual cwd and cmdline for h and observer.
   Query existing MCP session read-only and read latest observer/log/receipt.
   Do not infer liveness from this document or an old PID record.
2. Keep the existing observer; do not launch a second monitor or publisher.
   Do not source launch.tcl, reset, stop, synthesize, reroute or alter frozen inputs.
3. Wait for the existing route command and its already-submitted collection.
   Success saves `run_a/cp_full_top_routed.dcp` + `post_route`; failure saves
   `cp_full_top_route_design_error.dcp` + `route_design_failure_reports`.
   The parent interpreter may stay alive after completion: require actual
   top-level receipt and MCP completion, not PID disappearance.
4. After files stabilize, bind DCP/complete replay log/receipts/frozen scripts
   and actual h31-source closure. Audit all collection groups, full and internal
   setup/hold, WNS/TNS/WHS/THS, route errors, clocks/control BUFG connectivity,
   unconstrained paths, exceptions, resource/hierarchy and warning classes.
   Existing audit_route.py is read-only and requires explicit filename mapping;
   the old f mapping is historical only, never silently use its DCP or source.
5. A report-only failure is not a reason to repeat EDA. Preserve the failure;
   use only authorized report collection from the terminal design/checkpoint
   if required. No new architecture or performance experiment is authorized here.
6. Archive terminal evidence, update the CPU_PRIMARY claim ledger/report and
   recovery index, run applicable protection checks, commit/push this independent
   hardware branch, and compare full remote/local SHA. Keep author-final paper
   unchanged. Until then h closure and the combined task remain incomplete.

The paper deadline limits adding success claims to the manuscript. It does not
cancel the ongoing EDA or the obligation to collect and publish its outcome.
