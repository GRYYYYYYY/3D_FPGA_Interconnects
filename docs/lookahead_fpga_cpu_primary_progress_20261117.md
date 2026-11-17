# CPU-primary 实验进展快照（2026-11-17）

快照时间：**2026-11-17T00:00:59.586634+00:00**。
分支：`accel/lookahead-cpu-primary-closure-20261115`，继续使用现有独立 worktree。
这是已完成实验及在途状态的冻结记录，完整核物理闭环仍未完成。
[完整技术报告](lookahead_fpga_cpu_primary_closure.md)与
[接续说明](lookahead_fpga_cpu_primary_resume_db1d7e454.md)记录后续进展。
原 11 月 15 日、16 日快照保留，不回写历史状态。

## 当前结论

**尚无合格的完整核布线频率，尚不能证明 FPGA 优于本轮优化 CPU。**
旧 f 的默认布线和 SSI 布线均因实际拥塞失败；失败证据完整保留。
依据 SSI 的实际关键路径，仅实施一个 h 返回载荷 wordmux 修订。
h 的完整核功能校准、综合与标准 opt 已完成，资源有所减少；其 SSI
完整核仍在详细布局，尚未启动布线。不能把资源减少解释为时序闭环。

## 已完成的功能与模型验证

- h 只改变 dispatcher 的 116-bit 返回载荷选择，包含 cookie、node、label、status。
  原 f 源码保留，其余 30 份 DUT 源码及顺序状态逻辑不变；新配置有 31 份独立绑定的源码。
- h 局部协议、拒绝、选择器和生命周期检查通过；新完整核校准的 **52 个完整样本及 11 个拒绝用例通过**。
  完整输出、总周期、19 阶段、3,772 个区间、402 个 wave、72,917 次请求／返回与旧模型证据精确一致。
- 原 g 有限模型的 **160 个完整样本**重新核验来源、配置、输出及摘要后直接复用，未重复运行。
  `model_calibration_h_return_wordmux_a/calibration_reuse_contract.json`绑定新 RTL 与复用证据。
  这属于已执行用例的精确校准，不是全状态形式等价证明。
- CPU、GPU、CUDA 补档、native 身份和历史输出直接复用；未重复启动已有软件实验。

## 完整核实际资源

以下均为完整核，非局部模块。BRAM 使用 BRAM36 等价计数；各行 DSP 为 0。

| 阶段 | LUT | LUTRAM | SRL | FF | BRAM36 等价 | URAM | 状态 |
|---|---:|---:|---:|---:|---:|---:|---|
| f 综合 |1,244,096|286,776|1,280|749,617|1,148|640|已完成 |
| f 标准 opt |1,241,143|286,776|1,024|749,073|1,148|640|已完成 |
| f 默认布局／失败 DCP |1,233,715|286,232|896|749,174|1,148|640|布线失败 |
| f SSI 布局／失败 DCP |1,232,534|286,232|896|749,226|1,148|640|布线失败，终态审计完成 |
| h 综合／pre-opt |1,223,270（93.83%）|286,776|1,280|749,607|1,148|640|已完成 |
| h 标准 post-opt |1,220,068（93.59%）|286,776|1,024|748,933|1,148|640|已完成，尚未布局的结果 |

h 综合相较 f 综合减少 **20,826 LUT**；dispatch 层次从 99,304 降到 80,254 LUT。
层次行存在 LUT 合并，不能直接相加。h 标准 opt 进一步减少 3,202 LUT 和 674 FF；
post-opt 相较 f post-opt 减少 **21,075 LUT**。h post-opt 的 LUT logic 为 932,268，
BRAM 为 1,016 RAMB36 加 264 RAMB18，latch 为 0。
这些数量低于器件总量，但不证明局部放置、布线或时序合格。

h 综合终态与完整报告收齐，8,654 条综合告警均有覆盖记录；
138 个生成的常量别名尚未获得独立证明，未豁免为功能或物理签核。
标准 opt 子进程于 2026-11-16 21:55:09 UTC 退出，原 parent wait 返回 0。
实际 source project 的 impl_1 状态为 `Not started place_design`、40%、
`NEEDS_REFRESH=0`，符合仅执行到 opt 的设置，没有重置或重复启动。

h post-opt DRC 为 0，12 项 check_timing 均为 0；methodology 保留
1,024 条 SYNTH-5 和 1,000 条 TIMING-16。未布局时序为：
WNS **−5.106 ns**、TNS **−48,440.133 ns**、WHS **−0.091 ns**、THS **−13,166.243 ns**。
最差 setup 为 bank completion 状态到 dispatch error，最差 hold 为配置端口到 jobs 存储地址。
报告含估计／未布线延迟，不能据此生成合格频率。

## 旧 f SSI 的终态结论

旧 SSI 在 2026-11-16 18:42:24 UTC 返回失败，错误为 **Route35-3，全局拥塞等级 7**。
试算有 **5,795,346 个重叠**，比默认 f 少 14,368 个，但依然不合法。
试算中零 failed／unrouted／partial nets 不等于合法布线。
错误 DCP 的序列化报告另记 1,873,322 个 routable nets，其中仅 2 个 fully routed；
该状态与试算重叠统计分别保留，不混用。

全部 **21 组终态报告执行成功**，失败原因、全局与层次资源、setup／hold、
时钟、约束覆盖、拥塞、告警、源码及 DCP 绑定均已审计。
错误状态 WNS/TNS 为 **−15.487/−3,098,668.250 ns**，
WHS/THS 为 **−3.530/−1,410,972.500 ns**。
最差 setup 为 bank completion payload 到 dispatch error，跨越 3 个 SLR 边界；
最差内部 hold 为 fabric 请求保持寄存器到队列存储。
布局阶段 CLB 站点占用 99.92%，并有局部与跨 SLR 拥塞。
这支持对返回载荷选择网络作一次局部修订，不构成所有 FPGA 的普遍 no-go。

