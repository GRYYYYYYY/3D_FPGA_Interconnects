# 主命题与定位

保持源上下文的双粒度依赖解耦：把定义 lookahead 输出所需的 source/layer/cost 关联与可解除的执行顺序分开，在 native wire-map 兼容路径和独立 whole-pair 波次路径中分别建立可检验机制。

- **C1 跨组解耦**：私有 sample 状态 + 原序 strict-delay 归并。Group/Flat/Pipeline 同 cohort 控制表明受益来自移除组屏障，不能归功于 Pipeline 库原语。包含 2D 对照；并非控制层数的等尺寸实验。
- **C2 搜索内解耦**：FP32 完整代价对、波次快照、严格改进、同桶闭包、源相对记录。shift0/20 原始完整 profile 的操作数揭示并行度/工作量交换。不能继承 STRICT 等价性，不能宣称任意 FP32 图的全局词典序最优。
- **C3 原生异构集成与有限映射**：共同的是逻辑 sample/context，不是统一 CSR。STRICT 保留 RRGraphView；ALT 单独转换图/映射。CPU/CUDA native E2/Process、QoR 和有限 RTL/model 支撑系统价值与边界。硬件尚无合格完整核频率。

## 最近工作与具体差异

LaZagna 为 3D 架构生成/评价提供基础，已更新为 ICCAD 2025 正式版本。Flatland 解决 placement。Poolad 等多 die lookahead 利用 intra-die 表和 die-crossing penalty 改善启发式，本稿改变所选构建策略的执行组织，不能说前人缺乏跨层意识。

MultiQueue routing 的部分 Dijkstra/A* 变体已有确定性和 serial equivalence；不能将所有优先级放松说成放弃正确性。Davidson GPU SSSP、delta stepping 和 SPLAG 已建立 bucket/frontier/coarse priority 的工作与并行度权衡。本稿区别在 source-relative/layer table、whole-pair FP32、闭包完成和 native consumer 的完整结合及因果控制，未宣称首创 bucket/atomicMin。

`compressed_map` 是更接近的替代方案。锁定可执行文件的单层断言与源码均明确排除当前两层图；此次仅做适用性预检，未做 unsupported 图的运行计时，未宣称性能胜出。map cache 是合法缓存命中替代路径；36 条已有正式复用记录经过独立 FULL/STA。本稿限定首次构建/身份不兼容，改变 netlist 不一定使 cache 失效。

## 标题和主结果

保留冻结稿现有题目，避免未经作者核对修改已登记题目。LSTM 不是整个研究预先盲选：未参与先前 ALT 调参，在它自身 qualification/timing 前冻结。原生 headline 限定八核同 cohort Pipeline；64-worker resident 是另一边界。s38417 CUDA 负结果和 ALT congestion 差异均保留。

完整核是否最终成功不影响本文这组软件机制与实测主结论；条件模型不是 achieved-frequency FPGA 性能。
