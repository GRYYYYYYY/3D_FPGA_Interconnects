# Lookahead mechanisms and native ALT CPU comparison

The author-review base is 8f3c1522f836c4a2b0104009fce67a76b640975c. The working branch is paper/dac2027-mechanism-ablation-20261118. The paper is in paper/dac2027_mechanism_ablation; the experiment plan, scripts and budgets are in accel/lookahead/native_alt_cpu_ablation_20261118.

## P0 publication

The independent P0 paper was compiled, checked, inspected on all seven pages, rebuilt from its anonymous archive, committed, pushed and verified against the full remote SHA **8a7f97603a826862c2e633f054d5fe903d5246a8** before P1 admission started. At this commit main.pdf has SHA256 c5de51ed73e24e4e751e79623dfb5e0e45274e86e7f6ab144e5d7d168ba2da8b; submission_source.zip has SHA256 baca7578ed9f98a1f86d89863f83f5eb42acf9ab7ac4f900db422980d8fde80d. The parent paper directory remains independently accessible.

P0 Figure 1 shows when a free worker can cross a group join and why successful same-bucket improvements require another wave. Table II connects the original BNN40 operation profiles with archived warm complete-batch measurements from R6 commit 480ba6d5cc2b9d73696a44315777c0e658d8a7b4.

| R6 measure | Shift 0 | Shift 20 |
|---|---:|---:|
| Sample waves | 19,691 | 2,161 |
| Maximum per sample | 627 | 59 |
| Eligible edges | 1,282,443,890 | 1,286,937,147 |
| Edge-weighted frontier, rounded | 16,061 | 106,780 |
| ALT CPU on 8 cores, seconds | 7.304299887 | 7.065944795 |
| ALT CUDA, seconds | 2.830302942 | 0.314170320 |

The paper recomputes three warm repetitions per independent process, then the median of three such process medians. The four configurations give CPU and GPU ratios of 1.033733× and 9.008817×. All 40 samples use the same bound original input. Complete CPU reference bytes agree across shifts, profiling references match those outputs, and the CUDA run records report complete C++ agreement in every batch. The historical worker recorded source, compiler/build commands and completion-time binary digests. Each invocation lacks an independent launch-time binary digest. Load and preparation precede the timer; reset, search, closure, output materialization, GPU readback and synchronization lie within it. Output validation follows it. The new native comparison retains its own timing bounds.

R6 source and object hashes, original measurements, independent profile summaries and input/output bindings are in the paper's evidence/r6_bnn40.json. Original full measurement/command/snapshot records are addressable at the bound R6 commit. The two underlying profile logs remain in the paper evidence; recompute.py and recompute_mechanism.py reproduce the figures/table entries.

From native main-table stage means, E2 is 13.70% of Pipeline Process on GEMM and 14.39% on BNN. Holding the remainder fixed gives zero-E2 estimates of 1.159× and 1.168× and replacement estimates of 1.110× and 1.110×. The measured within-repeat Process speedups average 1.102× and 1.098×. These estimates use only the pre-existing measurements at 30bc11372b173165c0b7bf2574b21c8fddaa8eff.

## P1 execution contract

The single task budget starts at 2026-11-17 23:27:26 UTC. P1 started 23:33:52 UTC at first resource admission. Its queue/admission deadline is 00:03:52 UTC and absolute end is 02:33:52 UTC on November 18. Beijing timestamps and full precision are in the budget files. Job job-baff5ebc-ed3d-48d0-a524-48a48436eed9 entered the allocation within the admission window. The first CreateJob request explicitly rejected a zero retention period without creating a job. The one recovery used the previously supported 60-second retention under the original clock.

The plan uses the unchanged native runner from 30bc113, all five original input hashes, predeclared map/capture digests, original libraries, shift20 and 40 samples. Three qualification processes precede each case. Nine formal processes per case rotate Pipeline/ALT CPU/ALT CUDA, ALT CPU/ALT CUDA/Pipeline and ALT CUDA/Pipeline/ALT CPU. Each main process performs native routing and is followed by independent original-VPR FULL/STA readback. New CPU/CUDA quality is compared against the new Pipeline in the same repeat. New paired performance uses only this allocation.

Shared storage for original records is results/native_alt_cpu_ablation_20261118/worker_a inside this worktree. The platform receipts are in the adjacent platform directory. analyze.py reads the completed worker records, retains raw seconds and calculates ratios only for complete cases. archive.py binds retained small records and large output artifacts.

## FPGA pause management

The start-of-task read-only check recorded the live group, process birth identities, stopped threads, fresh observer heartbeat, two controller locks and the original budget digest. The recovery entry is accel/lookahead/fpga_device_migration/pause_20261117/RESUME.md in the device-migration worktree. Publication and software job completion do not change the hardware pause policy.


## Completed allocation

The allocation used NVIDIA H100 80GB HBM3, eight physical cores [0, 1, 2, 3, 4, 5, 6, 7] on NUMA 0, with MPOL_BIND. Its GPU identity is GPU-aca86420-7228-71f7-21f5-ce4f5a1c9a6d.

