# CODEX_NEXT_AFTER_DB1D7E454.md

继续当前 `accel/lookahead-cpu-primary-closure-20261115` 分支。

本轮目标：完成 SSI 完整核物理实现收敛，并判断是否能够证明 FPGA 优于优化 CPU。

## A. 在途任务核查

1. 核对 SSI Phase 3.5 对应的 Vivado project、run、进程 PID、启动时间和日志。
2. 确认是否仍在运行，禁止重复启动已有任务。
3. 若已结束，收集完整终态、失败原因、checkpoint 和报告。
4. 若仍在运行，继续监督并保存状态快照。

## B. 完整核实现结果

收集并核验：

- 完整核综合资源。
- opt-only 前后资源变化。
- LUT、LUTRAM、FF、DSP、BRAM、URAM。
- Place、Route 完成状态。
- WNS、TNS、WHS、THS。
- 最差 setup/hold 路径。
- 未约束路径和时钟连通情况。
- 最终 checkpoint 和可复现 Tcl。

区分完整核结果与局部模块结果。

## C. 性能资格

只有完整核获得合格布线频率后，才进行正式 FPGA 时间换算。

复核：

- BNN40、LSTM40 完整输出。
- RTL 周期与模型校准。
- 外存访问、阻塞、FIFO 和尾部排空。
- 完整 batch 周期统计。
- 64-worker 优化 CPU 的同口径比较。

计算 FPGA/CPU 加速比，并分别报告基础、保守存储情景。

GPU 保留参考，不将超过 GPU 设为硬性验收条件。

## D. 如果 SSI 失败

不要直接扩大架构或增加并行度。

先定位实际失败的关键路径、资源超限或拥塞原因，提出一个具有明确依据的最小修改。

修改前保留当前失败证据，修改后建立新的候选配置并重新验证。

## E. 交付

更新进度报告、claim ledger、证据索引及恢复说明。

推送独立分支并核对远端 SHA。

不得修改 main、原稿、STRICT、旧 golden 和历史证据。

最终明确给出：

1. 完整核是否实现成功。
2. 实际资源使用。
3. 合格布线频率。
4. BNN/LSTM FPGA 时间。
5. 相对优化 CPU 的加速比。
6. 尚未解决的问题。

禁止将目标频率、理想内存模型或局部模块时序包装成完整 FPGA 性能结果。
