# R6.2 后恢复 FPGA 仿真与模块 OOC 实验

日期：2026-11-12。用途：直接交给服务器 Codex 执行。

本文件依据用户上传的 `FPGA_Quick_Validation_Templates_20261108.zip`，修正此前把真实板卡、已安装 shell 和实测随机 RMW 服务作为硬件研究统一启动门槛的做法。本包是新任务合同和设计建议，不包含已经执行的新 FPGA 结果。

## 0. 明确授权与研究目标

用户已完成摘要注册，现在明确要求继续 FPGA 加速方法与实验，允许不使用实板。恢复独立的 RTL/HLS、模块 OOC 和有限资源架构仿真轨道。

研究目标仍为：在同任务、明确语义和同计时范围下，争取 FPGA 优于基础 GPU、优化 CPU、原 VPR 多线程等基线；GPU 与 CPU 不要求排序。该目标不预设必然成功。

实验验收与性能目标分开：首先交付正确可执行的硬件原型、真实 RTL 周期、资源/时序和有限模型；是否达到优势由结果判断。不能要求先有板测随机 RMW 或先证明完整大图必胜，才允许写第一个 RTL 服务单元。

本次明确允许新增必要的 CPU/GPU 同范围计时、HLS/RTL/OOC、候选事务重放和闭环架构模拟。之前“论文整合任务不启动新实验”的限制只适用于该论文任务，不用来阻断本次用户重新授权的 FPGA 工作。

### 基点与隔离

- 仓库：`https://github.com/GRYYYYYYY/3D_FPGA_Interconnects`
- 推荐源码基点：`7e63b917f37273f80c03327e024d86b797ee221b`，含整合稿及冻结 R6.2 证据。
- 冻结实验基点：`ea1d0d793f7655d421595fcf2ee961c9cdc9af92`。
- 建议新分支：`accel/lookahead-fpga-sim-restart-20261112`。
- 新代码建议放 `accel/lookahead/fpga_sim_restart/`；运行结果使用独立 run_id。
- 保护 main、旧 golden、STRICT、现有整合稿和未跟踪指导文档；旧 R6.2 停止记录保持原样。

先盘点现有工作区和资源，使用独立 worktree。通过技术阶段后直接继续，不逐阶段索要确认。不要终止其他用户作业。GPU 计时与重型工具作业使用隔离资源或错开。

## 1. 这次哪些条件不再阻塞？

| 状态 | 本轮处理 |
|---|---|
| XRT 没有发现 FPGA | 记录 `board_measured=false`，继续模块仿真 |
| 没有安装 XPFM / 完整 shell | 使用直接 RTL/HLS 导出和 Vivado 模块 OOC，不要求整卡链接 |
| 没有实际 HBM 随机 RMW 测量 | 使用有限参数化存储服务模型，标注 assumed 并做敏感性 |
| 新候选没有实现频率 | 先做功能与周期；最终按本候选 OOC 支持频率换算；目标频率只作假设筛选 |
| 小图 FPGA 比 CPU 慢 | 保留负结果；若确属填充/粒度问题，不据此自动取消大图模型 |
| 还没证明赢所有基线 | 继续完成有明确范围的原型验证，不强填 superiority=true |

仍要处理具体技术失败：错误输出、丢更新、未排空、死锁、资源超过器件、时序不收敛、完整工作量的必要下界无余量。这些可以否定某个候选或限制其结论，不能以“无板卡”代替工程分析。

必须区分两种校准：

1. **架构模拟器对 RTL 的校准**：本轮可以无板完成。
2. **外存模型对实际板卡的校准**：本轮允许缺失，限制结论为指定条件下的仿真评估。

## 2. 必读证据与复用范围

读取：

- `docs/lookahead_accel_round6_screen.md`
- `docs/lookahead_accel_round6_1_native_compact.md`
- `docs/lookahead_accel_round6_2_closeout.md`
- `accel/lookahead/round6_1/bucket61.hpp`
- `accel/lookahead/round6_1/cache61.cpp`
- `accel/lookahead/round6_1/cuda_solver61.cuh`
- `accel/lookahead/round6_1/backend61.cpp`
- `results/lookahead_r6_2_20261109T191213Z/evidence_snapshot/physical_memory_service_contract.json`
- 同目录 `hardware_service_decision.json`、`holdout_results.json`
- `results/lookahead_accel_round6_20261109T150000Z/evidence_snapshot/profile_summary.json`

