# Sparse Stream R2（执行中）

本轮从 `5651a34abb97939bee6402c5af585753ab07f64b` 建立独立 worktree 与分支。原始 main、原稿、STRICT、旧 golden、历史结果和未跟踪指导文件不修改。当前状态是 **in_progress**；本文件不构成完整候选或板卡性能结论。

## 当前可复核结果（21:49 UTC）

有效 POP 的 whole-pair 归约、原桶闭合后等待所有事件排空的结束规则、稀疏目录/工作列表、有限 owner/state 缓存、changed/commit 流水、共享物理通道、cost 一次加载和 Q=1 batch 控制均已有可运行实现。当前完整32路候选为32 owners、每owner 8192成员/changed容量、32个假设物理通道，每通道64个ID；尚未实现或验证64路完整核。

新共享通道归约版本的8路及32路均通过97个完整RTL/独立模型用例，核对全部周期、输出和流量。8路及32路均完成36组固定纳秒延迟假设校准。进一步的并行4-way缓存选择已通过81920组XSim穷举与owner/state单元检查，完整8路和32路F1/F0均重新通过97项及36组固定ns校准。最新bank上下文选择树的完整8路通过97项、36组固定ns及两个Q40输出边界；对应32路F1/F0校准与容量边界继续运行。

下表为已完成的真实小图RTL完整batch。统一60-cycle基础延迟、0至12周期随机扰动、最短2-cycle通道接收间隔；不是板测或已定频结果。`F1`为有限4-way×32-set×32B owner缓存，`F0`为保留有限并发与ACK的无合并服务；state backing、物理通道、batch边界与请求流水保持对应。

| 完整RTL配置 | d3：8 sample周期 | d4：12 sample周期 | d4发射/周期 | d4提交/周期 |
|---|---:|---:|---:|---:|
| 8-lane F1，many8_fabric_tree_a | 49,224 | 135,871 | 0.112158 | 0.034246 |
| 32-lane F1，many32_fabric_tree_a | 104,440 | 202,122 | 0.075395 | 0.023021 |
| 32-lane F0，many32_request_f0_reduction_b | 127,055 | 292,003 | 0.052188 | 0.015935 |

吞吐分母为完整resident batch所有周期，和单元热命中II1是不同量。32路为真实大图配置使用更大的有限目录/成员容量，小图初始化成本因此增加；不能把表格当作只改变lane数的缩放实验。各数组32B事务数、峰值并发、完整输出hash及原始summary引用见[机器可读小图结果](../results/fpga_sparse_stream_r2_20261112/analysis/completed_native_2105.json)。

当前物理证据分层如下。所有资源均为Vivado实际结果；同步集成上下文包含真实BUFG及launch/capture寄存器，其资源计入，不能称为完整shell。

| 版本/范围 | LUT | FF | BRAM36 / BRAM18 / URAM | 5ns结果 | 可用范围 |
|---|---:|---:|---|---|---|
| owner_context_a，旧选择单元，已路由 | 7,629 | 4,223 | 13 / 2 / 0 | WNS −1.758，WHS +0.006 | 同一已路由网表8ns重新STA：+1.242/+0.006，仅此单元125MHz |
| many8_context_tree_a，冻结完整8核已路由 | 234,879 | 154,909 | 368 / 112 / 0 | −2.656/+0.010 | 同一已路由网表8ns STA +0.344/+0.010，匹配97项及36组校准，仅该8核125MHz |
| many8_context_reduction_b，共享通道修复完整8核已路由 | 234,728 | 154,823 | 368 / 112 / 0 | −2.823/+0.003 | 同一实际网表8ns STA +0.177/+0.003，匹配97项及36组校准，仅此8核125MHz |
| central_reduction_a，33×32共享通道综合 | 223,029 | 100,412 | 0 / 0 / 0 | −0.108/−0.074 | 正在布线，单元结果 |
| state_way_context_a，新选择state单元已路由 | 7,095 | 4,564 | 16 / 1 / 0 | −0.212/+0.012 | 同一已路由网表8ns STA +2.788/+0.012，仅此单元125MHz |
| many32_mshr_a，旧线性选择完整32核综合 | 1,083,688 | 586,261 | 1064 / 296 / 288 | −14.408/+0.025 | 旧固定候选负结果，新完整32实现继续 |
| many32_reg_b，旧多写MSHR完整32核综合 | 1,575,155 | 848,380 | 1064 / 296 / 288 | −7.110/+0.025 | 超LUT容量，停止此固定候选布线 |
| many32_c，旧ready完整32核综合 | 1,505,153 | 817,663 | 1665 / 446 / 288 | −6.091/+0.025 | 超LUT容量，停止此固定候选布线 |

