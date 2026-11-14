# Descriptor front: corrected service contract and exact representation

**NO_GO_THIS_CONFIGURATION.** Exact descriptor fusion is functionally verified,
but its matched native representatives are slower. F2 group redistribution
reduces complete-batch conditional cycles by about 1.5%, remains slower than
CUDA, and the actual generic common-network mapping exceeds device capacity.
The repaired local four-lane frontend passes 5 ns timing; the backend retains
outer-interface hold failures. No complete-kernel clock or board result is claimed.

Base: `ccec3da64b4c5be643809c2bdda94145c4bb8187`.
Independent branch: `accel/lookahead-descriptor-front-20261114`.
Guidance: [the complete independent execution document](CODEX_FPGA_DESCRIPTOR_FRONT_AFTER_CCEC3DA.md).
Implementation: [fpga_descriptor_front](../accel/lookahead/fpga_descriptor_front/).
Raw evidence root: `results/fpga_descriptor_front_20261114/` in this worktree.

## Changes and limits

This experiment replaces historical abstract service assumptions with finite
registered request/return networks, per-group request and return quotas,
synchronous directory RAM operations, an actual global minimum collector,
six elastic FP32 arithmetic stages and a synchronous eight-bank output service.
It adds an exact packed descriptor representation and separates its effect
from the effect of changing eight groups of eight lanes into sixteen groups
of four lanes. Historical final-D totals are not reused as the new C0.

| Configuration | Representation | Groups × lanes | Total lanes |
|---|---|---:|---:|
| C0 | Separate ROW and META | 8 × 8 | 64 |
| F1 | Exact packed descriptor | 8 × 8 | 64 |
| F2 | Separate ROW and META | 16 × 4 | 64 |
| F3 | Exact packed descriptor | 16 × 4 | 64 |

All four use 256 E contexts, 512 beat slots, 128 fork tokens and 128 ready
capacity; global POP admission remains eight per cycle. Each group permits
one EDGE request and one EDGE return per cycle, separately from its control
request/return service. The common network has 32 physical 32-byte ports,
32 credits per port and four classes sharing each port. The initial memory
assumption is 80 ns from actual external issue, with a 5 ns issue interval.
These are simulation assumptions, not measured HBM performance.

Each source has FIFO4 followed by a registered request arbiter. The physical
port has four FIFO4 clients, a tagged held request, request FIFO2, response
FIFO2, return FIFO4 and registered client/source return paths. A released tag
is reusable on a later edge. Full FIFO replacement cannot occur on the same
edge as a pop. Backend context queues and directory/completion ACK delays
are explicitly charged. The new global fabric replaces the old local fabric;
it does not provide a second pool of credits.

The bank directory uses 8192 members and 4096 buckets. Its payload, next,
free-stack and head/tail RAMs have explicit synchronous operations. APPEND
completion is required before publication retirement. An actual 64-bank
collector and six registered min stages replace a software-wide minimum.
Output target updates use synchronous read/compare/write, same-cell forwarding,
finite completion positions and eight bank arbiters. Export includes backing
writes and ACK drain. Exact interface timings are recorded with each final
source-bound run.

The complete accumulator datapath and assembled kernel remain outside full RTL
calibration. Local module calibration does not grant a complete-kernel clock.
Conditional cycle estimates are never divided by an inferred frequency from WNS.

## Final four-grid representative comparison

The sample list was fixed before new timing results: BNN 2/19/35 plus historical
tail 31, and LSTM 7/19 plus historical tail 18. These are complete actual samples,
not trace-driven kernels. Final model D includes the real 32-to-2 registered
output ACK collector and registered export start/done boundaries. Every output
matches its frozen golden slice. The table sums the selected samples only; it
does not extrapolate forty-sample time.