旧 SSI 错误 DCP：627,280,835 字节，SHA256
`0bd512a2622439528b1802a398530385473c85bb6c5ac4cf5858ffc47316568f`。

## 当前唯一在途 EDA 实验

- h 运行目录：`full_impl_h_ssi_spreadslls_a/run_a`，属于非工程模式完整核回放。
  它从 h 新 post-opt DCP 开始，不是旧 f 综合、opt 或 SSI 的重启。
- h 输入 DCP：402,149,724 字节，SHA256
  `832f257f83d47575d9ea4bfb448b19f49be489ce93d18938a0a1b4f29ab0e3d5`。
  `freeze.json`绑定实际 DCP、冻结 Tcl 和 clock／census helpers；`launch.tcl`为可复现入口。
- 策略：`SSI_SpreadSLLs -ultrathreads`，8 线程，后续默认 phys_opt、默认 route，5 ns 为目标约束。
  只评估 h 这一 RTL 修订，没有增加并行度或同时展开其他架构。
- 会话 `vivado-20261115-113226-a1b5e8eb`；PID **1165972**，出生 start_ticks **164991348**；
  boot ID `2c285022-7829-4b21-84d8-176f6732a754`。发布前重新核对匹配。
  此 PID 是复用的 Vivado parent，不能把其出生时间当作 h 启动时间。
- h 回放于 **2026-11-16 21:58:41 UTC** 开始，DCP 打开和真实时钟复核均返回 0。
  `place_design` 于 **22:11:42 UTC** 开始。全局布局已完成；快照时处于
  **详细布局 Phase 3.6 Small Shape DP**，跨 SLR 网络拆分子阶段完成。
  尚无 place 终态、placed checkpoint 或 route 启动回执。
- 当前预布局告警给出 SLR1→SLR2 需求 **19,714/23,040 SLL**。
  这是阶段估计，不是最终布线占用或时序结论。
- 实际 clk 连通复核：1,237,261 个 all/core/direct 时钟引脚名称集合完全相同。
  唯一 pre-place BUFG 为 reset 控制，99,097 个负载、**0 个时钟负载**；
  核心 clk 的声明外部 OOC 源为 `BUFGCE_X0Y144`。
  reset 的 Timing38-242 上游 OOC 延迟／skew 限制保留，不给 reset 伪造核心时钟上下文。
- 只读监控器每 60 秒保存出生身份、阶段回执、日志与 checkpoint 大小。
  它不执行 EDA、不重启任务；继续监督应复用现有进程与快照。

日志在 `dispatch_synth_a/.vivado-ai/vivado_42346525_14d7ac8e.log`，
h 回放起始偏移为 **4,219,527 字节**。日志目录旧名称不代表当前候选。
冻结脚本会在各阶段完成后保存 DCP，失败时保存错误 DCP 并收集完整终态报告。

## 软件对照与条件模型结果

| 对照，完整 BNN40／LSTM40 resident 均值 | BNN40 秒 | LSTM40 秒 |
|---|---:|---:|
| 本轮优化 64-worker CPU |0.699624213|0.725510098|
| 保留 H100 GPU 参考 |0.151799969|0.159498000|

CPU 完成 8／32／64-worker 对照，结论限定于当前分配：容器配额 55 CPU-time，
40 个样本最多并行 40 个求解；三个进程均值的标准差为 0.026647139／0.021287159 秒。
GPU 更快不作为停止条件；BNN 历史 GPU 可执行文件缺少同期摘要的限制仍保留。

| 完整有限模型，仅假定 200 MHz | BNN40 周期／条件秒 | LSTM40 周期／条件秒 |
|---|---:|---:|
| 基础：80 ns 延迟／5 ns 发射间隔 |102,557,024／0.512785120|104,154,414／0.520772070|
| 保守：160 ns 延迟／10 ns 发射间隔 |135,128,351／0.675641755|137,198,248／0.685991240|

上述模型值保留完整输出与周期分解，**不属于实际合格布线频率下的 FPGA 时间，也不是板测**。
保守 BNN40 条件预测还慢于最快 CPU 进程均值，不能宣称稳健优势。
当前正式 FPGA 时间与 CPU 加速比均为空。获得合格频率后，须按实际周期重新处理
纳秒级存储参数，完成必要校准与完整 BNN40／LSTM40 模拟，不能简单将旧周期除以新频率。
OOC 完整核不包含 shell、PCIe 或 HBM 控制器；外部时钟、存储服务及端口物理边界限制明确保留。

## 证据与恢复

[归档索引](../accel/lookahead/fpga_cpu_primary/evidence_snapshot/manifest.json)绑定完整可归档输出、
报告、源码和配置；内容寻址压缩对象可通过 `delivery/archive.py --restore <新目录>` 恢复。
大型 vendor DCP 留在现有工作区，Git 中归档摘要与重放绑定，不声称上传了 DCP 二进制。

本次原始发布快照位于 `results/fpga_cpu_primary_20261115/full_impl_h_ssi_spreadslls_a/github_progress_snapshot_20261117_a`，
包括 MCP 状态、进程身份、部分日志／回执、持续监控副本及摘要。
h 综合、opt 和旧 SSI 终态分别位于 `synthesis_collection_a`、`opt_terminal_a`、旧 SSI `terminal_audit_a`。
恢复时核对 PID、出生时间、boot、receipt 和日志；禁止重复启动现有回放。

main、原稿、STRICT、旧 golden、历史归档及其他分支保持不变。