真实40-sample完整架构仿真已通过一个新请求流水场景：16-cycle基础延迟、2-cycle通道间隔、0至12周期扰动下，BNN/LSTM分别180,141,407/184,018,993cycles。完整输出、逐wave提交唯一性与工作量、全部ACK、初始化/输出流量和有限容量审计通过，且输出与合格native ALT一致。旧registered-ready模型60-cycle场景分别285,155,267/293,638,486cycles也通过；两组同时改变请求流水与延迟，不能把其比值当作单项流水收益。默认60cycle、120cycle和F0继续运行，尚无合格32核频率下的秒数。`board_measured=false`、`whole_kernel_timing_closed=false`、`fpga_simulated_superiority_supported=false` 保持不变。外存延迟及通道服务是明确假设，不是HBM实测；5ns/8ns固定时间组合目前也只是频率敏感性假设。

软件对照已经完成并保存独立进程原始样本。新增prepared CSR+POP同范围GPU V2均值：BNN basic/compact 0.156690577/0.151799969s，LSTM 0.159888578/0.160247990s；旧GPU V2原样保留。native E2/Process及ALT与STRICT的历史差异另表处理。当前没有FPGA优于这些基线的完整证据。

## 已实现并核验的证据

- C++ 有效 POP whole-pair 在线归约：d3/d4 和 BNN/LSTM 各完整 batch byte-exact；每个原桶闭合点与独立旧 closed-fold oracle 比较，R1 每 wave 既有工作量列不变。软件 oracle 的额外开销不用于 CPU 速度比较。
- 91 个额外 native graph fixtures（182 sample）输出正确；随包 180 项算法检查单列。5 类不支持的 FP32 位模式被明确拒绝。初始负零测试生成器和弱错误检查的问题保留在 failures 中，正确证据为 `numeric_rejections_bit_exact.json`。
- `m2c`：8 lanes/8 owners，POP 双路独立确认、每 lane 16 tagged metadata contexts、8 路同步 RAM whole-pair/seen reducer；snapshot bucket 平衡树和 epoch 控制树；每 bank 16 个初始化写在途；硬件顺序 batch controller，cost 仅加载一次，每 sample 输出写 ACK 全部返回后继续。
- 所有 33 个逻辑客户端共享 8 个假设物理接口，每接口 64 IDs、32B 行，包含请求 FIFO、仲裁、乱序 tag 映射和寄存器返回。此接口不是实测 HBM，也不是完整板卡 shell。
- m2c 完整 d3/d4、91 个 native RTL fixtures、两个 40-sample 容量用例通过。容量用例覆盖 node 4095/cell 32767、qid 改映射和 25,538-cell 最后不足整行的输出；这是小图节点容量下的真实 batch 控制证据，**不是** BNN/LSTM 大图 RTL 结果。
- Vivado 2022.2 XSim 单元测试通过 4,000 次双路背压事件和约 1.9 万次 reducer 更新，核验 whole-pair、独立 seen、同地址转发、完整导出及错误 qid。

## 早期小图周期消融（无合格频率，外存假设）

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

