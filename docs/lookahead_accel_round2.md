# Lookahead FPGA 加速实验：第二轮

目标修改为 **FPGA 优于各个软件基线**，不要求 CUDA 优于 CPU。CUDA 是补充基线，较慢的结果仍有效。目前尚未证明 FPGA 在 tseng / BNN 或完整 lookahead 构建上优于 CPU/CUDA；下面只报告已经取得的证据。

独立分支为 `accel/lookahead-round2-20261108`，父提交 `97e508a`。新输出目录为
[`results/lookahead_accel_round2_20261108T122100Z`](../results/lookahead_accel_round2_20261108T122100Z)。
[第一轮记录](lookahead_accel_round1.md)及原 CPU 论文证据保留，冻结 CPU 和原 VPR 二进制的 SHA256 未变。

## 本轮实现和验证

- 新增真实的 CPU/CUDA 动态库接口，输入来自当前 native RRG、全局 sample 列表和坐标转换，不接受 golden map。native 原有有序归并和后续填充继续执行。导入离线结果只保留为独立正确性检查。
- 新增组合缓存核：heap 顶部 127 项、标签 64 行、带标签的 cost cache 64 行。cost cache 在一次调用开始时清空，batch 内复用，填充计入 E1。
- 新增共享状态机的多上下文核、1/2/4/8 上下文 C 模型差分测试，以及 1/2/4 上下文 RTL 检查。另做真实依赖距离实验，没有使用错误的 `DEPENDENCE false`。
- 新增有限带宽/并发数的 AXI 仿真模型，检查背压、credit、burst、VALID 稳定性和完成时排空。双引擎也共享同一模型的 bank。

主机测试 9/9 通过；包括语义边界、libstdc++ heap 对照和随机图差分。
新四上下文 C 模型通过 tseng 全部 8 个、BNN 全部 40 个 native sample 的逐位检查。
这些大图结果是 C 模型正确性证据，不是大图 FPGA 性能测量。

完整 heap、CSR、标签更新、IPIN map、终止检测均在核内执行，没有用 CPU 补算其搜索结果。
STRICT_FP32、邻接顺序、相等 delay 的处理、heap tie、SINK 行为和 group 归并约定沿用第一轮。

## FPGA RTL：相同的小型完整 native 图

所有数字均来自 N=552、E=802、4 个全局 sample 的完整 native workload；没有截断大图冒充完整图。
目标器件为 `xcu280-fsvh2892-2L-e`，Vivado / Vitis HLS 2022.2，目标周期 5 ns。

| 功能 AXI 仿真变体 | RTL 周期 | 相对前一项 |
|---|---:|---:|
| 第一轮 heap31 | 293,852 | — |
| heap127 | 289,381 | −1.52% |
| 再加标签 64 行 | 275,305 | −4.86% |
| 再加 cost cache 64 行 | 265,241 | −3.66% |

组合缓存核布线后使用 27,154 LUT、31,004 FF、4 DSP、49 BRAM18 等效块、0 URAM。
200 MHz 内部 setup / hold 检查通过，WNS +0.441 ns、WHS +0.019 ns；无无时钟或未约束的内部端点。
这是核的 OOC 实现，未建立平台 shell、外部接口或实板时序结论。没有把工具估算周期反算成已验证 fmax。

受限模型统一采用 64 周期请求延迟、1 个共享 bank、每 4 周期最多一个原生 R 或 W beat、每端口每方向 2 个 outstanding 请求、每端口 1 个有限 read 返回槽。窄 beat 也占完整服务槽。这是可控的合成敏感性实验，尚未校准为真实 HBM。

| 相同受限 AXI 模型 | RTL 周期 |
|---|---:|
| F0 | 2,091,704 |
| 缓存关闭 | 2,625,249 |
| heap31 | 1,211,614 |
| 两个完整引擎，共享 bank | 1,063,676 |
| 组合缓存 | **996,173** |
| 共享状态机，1 上下文 | 1,396,523 |
| 共享状态机，4 上下文 | 1,410,463 |
| 4 上下文，加真实依赖距离 | 1,346,628 |

所有列出的受限仿真均完成，所有输出端口逐位匹配。组合缓存比 F0 少 52.38% 周期；这不是对 CPU 的加速比。
双引擎与共享状态机是不同架构，不能把复制引擎的收益归因于共享流水线的访存延迟隐藏。

