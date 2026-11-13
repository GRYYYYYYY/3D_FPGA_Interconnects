# Sparse Stream R2（执行中）

本轮从 `5651a34abb97939bee6402c5af585753ab07f64b` 建立独立 worktree 与分支。原始 main、原稿、STRICT、旧 golden、历史结果和未跟踪指导文件不修改。当前状态是 **in_progress**；本文件不构成完整候选或板卡性能结论。

## 当前可复核结果

12:11 UTC 更新：P8 gap1的BNN/LSTM完整40batch已通过输出、逐wave工作量、容量、ACK、native身份及版本绑定，周期分别359,062,210/366,543,747。同条件周期为P32的2.463/2.446倍；其余6个P8 batch继续。旧完整32核及SSI重试已有路由负结果，两个旧bank候选也报告非法路由、等待最终文件。尚无完整32核时钟，全部主比较FPGA秒数仍为null。

有效 POP 的 whole-pair 归约、原桶闭合后等待所有事件排空的结束规则、稀疏目录/工作列表、有限 owner/state 缓存、changed/commit 流水、共享物理通道、cost 一次加载和 Q=1 batch 控制均已有可运行实现。当前完整32路候选为32 owners、每owner 8192成员/changed容量、32个假设物理通道，每通道64个ID；另有保持32 owners、改为8共享物理通道的P8候选正在独立验证。尚未实现或验证64路完整核。 当前harness物理/发射掩码为32bit，central client ID为6bit；64个owner再加controller需要65个central clients，不能只改lane参数。构建入口已显式拒绝超出当前实现范围的配置，见 `analysis/topology_limit_guards_0137.json`；此限制不代表新互连实现不可行。

最新P32候选是按真实布局路径修复的并行router ready归约。完整8路已通过97项、36组固定纳秒、两个Q40并取得本版本125MHz OOC资格。新32路F1现已通过97项逐周期/输出/流量/阶段核对、36组固定ns、18组10ns补充及4项Q40/热点容量边界；同一模型的三档延迟、两张图共六个native40完整batch已重新绑定，见`analysis/router32_bound_0627.json`；额外gap1/gap4四项完整batch也已通过审计并绑定，见`analysis/router32_gap1_bound_0725.json`和`analysis/router32_gap4_bound_0907.json`。F0也已通过97+36+18+4，同一模型的BNN/LSTM两个native40 batch已经重新绑定，见`analysis/router32_F0_bound_0658.json`。对应完整32核综合已完成，实际布局布线仍在运行；所有完整32核时钟均为null。旧checked F0默认route拥塞失败和中央33×32单元非法路由的证据均已保存，同网表SSI重试也已因局部SLL拥塞失败，另行保存只读诊断。32-owner/8共享通道P8候选已通过独立97+36+18+4校准，其中gap1两张图的完整40batch已审计通过，另6个batch和物理实现仍在运行。

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
| many8_way_context_a，并行way完整8核已路由 | 235,916 | 154,920 | 368 / 112 / 0 | −2.500/+0.006 | 同一实际网表8ns STA +0.500/+0.006，匹配97项及36组校准，仅此8核125MHz |
| central_reduction_a，33×32单元route结束但非法 | 223,763 | 100,478 | 0 / 0 / 0 | −12.343/−0.038 | 62,694条资源冲突，RTSTAT-13，无频率资格 |
| central_onehot_a，33×32单元合法布线 | 414,660 | 100,427 | 0 / 0 / 0 | −6.302/+0.001 | 5/8/10ns均未通过；实际12.5ns STA +1.198/+0.001，仅此单元80MHz |
| many8_bank_context_a，bank选择树完整8核已路由 | 235,511 | 154,845 | 368 / 112 / 0 | −3.103/+0.003 | 8ns仍−0.103；同一网表10ns +1.897/+0.003，仅此8核100MHz |
| pair_legacy_context_a，原FP32单元已路由 | 813 | 611 | 0 / 0 / 0 | +0.043/+0.005 | 相同真实同步上下文，仅此算术单元200MHz |
| pair_checked_context_a，错误路径修复单元已路由 | 783 | 612 | 0 / 0 / 0 | +0.221/+0.016 | 新旧所有输出周期等价，仅此算术单元200MHz |
| many8_grant_context_a，one-hot仲裁完整8核已路由 | 235,875 | 154,905 | 368 / 112 / 0 | −3.012/+0.010 | 8ns仍−0.012；同一网表10ns +1.988/+0.010，仅此8核100MHz |
| many8_address_context_a，地址前移完整8核已路由 | 234,657 | 155,130 | 368 / 120 / 0 | −2.201/+0.001 | 同一网表8ns +0.799/+0.001，仅此8核125MHz |
| many8_checked_context_a，FP32修复完整8核已路由 | 234,904 | 154,972 | 368 / 120 / 0 | −2.531/+0.010 | 同一网表8ns +0.469/+0.010，仅此8核125MHz |
| many8_router_ready_context_a，并行ready归约完整8核已路由 | 234,392 | 155,114 | 368 / 120 / 0 | −1.859/+0.007 | 同一网表8ns +1.141/+0.007，仅此8核125MHz |
| state_address_context_a，地址前移state单元已路由 | 6,989 | 4,556 | 16 / 2 / 0 | +0.014/+0.001 | 完整性、4M backing与独立周期差分通过，仅此单元200MHz |
| state_way_context_a，新选择state单元已路由 | 7,095 | 4,564 | 16 / 1 / 0 | −0.212/+0.012 | 同一已路由网表8ns STA +2.788/+0.012，仅此单元125MHz |
| many32_context_reduction_b，旧共享通道归约完整32核，非法布线 | 1,078,639 | 607,495 | 1064 / 296 / 288 | −22.325/−0.088 | 134,257条资源冲突，RTSTAT-6，无频率资格 |
| many32_mshr_a，旧线性选择完整32核综合 | 1,083,688 | 586,261 | 1064 / 296 / 288 | −14.408/+0.025 | 旧固定候选负结果，新完整32实现继续 |
| many32_reg_b，旧多写MSHR完整32核综合 | 1,575,155 | 848,380 | 1064 / 296 / 288 | −7.110/+0.025 | 超LUT容量，停止此固定候选布线 |
| many32_c，旧ready完整32核综合 | 1,505,153 | 817,663 | 1665 / 446 / 288 | −6.091/+0.025 | 超LUT容量，停止此固定候选布线 |

旧checked完整32核的实际综合使用10ns实现目标，不能混入上表的5ns列。两者均包含32 owners、8192成员/changed容量、32共享物理端口和真实同步上下文。F1仍在布线；F0于04:43正式因拥塞失败。综合setup为正不构成时钟资格。

| 完整32核 | LUT | FF | BRAM36 / BRAM18 / URAM | 10ns综合setup / hold | 完整核频率 |
|---|---:|---:|---|---|---|
| many32_checked_context_10ns_a，F1 | 1,075,171 | 607,781 | 1064 / 328 / 288 | +4.590 / −0.080ns | 未取得 |
| many32_f0_checked_context_10ns_a，F0 | 944,933 | 551,508 | 1064 / 296 / 288 | +4.590 / −0.080ns | 路由失败，无频率资格 |
| many32_router_ready_context_10ns_a，新P32 F1 | 1,079,700 | 607,788 | 1064 / 328 / 288 | +4.359 / −0.080ns | 实现中，无频率资格 |
| many32_f0_router_ready_context_10ns_a，新P32 F0 | 947,951 | 551,507 | 1064 / 296 / 288 | +4.590 / −0.080ns | 实现中；只读布局诊断setup/hold仍负 |
| many32_p8_router_context_10ns_a，P8 F1 | 920,818 | 560,586 | 1064 / 328 / 288 | +4.590 / −0.080ns | 校准及2个完整batch通过，其余6项与实现中，无频率资格 |

