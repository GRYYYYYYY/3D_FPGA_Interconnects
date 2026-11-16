# CPU-primary L1 complete-core closure

Earlier frozen checkpoint: [2026-11-15 completed and in-flight experiments](lookahead_fpga_cpu_primary_progress_20261115.md). It records the 21:00:20 UTC observation separately from the subsequent qualification evidence in this report.

Status: implementation and verification in progress. This file is updated as
terminal evidence arrives; it is not a claim of completed FPGA acceleration.

The selected RTL is the candidate payload-wordmux revision frozen as31 sources
in `full_synth_f_wordmux`. Its three-seed local comparison passed49,693 edges.
The complete52-sample/11-rejection suite also passed: full outputs, total
cycles,19 phase totals,3772 intervals and72917 requests/returns match model_g
exactly. `model_calibration_g_wordmux_a/calibration_reuse_contract.json` binds
this source to the reverified160 existing model samples without rerunning them.
Default5ns full-core synthesis completed at21:03:34UTC on2026-11-15.
Its actual global footprint is1,244,096 LUTs (95.43%),749,617 FF,1,148 BRAM36
equivalents,640 URAM and0 DSP. It is below the bare-device LUT capacity by
59,584. Terminal synthesis source/diagnostic collection is complete. Standard opt
has produced1,241,143 LUTs (95.20%),749,073 FF and unchanged BRAM/URAM/DSP
counts. Opt-only terminal reports and DCP are verified. Full-core placement, physical
optimization and route were launched at23:54:12UTC from that DCP. Placement
completed, with1,233,715 LUTs (94.63%) and749,174 FF in the actual post-place
report. BRAM/URAM/DSP counts remain unchanged. Post-place report collection
is complete. Standard physical optimization completed without changing cells
or improving WNS. The original routing attempt terminated with Route35-3 global
congestion level7 on2026-11-16 at07:50:23UTC. Its error checkpoint reports the
same1,233,715 LUTs and749,174 FF, with unchanged BRAM/URAM/DSP counts, but
5,809,714 node overlaps make routing illegal despite a zero failed-net summary.
One independent SSI_SpreadSLLs implementation from the same unplaced post-opt
DCP started at10:53:05UTC; original synthesis/opt/physical results are preserved.
Routed clock and complete physical closure remain unqualified, including the
external interface context gap below.

The preceding dispatcher revision e completed synthesis and standard opt_design.
It still required1,351,028 LUTs (103.63%),47,348 above U280 capacity, and did not
enter placement/route. Its actual resource, unplaced timing and OOC reset-buffer
warning are preserved below. That result motivated the single bounded wordmux
followup. The f synthesis result is109,826 LUTs below e under the same
tool/part/constraint/synthesis options. That is a measured total-core mapping
difference, not a guaranteed timing improvement or a hierarchy-level attribution.

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
memory sensitivity point. All31 selected DUT source hashes match the f synthesis freeze.
Full-capacity16K-cycle PV initialization is charged on every sample; it accounts
for83.32%/73.11% of the small graphs, so their elapsed cycles are not scaled to
large workloads. `fixtures_wordmux_source_a/verification.json` and both wordmux run directories
bind the selected functional result and complete event/phase/request-kind traces. Model calibration at this test service point is complete with the declared
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
5ns test clock and the same31-file selected DUT closure. These are observed
exact matches on the declared test suite, not a formal equivalence proof for
all graphs. Full-core routed-clock qualification remains separate.

A separate read-only audit also verifies all3,772 ordered phase intervals
across402 waves and all72,917 logical return cycles/source/kind/ID/generation
tuples, including matched-request addresses. It uses each RTL sample's actual
start/end and removes only the52 recorded zero-length model-constructor IDLE
intervals. No replay or fitted offset is used. RTL return traces do not contain
payload/address fields; payload equality is not falsely claimed from that trace.
See `model_calibration_g_phase_return_a/terminal.json`.

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

The selected f synthesis has31 matching frozen/current sources and actual
1,244,096 LUTs (956,040 logic +288,056 memory),749,617 FF,1,148 BRAM36
equivalents,640 URAM and0 DSP. The original run ended at21:03:34UTC;
its child PID/start identity is no longer present, and the project reports
`synth_design Complete!`/100%. It was never reset or relaunched. The stable
687,584,098-byte terminal DCP SHA-256 is
`3f2fb57724e3859c0c6ec501c69fa6b54189ebe1a9f363df23dff097fb805989`.
The31-file binding SHA-256 is
`87f2d59e5b2ed7b3ed49a035afdaab6f8db0ce26cb86d0f3a4a9f0a00ae1d6f1`.
Terminal reports and review are in `full_synth_f_wordmux/final_synthesis_review`.

