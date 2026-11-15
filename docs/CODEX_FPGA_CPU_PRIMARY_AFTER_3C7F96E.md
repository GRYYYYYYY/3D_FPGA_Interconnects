# FPGA 对 CPU 加速的完整实现与仿真验证指导

文件名：`CODEX_FPGA_CPU_PRIMARY_AFTER_3C7F96E.md`  
适用项目：DAC2027 / `GRYYYYYYY/3D_FPGA_Interconnects`  
基点：`3c7f96e6037030949b729240977c2ced373843c6`  
基点分支：`accel/lookahead-local-fabric-20261115`  
建议新分支：`accel/lookahead-cpu-primary-closure-20261115`

这是一份可单独交给服务器 Codex 执行的完整任务，不依赖任何此前未上传的 Markdown 或 ZIP。以仓库中的真实源码、归档证据和本文件为依据接续工作。任务是实现与验证，不要仅返回方案。

## 1. 用户最新目标：以 CPU 加速为主，GPU 为保留的对照

用户现在接受：**FPGA 在明确计时范围内快于优化 CPU；GPU 可以更快。需要解释当前 FPGA/GPU 差距的具体原因。**

据此执行以下变更：

- 取消历史指导中“只有预测快于最强 GPU 才进入完整 top、RTL 或 OOC”的前置条件。本轮不再以 GPU 胜负决定是否推进。
- 保留强 CUDA 结果及全部负结果。目标变更应在本轮配置、报告和 claim ledger 中注明，历史记录不改写。
- 不要求证明“所有 FPGA、所有架构都不可能比 GPU 快”。只能给出限定工作负载、器件、频率、队列、算法和存储服务条件下的解释或下界。
- 优先完成一个可实现且有 CPU 加速潜力的完整核。L1 是首选；L2 是可选优化，不能成为 L1 完整验证的前置条件。
- 接受明确标注的 **RTL／架构仿真评估**。不把“服务器没有 FPGA 实板”作为停止理由，也不把仿真称为实板实测。
- 200 MHz 是现有条件模型参考点，不是本轮唯一允许的工作频率。若较低、真正闭合的频率下仍优于 CPU，可以选用。

以下项目仍必须满足：功能正确、有限真实资源、完整连接的核心、合理约束下的布局布线、RTL 与模型的可解释校准、同范围 CPU 比较、ALT／STRICT 语义边界。

## 2. 已知事实：复用证据，不重跑已完成工作

先读取：

- `docs/lookahead_fpga_local_fabric.md`
- `accel/lookahead/fpga_local_fabric/README.md`
- `accel/lookahead/fpga_local_fabric/model/finite.hpp`
- `accel/lookahead/fpga_local_fabric/delivery/resource_budget.py`
- `accel/lookahead/fpga_local_fabric/delivery/` 中的实际仿真、综合、分析和归档入口。
- `results/fpga_local_fabric_20261115/` 的资源账本、完整 L1 receipts、复用证据索引；如归档需要还原，按现有 manifest 恢复，不覆盖历史目录。
- `accel/lookahead/fpga_sparse_stream_r2/cuda_prepared_pop.cu` 及对应软件测量 receipts。

### 2.1 资源与时序

当前目标 part 为 `xcu280-fsvh2892-2L-e`，总资源为 1,303,680 LUT、2,607,360 FF、2,016 BRAM36 等价、960 URAM。

| 组成 | LUT | FF | BRAM36 等价 | URAM | 证据性质 |
|---|---:|---:|---:|---:|---|
| 全尺寸 radix 网络 | 360,844 | 250,425 | 0 | 0 | 网络实际综合；未取得全网络布线频率 |
| Radix + L1 | 1,254,466 | 818,745 | 1,148 | 640 | 模块算术合成；剩 49,214 LUT，约 3.775% |
| Radix + 最终 L2 | 1,305,474 | 861,241 | 1,148 | 640 | 模块算术合成；超 1,794 LUT，约 0.1376% |