- 后续 fabric/way 修复版 tile 和完整32路候选的 routed OOC、setup/hold闭合。已通过的冻结8路原型125MHz和pair_lane单元200MHz均不能替代新完整32核。
- 最新bank上下文选择树的完整32路F1/F0重新校准和容量边界。并行4-way版本的完整8路及32路F1/F0已通过97项及36组固定ns校准；最新bank8也通过97项、36组固定ns和两个Q40边界。
- 完整大图模型的全部内存/F0对照、逐wave工作审计和匹配完整32核OOC。已终态结果按上文列出；不能由M1或部分场景代替未完成证据。
- 相同大图状态/物理通道的F0/F1消融和完整核合格频率下的固定ns内存敏感性。

配置在 `accel/lookahead/fpga_sparse_stream_r2/config/experiment_spec.r2.yaml`；逐项状态在 `results/fpga_sparse_stream_r2_20261112/checkpoint.json`。所有失败版本、源代码快照、周期日志与工具日志留在本轮 results。尚未声明 FPGA 胜过 CPU/GPU，尚无 board measured 结果。



## 冻结 native E2 / Process 对照（历史实测，独立范围）

以下为R6.2相同worker、8线程/affinity的三个独立进程均值，原始21行与binary/map/route绑定保存在 `baselines/native_reuse/audit.json`。E2包含native构造/转换，Process还包含routing/FULL/STA；不作为resident V2分母。BNN此表只有已合格pipeline补充，不能暗示该cohort具有全部后端。

| case | backend | E2均值(s) | Process均值(s) | n |
|---|---|---:|---:|---:|
| bnn | pipeline | 9.154427093 | 72.206928833 | 3 |
| lstm_s2 | alt_cpu | 9.781227827 | 81.246322992 | 3 |
| lstm_s2 | alt_cuda | 3.088784138 | 74.702667973 | 3 |
| lstm_s2 | flat | 9.908701590 | 81.545226081 | 3 |
| lstm_s2 | pipeline | 9.907448727 | 81.726693397 | 3 |
| lstm_s2 | stock | 65.413333333 | 137.394711821 | 3 |
| s38417 | pipeline | 0.160015837 | 6.022681292 | 3 |

LSTM ALT相对STRICT保留23,111个congestion-word差异，delay/missing差异均0；相同ALT输出仅复用ALT的native资格，未声明STRICT等价。新增prepared-POP CUDA/CPU实测另列V2，不赋予历史native E2新的计时含义。

## 历次实现与失败记录（保留当时状态）

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


20:25 actual32resourceaudit: oldmultiwrite-MSHR many32_reg_b synthesizes1575155LUT848380FF1212BRAMtiles288URAM,120.82percentofU280LUTcapacity. Thatfrozenvariantwillnotberouted. Singlewrite-MSHR many32_mshr_a drops to1083688LUT586261FF1064RAMB36+296RAMB18+288URAM(83.13percentLUT); itstillusesoldlinearselection/REQUEST_STAGE0andhasnoclockqualification. Thematchednewrequest/treecomplete32contextcontinues. Thisresourceimprovementisactualsynthesis,notanaggregateestimateorFPGAwideproof.

A matchedfinalREQUEST_STAGE1 F0variant is nowbuilding/calibrating,withactualcomplete32physicalcontext synthesisstarted20:24:32. OldREQUEST_STAGE0F0/F1runs remainseparatelybound. AnF0hostmodel optimization snapshots onlyoldFIFOheads/validbits instead of copyingentireFIFOstorageeveryclock; itmust passitsown97caseRTLcomparison beforeuse. Hardwarestate transitions andeventclocks remainunchanged.

## 20:51 UTC：共享通道归约修复与独立重新校准

旧32-lane综合显示中央共享通道有52级 bc→error 路径。现将可独立计算的请求ready、响应consume、busy和错误条件改为向量归约，保持原仲裁次序、有限容量和协议拍数。8/32-lane分层单元分别完成41000/161000请求的逐周期差分；中央33×32单元另外通过两个物理端口同时非法ID注入和sticky error复位测试。

