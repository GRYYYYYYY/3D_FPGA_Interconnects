# 选题 A 实现与研究边界

## 迁移关系

| 来源 | 本项目的具体实现 | 尚未实现或不能直接等同的内容 |
|---|---|---|
| H3D | 层区间与共享垂直节点建模；按层区间生成 CHANZ 候选；失败时完整图回退 | HBT 位置优化、论文动态规划、全树最优性；相邻工程已有的 A3 需要后续接入 |
| InstantGR | 搜索后端抽象；CPU 批次并行；CUDA 同步松弛基线 | 网格 `.cap` 无法替代 FPGA RRG；未复现其算法和性能 |
| RouterAcc | 顺序候选访问、AXI 请求/结果分离、FIFO 和流水线代价计算 | 完整 A* 引擎、图存储控制器、HBM 银行映射、板级数据通路 |
| LaZagna/VTR | 原生 XML/SQLite 图投影、switch ID、容量、导回 VPR 检查和 STA | 本轮大图实测是 Hecate/VTR；没有把它冒充 LaZagna 论文架构复现 |

参考：[H3D 论文](https://www.cse.cuhk.edu.hk/~byu/papers/C297-ICCAD2025-3DRoute.pdf)、[InstantGR 官方仓库](https://github.com/cuhk-eda/InstantGR)、[LaZagna 官方仓库](https://github.com/sharc-lab/LaZagna)、[VTR 文件格式](https://docs.verilogtorouting.org/en/latest/vpr/file_formats/)。本项目没有复制这些仓库的算法源码。

## 数据和容量语义

图为固定有向多重图。原始 RR node ID 与 edge ordinal 保持可追溯，CSR 仅重排邻接访问；相同端点、不同 switch 的边不会合并。节点包含类型、容量、XY 边界和层区间，CHANZ 可以跨越多个层。

一个 Net 的多条支路共用节点时，只占用该节点一次。不同 Net 的占用相加，最终必须不超过容量。CHANZ 的所有入边和出边共用其节点容量，不能分别获得新的容量预算。

源文件中的完整 switch/R/C 信息留在权威 XML/SQLite 中。计算投影使用可解释的整数代价，没有把 R/C、真实工艺寄生或 clock pin 语义捏造为常量。独立图审计不等于 VPR FULL 检查；存在非可编程 short/buffer 或双向 pass-gate 的图暂时拒绝导入，避免遗漏闭包与电气约束。显式跨层边可导入，但额外共享物理 bus-mux 组必须由原工具验证。

文本 `graph.rrg`：首行 `H3DRRG 1 N M`；N 行节点：`external_id kind capacity xlow ylow zlow xhigh yhigh zhigh`；M 行边：`external_id dense_src dense_dst switch_id base_cost vertical_entry`。类型顺序为 SOURCE、SINK、IPIN、OPIN、CHANX、CHANY、CHANZ。

`nets.txt`：首行 `H3DNETS 1 K`；随后每行 `net_id dense_source sink_count dense_sink...`。重复 SINK 类、多个驱动或不匹配类型会被拒绝。重复 pin 到同一 SINK 类的情况需要 pin-aware 接口，不能去重后假装完整电路。

## 搜索与协商

每个 Net 从 SOURCE 开始构造树。对每个终端，从当前树的所有节点同时启动 Dijkstra，以零增量代价复用已有树。严格正边权保证新增支路不产生零代价前驱环，回溯返回有向边 ID。

`--tree-objective source` 是可选的源点构树对照。每次搜索仅以原 SOURCE 为零距离源，
已有支路保留其源点距离；GPU 同一快照中复用这一组距离，回溯后跳过已存在的共同前缀。
CPU/GPU 的多终端根到叶距离用独立 Bellman–Ford oracle 校验。
该模式暂时只支持完整图的 CPU/活跃前沿 CUDA，不支持 portal 剪枝或旧 `cuda_dense`。
它可能缩短源到终端的路径，但不最小化总树长，也没有时序关键度反馈；大图中可能增加线长和拥塞。

候选模式按 `(layer_low, layer_high)` 对 CHANZ 分组，每组选择几何距离得分最低的 K 个节点。它是启发式剪枝，不保证最优；剪枝图无法连接某个终端时，重新搜索完整图。当前直接跨层边不参与 CHANZ 排名。

对进入资源 v 的边 e，公共代价为：

```
base = base_cost(e) + vertical_entry(e) * vertical_penalty
excess = max(0, occupancy(v) + 1 - capacity(v))
cost = min(INF, base * (1 + history(v)) + present * excess)
INF = 0x3fffffff
```

零容量、非法或饱和代价不可通过。成本使用 64 位中间值，CPU/GPU 的路径距离也使用 64 位。`history` 对超用资源累加，`present` 每轮增长。数值饱和会导致失败而非绕回低代价。

每轮只重布线未连接或经过超用资源的 Net。一个批次先移除其旧树，所有线程读取同一占用快照，线程间没有写共享搜索状态。搜索完成后按确定顺序提交：发现冲突先用实时占用做硬容量修复；若不可达，则用实时协商代价重搜，使下一轮能继续迁移拥塞，避免保留过时快照形成反复竞争。

`--schedule portal` 依据上一轮树的 CHANZ 使用集合分批。第一轮尚无树，这一启发式不能提前预测全部冲突。它与候选限制是不同机制，正式消融应分别控制。

成功条件是全部 Net 连通且总 overflow 为零。失败 Net 不保留半棵树。达到迭代预算、不可达或代价饱和时输出显式失败及全部计数，不宣称不可布证明。

## GPU 正确性边界

旧 `cuda_dense` 保留 incoming CSR 双缓冲 Bellman–Ford 式全图松弛，作为测量对照。

新 `cuda` 的图、距离与边代价驻留设备。每棵树或修复重试上传 occupancy/history/allow，设备生成与 CPU 相同的整数边代价。每个活跃顶点由一个 warp 扩展出边；距离的并发读写都用 64 位原子操作，每轮标记去重，下一前沿最多 N 个顶点。前沿耗尽后距离收敛，才沿满足 `d[u]+cost(e)=d[v]` 的入边回溯。正边权使回溯距离严格下降，避免前驱环；不在目标首次可达时提前停止。

同一树代价不变时，新增树节点作为零距离源，只传播新的距离降低；代价快照改变（新树、冲突修复、候选回退）必须重置。GPU 回传目标路径，不回传所有顶点的前驱。CPU/GPU 等代价路径的选择可不同，正确性以独立最短路 oracle 和 FULL 检查为准，质量通过 VPR 时序/线长比较。

设备初始化发生在 `routing_seconds` 之外；`process_seconds` 包括初始化、图加载和结果输出。`gpu_metrics` 记录准备次数、搜索次数、松弛轮数、前沿顶点数、H2D/D2H 字节和同步完成的主机墙钟时间；这些不是 CUDA Event 纯 kernel 时间。GPU 任务默认结束于独立审计，通过哈希绑定的 CPU 后处理执行 FULL/STA，避免 VPR/Tcl 环境依赖占用 GPU 作业。

新的规模实验 `run_scaling.py` 使用另一条流程：携带校验过的 Tcl/TBB 等依赖，在同一 GPU
节点执行原 VPR 与 GPU 的路由至 FULL/STA 配对计时，完整流程包含独立审计和导出。
详见 [规模实验协议](scaling_protocol.md)。首次实现仍对每棵树上传完整节点状态、计算全图边代价，
并等待全部可达距离收敛。GPU 内部路径搜索更快不等于与目标相关的搜索工作量更少；
需要结合前沿访问数、状态上传字节、失败/超时和实际完整流程时间判断扩展性。

## HLS 和工具选择

使用 AMD Ross `hls-pragma-scope`、`hls-pipeline`、`hls-dataflow` 规则审查：INTERFACE 仅位于顶层，PIPELINE 位于各单层循环内，DATAFLOW 顶层只声明通道并调用 load/compute/store；每条 FIFO 恰好一个生产者和一个消费者。

使用前查询了 Vivado MCP，会话列表为空。该任务的硬件内核属于 Vitis HLS，当前连接器没有 HLS flow 工具，因此直接调用已安装的 2022.2 `vitis_hls -f`；不使用新版本的 `vitis-run` 或 `hls::task`。协同仿真由 HLS 调用 XSim。没有额外启动 Vivado GUI。

顶层 AXI 指针缓冲区在联合仿真中按声明 depth=4096 访问，因此 testbench 分配完整深度，并检查 count 之外的输出未修改。内核无共享目标节点写回，避免并发更新占用；它仅计算候选代价，CPU 保留提交与全局控制。

## 可复现实验协议

固定 RRG、端点、布局、整数目标函数和迭代预算。`batch_serial` 与 `parallel` 仅改变线程数，检查整个路由指纹一致；`serial` 改变批次大小，不能直接归因于线程；`portal` 同时打开候选与调度，属于组合探索变体。

重复实验顺序轮换，路由进程顺序执行；保存每次输出、返回码、失败、图审计和实际 process 时间。本轮部分测量期间并发运行了 HLS/XSim 验证，共享主机其他负载也不受控制，两轮结果仅作初步测量，不构成统计显著性或论文级整体加速结论。VPR 原算法使用时序驱动目标，与当前单位代价原型不同，不能用二者时间直接证明同质量加速。