Under the same synthesis flow as e, f reduces the global LUT count by109,826.
The rebuilt candidate hierarchy changes from249,583 to139,455 LUTs, including
a lane-FIFO scope decrease of167,130 and route scope increase of57,067. These
are mapped hierarchy accounting changes, including surrounding mux logic;
they do not mean that actual FIFO capacity changed. Summing child/self scopes
is not equivalent to the adjusted global physical LUT count.

Pure-synthesis, unplaced f timing is WNS−6.173ns, WHS−0.091ns and WPWS1.8ns.
The worst emitted setup path goes from bank29 completion payload cookie bit283
to the dispatcher error register:11.055ns data delay,48 logic levels, of which
8.607ns is estimated routing. Three of the20 emitted max paths are external
configuration-to-state-enable paths. DRC has zero violations; this does not
qualify a clock. The synthesis netlist had no internal BUFG/MMCM/PLL and lacked
`HD.CLK_SRC` on `clk`. All1,238,201 sequential clock pins, the `core_clock`
associated set, and the direct leaf clock-pin set of the `clk` net were compared
by complete sorted names and are identical, not merely equal in count.

The new implementation-only hook checks this actual connectivity, then declares
external OOC core-clock source `BUFGCE_X0Y144` on `clk`. It keeps5ns period,
original I/O delays and uncertainty, and adds no reset clock, timing exception,
boundary constant or severity waiver. Control BUFGs are classified by their
actual output loads separately; `IS_CLOCK` matches are clock-like pins, not a
proof that every matched pin is sequential. Post-opt must recheck actual
`clk` context. The existing e constraint already declared this core-clock
source; e's later reset-BUFG warning remains a separate historical finding.
The frozen new hook passed a40.212s read-only test on f. Two slower auxiliary
clock queries were interrupted and retained as tool-query diagnostics; the
synthesis and implementation runs were not interrupted by those actions.

Raw synthesis has8,658 WARNING messages, no ERROR/CRITICAL WARNING, no latches
and no `Synth8-326`. Manual source review retains142 unresolved anonymous
constant warnings. A bounded optimized-netlist alias lookup found none of
those aliases; absence is not evidence of dead statistics, padding or harmless
removal. No waiver or universal formal-equivalence claim is made. Actual
post-opt and placed/routed reports remain required for physical qualification.

Standard f opt_design completed its optimization body in509 seconds. Its
actual global report uses1,241,143 LUTs (953,343 logic +287,800 memory),749,073
FF,1,148 BRAM36 equivalents,640 URAM,0 DSP and1 BUFGCE. LUT headroom is62,537;
this is95.20% of bare U280 capacity, not a placement/routing guarantee. The
post-opt unplaced WNS is−6.165ns, WHS−0.091ns and WPWS1.8ns, with the same
48-level bank29 completion-to-dispatcher-error worst setup path. The complete
opt-only run ended at23:51:48UTC. Its402,895,145-byte DCP SHA-256 is
`3781ee752bae928c4993e5f148247f9b118b85f97d20f452e861c00cb4779ada`.
Both end markers and the original child exit are verified. The project stopped
normally at `Not started place_design`/40%. Global and vendor DRC both report
zero violations; coverage checks report no missing clocks/delays or loops.
The same implementation resumed at23:54:12UTC. Its generated script opens
this opt DCP directly, then runs place, physical optimization and route; it
does not rerun synthesis, initialization or opt. See `physical_gate.json`,
`post_opt_terminal_a/terminal.json` and `physical_a/process_birth.json` under
`full_synth_f_wordmux`.

All1,237,401 post-opt sequential clock-pin names still exactly equal both the
`core_clock` associated set and the direct `clk` leaf set. Core `HD.CLK_SRC`
remains `BUFGCE_X0Y144`. The optimizer added only
`dispatch/core_reset_BUFG_inst`:99,093 input loads and zero clock-like loads,
with I from `dispatch/core_reset`, CE tied high, and O driving control paths.
The remaining `Timing38-242` names external reset, not the core `clk`.
Twenty max and20 min paths through this buffer are explicitly reported;
their worst slacks are+0.866ns and+1.390ns respectively, still unplaced.
The warning is retained without an invented reset clock or waiver. This
clock-context evidence supports the actual physical verification launched after
all opt terminal reports and checkpoint were collected; it does not qualify
200MHz, route completion or board deployment.

