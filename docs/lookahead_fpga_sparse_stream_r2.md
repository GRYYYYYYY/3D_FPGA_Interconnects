# Sparse Stream R2（执行中）

本轮从 `5651a34abb97939bee6402c5af585753ab07f64b` 建立独立 worktree 与分支。原始 main、原稿、STRICT、旧 golden、历史结果和未跟踪指导文件不修改。当前状态是 **in_progress**；本文件不构成完整候选或板卡性能结论。

## 已实现并核验的证据

- C++ 有效 POP whole-pair 在线归约：d3/d4 和 BNN/LSTM 各完整 batch byte-exact；每个原桶闭合点与独立旧 closed-fold oracle 比较，R1 每 wave 既有工作量列不变。软件 oracle 的额外开销不用于 CPU 速度比较。
- 91 个额外 native graph fixtures（182 sample）输出正确；随包 180 项算法检查单列。5 类不支持的 FP32 位模式被明确拒绝。初始负零测试生成器和弱错误检查的问题保留在 failures 中，正确证据为 `numeric_rejections_bit_exact.json`。
- `m2c`：8 lanes/8 owners，POP 双路独立确认、每 lane 16 tagged metadata contexts、8 路同步 RAM whole-pair/seen reducer；snapshot bucket 平衡树和 epoch 控制树；每 bank 16 个初始化写在途；硬件顺序 batch controller，cost 仅加载一次，每 sample 输出写 ACK 全部返回后继续。
- 所有 33 个逻辑客户端共享 8 个假设物理接口，每接口 64 IDs、32B 行，包含请求 FIFO、仲裁、乱序 tag 映射和寄存器返回。此接口不是实测 HBM，也不是完整板卡 shell。
- m2c 完整 d3/d4、91 个 native RTL fixtures、两个 40-sample 容量用例通过。容量用例覆盖 node 4095/cell 32767、qid 改映射和 25,538-cell 最后不足整行的输出；这是小图节点容量下的真实 batch 控制证据，**不是** BNN/LSTM 大图 RTL 结果。
- Vivado 2022.2 XSim 单元测试通过 4,000 次双路背压事件和约 1.9 万次 reducer 更新，核验 whole-pair、独立 seen、同地址转发、完整导出及错误 qid。

## 当前周期消融（无合格频率，外存假设）

统一 60-cycle base latency + 有限随机扰动、每物理通道最短 2-cycle 接收间隔。周期包含 device 内部初始化、cost/job/metadata、搜索、控制、commit、输出与 ACK。一次 batch start，初次 H2D/最终 D2H 不计。

| 配置 | d3：8 sample | d4：12 sample |
|---|---:|---:|
| 新 bucket/control/共享接口/真实 batch，旧 sparse closed fold，初始化在途 1 | 115332 | 227194 |
| POP 在线归约，初始化在途 1 | 111122 | 213993 |
| POP 在线归约，初始化在途 16（m2c） | 40874 | 108659 |

该消融不是将 R1 25 个独立内存服务直接重命名。完整共享接口、每 sample 输出 ACK 等边界变化已包含；R1 冻结结果独立保留。16/60/120-cycle latency 与 1/2/4-cycle service gap 的已执行小图敏感性结果在 `rtl/m2c_*`；这些是周期假设，尚不换算为实测秒数。

## M3 当前进展与负结果

新增 owner 同步 RAM 弹性流水，request k+1 的 tag/read 与 k 的 RMW/event 重叠；热命中单元测试实际观测到连续 4096 周期各退休 1 候选。首次压力版本发生脏缓冲满与 response FIFO 头部 fill 的等待环，已保留失败源码/日志。修复为 admission 时预约 dirty credit、payload-ready 控制写请求后，4800 候选压力验证全部退休，32 MSHR/16 dirty buffer、48 物理在途被实际覆盖。