完整BNN/LSTM模型、97项完整用例、36组固定纳秒校准与四项Q40/容量边界已分别绑定至同一F1/F0模型和冻结RTL，见 `analysis/checked32_bound_0256.json`、`analysis/checked32_F0_bound_0328.json`。这些绑定仍输出null秒数，等待对应完整核的实际路由资格。

真实40-sample完整架构仿真已完成三档F1延迟及匹配F0场景。其中：16-cycle基础延迟、2-cycle通道间隔、0至12周期扰动下，BNN/LSTM分别180,141,407/184,018,993cycles。完整输出、逐wave提交唯一性与工作量、全部ACK、初始化/输出流量和有限容量审计通过，且输出与合格native ALT一致。旧registered-ready模型60-cycle场景分别285,155,267/293,638,486cycles也通过；两组同时改变请求流水与延迟，不能把其比值当作单项流水收益。默认60-cycle及120-cycle场景也已完成并通过审计（见下表）；匹配F0也已完成并通过全部工作/容量/ACK审计及native身份核验；仍无合格32核频率下的秒数。`board_measured=false`、`whole_kernel_timing_closed=false`、`fpga_simulated_superiority_supported=false` 保持不变。外存延迟及通道服务是明确假设，不是HBM实测；5ns/8ns固定时间组合目前也只是频率敏感性假设。

完整候选绑定检查已将bank32的97项、36组固定ns、四项容量边界、冻结RTL/模型参数、16/60/120-cycle真实40batch工作审计和native ALT输出关联到同一模型可执行文件。由于完整32核尚无合格时钟，六个batch的模拟秒数均保持null。五项反例确认8路时钟、算术单元时钟、错误cache配置、其他模型run及其他native绑定不能混入；见 `analysis/bank32_bound_0129.json` 与 `analysis/binding_guard_tests_0104.json`。

软件对照已经完成并保存独立进程原始样本。新增prepared CSR+POP同范围GPU V2均值：BNN basic/compact 0.156690577/0.151799969s，LSTM 0.159888578/0.160247990s；旧GPU V2原样保留。native E2/Process及ALT与STRICT的历史差异另表处理。当前没有FPGA优于这些基线的完整证据。

## 已完成的大图架构模型场景（周期结果）

每项均为一次硬件启动、40个sample，包含mutable初始化、cost/job、搜索、提交、归约、输出写回和全部ACK。外存为32个共享同步假设物理通道，每通道64个ID、32B事务、最短2-cycle接收间隔，ready允许时采用固定seed的6/7接受条件，返回有0至12周期扰动。完整32核尚无合格频率，表中不填主比较秒数。

| 配置 | 基础延迟(cycles) | BNN完整周期 | LSTM完整周期 | BNN/LSTM内部流量(GB) | 验证 |
|---|---:|---:|---:|---:|---|
| F1，新请求流水modelC | 16 | 180,141,407 | 184,018,993 | 75.889 / 77.446 | 完整输出、工作量、容量、native ALT身份通过 |
| F1，新请求流水modelC | 60 | 285,126,884 | 293,652,813 | 75.479 / 77.029 | 完整输出、工作量、容量、native ALT身份通过 |
| F1，新请求流水modelC | 120 | 476,474,977 | 491,059,110 | 75.459 / 77.020 | 完整输出、工作量、容量、native ALT身份通过 |
| F1，旧registered-ready modelD | 60 | 285,155,267 | 293,638,486 | 75.475 / 77.032 | 完整输出、工作量、容量通过；历史对照 |
| F0，新请求流水 | 60 | 596,202,956 | 606,725,605 | 85.844 / 87.488 | 完整输出、工作量、容量、native ALT身份通过 |
| F0，旧registered-ready | 60 | 596,009,195 | 606,848,449 | 85.843 / 87.488 | 完整输出、工作量、容量、native ALT身份通过 |

16与60-cycle行的延迟假设不同，不能从比值归因流水加速。同为60-cycle时，新请求流水BNN周期下降0.00995%，LSTM上升0.00488%，不支持吞吐显著改善。三档F1及匹配60-cycle F0场景均已完成并通过审计。旧modelE仅优化主机求值，完整两图总周期、阶段日志、服务计数、逐周期摘要及输出与modelD完全一致；它是模型实现一致性检查，不是独立硬件测量样本。

新F1的BNN/LSTM逐wave唯一提交数分别104,210,988/106,141,205，与M1全部匹配；成员/changed峰值为6892/6863和6986/6982，均低于8192。owner/state MSHR与dirty峰值均实际达到32/16。16-cycle延迟场景的完整batch平均发射7.144/7.116候选/周期，观测峰值25/24，存在真实多候选并行；不以32-lane名义值充当实际吞吐。

在16-cycle延迟场景的已观测流量及gap2假设下，平均事务吞吐约为gap限制上限的82.3%/82.2%；60-cycle场景降为51.7%/51.2%，平均候选发射4.514/4.459每周期。该条件服务界用于解释已完成结果，既不是其他架构的上限，也不是HBM板测。每数组事务、阶段占比、重叠的owner/state请求停顿计数见 `analysis/completed_native_0252.json`；工作审计和native身份引用见checkpoint。旧阶段记录中的“尚无完整大图”仅描述其当时状态。

进一步的筛选固定各场景已经发生的逐通道事务与gap2合同，仅以最忙物理端口计算最早最后接收时刻，仍需147,661,357至152,075,773周期。即使忽略返回延迟、仲裁、依赖和排空，要追平新basic/compact GPU均值所需的条件kernel频率仍约942至978MHz；这不是已支持频率或FPGA性能结果。它只表明保持这些流量与端口合同、单独增加lane或缩短控制不能消除传输工作。改变cache、布局、工作量、端口或时钟域会使此前提失效，必须重新模拟。六个完整F1场景、每个GPU分母和输入hash见 `analysis/traffic_screen_checked32_0345.json`。

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

- P8独立BNN/LSTM完整40batch及延迟/带宽敏感性：已通过97+36+18+4全部重新校准，四组配置中gap1两项已完整审计，另6项仍在执行。P32 gap4已完整通过审计并绑定。
- 完整32路的routed OOC与setup/hold审查；address与checked完整8路均已通过125MHz，grant完整8路通过100MHz。已有冻结8路100/125MHz和state/pair单元200MHz不能转移给新完整32核。
- 将已完成的全部F1/F0 native40结果绑定到最终合格的完整核版本；完整输出、逐wave工作/容量/ACK审计与native身份已通过。
- 通过完整核OOC后，绑定其精确版本和频率，明确内存周期参数到纳秒的换算，再建立模拟秒数列；无板卡shell/实板结论。
- 汇总全部正负结果、验证证据快照、复核原worktree保护状态并推送独立分支。

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

