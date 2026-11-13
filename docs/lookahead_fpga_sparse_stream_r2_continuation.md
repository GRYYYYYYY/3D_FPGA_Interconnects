# R2 continuation after 82860ce

Review base: `82860ced203bde54f1fa267446b3d0edc521a293`. Work continues on
`accel/lookahead-sparse-stream-r2-20261112` in the existing isolated R2 worktree.
No reset, force synchronization, main merge, or historical evidence replacement.
The original guide and bundle remain outside the experiment changes.

The live evidence entry is
`results/fpga_sparse_stream_r2_20261112/continuation_82860ce/current_manifest.json`.
It points to an immutable, timestamped observation with process identities.
Historical `running` receipts and checkpoint pending fields are historical facts,
not proof of current liveness. All statements below are scoped to their evidence.

## Recovery and existing candidates

The original interrupted P8/F0 pipeline retains its receipt and partial hot-capacity
output. The append-only `recovery/p8_f0_resume_2108` manifest rechecks 1,103 source,
executable and evidence hashes, preserves eight passed stages, and has passed newly tagged
8192/8193 hot cases, four boundary calibrations and eighteen fixed-10ns cases.
The terminal qualification SHA256 is
`befb1b8857c2702df7e5fce0db21f8afab7129a985229dd64a2fcab80ad84eb0`.
The gated supervisor recorded `GATES_PASS` from an actual `--check-only` invocation before starting
BNN/LSTM native40 at 60/g2, 16/g2 and 16/g1. No clock qualification is inferred from
cycle-model eligibility. Original missing-stage receipts are never fabricated.

Four original runs have terminal route failures: checked P32/F1, router P32/F1,
router P32/F0 and router P8/F1. Their reports and frozen sources are archived under
`evidence_snapshot/completed_continuation_routes_2058` (299 verified files).
All have illegal routing plus negative setup/hold slack at 10 ns. Their complete
kernel FPGA seconds remain **null**. P8/F0 original routing is observed separately;
an intermediate WNS is not timing qualification.

Six P8/F1 60/g2, 16/g2 and 120/g2 full batch traces have been archived in
`checkpoint_20261113T2055` after `checkpoint_20261113T1212` and all 1,911 new
records verified (8,848,246,884 raw bytes; 2,430,692,889 archive bytes). Their
completed work/native audits remain unchanged. The 16/g1 pair was already archived
in the preceding chain. Three bounded Git pushes publish this delta.

## Wave-private INF investigation

The first full native40 profile preserves every output byte and every original
per-wave work row. BNN/LSTM candidates are 1,286,937,147 / 1,309,512,712; peak touched
four-node lines per wave are 212,889 / 215,188, rather than changed-only capacity.
For owner=line4[4:0], subbank=line4[5], peak per subbank is 3,383 / 3,401; peak per
owner is 6,745 / 6,784. Detailed touched2/touched4, changed2/changed4, repetition
histograms and owner/subbank distributions are retained in `accumulator/profile_a`.
These are functional instrumentation measurements, not FPGA cycles or CPU timings.

The independent INF oracle reduces candidate whole pairs against INF, then compares
against unchanged wave-start canonical labels at commit. It retains the original
bucket closure and early completion boundary. The finite-cache investigation uses
64 subbanks, 1024 sets and four ways each; real conflicts can spill even below the
aggregate capacity. No old model calibration is inherited by this new structure.

Current prepared-POP CUDA comparison targets are BNN 0.151799969444 s (compact) and
LSTM 0.159888578444 s (basic). Conditional frequency/traffic budgets are separated
from actual simulation and OOC. No FPGA board measurement has been made.

## New measured and simulated results

The private-INF functional oracle passes four native cases including complete
BNN/LSTM40 and 91 additional ALT fixtures. All full-output bytes and per-wave work
counts match; first-touch versus first-improvement ordering changes some order
hashes, explicitly recorded in `private_inf_work_validation.json`.

Finite 4-way/1024-set instrumentation reports 15,588,763 / 15,023,242 evictions and
9,097,564 / 9,027,483 distinct spilled lines across the complete batches. Capacity
and physical-port traffic include all touched lines. The bounded scratch layout
uses 64 bytes per line and four 32-byte transactions per fragment RMW, plus sparse
enumeration and final canonical state128 reads/writes.