| Configuration | BNN four-sample cycles | Change from C0 | LSTM three-sample cycles | Change from C0 |
|---|---:|---:|---:|---:|
| C0 | 7,305,687 | — | 5,531,365 | — |
| F1 | 8,634,228 | +18.185% | 6,549,289 | +18.403% |
| F2 | 7,194,777 | -1.518% | 5,448,846 | -1.492% |
| F3 | 8,549,910 | +17.031% | 6,486,197 | +17.262% |

F2 is selected independently for both complete-batch comparisons. Fusion reduces
physical request count (BNN selected samples: 78,446,007 for C0 versus 65,591,391
for F3), but this does not translate into lower wall cycles. F3 POP+expand grows
from 4,910,825 to 6,153,954 cycles while finalize remains about 2.25 million.
The finite fused D records retain their token until both branches hand off;
reduced traffic does not imply an earlier token release. Occupancy and actual
token-residence diagnostics are kept with the run, without treating parallel
slot-cycle counts as wall time or as a counterfactual proof of an untested fix.

Intermediate models A/B/C are preserved. They establish functional or protocol
bring-up evidence, but their timing is superseded by D. In particular C lacked
the final registered export/ACK boundaries; its totals are not silently adjusted
and relabeled. D actually reruns the affected samples with a new source freeze.

## Complete native batches under the final contract

All four mandatory forty-sample batches complete the actual algorithm, including
new spills, all waves, per-sample initialization, target/queue drain and every
output write ACK. Concatenated outputs match the two full golden SHA-256 values
below. Fourteen matching final-D representative checkpoints are reused; the
remaining 146 samples are newly executed. CPU parallelism does not overlap
hardware samples. These are finite-model results under the 200 MHz / 80 ns /
5 ns assumption, with **no qualified complete-kernel clock**.

| Case | Configuration | Complete cycles | Conditional seconds | Change from C0 |
|---|---|---:|---:|---:|
| BNN40 | C0 | 72,347,012 | 0.361735060 | — |
| BNN40 | F2 | 71,238,001 | 0.356190005 | -1.533% |
| LSTM40 | C0 | 73,374,604 | 0.366873020 | — |
| LSTM40 | F2 | 72,236,324 | 0.361181620 | -1.551% |

| Case/configuration | Init | POP+expand | Finalize | Export | Other control | Sum |
|---|---:|---:|---:|---:|---:|---:|
| BNN C0 | 1,284,240 | 48,888,167 | 22,012,290 | 126,640 | 35,675 | 72,347,012 |
| BNN F2 | 1,284,240 | 47,780,276 | 22,011,170 | 126,640 | 35,675 | 71,238,001 |
| LSTM C0 | 1,304,280 | 49,609,893 | 22,295,250 | 128,920 | 36,261 | 73,374,604 |
| LSTM F2 | 1,304,280 | 48,472,608 | 22,294,255 | 128,920 | 36,261 | 72,236,324 |

The categories are exclusive measured wall-cycle phases and sum exactly to the
complete cycles. Per-bank retry counters are not summed to manufacture time.
The small F2 improvement is concentrated in POP+expand. F2 is still approximately
2.35×/2.26× the strongest BNN/LSTM CUDA resident time even under the conditional
clock. There is no simulated software advantage, and a 1.5% modeled improvement
is not evidence of a confirmed hardware speedup.

F1/F3 have complete representative samples, not claimed forty-sample measured
batches. Historical final D used a different service contract; its roughly
52-million-cycle totals do not substitute for these fresh C0 results.

## Critical waits and the conditional-candidate decision

No supplemental candidate is launched. The decision uses complete batch D,
not old enum5/K1 no-go conditions. For each wave the diagnostic selects the
bank with the latest actual busy/retirement edge and retains that bank's
exclusive finalization-state histogram. Its categories sum to finalization
wall cycles; they do not sum overlapping banks or retry attempts.
The labels are priority-coded state occupancy, not a direct causal stall
measurement. Empty-final waves (329 BNN and 328 LSTM per configuration) retain
the default bank zero with no busy edge; they are not evidence that bank zero
is critical. Independent review checks the wave-level histogram identities.

