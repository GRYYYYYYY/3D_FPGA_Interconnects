# Lookahead acceleration: round four

Base: `96629a57511080a95c4d5e5050365fc2ada0fb4c`. Independent branch:
`accel/lookahead-round4-20261108`; no merge into main. Experiment root:
`results/lookahead_accel_round4_20261108T182500Z`.

The independent on-chip full-search and early-stop backends are implemented and
verified with one and four engines. Runtime graph loading, exact maps and warm
search without external graph traffic pass RTL verification. The four-engine
early kernel remains 7.32–9.96× slower than the best measured same-algorithm CPU
on the three complete 3D inputs, although its RTL-derived time beats basic CUDA.
The objective of FPGA superiority over all software baselines is **not met**.

All FPGA times below are functional RTL cycles converted at **125 MHz**, verified
by one fixed timing recheck of each unchanged routed netlist. Original 200 MHz
implementations fail setup timing and are not timed at that frequency. This is
constrained internal OOC timing, **not board measurement, system AXI timing or
C simulation wall time**. No maximum achievable frequency is inferred.

## Scope and modes

The new backend is independent of all older full-search/cache implementations.
`STRICT_FULL_FLOOD` retains complete search, exact libstdc++ heap ordering and
statistics. `MAP_EQUIVALENT_EARLY_STOP` is a separately named mode preserving the
full output map, including congestion and NaN sentinels, in its admitted numeric
domain. It does not preserve suffix operations, final scratch or suffix error
timing. The original full modes have not been redefined.

Targets are deduplicated from all input IPIN/cell pairs, including unreachable
targets; preparation uses no golden or preliminary reachability search. Output
NaNs act as unseen bits. State/output reset and leftover queue reset are inside
E1. Empty targets still perform the contracted reset; unreachable targets cause
heap exhaustion. The first legal callback already has the final minimum delay,
and strictly-smaller recording means equal-delay callbacks cannot replace its
congestion.

Eligible costs must be nonnegative finite normal FP32 or positive zero. CPU and
CUDA input-only admission proves a conservative no-overflow bound; hardware
uses an exponent bound of 240 at its fixed capacity. All additions remain
sequential RN FP32 with contraction disabled. Heap comparisons use unsigned
FP32 bit patterns only in this admitted domain. Queue capacity is E+1.

## Architecture and input loading

Runtime capacity is `N<=4096, E<=16384, J<=32, C<=128, K<=64`. These are generic
limits, not hardcoded input topology. The search function has no external-memory
interface or conditional miss path. Complete 96-bit heap entries occupy even/odd
sibling banks; labels, CSR, nodes, costs, cell mappings and compact output reside
in RAM. Pop preserves down-then-up ordering and chooses the right equal child.
The heap test checks the entire array arrangement, not just the returned delay.

Commands separately load the static image, execute warm, or load and execute.
A failed load invalidates the previous image. Warm shape mismatch is rejected;
callers must explicitly reload changed contents even if dimensions are equal.
The testbench poisons all external costs with NaNs during warm calls and changes
graphs in one RTL simulation, ensuring runtime loading and image reuse are real.

The single and four-engine candidates share the search implementation and
capacity constants. Each engine has private graph/workspace RAM. Four-engine
assignment is static round-robin by original qid, and writeout retains qid order.
This is not a ready-task scheduler. No samples are duplicated to inflate J.
Graph replicas and their load cost count in the resource and first-call results.

Three separate FPGA ranges are recorded: `load_static_to_onchip`, warm E1
(reset, search, output initialization/writeout and drain), and first call from
device memory (load plus this E1). Functional AESL AXI is a functional simulation
model, not a zero-latency algorithm lower bound or calibrated U280 HBM.

## Inputs and correctness

| Complete native input | N | E | J | Map cells per sample |
|---|---:|---:|---:|---:|
| 3×3, W8, two layers | 654 | 1,570 | 8 | 18 |
| 4×4, W8, two layers | 1,592 | 4,176 | 12 | 32 |
| 5×5, W8, two layers, held out | 2,862 | 7,922 | 12 | 50 |

The third graph was selected before hardware measurements. All graphs come from
the project's Hecate architecture and native global sample list, without graph
truncation, layer partitioning or sample filtering. The new graph's complete
native wire map also matches the original VPR binary. That run is correctness
evidence; its routing exit status does not provide an E1 timing baseline.

