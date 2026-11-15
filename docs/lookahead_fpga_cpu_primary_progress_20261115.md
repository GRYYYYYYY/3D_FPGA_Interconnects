# CPU-primary 实验进展与在途任务（2026-11-15）

本次为按用户要求推送的进度检查点，观察截止 **2026-11-15 21:00:20 UTC**。
当前尚未取得合资格完整核的布线频率，因此**尚不能宣称 FPGA 已优于优化 CPU**。
完整综合正在收尾；本次推送不停止或重启该作业。

独立分支：`accel/lookahead-cpu-primary-closure-20261115`，固定起点
`3c7f96e6037030949b729240977c2ced373843c6`。目标为明确范围内优于合资格
优化 CPU，GPU 保留强对照并允许更快；不再使用“未超过 GPU 就不能进入完整 top”的门槛。

## 已完成的实验

| 项目 | 已完成结果 | 结论范围 |
|---|---|---|
| L1 完整连接 | `cp_full_top` 连接 64 lanes、16 前端、64 banks、32 端口有限访存网络；包括初始化、真实 cost、POP、enum2、scratch、K8、publication、输出写入与 ACK 排空 | 完整功能连接已实现；不包含平台 shell、PCIe/HBM 控制器 |
| 优化 CPU 对照 | 8/32/64 线程有限扫描；18 个独立进程，每个 1 次预热、3 次正式完整 batch；72 个输出全部通过 | 当前分配下 64 线程最优；不是所有 CPU 实现的全局最优 |
| 当前 f 候选局部 RTL | payload-wordmux 与旧 router 比较：3 seeds、49,693 edges，通过输出、仲裁、回压和复位检查 | 改写不增加状态或周期；不由功能等价推断面积或时序收益 |
| 当前 f 完整 RTL | 52 个正向样本、11 个非法配置拒绝全部通过；包含真实 native 图与确定性回压/延迟抖动 | 非法配置不发物理请求；完整输出与冻结 golden 相同 |
| RTL／有限模型校准 | 总周期、19 个阶段、3,772 个有序区间、72,917 次请求与返回时序均一致 | 声明测试集上的精确匹配，不是任意图的形式证明 |
| 完整有限 batch | model_g：基础及保守外存服务各 BNN40 + LSTM40，总计 160 样本，完整输出全部通过 | 当前 f 与原结果通过源码、输出、周期及请求契约显式绑定复用，没有重跑已有 batch |
| 输出后处理 | BNN40/LSTM40 均值 1.561172/1.537052 ms；每例 3 个独立进程 | 预触页布局重放，非 DMA、非板测；分配和首次触页另列 |
| GPU 与历史证据 | 已完成 H100、native 身份、CUDA 补档、旧模型及旧 no-go 证据继续保留 | 不重跑、不改写历史结论；BNN 历史二进制身份限制仍明示 |

## 性能结果与限制

以下均为完整 40 样本 resident 范围；CPU/GPU 为测量，FPGA 为指定外存服务和
**假设 200 MHz** 下的有限模型预测，尚不是实际布线频率下的硬件结果。

| 结果（秒） | BNN40 | LSTM40 |
|---|---:|---:|
| 优化 CPU，3 个进程均值的均值 | 0.699624213444 | 0.725510098000 |
| CPU，进程均值的样本标准差 | 0.026647139383 | 0.021287159254 |
| 保留的 H100 强对照均值 | 0.151799969444 | 0.159497999889 |
| FPGA 基础模型，假设 200 MHz | 0.512785120 | 0.520772070 |
| FPGA 保守模型，假设 200 MHz、160 ns 延迟/10 ns 发射 | 0.675641755 | 0.685991240 |

基础模型相对 CPU 均值的条件比值为 1.364×/1.393×；保守模型为
1.035×/1.058×。BNN 保守模型慢于最快 CPU 进程均值 0.668920613333 s，
因此不能声称稳健优势。GPU 在这些比较中更快，这不阻止完整核验证。

基础模型 BNN/LSTM 总周期为 102,557,024/104,154,414；其中 EXPAND 为
79,064,871/80,352,785，FINALIZE 为 21,483,099/21,759,568，INIT 为
1,283,120/1,303,160。保守模型总周期为 135,128,351/137,198,248。
完整 19 阶段及端口守恒分解保存在归档中；重叠等待项不直接相加。
外存服务是假设，完整 top 的可实现频率、资源及布线仍须实际验证。