另补入已冻结的R6.1 BNN native cohort，复用12个合格独立进程，覆盖原VPR多线程、optimized STRICT、ALT CPU和基础CUDA。该worker与上表R6.2及本轮prepared-POP worker不同，不计算跨cohort速度比。下表保持其历史中位数口径，E2/Process均不改名为V2。

| BNN backend（R6.1） | E2中位数(s) | Process中位数(s) | n |
|---|---:|---:|---:|
| stock | 63.030000000 | 125.577600437 | 3 |
| optimized | 10.393390145 | 73.061830186 | 3 |
| alt_cpu | 9.751707411 | 72.823985672 | 3 |
| alt_cuda | 3.104359912 | 66.725847946 | 3 |

输入prefix和完整ALT输出hash与R2一致；原始行、命令、binary/map/route/输入绑定及统计见 `baselines/native_reuse/r61_bnn_baseline_supplement.json`。BNN ALT对STRICT的24,434个native congestion-word差异同样保留，不能与历史offline sample的133,798个差异混为一谈。

同一新请求流水、共享通道和外部state服务下，F1相对F0使BNN/LSTM完整周期减少52.176%/51.600%，流量减少12.074%/11.956%；见`analysis/cache_R1_complete_0255.json`。此处只有模型周期与流量比。两类cache配置中新/旧请求流水的native周期变化均小于0.04%，不支持它带来显著吞吐收益。

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

2026-11-12T23:27:27.656063+00:00 continuation: new bank-tree complete32 F1/F0 syntheses finish with1091365/957243LUT,607867/551610FF,1064RAMB36+296/264RAMB18 and288URAM. Both fit the actual part; both5ns synthesis reports are WNS-1.075/WHS-.080, with frontend arithmetic29levels now worst. Fresh complete32F1 calibration97+36 andF0 calibration97pass;Q40/hot/fixed-ns followups continue. Actual full32F1/F0 routing launches23:25:54/55. Separate5/8/10ns routed STA scripts preserve constraints and wait for actual completion; no current complete32clock.

2026-11-12T23:34:48.024846+00:00 reviewed milestone: complete8 parallel-way context passes8ns setup+.500/hold+.006/pulsewidth+3.458, all328794routable nets complete, no route errors and all12 check_timing categories zero. Real context resources235916LUT154920FF368RAMB36+112RAMB18. Source and actual dependent parameters bind the independently passed97+36case many8_way_tree_a. This additional125MHz qualification remains limited to its frozen8prototype; bank32F1/F0 routing is still active and no main clock is assigned.

2026-11-12T23:53:21.293932+00:00 diagnosis: saved central33x32 physopt DCP reports internal return-arbitration to returned counter -1.984ns, and excluding counter endpoints only from report selection still shows -1.981ns to busy tag state. Estimated interconnect fractions72.137%/85.013%, with internal SLR crossing; no routed clock claim. Direct one-hot grants avoid encode/decode on handshake paths; bounded population trees replace serial counter increments. Same-cycle independent calibration and fresh8tile checks are underway; old active32 routes use immutable sources.

2026-11-13T00:08:05.812010+00:00 reviewed milestone: bank-tree complete8 routes all330191nets withzeroerrors.5ns/8ns setup failures retained; actual10ns STA setup+1.897,hold+.003,pulsewidth+4.458 and12check_timing categories allzero. Source/parameters bind97+36passing cases. Qualification is100MHz only for many8_bank_tree_a; no clock transfer to neweronehot/address versions or32native.

2026-11-13T00:12:58.928984+00:00 continuation: onehot fabric unit passes33000transactions+invalid-ID recovery;8/32hierarchies pass41000/161000transactions with exactly matching old independent model cycles.1156896 XSim priority/count cases pass. Complete8grant97+36andQ40pass. Its central-unit synthesis227188LUT100414FF,5ns-.259/-.074 is worse than prior223029LUT100412FF,-.108/-.074, so this standalone successor route is skipped; combined8OOC and baseline32routes continue. Separately, physical state-address precompute stores32extra bits in the existing64-entry request FIFO, no added cycles. Two nonzero-base4M-backing tests (ownerbits3/5) pass15360operations and exact independent cycle logs; complete8address97passes,36andQ40continue. State-address unit synthesis6848LUT4556FF16RAMB36+2RAMB18,5ns+.022/-.074,route started00:11:25; no unit clock claim yet.

2026-11-13T00:18:26.237135+00:00 conditional screening: frozen32lane one-candidate-per-lane issue ports and audited unchanged full work imply candidate-only minima40216786/40922273cycles. At hypothetical200MHz these alone exceed the newly measured prepared-POP GPU best means; required clock before any other cost is264.933/255.942MHz. This is a fixed-work/width/clock conditional screening statement, not FPGA performance or a global no-go. Current fullkernel frequency remains unqualified. Address-forward complete8 now passes97+36plusbothQ40cases; fresh32F1/F0 calibration proceeds from that passed gate.

2026-11-13T00:26:04.248216+00:00 continuation: complete8grant synthesis236600LUT154720FF368RAMB36+112RAMB18,5ns-1.075/-.080,route00:19:23. Complete8address synthesis235316LUT154701FF368RAMB36+120RAMB18,5ns-1.075/-.080; failing setup endpoints fall5872to504, but no routed tile frequency yet;route00:24:50. Complete32bank F0 now passes97+36andallfour boundaries, matchingF1 scope. Address32F1/F0 source/parameters bind fresh compiled candidates; complete32syntheses start00:21:00/02, independently of the older immutable32routes.

2026-11-13T00:31:05.870176+00:00 state-address unit qualification: actual5ns route setup+.014ns,hold+.001ns,pulsewidth+1.958ns; all9818netsrouted,0errors,12check_timing categorieszero. Resources6989LUT4556FF16RAMB36+2RAMB18include realcontext. Bound ownerbits5stage1RTL andnonzero-base4Mfullbacking independentcalibration.200MHz applies only to this unit. No complete32 clock exists yet.

2026-11-13T00:35:40.274531+00:00 arithmetic error-path repair: operand legality registers alongside operands; overflow predicate exactly compares the original exponent plus the normalization and rounding carries without decoding the completed FP32 word. Data rounding and sticky-error latency remain identical. CPU bit-exact500000sums pass; XSim old/new262144directed pairs plus500000random cycles match every data/handshake/error/reset signal. Complete8checked recalibration and matched old/new actual synchronous-context unitOOC are in progress. This is a new unqualified variant, not inherited200MHz.

2026-11-13T00:54:56.536734+00:00 checked-arithmetic milestone: new and original pair units both pass actual5ns setup/hold/pulse with zeroDRC and12check_timing categories zero; matchedcontext resources783/813LUT and612/611FF. The first mechanical review falsely required an RTSTAT-10 warning; clean zero-violation DRC is now explicitly accepted, and the failed review artifacts remain. Complete8checked97+36+twoQ40passes; full8physical5ns target starts00:49:46. Complete32checked F1/F0 fresh calibration starts from that passed8gate; immutable complete32physical contexts launch synthesis00:52:47/53 with explicit10ns target. This target is motivated by actualbank8only100MHz and ongoing32routing congestion, not claimedfrequency or an isolated arithmetic timing comparison. Old5ns candidates continue unchanged. Main32clock remainsnull.

