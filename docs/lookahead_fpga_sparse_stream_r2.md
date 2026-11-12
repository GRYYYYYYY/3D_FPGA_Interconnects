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

新增 commit proposal response、label/pending read、allocator、directory forwarding/publication 流水；独立持续吞吐、同 tail append/stale/capacity 校验仍在执行。小图通过不能替代大图状态 backing、完整候选 OOC 或新架构模型校准。

## 尚未完成

- m2c routed OOC 正在执行；资源、最坏路径、setup/hold 资格以实际报告为准。
- M3 完整并发域与容量验证、新模型校准、修改后 tile OOC。
- 大地址 node-state backing/cache、统一可扩展映射、32/64 topology 与全部共享物理资源的实现和资格。
- BNN/LSTM 完整 40-sample 有限架构仿真、新完整候选 OOC；目前只有 M1 功能结果，不得当成硬件性能。
- 通用表示变换 CPU/CUDA 对照及 native 身份/回接。已有 GPU V2 和 R1 证据复用，不申请新 GPU 补测。

配置在 `accel/lookahead/fpga_sparse_stream_r2/config/experiment_spec.r2.yaml`；逐项状态在 `results/fpga_sparse_stream_r2_20261112/checkpoint.json`。所有失败版本、源代码快照、周期日志与工具日志留在本轮 results。尚未声明 FPGA 胜过 CPU/GPU，尚无 board measured 结果。