| F2 complete batch | Publication-held observer cycles | K8-full cycles | Scratch/merge cycles | Finalize cycles |
|---|---:|---:|---:|---:|
| BNN | 17,526,388 | 1,048,291 | 869,658 | 22,011,170 |
| LSTM | 17,805,258 | 1,060,944 | 821,729 | 22,294,255 |

Publication occupies about 79.6%/79.9% of this exclusive critical-tail observer,
versus about 4.8% K8-full and 4.0%/3.7% scratch/merge. These observations do not
establish the guide's required K8 or single-merge causal bottleneck, so K16 and
merge2 are not selected. As an additional diagnostic, removing the entire
measured finalize phase from the unchanged F2 schedule still leaves
0.246134155/0.249710345 s, above the CUDA targets. This subtraction is not a
new simulated architecture or a lower bound on all possible designs.

Two-sample phase interleaving is also not selected: the matched F3 representatives
increase expansion, so its required premise is absent. No `max(expand,finalize)`
shortcut, duplicated free service, unimplemented packed dual-job RAM or automatic
URAM capacity reduction is credited. The experiment does not scan extra K,
scratch, context or frequency configurations.

F2 dynamic peaks are K=8, spill IDs 883/824 per bank (capacity 2048), directory
members 3495/3531 per bank (capacity 8192), and two accepted output ACKs per
cycle. Every sample checks complete traffic, publication/retirement and output
conservation. The normal native export requires no ACK-source backpressure;
small jitter and actual RTL tests exercise collisions and blocked returns.

The appropriate result is **FINITE_MODEL_GAIN_ONLY** for F2's small change and
**NO_GO_THIS_CONFIGURATION** for the software-advantage target. Neither case
meets the full-kernel advancement conditions: there is no predicted same-boundary
software win or single concretely implemented remaining fix, and the separate
F2 frontend/global adapter/full accumulator/assembled timing qualifications are
missing. Therefore no synthetic substitute is presented as a complete kernel,
and no ineligible complete-kernel OOC is launched. This does not rule out other
FPGA structures.

No descriptor CUDA run is triggered: F3 worsens the gap and does not enter the
complete-kernel stage. F2 uses the old separate representation. The strong
historical CUDA baseline remains the target, while packed software is given a
complete functional CPU implementation and formal CPU measurement. No alternate
clock or memory-service point is claimed; changing either requires a fresh
finite-model execution with the corresponding service and pipeline contract.

## Exact descriptor and identity

The little-endian 8-byte ABI is begin32, degree16, cell15, valid1. Invalid cells
are encoded as zero. Admission checks all native nodes and samples before
selecting the format. Degree overflow selects an exact whole-graph 16-byte
begin/end/cell/flags representation; it does not truncate degree or expand
hardware capacity. Address and stride calculations use wide arithmetic.

All 100 native samples and 20 forced-16-byte small samples match frozen ALT
outputs. Boundary tests include degree 65536 and a complete 65538-degree
fixture, forced-8-byte rejection, 32-bit offset limits and addresses above
2 GiB. Native maximum degree is at most 249, so both large graphs admit 8 bytes.
The full packed backing is independently decoded against original semantics.

| Native case | Nodes | Prepared edges | Descriptor bytes, all 40 samples | Descriptor address interval, bytes |
|---|---:|---:|---:|---|
| BNN | 4,102,608 | 38,342,776 | 1,312,849,920 | [1,499,042,816, 2,811,892,736) |
| LSTM | 4,166,724 | 38,985,028 | 1,333,370,880 | [1,522,646,016, 2,856,016,896) |

The actual layout retains the old ROW/META reservation and adds this descriptor
region; it does not claim that old storage has been reclaimed. All four controls
reserve the same address region before downstream canonical/scratch/output/cost
memory, so a change in downstream port striping is not an accidental variable.
These are device-layout byte addresses; the generic fabric's line address is
in 32-byte units. The complete admission/address checks precede execution.