The actual f placer completed placement on2026-11-16. At the earlier observation in
`physical_a/placement_observation_a`, it reports21,589 of23,040 SLLs required
across the SLR1/SLR2 boundary (93.70%, `Place30-356`). Vivado describes that crossing
as routable but warns of possible performance impact. This is a real physical
connectivity warning, not an observed routing failure or a routed frequency.
The placement/route job remains active; no revision has been selected from
this warning alone. The live log is cumulative: its retained opt prefix is
byte-identical to the terminal opt snapshot; this observation captures only
the new physical continuation block.

The subsequent `post_place/utilization.rpt` reports1,233,715 LUTs
(946,587 logic+287,128 memory),749,174 FF,1,148 BRAM36 equivalents,640 URAM,
0 DSP and1 BUFGCE. SLR0/1/2 CLB site occupation is99.86/99.99/99.95%;
SLR1 LUT occupation is98.24%. Actual post-place SLL usage is21,816/23,040
(94.69%) across SLR1/SLR2 and19,723/23,040 (85.60%) across SLR0/SLR1.
These boundary totals include both directions and differ from the earlier
placer estimate. The report shows no TX/RX SLL registers used. `Place46-14`
warns that the design is highly congested and may have difficulty routing.
The internal post-placement timing estimate was WNS−20.657ns/TNS−4,535,293.207ns.
The completed formal report has WNS−20.657ns/TNS−4,518,861.000ns,
WHS−3.474ns/THS−1,298,322.375ns and WPWS1.800ns. Neither is routed timing
or a qualified frequency. All twelve check_timing categories are zero, but
DRC has one RTSTAT-13 Critical Warning: insufficient routing prevents the
routing-status checks from running. Methodology has1,024 SYNTH-5,1,000
TIMING-15 and1,000 TIMING-16 occurrences. These are retained without waivers.
The worst reported setup path is output_service rd_ptr to state CE,29 levels,
24.837ns data delay including22.998ns estimated interconnect;15 of20 setup
paths instead target admin/cost_word, whose worst path is only0.146ns better.
The worst hold path starts at external sd[4126], not an internal register.

Actual reset BUFGCE placement is X0Y143; the declared external core clock source
X0Y144 remains unused by the design. These distinct locations are in
`post_place/buffer_locations.txt`. The placed DCP SHA256 is
`95391ea0a0d2954f3273e711c82c1889014128e1147357adcdeb66eebb96beaa`.
The independent post-place audit covers65 reference hashes,31 source files
and11 hook bindings. Its record distinguishes inherited structural census from
new post-place measurements. Standard phys_opt then reported zero changed
cells/nets and zero WNS/TNS gain. Its completed DCP SHA256 is
`c0367c8c41a0b9328da553de712af5da7124fbfab79c4b85f2aaeb19128ccbf9`.
Actual route_design is now running. A separate reused session completed a
read-only congestion report from the placed DCP with return code0. No active
hook was modified. The report contains60 windows: four directions, three
congestion types and levels3–7; all12 direction/type combinations reach level7.
Its hierarchy crossing rows report fabric12,477 nets, candidates6,700 and
dispatch3,976; these are net counts, not SLL occupation, and hierarchy rows
must not be summed with their descendants. Window cell percentages identify
physical concentration, not a causal attribution or total resource fraction.
See `physical_a/congestion_review_a/terminal.json` and `analysis_a` for the
report, input DCP binding, execution transcript and parsed rows.

The original route run subsequently reports estimated SLL demand26,153/23,040
(113.51%) across SLR1/SLR2 and23,852/23,040 (103.52%) across SLR0/SLR1;
its highest local column is209%. These router demand estimates are distinct
from the actual placed SLL counts above. Route35-3311 warns that a suitable
crossing solution might not be found. Route35-41 reports unusually high hold
violations and Route35-445 identifies at least1,953 high-pin-utilization CLBs.
SLL assignment and the logged global-routing step have returned, while the
full route remains running. The intermediate timing values are WNS−19.926ns,
TNS−3,843,878.163ns, WHS−2.452ns and THS−861,714.827ns; none is a final
routed frequency. The observation is frozen in `physical_a/route_sll_demand_a`.
Read-only reviews of a registered boundary context and installed SSI placement
directives are feasibility checks, not selected revisions or launched candidates.
The original run was allowed to reach its actual terminal result before a
single implementation-strategy followup was selected.