两套模块合计都不是完整 top 实现结果。账本未包含全部全局 phase/sample 控制、clock/reset 分布及集成效果。完整综合可能消除部分冗余，也可能加入接口、控制和物理开销，不能预先断言方向。

前端局部 context 和最终后端局部 context 已通过 5 ns 布线时序；最终后端 setup/hold 余量约 +0.007/+0.009 ns。局部通过不能替代完整核通过。

`ACK_METADATA=0` 已经实施并节省 6,112 LUT；最终超额 1,794 LUT 已计入此收益，不得再次计作新优化。

### 2.2 L1 完整 batch 与软件对照

| 指标 | BNN40 | LSTM40 |
|---|---:|---:|
| L1 完整条件模型周期 | 72,317,544 | 73,419,021 |
| 假设 200 MHz 的条件秒数 | 0.361587720 | 0.367095105 |
| Xeon Gold 6530 packed CPU，8 线程，实测秒数 | 2.842626751333 | 2.933218058 |
| 该 CPU／条件 FPGA | 7.8615× | 7.9903× |
| Xeon Platinum 8462Y+ prepared CPU，8 线程，实测秒数 | 3.654426308 | 3.669705272 |
| 该 CPU／条件 FPGA | 10.1066× | 9.9966× |
| 强 CUDA，实测 resident 秒数 | 0.15179996944444446 | 0.15949799988888888 |
| 条件 FPGA／CUDA 耗时 | 2.3820× | 2.3016× |

这些 CPU／FPGA 比值目前只是**实测 CPU 对条件 FPGA 模型的比较**。不得写成已经完成的 FPGA 硬件加速成果。两组 CPU 的平台与表示不同，必须分列，不能把跨主机差异归因于数据格式。

软件统计复用时保留原始均值、中位数和试验层次。三独立进程各三正式重复是三组进程证据，不能写成九个独立进程。

L1 完整 ALT 输出 SHA-256：

- BNN：`a8ca4003a3b015145635a3f776bb62a3aec1ec2121a1fbfc8712d2a2dc1c8c3f`
- LSTM：`6b2acd7718d880075d653b3b83f1fa3abb5161f6f346ed39c3aa1285160a95cf`

L2 只有 BNN4/LSTM3 代表样本结果，总周期分别改善约 9.53%/9.50%；还没有完整 BNN40/LSTM40 性能结果，不得按这个比例外推正式整批结果。

## 3. 工作区与证据管理

1. 核对指定完整 SHA、当前 worktree 列表、未提交改动和活动进程。在该 SHA 上建立独立 worktree 与新分支；如同名分支已存在，检查真实内容后接续，不能强制覆盖。
2. 保留 main、原稿、STRICT、旧 golden、历史结果及既有未跟踪指导文档。本轮源码、报告、结果放新路径，避免旧报告生成器改写历史文件。
3. 在新 `experiment_config.json` 中记录目标改为 `CPU_PRIMARY_GPU_COMPARATOR`、实际基点、工具版本、part、完整配置、计时边界和原始输入哈希。
4. 不重新启动已结束的旧模型、旧 OOC 或 GPU 测量。先复用来源闭包完整的证据；确因新数据表示或边界变化而失效时，记录原因后补对应证据。
5. 长任务可监督运行和分阶段推送，但“已启动”“仍运行”“阶段检查点”与“最终完成”分开。归档使用源码／二进制／输入绑定和进程出生身份，避免重复作业或错收别的进程结果。

建议新源码目录为 `accel/lookahead/fpga_cpu_primary/`，结果目录为 `results/fpga_cpu_primary_20261115/`，新报告为 `docs/lookahead_fpga_cpu_primary_closure.md`。它们是本轮待创建路径，并非声称基点已存在。

## 4. 第一优先：完成真实 L1 核心 top

### 4.1 集成范围

从已实现 L1 模块构造真实连接、可综合、运行时输入图的完整核心 top。至少包含：

