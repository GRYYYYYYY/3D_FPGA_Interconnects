# Independent FPGA subsection draft: CPU-primary evaluation

This is a separate draft. It does not modify the original manuscript. The
implementation and physical-closure results below remain provisional until
the closure report's qualification ledger is finalized.

The original f complete-core implementation fits the device's global LUT count
at1,233,715 LUTs,749,174 FF,1,148 BRAM36 equivalents and640 URAM, but routing
failed with level7 global congestion and5,809,714 node overlaps. It therefore
provides no qualified frequency or FPGA-versus-CPU timing result. One same-source,
same5ns `SSI_SpreadSLLs` implementation has completed placement at1,232,534LUTs
and749,226FF, with unchanged BRAM/URAM/DSP. Its SLL boundary use is85.45%/89.09%,
but CLB sites remain99.92% occupied and the high-congestion warning persists.
Completed post-place reports give WNS−15.487ns/WHS−3.530ns at5ns; setup and
hold remain unclosed. Default phys_opt made zero cell changes and no timing
improvement; default routing is now in progress.
Initial router estimates still exceed total SLL capacity onSLR0/1(106.02%)
and show localized over-capacity columns on both boundaries; route terminal
legality and frequency remain unknown.
Existing200MHz model
predictions remain conditional; the physical OOC interface-context limitation
also remains unresolved. These observations do not establish a universal FPGA
no-go and do not alter the retained historical evidence.

We evaluate a finite FPGA core against an optimized CPU implementation of the
same ALT whole-pair FP32 lookahead contract. A retained H100 implementation is
a strong comparator; surpassing the GPU is not a condition for studying CPU
acceleration. We distinguish measured software time, RTL cycles, architectural
predictions at an assumed frequency, and predictions supported by a routed
complete-core frequency. No FPGA board time is measured.

The L1 core connects64 candidate lanes,16 frontend groups and64 canonical banks
to32 physical memory ports. Its runtime sample controller performs real state
initialization, cost loading, directory traversal and canonical POP, independent
transaction/descriptor lifetimes, finite candidate reduction and scratch,
K8 whole-word commit, serialized publication, and final output write/ACK drain.
The model retains finite queues, tags, identity and backpressure. Samples are
processed sequentially by the FPGA controller. The physical scope is the
complete core on the U280 FPGA, excluding platform shell, PCIe and HBM
controller; memory service is a stated simulation assumption.

The optimized CPU comparison uses an explicitly bound and NUMA-placed packed
implementation on a dual Xeon Gold6530 allocation. We tested8,32 and64 workers;
64 workers minimize mean resident time for both complete40-sample workloads.
Three independent processes each contribute three formal repeats after warmup.
The means are0.699624s for BNN40 and0.725510s for LSTM40, with process-mean SDs
0.026647s and0.021287s. The allocation has64 physical cores and a55-CPU-time
container quota;40 samples permit at most40 simultaneous solves. These results
characterize this allocation, not an unconstrained server. We retain the old
8-thread cohorts separately and do not use them as the strongest current CPU.

The strongest retained GPU resident means are0.151800s and0.159498s. CUDA
exposes sample parallelism through its second grid dimension and uses actual
64-bit atomic whole-pair minima. Its resident timer includes initialization,
wave launch/control, per-wave completion reads and final synchronization.
Full output transfer and research golden comparison occur after that timer.
The earlier BNN receipt lacks a contemporaneous executable digest; its frozen
source/build records and currently retained executable are documented without
retroactively claiming an execution-time hash.

Full-capacity RTL has completed two distinct native graphs with exact complete
output comparison (all8 and all12 samples); the complete congestion and11 range-rejection
checks also pass. Quantitative model calibration covers52 complete executions
across baseline service, deterministic backpressure/jitter and conservative
service. Outputs, all19 phase counts, total cycles, request-kind/retirement
counts and the complete request cycle/source/kind/address/identity schedules
match RTL exactly in these tests. A targeted RTL probe identified a missing
registered frontend-idle visibility stage in the earlier model; the corrected
model includes that register rather than fitting a cycle correction. The
observed exact matches are not a universal formal equivalence claim.
The first graph uses
157,312cycles and42waves; the second uses268,916cycles and106waves. The core
issues4,192 and21,511 physical transactions respectively, all acknowledged.
These small workloads validate the production structure; they are not scaled
into BNN/LSTM performance by graph size or lane count. The selected full batch
must be evaluated by the calibrated finite model at an actually qualified
complete-core clock.

Initial implementation targets5ns. We predeclare80ns/5ns latency/issue service
and a160ns/10ns diagnostic sensitivity scenario. They are not measured HBM
latencies or guaranteed bounds. Frequency changes require converting these
absolute times into service cycles and rerunning the model. Until full-core
resource/timing and model calibration are complete, no simulated FPGA speedup
number is claimed in this draft.

We separately measured complete-batch host output conversion on CPU0 of the
Xeon Gold6530 server. Three independent processes per case each ran one warmup
and three formal repeats; means were1.561172ms for BNN40 and1.537052ms for LSTM40,
with sample SDs of the three process means0.055318ms and0.106717ms. All repeated
outputs were byte-exact. This experiment replayed the physical layout from the
actual selected g outputs; it did not capture board DMA. The conversion timer
covers cost-pair word reordering and tail/stride removal using preallocated,
prefaulted buffers without cache flushing. Allocation and first touch were timed
separately; file I/O, validation, native map assembly and transfers were excluded.
The [bound postprocessing receipt](../results/fpga_cpu_primary_20261115/postprocess_final_g_a/delivery.json)
retains all repetitions and quiet-window observations. Packed CPU/CUDA output
conversion also lies outside resident, so this cost is not charged only to FPGA.
No board-readback or complete production E2 time is established by this cohort.

Resident completion, one-build construction E2 and the complete VPR Process
are distinct outcomes. Required preparation, transfers and postprocessing must
be included in E2 on the actual timeline, without counting already-included
control twice. The selected CPU reads the same packed descriptor and edge
images, so their required construction is common preparation for these
representations, not an FPGA-only cost. Only actual net additional steps can
consume the conditional resident margin. Research-only golden verification is not automatically charged
as production work. ALT exact-output agreement supports the retained native
import/QoR scope; it does not establish bitwise equivalence to STRICT.

The final discussion will explain the measured implementation's candidate
utilization, canonical/publication service and queue pressure alongside the
GPU's batch parallelism. Overlapping stall counts are not additive removable
time, and a minimum lifetime observed in a trace is not a universal hardware
lower bound. These results cannot establish that every FPGA architecture must
be slower than a GPU.
