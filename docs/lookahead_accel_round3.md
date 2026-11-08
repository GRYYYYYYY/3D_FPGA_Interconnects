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

## 第二阶段已完成的测量

相同完整小图、相同缓存配置、相同共享 bank 和全局 credit 池：

| 变体 | 功能 RTL 周期 | 受限 RTL 周期 | 时序通过频率 | 受限时间 ms | LUT / FF / DSP / BRAM18 |
|---|---:|---:|---:|---:|---|
| 匹配单 resident | 1,260,676 | 4,483,179 | 200 MHz | 22.415895 | 26854 / 31327 / 4 / 49 |
| 双完整 resident | 630,600 | 2,247,992 | 200 MHz | 11.239960 | 53367 / 61100 / 8 / 98 |
| 单引擎 packed write-through | 1,196,996 | 3,971,796 | 200 MHz | 19.858980 | 25498 / 30449 / 4 / 51 |
| 单引擎 packed write-back | 1,216,708 | 4,018,356 | 200 MHz | 20.091780 | 25549 / 30869 / 4 / 51 |

双引擎时间收益为 **1.9943×**，故 `scale_gate.json` 放行四引擎及下一档完整 3D 图。双引擎 setup +0.562 ns、hold +0.019 ns；通过 Vivado MCP 再次打开 routed DCP 复核。两引擎活跃区间重叠 2,247,172 周期，活跃周期为 2,247,172 / 2,247,718，完成差为 546 周期；全局 outstanding 峰值 4R / 8W。活跃区间按 `ap_idle` 撤销计数，包含访存等待，不代表每周期同时完成有用运算。

打包布局减少 11.41% 受限周期；packed write-back 相对自己的 write-through 控制增加 1.17% 周期，**不作为正收益优化推广**。标签读请求为 8,390 → 4,276 → 4,276，写请求为 14,996 → 4,860 → 2,968，写 beat 为 14,996 → 9,764 → 7,872。graph、queue、result 流量保持相同。写回减少请求却没有减少总时间，具体关键路径归因未进一步隔离。

共享 bank 每四周期一个原生 beat，在 200 MHz 下上限为 50 Mbeat/s；只有全部使用 512 位有效 beat 时才对应最高 3.2 GB/s。实际 graph / queue / result / state 端口为 256 / 128 / 512 / 32 位，打包标签版本 state 为 64 位。HLS 每个 AXI master 内部配置 16R / 16W outstanding 槽，但受限模型仍只准入全局 8R / 8W、每端口 2R / 2W；两者分别记录。

按单引擎已观察到的 71,340 个 beat，仅固定 bank 的服务跨度就至少需要 285,357 周期。这个小输入下的条件下界已超过 CPU 周期预算，说明只复制引擎不足以达到最终目标；它不是实板时间或大图外推。

## 放行后的扩展实验

本轮下一档采用完整 4×4、W8、两层 RRG：1,592 节点、4,176 边、12 个 native sample。外部 queue 逻辑读写为 70,151 / 33,712，比小图显著增加。这是本轮的中档规模阶梯，报告实际规模，不将其外推为工业级大图性能。

四引擎继续用原 scalar label 布局及 heap127 / label64 / cost64，避免将复制收益与标签打包混在一起。主机验证覆盖两张完整 native 图和 200 组 0–13 sample 的随机 batch；全部 15 个主机测试通过。小图四份 pop 数为 546 / 1,075 / 546 / 1,075，下一档为 3,791 / 3,504 / 3,711 / 3,586；实际 RTL 区间另测。

下一档 CPU/CUDA 独立任务 `job-032cba1b-9f94-43f3-b4c8-7db4abf95b20` 成功完成，25 个进程、150 次完整 batch 逐位一致；最佳 CPU warm E1 为 201.099 μs（8 workers），基础 CUDA 为 2.425664 ms（12 CTAs）。200 MHz 下胜过已测 CPU 的预算是 40,219 周期。完整 cold/warm 配置表在机器报告中保留。

原 VPR 在该图上生成的最终 wire map 与导出构建器逐位一致。其后续一次 routing 未收敛，退出码为 2；这是完整 lookahead 组件核对，不是 VPR 布线收敛测试。

