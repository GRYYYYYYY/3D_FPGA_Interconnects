# Bounded CPU-primary software baseline

This directory owns only the CPU audit and thread sweep for base
`3c7f96e6037030949b729240977c2ced373843c6`. No FPGA or GPU experiment is launched.
Original software and historical results are read-only.

`cpu.cpp` is derived from the already qualified packed-descriptor CPU. The
whole-pair FP32 ALT algorithm and persisted8B descriptor/edge backing are
unchanged. The old16-thread command-line cap is removed in favor of the actual
OpenMP affinity limit. Scratch allocations are made by their bound workers
with MPOL_LOCAL, while graph/shared descriptor/edge allocations use
MPOL_INTERLEAVE over the selected sockets. Storage allocation is outside the
resident region; every mandatory per-sample state reset remains inside.
This new matched cohort therefore uses fresh8/32/64 measurements; the original
8-thread timings remain separately reused, not overwritten or reclassified.

`sweep.py` fixes8/32/64 threads before inspecting results, chooses one logical
CPU per physical core, pins8/32 to socket0 and64 across the two sockets, and
uses explicit OpenMP places plus passive waiting. The available physical-core
count is64, but the cgroup CPU bandwidth quota is55 CPU-time. All40 real jobs
are scheduled dynamically; at most40 sample solves can execute at once, even
with64 OpenMP workers. This limitation is the actual CPU implementation's
parallel organization, not an artificial serial CPU restriction.

One warmup plus three retained full batches run in each of three independent
processes per case/thread point, sequentially. Every repetition compares its
entire output against frozen ALT golden, outside the timed region. The final
binary output is hashed again by the runner. Reports retain individual values,
process means and process-level sample standard deviation; nine repetitions
are not nine independent processes. There is no small-n confidence-bound claim.
The best measured thread point is chosen separately per case by the mean of
three process means, with all candidate values retained.

The timer begins after immutable inputs are loaded and verified and after
scratch storage is allocated. It includes runtime cost preload, per-sample
label/proposal/pending/version/output/seen reset, directory initialization,
all actual POP/FP32/merge/wave/target work, final output memory writes and
parallel worker completion. File loads, packed construction, full persisted
image validation, research golden/SHA verification and file export are outside.
These are explicit RESIDENT_COMPLETE_BATCH_V2 boundaries, not an E2/Process
claim. No FPGA board transfer or launch time is invented.

The runner logs source/include/compiler/binary/input hashes, real commands,
worker CPU IDs, NUMA allocation maps, PID birth identity, cgroup counters and
observed active model/EDA/software competitors. A lock and live-executable
check reject duplicate runs; incomplete result paths are preserved for review.
It does not stop, restart or modify historical EDA/GPU jobs. Parent coordination
provides the quiet measurement window; checking the process list alone is not
a claim that the entire physical host is exclusively reserved.

`audit.py` verifies historic packed8 and prepared CPU receipts against the
base's descriptor archive and preserves the distinction between Xeon6530 and
8462Y+ platforms. Existing VPR/E2/Process measurements remain separately scoped.
The selected new result is the best measured **packed CPU in this bounded
configuration set under the current allocation**, not the strongest possible
algorithm, unlimited host CPU or native STRICT implementation.

Reproduction (new result directory/source freeze for changed code):

```sh
python3 accel/lookahead/fpga_cpu_primary/software/sweep.py
python3 accel/lookahead/fpga_cpu_primary/software/audit.py
```

The final software-only summary is `RESULTS.md`; receipts are under
`results/fpga_cpu_primary_20261115/software_a/`. Parent owns final FPGA
integration, archive, commit and push. Do not infer hardware acceleration from
these CPU results without the required full-core implementation/model evidence.