| Input | Full cross-edge visits / pushes | Early cross-edge visits / pushes |
|---|---:|---:|
| 3×3 | 2,304 / 1,134 | 712 / 604 |
| 4×4 | 11,232 / 4,014 | 4,992 / 2,754 |
| 5×5 | 20,736 / 5,802 | 11,962 / 5,306 |

These are instrumented logical counts, not hardware cycles. All map bits match.
The native 3×3 list includes two empty-target samples; both are retained.

C++ full/early maps pass 1,533 checks covering equal delays, shared cells,
unreachable/empty targets, zero cycles, duplicate edges, SINK edge order,
repeated scratch reuse and numeric admission. Hardware host verification also
passes 509 corner/random graphs × four API transactions in each mode, with full statistics
checked against the C++ reference. CTest passes all 19 old/new tests. Runtime
admission tests cover oversize inputs, malformed CSR/IDs/cells/costs, invalidated
images, shape changes, shrinking graphs, zero jobs and empty targets.

All native tseng (8) and BNN (40) samples pass the C++ map differential:

| Input | Full pops | Early pops | Full edge visits | Early edge visits |
|---|---:|---:|---:|---:|
| tseng | 1,545,152 | 1,531,278 | 6,048,704 | 6,001,551 |
| BNN | 272,831,946 | 272,531,146 | 1,328,143,040 | 1,327,099,655 |

The large-input work reductions are much smaller than the small 3D reductions.
They do not establish a runtime gain; the separate CPU/GPU measurements do.

## Measurement protocol

CPU and basic CUDA are run sequentially on one H100 worker per cohort, with
eight distinct physical CPU cores on one NUMA node. Small inputs test CPU
workers 1/2/4/8 and one CUDA CTA per real sample; every CTA has 128 threads.
Five fresh processes each execute one cold E1 plus five warm E1 calls. The large
cohort uses CPU8 and CUDA J CTAs with three fresh processes and three warm calls
per process. Full and early configurations are shuffled with a fixed seed.

Resident allocation/upload and input-only target preparation are separately
reported. Every timed call resets its own state/output, completes the entire
native sample batch and verifies all golden map bits outside timing. CPU/GPU
operation totals must agree for the same algorithm and input. GPU uses actual
CUDA kernels and events; there is no CPU fallback. It is a basic GPU baseline.
The estimator is the median of fresh-process warm medians, with process-median
minimum/maximum retained. Cold values are fresh-process first-call medians.

HLS uses frozen source/input hashes, classic Vitis HLS/Vivado 2022.2 and U280.
The heap loops achieve II=2 in the schedule, but a 7.169 ns HLS timing estimate
flags a RAM-read/compare/select/write path. This is not an achieved-II or AXI
stall violation. The final clock must come from implementation. RAM primitive
counts are taken from the implemented design rather than the HLS area estimate.
The generated even heap bank retains two ports, while the odd bank is simplified
to one read/write port; dependent accesses remain scheduled, with no false
dependence suppression or unlimited-port assumption. Actual routed critical
paths differ: full single is a cascaded cell-map RAM read to output-RAM enable
(5.128 ns data delay), while early single is an even-to-odd heap RAM path
(5.065 ns data delay). These are routed-path observations, not deductions from
the HLS estimated critical path.

## Measured CPU/GPU results

All times below are microseconds. Each entry is **cold first E1 / warm E1**.
CPU uses the best tested worker count separately for each mode: 8/full and
2/early on 3×3, 8/8 on the other inputs. Thus best-configuration CPU full/early
ratios are not mislabeled as a fixed-worker algorithm ablation.

| Input | CPU full | CPU early | Basic CUDA full | Basic CUDA early |
|---|---:|---:|---:|---:|
| 3×3 | 268.722 / 72.908 | 95.926 / 25.920 | 74,348.930 / 923.808 | 73,168.221 / 357.312 |
| 4×4 | 501.743 / 233.112 | 509.856 / 126.522 | 76,683.708 / 2,444.640 | 74,315.071 / 1,632.320 |
| 5×5 | 561.303 / 373.918 | 782.079 / 211.585 | 77,623.138 / 4,427.520 | 76,252.930 / 2,901.952 |
| tseng | 40,139.881 / 36,624.166 | 38,636.523 / 36,550.530 | 713,802.551 / 650,750.366 | 698,062.622 / 634,528.015 |
| BNN | 9,137,473.287 / 9,246,607.621 | 9,268,716.515 / 9,208,045.313 | 36,317,636.719 / 36,250,781.250 | 35,940,816.406 / 35,640,054.688 |