新 changed 服务用四个 sector append 端口处理整行 mask，membership 直到 commit ACK 才清除。owner/changed 组合测试通过跨驱逐重复改善：2534 个 fence 前写回、3281 次 sector events、2793 个唯一 changed IDs，完整 backing 和 ACK 清标验证通过。

新增 commit proposal response、label/pending read、allocator、directory forwarding/publication 流水。bank_pipe_b 独立测试完成 1038 次 commit、512 次 POP、16 次 stale，5009 cycles，连续 511 周期各确认一次 commit，member peak 527。pipe_full_d 通过 d3/d4、全部91fixtures和两组压力图；仅修正 reducer RAM 端口的 pipe_full_e 保持 d3/d4 39531/102270 cycles。小图通过不能替代大图状态 backing、完整候选 OOC 或新架构模型校准。


## M4 外部状态闭环与新模型

external_b 实现每 owner 4KiB state cache、32 MSHR、16 dirty buffers、64-entry FIFOs；每 node128bit(label64/pending32/flags32)，32个 POP/commit contexts 和32个 changed-mark contexts。changed 的 membership 存在外部状态中，目录发布后才请求 CLEAR，写 ACK屏障后才能完成 wave。初始化真实写 proposal与全部state backing，不能从 host免费复位。全部41逻辑clients共享8物理通道。

完整d3/d4为47824/131079 cycles（60-cycle假设、gap2）；91fixtures和两组热点图均核对输出、wave label/home/changed集合。真实4,194,304-node地址范围的构造图完整初始化并搜索到node4194303，输出32768cells，1856186cycles；这是地址与协议测试，不是BNN/LSTM工作量。每owner changed容量512时，8192-node星图实际触发显式容量拒绝，未发布输出。两个40sample容量batch也通过。

新的独立C++逐周期模型：owner stress/warm、node-state7680ops/165414cycles、fabric33000requests/25091cycles分别日志精确一致。完整external_model_b对97个独立RTL用例全部周期日志与输出精确一致（2native、91fixtures、2stress、2大地址）。该校准只覆盖8路及列出的有限内存配置；不能继承给尚未实现的32/64路。

## 通用变换软件对照（实测CPU）

prepared_CSR_valid_POP_CPU完整包含每sample mutable初始化、cost复制、搜索、changed commit、原桶闭合点结束和输出写入。3进程各1预热+3正式完整batch，8线程，完整输出与ALT golden一致。BNN均值3.307430729s、样本标准差0.086225747s；LSTM均值3.438127634s、标准差0.068122253s。外部CSR准备与首次装载不计，符合V2；CPU主机并发运行Vivado且不同于GPU主机，不能声称同机软件speedup。

已检查旧basic/compact CUDA：expand仍运行时eligible判断，confirm在闭合点扫描settled，不是prepared CSR+POP在线归约的等价优化实现。原GPU V2结果保留；新增 prepared CSR+POP CUDA 已完成，见后面的独立实测结果，未给旧结果改名。

## 尚未完成

- 完整 tile 和完整32路候选的 routed OOC、setup/hold闭合。已有 pair_lane 单元200MHz闭合不能代替完整核。
- 新注册ready和F0路径的32路重新校准、容量边界与完整大图；8路F1/F0各97个用例已经逐周期精确校准。
- BNN/LSTM各40sample的有限架构仿真已启动，尚无完整输出或性能结论；M1功能正确不等于M5完成。
- 相同大图状态/物理通道的F0/F1消融和完整核合格频率下的固定ns内存敏感性。

配置在 `accel/lookahead/fpga_sparse_stream_r2/config/experiment_spec.r2.yaml`；逐项状态在 `results/fpga_sparse_stream_r2_20261112/checkpoint.json`。所有失败版本、源代码快照、周期日志与工具日志留在本轮 results。尚未声明 FPGA 胜过 CPU/GPU，尚无 board measured 结果。