- sample/phase 控制、初始化、wave 推进、终止判定与输出排空；
- POP、独立 T/D/ready/target 生命周期、真实枚举和 FP32 数据通路；
- radix 请求／返回网络、有限 tag/信用/缓冲和真实反压；
- canonical、scratch、目录及 L1 提交服务；
- 生产位宽与实际地址适配，包括尚未完整验证的 64-bit leaf line 到 32-bit network line 适配；
- 完整输出写入、ACK 及所有未完成事务的排空。

完整 top 不能用零延迟 C++ 回调代替实际硬件模块，不能用未连通模块的资源和时序相加代替连接后的实现。外存可以由 testbench／体系结构模型提供，但接口、流控、请求标识、有限在途数和时序合同必须明确。

保留完整 `source6 + kind4 + generation32 + localID32` 身份语义。除非针对某类消息证明值域和无别名条件，否则不能截短 generation/localID；scratch 某些身份字段可能包含完整地址信息。不得硬编码只对已知 sample 正确的响应或截断图容量。

### 4.2 必要功能验证与校准

先运行当前模块测试中可复用的已验证用例，再补集成才引入的缺口：

- 至少两个不同完整小图，从输入到最终完整输出比较；测试实际部署参数的 top，而不只验证缩小 lane/容量的替身。
- 覆盖至少一次多 wave、同 bank/同字冲突、非空发布排空、外存反压以及容量边界／越界拒绝。优先复用现成向量，不为凑测试数量另造大量重复用例。
- 比较模型与 RTL 的输出、阶段边界、总周期、关键请求和退休计数。若不能逐周期一致，解释每类差异及误差范围，不能仅用一个平均校正系数掩盖缺失服务。
- 用至少一个有实际拥塞／回压的 trace 校准，不能只凭无冲突微原型推广到大图。

这里的小图用于验证**同一完整硬件结构**。大图仍可采用已校准的有限架构模拟，无须把 BNN/LSTM 的全部数十亿操作跑成门级仿真。但小图没有触发的容量、流量或阶段路径，必须有针对性证据覆盖。

## 5. 第二优先：完整资源和可达频率

### 5.1 先做 L1 完整综合，不因慢于 GPU 而拒绝进入

第一轮直接综合完整 L1 top，目标仍为现有 U280 part。记录真实层次资源、LUT logic/LUTRAM、FF、BRAM、URAM、DSP、被裁剪逻辑、未连接端口和黑盒情况。

**“完整资源账本离容量很近”是需要真实综合的理由，不是再次只做一份账本就停止的理由。** 同时不要把综合后未裁剪的算术合计当成已布线成功。

明确报告范围：

- 若是裸器件上的核心 OOC，完整核心必须真实连接；写明未纳入的平台 shell、PCIe、HBM 控制器及外部服务假设。
- 若声称某张卡的平台部署可行，使用该 shell 的实际可用区域／资源，包含必需平台接口成本，不能用裸片总资源冒充用户区资源。
- 本轮允许先完成核心 OOC 研究，不以部署 shell 或实板缺失自动阻断核心仿真结果，但结论必须限定为所实现范围。

### 5.2 资源可容纳时推进布局布线

先按已建立的 5 ns 约束尝试完整核心实现。根据真实失败路径和拥塞判断下一步：

- 可以降低目标频率，或修复一个明确关键路径后再实现；不预设必须达到 200 MHz。
- hold 问题需要真正修复，降低频率不自动解决 hold。
- 不允许用假路径掩盖真实反馈／控制路径，不用 WNS 反推一个未经实现的新频率。
- 对 core 内所有实际时钟路径检查 setup、hold、pulse width、约束覆盖、DRC 和 methodology 问题；OOC 外部时钟／端口假设单独说明。
- 有效频率只能来自被选完整 top、对应 part/约束/工具与实现报告，不能借用局部 context 的通过结果。

本轮不做没有明确依据的大范围频率、种子或参数扫描。一次失败后先解释路径，选择针对性的下一点；通过的足够频率即可进入评估。