已有 R4/R5/R5.1 的 testbench、周期计数、FP32 核对与 OOC 脚本能复用则复用，但不得继承旧核的频率、周期或缓存命中率作为新候选数据。

保留原始表示 ALT shift20 的 native 资格。compact/direct 的离线资格不自动升级为新的 native 资格。新硬件若采用压缩表示，需用实际导出/导入代码证明与原始 ALT 输入输出一致，记录转换成本及范围。

## 3. 固定本轮的唯一候选

候选名称：`ALT_LINE_OWNER_REDUCE_V1`。

**一个活动 sample（Q=1），64 个目的行 owner，每 owner 4-way × 32 sets 的 128-line 缓存，以及有限 MSHR、脏驱逐缓冲、请求与响应 FIFO。**所有原生 sample 依次完成；例如 BNN 仍完成全部 40 个 sample，不能人工重复同一个任务制造 batch。

CPU/GPU 保留各自合理的并行调度和已验证线程数。平台不必采用相同 context 数，比较对象是同一完整 batch。

### 3.1 为什么不用旧的 128-way 精确 LRU？

旧软件观察器按 `dst % 64` 分 owner，每项缓存一个 64-bit pair，miss/dirty eviction 各按 32B 事务计；每 qid/owner 128 项，全相联并精确 LRU。它没有实现 128 路硬件查找和并发同一行 RMW。

本候选按 32B 行分配：

```text
line   = dst >> 2
sector = dst & 3
owner  = line % owner_count
set    = (line // owner_count) % 32
tag    = line // (owner_count * 32)
```

完整候选 `owner_count=64`，tile 按实际 owner 数计算。Tag 身份还需包含必要的 epoch/sample 信息。不能令 `set=line%32`：owner 已占用低位，这会使每 owner 的有效 sets 退化。

同一行四个 pair 归一个 owner，整行读取和写回；其缓存总数据容量为 `64 * 128 * 32 = 262144 bytes`，即 **256 KiB**。Tag、valid、dirty/sector、epoch、替换状态和 scoreboard 要实体化为 RAM/寄存器，不得用 C++ 容器代表免费查找。

冻结一个简单确定替换策略：建议 round-robin。初版保持每 wave flush/invalidate，不同时引入跨 wave 保留缓存。

Q=1 用于缩小成员池、目录与状态复制，让单个大 frontier 使用宽数据通路；不声称其天然比 Q=8 更快。R6.2 原 Q=8 的 22.04 MiB 账本不能直接作为新候选资源结果。

### 3.2 首个候选参数是设计输入，不是实测值

| 项目 | 固定设计起点 |
|---|---|
| 同时活动 sample | 1 |
| 完整架构 edge lanes / owners | 64 / 64 |
| 第一 RTL 服务单元 | 1 owner |
| 中间物理原型 | 8-lane / 8-owner tile |
| 每 owner cache | 4 ways × 32 sets × 32B |
| 每 owner MSHR | 32，按 line 匹配 |
| 每 owner dirty buffer | 16 |
| 每 owner request / response FIFO | 各 64 |
| 替换 | round-robin，固定实现 |
| 设计目标频率 | 200 MHz，仅目标，最终由 OOC 决定 |

不得扫描大量 lane/context/cache 参数来寻找漂亮数字。只有明确的功能、资源或时序问题才作有记录的修复。

### 3.3 正确性必须实现到协议层

1. 每 wave 的 parent 从不变的 `label` 快照读取。
2. 候选 pair 写入独立 proposal home/cache，不能提前改动本 wave 的 parent labels。
3. 始终选择完整 `(delay, congestion)` pair；沿用 ALT 的 FP32 域和字典序严格改进。不把两个不同路径的最小分量拼接。
4. 同 line MSHR 合并四个 sector 的候选；脏驱逐尚未获写确认时，对该行的后续读/更新必须等待或正确转发。
5. 所有 accepted candidates、响应、RAW 依赖、脏驱逐和 flush 写确认完成，才允许 wave commit。
6. commit 后发布 pending；同 bucket 重入继续闭包，闭包后记录目标单元。
7. 初始化、sample 切换、epoch 回绕/清理、容量上限和输出排空都有实际逻辑。溢出返回失败，不发布部分 map。

`label` 与 proposal 可以保持单调持久状态，但禁止在软件模型里免费复制/清空 N 项数组。若用 touched list/bitmap 避免全图扫描，它们的构造、端口、去重和重置都要建模并计时。

### 3.4 互连和外存端口不是免费资源