## 实际资源结果

前一候选 e（dispatcher 重构、30 个 DUT 文件）已完成 Vivado 2022.2 默认
5 ns 综合及标准 `opt_design`，目标器件 `xcu280-fsvh2892-2L-e`。

| 阶段 | CLB LUT | 利用率 | FF | BRAM36 等价 | URAM | DSP |
|---|---:|---:|---:|---:|---:|---:|
| e 综合 | 1,353,922 | 103.85% | 749,255 | 1,148 | 640 | 0 |
| e 标准 opt_design 后 | 1,351,028 | 103.63% | 748,683 | 1,148 | 640 | 0 |

e 优化后仍超过器件 1,303,680 LUT 容量 **47,348 LUT**，保留 UTLZ-1 错误，
未启动布局布线。其未布线 setup slack 为 −4.992 ns、hold 为 −0.091 ns；
这些是未布线估计，不能换算成已通过的工作频率。reset buffer 的 Timing 38-242
警告与未完成的告警分类也保留；没有降低 DRC 严重性或添加虚假路径豁免。
更早 d 的 `no_timing` 综合使用不同选项，不能与 e 构成单一 RTL 改动的受控面积对照。

## 正在进行的实验与接续方法

当前 f 为唯一的有界后续资源候选：保留 e 的功能结构，只将 candidate router
的逐层 96-bit payload mux 改为胜者索引选取三个 32-bit 字。冻结闭包为 31 个
DUT 文件，使用与 e 相同器件、5 ns 约束及默认 timing-driven 综合选项。
不能预设该表达式一定减少资源。

- 运行目录：`results/fpga_cpu_primary_20261115/full_synth_f_wordmux`。
- 启动时间：2026-11-15 19:41:48 UTC；Vivado 会话：`vivado-20261115-135006-f83e6b28`。
- 子进程 PID：863147；`/proc` start ticks：167927650。接续时须同时核对启动身份，不能只凭 PID。
- 观察时日志已记录 `synth_design completed successfully`，0 errors、0 critical warnings、8,658 warnings；项目 run 仍在收尾，正式 utilization 与终态 checkpoint 尚未收齐。这不等同于整个综合交付完成或告警审计通过。
- 当前尚未启动 f 的 opt/place/route。pre-opt/post-opt 报告脚本已准备，尚未应用或执行；reset buffer 文档调查也没有修改约束。
- 后续复用该 project/run：取得终态全局资源与源码绑定，再按实际证据决定标准 opt-only；实际容量满足时继续完整核 place/route，检查 setup/hold/pulse、DRC 和约束覆盖。频率或服务点改变时重新校准并执行必要的完整 batch。

没有因缺少实板停止，也没有宣称板测。L2、缩减配置或换器件没有在本检查点
实现；旧配置失败不构成“所有 FPGA 都不可能超过 GPU”的证明。

## 可审计交付

- [完整实验与周期报告](lookahead_fpga_cpu_primary_closure.md)
- [历史证据、计时边界和复用限制](lookahead_fpga_cpu_primary_evidence.md)
- [独立文稿草案](lookahead_fpga_cpu_primary_manuscript.md)（原稿未改）
- [代码、重放命令与目录说明](../accel/lookahead/fpga_cpu_primary/README.md)
- [证据归档 manifest](../accel/lookahead/fpga_cpu_primary/evidence_snapshot/manifest.json)

归档包含完整测试输出、周期/阶段结果、日志快照、源码绑定和复用契约。
`github_progress_20261115_a/checkpoint.json` 记录本次观察时刻、进程身份和日志
快照摘要；通过 `delivery/archive.py --restore NEW_DIRECTORY` 可恢复原始证据布局。
完整 vendor 工程及 DCP 保留在本地，Git 中记录已完成 checkpoint 的摘要；
本次显式标记 f 为在途目录，不对仍可能写入的 DCP 声称终态 SHA。
`archive.py --verify` 验证归档及源码绑定，`check_protection.py` 检查受保护 refs 和修改范围。
推送只更新本独立候选分支，main、原稿、STRICT、旧 golden、其他分支与历史归档不变。