| Complete ALT output | SHA-256 |
|---|---|
| BNN | `a8ca4003a3b015145635a3f776bb62a3aec1ec2121a1fbfc8712d2a2dc1c8c3f` |
| LSTM | `6b2acd7718d880075d653b3b83f1fa3abb5161f6f346ed39c3aa1285160a95cf` |

The previous native input arrays, unchanged import adapter, actually imported
ALT output and final wire maps are rehashed in
`software_reuse_a/native_identity.json`. Identical bytes through that unchanged
chain justify reusing native/QoR qualification. This is a transitive identity
proof, not a new VPR run. ALT is not claimed bitwise equivalent to STRICT.

## Evidence reuse and comparison boundary

`reused_evidence.json` verifies 254 historical software receipts, six completed
P8/F0 model batches, supplemented CUDA source bindings and frozen golden hashes.
No historical GPU/model experiment is restarted. The strongest frozen resident
complete-batch CUDA means are BNN **0.15179996944444446 s** and LSTM
**0.15949799988888888 s**. Their nine observations are three independent
processes with three retained repetitions each, not nine independent processes.

The strongest same-boundary historical eight-thread prepared CPU controls on
the H100 worker have mean-of-process-means 3.654426308 s and 3.669705272 s.
They run on a Xeon Platinum 8462Y+, distinct from this FPGA tooling host.
Other CPU cohorts and native E2/Process observations remain separately reported
in `software_reuse_a/software_baselines.json`. Summed router worker time cannot
stand in for resident wall time or complete VPR Process acceleration.

The new packed CPU implementation uses the same persisted representation,
performs every sample reset and checks complete output. Functional timings
under concurrent modeling/EDA are explicitly unqualified. Formal measurements use a quiet window, eight distinct physical cores, explicit
affinity, one warm-up and three retained repetitions in each of three processes/case.

Construction, backing writes, cache validation and first transfer are outside
resident. E2 must include whichever of these operations the deployment needs.
No board transfer or new native Process time is measured; no amortization is
assumed merely because a batch contains forty samples.

## Local implementation evidence

The final four-lane fused frontend context passes actual 5 ns OOC timing:
setup +0.255 ns, hold +0.019 ns and pulse +1.968 ns, with zero failing endpoints,
all twelve constraint coverage counts zero and no methodology violations.
All 15550 routable nets are routed; the 857 RTSTAT warnings are external-only
outputs without internal sinks, as classified in the retained net audit.
The result is **LOCAL_RTL_TIMING_QUALIFIED** for this specific context.

Earlier frontend A/B setup failures (-0.650 ns and -0.335 ns) are retained.
The final repair moves operand legality checking behind existing registers and
replaces the wide beat-position selection with links inside the same finite
beat-slot pool. It adds neither payload slots nor pipeline latency. Twelve
complete pin traces are byte-identical before/after the repair, covering FP32,
four/eight-lane groups, parent context and actual BNN/LSTM address/target windows.
The independent old beat-match cycle model still agrees. Native tests use real
nonzero absolute EDGE bases, both descriptor formats, zero-degree targets and
the highest legal beat offset. Full generation/job identity for two simultaneous
samples is not claimed by this single-active-sample implementation.

The final backend context retains enum2 and real K8 canonical behavior. Native
fixed and out-of-order-response tests cover 19 waves each; additional tests
cover 2048 operations and 2048 saturated-port requests. The canonical stage
replay checks 11749 cycles per bank, including held publication and actual
release one edge after result consumption. Physical requests are checked
against the 16-edge external memory latency. These are local backend tests,
not a complete native-kernel RTL run.

Backend OOC B uses real FF queues at the parent interfaces. An earlier attempt
inferred LUTRAM for FIFO2 payloads; its reports are preserved, and the corrected
FF implementation reproduces the same pin-cycle traces. At a 5 ns clock with
unchanged input/output min 0.100 ns and max 0.800 ns, the final routed result is:

