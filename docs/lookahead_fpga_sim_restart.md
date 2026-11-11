# R6.2 后 FPGA 重启：首个 owner 实际交付

本轮已交付可运行的单 owner RTL、有限存储 testbench、完整内存差分、真实周期日志及 OOC 报告。**整轮任务尚未完成**。当前没有完整小图闭环 RTL、64-owner 全核、完整大图架构仿真或 FPGA 优势结论。

基点 `7e63b917f37273f80c03327e024d86b797ee221b`；独立分支 `accel/lookahead-fpga-sim-restart-20261112`；run_id `fpga_sim_restart_20261111T231000Z`。工作目录 `/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SIM_RESTART_R62`。原工作区、main、原稿、STRICT、旧 golden、历史证据和未跟踪指导材料未修改。依据用户提供的 YAML 建立了 `accel/lookahead/fpga_sim_restart/config/experiment_spec.simulation_restart.yaml`；原模板和执行合同也完整保留。实际执行开始于 2026-11-11 UTC，保留用户指定的 20261112 分支命名。

## RTL 与验证范围

固定 Q=1、4-way × 32 sets × 32B、32 MSHR、16 dirty slots、请求/响应 FIFO 各 64；支持 whole-pair FP32 字典序、同 line 合并、脏写确认前 RAW 阻塞，以及 flush/invalidate/fence。原语与状态均由 RTL 实体化；运行时加载请求。`OWNER_BITS=6` 的单 owner 测试核对完整 64-owner 地址分配公式，但不等于并发 64-owner 实现。

| 测试 | accepted | 总周期，含初始化/排空 | 比较 32B 行数 | 差异 |
|---|---:|---:|---:|---:|
| directed_ii1 | 2646 | 153,496 | 4,096 | 0 |
| directed_latency60 | 2646 | 22,748 | 4,096 | 0 |
| directed_owner64 | 2646 | 154,010 | 131,072 | 0 |
| real_waves | 224 | 1,144 | 4,096 | 0 |
| real_waves_d4 | 104 | 1,021 | 4,096 | 0 |

另有 NaN、Inf、负数、subnormal 和负零五项拒绝测试，均不发布成功 fence。压力测试实测 request FIFO/MSHR/dirty high-water 分别达到 64/32/16。完整 cycle、transaction、action、accept-to-reduce 和 memory-feedback 日志均保留。请求侧观测到 II=1 接受间隔；这不等于带任意访存、图前端及互连的持续 edge II=1。`retired` 是候选归并计数，写入可见性由最终 fence 确认。

这些是 RTL **服务单元**测试。d3、d4 各重放 qid0 的前两个完整 wave，parent/candidate 由软件生成；其余 sample、FP32 pair 生成、图读取、目录/成员、closure、输出控制尚未成为 RTL。它们不是完整小图 batch。

存储服务器有限：64 outstanding、32B 事务、16 abstract banks、共享读写链路每 2 cycles、bank 间隔 8 cycles、读写切换 4 cycles，以及延迟/重排/背压。测试采用 60/60 或 600/800 read/write cycles 的显式 stress 参数，单时钟 testbench 为 5ns。它们不是整个 YAML 32-channel 五情景实验，也不是板测；不将这些周期直接换算为完整 FPGA batch 时间。

## OOC 与保留的负结果

Vivado 2022.2，`xcu280-fsvh2892-2L-e`，本次源码实际综合、placement、routing。最终资源：{'luts': 10254, 'logic_luts': 5632, 'lutram': 4622, 'ffs': 2343}。完整报告、约束、DRC、check_timing 与 checkpoint SHA 见证据索引。

| 同一最终 routed owner | setup WNS ns | hold WHS ns | 全约束通过 |
|---|---:|---:|---|
| 200 MHz 目标 | -1.588 | -0.235 | False |
| 125 MHz 一次回退静态检查 | 1.412 | -0.235 | False |

125 MHz 是同一 route 的检查，不是新的重布局频率扫描。边界端口缺少 top-level routing/HD.PARTPIN_LOCS/HD.CLK_SRC 支持，hold 问题与 OOC 接口限制完整保留。没有 false-path 隐藏依赖；没有把 setup 单独通过说成全时序通过。寄存器到寄存器报告另列，不能用于宣称 shell 接口或 64-owner 全核频率。`performance_hz` 仍为空。

