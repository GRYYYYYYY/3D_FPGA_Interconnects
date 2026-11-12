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

已检查旧basic/compact CUDA：expand仍运行时eligible判断，confirm在闭合点扫描settled，不是prepared CSR+POP在线归约的等价优化实现。原GPU V2结果保留；新的通用变换CUDA对照仍待实现/测量，不能给旧结果改名。

## 尚未完成

- m2c/m3d/m3e 综合正在执行。m3c 多写位置导致 RAM 推断失败；m3d reducer 映射 LUTRAM，改为显式读/写端口后单元实际为7 RAMB36+1 RAMB18，XSim通过。m3d又报告浮点 CARRY8 timing loops并自动disable timing；不能据此获得完整频率资格。单赋值算术修复通过500000次FP32位精确加法，单元综合待核验。全部负结果保留。
- 完整 tile routed OOC、真实 setup/hold 闭合仍未完成。
- 32/64 topology、有限分层汇聚及候选完整核资格仍未完成；开始验证5-client/1-uplink和33-client/32-physical-port单元。
- BNN/LSTM 完整 40-sample 有限架构仿真、新完整候选 OOC；目前只有 M1 功能结果，不得当成硬件性能。
- 通用表示变换 CPU/CUDA 对照及 native 身份/回接。已有 GPU V2 和 R1 证据复用，不申请新 GPU 补测。

配置在 `accel/lookahead/fpga_sparse_stream_r2/config/experiment_spec.r2.yaml`；逐项状态在 `results/fpga_sparse_stream_r2_20261112/checkpoint.json`。所有失败版本、源代码快照、周期日志与工具日志留在本轮 results。尚未声明 FPGA 胜过 CPU/GPU，尚无 board measured 结果。


R2 continuation 18:15 UTC (in progress): mapped arithmetic feedback was removed using single-assignment normalization/rounding. The isolated pair_lane routed at 200MHz with WNS +0.077ns and WHS +0.020ns, zero timing loops; OOC clock-source/partition-pin placement warnings remain, and this is not full-kernel qualification. M3d actual synthesis:735949LUT,170150FF,300RAMB36+153RAMB18. M3e explicit reducer ports:589685LUT,167533FF,356RAMB36+161RAMB18. Both retain48old-FP mapped-loop warnings and cannot supply a frequency claim; routing these obsolete candidates was skipped and their evidence retained.

external_d bitmap RAM passed97complete RTL/model-trace comparisons; Vivado parser rejected a mixed initialized/uninitialized net declaration at external_bank.sv:47. external_e only separates those declarations and is synthesizing. external_f also records write-buffer dependencies at MSHR admission, clears them on ACK, and replaces rotated-index arbitration with fixed-index balanced selection. The scoreboard is checked against all original address guards every RTL clock. Owner warm/stress and node-state complete traces remain exact;95complete small/pressure traces are exact, and both64K/4Maddress regressions pass. Complete f OOC is running. No complete-tile frequency is yet qualified.

New software measurements are independent of oldGPU V2, which remains unchanged. `software/prepared_pop_gpu_b` has91fixtures x2CUDArepresentations and4native inputs x3processes x(1warmup+3measurements), plus8-thread CPU on the same H100worker. All218process receipts pass and output bytes match. BNN/LSTM compact CUDA V2 means:0.151799969444/0.160247990444s; basic CUDA:0.156690577111/0.159888578444s; same-worker transformed CPU:4.534045816222/4.623006792333s. Original failedgpu_a is retained:91fixtures and smallnative passed; missing largepreparedCSR file prevented any large timing. The corrected worker preflights files, loads separately bound prepared CSR, and checks eligibility reconstruction.

This tighter software baseline excludes a fixed32-lane<=200MHz candidate with unchanged edgework and one candidate/lane/cycle even before initialization/commit/memory. It does not exclude changedwork/higher-frequency/wider structures. Actual hierarchy is now coded: five bounded clients per owner ->one64taguplink->shared physical ports; parameterized many_tile has8reducer banks and bounded8192member/changed entries per32-owner. Modules and complete8/32topologies are being independently calibrated; no8-lane calibration is claimed for32. Full BNN/LSTM architecture simulation, complete-kernel timing, F0/F1 large-state ablation, and native timing-scope audit remain pending.

18:20 continuation: composed161client/32physical fabric passed161000transactions at96775cycles with every cycle equal to its independent model. many8_b integrated topology passed95cases exact to many8_model_a; native cycles48873/135753. Full32RTL compilation/calibration remains in progress. The actual8192-entry bank synthesized13989LUT,8416FF,57RAMB36+15RAMB18. Vivado confirms2016BRAM36equivalent and960URAM available onxcu280:32banks alone require2064BRAM36equivalent, so the all-BRAM fixedcandidate cannot fit. A separately frozen USE_URAM version moves large directory/member/free/changed arrays to URAM; inference and implementation are pending, not presumed.