### 5.3 如果完整 L1 实际装不下或难以布线

按资源报告选择一个范围受控的修订，目标是完成 CPU 加速核：

1. 检查综合后仍保留的重复控制、可证明常量和局部地址/身份转换。
2. 网络 360,844 LUT 中有 104,704 LUT-as-memory。可针对**一个明确 FIFO/标签存储模块**比较存储映射，保留容量、端口、回压及身份；新增同步读延迟必须纳入模型。
3. 不能把大量 FIFO4/FIFO2 的分布式 RAM 简单折算成“空闲 BRAM 足够，因此免费替换”。浅队列与并行端口有真实成本。
4. 若高占用主要来自并行规模，可选择一个较小规模配置，例如减少物理 lane／前端请求者，保留明确的逻辑 bank 和状态映射。重新验证资源、模型和输出；不得按 lane 数直接线性换算时间。

现在的条件 CPU 优势允许探索面积／频率折中；不必为了击败 H100 继续增加队列、lane 和网络。是否还快于 CPU，以更新后的结果判断。

### 5.4 L2 的位置

L2 可以作为非阻塞的第二候选：做实际集成资源检查、一个局部面积修订或完整 batch 的性能诊断。超出 1,794 LUT 不能当作“只要省 1,794 就必定成功”，也无需因为小幅模块超额禁止一次有价值的实际集成综合。

只有最终真实资源、功能与时序资格齐全时，L2 才能替代 L1 成为正式硬件结果。若只有有限模型结果，明确标注未实现候选，不能与 L1 的已实现频率拼接。

## 6. 换器件：后备路线，不要求购买实板

当前先不因 1,794 LUT 的算术超额换板。需要迁移时，应先核对工具实际可用器件，再做独立迁移实验。

| 目标 | 官方 LUT | 主要外存 | 判断 |
|---|---:|---|---|
| U280 | 约 1,304K，当前精确 1,303,680 | 8 GB HBM2，官方峰值 460 GB/s | 当前基准 |
| U55C | 约 1,304K | 16 GB HBM2，官方峰值 460 GB/s | HBM 容量增大，但不增加 LUT，不能解决 LUT 缺口 |
| U250 | 1,728K | 64 GB DDR4，官方峰值 77 GB/s | LUT 增加约 32.5%，但存储体系不同 |
| VU37P / VU47P / VU57P | 三者都是 1,303,680 | 分别 8 / 16 / 16 GB HBM | 型号后缀增加不代表 LUT 增加 |

这些是器件／产品规格，峰值带宽不是该工作负载的随机 RMW 有效服务率。

迁移要求：

- 查询已安装 Vivado 的实际 part、速度等级、许可和工具支持；不假定有某设备库或新版平台。
- 没有卡也可做指定 part 的综合/OOC。若只做逻辑迁移，结果就标“逻辑迁移”，不声称新板卡应用加速已成立。
- 换到 U250 后，不能继续沿用 U280 的 32 路 HBM 端口、80 ns 延迟和 5 ns 物理发起间隔作为 U250 实际参数。必须重新描述 DDR 控制器、端口映射、并发、读写切换和排队服务。
- 若改用其他 HBM 平台，核对实际 LUT、用户区、HBM 通道和工具链，不以 System Logic Cells 代替 LUT。
- 购买板卡、升级工具链及扩大研究到多个新平台不属于本轮必需步骤。

## 7. 频率与外存模型必须一起更新

基点模型合同为假设 200 MHz、外存 80 ns、物理 issue 间隔 5 ns。

新频率选定后，把纳秒参数转换为实际模型周期；协议中本来以核心边沿计数的阶段保留各自的硬件语义。若需要多时钟或更细时间粒度，使用明确的时间推进，不凭取整偷偷增加服务能力。

例如绝对内存延迟对应周期一般为 `ceil(latency_ns * f_MHz / 1000)`。重新检查端口发起、返回排队、读写依赖、总带宽与 bank 限制，跑新的校准和选中配置的完整 batch。**不能把旧 200 MHz 模型周期简单除以一个新频率，就宣称得到新实现时间。**