Case | State | Qualification processes | Formal processes | Successful independent readbacks
---|---|---:|---:|---:
GEMM | COMPLETE | 3 | 9 | 12
BNN | COMPLETE | 3 | 9 | 12

Fresh formal processes run sequentially. The performance denominator and QoR control come from this allocation. The original Stock table stays on its original cohort.

Case / scope | Pipeline seconds | ALT CPU seconds | ALT CUDA seconds | Pipeline / ALT CPU | ALT CPU / ALT CUDA | Pipeline / ALT CUDA
---|---:|---:|---:|---:|---:|---:
GEMM / E2 | 42.664 ± 6.151 | 43.987 ± 2.428 | 9.422 ± 0.578 | 0.976 ± 0.183 | 4.690 ± 0.533 | 4.513 ± 0.403
GEMM / Process | 247.891 ± 18.033 | 254.704 ± 3.788 | 222.393 ± 4.913 | 0.973 ± 0.074 | 1.146 ± 0.042 | 1.115 ± 0.090
BNN / E2 | 19.309 ± 0.452 | 18.850 ± 0.540 | 4.354 ± 0.123 | 1.025 ± 0.007 | 4.331 ± 0.151 | 4.437 ± 0.156
BNN / Process | 102.236 ± 0.338 | 101.337 ± 0.856 | 87.244 ± 1.138 | 1.009 ± 0.006 | 1.162 ± 0.015 | 1.172 ± 0.016

Each entry gives mean and sample SD over three fresh processes or three direct within-repeat ratios. Raw measurements for every repeat follow.

Case | Repeat | Arm | E2 s | Process s | Independent readback s | CPD ns | Wirelength | Iterations | CPD vs Pipeline % | WL vs Pipeline %
---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:
gemm | 1 | pipeline | 35.5975 | 227.0696 | 155.5787 | 13.2667 | 4095178 | 15 | 0.0000 | 0.0000
gemm | 1 | alt_cpu | 45.8982 | 255.0357 | 186.9967 | 13.2667 | 4092614 | 16 | 0.0000 | -0.0626
gemm | 1 | alt_cuda | 8.7921 | 223.6123 | 172.7597 | 13.2667 | 4092614 | 16 | 0.0000 | -0.0626
gemm | 2 | alt_cpu | 41.2546 | 250.7606 | 177.6219 | 13.2667 | 4092614 | 16 | 0.0000 | -0.0626
gemm | 2 | alt_cuda | 9.9291 | 226.5823 | 174.8655 | 13.2667 | 4092614 | 16 | 0.0000 | -0.0626
gemm | 2 | pipeline | 46.8204 | 258.4602 | 175.2137 | 13.2667 | 4095178 | 15 | 0.0000 | 0.0000
gemm | 3 | alt_cuda | 9.5451 | 216.9855 | 172.2746 | 13.2667 | 4092614 | 16 | 0.0000 | -0.0626
gemm | 3 | pipeline | 45.5738 | 258.1443 | 174.6685 | 13.2667 | 4095178 | 15 | 0.0000 | 0.0000
gemm | 3 | alt_cpu | 44.8084 | 258.3156 | 176.9650 | 13.2667 | 4092614 | 16 | 0.0000 | -0.0626
bnn | 1 | pipeline | 18.7892 | 102.1418 | 67.0249 | 11.0943 | 1538209 | 19 | 0.0000 | 0.0000
bnn | 1 | alt_cpu | 18.2281 | 100.7159 | 68.7189 | 11.0943 | 1537866 | 19 | 0.0000 | -0.0223
bnn | 1 | alt_cuda | 4.3272 | 86.0266 | 65.8092 | 11.0943 | 1537866 | 19 | 0.0000 | -0.0223
bnn | 2 | alt_cpu | 19.1143 | 100.9824 | 66.7611 | 11.0943 | 1537866 | 19 | 0.0000 | -0.0223
bnn | 2 | alt_cuda | 4.2461 | 88.2805 | 66.6202 | 11.0943 | 1537866 | 19 | 0.0000 | -0.0223
bnn | 2 | pipeline | 19.6075 | 101.9557 | 67.4587 | 11.0943 | 1538209 | 19 | 0.0000 | 0.0000
bnn | 3 | alt_cuda | 4.4876 | 87.4250 | 66.1138 | 11.0943 | 1537866 | 19 | 0.0000 | -0.0223
bnn | 3 | pipeline | 19.5316 | 102.6110 | 67.1197 | 11.0943 | 1538209 | 19 | 0.0000 | 0.0000
bnn | 3 | alt_cpu | 19.2065 | 102.3137 | 66.5207 | 11.0943 | 1537866 | 19 | 0.0000 | -0.0223

The raw CSV also includes the qualification processes, map/route digests and per-run pass flags. Each accepted ALT map and capture matched its predeclared identity. The archive index binds original small records, review copies and large worker artifacts. The complete unmodified raw files remain on shared storage.
