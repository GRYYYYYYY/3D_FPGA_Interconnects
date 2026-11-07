# 原生 lookahead 切片与存储实验

本轮按 `results/native_lookahead_analysis_20261101/next_experiment.json` 执行 D0–D3。实验源码在 `vendor/vtr_cpu_slices`，继承两处并行 BB 通知修复；历史 solver、结果和默认选项保持原状。过程文件在 `results/native_cpu_slices_20261101`。运行中的阶段不能视为已通过。

## 实现与对照

`VPR_CPU_LOOKAHEAD_MODE` 选择同一候选二进制中的消融：

| 模式 | 采样表 | 调度与插值 |
|---|---|---|
| legacy | 原 vector 单元 | 提取的旧组内实现，原全层重复插值 |
| refactored | 原 vector 单元 | 已有重构组内控制，原全层重复插值 |
| slice | 原 vector 单元 | 原组内调度；每个使用的 segment/channel 最终只插值一次 |
| compact | 12 字节标量单元 | 与 slice 相同的组内采样和最终插值 |
| bounded | 同一标量单元 | 有界组批；最后完成的样本原序归并、提交和填充本 source layer |

另以历史 `vpr_cpu` 为冻结主线对照，以 `VPR_HYBRID_LOOKAHEAD_TASKS=1` 运行旧全局 pipeline。D0 未复现历史重构退步，因此在正式测量开始前将同二进制 pipeline 加入 D3 对照，区分已有跨组并行与新有界方法。legacy 与历史 ELF 不是同一构建，二者用途需分开说明。

冻结 CPU 已包含旧组内采样并行，不是未优化的原版 VPR。`frozen → slice` 同时包含代码重构和插值重排，不能将其全部性能差异归于插值；`slice → compact` 比较同二进制的存储实现；`compact → bounded` 比较的则是跨组调度、工作区复用与对齐、切片提交的组合，不能分别声称每一部分已有独立性能收益。`pipeline → bounded` 用于观察新方案相对已有跨组调度的增量。

标量表保留独立 occupied 位，不能以 `Cost_Entry::valid()` 代替“曾插入过条目”。严格 `<` 更新，保留相同 delay 时最早的 congestion；不修改 flood 起点、堆、扩展次序或坐标映射。通用 `Expansion_Cost_Entry` 的其他代表值方法不变。

bounded 首先保存起点 ID 等元数据，而不预分配全部组的结果表。每批样本数不超过结果表上限，工作 slot 各有私有 Dijkstra 工作区。各样本独占结果表，以 acq_rel 原子递减发布完成；最后一个样本按原序归并到首样本表并立即调用消费者。其他 worker 继续取任务，无忙等。组过大或预算过小则使用单表原序串行插入。批次间有屏障，因此不声称完全无全局同步。

最终 map 预先分配。每组只写一个 `(from_layer, channel, segment)` 区域，插值固定 `(from_layer,to_layer,channel,segment)`，保持原 x 外层/y 内层。未采样 source layer 对实际使用的类型补默认值，完全未使用类型保留原始 NaN。

## 内存约束

`VPR_CPU_LOOKAHEAD_TEMP_BYTES` 指定临时预算，`VPR_CPU_LOOKAHEAD_WORKSPACE_BYTES` 提供诊断得到的单工作区估计。调度据此减少 slot，并限制结果表数量至至多 `2P` 和剩余预算可容纳数量的较小值。结果表存储有明确上界，工作区对象数量有明确上界；原生优先队列仍可增长，因此这不是进程 RSS 的硬上限。预算连一个工作区和单表都无法容纳时仍需最小单槽工作集，日志明确给出估计值。图、最终 map、路由状态和分配器保留空间单列，不混入结果表上界。

令活跃组数为 `G`、单表单元数为 `C=L×W×H`、样本总数为 `S`、工作槽数为 `P`。旧 pipeline 保留 `G` 个组表及至多 `min(S,2P)` 个样本表，表头数组占用上界为 `24C[G+min(S,2P)]` 字节，另有有效单元的动态条目分配。新实现令活跃样本表上限为 `K≤2P`，在首样本表上归并，不另分配组结果表，因此标量表数组上界为 `12CK` 字节。这里比较的是实现的表存储上界，不是测得的峰值 RSS 或所有表必然同时达到上界；旧实现的尚未处理 token 也可能还没有分配表。全局起点/组元数据仍需 `O(G+S)`，最终完整 lookahead 表仍单独存在，不能据此声称整个算法内存与 `G` 无关。

## 验证与计时

D2 初版虽然全部合法，但 GEMM 四核在开启逐边计数器时，bounded 阶段达到 63.899 秒、累计 flood 230.691 秒；四槽各执行十次，峰值并发四，搜索工作计数不变。布局检查发现新增五个 uint64 计数器将工作区从 128 扩至 168 字节，连续存放且仅八字节对齐，本机缓存行为 64 字节。新增 alignment_gate 在同一二进制中比较原布局与隔离槽；前者通过 `VPR_CPU_LOOKAHEAD_UNALIGNED=1` 选择。GCC 11 未提供标准硬件干扰常量，对齐槽采用 128 字节 fallback，stride 为 256。该阶段用于识别诊断扰动，不以开启计数器的速度比宣称正式算法加速；原 D2 数据完整保留。

原生阶段均使用固定 packed netlist、placement、RR 图和输入哈希；同一比较使用相同物理核，TBB/OMP 及进程亲和性统一控制。所有计时变体都序列化 map，并与本轮原版串行资格产物逐字节比对。成功路由必须零超用，原生 FULL/STA 与独立原版读回 FULL/STA 均通过，独立检查不得改变路由 SHA。

D0 诊断启用 `VPR_CPU_TRACE`/lookahead report，不进入正式加速比。JSON trace 记录整体/嵌套阶段、flood 起点、push/pop/expanded/edge_visit/峰值队列及 RSS。新存储候选补有效表项、坐标、分配/释放、slot 及 ready/start/end。各事件可能嵌套或在多线程重叠，累计工作时间不得直接相加为墙钟。

D1 验证 ex5p 单/双层与 GEMM/elliptic 的 1/4/8 核。D2 检查 scalar representation 与 bounded scheduling，并覆盖单槽退化路径。D3 关闭诊断，用五变体、GEMM/elliptic 4/8 核、各三次重复及 rebuild/reuse 两种模式评估，共 120 项。共享缓存取同一原版串行产物；独立回验计入 workflow，主进程另报。宿主和内存共享，不声称独占或物理冷缓存。只有完整进程的重复增益与质量同时达标，才考虑推广。

`scripts/check_native_compact_costs.py` 从实际候选提取两种条目实现，已完成 100,000 个夹具、1,551,076 次字段逐位检查，含 NaN、无穷值、正负零、等值延迟与乱序完成。该检查不替代原生多层器件验证。
