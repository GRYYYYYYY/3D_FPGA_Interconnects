# CPU-primary L1 complete-core closure

Status: implementation and verification in progress. This file is updated as
terminal evidence arrives; it is not a claim of completed FPGA acceleration.

The independent branch starts at `3c7f96e6037030949b729240977c2ced373843c6` and
changes the goal to `CPU_PRIMARY_GPU_COMPARATOR`. GPU may remain faster. Full
L1 implementation proceeds without the old GPU-win gate. Historical no-go
results remain valid for their original configurations and are not rewritten.
No FPGA board measurements are claimed. The selected starting part is
`xcu280-fsvh2892-2L-e`, Vivado2022.2,5ns initial full-core OOC constraint.

## Strongest measured CPU in the current allocation

A bounded8/32/64-thread sweep is complete:18 independent processes, each with
one warmup and three formal complete batches. All72 outputs match frozen ALT
whole-pair FP32 results. Selection is lowest mean of three process means.

| Case | Threads | Mean resident seconds | SD of three process means |
|---|---:|---:|---:|
| BNN40 | 8 | 2.552500793667 | 0.042481221713 |
| BNN40 | 32 | 1.120514904778 | 0.032437644597 |
| BNN40 | 64 | 0.699624213444 | 0.026647139383 |
| LSTM40 | 8 | 2.610159214444 | 0.045129987151 |
| LSTM40 | 32 | 1.137800883667 | 0.029544175110 |
| LSTM40 | 64 | 0.725510098000 | 0.021287159254 |

Platform: dual Xeon Gold6530,64 physical cores/128 logical CPUs, one thread per
physical core, explicit affinity and NUMA first-touch/interleave placement.
The actual container quota is55 CPU-time. Forty independent samples permit at
most40 concurrent solves.64 workers are best measured under this allocation;
this is not an unconstrained whole-server claim. Three process means are the
independent statistical units, not nine independent processes. Whole-process
quota-throttle counters include allocation and cannot be assigned entirely to
the resident interval. See `accel/lookahead/fpga_cpu_primary/software/RESULTS.md`
and raw `software_a/delivery.json` for source, binary, placement and outputs.

These replace the old8-thread cohort as the main current CPU comparison. The
old assumed200MHz L1 model would be only1.935×/1.976× faster than these CPUs,
not≈8×. Those are historical conditional-model ratios, not new qualified FPGA
results. Routed frequency, updated service cycles and full-model calibration
will determine whether an advantage survives.

## Actual connected core and current verification

`cp_full_top` supplies runtime sample configuration and connects64 candidate
lanes,16 independent frontend groups,64 production banks, full directory/PV/
scratch/output capacities and one shared32-port finite-credit memory network.
It implements sample reset/init, actual cost reads, SEED, directory MIN tree,
TAKE/RELEASE and POP, complete expansion fences, enum2 finalization, actual L1
publication drain, subsequent waves and final output writes/ACKs. All samples
are sequential at the FPGA batch controller, as in the existing L1 model.

Physical request identity retains source6/kind4/generation32/localID32, with
source-specific values proven by the module ABI; upper64-bit line addresses
and end ranges are checked before32-bit transmission. Immutable graph admission
proves encoded cost indices fit the loaded cost table; this is an explicit
host admission invariant, not an additional leaf hardware check.

Two complete native inputs are generated and independently validated using the
production C++ Graph/descriptor path. Only input/configuration reaches the
external memory model; expected output is held by the testbench checker.
Production bank, POP dispatcher and32-source admin local tests passed. The
complete production-core suite has now passed two full native graphs and a
second full d4 run with deterministic latency jitter/request backpressure:

| RTL case | Jobs/pairs | Cycles | Waves | Physical requests/ACKs |
|---|---:|---:|---:|---:|
| native_d3_w8 | 8/144 | 157,312 | 42 | 4,192/4,192 |
| native_d4_w8 | 12/384 | 268,916 | 106 | 21,511/21,511 |
| native_d4_w8 stress | 12/384 | 276,758 | 106 | 21,511/21,511 |

All complete host-format output hashes equal the frozen goldens. Eleven invalid
configurations are rejected without issuing a physical request. Stress adds
0..16cycles deterministic return jitter and allows requests for14 out of each
19cycles; these are test conditions, separate from the predeclared conservative
memory sensitivity point. All30 DUT source hashes match the synthesis freeze.
Full-capacity16K-cycle PV initialization is charged on every sample; it accounts
for83.32%/73.11% of the small graphs, so their elapsed cycles are not scaled to
large workloads. `fixtures_full_b/summary.json` and its complete event/phase/
request-kind traces bind the functional result. Model calibration at this test service point is complete with the declared
limits below.


## RTL/finite-model calibration

