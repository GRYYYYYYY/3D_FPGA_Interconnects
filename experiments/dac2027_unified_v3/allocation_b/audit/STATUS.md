# Reservation B measured subset

Inspire recorded job_stopped at 2026-11-18 16:43:50 UTC after 10,922 seconds of job runtime. Instance events report container termination. The receipts do not identify the actor or underlying cause. The platform limit was 24 hours and the protocol deadline was 2026-11-19 13:00 UTC.

| Workload | Full processes | Group and Flat controls | Valid complete repeat sets |
|---|---:|---:|---|
| GEMM | 12 / 12 | 6 / 6 | All six arms |
| BNN | 12 / 12 | 6 / 6 | All six arms |
| LSTM | 0 / 12 | 0 / 6 | None |

One worker executed all 36 formal processes, with no formal interval overlaps. Each of the two measured workloads has 3 fresh processes per arm. The 24 full processes each supplied both E2 and Process. The 12 construction controls contributed E2. The CSVs preserve all individual nanosecond records, seconds, sample SDs and within-repeat ratios. No qualification or off-worker time enters these statistics.

## Qualification and scope

All 12 qualification processes are recorded in qualification.csv. All three Stock wire maps agree with the respective STRICT maps, and all complete ALT CPU/CUDA sample captures agree. The LSTM Stock qualification emitted the expected wire map, then exited with signal 11 during routing. It yielded no original route for a Stock-relative CPD/WL comparison. LSTM Pipeline and both ALT backends produced zero-overuse routes with successful independent FULL/STA. The existing worker queued the remaining LSTM formal cells after the initial readbacks. The reservation ended first. Its separate original-binary LSTM diagnostic also remained unexecuted. These records establish map agreement on LSTM and leave the cause of its Stock routing failure unresolved.

All formal GEMM and BNN candidates met the one-sided +5% CPD/WL limits relative to their repeat-matched Stock route. CPD was unchanged. Signed wirelength changes ranged from −0.083% to −0.004% on GEMM and +0.068% to +0.091% on BNN. The decoded ALT maps changed 50,789, 24,434 and 23,111 congestion words on GEMM, BNN and LSTM, respectively. All delay words and missing-state masks agreed. The XML topology for all three graphs shows two layers.

## Evidence

The environment and protocol receipts in this directory identify the worker, eight physical cores, NUMA binding, H100 UUID, initial free memory, quotas, governor settings, compiler, CUDA and executable hashes. The input manifest, source and binary SHA256 bindings, build provenance and topology counts are in the parent experiment and audit directories. The Stock baseline is VTR 0b912334fdd8, Release, assertion level 2. The worker verified bindings before its first invocation. The historical motivation audit and the new matched GEMM breakdown are in timing-boundaries.md.

The original worker completed 45 independent route readbacks. The two remaining checks on the original GEMM repeat-2 routes, Pipeline and Stock, both passed on the editing host after termination. All 47 emitted routes now have passing independent FULL/STA receipts. The interrupted on-worker readback log is retained. The original route SHA256, CPD, WL, zero overuse, FULL and readback status for each route are in qor.csv. The compressed process archive includes commands, process logs, readback receipts and STA reports.

To reproduce the result from the shared run directory, set V3_ALLOCATION=b in the parent experiment directory and run closeout.py followed by validate.py. All formal timing remains bound to this reservation. The separate reservation A evidence and complete fallback manuscript remain archived.