四上下文本身产生负收益。声明每个上下文真实的循环依赖距离后，综合 II 从 20 降至 17；功能 AXI 周期从 514,988 降至 451,782（−12.27%），受限 AXI 周期仅减少 4.53%。
全局阻塞访存仍限制了重叠执行；该实现尚不是独立请求/响应调度器。
未经该依赖优化的四上下文核布线 WNS −1.149 ns，**未通过 200 MHz**。
加入依赖距离后的四上下文核 WNS −0.830 ns、WHS +0.019 ns，也未通过 200 MHz；周期减少没有消除时序问题。
各版本完整资源和最终时序见[机器生成报告](../results/lookahead_accel_round2_20261108T122100Z/report_final/report.md)；实现工具正常退出不等于时序通过。

## CPU / CUDA：同一 H100 工作节点的实测

GPU 任务 `job-49d5aba7-24eb-475e-a3df-7f4ff6248ebd` 成功完成。CPU 和 CUDA 使用同一节点、同一 NUMA 上 8 个物理核；每个 live 后端执行 3 个独立 native 进程，双方均无显式预热。CUDA 使用第一轮基础核，没有 CPU fallback。

| tseng，同一输入，3 次中位数 | E1 驻留搜索 batch | 完整 wire builder | 完整 router lookahead builder |
|---|---:|---:|---:|
| CPU live 后端 | 0.037030 s | 0.05 s | 0.06 s |
| CUDA live 后端，H100 | 0.679714 s | 1.10 s | 1.11 s |
| 原 VPR，多线程 | — | 0.21 s | 0.21 s |
| native per-group | — | 0.07 s | 0.07 s |
| native pipeline | — | 0.04 s | 0.04 s |
| native flat | — | 0.05 s | 0.05 s |

E1 包含重置、输出初始化、完整 heap/CSR/label/IPIN 搜索和完成检测，单独排除分配和图上传。
完整构建计时包含当前 native 数据转换、冷启动库/设备初始化、图上传、搜索、紧凑回读、有序归并和后续填充；外层 router timer 还包括 source / OPIN 构建。native 日志分辨率为 0.01 s，不能解释小于此粒度的差异。
三次 CPU、三次 CUDA 和所有 native 对照的最终 wire map 均与冻结参考一致。
只运行一轮 routing 是组件测试，不声称整个布线收敛或 VPR 全流程具有相同加速比。

CPU/CUDA 插件另外通过 tiny、tseng、BNN 全部 sample 的 replay 检查。BNN 插件单次 CUDA E1 为约 36.5765 s，属于一次诊断运行；大图正式重复测量仍使用第一轮记录，不能混成三次测量的新队列。

## 保留的失败证据和当前边界

2022.2 对 per-context heap 指针数组综合失败；后续版本又暴露了循环 turn 回绕但外部地址基址不回绕的 RTL 错误。Csim 通过并不足够，实际 cosim 检出了越界。显式基址寄存器版本通过了 cosim。
受限模型也曾因跨端口背压死锁、返回数据总线填充位宽错误而失败；最终模型增加有限返回槽并通过对抗性测试，错误版本不参与性能结论。
一次 XSim 宿主停滞保留了现场记录；去除波形/protoinst 调试的独立重跑通过，根因尚未确定。
CPU 插件卸载时的 OpenMP 崩溃通过保留动态库映射修复。详见 `engineering_notes.json` 和各次独立输出。

FPGA 的完整构建 E2、大图在真实内存约束下的性能、物理 HBM 连接和校准均尚未验证。当前 `(sample,node) -> cell` 映射仍是 O(JN) 的功能布局，其准备和上传开销不能隐藏。报告没有给出未经校准的大图线性外推值，也没有宣称 FPGA 已胜过 CPU/CUDA。

可复现入口为 `scripts/la_accel_hls.py`、`scripts/la_accel_bounded.py`、`scripts/la_accel_live.py`、`scripts/la_accel_live_gpu_job.py`。
[运行约定及命令](../accel/lookahead/README.md)、[最终 JSON](../results/lookahead_accel_round2_20261108T122100Z/report_final/report.json)、[导出图表](../results/lookahead_accel_round2_20261108T122100Z/plot_final/evidence.pdf)、[带 SHA256 的证据索引](../results/lookahead_accel_round2_20261108T122100Z/evidence_snapshot/index.json)共同记录数据与计时范围。