2026-11-13T01:10:26.771967+00:00 follow-up: bank8 at its actually qualified10ns period passes18fixed-ns RTL/model cases (80/300/600ns base,5/10/20ns minimum gap,integer-cycle ceil and5ns jitter steps); this is conditional memory calibration, not memory measurement. Complete8checked synthesis235674LUT154723FF368RAMB36+120RAMB18,5ns setup-.346/hold-.080,26level result-data path; route starts01:06:06. Two existing evidence archives are actually restored into a new directory:193files110703498rawbytes, all hashes verified; full archive-chain hashes are separately verified.

2026-11-13T01:30:15.450110+00:00 completion: latency120/gap2 F1 native40 completes at476474977/491059110cycles; complete work/capacity/ACK and per-wave commit uniqueness audits pass, nativeALTidentityexact. Meanissue2.701/2.667 and observed gap-only transfer utilization30.93%/30.63% are model observations, not fixed service ceilings. F0native stillruns. Intermediate address32 F1/F0 syntheses finish1091778/952227LUT,607749/551476FF,1064RAMB36+328/296RAMB18+288URAM; both5ns-1.075/-.080 legacy arithmetic error path. Their individualroutes are skipped because implemented checked-error successors already synthesize; bank baselines and latest full32OOCs continue. All predecessor evidence retained.

2026-11-13T02:04:20.331899+00:00 physical milestone: direct-onehot complete8 is qualified only at100MHz after real10ns STA+1.988/+.010/pulse4.458,330154netsfullyrouted,12checktimingcategorieszero.8ns-.012failure remains. Its worst5ns path is state_base to node_state busyCE acrossSLR, already addressed in the independently running address/checked successors. Latestchecked32 F1/F0 actual10ns syntheses1075171/944933LUT,607781/551508FF,1064RAMB36+328/296RAMB18+288URAM;bothsynthsetup+4.590/hold-.080,notclocks. Their fresh97pass,F1fixedns36pass;fullrouteslaunch02:04/01:57:08;remainingboundariescontinue.

2026-11-13T02:13:33.292027+00:00 test-orchestration failure: the new generic32candidate wrapper omitted the model argument when calling many_hot_capacity.py. AddressF1 first completes its8priorsteps (97+36+bothQ40) then stops before any hot-capacity DUT execution. Original script/receipt/log are preserved in failures/boundary_cli_argument_0209. The wrapper is corrected; already-started wrappers are observed until that exact argument failure and resume only the two missing tail tests in separate receipts. No RTL or nativebatch is restarted, no capacity pass is inferred.


## 02:27 UTC：宽载荷选择器独立候选

中央共享通道grant版本实际综合227188LUT，完整32核布线日志已报告局部SLL拥塞。新增默认关闭的`DATA_ONEHOT`候选，以已有one-hot仲裁结果驱动固定索引AND/OR平衡树，选择请求/返回的宽载荷；不改变优先级、ID、FIFO或寄存器边界。`fabric_onehot_a`独立RTL/模型验证和`central_onehot_a`相同33×32同步上下文综合正在运行。仅有测试/综合结果支持时继续集成，当前完整核和模型均未启用此候选，不能转移既有校准或频率。


## 02:30 UTC：地址前移8核时钟与32路边界

`many8_address_context_a`全部331690条可布线net已完成且无routing error；8ns STA setup +0.799ns、hold +0.001ns、pulse +3.458ns，12类check_timing均为零，实际234657LUT/155130FF/368BRAM36+120BRAM18。最坏路径转到bank5 state response RAM至data RAM，11级逻辑、路由占73.731%。5ns仍−2.201ns，保留失败；125MHz只绑定此8核的27个冻结RTL文件、有效参数及97+36项独立校准。

地址前移32路F1的两个Q40及8192恰满/8193显式拒绝均已完成，并与独立模型全周期一致。最初批处理遗漏模型参数的失败记录保留，修复只执行缺失尾项。旧REQUEST_STAGE0 F0的BNN/LSTM真实40batch分别596009195/606848449cycles，完整输出与native ALT一致；逐wave工作审计正在进行，不能将其与REQUEST_STAGE1 F1直接归因为单一cache收益。


旧REQUEST_STAGE0的完整F0逐wave工作/容量/ACK审计已通过。与相同R0、相同输入/内存假设的F1比较，BNN/LSTM F0/F1周期比约2.090/2.067，内部流量分别85.843→75.475GB、87.488→77.032GB。此处是模型周期消融，未赋予任何FPGA秒数；F0仍有有限读写/ACK和state cache，F1额外具有proposal owner缓存及miss合并。F0的owner停顿计数仅同node冲突，F1计全部dispatch阻塞，二者不能直接按同定义相减。新REQUEST_STAGE1 F0仍在运行。


## 02:45 UTC：FP32修复完整8核资格

`many8_checked_context_a`实际布线完成，331839条可布线net全部完成、零routing error。8ns下setup +0.469ns、hold +0.010ns、pulse +3.458ns，12类check_timing均零；实际234904LUT/154972FF/368BRAM36+120BRAM18。27个冻结RTL文件、有效参数及新的97+36项校准已绑定。最坏路径是bank6 owner请求FIFO RAM到MSHR候选RAM，17级逻辑、72.519%路径延迟为布线。单独FP32单元时序改善没有转化成完整8核更高的合格频率；新旧address/checked版本均仅证明125MHz，200MHz负结果保留。完整32核仍在布线。


## 03:10 UTC：宽载荷one-hot候选的资源负结果

`DATA_ONEHOT=1`中央33×32单元通过33000笔事务、21492个完整周期及同时非法ID17/63、sticky error和reset恢复的独立差分。相同实际同步上下文的最终综合为413842LUT/100412FF，无BRAM/URAM；相较直接one-hot握手但原载荷MUX的227188LUT，增加186654LUT（82.16%）。5ns综合setup从−0.259改善到+0.198ns，hold仍−0.074ns；综合正setup不能称为200MHz合格。

此候选未达到减少中央互连资源压力的目标，停止其单元布线和完整32集成。保留全部正负证据及默认关闭参数，不发布未做过的完整32资源估计或频率。已在运行的完整核保持原载荷MUX；此决定仅针对该one-hot宽载荷实现，不是全体互连或FPGA研究的no-go。证据见`timing/central_onehot_a/candidate_review.json`。


03:28 UTC：最新checked32的F0尾项也通过，F1/F0均完成各自97项、36组固定纳秒和四项Q40/容量边界的全部周期/输出/流量核对；同模型完整native40工作审计与ALT身份已通过。四份原始批处理脚本失败记录仍保留，四个tail-only恢复记录均passed。当前尚缺对应完整核路由与时钟资格，绑定工具继续输出null秒数。


## 03:58 UTC：由完整32布局路径触发的候选路由修复

F0完整32布局诊断（独立DCP副本，不改正在运行的实现）显示SLR1 CLB占99.73%、LUT占90.49%，存在level7拥塞；最坏路径由front10的valid，经候选路由ready链到front11的使能，16级、8.914ns，其中7.570ns为估计布线。布局setup +0.507ns、hold −0.304ns且1,249,360条net未布线，只是诊断，不能赋予100MHz。14份诊断文件已校验归档。