The actual two-subbank RTL passes eight single-wave tests: empty,4096/4097 lines per subbank,
continuous RAW and conflict/backpressure stress, and four recorded complete waves.
A ninth test reuses the same RAM for two consecutive waves without reset, with worse second-wave pairs to expose stale accumulation; all512 candidates and both complete outputs pass.
Finite testbench queues are depth8; scratch has 1,048,576 lines. Real-wave stress
feeds all owner IDs into only two test subbanks; it is **not** evidence of a full
32-owner router. An independent sequential cache model matches fragment/residency
counts for the recorded waves. No complete-candidate cycle calibration is claimed.

The fixed-slot scan version fails even the optimistic compute-plus-enumeration
bound at 200MHz: 0.15960383 / 0.16143095 seconds. The occupied-list version removes
empty-slot enumeration and passes the same complete output checks. Its flush-all
scratch organization still fails the necessary traffic budget: conditional lower
bounds 0.266757485 / 0.27032213 seconds at P32,gap1,200MHz. These are lower bounds,
**not simulated whole-kernel predictions or FPGA measured seconds**. A hypothetical
resident-direct hybrid also fails the BNN necessary bound; LSTM has only a narrow
optimistic allowance and lacks implemented scratch/final-state arbitration.

Original RAM inference produced 114,020 LUTs including 86,144 LUTRAM and zero
BRAM. The RAM-port repair gives actual two-subbank synthesis of 6,040 LUTs,
1,776 FF,66 RAMB36 and10 RAMB18. All eight RTL cycle logs and complete pair outputs
are byte-identical before/after this repair. Direct32-owner replication alone
would require 2,272 BRAM36 equivalents versus2,016 available, before other modules;
full replication is rejected. A different tag/data/URAM organization would require
new implementation and verification. The recovered 5ns unit OOC (Quick directive) completed normally and legally
routed all10,167 nets. Routed resources are7,013 LUT/1,776 FF/66 RAMB36/10 RAMB18.
Setup slack is−6.048ns, hold+0.025ns and pulse-width+1.958ns; timing fails and no
frequency is qualified. These unit results do not qualify the complete kernel.

Local same-host8-core CPU controls measured 3.81462→4.56544 seconds for BNN and
3.70693→4.41971 seconds for LSTM (three timed reps after one warmup). These negative
measurements were made on the FPGA host under concurrent work and do not replace
H100-worker CPU baselines. New paired CUDA/CPU controls are submitted as
`job-7977d112-86f2-42f0-9c4e-6481294f1e30`; their actual state is recorded separately.

The first unit MCP parent aborted with exit134 during launch; its child synthesis
completed successfully. This is recorded as a tool/process failure, not an RTL
functional failure. Two local batch attempts also aborted in WebTalk/libudev host-information collection
after routing. Recovery2 reused the saved placed DCP and the real system libudev
preload found in stable existing Vivado sessions; it completed with final reports
and a routed DCP. All failures are preserved separately from the timing failure.

## Outstanding

Check the current manifest for actual liveness. Recovery tail calibration, the full-input finite-table profile, necessary budget
analysis and RTL microprototype are complete. Six P8/F0 full batch cycle runs and
the original P8/F0 routing are still running at this checkpoint. The new H100
control job is queued. New micro OOC recovery is complete with a negative timing result. Per-opcode
state-cache attribution for an integrated INF kernel and full-candidate cycle
calibration have not been produced: the implemented organization fails the
resource/traffic gates, so no full integration or full-candidate OOC is launched.
Full integration is conditional on the guide's technical gates; failures do not
cancel independent authorized work. Final remote SHA verification follows archive
verification and normal pushes to the independent branch.

After checkpoint `e92b6bcdc0a10da2339d8510e7897944e28a493c` was remotely verified,
`finalize_recovered_native.py` was launched (PID235736) to supervise the six already launched runs, recheck qualification, archive all terminal output/trace/audit evidence, and perform normal bounded pushes. It refuses dirty tracked/index state and never restarts experiments. Its append-only receipt directory is `supervision/finalize_recovered_native_2150`.
A separate read-only H100 watcher (PID261003, `supervision/private_inf_gpu_watch`)
will analyze all24 paired software cohorts after completion. Queue state and
model progress are observations, not completed results.
