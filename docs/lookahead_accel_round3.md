# Lookahead FPGA 加速实验：第三轮

目标为 FPGA 分别优于基础 CUDA、优化 CPU 和原 VPR 多线程，软件基线之间不要求排序。**目前尚未证明这一目标。**

分支 `accel/lookahead-round3-20261108` 从 `d6b2ea2` 创建，不合并 main。
新输出目录为 `results/lookahead_accel_round3_20261108T141500Z`。前两轮、CPU 论文证据和用户未跟踪的指导文档保留。

## 第一阶段

使用项目冻结的 Hecate 两层架构，由 native VPR 实际生成 3×3、W8 的完整 RRG：654 节点、1,570 边、8 个全局 sample、384 条跨层边。没有截断图或筛选 sample。六个非平凡 sample 均实际访问两层并产生跨层入队，heap 峰值最高 317，超过顶部 127 项缓存；另两个合法的单节点 sample 也完整保留。外部 queue 逻辑读写总数为 5,253 / 3,697。

全部紧凑 sample map 与 native golden 逐位一致；原 VPR 多线程在同一完整 RRG 上生成的最终 wire map SHA256 也一致。这次原 VPR 运行用于正确性核对，不将完整构建计时混入 E1。

CPU/CUDA 在同一 H100 工作节点上顺序测量，使用同一 NUMA 的物理核。每配置五个全新进程，每进程首调用加五次 warm 完整 batch。CPU 保留 1/2/4/8 worker，CUDA 为基础核的 8 个 CTA、每 CTA 128 线程。GPU 任务 `job-d108a56a-1534-4e03-824a-da059bfa74ab` 已成功完成。

| 同一完整 3D workload | cold-first E1，μs | warm E1，μs |
|---|---:|---:|
| 紧凑 CSR CPU，1 worker | 171.651 | 139.436 |
| 紧凑 CSR CPU，2 workers | 222.075 | 148.671 |
| 紧凑 CSR CPU，4 workers | 199.724 | **61.716** |
| 紧凑 CSR CPU，8 workers | 268.275 | 68.033 |
| 基础 CUDA，8 CTAs | 42,937.183 | 917.024 |

表中 cold 为五个进程首调用的中位数；warm 先取各进程五次调用中位数，再取跨进程中位数。没有预热后冒充 cold。分配及图上传在调用外；标签、heap 计数和输出初始化、完整搜索、完成检测在每次 E1 内。CUDA cold event 区间包含首次 launch/lazy-module 开销；设备初始化、上传和回读另存 service 时间。CPU 是 C1 紧凑 CSR 对照，不冒充原生 flat/pipeline 的 E2。

沿用第二轮单 resident 核，heap127、label64、cost64：功能 RTL 为 **1,260,676 周期**；受限 RTL 为 **4,483,179 周期**，所有结果端口逐位匹配且最终排空。U280 OOC 实现通过 200 MHz，setup +0.441 ns、hold +0.019 ns，27,154 LUT / 31,004 FF / 4 DSP / 49 BRAM18 等效块。

因此功能模型对应 6.303380 ms，受限模型对应 **22.415895 ms**。这些是 RTL 周期结合时序通过的目标频率得到的时间，不是实板实测，也不是 C 仿真宿主时间。要胜过已测的最强 warm 软件配置，200 MHz 下最多允许 **12,343 周期**；当前受限核慢约 363 倍，不能宣称 FPGA 优势。

## 第二阶段的控制与判断条件

单、双完整 resident 引擎采用相同搜索代码、heap127 / label64 / cost64。双引擎各有独立的完整队列、标签、输出和缓存，以 native sample 顺序的前后两半分工。两半各有 1,621 次 pop、3,648 次 edge scan；实际 RTL 重叠和完成时间差另行记录，不用逻辑负载相等代替重叠证据。

受限模型固定 64 周期最小请求延迟、一个共享 bank、每四周期最多一个原生 AXI R/W beat、每端口每方向两个 outstanding，全局读/写 credit 池各八个。端口位宽单独记录，窄 beat 也占完整服务槽。返回端每端口一个有限槽，地址保持期间预留全局 credit。该模型已通过背压、burst、全局 credit 和排空自检；它是合成敏感性模型，尚未校准为真实 HBM。

访存优化选择 packed label/write-back。已有单引擎标签读写为 8,390 / 14,996，其中 10,464 次写为逐 sample 初始化。先以 64 位打包 visited/expanded 的 write-through 版本隔离布局收益，再在同一源码和缓存配置下用 `LA_LABEL_WRITEBACK=1` 比较写回策略。dirty eviction 与每个 sample 的最终 flush 都计入 E1；FP32 位模式不变。没有同时改 heap 或 CSR。

四引擎及下一档完整 3D 图必须等待双引擎在同一受限模型、各自通过实现的频率下获得实际时间收益。共享状态机不作为前置条件，不扩展到 8/16 contexts。大图性能模型与完整 lookahead E2 等核心架构显示可行性后再推进。

第一阶段原始表见 `report_checkpoint1/report.md`，后续测量完成后在本文件追加阶段结论。完整日志、源绑定和输入哈希保存在上述独立输出目录。