`parallel_router.sv`现以每输入的one-hot grant/ready归约代替循环可变索引写入，保持原payload MUX、轮转优先级、64-entry FIFO和全部拍边界。四种8/32输入、8/32输出与96/118bit载荷配置各100,000周期的XSim差分及独立有限队列/串行仲裁核对通过，共3,106,952项接受；复位明确丢弃在途队列，收发守恒单列。32→32稳态连续9,487周期各接受32项，所有配置实际达到64项FIFO容量。新旧单元的周期和吞吐完全一致，此修复目标是缩短物理ready路径。新完整8核及OOC已启动；旧完整核路由继续，原模型必须经过新完整拓扑校准才能绑定。

此前checked32的F1/F0另已通过各18项10ns固定纳秒补充校准，与原冻结可执行文件hash一致；仍是显式同步外存假设，不是100MHz或HBM实测。


04:15 UTC：路由ready修复的完整8核97+36+两项Q40全部通过。实际综合235072LUT、154722FF、368RAMB36+120RAMB18；5ns setup−0.346/hold−0.080，算术数据路径仍最坏，未获得更高频率结论。完整8路由04:13:16启动；从已通过门槛启动新完整32F1/F0独立97+36+容量校准及10ns目标综合，分别04:14:37/35。原完整32实现与全部负结果保留。

## 04:44 UTC：完整32路F0的实际路由负结果

`many32_f0_checked_context_10ns_a`于04:43:13完成失败退出：`Route 35-3`全局拥塞等级7，timing congestion等级8，4,346,963个routing node overlaps。工具显示的0个unrouted/partially routed nets不能抵消这些非法重叠。运行状态为`route_design ERROR`，后续STA资格脚本正确拒绝继续，没有频率或模拟秒数。冻结错误DCP SHA256为`8402c3ca977a92ee24850814ef4dafd0d21982277ea84033815e480c218479c2`；完整日志绑定见`timing/many32_f0_checked_context_10ns_a/route_failure_0444.json`。独立会话正从副本导出只读诊断，原工程不重置。该负结果绑定旧checked F0结构及实际布局，不能扩展成其他架构的no-go。新ready链F1/F0候选继续独立验证；目前不声称它已解决整体拥塞。

默认失败后启动了同一综合网表的独立`impl_spread_a`：本机2022.2确认的`Congestion_SSI_SpreadLogic_high`策略，实际`SSI_SpreadLogic_high`布局和`AlternateCLBRouting`路由。依据是已测SLR1 CLB99.73%及全局拥塞7，而不是任意频率扫描。04:47:52启动；保持10ns约束、同一synth_1及全部功能边界，原impl_1不重置。综合网表SHA256 `f7f0f31981650a9a758c4bc41936b8bc51c9ed05f73444be8f49a97b2e256885`与精确run属性记录于`routed_sta_spread_a/implementation_binding.json`。此物理候选尚在执行，不预设成功，也不转移给F1或新router RTL。

04:55补充：新`many32_router_ready_a`完整97项RTL/独立模型校准全部通过，周期、输出、每数组流量、阶段和吞吐直方图一致，modelC可执行文件SHA256 `839e18598582680bc2c02a83751f5578501264fde82eecaa5372c8e8a9c73acf`。固定ns36和四项容量边界仍在执行，尚不提前发布完整native候选绑定。失败F0的错误DCP只读`route_status.rpt`显示1,249,397条routable nets中37条fully routed、1,249,360条unrouted；不能用路由过程中的临时计数声称完成。

05:17状态：新router32 F1已通过97项和36组固定ns校准，四项容量边界继续；F0已通过原生小图、91fixtures和两组压力，4M地址用例继续。F0实际综合完成947,951LUT/551,507FF/1064RAMB36+296RAMB18+288URAM，10ns综合setup+4.590ns、hold−0.080ns；未赋予频率。

完整模型新增有依据的gap单因素敏感性：保持modelC同一可执行文件、16-cycle基础延迟、32共享物理端口和原生40-sample不变，分别执行gap1与gap4的BNN/LSTM，共四个完整batch。已有gap2在该延迟下接近条件吞吐上限，因此该对照用于分离延迟与端口服务间隔；不是参数笛卡尔积、板测或任意频率扫描。当前正在执行，输出/工作/容量/ACK/native身份审计仍待终态。

## 05:30 UTC：共享通道单元的实际物理负结果与后续

`central_reduction_a`默认route于05:11:43结束，实际状态为`route_design Complete, Failed Timing & Nets!`，并非合法布线完成。180,716条routable nets中118,022条完整布通，62,694条存在资源冲突；DRC报RTSTAT-13。5ns下setup−12.343ns、hold−0.038ns，最坏bc到rd数据路径17.146ns，其中16.476ns为布线，8个逻辑层级。实际资源223,763LUT、100,478FF。原STA guard正确拒绝该状态；已有v2脚本不再执行扫频，因为非法路由和hold不能通过改周期修复。74文件归档`completed_central_route_failure_0527`已校验。

这提供了宽载荷MUX布线瓶颈的新依据，因而重新推进已完成独立功能/错误测试的`central_onehot_a`实际单元route（05:30:30启动）。先前413,842LUT、相对matched grant综合增加82.16%的面积负结果原样保留；全部冻结源码和原证据重新hash核对。此候选也含较新的direct-grant修复，不能把它与旧reduction单元的物理差异全归因于one-hot载荷。默认RTL仍DATA_ONEHOT=0，未集成到完整32核，也没有时钟或性能声明。


## 05:56：32-owner / 8共享通道完整候选

中央33×32单元的62,694条路由冲突、完整32 F0默认route拥塞失败，以及布局SLR的CLB压力，构成减少中央交换范围的实际依据。新增`many32_p8_router_a`，保留32个owner、8192成员/changed容量、4M状态backing、真实batch与全部ACK；物理端口改为8个，每端口64ID，地址按line_mod_8分配。该变体仍有多候选并行路由，所有数组竞争同一有限物理服务。

此变化在相同每通道gap下使总接收能力降至原来的四分之一，可能降低完整batch吞吐。新的97项、36组固定ns、4个容量边界、独立模型和真实完整batch必须重新验证，不能沿用P32流量或时间。05:56已启动实际完整核综合及RTL/模型构建；没有资源、频率或性能结论。原P32候选继续收集实际实现结果。依据与冻结参数见`analysis/ports8_candidate_decision_0556.json`，源/参数绑定见`timing/ports8_binding_0557.json`。


## 06:01：新router完整8核完成125MHz资格审查

`many8_router_ready_context_a`的328,548条可路由net全部布通，错误为0。5ns setup −1.859ns未通过；同一实际网表8ns重新STA为setup +1.141ns、hold +0.007ns、pulse width +3.458ns，12类check_timing均为0。已检查重复同源时钟约束提示、实际BUFG位置提示和只涉及32个终端signature输出的RTSTAT-10；DUT接口终止于真实同钟寄存器，无false/multicycle例外。新97项、36组固定ns、两个Q40和冻结源/参数绑定均通过。

资源为234,392 LUT、155,114 FF、368 RAMB36和120 RAMB18，包含同步上下文开销。最坏路径转移到bank2前端FP32的parent至pair，25层逻辑、6.735ns数据延迟，其中4.673ns是实际布线。合格档仍为125MHz；没有声称完整核频率超过旧checked8。该资格严格限于L8/P8、MC1024/CC512配置，不能传递给L32/P32或L32/P8。见`timing/many8_router_ready_context_a/routed_sta_v2/qualification_review.json`。