After Phase3.2, Route35-447 reports that congestion prevents all nets from
being routed and that the router will prioritize connectivity over timing
optimization. The original child subsequently completed the Phase3.3,3.4 and3.5
timing-update steps and entered Phase3.6 Update Timing. Those observations were
active-run snapshots, not terminal route results. The partial logs are
retained in `physical_a/route_congestion_priority_a` and
`physical_a/route_phase3_5_observation_a` and
`physical_a/route_phase3_6_observation_a`. The latter also preserves the preceding
mutable status JSON files before correcting their stale nested placement-stage
fields and earlier synthesis PID; current status now consistently names the
actual f synthesis and active route. No original run or historical report changed.
The run directory still contains an old `.vivado.end.rst` dated
2026-11-15T23:52:00.891512Z, earlier than the physical launch at23:54:12Z.
That file belongs to the preceding opt-only wrapper and cannot certify this
route's completion. Use the actual project/run status, birth-matched process,
current-stage markers and terminal reports together; do not reset this run.

The original route subsequently failed after Phase3.6: Route35-3 reports level7
global congestion; the terminal router summary contains5,809,714 node overlaps
while failed/unrouted/partially-routed net counts are zero. The zeros do not waive
overlapping routes. Global vertical/horizontal utilization is47.833%/48.2712%,
while the reported local North/East congestion peaks are102.337%/111.459%.
The original child exited at07:50:23UTC; the actual project reports
`route_design ERROR`, with current route/vivado error markers. Error DCP size is
628,605,511bytes, SHA256
`9706b2cae8ee7f48b7bb9c033e548d947c18bac362f3eba931a362e625947c35`.
`physical_a/route_terminal_a` preserves terminal logs, generated Tcl, markers
and the checkpoint binding. `final_synthesis_review/route_error_review_a`
classifies9,105 physical WARNING lines and2 ERROR lines; the tool's intermediate
one-error summary precedes the final Common17-39. All9,097 Route35-198 port
warnings remain unresolved interface-context limitations. The364,207 tight
setup/hold pins are represented by a truncated10,000-pin file, not a complete list.

Terminal error-checkpoint resource reports have now been generated in
`physical_a/route_terminal_collection_a/reports_b`; timing and other collection
steps are in progress. Their `Design State: Routed` header does not establish
legal routing or timing closure. The first collector attempt stopped before
report generation because Vivado2022.2 uses Tcl8.5.14 without `try/finally`.
The original script and empty output are preserved; `collect_v2.tcl` uses
validated `catch` cleanup semantics and a new output directory. This was a
report-script compatibility error, not a synthesis or implementation rerun.

The selected single followup is `full_impl_f_ssi_spreadslls_a`: same verified
unplaced opt DCP,31 unchanged sources,U280,5ns,8 threads and explicit ultrathreads,
with `place_design -directive SSI_SpreadSLLs -ultrathreads`, default phys_opt and
default route. Actual local congestion, SLL demand and repeated SLR crossings
on the placed critical paths motivate this placement change; no benefit is
assumed. Nearly100% CLB-site occupancy may leave insufficient redistribution
space. It neither repairs hold by definition nor supplies a physical OOC port
context. No RTL/lane/device candidate runs in parallel. The new non-project
flow uses a reused idle candidate-worktree interpreter, separate `run_a`
outputs, process-birth/command receipts and frozen scripts. It is not a reset
or relaunch of the original f project. Stage/checkpoint/report errors are
recorded separately; no model or CPU/GPU rerun is triggered at this point.

Terminal report collection also needs separate all-path setup/hold reports and
an explicit blackbox census, which are absent from the frozen post-route hook.
The audit must map the hook's actual filenames and allow the completed DCP size;
its default64MiB bound otherwise leaves the checkpoint unread. Separate internal
register-to-register reports can supplement diagnosis but cannot replace all-path
reports or qualify the external interface. If route or its hook fails, the flow
only attempts an error DCP. Once that file and the process are terminal, collect
missing reports in a new directory from the actual error DCP; never source the
fixed-output hook over earlier reports. These are collection requirements, not
executed additional EDA or evidence of route completion.