The selected model snapshot is now model_g, binary
`4ef2084643c48ad2937689ca02e9573bd342799f68555acf9bb1516f6cbce598`.
All52 complete small-graph executions match the full production RTL in every
output byte, all19 core-phase counts, total cycles, all12 request-kind totals,
parent/candidate/commit/publication/retirement counts and the complete logical
request schedule (cycle, source, kind, line, localID and generation).

| Complete RTL/model comparison | Samples | Total cycles, both | Maximum sample cycle difference |
|---|---:|---:|---:|
| d3 base | 8 | 157312 | 0 |
| d4 base | 12 | 268916 | 0 |
| d4 deterministic backpressure/jitter | 12 | 276758 | 0 |
| d3 conservative160ns/10ns | 8 | 162025 | 0 |
| d4 conservative160ns/10ns | 12 | 282252 | 0 |

The five source-bound comparisons are in `model_comparison_g`. All use the
5ns test clock and the same30-file repaired DUT closure. These are observed
exact matches on the declared test suite, not a formal equivalence proof for
all graphs. Full-core routed-clock qualification remains separate.

Corrections implemented actual omitted services: controlFIFO2, bounded POP
holds/capture, real ACK timing, per-port initialization, serialized cost loads,
finite enum/scratch finish, direct internal commit and wave/export edges.
The selected reset/member-release semantics follow RTL, even though an earlier
version had a smaller net error. No empirical multiplier is applied.

The model still evaluates service classes in rotating order with explicit
due-edge guards. It now samples the complete frontend-idle expression before
any service-class mutation and publishes it through the actual registered
visibility stage. Reset clears this register; LOAD/INIT preserve the real
settling semantics. Backend, network and output idle retain their own timing.
No unconditional extra cycle per wave is added. A changed DUT or selected
service/frequency point requires corresponding revalidation.

The conservative-service audit has since isolated a concrete missing visibility
stage in model_f. A source-matched diagnostic RTL probe shows that, for d3 q2
wave8, all transactions and top-level drain conditions are ready at relative
cycle21538 except the registered frontend-idle bit11. That bit becomes visible
at21539; the testbench observes FLUSH at21540. Model_f observed FLUSH at21539.
This changes the subsequent free-running bank rotor and can change source/tag
allocation even when request-address multisets and outputs agree. This is a
measured register-visibility omission, not merely an unexplained small error.
The explicit model_g repair removes every previously observed phase/request
residual in the52-case suite. Model_f's earlier maxima of1/13/18 cycles for
base d3/base d4/stress d4 and its19/32 exact schedules remain in the historical
receipts. They are not carried forward as current model error or attributed
solely to an unavoidable service-order approximation.

Model_f also completed the full80 large samples while this audit was in
progress. BNN40/LSTM40 outputs match every golden byte and their original
complete hashes. Cycles are102,563,265/104,150,798, or0.512816325/0.520753990s
at an assumed200MHz. These are explicitly **pre-repair conditional results**,
not final calibrated or implemented-frequency FPGA times. Their19-phase sums,
per-port request/return conservation and full outputs are preserved in
`model_full_c_200_base/verification/delivery.json`.

## Resource and clock qualification

The initial full-core source closure is30 files. Actual full-core synthesis is
running at5ns. The earlier1,254,466-LUT module sum is a historical planning
estimate, not this core's measured fit. Full-core resources, unconnected-output
classification, mapped memories, blackboxes and trimming will be audited from
the actual run. No complete-core clock is qualified yet.

The running first synthesis has now reported `Synth8-326`, automatically
breaking a combinational loop through output `write_v[1]`. The source chain is
strict-prefix second-valid → admin valid-gated request metadata → adapter
kind/address legality → network ready → first-write ready → second-valid.
This inferred timing exception is not accepted as closure. A bounded integration
repair separates stable export metadata from second-valid; only the actual
request-valid remains valid-gated. Capacity/credits/service latency remain
unchanged in the completed full native regression below.
The original synthesis stays running to retain actual resource evidence.
The repair is now frozen in `full_synth_c/source`. `fixtures_full_b` passed all32
full samples and11 rejection checks: complete outputs, every accepted-event
trace, all phase/kind/sample counts and absolute simulation finish times are
identical to `full_a`. The newly bound `model_calibration_f_admin_c` contract
independently verifies this identity and reuses the completed model_f runs;
its observed calibration differences remain retained in that prior contract.
The model_g contract now supersedes it for current calibration. Only
`cp_admin.sv` changed in the30-file DUT closure. Actual repaired full synthesis
started in `full_synth_c` at5ns after the regression passed; the original `b`
continues as retained diagnostic evidence. No repaired loop-free synthesis or
routed-clock claim is made before its terminal report.