新完整8-lane已通过97项逐周期/全输出/全部流量校准及36项固定纳秒假设组合。完整32-lane F1/F0回归与匹配的新OOC均已实际启动，尚未继承旧结构校准或时钟资格。请求流水版本的两项Q40容量测试和8192/8193成员边界通过；这两项Q40构造图不代表真实BNN/LSTM完整batch。真实完整batch仍逐周期运行，未报告最终性能。

旧many32_reg_b超过器件LUT容量；旧many32_mshr_a虽降至83.13%LUT，其旧线性选择路径仍失败。它们仅否决相应固定实现。旧external_f完整8路由结果为376265 LUT、194137 FF、516 RAMB36+193 RAMB18，5ns WNS −13.101ns、WHS +0.015ns，作为负结果保留；未用它给新结构定频。

缓存替换选择的进一步修复：新8-lane综合最坏路径经过state缓存victim的循环优先链（28级）。并行4-way候选掩码与平衡选择替代该链，保留最高匹配way、最低invalid way、圆形替换顺序。81920种状态组合XSim通过；owner stress/warm逐周期与旧stage1版本完全一致（30842/5162周期，4096连续II1退休）；4M地址state测试7680操作通过。初次使用SV保留字matches导致的编译失败日志保留，改名后的测试通过。新8/32完整拓扑构建和state独立OOC已启动，完整时钟与大batch结果仍待验证。

21:46 continuation: the saved routed state context passes setup, hold and pulse-width at8ns, all12 check_timing categories are zero, and every9852 routable net is routed with zero route errors. The mechanical checker separately rejects its5ns negative result. The actual complete8 context routes with234879LUT154909FF368RAMB36+112RAMB18,5ns WNS-2.656/WHS+.010. Its8ns reports currently show+.344/+.010; checkpoint saving and final scope review are still in progress, so no frequency has yet been transferred into results. The immutable snapshot chain through2135 verifies52883files across5snapshots.

21:49 reviewed milestone: many8_context_tree_a is qualified at125MHz only for its frozen complete8 prototype. All328111 routable nets are routed, setup+.344ns/hold+.010ns/pulse-width+3.458ns, all12 check_timing categories zero, no false/multicycle paths or removed IO constraints. The36fixed-ns test executable relinks the identical immutable Verilator RTL archive; the binding audit now follows and verifies this parent archive instead of incorrectly applying default32lane parameters to a C++ relink command. The initial failed audit is retained; v2 verifies all27source files, actualRTLparameters and reused object hashes. The complete32 candidate clock remains null.

22:08 continuation: the new complete32 shared-fabric F1 synthesis fits at1085529LUT607662FF1064RAMB36+296RAMB18+288URAM,5ns WNS-2.705/WHS-.080. Its worst path is commit-context cs to carg (30levels), and full routing started22:01:39. The corresponding F0 synth is954048LUT551629FF1064RAMB36+264RAMB18+288URAM,5ns-1.532/-.080; state victim selection remains critical. The parallel-way complete8 synth is236696LUT154718FF424BRAMtiles,5ns-1.075/-.080, and route began21:51:32. Parallel-way complete32 F1 now passes97+36; its four batch/capacity boundaries and F0 corresponding checks continue. No complete32 operating clock is yet qualified.

The completed-native work auditor passes d3/d4: candidate and changed work equal M1, each wave commits unique IDs with the exact expected count, every clock is accounted, mutable state/proposal initialization and job/output traffic are present, and member/changed/MSHR/dirty/physical-ID peaks stay bounded. Four separate injected mutations (dropped candidate, duplicate commit, free state initialization, event sampling) are rejected. These audits assign no clock and do not substitute small cases for unfinished BNN/LSTM40 results.