| Backend OOC B check | Actual result |
|---|---:|
| Setup WNS / TNS | +0.005 ns / 0 |
| Overall hold WHS / THS | -0.080 ns / -188.327 ns |
| Hold failing endpoints | 2450, all outer INPUT_INTERFACE |
| Internal register-to-register setup / hold | +0.005 ns / +0.011 ns |
| Pulse worst slack | +1.800 ns |
| Twelve constraint coverage counts | all zero |

The old direct external-input-to-core-RAM paths are eliminated. All remaining
negative hold paths end at the new boundary FFs; none are internal register
paths. This is useful evidence for the actual internal context, but the overall
OOC still fails. It does **not** establish a 200 MHz complete kernel. Existing
replacement RAM methodology warnings and external-only dangling output nets are
classified in the raw audit; no missing internal loads are hidden.

The actual combined output service/ACK collector closes 1413 cycles, 1024 target
updates and 62 exported beats/ACKs. Four simultaneous source ACKs exercise the
two registered collector slots and source backpressure. Exact independent
replays check source holding, arbitration, forwarding, packing and final drain.
Export first-write-valid is three edges after start acceptance; done becomes
visible two edges after the last ACK handshake. This closes a real model/RTL
capacity mismatch found during review; a free software-only ACK quota is not
used. Output RAM inference is recorded separately from this functional result.

The service tests compare actual HDL pins against explicit cycle models and
separate conservation oracles:

| Service | Matched cycles | Work / stress |
|---|---:|---|
| Directory bank | 173877 | 24610 commands; full 8192-member pool; detach/append/free/MIN hazards |
| Complete memory network, 8 sources / 2 ports | 2184 | 2048 requests; OOO returns; FIFO4 and 32 credits reached |
| Candidate network, 64 lanes / 64 banks | 2817 | 4096 candidates; hot-bank conflicts; FIFO16 reached |
| Six-stage MIN tree | 1200 | 533 transactions with output backpressure |
| MIN collector + 64 actual directory banks | 8824 | 32 queries, initialization and staggered responses |

The full 208-source/32-port C++ transport adapter is separately compared with
the composed network for 45071 transactions over more than 12000 cycles. This
does not turn the reduced-geometry HDL test into a full-network routed timing
claim. Independent return payload tests use non-echo 256-bit values, and all
32 physical-port/four-class destination encodings are checked.

The descriptor front's FP32, EDGE and fused decode/context calibration applies
only to those actual modules. In particular F2's separate ROW/META controller
does not inherit a complete-front timing qualification from the fused F3 RTL.
Full accumulator and global integration timing also remain separate.

## Resource accounting method

Use actual physical inference, including queue payload and control, rather than
logical RAM bits. One directory bank synthesizes to 794 LUT, 379 FF,
9 BRAM36 + 2 BRAM18 and 2 URAM. Arithmetic scaling to 64 banks is 50816 LUT,
24256 FF, 640 BRAM36 equivalents and 128 URAM, before global placement.
The complete 64×64 candidate network synthesizes to 250969 LUT and 7872 FF;
this substantial crossbar cost is not replaced by an ideal unit-cost router.
The minimum collector/tree adds 1666 LUT and 1787 FF.

Backend B synthesizes to 17072 LUT, 19173 FF, 14 BRAM36 equivalents and 16 URAM
per two banks. Replacing its local fabric and physical FIFO2 pair subtracts
3800+150+166 LUT and 6058+570+527 FF, leaving 12956 LUT and 12018 FF per pair
for conservative composition bookkeeping. There are 142 local-fabric telemetry
FFs per pair that may be duplicated by the new network's counters; this possible
overcount is explicit. Routed counts differ and are retained in their own ledger.
The common network is added once, with full 256-bit write payload and metadata
through every real queue. None of these arithmetic sums constitutes a placed
complete-kernel fit result.