`analysis/resident_checked_0600.json`及同名CSV将已绑定的六个F1、两个F0完整batch与新prepared CPU/basic/compact软件实测分别列出。8个完整模型行的FPGA秒数和全部软件/FPGA比值均为null，因为这些完整32核尚无合格时钟；模型主机耗时和native E2/Process未作为resident分母。该表是旧checked候选的可追溯汇总，新的P32/P8变体将分别生成新绑定。


## 06:27：新P32 F1完成全部并发域校准和native身份绑定

`many32_router_ready_a`通过完整97项、36组固定ns、18组10ns及4项Q40/8192容量/8193拒绝校准，逐周期、全部输出和报告的流量/阶段均与独立模型一致。8193用例的RTL和模型都返回非零错误且无output，负结果按预期核验。`analysis/router32_bound_0627.json`绑定至同一可执行文件`839e18598582680bc2c02a83751f5578501264fde82eecaa5372c8e8a9c73acf`、27份冻结SV及L32/P32/MC8192/CC8192/U1/R1/F1参数。既有三档延迟的BNN/LSTM完整40batch及native ALT身份因此可复用；没有重跑相同模型、没有使用旧校准替代新并发路径。完整32核物理实现仍在运行，六行模型秒数继续为null。


## 06:51：P8完整核综合完成并进入实际实现

`many32_p8_router_context_10ns_a`实际综合为920,818 LUT、560,586 FF、1064 RAMB36、328 RAMB18和288 URAM；BRAM tile等效1228/2016，URAM288/960，LUT920818/1303680。相对于对应新P32 F1，LUT少158,882、FF少47,202，RAM数量相同；27份核心SV完全相同，差别来自PHYS32→8及相应同步上下文宽度，不能把总差额解释为某一个模块的纯资源成本。

10ns综合后STA为setup +4.590ns、hold −0.080ns、pulse +4.300ns；最坏setup是bank0前端FP32 parent至pair的26层逻辑，5.255ns估计数据路径。综合结果不授予频率。原XDC在综合时已解析/应用，post hook在空clock查询后重新加载相同冻结XDC，保存的时钟/时序报告对应10ns。47文件完成归档并核验；06:51:20已经启动完整impl及5/8/10ns实际网表STA流程。

P8已独立通过97项和18组10ns校准，固定ns36及四项边界继续执行。其完整小图d3/d4周期为104,587/203,964，对应P32为104,440/202,122；这是共享同一小图输入的完整batch周期，不能推断4M真实batch的端口瓶颈。见`analysis/ports8_vs32_small_0637.json`与`timing/many32_p8_router_context_10ns_a/synthesis_review_0651.json`。完整P8 native40尚未运行，不借用P32的流量或时间。


## 06:58：新P32 F0完成并发域校准；P8进入容量门

新F0的97+36+18+4全部通过；8192完整输出和8193明确拒绝、无输出行为均正确。`analysis/router32_F0_bound_0658.json`将两个已有真实40-sample完整模型结果绑定到本次冻结源与参数。新的`analysis/resident_router32_0658.json`及CSV包含F1六行、F0两行；对应完整核尚未获得合格时钟，所有FPGA秒数、软件/FPGA比值仍为null。

P8另已通过97+36+18，正执行四项容量/完整batch边界。该配置后续必须运行自己的真实完整batch及内存敏感性：固定gap2下16/60/120周期基础延迟，以及16周期延迟下gap1对照；每项均为BNN/LSTM各40sample。这样检验减少端口后的延迟与带宽影响，不借用P32的流量或结果，也不做全部参数笛卡尔积。当前这些P8大图运行尚未启动。


## 07:22：新P32 F0布局诊断与证据快照

从正在运行的K实现中只读复制完整placed DCP，并在独立A会话生成报告；源与副本SHA均为`d13ea5f5ec450b885a8aa4e465c13433f07dc23a83c479a450ffefc8188cb7a1`，未修改原实现。10ns估计setup−2.601ns、hold−0.317ns、pulse+4.300ns；1,252,808条可路由net中1,252,781条尚未布线，27条显式gap。因此不是可用频率证据。

最坏数据路径由bank4 metadata valid，经cell-router仲裁/输出FIFO ready到bank25 metadata旋转CE，9层逻辑、11.837ns估计数据延迟，其中11.205ns（94.661%）为估计布线；数据路径三次跨SLR。SLR0/1/2的CLB占用96.19%/99.83%/86.45%，最大拥塞等级7。相对旧checked F0的较少逻辑层级不能解释为时序已改善：网表、布局和最坏路径都不同。继续已启动的P8减少物理交换范围候选与原有实际路由；15份诊断文件见`completed_router_F0_placement_0722`。

`checkpoint_20261113T0700`的4,262份新增文件已冻结并校验；连同前序共95,142份文件、16个快照。P8运行中的RTL和当时未结束的gap1/gap4原始记录明确延后归档，不将中间文件作为最终结果。gap1两个真实40batch现均已完成并与native ALT全部输出一致，工作/容量/流量的独立审计仍在运行。


## 07:25：gap1完整batch带宽敏感性

同一P32 modelC可执行文件、原生40batch输入、seed1729、基础延迟16cycle和有限资源下，仅将物理端口最小接收间隔由2改为1。BNN/LSTM完整周期为145,758,496/149,850,247，相对gap2的180,141,407/184,018,993减少19.0866%/18.5681%。内部流量分别75,587,946,528/77,152,373,792字节，减少0.3967%/0.3794%；该小幅流量变化来自并发时序变化，不能假定不同gap的缓存行为完全相同。

两项均通过全部输出、工作总量、逐wave无重复changed提交集合、容量和全部ACK排空审计；新router97+36+4与源/参数绑定见`router32_gap1_bound_0725.json`。本次记录为假设外存下的架构周期结果。`resident_router32_0725`汇总10行完整模型与现有软件实测，完整32核仍无合格时钟，FPGA秒数和比值全部为null。

固定本次流量、映射、同步服务gap的条件筛选下，最少传输周期为73,960,329/75,745,819；匹配已测prepared GPU均值仍要求约472–487MHz。这仅是忽略依赖、仲裁、延迟、控制和排空的必要条件，不是可实现频率或总体no-go。改变缓存、布局、工作量或物理服务后必须重算。gap4及独立P8仍继续执行。


## 07:40：完整输入身份再核对

`analysis/current_large_input_identity_0740.json`将当前BNN/LSTM workload、prepared CSR和golden逐文件重算SHA，与既有冻结生成清单全部一致。新增运行的`run_large_model.py`在启动模型前重复这些检查，并将prepared文件、生成回执及runner哈希直接写入本轮回执；不改变RTL、模型可执行文件、内存合同或计时边界。历史回执不改写，此次当前文件核对不冒充过去运行时的新测量。P8完整batch仍等待独立容量门。


07:43证据补记：`checkpoint_20261113T0726`新增48文件，2,894,508,908原始字节、799,506,595归档字节，已通过全链逐文件SHA核验（95,190文件/17快照）。其中包含gap1两项完整提交/阶段/流量/输出记录；P8与gap4运行中的日志继续明确延后。P8最大cell Q40 RTL已单次启动完成40sample、1,889,264cycle、输出完全一致，其余边界仍在执行。


