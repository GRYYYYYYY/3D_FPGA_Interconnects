# Lookahead FPGA 加速第一轮实验证据

> 后续目标已按用户要求调整为“FPGA 优于其他几个基线”，不要求 GPU 快于 CPU。
> 本文保留第一轮原始目标及测量记录；后续实验见第二轮报告。

实验日期：2026-11-08。分支：`accel/lookahead-strict-20261108`，起点
`068aabd0f604a094c3b42b378028d9e9b5f54b39`。已完整阅读实验指导，实际完成
P0–P2 的导出、参考、CUDA、完整 HLS 核和小图实现闭环，并进行了五类优化的初步消融。
**目标 FPGA > 基础 GPU > 优化 CPU > 原 VPR 多线程尚未得到验证。**

完整数据见 [自动汇总表](../results/lookahead_accel_20261108T125500Z/report_final/report.md)、
[机器可读记录](../results/lookahead_accel_20261108T125500Z/report_final/report.json) 和
[可导出图表](../results/lookahead_accel_20261108T125500Z/report_final/evidence.pdf)。
大文件和工具工程留在本机的新实验目录，仓库只保存代码、摘要及关键报告。

## 已实际完成的范围

| 工作 | 实际结果 |
|---|---|
| 环境、输入、基线 | Vivado/Vitis HLS 2022.2；U280 `xcu280-fsvh2892-2L-e`；本机无 GPU，启智 H100 80GB 实测；冻结输入和 ELF 哈希核对 |
| Native workload | 在冻结的两个 translation unit 的独立副本中插入 opt-in 导出；直接读取全局 sample 列表、native RR accessor、`get_xy_deltas` 和 golden |
| STRICT_FP32 CPU | 独立 `std::priority_queue` 参考；逐位比较 sample map，原序 group merge；完整 tseng 和 BNN 均通过 |
| 基础 CUDA | 图预先上传；持久 CTA 组批；每任务私有 heap/labels；128 lanes 计算邻居，owner 按原序提交；仅返回 map/status；真实 H100 测量 |
| 完整 HLS | heap push/pop、CSR、visited/expanded、IPIN map、边过滤、终止与错误状态均在核内；不是浮点加法 PE 的外推 |
| FPGA 闭环 | 语义小图及完整 tiny-native RRG 的 csim/csynth/RTL cosim 通过；九个核心/控制版本的 OOC 布局布线和 200 MHz 内部时序检查通过 |
| 原生接回 | 将 tseng 的 HLS C 输出经验证适配器接回 native 原序归并和后处理，最终 wire map 哈希一致；这是离线正确性测试 |

旧 CPU 论文和 `results/native_*` 未修改，原有 owner/supervisor 未启动。
[保全审计](../results/lookahead_accel_20261108T125500Z/preservation_audit.json) 确认两个冻结 ELF 未变化。

## 输入和计时边界

| 完整 native RRG | 节点 | 有序边 | 全局 samples |
|---|---:|---:|---:|
| tiny-native，4×4 device / channel 8 | 552 | 802 | 4 |
| tseng | 93,276 | 860,020 | 8 |
| BNN，3D | 4,102,608 | 39,480,616 | 40 |

tiny-native 由 VPR 对实际小 BLIF 建图，未用截取子图冒充完整 workload。
没有复制任务增加 GPU 占用率。所有后端使用同一 source、边序、cost 位模式、IPIN cell
映射和输出范围；eligible CSR 单独记录转换后的输入哈希。

E1 为图驻留后的整个 flood batch，包含状态/输出初始化、队列、图和标签访存、IPIN 记录与完成。
分配、图转换/上传、golden 校验和文件写出不在 E1；CUDA 使用 event，CPU 使用 wall clock。
E2 为原生完整 lookahead builder，包含 native 保留阶段、归并、插值、src/opin 和 minima。
GPU/FPGA 在线 E2 服务尚未完成，不能把离线导入时间算作其 E2，也不能用 E2 除以 E1。
本轮 native 流程在一轮 route 后以预期 rc=2 结束，仅接受完整 builder timer 和一致 wire map；
不宣称布线成功或 FULL/STA 已验证。

