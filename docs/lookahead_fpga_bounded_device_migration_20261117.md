# h single-target migration — implementation in progress

This report includes the **completed synthesis/opt audit**, not terminal physical qualification.
Experiment `H_SAME_RTL_SINGLE_PART_MIGRATION_V1` starts from hardware review
`706feba1cbefcf828d998560440c488cd081ba07` in independent branch
`accel/lookahead-h-device-migration-20261117`. No paper is modified.

The uniquely frozen target is **xcu250-figd2104-2L-e**. Vivado2022.2 actually
loaded it and obtained a Synthesis/device license in a small preflight.
Installed part properties give1728000LUT,3456000FF,2688BRAM36,1280URAM,
4SLRs; loaded sites include98880SLICEM,117120SLICEL,384BUFGCE. XCVU13P
was enumerated only; XCU250 passed the priority preflight, so no second
part enters full synthesis. Same nominal -2L/E grade does not eliminate
changes in silicon, SLR geometry and timing models.

All31sources from `dispatch/return_wordmux/sources.json` match original h
binding and the base commit byte for byte. Top `cp_full_top`, source order,
empty external defines/includes and parameter overrides remain frozen.
The source preserves64candidate lanes,16front groups,64banks,32logical
memory service ports,K8 and all original capacities/protocols. Prior RTL
calibration may be reused; this is not post-synthesis formal equivalence.
The138unproven synthesis aliases remain a limitation.

Core clock remains5ns, uncertainty0.1ns and blanket min/max input/output
delays0.1/0.8ns. HD.CLK_SRC changes from U280 BUFGCE_X0Y144 to the median
unused BUFGCE site found on the newly loaded target, BUFGCE_X0Y192 inSLR2.
This external OOC clock assumption is not a deployed board clock. No old
DCP, LOC/BEL/pblock/partition pin or PACKAGE_PIN mapping is imported.

The single implementation chain is full OOC timing-driven synthesis
(default directive/rebuilt hierarchy), standard opt, SSI_SpreadSLLs placement
with ultrathreads, default phys_opt, default route. Local2022.2help confirms
these placement options. Eight threads are frozen. Each completed stage
writes its own checkpoint and SHA/length, resources and census gates; terminal
collection bounds path reports to20. No result-driven target/strategy search.

| Qualification layer | Current state |
|---|---|
| Legal complete routing | Not yet established; placement running |
| All-required core OOC timing | Not yet established; no qualified frequency |
| Conditional model performance | Pending physical qualification |
| Actual board/platform performance | Not measured; seconds and speedup null |

32logical ports do not mean32deployedDDRchannels. Prior200MHz memory models
remain conditional and cannot be combined with new device capacity as board
performance. No CPU/GPU experiments, shell, PCIe or memory-controller deployment.

Budget uses a conservative start2026-11-17T11:10Z before preflight;22h compute
cutoff2026-11-18T09:10Z,24h delivery cutoff11:10Z. Monotonic derivation and
actual record samples are explicitly documented, not a renewed budget.
Dedicated supervisor PID1017775 owns worker wrapper1144478 / Vivado1144514
in process group1144478. The supervisor has a flock, process birth identities,
60s heartbeat, original-budget recovery and identity-checked SIGINT at22h.
It never cancels old or shared tasks; an unconfirmed stop remains explicit.
Separate publisher entry PID1181978 waits for terminal/budget, then invokes
the verified Codex CLI for substantive audit and final publication. Exactly
one final publisher is designated; no automatic second experiment.

Raw evidence and live status:
`results/fpga_device_migration_20261117/migration_a/`.
Reproducible scripts and immutable initial snapshot:
`accel/lookahead/fpga_device_migration/`.
`initial_snapshot/manifest.json` identifies all copied evidence, including
31frozen sources. Vendor checkpoints will remain at their absolute raw paths
with SHA256/length receipts, not Git blobs. Live heartbeat/logs are not terminal
archives. `physical_qualification.json` currently has whole_task_complete=false.

Recovery: inspect birth identities, heartbeat/stages and budget first.
`supervise.py <absolute raw run directory>` resumes the sole observer under
its lock and never restarts a recorded worker. `terminal_publisher.py <raw>`
has its own lock and refuses duplicate audit invocations. Inspect
publisher_invocation/agent log/final message and remote verification receipt
before recovery; never re-source launch.tcl or restart original h.

