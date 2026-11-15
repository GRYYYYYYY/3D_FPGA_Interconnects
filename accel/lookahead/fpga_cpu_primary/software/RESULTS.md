# CPU-primary baseline: completed bounded thread sweep

All18 independent processes passed all72 complete BNN40/LSTM40 batches
(18 warmups +54 formal), using exact frozen ALT full output validation after
every repetition. No observed competing EDA/model/software benchmark was active
during the coordinated quiet window. The raw terminal is
`results/fpga_cpu_primary_20261115/software_a/terminal.json`; `delivery.json`
binds summaries and checks every output and actual worker placement.

Platform: Intel Xeon Gold6530, two sockets ×32 physical cores, SMT2; process
allowed CPUs0–127, selected one hardware thread per physical core0–63. Container
CPU quota is55 CPU-time (`cpu.max=5500000 100000`).8/32 workers use socket0;
64 use both sockets.40 real samples permit at most40 simultaneous sample solves.
OpenMP dynamic sample scheduling is preserved, with passive idle waits.

Shared input is allocated with MPOL_INTERLEAVE over the selected sockets;
each pinned worker creates and first-touches its own scratch using MPOL_LOCAL.
The exact worker CPU list and NUMA maps are saved. The maps are captured after
the main thread's default policy switches to LOCAL; they must not be misread
as a before-allocation shared-input policy dump. At64 workers aggregate pages
are balanced across both nodes. No new data representation or FP32 algorithm
was introduced; the scalar work and sample initialization remain timed.

## All fixed thread points (seconds)

Statistics use3 independent process means. Each process retained3 complete
batch repetitions after1 warmup; the SD below is over the3 process means,
not over9 supposedly independent runs. No small-n confidence claim is made.

| Case | Threads | Mean of process means | SD of process means | Median of process medians |
|---|---:|---:|---:|---:|
| bnn_export | 8 | 2.552500793667 | 0.042481221713 | 2.534887032000 |
| bnn_export | 32 | 1.120514904778 | 0.032437644597 | 1.111829053000 |
| bnn_export | 64 | 0.699624213444 | 0.026647139383 | 0.694246864000 |
| lstm_s2 | 8 | 2.610159214444 | 0.045129987151 | 2.605319930000 |
| lstm_s2 | 32 | 1.137800883667 | 0.029544175110 | 1.123046453000 |
| lstm_s2 | 64 | 0.725510098000 | 0.021287159254 | 0.725314705000 |

Selected by the predeclared lowest mean rule: **64 threads for both cases**.

- bnn_export: process means 0.668920613333, 0.716718638667, 0.713233388333; raw3×3 repetitions remain in terminal.json.
- lstm_s2: process means 0.719377838000, 0.749190293333, 0.707962162667; raw3×3 repetitions remain in terminal.json.

The current cgroup reports0 newly throttled periods for8/32-thread processes,
and5–8 for64-thread processes. Those counters span the whole process including
parallel scratch allocation; no exact attribution to timed resident intervals
is claimed. The measured64-worker configuration remains fastest under the
actual allocation. It is not a claim about an unconstrained64-core server.
No quota adjustment, frequency normalization or optimistic extrapolation is
applied. Background host-service activity outside the monitored benchmark
classes is not represented as an exclusive physical-host reservation.

The historic isolated packed8 means2.842626751333/2.933218058s and prepared8
Xeon8462Y+ means3.654426308/3.669705272s remain distinct, hash-bound historical
cohorts. Their current source/binary/environment and process-level statistics
are audited in historical_audit.json. The fresh matched8-thread cohort uses
the new affinity/NUMA/passive-wait harness; its difference from old8 must not
be attributed solely to a packing or allocation optimization across sessions.
Native stock/STRICT is not treated as a same-algorithm resident baseline.

The old conditional200MHz L1 times would give CPU/model ratios
**1.934867× BNN /1.976355× LSTM** against these stronger measured CPUs,
not the old≈8× comparison. These are only comparisons against an assumed-clock
model. Parent's actual full-core fit, routed frequency, finite-model calibration,
updated memory service and output evidence determine any formal FPGA claim.
No FPGA win, GPU win/loss change, board time or extrapolated lower-clock cycle
result is asserted by this CPU subtask.

## Exact timing boundary and other scopes

The resident clock starts after full immutable input loading/validation and
scratch allocation, before runtime cost preload. Included: mandatory sample
label/proposal/pending/version/marked/seen/output reset; directory/free-list
initialization; all actual POP, FP32 whole-pair merge, waves, target output
writes, and worker completion. Research golden comparisons, SHA/archive I/O,
file export, descriptor construction, initial graph load and persisted-image
validation are excluded. Those necessary production setup portions belong in
E2 when actually required; research validation must not be silently charged
as production work. CPU/GPU/FPGA each complete all40 real jobs. GPU evidence
retains per-wave host completion reads/waits; no GPU run is restarted.

The unchanged descriptor construction already has one isolated observation
per case in historic construction_isolated_a; its exact source/input/output
receipt and stage times are reused in historical_audit.json. It is one
observation, not a3-process statistical cohort. CPU packing/verification/file
stages and GPU/control/resident timings must not be double-counted when forming
an E2 timeline. No board transfer is measured, no free across-build amortization
is granted, and native VPR Process remains its separate historical scope.

The new byte outputs are the same ALT results as before; transitive native/QoR
identity can therefore be reused under the unchanged import adapter. This does
not claim bitwise STRICT equivalence or a new native VPR run. Full hashes:

- BNN: `a8ca4003a3b015145635a3f776bb62a3aec1ec2121a1fbfc8712d2a2dc1c8c3f`
- LSTM: `6b2acd7718d880075d653b3b83f1fa3abb5161f6f346ed39c3aa1285160a95cf`

All CPU experiments are terminal. Only new software/ and software_a/ paths were
written. No historical sources/results were modified; no commit/push performed
by this subtask. Parent owns final source/evidence archive and publication.