64 个 producer 到 64 个 owner 必须实现或显式模拟有限缓冲、仲裁和背压；建议先验证 8×8 tile，再组成有寄存器/FIFO 的分级互连。不可假设任意 64×64 无冲突交换。

64 个逻辑 owner 不等于 64 个独立 HBM 物理端口。例如映射到 32 个物理服务通道时，每通道共享两个 owner，并与其它数组流量竞争；不要只给 proposal 单独享有全部带宽。

### 3.5 最小消融

- **F0**：同 owner、同 Q、同算术、同有限内存服务，cache bypass，每个 proposal 走显式行 RMW。
- **F1**：开启上述行缓存、同 line MSHR 合并与写回。

先主张缓存/合并机制整体收益。128 行等于 512 个 pair 槽，不得把它与旧 128-pair 配置的差异全部归因于行布局。若要单独声称行打包贡献，再用软件事务重放增加等数据容量的 512-pair、4-way 对照；本轮无需立刻做第三套完整 RTL。

## 4. 新计时范围：完整真实 batch 的驻留服务

新 scope 版本：`RESIDENT_COMPLETE_BATCH_V2`。

起点：可消费的 graph/cost/jobs 已位于各平台声明的内存，完整任务开始执行。

终点：全部真实 sample 输出提交到声明的目标内存，所有必要事务完成。

**包含：**每任务必要 reset、CSR/node/cost 访问、label/proposal RMW、目录/成员/seen、仲裁与背压、全部波次控制、commit、target completion、输出写入与排空。

**排除：**主机外部转换、首次整图 H2D、一次性主机入口控制、最终结果 D2H、外部后处理。CPU 输出在主存，GPU/FPGA 输出在各自设备存储，布局与缓存状态明确。

### 4.1 不能直接把旧 E1 改名

`cuda_solver61.cuh` 中：`resident_s` 在最终 D2H 前结束，而 `E1_wall_s` 还包含最终 D2H/unpack。每 wave 的完成标记 D2H 与随后 host 发核在 `resident_s` 中，是当前算法实现必须承担的控制成本。

- 新主图优先按完整 `resident_s` 对齐；不能只累加各 CUDA kernel 的 event 时间，漏掉波次间必须的控制空隙。
- 初始 host 调用开销可排除；算法内部每 wave 的控制不能删除。
- 旧 0.309712337 s 可作预筛参考，不得直接重命名成新 scope 的测量值。
- 如冻结记录已有同范围的 `resident_s`，先复用；否则只补必要的少量同范围测量，保留旧 E1/E2/Process。

### 4.2 基线角色与范围

保留：原 VPR 多线程、最佳已测优化 STRICT CPU、同算法 ALT CPU、原始基础 ALT CUDA，以及已有离线 compact CUDA 这一更强软件参考。

对整个 resident batch 比较时，每个基线必须执行同一 sample 集和输出任务；所有必要初始化计入。基线可用自己的合理布局与线程。算法间差异通过已有 native/QoR 资格解释；硬件贡献以相同 ALT CPU/CUDA 为直接对照。

某个原 VPR 基线如果只有完整 E2，不能用它除以 FPGA 的 sample 核时间。自动复用/增加对应核心区间计时；未补到的标 `not_evaluated_same_scope`，不能阻止第一 RTL 原型。正式声称优于该基线时再要求同范围证据。

软件正式计时建议 3 个独立进程，每进程预热后测固定次数并保存全部原始值；延续论文的 mean/sample-SD 和配对规则，不只报告最小值。RTL 确定周期不靠重复同一次仿真制造 SD。

## 5. 有限存储服务模型：可假设，但不能无限快

建议直接使用 XSim/适配 RTL 仿真器 + 自定义 SV AXI slave 或可用的 AXI VIP。没有 XPFM 时不强行依赖整卡 `hw_emu` 链接。

存储模型至少定义：32B 对齐事务、有限 request/response/outstanding、每通道服务带宽、read/write latency、读写切换、bank 争用、同地址 RAW、write response 与背压。测试平台的稀疏内存容器只储存功能数据，性能通过有限服务器推进；不能让 DUT 看见零时延数组。

参数文件里的值分成 documented / derived / assumed / RTL-observed。没有板测的值明确 `assumed`。本包给出的参数只是预先选择的情景，不代表 U280 测量，也不是严格物理上下界。

### 5.1 小而明确的敏感性集合

设计起点：32 个服务通道、256-bit 接口，DUT 单时钟。总读写共享带宽情景为 64 / 128 / 192 GB/s，read/write 响应基础延迟示例为 150 / 300 / 600 ns。