R2 continuation 18:15 UTC (in progress): mapped arithmetic feedback was removed using single-assignment normalization/rounding. The isolated pair_lane routed at 200MHz with WNS +0.077ns and WHS +0.020ns, zero timing loops; OOC clock-source/partition-pin placement warnings remain, and this is not full-kernel qualification. M3d actual synthesis:735949LUT,170150FF,300RAMB36+153RAMB18. M3e explicit reducer ports:589685LUT,167533FF,356RAMB36+161RAMB18. Both retain48old-FP mapped-loop warnings and cannot supply a frequency claim; routing these obsolete candidates was skipped and their evidence retained.

external_d bitmap RAM passed97complete RTL/model-trace comparisons; Vivado parser rejected a mixed initialized/uninitialized net declaration at external_bank.sv:47. external_e only separates those declarations and is synthesizing. external_f also records write-buffer dependencies at MSHR admission, clears them on ACK, and replaces rotated-index arbitration with fixed-index balanced selection. The scoreboard is checked against all original address guards every RTL clock. Owner warm/stress and node-state complete traces remain exact;95complete small/pressure traces are exact, and both64K/4Maddress regressions pass. Complete f OOC is running. No complete-tile frequency is yet qualified.

New software measurements are independent of oldGPU V2, which remains unchanged. `software/prepared_pop_gpu_b` has91fixtures x2CUDArepresentations and4native inputs x3processes x(1warmup+3measurements), plus8-thread CPU on the same H100worker. All218process receipts pass and output bytes match. BNN/LSTM compact CUDA V2 means:0.151799969444/0.160247990444s; basic CUDA:0.156690577111/0.159888578444s; same-worker transformed CPU:4.534045816222/4.623006792333s. Original failedgpu_a is retained:91fixtures and smallnative passed; missing largepreparedCSR file prevented any large timing. The corrected worker preflights files, loads separately bound prepared CSR, and checks eligibility reconstruction.

This tighter software baseline excludes a fixed32-lane<=200MHz candidate with unchanged edgework and one candidate/lane/cycle even before initialization/commit/memory. It does not exclude changedwork/higher-frequency/wider structures. Actual hierarchy is now coded: five bounded clients per owner ->one64taguplink->shared physical ports; parameterized many_tile has8reducer banks and bounded8192member/changed entries per32-owner. Modules and complete8/32topologies are being independently calibrated; no8-lane calibration is claimed for32. Full BNN/LSTM architecture simulation, complete-kernel timing, F0/F1 large-state ablation, and native timing-scope audit remain pending.

18:20 continuation: composed161client/32physical fabric passed161000transactions at96775cycles with every cycle equal to its independent model. many8_b integrated topology passed95cases exact to many8_model_a; native cycles48873/135753. Full32RTL compilation/calibration remains in progress. The actual8192-entry bank synthesized13989LUT,8416FF,57RAMB36+15RAMB18. Vivado confirms2016BRAM36equivalent and960URAM available onxcu280:32banks alone require2064BRAM36equivalent, so the all-BRAM fixedcandidate cannot fit. A separately frozen USE_URAM version moves large directory/member/free/changed arrays to URAM; inference and implementation are pending, not presumed.


18:47 continuation (in progress): many32_b now passes the complete95case RTL suite (2native,91fixtures,2pressure), and independent many32_model_b/d/e logs are exact. Native32 cycles are104498/201809. Models d/e remove host-only full-cache copies and replace nested arbiter searches by equivalent bitsets; no clocks, dependencies or events are sampled/skipped. Every optimization was recalibrated. Full BNN/LSTM models b/d were explicitly interrupted as superseded, with partial logs/receipts retained; e owns the current complete-batch run. Only one hardware start drives all40samples; compact trace suppresses text rows, retains all cycle evaluation, counters, phase/commit logs and a cycle digest. No elapsed host-model time is used as FPGA performance.