The small worker is Intel Xeon Platinum 8462Y+ with NVIDIA H100 80GB HBM3,
CUDA 12.8 and driver 570.124.06. Affinity, NUMA, cgroup quota, compiler versions,
commands, source/input hashes and all individual observations are archived.
This is controlled affinity, not proof of exclusive physical CPU ownership.

CUDA cold E1 includes first-kernel runtime/lazy-loading gaps between the two
CUDA events; its approximately 70 ms startup on small inputs is not steady
kernel work. FPGA first-call-from-device-memory excludes host driver/module
startup. These cold ranges are documented independently, not used to manufacture
an end-to-end first-call speedup. Warm E1 is the main matched comparison.

At fixed CPU8, full→early warm ratios are 2.645×, 1.842× and 1.767× on the
three 3D inputs. Fixed basic CUDA ratios are 2.585×, 1.498× and 1.526×.
Large-input ratios are CPU 1.002× / GPU 1.026× for tseng and CPU 1.004× /
GPU 1.017× for BNN. These small differences are descriptive medians; the
process-median ranges remain in JSON and no statistical-significance or general
large-graph acceleration claim is made.

Preparation is not free. For the selected early configurations, input-only
admission/target preparation and total resident preparation are listed below,
again in microseconds. Total GPU preparation includes runtime/context setup and
allocation/upload; it is not a matched FPGA host-service range.

| Input | CPU targets / total preparation | GPU host targets / total preparation |
|---|---:|---:|
| 3×3 | 7.020 / 11.778 | 8.771 / 399,708.560 |
| 4×4 | 17.932 / 50.110 | 21.552 / 408,805.327 |
| 5×5 | 30.443 / 81.710 | 34.416 / 403,527.696 |
| tseng | 670.650 / 1,976.628 | 678.572 / 415,251.456 |
| BNN | 266,435.486 / 338,038.694 | 220,109.265 / 766,344.608 |

FPGA target construction is included in its measured static-load cycles;
per-call output/seen reset stays inside warm E1 on every backend.

## Verified RTL cycle observations

All four modes pass twelve transactions: load-and-run, warm, repeated warm and
load-only on each runtime-loaded input. The complete native maps and the
mode-specific reference statistics match. The following table is in cycles,
independent of whether the requested 200 MHz clock closes.

| Input | Full single | Full four | Early single | Early four |
|---|---:|---:|---:|---:|
| 3×3 warm E1 | 181,395 | 60,211 | 59,625 | 23,721 |
| 4×4 warm E1 | 893,427 | 230,692 | 371,776 | 123,821 |
| 5×5 warm E1 | 1,630,309 | 415,461 | 830,104 | 263,392 |

Compared to the frozen external-full four-engine functional RTL, the first two
on-chip-full cycle gains are 6.952× and 7.802×. This is a residence/architecture
comparison under functional AXI, not a physical HBM limit or an algorithm
lower-bound claim. Single→four full cycle gains are 3.013×, 3.873× and 3.924×.
Early gains must additionally be compared with the faster early software.

## Implemented timing, resources and matched time

The fixed 125 MHz check changes only the clock constraint of each routed DCP.
All four designs pass setup, hold and pulse checks; no internal endpoint lacks
a constraint. External input/output delays remain unconstrained (single:
513/751 ports; four: 1,309/2,884), and OOC `HD.CLK_SRC` is unset. Integrated clock
insertion/skew, AXI shell timing and board memory behavior remain unverified.
Resources below are post-route, with BRAM expressed in 18 Kb equivalents.

| Kernel | Original 200 MHz setup slack (ns) | 125 MHz setup / hold slack (ns) | BRAM18 | LUT | FF | DSP |
|---|---:|---:|---:|---:|---:|---:|
| full_1 | -0.543 | 2.457 / 0.020 | 364 | 11,605 | 12,096 | 7 |
| full_4 | -0.905 | 2.095 / 0.019 | 1,000 | 45,432 | 48,237 | 23 |
| early_1 | -0.388 | 2.612 / 0.021 | 360 | 12,074 | 12,781 | 7 |
| early_4 | -1.095 | 1.905 / 0.019 | 1,000 | 47,812 | 50,986 | 23 |

All designs use zero URAM. Warm graph AXI reads and writes are zero. The RTL
monitor proves all output requests receive their B responses before completion;
writeout is 1,536 / 3,648 / 5,376 bytes for the three complete batches, including
all maps and statistics. External adapters have burst length 16 and 16 read/write
outstanding slots per bundle; those settings do not imply integrated HBM banks
or available physical bandwidth. Static graph loading and output flushing use
AXI; the search hot loop uses local memories only.