Directory, candidate and minimum/common-network synthesis are resource-only
runs without a clock constraint. Output RAM synthesis also precedes its Tcl
clock creation; adding a clock afterward is not timing closure. Frontend and
backend context flows use their actual 5 ns XDC before synthesis and routing.
This distinction is retained in the compositional ledger.

The repaired full output context synthesizes to 16971 LUT, 7477 FF,
56 BRAM36 + 8 BRAM18 (60 BRAM36 equivalents), zero LUTRAM/URAM/DSP. Its initial
template instead inferred 116082 LUT including 77824 LUTRAM and zero BRAM;
that failed inference and its warnings are preserved. A single explicit write
address/data/enable template restores the intended RAM while producing exactly
the same two complete RTL traces. No routed output-clock result is claimed.

The generic network preserves an opaque 32-bit local identity and eight-bit
source ID. The functional model retains separate kind/id/generation fields for
checking. Per-source packing fits the native admission bounds, but the final
source-specific wire adapter and its complete-top timing are not implemented
or calibrated here. Opaque payload transport tests are not evidence for that
missing whole-kernel adapter. This remains an explicit qualification limit.

## Formal packed CPU and isolated construction

The tooling host is a dual-socket Intel Xeon Gold 6530. The final packed CPU
means of process means are **2.842626751333 s BNN40** and **2.933218058 s LSTM40**;
median-of-process-medians are 2.786294191/2.910972875 s. Each case uses three
independent processes, one warm-up and three retained repeats per process,
eight distinct physical cores and explicit OpenMP affinity. All complete
outputs match and all process competition checks pass. These measurements are
on a different host from the historical Xeon 8462Y+ cohorts; no representation-only
speedup is attributed across hosts.

The original EDA process tree was temporarily suspended in memory during this
window, then resumed with the same sixteen PID/start identities. Every suspended
process has exactly zero CPU ticks of progress in the recorded interval. The
wrapper resumes in `finally`, including on measurement failure. Existing EDA
memory remains resident; it performs no concurrent computation. This allows
isolation without restarting or discarding the ongoing synthesis.

One isolated converter process per case gives the following observations;
these are single construction observations, not a nine-repeat statistical result.

| Conversion stage, seconds | BNN | LSTM |
|---|---:|---:|
| Native load and preparation | 1.472225010 | 1.468351236 |
| Full-input admission | 0.432226943 | 0.445848315 |
| Independent eligibility identity | 0.120627044 | 0.122630682 |
| Packed construction | 0.639816268 | 0.647709184 |
| Backing writes | 0.221518203 | 0.236807465 |
| Independent decode checks | 0.496897985 | 0.505485695 |
| Total process wall, including checks/control | 3.593837371 | 3.589895270 |

Generated descriptor/EDGE/ROW backing hashes are identical to the original
admitted conversion. The converter's internal receipt conservatively retains
its default unqualified flag; the external isolated-run receipts qualify only
these new observations. The earlier concurrent construction timings remain
separate. No transfer or board timing has been measured: a cold E2 deployment
must add its required conversion/validation, transfer, execution and result
return, while an actually cached deployment must state its cache-check cost.
Resident and E2 times are not interchanged.

## Final common-network mapping and stop decision

The actual full208-source/32-port network completes synthesis optimization with
zero errors, zero critical warnings and512 warnings. Its raw `Report Cell Usage`
contains the following mapped primitives:

| Primitive | Actual count |
|---|---:|
| LUT1 / LUT2 | 4,414 / 34,618 |
| LUT3 / LUT4 | 4,350,370 / 356,592 |
| LUT5 / LUT6 | 4,398,596 / 592,345 |
| MUXF7 / MUXF8 | 1,860,554 / 359,728 |
| FDRE | 324,743 |
| RAM16X1D / RAM32M / RAM32M16 / RAM32X1D | 64 / 32 / 7,040 / 64 |