小图四引擎已完成全部 HLS 阶段和受限 RTL：功能周期 418,606，受限周期 **1,481,556**，在实际通过的 200 MHz 下为 **7.407780 ms**，相对同配置双引擎获得 **1.5173×** 时间收益。实现为 105,529 LUT / 122,163 FF / 16 DSP / 196 BRAM18；setup +0.010 ns、hold +0.019 ns，Vivado MCP 重新打开 routed DCP 后复核一致。该频率仅指核心 OOC，不能据此声称完整板级接口已通过时序。

四路全部活跃的重叠为 769,435 周期，平均活跃引擎数 3.0375；各路活跃周期为 769,435 / 1,480,042 / 769,703 / 1,481,048，完成差 711,613，最大/最小为 1.9249。原顺序连续分块的负载不均限制了复制收益；没有重排、复制或删除 native sample 来改善数据。全局 outstanding 峰值达到 8R / 8W，共享 bank 和 credit 池没有随引擎数增加。

该小图四引擎仍比本轮最佳 C1 warm 慢 **120.03 倍**，也慢于基础 CUDA。其正收益是相对匹配双引擎的微架构收益，最终 FPGA 优势目标仍未达成。

下一档图的双、四引擎也分别完成全部 HLS 阶段，并通过 200 MHz。其功能 RTL 为 3,488,728 / 1,799,906 周期；资源和 setup/hold 与对应小图实现一致。双引擎全部 32 份、四引擎全部 52 份综合 Verilog 在两种输入间逐字节一致，记录见 `dual_cross_input_rtl_manifest.json` 与 `quad_cross_input_rtl_manifest.json`，没有针对已知图预计算搜索。八个核心实现的 routed DCP 哈希、源绑定、时序与资源汇总在 `implementation_artifacts_manifest.json`。

扩展图受限 RTL 最终也全部通过，四路结果逐位一致并排空：双引擎 **15,410,568 周期 / 77.052840 ms**，四引擎 **7,984,906 周期 / 39.924530 ms**，同输入、同缓存、同访存限制下获得 **1.9300×** 时间收益。

双引擎活跃周期为 15,150,494 / 15,410,288，重叠 15,150,494，完成差 259,794。四引擎为 7,984,396 / 7,194,143 / 7,786,916 / 7,653,832；四路全部重叠 7,194,143 周期，平均活跃引擎数 3.8346，最大/最小为 1.1098，完成差 790,253。双、四引擎全局 outstanding 峰值分别为 4R/8W、8R/8W；bank 服务槽利用率为 14.16%、27.33%。队列读写共 311,589 个 beat，占四引擎总量 545,615 的约 57.1%。

## 最终同口径 E1 对照

下表 CPU/CUDA 为同一工作节点上的 warm 实测中位数；FPGA 为完整受限 RTL 周期按通过实现的 200 MHz 换算。单位均为 **ms**，包含状态初始化和完整 sample batch。FPGA 数字不是实板测量。

| 完整输入 | 最佳 C1 CPU | 基础 CUDA | 单 resident RTL | 双 resident RTL | 四 resident RTL | 胜过已测最强 warm 软件的周期预算 |
|---|---:|---:|---:|---:|---:|---:|
| 3×3，两层，654 节点 / 8 samples | 0.061716（4 workers） | 0.917024（8 CTAs） | 22.415895 | 11.239960 | 7.407780 | ≤12,343 |
| 4×4，两层，1,592 节点 / 12 samples | 0.201099（8 workers） | 2.425664（12 CTAs） | 未运行 | 77.052840 | 39.924530 | ≤40,219 |

四引擎在两张图上仍分别比最佳 C1 warm 慢 120.03 / 198.53 倍，也均慢于基础 CUDA。扩展图所有 CPU/GPU cold-first 与 warm 配置如下，统计方法与第一阶段相同：

| 4×4 workload | cold-first E1，μs | warm E1，μs |
|---|---:|---:|
| CPU，1 worker | 871.871 | 813.733 |
| CPU，2 workers | 500.773 | 416.775 |
| CPU，4 workers | 499.213 | 377.890 |
| CPU，8 workers | 418.675 | 201.099 |
| CUDA，12 CTAs | 43,632.961 | 2,425.664 |