The following times are microseconds. FPGA columns are **RTL cycles / 125 MHz**,
with functional AESL AXI; CPU/GPU columns are measured warm E1. First FPGA call
starts with the image already in device memory, and includes runtime loading.

| Input | FPGA early4 load only | FPGA early4 first | FPGA full4 warm | FPGA early4 warm | CPU early warm | GPU early warm |
|---|---:|---:|---:|---:|---:|---:|
| 3×3 | 67.456 | 258.712 | 481.688 | 189.768 | 25.920 | 357.312 |
| 4×4 | 188.696 | 1,178.712 | 1,845.536 | 990.568 | 126.522 | 1,632.320 |
| 5×5 | 343.136 | 2,449.720 | 3,323.688 | 2,107.136 | 211.585 | 2,901.952 |

First-call cycles are observed transactions, not the arithmetic sum of separate
warm and load-only calls. Control setup differs between these commands.

## Gain decomposition and expansion decision

Architecture gains compare the frozen external-full four-engine RTL to on-chip
full four-engine RTL, preserving the input and algorithm. At the respectively
verified 200 and 125 MHz clocks, time gains are **4.345× / 4.876×** on 3×3/4×4;
the larger 6.952× / 7.802× numbers above are cycle gains only. The change also
replaces external memory accesses with local RAM; it is not a cache-size ablation.

Algorithm gains are reported independently at fixed CPU/GPU configurations above.
At fixed on-chip four engines and 125 MHz, full→early gains are **2.538× / 1.863× /
1.577×**. Combining architecture and algorithm gives **11.029× / 9.085×** over
external-full four-engine RTL on the first two graphs. This is a kernel E1
comparison, not native lookahead E2.

| Input | Same-algorithm CPU / FPGA early4 | Same-algorithm GPU / FPGA early4 | CPU full / FPGA early4, combined software+hardware E1 | Early4 cycles | Budget to strictly beat best early software |
|---|---:|---:|---:|---:|---:|
| 3×3 | 0.137× | 1.883× | 0.384× | 23,721 | 3,239 |
| 4×4 | 0.128× | 1.648× | 0.235× | 123,821 | 15,815 |
| 5×5 | 0.100× | 1.377× | 0.177× | 263,392 | 26,448 |

Ratios below one mean FPGA is slower. Both the same-algorithm comparison and the
full-software→early-hardware comparison fail to beat CPU. Preparation is shown
separately above; complete host/FPGA service or native E2 gains are unmeasured.

RTL counters expose load imbalance rather than assuming perfect concurrency:

| Early4 input | Engine search cycles (0, 1, 2, 3) | Cycles with at least two searches active |
|---|---|---:|
| 3×3 | 11,030, 1,316, 22,914, 23,422 | 22,914 |
| 4×4 | 117,496, 65,559, 123,212, 63,346 | 117,496 |
| 5×5 | 262,552, 149,427, 246,651, 168,339 | 246,651 |

Heap loops achieve II=2, but one pop traverses multiple dependent levels: on the
single engine, 3×3 full has 3,242 pops totaling 81,516 pop-active cycles (25.14
cycles/pop); early has 583 pops totaling 14,901 cycles (25.56 cycles/pop).
On-chip storage removes external graph stalls but not this sequential work.

A conditional scheduling bound divides the observed total engine search work
by engine count. It assumes unchanged per-task datapath work, perfect balancing
and zero dispatch/output overhead. **These are model bounds, not RTL results
from an implemented dynamic scheduler.**

| Input | Perfect four-engine lower bound | Perfect J-engine lower bound | Actual J | Software cycle budget |
|---|---:|---:|---:|---:|
| 3×3 | 14,671 | 7,336 | 8 | 3,239 |
| 4×4 | 92,404 | 30,802 | 12 | 15,815 |
| 5×5 | 206,743 | 68,915 | 12 | 26,448 |

Even the optimistic one-engine-per-real-sample bound exceeds the CPU budget on
all three inputs. This supports deferring ready-task scheduling, 8/16 engines,
frequency/capacity sweeps and large-graph FPGA/E2 work for this datapath. Static
round-robin is the implemented four-engine policy; no dynamic scheduler result
is claimed. A future candidate must first reduce dependent search/heap work per
sample while retaining the verified map contract, then pass the updated cycle
budget on the held-out graph. The small tseng/BNN early-stop reductions also
provide no evidence for assuming a large-graph algorithm speedup.