避免全排列：先中央情景 128 GB/s、300 ns；再带宽单独变为 64/192；延迟单独变为 150/600，共 5 个情景。读写切换、bank 服务冲突和有限 outstanding 参数同样显式冻结；必要时另做针对性小压力测试。

所有数组共享声明过的通道总预算。每通道 read+write 共用链路，不能给两个方向各自一份峰值带宽。默认抽象映射可用 `address_line=physical_byte_address>>5`、`channel=address_line%32`、`bank=(address_line//32)%16`；先明确各数组真实基址和 stride，不能重复使用 channel 低位作为 bank，也不能令不同数组共享错误的局部地址空间。

强制接口上限：`B_effective <= channels * bytes_per_beat * interface_frequency`。若接口跟随 200 MHz 的核时钟，32×32B×200MHz 上限是 204.8 GB/s。频率降低时重新检查这个约束；不能在 125 MHz 的同宽接口上仍填 192 GB/s。若引入独立接口时钟，增加相应 CDC/FIFO 与物理约束。

改变核频率时，外存延迟仍用 ns，物理带宽假设仍用 bytes/s；换算为周期。已包含在 RTL/架构周期中的存储等待不能再额外相加 bytes/bandwidth。

### 5.2 暂无真实 HBM 校准如何表述？

可以写“在声明的有限存储服务情景下，RTL 验证或 RTL 校准的驻留核性能”。不能写“该 U280 实板实测带宽/性能”。没有真实校准不会阻止本轮运行。

## 6. 按产物推进：先 RTL，不再只写账本

### S0：冻结输入和小规模事务重放

只做一次必要环境盘点。确认 Vivado/HLS/RTL 仿真器和目标 part；XRT=0、XPFM 缺失只记状态。Vitis 2022.2 使用该版本支持的命令，不套用新版本才有的 unified CLI。

复用既有真实小图、BNN 和 LSTM 导出/哈希。冻结：BNN 用于设计，LSTM 作为新硬件候选的保留验证输入；它并非整个项目首次使用，也不是跨架构留出。先选择完整小图与确定性的边界/冲突样例，不为快而抽掉小图任务语义。

为新 owner/line/4-way/RR 策略生成候选事务流并重放。旧 20.87% 命中率和旧 dst 分 bank 结果不继承。全 wave 的重复目的数只是机会，不代表有限缓存可实现的命中/合并率。

先用小例和有代表性的完整 wave 驱动服务单元；完整 BNN 新缓存重放可与 RTL 开发分开推进，不必等全图重放结束才开始写硬件。

### S1：一个 owner 的真正 RTL + OOC

实现 synthesizable owner service，含四路 tag 查找、hit、miss/MSHR、同 line merge、dirty eviction、read response、write ack、fence 排空。

testbench 至少覆盖：同 pair 连续更新；同行不同 sector；延迟响应；脏驱逐后立即重访；MSHR/FIFO 满；读写相遇；非改进候选；epoch/sample 切换。所有测试比较整个受影响 proposal memory，不只比较输出数量。

记录真实周期和计数：accepted/retired、持续输入间隔、反馈延迟、32B read/write、merge、各队列高水位、RAW/冲突/脏驱逐/fence stall。

运行 OOC 综合，并对选定单元进行 placement/routing，保存资源、setup/hold、约束、未约束路径和 DRC。输入须运行时加载，不把工作负载编译成常量后让工具剪掉数据通路。

此阶段即使尚未显示整体 GPU 优势，也应交付可运行原型和结果。只有功能错误或真实工具/资源阻塞才修复对应项。不得再次因没有板卡/平台而停在书面分析。

### S2：8-owner tile、完整小图闭环及完整候选物理覆盖

复用已实现单元，加入实际 FP32 pair 生成、图读取、pending/目录/成员、wave fence、commit、closure 与输出。

完成至少一个完整真实小图 batch 的 RTL 输出与周期；再用未参与调参的另一完整小图作模型校准留出。新候选同算法参考是 ALT CPU，STRICT 差异仍按既有语义轨道保留。

一个 tile 的时序不能直接当成 64-owner 全核频率。完整候选的 OOC 应覆盖 64-owner、实际互连、目录、控制与算术，或明确列出未实现的组件。如果只有 tile 完成 OOC，大图暂用 target frequency 并标 `projected`，不得伪称全核已支持该频率。