Actual bank8192_uram synthesis gives13962LUT8432FF31RAMB36+14RAMB18+7URAM. The synthesis posthook had unloaded timing constraints (WNS/WHS infinity, no clocks); these reports are not qualification evidence. Opening the synthesized design reloads the XDC:5ns WNS-1.130/WHS+.025, zero combinational/latch loops. Routing is ongoing. A subsequent RTL repair snapshots the original bucket tail and ends POP there, eliminating the new-member NIL write. This makes member_next one synchronous read/one write and MA-bit wide; the independent old NIL-terminated model remains the cycle/output reference. many32_c RTL compiled; full regressions and complete-kernel synthesis are running.

external_f actual complete8 synthesis:376759LUT194031FF516RAMB36+193RAMB18. Opened valid5ns constraints giveWNS-4.876/WHS+.025, zero mapped loops. Critical path goes from state-request BRAM through ready logic to physical_rsp_ready,36logic levels. A new FIFO only advertises registered free space, adding a single full-to-nonfull acceptance bubble and breaking this combinational ready path. New RTL and independent models must be calibrated again; old zero-error calibration is not inherited.

The standalone C33/P32 physical fabric synthesized200285LUT54069FF132RAMB36+33RAMB18. Its four-entry request FIFOs waste4.5BRAM each; new source uses synchronous distributed RAM for these shallow FIFOs. Complete many8_reg_b OOC includes the registered-ready/tail repair and shallow-memory mapping. many32_reg_a RTL compilation is underway. No new candidate is yet declared resource/timing qualified.

Native reuse audit in baselines/native_reuse/audit.json verifies actual input-prefix hashes and complete ALT-output hashes for both BNN/LSTM;21historical native timing/qualification rows are preserved with host/binary/library/map/route bindings. Native E2/Process remains a separate timing scope and never enters V2 speedup denominators. Existing ALT versus STRICT congestion differences remain. The new CUDA job finished with API state job_succeeded (job-eb9a21bb-c74e-46f6-98b8-4d485c2a4236); originalGPU V2 and failedfirst transformed-worker evidence are retained.


19:13 continuation (in progress): registered-ready complete8F1 and F0 each pass97RTL tests and independent cycle logs, including both large-address graphs. Same60cycle/gap2 assumptions: F1 d3/d4=48873/135753cycles, F0=77421/270142cycles. Proposal write/read beats are F1:1824/1348 and7543/6734, F0:2276/3068 and9458/19892. These are functional RTL cycle results, not board timings or32-lane extrapolation. many32_c also passes97RTL output tests; its independent tail calibration and40-job boundary tests are running.

The original8192URAM bank routes with WNS-1.402ns/WHS+.020ns at5ns, a retained negative. The tail-snapshot/13-bit single-write next-array and registered-ready bank synthesizes14628LUT8418FF17RAMB36+6RAMB18+9URAM, WNS-.502ns/WHS+.025ns; its route is active. Complete8 many8_reg_b has358396LUT214592FF368RAMB36+112RAMB18 and valid5ns synthesis WNS-3.017ns/WHS+.025ns; route remains active.

Owner MSHR candidate/count arrays now have one whole-word allocation/merge write port. Standalone actual synthesis falls from24036LUT12460FF to6909LUT3236FF (644LUTRAM,13RAMB36+2RAMB18). All warm/stress cycles are byte-identical to the previous owner:4096 consecutive warm retirements;4800stress accepted=retired,32MSHR/16dirty/48physical outstanding,395merges. Its standalone synthesis WNS-1.126ns remains negative; route and full8/32integration are pending. Earlier many8_mshr_a build used nonexistent command-line MC/CC parameter names and failed before elaboration; corrected many8_mshr_b uses MEMBER_CAP/CHANGED_LIMIT and retains the first log.

The OOC source assumption for new implementations is BUFGCE_X0Y144 in regionX4Y6, checked on the actual device; external global clock routing is estimated, without a containing shell. Ross methodology skill targets2026.1, so local2022.2 text reports are used. Adding the source assumption does not erase external_f's1000 reported TIMING-16 violations or change its-4.876ns opened-synth WNS. No false path, waiver or multicycle exception was added. See completed_ooc_1913 for archived methodology reports and constraints diff.