第一次路由结束后发生 `realloc(): invalid pointer`，堆栈经 libudev、许可证主机信息查询和 WebTalk，退出码 6。按[原始问题报告](https://github.com/fastmachinelearning/hls4ml-tutorial/issues/81)所关联的 AMD AR 000034450，采用仅本进程的 `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libudev.so.1`；从同一 synth DCP 恢复后成功保存 route 和报告。AR 页面正文未能直接读取，不声称已核验其完整适用版本。没有替换库、stub、许可证规避或全局偏好修改。初始失败、恢复以及最终修正源码的独立运行全部保存。

## 单 owner 模型对照

模型独立推进 FIFO、MSHR、cache、dirty buffer、有限内存与 fence，不读 RTL 周期作为调度输入。逐阶段最大相对误差 0.00779%；每一阶段输出和读写事务数相同。配置签名及逐阶段对照在 `model_comparison.json` 和各 `model.json`。

最初真实 wave 约 19% 的误差没有删除：日志定位到空闲 way 优先级不一致。初版循环 RTL 在 XSim 的初始分配选择 way3，而模型/事务重放选 way0；最终改为显式最低空闲 way 优先，随后全回归。该变化未改 ways/sets/MSHR 等候选参数。d4 wave 未用于这次修正，修正后对照通过。记录的是观测到的实现差异，不推定为已证实的工具缺陷。

此对照只证明服务单元范围。`architecture_model_rtl_calibrated=false`：缺少完整小图闭环和相同 64-owner 配置的校准，不能把单元结果升级成全核校准。

## 完整真实 batch 的功能事务重放

读取原始表示和冻结哈希，BNN、LSTM 各完整 40 jobs。每 wave 将所有 proposal-home pairs 与提交 labels 全量核对；每 sample 与原始 ALT CPU `std::map` 搜索逐字比较；F0/F1 完整输出 SHA 相同。完整输出已无损压缩保留。首次使用 DirectDirectory 参考的记录也保留，最终参考已明确改为原始目录实现。

| 输入 | 消融 | jobs | eligible candidates | 串行缓存命中率 | proposal 读写 GB | 完整输出 |
|---|---|---:|---:|---:|---:|---|
| native_d3_w8 | F0 | 8 | 2,136 | 0.000% | 0.000098 | exact |
| native_d3_w8 | F1 | 8 | 2,136 | 76.966% | 0.000031 | exact |
| native_d4_w8 | F0 | 12 | 15,239 | 0.000% | 0.000637 | exact |
| native_d4_w8 | F1 | 12 | 15,239 | 77.814% | 0.000196 | exact |
| bnn_export | F0 | 40 | 1,286,937,147 | 0.000% | 45.182830 | exact |
| bnn_export | F1 | 40 | 1,286,937,147 | 46.533% | 25.274703 | exact |
| lstm_s2 | F0 | 40 | 1,309,512,712 | 0.000% | 45.998508 | exact |
| lstm_s2 | F1 | 40 | 1,309,512,712 | 46.121% | 25.913555 | exact |

这里的 C++ 重放未建立并发 MSHR/互连/全部数组访存的有限时间调度。表中命中率和事务属于该串行重放顺序；它们不是大图 RTL hit rate、完整架构模拟周期或必要物理下界。软件运行耗时没有作为 FPGA 时间。

## 尚未完成及结论边界

- 完整小图 batch 闭环 RTL，包括算术、图访存、目录/成员、commit/closure/output。
- 8-owner tile、64 lanes/owners 实际互连及完整候选 OOC；最终接口 setup/hold 门槛。
- 对应配置的全核 RTL 校准、BNN/LSTM 全量闭环有限架构模拟、F0/F1 与五个预声明内存情景。
- `RESIDENT_COMPLETE_BATCH_V2` 的匹配 warm CPU/GPU/VPR 计时、硬件/模型输出的 native bridge/final map 检查、最终速度/QoR/敏感性图表。

已抽取 24 条历史 `resident_s` 并保留 JSON 来源路径，注明 cold/native 范围；它们不是新 warm cohort。旧 E1 未重命名，未给出范围不匹配的加速比。`board_measured=false`；没有以 XRT/XPFM/实板缺失作停止条件，也没有判定固定候选已经获胜或已被全面否定。

[RTL、运行说明](../accel/lookahead/fpga_sim_restart/README.md)；[机器状态](../results/fpga_sim_restart_20261111T231000Z/evidence_snapshot/status.json)；[完整证据索引](../results/fpga_sim_restart_20261111T231000Z/evidence_snapshot/index.json)。大 DCP 位于索引的本机路径，未冒充已随 Git 上传。
