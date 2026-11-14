# Final D finite model results

The full native model is functionally correct on all tested outputs, but this
configuration does not meet either reused GPU target under its assumed200MHz,
80ns latency/5ns issue interval,32physical32B ports and32credits/port contract.
F2 improves complete elapsed cycles by about1.5%; descriptor fusion F1/F3 slows
the matched complete representatives. No complete FPGA clock or board result
is claimed. This result does not rule out other FPGA architectures.

## Complete native batches

|Input|Configuration|Samples|Cycles|Conditional seconds|Init|POP+expand|Finalize|Export|Other|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|bnn_export|C0|40|72,347,012|0.361735060|1,284,240|48,888,167|22,012,290|126,640|35,675|
|bnn_export|F2|40|71,238,001|0.356190005|1,284,240|47,780,276|22,011,170|126,640|35,675|
|lstm_s2|C0|40|73,374,604|0.366873020|1,304,280|49,609,893|22,295,250|128,920|36,261|
|lstm_s2|F2|40|72,236,324|0.361181620|1,304,280|48,472,608|22,294,255|128,920|36,261|

BNN F2 improves1.532905%; LSTM improves1.551327%. The corresponding conditional
times are2.346443 and2.264490 times the reused GPU targets0.151799969444s and
0.15949799988888888s (`RESIDENT_COMPLETE_BATCH_V2`). These ratios compare the
assumed model to software evidence; they are not qualified FPGA speedups.
Complete sample phases sum exactly; CPU simulator parallelism is never counted
as FPGA sample overlap. Each sample performs initialization and all final ACKs.

Complete output SHA256 (identical for C0/F2 and frozen golden):

- BNN: `a8ca4003a3b015145635a3f776bb62a3aec1ec2121a1fbfc8712d2a2dc1c8c3f`.
- LSTM: `6b2acd7718d880075d653b3b83f1fa3abb5161f6f346ed39c3aa1285160a95cf`.

## Matched complete representatives

Selection was frozen before timings:BNN2/19/35/31; LSTM7/19/18.
C0/F1 have8groups of8lanes; F2/F3 have16groups of4lanes. All have64lanes,
E256,512beat slots,128fork tokens,128ready capacity and the same physical
memory contract. F1/F3 use packed descriptors; C0/F2 use aligned ROW+META.
Grouping and fusion still incur distinct actual control/resource costs.

|Representative sum|C0|F1|F2|F3|
|---|---:|---:|---:|---:|
|BNN4 complete samples|7,305,687|8,634,228|7,194,777|8,549,910|
|LSTM3 complete samples|5,531,365|6,549,289|5,448,846|6,486,197|

F1 slows18.1850%/18.4028%; F3 slows17.0309%/17.2621%. F2 improves
1.5181%/1.4918% and was selected dynamically as best in both cases. Fusion
reduces ROW/META requests, but keeps each finite token live through POP, DESC
and both branch handoffs; observed longer residency and fuller groups accompany
its expansion cost. Request reduction alone does not establish acceleration.
`representatives_comparison.json` includes the actual occupancy/residency evidence.

## Bottleneck observations and scope of stopping

F2 full BNN/LSTM expansion costs47,780,276/48,472,608cycles. Finalize costs
22,011,170/22,294,255cycles. Removing measured finalize diagnostically leaves
0.246134155/0.249710345s, still above the GPU targets. That subtraction is not
a simulation or lower bound for another architecture. The critical-tail bank
observer is selected by latest actual activity per wave; its exclusive final
histogram reports publication-held17,526,388/17,805,258cycles, K8-full
1,048,291/1,060,944, scratch869,658/821,729. These labels partition observations
by priority and do not isolate counterfactual causes. Overlapping bank busy or
context counters must not be added as elapsed time.

No K16 or merge2 was selected: the actual observations do not establish the
required isolated critical K8/single-merge dependency. No two-sample interleave
was selected: F3 does not reduce representative expansion. No alternative clock
or memory-service point is claimed. Such changes require new finite execution;
old cycles divided by a new frequency would not qualify.

Full F2 BNN/LSTM request totals773,933,212/790,998,596 are freshly counted,
including changed spills9,112,556/9,307,643. Canonical touched/changed totals
and complete algorithmic outputs remain correct. Mean token residency is
56.065509/55.943925cycles (slot-cycle integral divided by102,924,851/104,739,179
reservations); this integral is not wall time. Full directory peaks3495/3531
remain below8192members/bank; scratch-ID peaks883/824 below2048; K reaches8;
export ACK acceptance peaks2/cycle. Maximum actual POPtransactions/sample
2,575,438/2,621,038 fits24bits; maximum physical line90,173,858/91,589,922 fits32bits.

## Validation, bindings and limits

`independent_verification.json`:PASS334 unique sample receipts, comprising
160small regular/jitter +160full native +14F1/F3 representatives. The28
representative runs overlap full batches in14C0/F2 checkpoints. Validation checks
exact golden output bytes, binary/frozen-source hashes, phase sums, wave counts,
traffic/return conservation, candidate counts, directory/K/queue/credit bounds,
group occupancy bounds, output RAM completions and two-ACK admission limit.

D corrects registered exporter start/done and ACKcollector boundaries. Actual
C-to-D reruns gave+3cycles in80normal small and28native representative samples;
the28native wave traces, traffic and outputs remained identical. Jitter tests
exercise52 ACKsource rejection cycles across30cases. A/B/C intermediate roots
and supersession receipts are retained; they are not final timing evidence.

The208source/32port adapter check is C++ equivalence against shared registered
network primitives, not a full native RTL run. Local RTL simulations separately
cover front, backend, directory, output and memory boundaries. C0/F2 ROW/META
control, opaque wire tag packing, full accumulator pipeline and complete global
assembly remain outside end-to-end RTL calibration. Aggregate timing error has
no proven sign. Full payload/metadata/FIFO/RAM/routing resources must be charged
by the parent resource audit; C++ object sizes are not hardware resource totals.

`complete_kernel_clock_qualified=false`, `board_measured=false`; qualified and
board seconds remain null. Source, input and binary bindings are in
`model_d/binding.json`; complete execution terminal is
`model_d/full_C0F2_terminal.json`, ending2026-11-14T16:40:14.091292+00:00.
Frozen binary SHA256:
`651023422a3d036f6119f1a6d13d4aa70e02d79727b90ff611c7467bd886ef13`.

The worker has no remaining model process and does not commit/push. Final
cross-worker resources, archive and publication belong to the parent task.
