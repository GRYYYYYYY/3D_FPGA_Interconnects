# V3 allocation A

Inspire stopped job `job-ff687cfa-843b-4fb0-9777-4a475a36d057` at 2026-11-18 13:21:45 UTC after 1,054 seconds of runtime. The reserved maximum was 24 hours and the protocol deadline was 2026-11-19 13:00 UTC. The scheduler placed one worker on qb-prod-gpu435. Its terminal events show the containers stopping. The initiating actor and cause are unspecified in these receipts.

| Workload | Qualification processes | Formal full processes | Formal Group / Flat controls |
|---|---|---:|---:|
| GEMM | Stock completed. Pipeline was interrupted before its output record. | 0 / 12 | 0 / 6 |
| BNN | Stock, STRICT Pipeline, ALT CPU and ALT CUDA completed. | 0 / 12 | 0 / 6 |
| LSTM | None started. | 0 / 12 | 0 / 6 |

There are zero eligible repeat pairs. The raw timing, paired statistics, stage breakdown and Amdahl files contain headers. The qualification receipts include diagnostic timers. The identical high-resolution wrapper and process boundary are specified for the formal runs. Qualification time and independent validation time are excluded from all timing tables.

## Equipment and input verification

The worker exposed a Xeon Platinum 8462Y+, CPU threads 0–7 mapped to eight different physical cores on socket 0, NUMA node 0. Its cgroup allowed ten CPUs and 200 GiB. Memory was bound to node 0. The H100 80GB HBM3 had UUID `GPU-9a0b024f-1672-8e02-3cae-ddf1760e07d7`, 81,559 MiB total and 81,090 MiB free at preflight. The eight cores used the performance governor. GPU clocks adapted under the inherited 700 W limit. The worker reported g++ 13.3.0 and CUDA 12.8.61. The VPR binaries identify GNU 11.4.0, Release and assertion level 2. The Stock source archive is bound to VTR 0b912334fdd83bb754b302146ac0d1ec9edc9a0e.

The topology counter found two layers in all three full XML inputs, each with a 40-context sampling plan. See topology.csv for nodes, edges, exact layer-counting convention totals and CHANZ inventory. The original BNN and GEMM Stock logs also identify 1,314 and 2,082 CHANZ nodes respectively with no fan-in. These input diagnostics remain visible alongside the final route-consistency results.

## Evidence index

| Files | Contents |
|---|---|
| environment.json, protocol.json, submission.json, allocation_stop.json | Device and host, affinity, memory policy, quotas, worker binding, allocation and termination |
| bindings.csv, build_provenance.json, timer_build.json | SHA256 bindings for original inputs, source, compiler/link inputs, executables and runtime libraries |
| coverage.csv, raw_timing.csv, seconds.csv, paired.csv, amdahl.csv | Planned, invoked and recorded cells, raw observations, repeat statistics and derived estimates |
| qor.csv, map_differences.json | Per-route original SHA256, CPD, WL, overuse, map and capture identities, Stock thresholds and independent checks |
| native_process_records.zip, verification.json | Commands, invocation and completion receipts, incomplete log, original and independent FULL/STA logs and timing reports, verification summary |
| motivation_raw.csv, timing-boundaries.md | Raw historical logs and the different denominators used for the two motivation percentages |
| fpga_pause.json | Read-only migration heartbeat at closeout |

All five retained routes passed independent FULL/STA readback with the original CPD and wirelength. The original routes had zero overuse. GEMM Stock had CPD 13.2667 ns and wirelength 4,095,331. See qor.csv for individual identities and BNN comparisons.

Independent validation uses the pinned original Stock executable to read each retained route on the editing host. Its host and scope are recorded in each readback receipt. The original route SHA256 is checked before and after readback. The off-worker checks supply no primary timing observations.

From the experiment directory, run `python3 closeout.py` followed by `python3 validate.py` against the retained run directory to reproduce the summary. The compressed archive includes the small process evidence and timing reports. The large input/route/capture files reside at the bound workspace paths.