Full many32_model_e BNN/LSTM40-job batches remain in progress. Its members_peak counter falsely includes uninitialized free-pool entries and must not be interpreted as occupancy; the pool_initialized fix is in model_f/reg_b and later, with small-native actual peaks9–16. All cycle/output comparisons remain exact. New byte-vector and optional one-combin-evaluation-per-cycle host models retain every clock/event and require independent RTL calibration; only two native traces are yet verified for many32_reg_model_d. No host-model elapsed time contributes to FPGA speedup.


19:47 continuation (in progress): complete32 registered-ready RTL passes97cases. Independent many32_reg_model_c/d/e each matches all cycles, full output, all array/channel traffic, issue/accept/commit histograms and phase totals. Models d/e use one low-phase combinational evaluation per clock; e additionally avoids recomputing provably empty owner/state services until a request,response,reset or fence arrives. Every hardware clock, RNG draw, response and counter remains evaluated; there is no event/time sampling. Fullnative40job runs remain active and have no completed-batch result yet.

The owner0/physical0 hotspot uses1048577node addresses and8192unique changed IDs. Exactcapacity completes byte-exact;8193 is explicitly rejected without output. Both complete positive and negative cycle logs equal the independent32model. many32_c also completes both40job/maxcell and partial-line/missing tests. The registered-ready32 version has completed its first40job boundary, second is running; boundary model comparisons are pending.

Actual complete8 MSHR RAM synthesis is234982LUT149070FF368RAMB36+112RAMB18. Its worst path is an80logic-level priority cascade from wait_write to writeback enable, WNS-14.402ns at5ns. A balanced low-ID free/issue and high-ID matching tree preserves the old selection order, and its owner unit traces are exactly unchanged. Complete8/32 integration is being recalibrated. This negative timing is retained despite the resource improvement.

Owner raw-port OOC with HD.CLK_SRC completes routing with WNS-4.508ns/WHS-2.044ns. Register-to-register hold is+.032ns; worst negative hold is rst input at.1ns relative to an internal estimated clock insertion of2.173ns. Lower frequency cannot resolve that input-reference mismatch. No old I/O delay or report is deleted. A separate synthesizable context provides real synchronous launch/capture registers for every DUT port and an internal routed BUFGCE at X0Y144. LFSRs only keep launch registers observable to synthesis; they are not functional stimulus or a performance workload. All context resources are included. The context top clock and signature retain actual timing constraints, and all DUT boundary paths are physical register-to-register paths. This qualifies only a registered synchronous integration environment, never a board/shell.

A real optional REQUEST_STAGE=1 inserts a FF after request RAM. Total FIFO admission remains64 including all stages. Independent pipeline FIFO modeling includes the added latency. Owner warm retirement still has4096consecutiveII1cycles; stress4800accepted=retired at30842cycles (OOO scheduling changes the trace from the earlier30924). Complete many8_request_a passes97full cycle/traffic/output comparisons to many8_request_model_a. The subsequent balancedtree owner retains this new trace exactly; many8_request_tree_b and many32_request_tree_a require their own complete checks.

Owner registered-context synthesis:7400LUT4201FF13RAMB36+2RAMB18,5ns WNS-.146/WHS-.074. Route remains active, so this is not clock qualification. Complete8 context with balanced selection began synthesis19:43. All fullkernel clocks remain null, board_measured=false, candidate_status=in_progress.


20:04 continuation (in progress): many8_request_tree_b and many32_mshr_a each pass97 complete independent cycle/output/traffic/phase/histogram comparisons. The former includes REQUEST_STAGE1 and balanced selection; the latter is REQUEST_STAGE0/old linear selection. Neither calibration is transferred to a modified path. bank8192_reg routed5ns WNS-3.668ns/WHS-2.540ns is a retained negative, not a qualified clock.