Route35-198 exposes a separate OOC interface limitation: external signal ports
lack HD.PARTPIN_LOCS, so their partial routes and input/output timing are not
accurate. The observation includes all8,192 sd bits; its9,097 warning lines
are a captured prefix, not a terminal warning census. Existing max/min I/O
delays and zero unconstrained endpoints do not resolve this gap. A future
internal register-path result under the specified clock-source assumption
must not be called complete interface Fmax or board timing. Physical boundary
connections and their launch/capture budgets need a documented context;
arbitrary coordinates are not platform evidence. See
`physical_a/ooc_boundary_review_a` and `post_place_path_review_a`. UG9052022.2
context guidance previously consulted is limited to7-series; it is not an
UltraScale+ complete-flow qualification. The actual tool properties, warnings,
and source-bound reports remain the evidence for this run.

The preceding e full-core source closure is30 files. Its actual5ns synthesis
completed on2026-11-15 at18:22:03UTC. The earlier1,254,466-LUT module sum is a
historical planning estimate, not the measured fit. That e run requires
1,353,922 CLB LUTs (1,065,866 logic +288,056 memory), exceeding1,303,680 by
50,242 (3.85%). It uses749,255 FF,1,148 BRAM36 equivalents,640 URAM and0 DSP.
Synthesis DRC reports one UTLZ-1 over-utilization error. Standard opt_design
subsequently completed successfully with1,351,028 LUTs (1,063,228 logic +
287,800 memory),748,683 FF, unchanged1,148 BRAM36 equivalents/640 URAM and
0 DSP. It remains47,348 LUTs over capacity. No DRC severity waiver is applied;
placement is not launched for this over-capacity mapping.

The worst emitted unplaced setup path has slack -5.000ns, data delay9.796ns
and42 logic levels, from bank0 completion payload to bank23 completion FSM CE.
Its7.804ns routing component is an unplaced estimate. Worst reported hold
is -0.091ns from external cfg_job_index to jobs RAM address. These results
are neither routed timing nor an achieved frequency. The e synthesis DCP
SHA-256 is876b7fdd3342c540335311f91c5fe180e018c1f984c26a988f2a1aa0757c61ac.

Baseline d used -no_timing_driven while e uses default timing-driven synthesis.
Both the dispatcher and synthesis option differ; their area delta is not a
controlled same-flow estimate of rewrite savings. No complete-core clock is
qualified yet. The following earlier-run history is retained for provenance;
b/c and the old standalone dispatcher are now cancelled as superseded.

The original b synthesis reported `Synth8-326`, automatically
breaking a combinational loop through output `write_v[1]`. The source chain is
strict-prefix second-valid → admin valid-gated request metadata → adapter
kind/address legality → network ready → first-write ready → second-valid.
This inferred timing exception is not accepted as closure. A bounded integration
repair separates stable export metadata from second-valid; only the actual
request-valid remains valid-gated. Capacity/credits/service latency remain
unchanged in the completed full native regression below.
The original synthesis was retained during diagnosis, then cancelled as
superseded after the selected dispatcher revision passed complete validation.
The repair is now frozen in `full_synth_c/source`. `fixtures_full_b` passed all32
full samples and11 rejection checks: complete outputs, every accepted-event
trace, all phase/kind/sample counts and absolute simulation finish times are
identical to `full_a`. The newly bound `model_calibration_f_admin_c` contract
independently verifies this identity and reuses the completed model_f runs;
its observed calibration differences remain retained in that prior contract.
The model_g contract now supersedes it for current calibration. Only
`cp_admin.sv` changed in the30-file DUT closure. Actual repaired full synthesis
started in `full_synth_c` at5ns after the regression passed. Both b and c were
later cancelled as superseded; neither supplied a completed default-mapping
baseline. Selected e has now completed without an8-326 message; its unplaced
result still does not qualify a routed clock.

An additional narrow `dispatch_synth_a` diagnostic exposes all runtime ports of
the unchanged production POP dispatcher. Its source matched the original b/c complete-core
freezes. This controller had standalone functional tests but no completed
resource/path report. The diagnostic was later cancelled as superseded and
supplies no completed clock or area result. Unlike the integrated core, it exposes all six
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
case. At the selected full-core frequency, nanoseconds convert by ceiling to
core cycles. A matching completed source/service point is reused; a changed
point requires new calibrated full-batch execution. Old cycles are not divided
by a newly chosen frequency. Board time remains null.

While synthesis was running, the coordinator authorized the repaired
candidate's complete BNN40/LSTM40 run at the initial200MHz target as a
conditional functional/capacity baseline. This exception to the
runner's coordinator gate does not qualify that frequency or establish final
selection. Its explicit decision receipt retains this distinction. If the
selected routed frequency differs, the corresponding full batches will be
rerun with newly derived memory service cycles. The predeclared conservative
service point has passed the same complete native RTL/model calibration.