数值域为非负有限 normal FP32 或正零，关闭 fast math/FMA contraction，使用 RN。
保留严格小于比较、等 delay 入队、libstdc++ 等子节点堆选择、source 零代价、SINK break
及原序归并规则。subnormal、负零、负数、溢出等不支持候选显式报错；NaN 只作缺失输出哨兵。

## CPU/GPU 实测

主表采用修复后的完整确认 cohort `job-1478286b-b4a4-41b4-b659-10959b08f564`：
同一 worker、Xeon Platinum 8462Y+、NUMA 0 的物理核 0–7、10 CPU 的 cgroup 配额，
H100 80GB，CPU 编译器 GCC 13.3.0。所有命令成功。以下为三次测量的中位数：

| E1 工作负载 | C1 CPU，8 核 | 基础 CUDA | 输出逐位一致 |
|---|---:|---:|---|
| tseng，8 samples | 0.0359295 s | 0.647027 s，8 CTA | 是 |
| BNN，40 samples | 9.82417 s | 36.5854 s，40 CTA | 是 |

CUDA 分别约慢 18.01 倍和 3.72 倍。这是本实现的负结果，不是 GPU 性能上界。
严格 owner heap 和提交顺序形成串行链，samples 数也限制 CTA 并行度；这是从结构得到的
解释，尚无 Nsight 硬件计数器归因。CUDA 每个进程先 warmup 一次，再测三次；CPU 每次
启动进程测一个 batch，OpenMP 启动计入 E1。保留这一热身策略差异，不把当前数值当成
平台性能上界。第一作业还测了 tiny 的 1/2/4 CTA 和 tseng 的 1/2/4/8 CTA，全部保留。

同一确认 worker 上，native 各变体使用同样 8 物理核和输入，三次 map 均一致：

| tseng 完整 lookahead E2 | stock | per_group | pipeline | flat |
|---|---:|---:|---:|---:|
| 中位数 / s | 0.21 | 0.06 | 0.04 | 0.04 |
| 三次范围 / s | 0.21–0.21 | 0.06–0.06 | 0.04–0.05 | 0.04–0.06 |

日志分辨率 0.01 s，小差异不能作高精度结论。B0 开了 parallel router，但该版本的
wire sample 循环本身仍为顺序。保留 flat 和 pipeline 两者，没有挑较慢者作为唯一分母。
即使来自同一 cohort，E1 与 E2 的计时范围不同，仍不能彼此相除。

第一作业 `job-a23dba0b-d95d-4207-9eda-066d536ed91f` 成功，但 C1 未固定到 native
的 NUMA 核集合，仅保留为 pilot。第二作业 `job-90fc6e1f-326e-448a-8424-81273d0e5bed`
的 E1 全部成功，native E2 却因继承 `OMP_PROC_BIND` 导致主线程亲和性改变，被审计拒绝，
作业整体失败；其 E2 被排除。修复在本机四个 native 变体上验证后，才运行最终远端确认。
三个 cohort 分开保存，没有把较快的重复值拼成一组，也没有删除失败结果。

## FPGA 功能周期与优化

这些是独立单因素的初步版本，尚未叠加为统一高吞吐核，收益不能相乘。
以下均为同一完整 tiny-native RRG、四个 samples、自动 HLS AXI 功能模型的 RTL 周期，
不是实板/HBM 测量，也不是大图预测。

| 优化 | 对应控制周期 | 优化后周期 | 周期减少 |
|---|---:|---:|---:|
| eligible CSR，802→592 条边 | F0 410,625 | 397,195 | 3.27% |
| 64 项标签缓存 | cache-off 378,002 | 363,926 | 3.72% |
| heap 顶部 31 项缓存 | cache-off 378,002 | 293,852 | 22.26% |
| 四个 AXI master 对一个 | one-port 379,651 | four-port 378,002 | 0.43% |
| 双引擎并发 | 显式串行 410,772 | 208,948 | 49.13% |