时序不收敛时针对关键路径作有限流水修复，或报告较低的支持频率；不能反复扫描器件和目标频率直到数字好看。资源账本包含 tags、FIFOs、仲裁、跨 SLR 和接口预留；预留是设计假设，不冒充 shell 已验证配额。

### S3：有限、闭环的架构模拟器

实现 C++/离散事件模型，复现相同队列容量、service II、反馈依赖、互连、存储服务、wave fence 与完成事件。功能 labels/proposals/pending 由模型执行推进，不由预先的 golden frontier 免费供给。

必须计 CSR/node/cost/label/proposal/members/seen/targets/output 和 reset/commit/drain；不能只模拟 proposal trace 后将它当整个 batch。

在与 RTL 相同输入和内存情景下比较总周期与主要 stall 分解。至少有一个未参与模型调节的完整小图。建议事先冻结总周期误差目标：典型不超过 5%，最差不超过 10%；这只是工程验收目标，不代表真实硬件误差保证。若超出，定位遗漏与调度差异；若某部分仍未校准，单列该部分并保持结果为 projected。

`architecture_simulated` 只能用于已覆盖主要组件、按适用范围完成 RTL 校准的结果。模块校准与全核校准不能混称。记录校准配置签名：owner/lane 数、互连、FIFO/MSHR、目录和服务参数。64-owner 最终模型至少用相同配置的完整小图 RTL 校准，覆盖新增互连层级、共享通道和全局 fence；若仅有 8-owner/tile 校准，64-owner 大图结果保持 `projected`，即使完整 OOC 已通过。无需对大图运行完整 RTL 才能开发模拟器。

### S4：大图完整 batch 与匹配基线

使用 BNN 全部 40 个 sample；通过后再用 LSTM 全部 40 个 sample 检验固定候选。保留真实小图负结果。

先运行 F0/F1 的中央内存情景，再用 F1 的 5 个预声明情景。所有样例必须输出完整结果并核对，不能只测最快 wave 或只运行高命中片段。

对齐/补测必要 CPU/GPU resident scope。GPU 节点暂不可用不阻断 RTL/OOC；对应优势结论保持待评估。

软件模型耗时不是 FPGA 时间。最终时间为完整仿真周期 / 该范围对应的 OOC 支持频率；频率只有假设时明确条件性并报告敏感性。基础 GPU、compact CUDA 和最佳同算法 CPU 均保留，不隐藏较快软件基线。

### S5：下游检查与论文图表

将硬件/架构模型实际输出接回现有 native bridge。先完成完整 sample 与最终 map 差分；若相同原始 ALT 输出、同 bridge 及输入身份得到确认，可以复用已有 QoR 范围并说明复用依据。若 bridge/表示/数值语义有变化，再对代表性设计运行必要 native FULL/STA/QoR；不能仅凭旧 compact 离线资格跳过。

根据实际证据形成：

1. 功能与输出/QoR 表。
2. 同范围完整 resident batch 速度，明确 measured_cpu/GPU 与 rtl/architecture_simulated。
3. F0/F1 周期、32B 事务、合并与瓶颈分解。
4. OOC 资源、频率及覆盖范围。
5. 带宽/延迟敏感性，包含输赢转折点。
6. 冷调用开销情景和原生模块占比，作为补充，不要求其加速比与主核相同。

图表数量可以合并，不为凑数量增加实验矩阵。

## 7. 现有数据如何指导候选，而不代替实验？

BNN shift20 已有 `eligible_edges=1,286,937,147`，完整 wave 重复目的候选约 951,170,650。这个约 74% 的重复机会支持研究归并，但有限缓存的实际合并能力必须重新测。

仅边工作下界，在 64 lanes、假设 200 MHz 下，II=1/2/3 分别约为 0.10054/0.20108/0.30163 s，尚不含其它工作。125 MHz、II=2 时约 0.32173 s。旧约 0.31 s CUDA 只能用作粗筛参考，最终比较换成新同范围记录。

这些算术说明需要落实持续 service II、互连和存储，并非已经证明可达。首次完整 RTL 和 OOC 仍应实际执行；若随后同范围完整工作量的乐观下界已经超过软件，停止扩大该候选并交付明确负结果，不把它包装成“所有 FPGA 不可行”。

## 8. 传输与应用收益

主图使用 resident scope，不把主机转换和首次 H2D 加进去。另作完整调用情景：转换、H2D、启动、驻留核、D2H、必要后处理，避免重复计算同步等待。

未知 PCIe/调用开销用有标签的情景，不能用 CPU memcpy、GPU H2D 或 AI 估计冒充目标 FPGA 实测。真实 40 个 sample 属于一个已有 batch；重复同一个 batch 只是统计重复，不能作为人为摊销 K。