## 08:06：新P32 F1布局诊断完成

独立J会话读取已复制的placed DCP，输入SHA为`4b818b80863c696fb2075acfcf24f44e9b569fe5c1834fe024097a0f96f4c054`，原F实现继续运行。10ns估计setup−1.973ns、hold−0.338ns、pulse+4.300ns；1,405,256条可路由net中1,405,217尚未布线、39条显式gap，12类check_timing为0。实际placed资源1,070,543 LUT、608,190 FF、1064 RAMB36、328 RAMB18、288 URAM。SLR0/1/2 CLB占用97.47%/99.96%/98.75%，最大拥塞7；最坏路径从bank12前端候选经router仲裁/ready至bank26前端position，12层逻辑、11.394ns估计数据延迟，10.496ns估计布线（92.119%）、数据跨SLR五次。此为未布线估计，不能授予频率。15文件归档`completed_router_F1_placement_0806`已完整验证，作为同核心F1 P8布局的后续对照。

## 08:07：P8独立并发域门通过，完整大图运行已启动

`many32_p8_router_a`与独立模型通过97+36+18+4全部校准。两个Q40 RTL分别1,889,264/1,528,133cycle，单次启动完成40sample、全部输出一致；8192热点接受用例覆盖1,048,577节点地址、955,453cycle，8193用例按预期显式拒绝且无输出，均与独立模型逐周期相同。四项边界另行重放也全部一致。证据索引为`analysis/ports8_complete_calibration_0808.json`。

现已启动P8自身的四组native40：基础延迟/最小服务间隔为60/2、16/2、120/2、16/1 cycle，每组BNN和LSTM各40sample，共8个完整batch。每次启动均再次验证workload、prepared CSR、golden和模型可执行文件身份，回执已记录。八项目前仍运行中；不借用P32流量、输出计时或时钟，也不以进度日志作为完整性能结果。P8物理实现和只读布局副本捕获继续执行。


## 08:17：one-hot共享通道单元取得合法布线，时序审查继续

`central_onehot_a`的实现子进程08:13:36正常退出，468,494条可路由net全部布通、错误为0；实际资源414,660 LUT、100,427 FF、无BRAM/URAM。5ns最终setup−6.302ns、hold+0.001ns、pulse+1.968ns，因此没有5ns频率资格。父会话仍执行同一实际网表的5/8/10ns STA，尚未完成最终审查，见`route_stage_review_0817.json`。

该单元解决了本版本的路由合法性，但保留先前相对matched grant综合面积增加82.16%的负结果；与旧reduction单元比较还混入较新的direct-grant修复，不能作纯one-hot收益归因。默认完整核仍DATA_ONEHOT=0，未将该大面积单元集成到完整32核，也没有传递其单元时钟。


08:26证据补记：`checkpoint_20261113T0808`新增1,220文件，793,258,651原始字节、105,704,156归档字节；全链96,410文件/18快照SHA校验通过。P8完成的RTL原始记录已包含，10个仍活动的native batch明确延后。原worktree HEAD、main、全部tracked文件状态及11个受保护指导/压缩文件复查不变，见`protection_0826.json`。A已启动P8布局副本的只读诊断，原H实现继续；其结果仍待完成。


## 08:40：one-hot单元80MHz OOC资格

冻结源、参数C33/P32/DATA_ONEHOT1、33,000合法混合事务及错误ID/reset恢复的功能证据均重核一致。5/8/10ns的实际STA setup分别−6.302/−3.302/−1.302ns，hold均+0.001ns，失败保留。同一已布通网表明确补测12.5ns，setup+1.198、hold+0.001、pulse+5.718ns，468,494条net全部布通，12类check_timing零。已审查同源clock替换XDCC-4/8、BUFG固定位置CLKC-3及仅32个terminal signature输出的RTSTAT-10；无false/multicycle例外。仅这个真实同步上下文单元取得80MHz资格，并非最大频率证明，不能转给完整32核、内存控制器或板卡。

实际414,660LUT/100,427FF，之前matched综合面积增加82.16%的负结果保留。最坏路径request FIFO read_data至local_id，8层逻辑、10.903ns数据路径，9.950ns实际布线（91.259%）。完整核默认DATA_ONEHOT仍0。`routed_sta_12p5_0829/unit_qualification_review.json`及133文件归档`completed_central_onehot_route_0840`完成核验。

## 08:43：P8布局与同版本P32 F1对照

P8只读placed DCP的源/副本SHA为`e9f21516f4afe65a9fed43d70ca344cc0eb3599b28986a96baa7375c56521f53`；10ns estimated setup+0.506、hold−0.268、pulse+4.300ns。1,294,651条可路由net中1,294,605尚未布线、46条显式gap，所以不是频率资格。最坏路径仍是跨bank候选路由ready链，10层逻辑、9.117ns估计数据路径、8.267ns估计布线（90.677%），数据三次跨SLR。

实际placed资源912,018LUT/562,128FF、1064RAMB36+328RAMB18+288URAM；相对P32 F1少158,525LUT、46,062FF，RAM数量相同。源/参数检查确认27核心SV相同，只有PHYS32→8；同步上下文宽度变化也包括在资源内，不能将总差额当成单个模块纯成本。SLR0/1/2的CLB占用从97.47/99.96/98.75%变为82.85/99.71/96.93%，SLR2↔1、1↔0连线使用率从70.02/51.83%变为62.49/29.66%。最大拥塞等级仍7，热点转到候选router区域。`analysis/ports8_vs32_placed_0843.json`记录该限定比较；15文件只读归档完成。原H已进入实际路由，P8八个native40模型仍在运行；正setup估计不替代最终setup/hold、路由完整性和约束审查。


## 09:08：P32 gap4完整batch与内存敏感性收尾

基础延迟16cycle、最小接收间隔4cycle的BNN/LSTM全部40sample分别完成331,787,140/337,525,148cycle、76,367,574,304/77,956,147,712内部字节。与同模型、同输入、同seed的gap2相比，周期为1.841815/1.834186倍，流量为1.006306/1.006584倍；每wave提交集合、候选及changed总量不变，全部输出、容量和ACK审计通过。gap4平均发射3.878804/3.879749候选每周期，提交0.314090/0.314469节点每周期，分母包含全部resident工作。

`analysis/memory_sensitivity_P32_completed_0907.json`现汇总五种内存条件、两张图共10个完整F1结果：16cycle下gap1/2/4，以及gap2下60/120cycle。分析器重算实际输入和输出SHA并要求同可执行文件、拓扑、seed和逐wave提交集合；它不改变模型，不赋予频率。此前八条完成结果已与旧gap1/gap2比较逐项核对。新结果绑定见`router32_gap4_bound_0907.json`，合并F0后的`resident_router32_0907`有12条架构模拟结果，全部FPGA秒数及软件/FPGA比值仍为null。

固定本次逐通道流量和gap4合同的必要传输周期为298,888,633/306,165,213，仅用于该条件筛选；不得作为FPGA实际性能或其他结构的上限。八个P8完整batch及八个完整核物理实现仍在执行。原始终态trace将在后续增量快照归档，原80MHz one-hot单元资格不传递给完整核。