cache-off 与 F0 差异来自访问封装和 HLS 生成代码，不能将全部差值归因于缓存。
双引擎在 RTL 中有 201,810 个重叠活动周期；两个端口输出逐位一致。单纯删除 DATAFLOW
仍得到 208,948 周期，因此真正串行控制使用前一引擎状态作为启动依赖。串行控制也允许
算子共享，HLS DSP 估计为 4，双引擎为 8；这是引擎复制收益，非共享流水线的交错调度收益。
八个逻辑 AXI master 不代表已经绑定八个物理 HBM 通道。单端口实现为 33,612 LUT、
45,045 FF、31 个 BRAM18 等效；四端口 cache-off 为 23,193 LUT、29,192 FF、49 个 BRAM18 等效，
因此端口组织同时改变面积和缓冲开销，不能只归因于带宽。

F0 tiny 核的实现结果：LUT 20,973，FF 26,009，DSP 4，BRAM18 等效 49，URAM 0；
5 ns 约束下 setup WNS +0.986 ns、hold +0.019 ns。heap31：LUT 25,027，FF 30,176，DSP 4，BRAM18
等效 49，URAM 0；setup WNS +0.733 ns，MCP 独立检查 hold +0.019 ns。
cache-off 为 23,193 LUT、29,192 FF；heap31 相对它增加 7.9% LUT，
标签缓存为 24,264 LUT，增加 4.6% LUT。两者及 eligible CSR 均通过 200 MHz 的内部 setup/hold 检查。
双引擎为 41,974 LUT、50,686 FF、8 DSP，setup +0.474 ns、hold +0.019 ns。
频率仅报告通过的 200 MHz 目标，不用 estimated fmax 或 `1/(period-WNS)` 冒充实现频率。
这些是 core OOC；HD.CLK_SRC 未绑定，外部 IO 未加延迟，不能宣称平台 shell 时序已经收敛。

heap 下沉循环的综合 II=29；原始日志和 verbose schedule 显示队列 AXI 请求/响应的
跨迭代依赖，见 [结构化诊断](../results/lookahead_accel_20261108T125500Z/heap_ii_diagnosis.json)。
请求延迟从 1 改为 64 周期时，F0 为 2,007,435 周期，heap31 为 1,129,300 周期；
同结构 cache-off 为 1,955,466 周期，heap31 对其减少 42.25%。该测试仍缺共享读写带宽仲裁和真实 HBM 校准，
仅作为延迟敏感性证据。最初脚本误读复制来的旧汇总表，原记录保留，正确值来自新生成的
XSim transaction 文件并保存在 `result_corrected.json`。

## 验证、失败和复现

`ctest` 三项通过：关键语义、heap31 随机差分、label64 随机差分。包括 20,000 次
混合堆操作与标准库对比、每种缓存 200 张随机图、零环/同代价/输出碰撞/静态过滤，
以及容量、预算和不支持数值的显式失败。tseng/BNN 的完整 HLS **C** 回放时间不列为 FPGA 时间。

共享 AXI bundle 的双 DATAFLOW 引擎综合失败，保留日志。随后独立端口 RTL 输出正确但
C 后检查因适配器临时缓冲区 beat 对齐越界失败；按 64 字节倍数设置 cosim depth 后通过。
逻辑容量不变，没有通过丢弃任务或边规避问题。失败流程、命令、返回码和 source binding
均保留在新实验目录。

复现命令及二进制契约见 [后端 README](../accel/lookahead/README.md)。
新脚本拒绝覆盖已有输出，HLS 各阶段校验前置阶段和源码/输入绑定。原始大文件留在共享磁盘，
复制仓库到别处时需要补齐 README 中声明的冻结 VTR archive、runtime 和输入。

## 尚未完成的研究项

本轮完成的是第一阶段及初步消融，未声称整个优化路线完成。仍需：共享搜索流水线的多上下文
交错调度、物理 HBM 连接及有界带宽/延迟/背压模型、小中图校准后大图预测、cost LUT 驻留、
几何映射压缩、在线 GPU/FPGA E2 接入，以及代表性下游 FULL/STA 验证。
当前 O(samples×nodes) cell 映射和每上下文 E+1 heap 保留了语义，但占用较大；BNN 的
40-context heap 容量为约 18.95 GB，不能当成最终 FPGA 存储设计。实测单任务队列峰值
为 607,409 项，40 个 samples 共出队 272,831,946 次；计数见 `operation_counts.json`，
它们是软件操作计数，不是 FPGA 周期。观察峰值不能替代带溢出检测的容量/溢写保证。
没有生成未经校准的 FPGA 大图秒数或四平台排序。