The9,736,935 logic LUT primitives require at least4,868,468 physical LUTs even
under the optimistic limit of two logical functions per dual-output LUT. This
already exceeds1,303,680 device LUTs (373.44%) before counting its RAM LUTs or
any other module. This is an actual mapped-netlist lower bound, **not** an exact
post-combining utilization count. All512 warnings are `Synth8-7186`: the client
qmem distributed-RAM attribute is ignored. The actual mapped implementation is
counted, with no assumed attribute-based saving.

After this decisive negative result, the subsequent `Translating synthesized
netlist` import was deliberately terminated. Synthesis optimization completed;
the full `synth_design` command did not return a success code. No completed
common-network `report_utilization`, DCP or routed clock is claimed. The original
source freeze, raw mapped report, complete log, warning rows and process
termination receipts are retained in `services_memory_synth`. This is an
evidence-based stop of this generic network implementation, not a tool failure
relabelled as successful synthesis and not a claim that every FPGA network is
infeasible.

Replacement-aware bookkeeping gives the following conservative composition.
LUT figures including this network are **lower bounds**, exclude its RAM LUTs,
and are not an integrated placement result:

| Composition | LUT | FF | BRAM36 equivalents | URAM |
|---|---:|---:|---:|---:|
| Common modules excluding frontend | >=5,603,482 | 750,711 | 1,148 | 640 |
| Add16 synthesized F3 four-lane contexts | >=5,753,690 | 890,887 | 1,148 | 640 |
| Device capacity | 1,303,680 | 2,607,360 | 2,016 | 960 |

F2's separate ROW/META frontend area remains unknown. Full-top constant
propagation and a different staged/sparse return network could change area;
they are future implementations requiring fresh evidence, not free savings
credited here. The next research question is how to replace this expensive
all-destination registered routing while preserving bounded service, rather
than adding K or assuming a faster clock.

## Reproduction, archive and terminal state

Use the subdirectory commands in the implementation README and the exact frozen
commands/bindings in each run. Final model D is the performance source; A/B/C
remain intermediate evidence. `review/model_d_unique_full_batch_audit.json`
checks334unique samples,14 identical reused references, all four ordered full
outputs, actual input/golden hashes, phase sums, traffic and dynamic capacities.
`review/software_formal_parent_audit.json` checks six independent CPU processes,
18 retained repetitions and the sixteen-process suspension/resume identities.

The compact archive is
`results/fpga_descriptor_front_20261114/evidence_snapshot_final_a/manifest.json`.
`delivery/archive.py evidence_snapshot_final_a --verify` verifies each compressed
object's original length and SHA-256 plus final source/report hashes. It retains
full outputs, raw timing and functional traces, actual mapping statistics,
failed attempts, commands and bindings. Regenerable multi-gigabyte backing,
ELF/vendor build trees and DCP are omitted with their producing bindings; the
nested backend archive is not duplicated because its original evidence is
included directly. Historical archives are referenced without repackaging.

Only this independent candidate branch is committed and normally pushed.
The post-publication receipt records the actual local and remote full SHA,
archive verification and terminal process scan outside the immutable snapshot,
avoiding a self-referential commit/archive hash. All18 protected local refs,
original guidance and old tracked files remain unchanged. No old GPU/model
experiment was restarted. All owned experimental processes are terminal;
historical sessions were left untouched. Minor frozen testbench whitespace and
the original guide's final blank line are intentionally preserved for hash identity.

Final status: **FUSION_FUNCTIONALLY_VERIFIED**, **FINITE_MODEL_GAIN_ONLY**,
**LOCAL_RTL_TIMING_QUALIFIED** for the actual L4 descriptor context, and
**NO_GO_THIS_CONFIGURATION** for software advantage and the generic network.
`complete_kernel_clock_qualified=false`, `estimated_seconds_at_qualified_clock=null`,
`board_measured=false`, `board_measured_seconds=null`.
