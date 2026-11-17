# h single-target migration — implementation in progress

As of **2026-11-17 19:16 UTC**, synthesis, opt and placement are complete; **phys_opt is running and route has not started**. This is not terminal physical qualification.
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
| Legal complete routing | Not yet established; phys_opt running |
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

## Natural placement audit, 2026-11-17 16:40 UTC

The complete placement DCP has been independently SHA256/length/metadata
verified:1046182493bytes, SHA256
`9000c97d4f40506eeb4a7f5dc4127f814136cfdf84713512c4c0b4ee0cb25fa7`.
Actual part/top/OOC match the frozen new target. No checkpoint was reopened in
Vivado or used to launch implementation. Independent phys_opt_design began
15:55:19UTC and remains active; route_design has not started.

Global placed resources:1214168LUT(927040logic+286232LUTRAM+896SRL),
749118FF,1148BRAM36equivalent,640URAM,0DSP,0latches,0blackboxes.
CLB occupancy183007/216000(84.73%); reported CLBM usage84394.

| SLR | LUT | FF | BRAM36 eq. | URAM | CLB used (%) | CLBM used (%) |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 356335 | 262765 | 510 | 300 | 53669 (99.39%) | 24641 (99.68%) |
| 1 | 397813 | 199962 | 94 | 20 | 53973 (99.95%) | 24701 (99.92%) |
| 2 | 353338 | 204793 | 374 | 220 | 53603 (99.26%) | 24568 (99.39%) |
| 3 | 106682 | 81598 | 170 | 100 | 21762 (40.30%) | 10484 (42.41%) |

All per-SLR totals reconcile to the global report. CLBM is the report's direct
label; independent SLICEM-site census remains a terminal audit item. Full LUTRAM,
SRL and logic breakdowns are retained in the machine-readable audit/report.
Local density is high despite global70.26%LUT utilization. No strategy or
floorplan change follows. Reported SLR3/2,2/1,1/0connectivity is respectively
8802,20789,16393out of23040(38.20%,90.23%,71.15%). These are placement
accounting values, not completed routed crossings.

The DCP's naturally generated QoR JSON records estimated WNS−18.525ns and
TNS−6250817.000ns. Global congestion levels inN/E/S/W order are6/5/5/7;
long7/6/7/6; short7/7/6/7. Tile percentages and hold slacks are blank, not zero.
The earlier−23.420ns value is an intermediate estimate. Neither establishes
qualified frequency or terminal timing failure.

Stage DRC reports one RTSTAT-13 insufficient-routing critical warning because
routing has not yet run. It is not route_design failure. A reset HD.CLK_SRC
Timing38-242warning occurs in phys_opt and was also observed in original h
logs; actual clock/control-buffer loads and skew must still be audited. No
reset clock constraint, timing exception or I/O delay change is made.

Worst setup/hold endpoints, logic/net delay, levels, fanout, SLR traversal and
skew are not naturally reported yet. They remain explicitly pending the
terminal collector/supplementary serial read-only audit. No commands were
submitted to the busy Vivado. Immutable evidence is in
`accel/lookahead/fpga_device_migration/placement_audit_20261117/`.

## Requested GitHub progress publication — 2026-11-17 19:16 UTC

All completed work remains in this independent branch. The new immutable
`accel/lookahead/fpga_device_migration/progress_snapshot_20261117T191651Z/` captures the current
stage receipts, monitoring history, budget, process identities, publisher
heartbeat, qualifications, full log prefix through capture, prior remote
verification receipts, and three complete-checkpoint identities. Its manifest
records each file length/SHA256. Vendor DCP binaries remain on the server.

Physical optimization is still active; route and terminal path/clock/SLR
qualification are pending. The captured estimate is-18.347ns,
not a terminal result. No implementation input, observer/publisher, budget,
main branch or manuscript is changed by this publication.