An additional narrow `dispatch_synth_a` diagnostic exposes all runtime ports of
the unchanged production POP dispatcher. Its source matches both complete-core
freezes. This new controller had standalone functional tests but no completed
resource/path report. The diagnostic preserves the full-core runs and cannot
qualify their clock or area. Unlike the integrated core, it exposes all six
statistics counters. Vivado2022.2 excluded the diagnostic's original bulk I/O
delay commands because they selected more than10,000 objects; the5ns internal
clock remains applied. A separate chunked post-synthesis constraint file is
prepared for path/coverage analysis. Synthesis ran without the excluded I/O
delays, which is an explicit diagnostic limitation. Neither complete-core log
contains that object-limit warning.

The OOC scope excludes shell, PCIe and HBM controller. Input/output min/max
boundary delays are0.1/0.8ns with0.1ns clock uncertainty. No real path is declared
false to manufacture timing closure. Vivado2022.2 project flow uses the actual
`STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS` property with explicit `-name/-value`
arguments for `-mode out_of_context`; failed setup attempts are retained.

## Memory scenarios and interpretation

Predeclared service scenarios are80ns latency/5ns issue interval and a diagnostic
160ns/10ns scenario. Both are assumptions, not measured HBM or guaranteed worst
case. Once a full-core frequency is selected, nanoseconds convert by ceiling
to core cycles and the model is rerun. Old cycles are not divided by a newly
chosen frequency. Board time remains null.

While full synthesis is running, the coordinator has also authorized the
current repaired candidate's complete BNN40/LSTM40 run at the initial200MHz
target as a conditional functional/capacity baseline. This exception to the
runner's coordinator gate does not qualify that frequency or establish final
selection. Its explicit decision receipt retains this distinction. If the
selected routed frequency differs, the corresponding full batches will be
rerun with newly derived memory service cycles. The predeclared conservative
service point is being checked on the same complete native RTL structure.

## Resident memory and one-build E2 scope

The selected40-job layouts occupy address spans2,885,563,488/2,930,877,536
bytes for BNN/LSTM, within nominal8GiB backing. Required fused descriptor
inputs are1,312,849,920/1,333,370,880bytes and prepared edges are
153,371,104/155,940,112bytes. The reserved old-META address gap is not an
additional loaded input. These checks apply to these two layouts; independent
maximum nodes/jobs/cells are not asserted to fit8GiB in every combination.
`resident_memory_span.json` binds the address arithmetic to the prior admission.

Required construction is not assumed free. The unchanged converter already has
one isolated, source/input/output-bound observation per case, reused through
`software_a/historical_audit.json`:

| Historical converter stage, seconds | BNN40 | LSTM40 |
|---|---:|---:|
| Native load and eligible graph preparation | 1.472225010 | 1.468351236 |
| Format/range/target admission | 0.432226943 | 0.445848315 |
| Descriptor image construction | 0.639816268 | 0.647709184 |
| Descriptor backing writes | 0.221518203 | 0.236807465 |
| Independent prepared-edge identity check | 0.120627044 | 0.122630682 |
| Independent descriptor decode check | 0.496897985 | 0.505485695 |

These are single observations, not a new three-process cohort. Timers were
checked in `descriptor/convert.cpp`: backing-write time covers descriptor writes,
not all converter I/O, and the stage rows are not a replacement for process
wall time. Independent identity/decode checks are research validation; format
admission and actual image construction remain required for this representation.
File persistence depends on the deployed input path. Device transfer, invocation
and required host postprocessing have no board measurement here. No transfer
bandwidth is invented, and no resident advantage is promoted to an E2/Process
advantage. The separate native E2/Process table and ALT/STRICT qualification
remain in the companion evidence report.

## Provisional claim ledger

| Claim | Current support |
|---|---|
| Optimized CPU thread selection on current allocation | measured, complete |
| Whole-pair ALT CPU outputs equal frozen golden | exact full batches |
| Runtime connected production L1 source/function | 32 complete executions and11 rejection checks passed |
| Complete-core resources fit U280 | pending actual synthesis |
| Complete-core routed clock | unqualified |
| RTL/finite-model calibration at200MHz test service | 52 complete cases with exact phase/request schedules |
| Final-frequency complete-batch FPGA time | pending |
| CPU-primary acceleration in simulated scope | not yet established |
| GPU universally unbeatable by FPGA | neither required nor claimed |
| Board-measured FPGA/E2 speedup | not measured |

Resident, one-build E2 and native VPR Process remain separate. ALT output
identity does not establish STRICT bitwise equivalence. Full evidence, failure
classification, reproduction, archive verification and remote commit identity
will be appended only when those steps complete.

The MCP webserver status adapter reports an invalid recursion string with
Vivado2022.2; that metadata is not used as job status. Direct Tcl proxy
`get_property STATUS/PROGRESS [get_runs synth_1]` and the source-bound child
process/run log supply the authoritative state. The existing job is retained.

This source/evidence checkpoint is not final completion. `checkpoint_stage.json`
records the still-live full synthesis and pending physical/full-batch stages.
The compressed archive is a point-in-time snapshot; subsequent terminal results
will be added in the same independent branch.