22:13 bank-path follow-up: actual complete32 shared-fabric synthesis located a30level path from context state to carg. The external bank had four loop-carried32-entry priority selections. They are replaced with parallel state decoding, balanced first-ID trees and bounded-width population sums; the16-entry initialization selection also uses the existing balanced tree. All original priorities, context counts, credits, capacities and cycle boundaries are retained. XSim bank_context_tree_a passes689840 directed/random state and initialization-mask cases against the old serial algorithm. New full8 RTL pipeline and matching physical-context synthesis are active. The independent model remains unchanged; neither prior calibration nor clock qualification is inherited.

22:19 continuation: the new bank-selection complete8 passes all97full RTL/model cycle, output and traffic checks, including4Maddress backing. Exact27source/parameter binding to many8_bank_context_a passes. Its36fixed-ns sweep andQ40continue. This substantive small/concurrency gate enabled the new complete32 F1/F0 pipelines (many32_bank_tree_a/many32_f0_bank_a) and corresponding actual OOC syntheses at22:18:27/29. Full32 calibration and frequency are still pending; the already running exact cycle-model native batches are not restarted or transferred without fresh new-path calibration.

22:26 continuation: new bank8 completes36fixed-ns cases and bothQ40 output/cell boundaries, in addition to97full calibration. The old many8_mshr_b route finishes at233946LUT149015FF424BRAMtiles,5ns WNS-8.707/WHS-2.646, retained as an explicit failed-clock candidate. The old many8_reg_b route is357919LUT214646FF424BRAMtiles,5ns-13.101/-2.977; neither negative hold is hidden by a slower-clock claim. Source/work-audit commit22c9dced4967231e6784d32b652c7acdccaa6439 remains on the independent branch; snapshot2219 is being verified.

22:46 continuation: complete32 F0 parallel-way synthesis finishes at958906LUT551613FF1064RAMB36+264RAMB18+288URAM,5ns WNS-1.075/WHS-.080, frontend arithmetic29logic-level critical path. Its97+36independent calibrations and twoQ40 output cases pass. Only this predecessor route is skipped while the already implemented bank-tree complete32F0 successor synthesizes and recalibrates; the full32fabric baseline route remains active. Seven native audit gates await both actual40-sample completions and then check complete work/output/capacity, with no assigned clock. No fullnative batch is yet claimed complete.

22:48 reviewed milestone: the shared-fabric repair complete8 many8_context_reduction_b passes8ns setup+.177ns,hold+.003ns,pulse-width+3.458ns. All327945routable nets route, zeroerrors and12check_timing categories allzero. Its real BUFG/launch/capture context uses234728LUT154823FF368RAMB36+112RAMB18. The frozen many8_fabric_tree_a source/parameters bind27SVfiles and fresh97+36calibration. This is a second qualified125MHz8prototype, not a32lane/native clock or newbank/way qualification. The5ns failed result remains.

2026-11-12T22:54:22.607552+00:00 continuation: latest bank-tree complete32F1 passes97fresh RTL/model full-cycle/output/traffic tests. Parallel-way32F1/F0 each also passes allfourQ40/hot8192/overflow8193 boundary calibrations. Binding audit now evaluates complete dependent parameter expressions instead of a numeric prefix: C=41/161 and CTL=32/128 for8/32, OWNER_BITS=3/5. Seven actual source/parameter bindings pass; old artifacts retain their misleading display fields, while identical source hashes and explicit topology checks were unaffected. This audit correction changes no RTL, model cycles or OOC constraints.

2026-11-12T22:59:45.872214+00:00 complete-native milestone: new request-stage F1 modelC at16cyclebase/gap2 completes BNN180141407cycles and LSTM184018993cycles, each40samples with one hardware start. Both complete work audits pass, including physical/array traffic, init/output counts, capacity, per-wave unique commits and all outputs. Member/changed peaks BNN6892/6863 and LSTM6986/6982 fit8192. Both per-wave commit-set digests equal the completed oldR0lat60 control. Native output identity reuse passes allfour completed model cases. `large_complete_batch_model_verified=true` is scoped only to this completed scenario; no main clock or FPGA superiority is claimed.