四引擎扩展图已观察到的流量，在固定共享 bank 下仅服务跨度就至少需要 2,182,457 周期，即 10.912285 ms，仍超过该图的软件周期预算约 54 倍。此处是保持已观察流量不变的模型下界，不是实板测量或大图预测；复制引擎本身不能消除这项流量成本。

## 计时覆盖与后续依据

本轮的同口径实测分母为 C1 紧凑 CSR CPU 与 G0 基础 CUDA。B0 原 VPR 多线程用于完整 wire map 核对，B1 native flat 提供全局 sample 与 golden；未增加 B0/B1 的 E1 插桩，也没有将历史 flat/pipeline 或原 VPR 的 E2 时间用作 E1 分母。因此，“胜过本轮最佳软件配置”只是必要门槛，不能替代对所有原生软件基线的最终验证。

当前结果支持完整 resident 引擎复制的局部收益，但尚不支持推进大图 FPGA 时间预测或完整 lookahead E2。先用已归档的逐端口流量和周期检查外部 heap 请求粒度、状态初始化及搜索串行等待，再选择一个独立改变与匹配控制。小图四引擎的 bank 服务槽利用率为 19.26%；功能 AXI 模型下也需 418,606 周期，仍远高于 12,343 周期预算。功能模型并非零延迟算术下界，这一观察用于定位后续剖析方向，不用于声称物理性能极限。

一个可直接追溯的线索是：小图的 5,253 / 3,697 次外部 heap 逻辑读写，对应 RTL queue 端口的 15,759 / 11,091 次 AXI 请求，分别为三倍。下一项实验可先核查三字段 Entry 的请求合并，再与现状比较；本轮没有预先计入这种尚未实现的收益，也没有将访存模型调整为更宽松的参数来改善排序。

共享多上下文状态机没有成为本轮前置条件，未扩展至 8/16 contexts，也未全面重写异步调度器。STRICT_FP32、完整 sample 搜索和每次状态初始化保持不变。所有 FPGA 时间均来自 RTL 周期和通过时序的核心频率，没有实板测量，C 仿真宿主时间不参与加速比。

## 验证与归档入口

15 项主机测试通过；两套 CPU/GPU 作业共 70 个独立进程、420 次完整 batch（含保留的 2D 控制）逐位一致。八个 HLS cohort 的 csim、综合、功能 cosim、实现及对应受限 RTL 均通过；567 项最终源绑定、输入、结果端口、credit 与排空检查通过。前两轮归档的 888 个文件、冻结 CPU/VPR 二进制和未跟踪指导文档保持原哈希。

- [最终完整表、逐端口计数与重叠](../results/lookahead_accel_round3_20261108T141500Z/report_final/report.md)，[机器可读结果](../results/lookahead_accel_round3_20261108T141500Z/report_final/report.json)。
- [3×3 图表](../results/lookahead_accel_round3_20261108T141500Z/plot_final_d3/evidence.png)、[4×4 图表](../results/lookahead_accel_round3_20261108T141500Z/plot_final_d4/evidence.png)；同目录提供 PDF/SVG。
- [证据清单与 SHA256](../results/lookahead_accel_round3_20261108T141500Z/evidence_snapshot/index.json)，[最终审计](../results/lookahead_accel_round3_20261108T141500Z/evidence_snapshot/source_binding_final_audit.json)，[历史保护复核](../results/lookahead_accel_round3_20261108T141500Z/evidence_snapshot/preservation_final_audit.json)。
- [计时覆盖](../results/lookahead_accel_round3_20261108T141500Z/evidence_snapshot/scope_manifest.json)与[阶段决定](../results/lookahead_accel_round3_20261108T141500Z/evidence_snapshot/completion_decision.json)。

证据包包含两张完整小型 3D 图、workload、native golden、运行源码快照、原始软件测量、RTL 输出和实现报告；DCP、波形与构建目录留在本地，其关键哈希已归档。第三轮提交到独立分支，不合并 main。