An opt-in fixed physical time TB contract now takes kernel_period_ps/base_latency_ps/service_gap_ps/jitter_step_ps. Responses and service gaps round upward onto synchronous kernel edges, with no CDC assumed; the old cycle-based contract remains unchanged by default. Proposed200/125MHz and80/300/600ns cases are explicit sensitivity assumptions, never measured or OOC-qualified frequencies. Full fixed-time RTL/model calibration is pending.


20:10 continuation (in progress): owner_context_a completed route. At5ns it has WNS-1.758ns/WHS+.006ns. Re-running STA on the same fully routed netlist with8ns clock and unchanged.5/.1ns signature delays gives WNS+1.242ns/WHS+.006ns. check_timing lists zero no-clock,unconstrained endpoints,missingIOdelays,multipleclocks,loops andpartialdelays. The8nsDCP/XDC/reports are saved separately; old5ns failure remains. Methodology has only intentionalclockoverride warnings andBUFGLOCadvisory. This supports125MHz for this owner context only (oldlinearselector REQUEST_STAGE1), not a completekernel or board.

Complete8 balancedtree context actualsynthesis is235849LUT154686FF368RAMB36+112RAMB18;5ns WNS-2.088/WHS-.080, routeactive. Complete32 matchingcontext synthesis started19:57:12. All27commonRTLsourcehashes match the corresponding8/32functionalRTL frozen builds; top-levelparameters are recorded in timing/context_bindings_2008.json.

36fixed-ns8lane RTL/model cases pass allcycles,outputs,traffic andphysicalcontract metadata at explicitlyhypothetical5/8ns kernel periods,80/300/600ns base latency,5/10/20ns service gap and0..60ns seeded jitter.32lane sweep is running. Three32registeredready models c/d/e match bothcomplete40job boundaries and8192/8193hotcapacity, includingexplicitnegative/nooutput. NewREQUEST_STAGE1 reruns these boundaries rather than inheriting them. XSim pop_epoch_a additionally passes epochffff->0,qid63->0,staleevent rejection andreset/reinitialization.

Hostmodel profile_b identifies combinationalmodel evaluation andfinitefabric processing as the dominant simulation-host cost. An optionalword-chunk bitpacker changes no hardwareevents orclocks;266240exhaustive position/width/random checks pass UBSan. many32_request_model_c requires its own97casecalibration before its gated completebatchrun. Hostelapsedtime remains excluded fromFPGAresults. Archivescheckpoint1946andpredecessor1914 verify29772filehashes; futurelarge traces use bounded64MiBparts with exact reconstruction hashes.


20:17 update: all36 fixed-physical-time32lane RTL/model cases also pass, includingfullcycles,alloutputs,traffic/histograms/phases andcontractmetadata. These clocks remainhypothetical. XSim pop_metadata_a passes16simultaneousimmutablePOPcontexts,reverse-orderreturns,outputbackpressure,preservedpair/qid/epochdespitemutatedcurrentinputs,explicitduplicate-IDrejectionandresetrecovery. This unit test deliberatelychangescurrentepochbeforeoldreturnssolelytoverifythecaptureproperty; thelegalcontrollerstillwaitsfordrainbeforeadvancingepochs.


20:20 update: many32_request_model_c passes97 completeRTLcases fornewREQUEST_STAGE1/balancedtree;many32_f0_model_a passes97for matchedexternalstate/sharedchannelF0REQUEST_STAGE0. Both gatedrealBNN/LSTM40samplebatches have started. Newcandidate also runs full40samples at16and120kernel-cyclememorylatencies, alongside60; these are explicitlycycle-basedsensitivity assumptions, notfixed-ns orqualifiedclockresults. Physicalns mustbe disclosed usingthe actual eventualclock; the separate36scenariofixed-nsRTLcalibrations remainbound to theirrecordedperiods. No completebatchhasyetfinished.