核内 HBM 访问、随机 RMW、队列和 fence 都仍在主时间中。没有实板不是这些成本可以删除的理由。

## 9. 结果状态与完成标准

使用独立状态，不让 `board_measured=false` 把所有成果都变成失败：

- `fpga_method_rtl_verified`
- `fpga_module_ooc_timing_supported`
- `fpga_full_kernel_ooc_timing_supported`
- `architecture_model_rtl_calibrated`
- `resident_batch_superiority_under_declared_model`
- `board_measured=false`

每项带范围、证据路径、假设和对照。模块加速、完整 sample/batch 加速、完整 E2/Process 加速分开。

可以形成的结论：在指定有限存储情景、经 RTL 验证/校准及对应 OOC 频率条件下，完整驻留 batch 相对匹配软件基线的条件性加速。它是可报告的仿真方法结果，不是实板测量。

不能形成的结论：只凭 hit rate/资源账本/单 bank II 推导完整 FPGA 已胜；用目标 200 MHz 替代失败的实现频率；把纯服务 trace 冒充完整 batch；因为冷调用不占优就删除主核结果；因为主核占优就称整个 VPR 同倍加速。

首个实际交付应包含 RTL 源码、可复现 testbench、真实输出差分、周期日志和 OOC 报告。只增加报告、清单或模型必要界不算完成本次硬件重启。

完成阶段后独立推送、核对 SHA，说明已完成与未完成项。建议先把首个 RTL 服务单元和小任务闭环作为一个工作日内争取交付的目标；这是项目安排，不是工具耗时保证。遇到真正工具/许可证阻塞时给出命令和错误，并继续不受影响的软件/模型工作。

## 10. 最短启动指令

> 按本文件和同包 YAML 恢复无板 FPGA 实验。没有 XRT 设备、XPFM、完整 shell 或实测随机 RMW 不再作为模块 RTL/OOC 的停止条件。保留旧结论，建立新 scope 和独立分支。固定实现 Q=1、64 个行 owner、4-way 128-line cache 的候选，先交付一个 owner 的真实 RTL 输出/周期与 OOC，再接完整小图、校准模型及大图完整 batch。主比较是含内部访存与控制的 resident service，H2D/D2H 另列。不要只更新账本，也不要预设 FPGA 必须获胜。通过技术阶段后自主继续。

## 11. 来源

- 用户上传模板：`CODEX_FPGA_QUICK_VALIDATION_PROMPT.txt`、`FPGA_Quick_Validation_Guide_20261108.txt`、`experiment_spec.example.yaml`、`source_notes.txt`。本次读取其内容；组内五篇论文的描述按该包整理，不声称本次重新审阅原 PDF。
- [R6.2 结项与停止范围](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7e63b917f37273f80c03327e024d86b797ee221b/docs/lookahead_accel_round6_2_closeout.md)
- [R6 完整工作量](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7e63b917f37273f80c03327e024d86b797ee221b/docs/lookahead_accel_round6_screen.md)
- [旧 cache 观察器](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7e63b917f37273f80c03327e024d86b797ee221b/accel/lookahead/round6_1/cache61.cpp)
- [现有 CUDA 计时](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7e63b917f37273f80c03327e024d86b797ee221b/accel/lookahead/round6_1/cuda_solver61.cuh)
- AMD UG1399 2022.2：[Analyzing RTL Simulations](https://docs.amd.com/r/2022.2-English/ug1399-vitis-hls/Analyzing-RTL-Simulations)；[config_export](https://docs.amd.com/r/2022.2-English/ug1399-vitis-hls/config_export)。分别说明 co-sim 给定输入周期和独立实现评估。
- AMD UG1393 2022.2：[Speed and Accuracy of Hardware Emulation](https://docs.amd.com/r/2022.2-English/ug1393-vitis-application-acceleration/Speed-and-Accuracy-of-Hardware-Emulation)。PCIe 为功能模型，周边性能精度与 kernel RTL 区分。
- AMD PG276：[AXI Considerations](https://docs.amd.com/r/en-US/pg276-axi-hbm/AXI-Considerations)。32B 事务、对齐及读写服务限制；当前文档规则不等于本候选板测校准。
- AMD PG267：[Simple SRAM Model](https://docs.amd.com/r/en-US/pg267-axi-vip/Simple-SRAM-Model)。可用于功能内存模型；本任务仍需自行加入有限时序与带宽服务。