[Software measurement plot](../results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/plots/software_algorithms.pdf)
and [RTL cycles and CPU budget plot](../results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/plots/hardware_cycles_and_budget.pdf)
are available as PDF, SVG and PNG with explicit evidence labels.

## Evidence and boundaries

The [final machine-readable report](../results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/report_final.json),
[raw evidence index](../results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/index.json),
[source/API contract](../accel/lookahead/round4/README.md) and
[validation receipt](../results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/final_validation.json)
bind sources, inputs, outputs and timing. All three prior archives (1,898 files)
and the untracked guidance package passed preservation checks. The package
remains untracked. There are 996 timed CPU/GPU calls across 174 fresh processes;
both remote jobs finished successfully.

Initial monitor postprocessing failed on scalar whitespace and, in one run,
binary decoding after simulation completion. Those receipts/logs remain in the
archive. Independent `verification_v2.json` receipts compare all memory bytes,
scalar values and transaction markers against the original passing RTL runs;
only scalar whitespace is normalized. They also confirm unchanged cycle counts.
No failing simulation has been relabeled or replaced with C simulation time.

B0/B1 native same-range E1 and complete native lookahead E2 remain distinct
measurements; historical E2 is never divided by a new FPGA E1. Capacity-exceeding
graphs are rejected by this on-chip API. No winning range or large-graph FPGA
speedup is inferred from small-graph output equivalence or operation counts.

## Reproduction

Use a fresh output directory for every run. The two older complete 3D inputs
are in the third-round evidence archive; the held-out input is in this round's
archive. Paths in frozen reports preserve the original execution location;
reproduction commands below use paths available in a repository checkout.

```bash
cmake -S accel/lookahead -B results/r4_reproduce_cpu -DCMAKE_BUILD_TYPE=Release
cmake --build results/r4_reproduce_cpu -j 8
ctest --test-dir results/r4_reproduce_cpu --output-on-failure
```

To include the wide-heap and runtime admission host tests, additionally configure
`-DLA_HLS_INCLUDE=/path/to/Vitis_HLS/2022.2/include`. `-DLA_CUDA=ON` requires an
actual CUDA compiler/device. CMake tests establish functionality; official timing
cohorts use the explicit `-O2` commands frozen by `la_accel_round4_gpu_job.py`.

```bash
python3 scripts/la_accel_hls4.py \
  --output results/r4_reproduce_full4 --engines 4 --early 0 \
  --workload results/lookahead_accel_round3_20261108T141500Z/evidence_snapshot/native_d3_w8/workload.bin \
  --workload results/lookahead_accel_round3_20261108T141500Z/evidence_snapshot/native_d4_w8/workload.bin \
  --workload results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/native_d5_w8/workload.bin
python3 scripts/la_accel_hls4.py \
  --output results/r4_reproduce_full4 --resume --phases impl
python3 scripts/la_accel_monitor4.py \
  --hls results/r4_reproduce_full4 --output results/r4_reproduce_full4_monitor
```

Use `--engines 1` and/or `--early 1` with separate output names for the other
three controls. The script deliberately refuses to overwrite existing phase
logs. Classic 2022.2 flows are used because the installed Ross unified-IDE
examples target newer Vitis APIs. The original 200 MHz implementation and the
single fixed 125 MHz routed-netlist timing recheck remain separate artifacts.
The latter's Tcl, generated constraints, raw timing/resource/route reports and
original/rechecked DCP hashes are retained; large DCP binaries stay local.

`la_accel_round4_gpu_job.py` must run in the CUDA worker environment. It freezes
source, selects eight physical cores on one NUMA node, compiles both backends,
shuffles configurations, checks outputs/counts and writes every observation.
Pass the three complete workloads for the small cohort; pass all-sample tseng
and BNN with `--large` for the large cohort. Large input binaries are not copied
into Git; their existing export paths and SHA-256 hashes are retained. The
small complete inputs and all 509 semantic fixtures are included in the archive.

`la_accel_round4_report.py`, `la_accel_round4_validate.py` and
`la_accel_round4_archive.py` derive comparisons and check the evidence chain.
Plot with `.venv-report/bin/python scripts/la_accel_round4_plot.py`, using the
final report and a fresh output directory. PDF, SVG and PNG artifacts are
generated from the same machine-readable results.