Both model_g full scenarios have now completed, with160 independently checked
sample outputs, identical full ALT hashes, phase sums, per-port request/return
conservation and finite pool/queue/bank/spill/tag capacity checks. The selected
full-core clock remains unqualified; the following results are **conditional
predictions at an assumed200MHz**, with declared memory service:

| Case / service | Full cycles | Conditional seconds | Measured CPU mean / model | Model / measured GPU mean |
|---|---:|---:|---:|---:|
| BNN40 base80ns/5ns | 102557024 | 0.512785120 | 1.364361 | 3.378032 |
| BNN40 conservative160ns/10ns | 135128351 | 0.675641755 | 1.035496 | 4.450869 |
| LSTM40 base80ns/5ns | 104154414 | 0.520772070 | 1.393143 | 3.265070 |
| LSTM40 conservative160ns/10ns | 137198248 | 0.685991240 | 1.057608 | 4.300939 |

GPU remains faster. BNN conservative does not show a robust CPU advantage:
its prediction exceeds the fastest observed CPU process mean0.668920613333s,
although it is below the three-process mean0.699624213444s. LSTM conservative
is below all three observed process means, but a three-process observed range
is not a statistical bound or a guarantee for unmeasured memory behavior.
The deterministic model is not assigned artificial noise. CPU dispersion and
memory-service sensitivity are reported separately.

At200MHz the two contracts implement16/1 and32/2 latency/issue cycles. Their
ideal32-byte issue ceilings are204.8 and102.4GB/s across32 ports, shared by
reads and writes. Those ceilings are not measured effective random-RMW HBM
service. `full_g_200_two_scenario_summary_a` binds complete19-phase tables,
12x32 traffic, endpoint peaks, software process statistics and903 audited files.
The paired full runs are actual finite executions, not scaled historical cycles.

## Conditional mechanism diagnosis

The complete model_g base runs locate the main time in expansion:

| Metric at assumed200MHz | BNN40 | LSTM40 |
|---|---:|---:|
| Candidate / EXPAND cycle | 16.276978 | 16.297042 |
| Fraction of64-lane ideal candidate peak | 25.4328% | 25.4641% |
| EXPAND share of all core cycles | 77.0936% | 77.1477% |
| FINALIZE share | 20.9475% | 20.8916% |
| All other mutually exclusive phases | 1.9590% | 1.9606% |

The retained CUDA implementation exposes sample parallelism across the actual
batch; the FPGA core processes samples sequentially through finite POP,
frontend, transport and publication services. Phase durations and observed
throughput support a configuration-specific explanation. Overlapping stall
counters do not identify additive, independently removable losses.

For the fixed candidate count and64 II1 lanes at assumed200MHz, edge-work-only
bounds are100.541965/102.305681ms, both below the retained GPU means. Thus edge
work alone cannot prove a GPU advantage. A different, explicitly conditional
diagnostic holds every current non-EXPAND phase duration fixed and retains the
current FSM's lack of cross-phase overlap. Those fixed durations are
117.460765/119.008145ms; adding ideal edge service yields218.002730/221.313826ms.
This says that improving only expansion cannot catch the GPU under those
fixed assumptions. It says nothing universal about changing publication,
batch parallelism, lanes, frequency, memory or architecture, and is not a gate
on complete-core implementation. No POP lower bound or overlapping stall
count is added. `full_g_200_fixed_stage_diagnostic_a` preserves the calculation
and raw phase/candidate bindings. A changed frequency requires renewed finite
service discretization and execution before updating this diagnostic.

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
File persistence depends on the deployed input path. Device transfer and invocation
have no board measurement here. No transfer bandwidth is invented, and no resident
advantage is promoted to an E2/Process advantage. The separate native E2/Process
table and ALT/STRICT qualification remain in the companion evidence report.

The selected64-worker CPU also reads the same `descriptors.bin` and `edges.bin`
from its conversion directory and decodes that packed descriptor during the
resident solve (`software/cpu.cpp`). The approximately0.64s descriptor
construction observation is therefore common preparation for this CPU/FPGA
representation, not an FPGA-only charge. In a nonoverlap diagnostic with truly
common costs cancelled, net additional FPGA nonresident work must fit within
the current conditional margins: base186.839/204.738ms or conservative
23.982/39.519ms for BNN/LSTM. These are budgets at assumed200MHz, not measured
E2 benefits or guarantees at a different frequency. Transfers, overlap and
representation-specific differences need their own declared timeline.
`continuation_model_readiness_a` binds this review to actual CPU commands,
source and input receipts.