09:28证据补记：`checkpoint_20261113T0909`新增56份原始文件，2,895,182,371原始字节、802,413,160归档字节；全链96,466文件/19快照SHA核验通过。gap4的完整commit/phase/traffic/output证据已包含，八个P8仍活动的batch明确延后。`protection_0919.json`再次确认原worktree、main及11个受保护文件不变。P8终态监督流程已启动，仅等待现有运行，再顺序执行完整工作、native身份及精确绑定；失败保留现场，不重复启动实验。


## 10:44：真实完整batch的有限外存布局核对

P32/P8冻结harness的同一地址布局、真实workload/prepared header及完整job/output事务核对后，BNN/LSTM backing分别为1,605,730,304/1,631,147,264 bytes（约1.495/1.519 GiB）。其中proposal为32,825,344/33,341,440 bytes，128bit node-state为65,642,496/66,674,688 bytes，40sample的type/cell metadata为1,313,013,760/1,333,657,600 bytes；其余包括CSR、prepared edges、cost、job表和完整输出缓冲。LSTM最后不足整32B行累计640 bytes padding也已计入，输出写事务与完整结果一致。

这些是`std::vector<Line>`实际分配公式及输入header推导出的有限设备backing容量；每笔接受地址都有边界和`line mod P`映射检查。它们不是板测容量、片上RAM数、运行时流量或零延迟存储模型，也不含host oracle/snapshot容器。每类区域的起止行、padding、8/32物理端口容量分配、输入及冻结driver SHA见`analysis/native_backing_layout_1044.json`；复现工具为`sim/analyze_backing_layout.py`。不改变任何运行中的RTL、模型、输入或周期。


## 11:11 UTC：旧完整32核布线负结果和报告解析修复

`many32_context_reduction_b` 的子进程于10:56:31退出，最终状态是 `route_design Complete, Failed Timing & Nets!`。1,392,311条可路由网中1,258,054条已完整布线，134,257条存在资源冲突，仍有276,497处node overlap；RTSTAT-6为Critical Warning。实际5ns报告setup −22.325ns、hold −0.088ns、pulse +1.800ns，12项check_timing均0不能弥补非法路由。实际资源1,078,639 LUT、607,495 FF、1064 RAMB36、296 RAMB18、288 URAM。父级STA门禁退出1，未执行8/10ns；不从负slack推导可用频率。完整原始报告、32份冻结源码和DCP hash已记录于 `timing/many32_context_reduction_b/completed_route_rejection_1102.json`，76份紧凑归档逐文件校验通过。新P32/P8实现继续，旧候选的失败不扩展为整个研究结论。

检查这份真实报告时发现机械报告解析器的严重性列仅匹配单词，会漏掉 `Critical Warning`。已改为保留整个表格单元并按原allowlist拒绝未知/严重规则；没有放宽资格。旧完整核仍被独立的路由计数、setup、hold和父级状态检查拒绝，原结论未错误升级。新解析器在真实RTSTAT-6报告、13份既有合格报告、2个既有失败频点上复核，全部符合预期；原报告和资格文件均保留，没有重跑RTL或Vivado。回归入口为 `analysis/routed_rule_parser_regression_1101.json` 和 `analysis/routed_rule_parser_real_negative_1101.json`。

早期owner单元使用独立手工格式，另在 `analysis/legacy_owner_rule_parser_audit_1133.json` 补查实际报告：8ns setup/hold/pulse为+1.242/+0.006/+3.458ns，9911条可路由网全部布线，DRC仅签名输出的RTSTAT-10，12项约束检查均0。它不属于上述13份自动资格报告，也没有取得新的完整核资格。


## 12:11 UTC：P8首组真实完整batch及同条件通道数对照

32 owners/8共享物理通道的16-cycle延迟、gap1配置完成BNN/LSTM各40个sample，一次start，完整输出与既有ALT一致。逐wave唯一提交集合、全部工作量、容量、初始化/cost/job/output流量和全部ACK检查通过，native身份及本版本97+36+4绑定完成；另外18组10ns校准已在此前通过。对应证据为 `analysis/p8_large_l16_g1_bound_terminal.json` 及其引用的原始结果。完整核实际路由仍在执行，模拟秒数不发布。

| case | P8完整周期 | 内部流量(GB) | 发射/完整周期 | 提交/完整周期 | P8/P32同条件周期 |
|---|---:|---:|---:|---:|---:|
| BNN | 359,062,210 | 76.457 | 3.584162 | 0.290231 | 2.463405 |
| LSTM | 366,543,747 | 78.048 | 3.572596 | 0.289573 | 2.446067 |

观测发射峰值21/22、提交峰值15/15；这些峰值不替代上表完整batch平均服务率。成员/changed峰值BNN6892/6863、LSTM6986/6982，均不超过8192；owner及state MSHR/dirty峰值均32/16。每数组流量、阶段周期及实际容量记录见 `analysis/ports8_vs32_complete_large_l16_g1_terminal.json`。

该对照重新核对27份相同RTL、两侧冻结模型/宏、实际输入哈希、逐wave工作集合和完整输出。唯一历史模型源码差异在未实例化的F0类方法中，两侧TILE_CACHE=1均选择OwnerCycle；允许项绑定到这两个确切版本，未泛化豁免。每通道仍64个ID，因此端口数下降同时使总物理credits从2048降为512，不能将对照解释为只减少数据引脚而保持总服务能力。P8内部流量较P32增加1.149%/1.160%；资源减少和周期增加分别记录，未推断更快的完整核时钟。

固定这组已观测逐通道流量和gap1合同，条件最早传输界为298,851,543/306,336,337cycles；追平新basic/compact GPU均值的必要频率约1907至1969MHz。此筛选省略响应、依赖、控制及排空，只适用于固定流量和合同，不是FPGA频率或性能结果，也不是所有新结构的no-go。见 `analysis/traffic_screen_P8_large_l16_g1_terminal.json`。新的resident表 `analysis/resident_with_P8_gap1_1208.json` 包含14个完整模型行，所有FPGA秒数和比值仍为null。


## 12:20 UTC：同一旧checked F0综合网表的SSI重试失败

独立 `impl_spread_a` 使用 Congestion_SSI_SpreadLogic_high / SSI_SpreadLogic_high / AlternateCLBRouting；保留默认impl_1失败。此次重试因Route35-3339局部SLL需求及Route35-368全局拥塞结束，父级STA门禁退出1，没有执行计划的10ns频点。日志中SLR1/2路由需求估计30,506、可用23,040（132.40%），最大局部列200%；这与最终placed网表的SLR连接数量是不同统计量。

冻结错误DCP后，在独立空闲会话只读生成报告：1,250,752条可路由网中仅35条完整布线，1,250,717条未布线，RTSTAT-13为Critical Warning。报告中routing errors=0及utilization页的Routed标题不能证明合法布线。实际placed资源937,605 LUT、552,323 FF、1064 RAMB36、296 RAMB18、288 URAM，三个SLR的CLB占用87.11%/99.90%/95.96%。原错误DCP、副本及32份冻结源码hash已重新核对，没有改原run或约束。

完整审查见 `timing/many32_f0_checked_context_10ns_a/failed_spread_diagnosis_1205/review.json`。61份run文件和13份诊断文件分别归档于 `completed_SSI_retry_run_1220` 与 `completed_SSI_retry_diagnosis_1220`，逐文件校验通过。本固定网表两种物理策略均失败；新router/P8结构的独立实现仍在执行，没有从此失败赋予全局no-go结论。