没有实板时，外存服务仍可作为论文的显式模拟假设；不能称其为实测。用已有平台文档或已验证服务模型解释参数来源。额定峰值带宽不足以证明 80 ns 随机延迟或每端口持续 5 ns 服务可达。

在基准点之外，至少提供一个预先写入配置的较保守服务情景，评估 CPU 优势对访存变差的敏感性。若缺少实测参数，可把例如“延迟加倍、物理 issue 间隔加倍”标为诊断情景，而非平台实测或有保证的最坏界。只针对最终候选补必要完整批次，避免对全部历史候选扩展扫描。

## 8. CPU 是主对照：补最少但关键的公平性证据

### 8.1 resident complete-batch 主结果

采用冻结的完整 batch 边界，明确起止操作。应包含该实现每次必须做的设备状态初始化、所有 wave、访存、归并／发布、最终输出写入和排空；计时前的数据准备和计时后的完整主机读回单独报告。

读取并核对 `RESIDENT_COMPLETE_BATCH_V2` 的实际定义，而不是仅复用名称。CPU、GPU、FPGA 都完成相同的 BNN40/LSTM40 输出；不能把 FPGA 仅一个 sample 与 CPU/GPU 完整 batch 比。

区分两种比较：

- **硬件贡献**：同一 ALT whole-pair FP32 算法合同的优化 CPU 与硬件，确保同输入／输出和同范围。
- **系统贡献**：原 VPR 多线程、native STRICT/Pipeline 与 ALT 系统的 lookahead 构建 E2 或整个 Process；明确算法不同和 QoR 条件，不能伪称逐位相同。

### 8.2 线程数与平台

先审计现存 CPU 线程扫描、绑定、NUMA、编译选项和计时 receipts。若仅有 8 线程，不能称为该多核服务器“最强 CPU”。补一个有限线程集合：8、一个中间点、当前分配到的物理核数；若已有同设置证据则直接复用。遇到明显瓶颈再做有依据的改进，不做无限 CPU 调优。

固定合理的平台与线程选择规则，报告每种 CPU 实现的最好合资格配置及完整线程结果。多路机器的 NUMA 放置、线程绑定和输入常驻状态应明确；不要通过限制 CPU 可用核或不当数据布局制造优势。

正式计时原则上保留三独立进程、每进程多次正式重复；已有合格数据不重测。统计以进程为独立单位，报告分散程度，极小样本不要过度解读置信区间。FPGA 确定性仿真周期不伪造测量噪声，存储假设的不确定性单独做敏感性分析。

GPU 复用最强合资格基线。当前目标不要求 CUDA 重优化，也不因为 GPU 更快重启 GPU 作业；只有接口、算法或计时边界改变到不能复用时才补必要测量。

## 9. 解释 GPU 为什么更快，但不写普适不可能性

本轮已有可复用定量证据：

| L1 阶段 | BNN40 | LSTM40 |
|---|---:|---:|
| 展开周期 | 48,862,467 | 49,650,643 |
| 展开时间，假设 200 MHz | 244.312 ms | 248.253 ms |
| 展开占比 | 67.57% | 67.63% |
| finalize 周期 | 22,008,522 | 22,298,917 |
| finalize 时间，假设 200 MHz | 110.043 ms | 111.495 ms |
| finalize 占比 | 30.43% | 30.37% |
| 展开阶段平均 candidate/cycle | 26.338 | 26.375 |
| 相对 64 lane 理想峰值 | 41.15% | 41.21% |

当前有 128 个 T、128 个独立 D，以及有限 ready/target/E/beat、网络队列、物理端口与 canonical 发布能力。实际吞吐不能仅由算术 lane 峰值推断。