Required host output layout conversion has now been measured separately on the
Xeon Gold6530 server. The selected complete g outputs, bound to the revised RTL
calibration/reuse contract, supply8,028,160/8,172,160 valid bytes. The input is
explicitly **layout replay from actual completed outputs, not captured DMA**.
The decoder swaps the two32-bit words of each64-bit cost pair and removes
sample-tail/stride padding; every repeated decoded output is byte-exact.

| Complete-batch host stage, milliseconds | BNN40 | LSTM40 |
|---|---:|---:|
| Conversion: mean of three process means | 1.561172 | 1.537052 |
| Conversion: sample SD of three process means | 0.055318 | 0.106717 |
| Output allocation: mean, separately timed | 0.011404 | 0.013816 |
| Output first touch: mean, separately timed | 8.745916 | 8.388458 |

Both cases ran sequentially on CPU0 (socket0/core0), each with three independently
launched processes, one warmup and three formal repeats per process. The three
process means are the statistical units. Conversion uses preallocated, prefaulted
buffers and repeated no-flush cache state; it is not a cold post-DMA measurement.
Input file loading, output allocation/first touch, comparison/SHA and file output
are outside the conversion timer. Native map assembly, transfers and complete
production E2 remain unmeasured by this cohort. The coordinator suspended EDA,
DCP loading and archive work during measurement; quiet-window observations retain
the idle MCP/Vivado sessions and do not claim an exclusive machine.

The [postprocessing report](../results/fpga_cpu_primary_20261115/postprocess_final_g_a/REPORT.md)
and [delivery receipt](../results/fpga_cpu_primary_20261115/postprocess_final_g_a/delivery.json)
retain all process records and source/output bindings; the receipt SHA-256 is
`f5b5a073f9057f1be901edef378f23b8a1135c491754c595d15eb21bcd422719`.
Packed CPU and CUDA also perform output conversion outside their resident timers;
this host cost must not be charged only to FPGA in a resident comparison. A later
device frequency may reuse this host observation only with unchanged complete
output hashes, dimensions, physical layout, conversion code and host boundary,
retaining the measured host environment. It supplies no FPGA clock qualification.

## Provisional claim ledger

| Claim | Current support |
|---|---|
| Optimized CPU thread selection on current allocation | measured, complete |
| Whole-pair ALT CPU outputs equal frozen golden | exact full batches |
| Runtime connected production L1 source/function | 52 complete executions and11 rejection checks passed |
| Complete-core resources fit U280 | f actual post-opt95.20%; physical implementation pending; e post-opt103.63% retained |
| Complete-core routed clock | unqualified |
| RTL/finite-model calibration at200MHz test service | 52 complete cases with exact phase/request schedules |
| Complete model_g outputs at assumed200MHz | both scenarios,160 samples verified |
| Final-frequency complete-batch FPGA time | pending complete-core routed clock |
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
process/run log supply the authoritative state. Actual implementation status is read from the selected project and its bound
child process. No duplicate job is launched based on the broken status adapter.

After default full-core synthesis spent multiple hours in timing optimization
without a completed resource table, `full_synth_d_no_timing` adds one bounded
tool-flow diagnostic using installed2022.2 `-no_timing_driven`. Its30 DUT hashes
and5ns XDC bytes exactly match `full_synth_c`; prior runs were preserved during diagnosis.
The option disables timing-driven synthesis, not constraints or real paths.
Any resulting area applies to this mapping option, not a bound on the default
runs, and cannot qualify a clock without complete implementation reports.
The decision, installed command help, generated command and process identity
are retained in that isolated result directory.

The no-timing-driven full-core run completed successfully on 2026-11-15 at
15:50:57 UTC. Its actual synthesized utilization is 1,870,861 CLB LUT
(1,582,805 logic + 288,056 memory), 749,284 FF, 1,148 BRAM36 equivalents, 640 URAM
and 32 DSP. Against 1,303,680 available LUTs, this mapping exceeds capacity by
567,181 LUTs (43.51%). The tool-adjusted LUT count includes LUT combining;
post-synthesis opt_design/physical optimization may change it. This is a
synthesis-stage resource result, not a routed count or a bound on a different
mapping. `full_synth_d_no_timing/terminal.json` and
`terminal_cp_full_top_utilization_synth.rpt` retain the exact evidence.
The rebuilt hierarchy reports 278,419 LUTs in dispatch and 354,002 in bank
completion rows. These rows do not isolate FIFO cost: actual worst-path cells
include `completion/bad_result...` logic between dispatcher registers. Immediate
child/self LUT rows sum 16,384 above the global count, so the global report
remains authoritative and these rows must not be treated as independent area
blocks. The worst reported unplaced setup path starts at
`dispatch/result_rr_reg[0][1]/C` and ends at `dispatch/error_reg/D`: slack
-273.469 ns, data path 278.351 ns, 1,103 logic levels, with 16 DSP segments in
the return/error dependency chain. This is not routed timing or an Fmax.