Main, previous hardware and all paper refs/trees and original tracked diffs
are protected; guidance files have byte hashes. Full terminal resource/timing
comparison and verified remote terminal SHA will replace this running summary
only after actual completion or explicit budget-stop audit.

## Completed-stage audit at 2026-11-17 14:00 UTC

Full synthesis completed12:55:35UTC and standard opt13:15:35UTC. Placement
started13:23:12UTC and remains in partition-driven global placement. The
original budget and single target/chain are unchanged.

| Stage | LUT | LUTRAM | SRL | FF | BRAM36 eq. | URAM |
|---|---:|---:|---:|---:|---:|---:|
| New XCU250 synthesis | 1223270 | 286776 | 1280 | 749607 | 1148 | 640 |
| New XCU250 standard opt | 1220068 | 286776 | 1024 | 748933 | 1148 | 640 |

These values exactly match original h at the corresponding stage. They are
not area savings caused by migration. LUTRAM/SRL are included in total LUTs.
Both stages have0latches and0blackboxes. Synthesized primitive totals and
all9681output-driver census records match h. This corroborates unchanged
structure, not formal equivalence. Actual DCP metadata confirms the new part,
cp_full_top and OOC mode; both full hashes/lengths were independently verified.
The opt DCP embeds5ns,0.1ns uncertainty,0.1/0.8ns I/O delays and new HD.CLK_SRC.
All1238191sequential clock pins belong to core_clock and connect directly toclk.

The placer estimates20586/23040SLLs onSLR1→SLR2; this is a congestion risk,
not evidence of completed routing. No qualified frequency or model time follows.

Independent read-only audit and immutable stage reports are in
`accel/lookahead/fpga_device_migration/stage_audit_20261117/`. The frozen
capacity gate's supplemental rows incorrectly record zero LUTRAM/SRL from
unplaced SLR tables when their top-level Available field is blank. Original
utilization reports and this independent header-aware audit preserve the true
286776LUTRAM and1280/1024SRL counts. Main capacity gates are unaffected; no
frozen EDA inputs or running procedure was changed. New repeated diagnostics
are capped at100, unlike old logs: warning counts are not comparable incidence
reductions. No new Synth diagnostic IDs were observed in available text.

## Observer recovery at 2026-11-17 15:30 UTC

Detailed placement has completed; the same place_design command remains in
post-placement optimization. Its current estimated WNS−23.420ns signals timing
risk, not a routed result or an Fmax. No frequency claim or retry follows.

The observer was improved to sample all process-group members and their CPU/RSS,
and to require the whole group to exit before recording worker termination.
Only the old observer PID1017775 was stopped after checking its full birth
identity; the replacement PID2340438 resumed under the same lock and original
budget. Worker1144478 and Vivado1144514 were preserved. EDA source, flow,
constraints, target, directives and checkpoints were not changed or restarted.
Publisher entry1181978 remains the sole final auditor/publisher.

`accel/lookahead/fpga_device_migration/supervision_recovery_20261117/` records
this transition. The original budget.json PID field is initial provenance;
the current supervisor_identity.json and heartbeat identify the live observer.
Process identity, scope rejection and group exit checks passed. Final physical
qualification and terminal publication remain pending.

## Placement return and additional terminal audit requirements

The original place_design command returned successfully at2026-11-17
15:43:45UTC (0critical warnings/0errors in its final command summary).
Its frozen flow then began checkpoint/report collection. Independent
phys_opt_design and route_design had not started at the15:45UTC observation.
This is placement completion only, not a legal route or a qualified period.

The user's additional requirements are recorded in
`accel/lookahead/fpga_device_migration/supplemental_audit_requirements.json`
and passed to the existing sole terminal publisher. They require stage return
status; worst setup/hold endpoints, internal/boundary classification, logic/net
delay, levels, fanout, SLR crossings and clock skew; global/per-SLR resources,
CLB/SLICEM occupancy and congestion. Read natural reports first. Missing fields
may be collected serially from the same completed checkpoint after the original
worker terminates, within the original budget; never submit to the busy session.

No observer/publisher replacement or EDA input/budget change accompanies this
update. Single6.25ns STA remains gated on legally complete routing and failed
5ns setup. The paper cutoff is separate; no frozen manuscript or submission
date changes. The−23.420ns estimate is neither a final failure nor a frequency.