实际 prepared-POP CUDA 的 `grid=(ceil(n/256), jobs)` 用 `blockIdx.y` 暴露多个 sample 并行，合资格 node/thread 扫自己的 CSR 邻居，以 64-bit atomicMin 归并 whole-pair。当前 FPGA 整批时间是逐 sample 的有限模拟周期之和。两者完成同一真实 batch，但并行组织不同；不能为了让 FPGA 获胜强迫 GPU 改成逐 sample 串行。

CUDA resident 时间还包含逐 wave 的 host completion 读回／等待，并非删去所有控制成本的理想计算时间。

采用有限、实际可实现的对照来解释：独立生命周期对共享生命周期、radix 对已有网络、L1 发布对 L2 日志。已有证据充足就复用。队列满计数可能互相重叠，不相加成“可消除时间”；publication-held 状态占用也不等于全部可删掉的延迟。

### 9.1 可以使用的限定下界

固定 64 条 II1 candidate lane、200 MHz 时：

`T_edge >= N_candidate / (64 * 200e6)`

- BNN：100.542 ms；LSTM：102.306 ms。
- 这两个界均低于 CUDA 的 151.800/159.498 ms，因此单靠边工作量不能证明 FPGA 必然更慢。
- POP 与边处理能重叠时，其服务下界取最大值，不能直接相加。
- “保持当前 finalize 等阶段不变，前端需达到多少吞吐”是诊断计算，不能推广成所有阶段一起改变后的不可能性。
- trace 中观测到最短 D 驻留 43 周期，不自动构成每次操作的硬件服务下界。只有先证明固定结构中所有相关操作都至少占用 43 周期，才能使用 `N_parent * 43 / (128*f)`；改变容量、时钟或服务链后该界失效。

论文所需结论是“当前实现及条件下的差距有证据解释”，并不需要“任何 FPGA 永远不能超过 GPU”。

## 10. E2 与完整流程：保留边界，不把 resident 胜利外推

主结果可以研究核心 resident 加速，但另列一次性构建的 E2：

`T_E2 = T_required_preparation + T_input_transfer + T_launch/control + T_core + T_output_transfer + T_required_postprocess`

这个加法只适用于互不重叠且没有重复记账的分段。若 `T_core` 使用 resident 墙钟时间，其中已包含的 launch、逐 wave 主机读回或同步成本不得再次计入 `T_launch/control`。若传输、核心执行或 CPU 处理发生重叠，应按实际时间线总跨度或关键路径计算 E2，不能直接相加各阶段独立耗时。

- 区分生产路径必须执行的转换／检查，与研究时的完整 golden 验证、归档或 SHA 检查；后者不能随意全部塞入正式运行时间，也不能删掉实际必需检查。
- 能实测的 CPU 构造／后处理实测；无板传输与调用成本只能作为来源明确的估计或参数，不由 AI 臆造“测量值”。
- 没有真实多构建调用场景，就报告单次构建；BNN/LSTM 的真实 40 samples 是本次 batch，不是凭空制造的跨调用摊销。
- resident 优于 CPU 不自动代表 E2 或 VPR Process 优于 CPU。可以把这三类结果分别报告，并保留无收益的范围。
- ALT 输出一致只支持相应 ALT 合同。保留与 STRICT 的 congestion 差异、已有 native/QoR 资格范围以及同家族留出的限制。

## 11. 结果字段与正式成果判定

不要用一个 `fpga_seconds` 混合三种来源。可在新结果中建立这些字段，具体名称可适配仓库 schema，但含义必须分开：

```json
{
  "research_goal": "CPU_PRIMARY_GPU_COMPARATOR",
  "requires_gpu_win": false,
  "board_measured": false,
  "core_scope": "complete_core_ooc_with_declared_external_memory_model",
  "full_core_functional_verified": false,
  "full_core_fit_verified": false,
  "full_core_routed_clock_verified": false,
  "rtl_model_calibrated": false,
  "full_batch_outputs_verified": false,
  "qualified_clock_mhz": null,
  "fpga_assumed_frequency_seconds": null,
  "fpga_resident_estimated_seconds": null,
  "cpu_baseline_receipt": null,
  "cpu_speedup_estimated": null,
  "gpu_speedup_estimated": null,
  "memory_service_evidence_type": "declared_simulation_assumption",
  "cpu_primary_goal_met_in_simulated_scope": false
}
```