`dispatcher_restructure_decision_a.json` and `dispatcher_path_confirmation_a.json`
authorize one isolated dispatcher revision: equivalent rank-based grants,
independent return-group selection/error aggregation and static unpacked response
buses with bounded bank indices. Pre-edge capacity, identities, ledger rejection
without fallback, and all handshakes must remain unchanged. Six bounded local
XSim runs have now passed, including original-versus-revised output/lifecycle
comparisons,8192 assignment patterns,640 return patterns and the no-fallback
rejection case. These are reset-reachable/defined-payload simulation checks,
not exhaustive formal or arbitrary-X equivalence. The variant is selected for
integration validation. The new full-core52-sample/11-rejection calibration
subsequently passed with no model change or empirical correction. All160
complete model samples and source/binary/output bindings were reverified for
explicit reuse. Physical results remain necessary before qualification;
no predicted saving, hardware clock or CPU speedup is claimed from the rewrite.

After this complete integration check, the preceding default b/c and standalone
dispatcher runs were explicitly cancelled as superseded. Their original Linux
birth identities were checked, pre-signal logs frozen, and targeted pidfd SIGTERM
used; all signalled processes exited. These cancellations are neither completed
mapping results nor measured synthesis failures. Each isolated run retains a
`cancelled_superseded_a` decision, log snapshot and terminal receipt. The e synthesis/report collection and standard post-opt implementation
stage have since completed; e remains over capacity. No historical branch job
or artifact was modified.

The read-only `delivery/audit_route.py REPORT_DIR --out NEW_JSON` collects
source-bound resource, setup/hold/pulse, routing, clock, constraint and diagnostic
evidence after reports exist. It always requires manual qualification; missing
fields remain unknown. Its `route_audit_dev_a` historical/synthetic parser checks
are software validation only, not new complete-core implementation evidence.

This source/evidence checkpoint is not final completion.
`checkpoint_full_g_batches.json` records completed model_g batches and the
still-live physical work at snapshot time. Earlier source/calibration and
in-flight checkpoints remain preserved. The compressed archive is a point-in-
time snapshot; actual resource/route results and any necessary changed-frequency
batches will be added in the same independent branch.

The actual post-opt footprint authorizes one further bounded resource revision
recorded in `candidate_wordmux_a/decision.json`. It preserves64 lanes,64 banks,
all FIFO/hold capacities and the original balanced key arbitration, changing
only96-bit payload-tree selection into three32-bit array reads using the same
6-bit selected index. The historical shared router remains untouched. Local
comparison, complete RTL/model calibration and actual synthesis are required;
there is no predicted area or timing saving. G8, a second arbitration rewrite,
L2 and device migration are not implemented as parallel followup candidates.

Post-opt input DCP metadata explicitly retains OutOfContext=1 and
DisableAutoIOBuffers=1. Default optimization inserted
`dispatch/core_reset_BUFG_inst` for a high-fanout reset/enable net; it is not
the core-clock source. Timing38-242 reports missing HD.CLK_SRC on external
reset during post-opt timing estimation. This limitation is retained, without
assigning a fictitious reset clock source or waiving it. The over-capacity e
mapping is not a routed or timing-qualified result.

The selected wordmux revision has now passed all required integration comparisons.
Only the candidate-network instance changed and one dedicated router source was
added;29 preceding DUT sources, including the top, are unchanged. The output
service continues to use the protected shared router, so the complete closure
contains31 files. Both full test runs are byte/event/cycle-identical to the
preceding dispatcher revision; the new reuse contract SHA-256 is
`790e70b51c751b3ee2cfd6701d5621f061dc19a298eadc0bc24b344f21e51190`.
The local test is a known-valid behavioral comparison, not arbitrary-X or
formal equivalence. This checkpoint starts actual f synthesis and does not
claim complete-core physical closure.