以上是初始状态示例，不是本轮结果。按实际完成情况写入。

- 完整核资源／时序尚未通过：秒数保持为假设频率预测；不以局部 5 ns 证明完整核 200 MHz。
- 完整核心、所声明时序范围、输出和有限模型校准成立：可以给出 **经实现频率支持的模拟 resident 时间与模拟 CPU 加速比**，不必等待实板。
- 外存服务若仍是假设，应在主表旁明确标注，不能因为 RTL 校准通过就改成实测 HBM。
- 只有在所声明 CPU 基线与范围内得到一致优势，才把 `cpu_primary_goal_met_in_simulated_scope` 设为 true。GPU 更快不阻止该状态。
- 若原 schema 中 `fpga_seconds` 专指实板，继续保持 null，并新增上述模拟字段；不要因为实板字段为空而否认已完成的仿真研究，也不修改历史结果含义。
- 无实板则 `board_measured=false` 始终保留。

## 12. 最终交付

交付一个完整、可检查的候选及其结果，而不只是下一轮建议：

1. 真实完整 top、配置、仿真 testbench、校准模型及可重放命令。
2. 完整功能差分、实际综合资源、布线时序、约束和工具／part 记录；失败尝试保留。
3. 最终候选 BNN40/LSTM40 的完整有限模拟及软件比较；按实测、RTL 周期、实现支持的模拟、纯条件预测分别标识。
4. CPU 线程选择与最强合资格基线说明、复用 GPU 证据、resident/E2/Process 范围表。
5. 瓶颈分解与小范围机制对照，说明 GPU 更快的具体原因，避免普适不可能性宣称。
6. 新报告 `docs/lookahead_fpga_cpu_primary_closure.md`，包括目标变更、器件选择理由、正式结果或具体失败点、论文可用 claim ledger。
7. 独立 FPGA 小节草稿，可写入新的文档；保留原稿不覆盖。只有证据支持时才填“模拟加速×倍”，不得预填期望胜出数字。
8. 校验归档、提交独立分支、推送并核对远端完整 SHA；说明是否仍有作业，未完成时明确剩余项。

**新的停止条件不是 GPU 更快，也不是缺少实板。** 若真实完整核资源／时序仍失败、有限模型无法校准、输出不一致，或同范围最强合资格 CPU 不再被超越，应给出该具体原因和已尝试的有界修复。不要宣称所有 FPGA 方案不可行，也不要自动扩大到新器件或新算法的无限搜索。

## 13. 可追溯来源

- 本轮固定报告：[lookahead_fpga_local_fabric.md](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/3c7f96e6037030949b729240977c2ced373843c6/docs/lookahead_fpga_local_fabric.md)
- 有限模型：[finite.hpp](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/3c7f96e6037030949b729240977c2ced373843c6/accel/lookahead/fpga_local_fabric/model/finite.hpp)
- 实际 CUDA：[cuda_prepared_pop.cu](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/3c7f96e6037030949b729240977c2ced373843c6/accel/lookahead/fpga_sparse_stream_r2/cuda_prepared_pop.cu)
- AMD U280 DS963：[产品规格](https://docs.amd.com/r/en-US/ds963-u280/Alveo-Product-Details)
- AMD U55C DS978：[产品规格](https://docs.amd.com/r/en-US/ds978-u55c/Product-Details)
- AMD U250 DS962：[产品规格](https://docs.amd.com/r/en-US/ds962-u200-u250/Alveo-Product-Details)、[平台资源说明](https://docs.amd.com/r/en-US/ds962-u200-u250/FPGA-Resource-Information)
- AMD DS890，表 17：[Virtex UltraScale+ HBM 资源](https://docs.amd.com/api/khub/documents/dGU6Y~1b8XPqDFk5ulti6g/content)

