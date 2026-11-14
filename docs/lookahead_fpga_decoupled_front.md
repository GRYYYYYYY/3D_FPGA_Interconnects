# 有限跨 parent 预取与解耦图前端：固定配置停止记录

本轮状态为 **NO_GO_CONFIGURATION**。完成真实完整输入画像、同资源 A/B/C 局部调度与现有枚举 RTL 的实测复核；没有得到新的完整 FPGA 时间或硬件胜出资格。

新 B 解除了 edge 对 metadata 回包的等待，代表性大波次的 metadata 平均占用从约 128 降到 55；C 又减少长行续读等待，但增加槽位和返回仲裁压力，完成周期未稳定改善。保留原五周期枚举后端、64 lanes、200 MHz、每 sample 完整 canonical 初始化和完整 wave fence 时，BNN 即使理想计算/分配也至少需要 **153.275585703125 ms**，超过强软件目标 **151.799969444 ms**。因此按指导文件第 11、13、14 节停止扩大该配置。LSTM 的同类下界没有超过目标，不能声称 LSTM 也已被证明失败。

该结果不否决更高频率、流水枚举、其他初始化实现或所有 FPGA 架构。下一候选若改变这些条件必须重新计时、实现和验证；本轮没有用扩容来掩盖后端限制。

## 范围与固定来源

- 基点 `059ec4cc7c7c3793398016c0713c29a0e0c6d46a`；独立分支 `accel/lookahead-inf-decoupled-front-20261114`。
- 指导文件为用户仓库中未跟踪的 `docs/CODEX_FPGA_DECOUPLED_FRONTEND_AFTER_059EC4C.md`，完整读取并按条件推进。
- GPU 254 receipts、六项旧 F0 完整 batch、CUDA `.cu` 补档均直接复用；没有重跑这些实验。软件 summary SHA256 `fe71fe5755de198d3e718ef49ca84d326622b3ec57c5f067cf1641fdf79cda38`，binding SHA256 `1025336c61144439613d5feab53b42d5c2df667a47e3e2ae01fab947925d7b6c`。归档路径和 CUDA 源哈希见 `bindings/reused_evidence.json`。
- 软件/旧模型终态 `a64c934956be6514a27f66fd1a46f09ef4a2fab9`；GPU 独立归档 `cc71869709bcf3124ae81ebfdcd8f36819c4c90d`。计时范围仍为 `RESIDENT_COMPLETE_BATCH_V2`；BNN 采用较强历史目标，不改为较慢 INF CUDA 值。
- main、原稿、STRICT、旧 golden、旧结果保持不变。旧两 subbank OOC 的 setup +0.635 ns / hold +0.041 ns 仍只属于旧局部设计；旧完整核负结果不变。

## 配置、地址与字段依赖

机器可读配置：`accel/lookahead/fpga_decoupled_front/configuration.json`。A/B/C 全部使用 H=128、E=256、M=128、L=64；每 lane 四个 E、八个 beat 槽，总 512×32B；fork/ready 各 128。A/B 的 D=1，C 的 D=2；D 只限制已发未回请求，正在消费/已返回 beat 仍占共享槽，不能重复计算容量。

32 个 32B 物理端口，各 32 credits、64 请求队列、4 返回队列。80 ns/5 ns 固定合同在条件 200 MHz 下为 16/1 cycles。每请求入队前分配 tag 和客户端容纳返回的状态/槽；端口接受响应后归还 credit，最后有效 descriptor 消费后释放 edge 槽。每 lane 每周期至多一次返回写入；冲突进入有限端口返回队列。

| 请求/状态 | 产生/保存的字段 | 依赖方 |
|---|---|---|
| 有效 POP 快照 | node、whole pair、sample/epoch | fork 两个消费者；stage 1 的输入边界 |
| CSR_ROW | 两个 64-bit offsets | E 分配/edge 请求；node%4=3 需两条 line |
| CSR_EDGE | 原 32-bit descriptor，dst/cost index | FP32 lane；请求前已经持有 E |
| 常驻 cost table | delay/congestion FP32 operands | 两次真实 FP32 加法，关闭 FMA contraction |
| NODE_META | type/target 与该 sample 的 cell index | whole-pair 目标归约及 first-seen；B/C 不阻塞 edge |
| A 的 metadata 通知 | 同一次事务的 response 完成 | 只对 A 解除 edge 等待；不新增 metadata 请求 |
| 输出状态 | 8 banks ×4096×{seen,pair} | 每 bank 每周期最多一次更新，目标排空后局部结束 |
| finalize | canonical、pending、目录及 ACK | 完整 wave fence；不在 stage-1 局部周期内 |

以 32B line 为单位：row_base=0；edge_base=align32(ceil((nodes+1)/4))；meta_base=align32(edge_base+ceil(edges/8))；metadata 每 sample stride=align32(ceil(nodes/4))；label_base 在全部 metadata 后对齐；scratch_base 在 canonical 后对齐。`align32` 为 32 **条 line** 对齐；port=`physical_line & 31`，从不以 context 编号选端口。各输入的实际 base 值在画像 JSON 中。

非空行 edge 请求为 floor((end−1)/8)−floor(begin/8)+1；零度行不请求 edge。图从原 workload 按冻结 eligible/PreparedCSR 规则重建，不从 trace 的结果反推 operands；预计算 pair 仅用于逐位核对。metadata 每 sample 实际地址不同，对齐 stride 使 port 分布可按访问次数累加。

Stage 1 是明确的抽象：有效 POP 环境最多每周期送 32 快照；无 pending/目录时延；候选后端理想 ready；返回 FIFO 可同周期旁路；目标事件在 M context 中保留，额外 128-entry 目标 FIFO 只列预留容量，尚未实现独立队列；每 wave 重新建立目标状态。上述选择在三个配置中一致，既不是完整 batch 模型，也没有新 RTL 校准。全局选择器、return route、时钟频率和资源映射均未获得资格。

## 完整真实输入画像

冻结原生 pending17 参考加入流式计数，运行两个小图及 BNN/LSTM 各完整 40 sample。四份完整输出逐字节 SHA256 均与旧 golden 一致，receipt 与输出归档保留。该正确性属于参考遍历，不属于新的完整硬件模型。没有导出完整逐候选大 trace。

| 完整 batch 指标 | BNN | LSTM |
|---|---:|---:|
| nodes | 4,102,608 | 4,166,724 |
| cells | 25,088 | 25,538 |
| parents | 102,918,965 | 104,730,480 |
| nonempty parents | 58,250,255 | 59,300,519 |
| zero-degree parents | 44,668,710 | 45,429,961 |
| candidates | 1,286,937,147 | 1,309,512,712 |
| row 请求（画像口径） | 128,631,919 | 130,843,890 |
| edge 请求（画像口径） | 209,255,671 | 215,954,269 |
| metadata 请求（画像口径） | 102,918,965 | 104,730,480 |
| pop 请求（画像口径） | 102,924,851 | 104,739,179 |
| init 请求（画像口径） | 41,026,080 | 41,667,240 |
| final_read 请求（画像口径） | 118,725,942 | 121,154,080 |
| final_write 请求（画像口径） | 51,973,592 | 53,038,572 |
| edge beat 空余 descriptor 槽 | 387,108,221 | 418,121,440 |
| row distinct lines（全 batch） | 669,963 | 679,067 |
| edge distinct lines（全 batch） | 4,010,857 | 4,080,811 |

完整 degree histogram、row 四种起点/edge 八种起点对齐分布、七类每 port 请求、逐 wave touched/changed lines 及潜在复用计数均在 `profile_a`。edge alignment 分布包含零度 parent；空余槽按非空行实际请求计算。重复访问是潜在复用，未实现 cache，不能当命中率。

`final_read` 是每 wave 去重 touched line 的语义计数；`final_write` 是该 wave 改善 line 的计数。它们不包含新次序下的 spill/merge、目录、目标输出/成本装载流量，不能把七类合计称完整新架构流量，也没有借用旧 spill 次数。上述 incomplete traffic 的物理热点端口必要界分别为 23,644,094 / 24,435,953 cycles。

## 同资源 A/B/C：有效的局部结论

最终结果为 `front_b` 的 17 个冻结 native wave×3 配置，以及 `front_stress_b` 的两个真实连续 128-parent 窗口×3 配置。压力窗口以短非空行和 row 跨线打分，保留原连续顺序，并加确定性响应抖动。全部 57 项候选 operands→FP32 pair、目标 whole-pair/first-seen、parent/request/response/tag 退休检查通过。17 条原 trace 沿旧 manifest 按 SHA256 恢复，不重复归档；新增窗口保留。

| 原生波次 | A cycles | B cycles | C cycles |
|---|---:|---:|---:|
| bnn_export wave_19_30 | 93,072 | 92,905 | 93,906 |
| bnn_export wave_19_32 | 79,974 | 80,290 | 81,112 |
| bnn_export wave_2_38 | 118,457 | 118,360 | 119,267 |
| bnn_export wave_35_53 | 948 | 896 | 699 |
| lstm_s2 wave_19_30 | 93,970 | 94,203 | 95,002 |
| lstm_s2 wave_2_36 | 104,758 | 104,769 | 105,488 |
| lstm_s2 wave_33_58 | 856 | 738 | 762 |
| lstm_s2 wave_7_36 | 121,143 | 121,175 | 121,851 |

上表列完整大输入所选八个 native wave，另九个小图 wave 在归档中。局部 cycles 不与完整 GPU 秒数计算加速。

BNN wave_2_38：B→C 将续读等待从 1,396,392 降为 507,022 **descriptor-cycles**（约 63.7%），但首 beat 等待从 2,168,736 升为 2,325,563，槽不足尝试从 142,246 升为 1,762,526，返回写冲突从 66,940 升为 113,242。LSTM wave_7_36 的续读等待从 1,448,795 降为 530,551（约 63.4%），也没有得到净周期收益。不能将这些重叠等待相加为 wall time。

B 在上述两大 wave 的 E 峰值只有 168/183，低于 256；header 平均占用约 127.84，fork 接近满，lane 发射占比分别约 32.38%/31.97%。模型采用顺序优先分配 E 和同一有限返回路径，存在分配/入口/返回资源竞争。证据支持“D2 减少续读等待，但总完成未改善”，不支持唯一瓶颈的因果归因，更不支持 D4。没有运行 D4 或大范围参数扫描。

每个最终 JSON 保留 H/E/M/slot/fork/ready 的周期占用直方图、lane emit/idle/downstream、首读/续读 descriptor-cycles、每 port queue/flight/credit/return 直方图、credit/queue 阻塞尝试、response-full port-cycles，以及最后输入/parent/candidate/meta/response 的周期。ready FIFO 在该实现中同 tick 入队出队，因此周期末占用常为零；返回队列也按周期末采样，不把该数误作组合瞬间峰值。backpressure 下保持容量守恒。

初版 `front_a` / `front_stress_a` 已完整结束且保留，但 A 曾等到输出归约才解除 metadata 依赖。最终版本改为响应完成通知，重跑所有受影响比较，并补齐统计。正式结论仅使用 b；初版绑定源也保留，不能混用两个版本的周期。

## 可复算的固定后端必要界

单独前端/内存约束均未否决新 H/E/L 配置：取并行界最大值，BNN/LSTM 均小于预算。停止依据是额外核实的真实 fence 分隔后端，而不是再次套用旧 64-context 失败界。

令 N 为完整候选数，I 为每 sample 全 canonical 初始化写请求总数，U_w 为 wave w 的不同 touched lines，W 为波次数。对本轮保留的 64-subbank 后端：

```
C >= I/32 + N/64 + sum_w(5*U_w/64 - 5)
```

证明条件如下。

1. 初始化、各 wave 候选计算及 finalize 受真实 sample/wave 屏障分隔，才能相加。其他并行服务的 busy time 不加入该和。旧 `inf_finite_service.hpp::init()` 在 seed 前完整初始化并排空，未使用双 canonical backing、惰性 epoch 初始化或与前 sample 叠加。
2. `inf_flat_bank.sv` 在 flush/DRAIN 后逐条执行 ENUM_READ→META→SELECT→PAYLOAD→SEND，理想下每 resident line 至少五周期。`inf_combo_owner.sv` 只有 core_done 后才令 scratch finish。
3. `inf_scratch_boundary.sv` 随后枚举未被 resident-final 消费的 spilled line，每条必须经历一笔串行 scratch read（至少 16 cycles）。给它宽松五周期界仍成立。resident/spilled 交集只提交一次；最终 resident 数 R 加非 resident spilled 数 S 等于 U_w，与替换次序无关，不需要继承旧 spill 次数。假定沿用现有接收所有候选的 accumulator，不增加候选前置过滤。
4. 某 subbank 至少承担 U_w/64 条 line；每 wave 减五周期，宽松地允许第一次输出免费。后续 ACK、pending、目录、路由、端口争用等开销全部忽略，故仍只是必要下界。
5. 64 条 II=1 pair lane、200 MHz 是假设；未将旧局部 OOC 迁移为完整核资格。80 ns 合同不随核频率偷换为固定 16 cycles。

| 完整 batch 的界 | BNN cycles | LSTM cycles |
|---|---:|---:|
| 初始化 I/32 | 1282065 | 1302101.25 |
| 候选 N/64 | 20108392.921875 | 20461136.125 |
| 最终枚举（已扣边界） | 9264659.21875 | 9454162.5 |
| 合计 | 30655117.140625 | 31217399.875 |
| 强 GPU 预算 | 30359993.888800000000 | 31899599.97777777600000000 |

BNN 下界超过预算 295,123.251825 cycles，即 **1.475616259125 ms**（约 0.972%）。LSTM 下界 156.086999375 ms 低于 159.49799988888888 ms；剩余约 3.411 ms 不能视为完整模型的真实余量。BNN 已使同一固定候选无法同时达到两个目标。

新的 `enum_interval_tb.sv` 通过 vivado-mcp 在 Vivado 2022.2 / xcu280-fsvh2892-2L-e 上运行 XSim：两 wave 不重置，128 次 final handshake，每 wave 连续间隔均为五周期，pair/accepted/retired/enumerated 守恒通过，$finish=9095 ns。原始 compile/elaborate/simulate/MCP 日志和实际编译列表均保留。该测试只实测 resident 枚举间隔；spilled 非重叠及串行 read 条件由固定 RTL 状态与连接证明，并非新增 spill 校准或新前端 RTL 资格。编译有旧模块无 timescale/未设预编译库等提示，无 error/fatal；C++ 有导入旧 screen 的未使用重命名 main 返回警告，不在执行路径。

## 资源账本与资格边界

| 部件 | 本轮容量/逻辑存储 | 已知物理资格 |
|---|---|---|
| FP32 | 64 pair lanes，每 lane 两次加法、两 pipeline 项 | 模型实际 operands；新 64-lane RTL/LUT/FF/DSP 未综合 |
| H/E/M | 128/256/128，带 owner/generation/offset 状态 | 有限模型；RAM/mux 映射未实现 |
| edge payload | 512×32B=16 KiB，另计 tag/control | 有限槽模型；BRAM 碎片/端口复制未知 |
| fork/ready/target event | 128/128/128（最后一项预留未用） | M context 保持目标事件；无独立目标 FIFO RTL |
| 物理请求/返回/tag | 32×64 请求、32×4 返回、32×32 credit | 三策略共享；注册路由未校准 |
| 目标输出 | 8×4096×65 bit=260 KiB | 两输入 cell_count 均小于 32768；新组合未综合 |
| accumulator | 64×1024 sets×4 ways×4 sectors×64 bit，8 MiB payload | 现有单 bank FSM；完整映射/布线未知 |
| pending17 | MAX_N=4194304，逻辑 17 bits/node；64 subbanks K=8 | 本轮只保留参数，未校准新并发 POP/SEED/COMMIT |
| scratch/目录 | 1 命令/subbank；2048 spill IDs/subbank；完整同 word/事件规则 | 未进入新的完整模型，未宣称容量/流量通过 |
| 初始化/控制/router/ACK | 计时边界必须保留 | 此次下界给零额外成本；未获得新物理资格 |

新完整核 LUT/FF/BRAM36/URAM/DSP 使用量均为 **未测量**，不能机械沿用旧 864 URAM/1888 BRAM36 加几 KiB。资源表是明确的逻辑容量及缺失资格，不是 fit 证明。

| 阶段/产物 | 状态 |
|---|---|
| 0：完整真实地址画像及必要界 | 完成；四份参考完整输出对旧 golden |
| 1：同资源前端局部模型 | 最终 51 native +6 连续窗口通过；未 RTL 校准 |
| 保留后端枚举 RTL witness | 完成；只验证必要界的现有 FSM 前提 |
| 2：新前端 RTL、周期校准、局部 OOC | 未进入：BNN 的固定后端必要界已失败 |
| 3：新完整连续有限架构/40 sample | 未进入；profile 不能替代它 |
| 4：完整核资源/时序 | 未进入；无新完整核频率资格 |

`fpga_seconds=null`、`complete_kernel_clock_qualified=false`、`board_measured=false`。不报告 simulated_resident_seconds 或 FPGA 加速比。

## 复核、归档与交付

源码位于 `accel/lookahead/fpga_decoupled_front/`：`run_profile.py`、`run_front.py`、`stress_front.py`、`analyze.py`、`verify_evidence.py`、`bind_evidence.py`、`archive.py`；目录存在即拒绝重建，避免覆盖已完成运行。重新实验应在新的结果目录/checkout 中显式调整运行名。归档恢复可使用 `archive.py --restore <空目标目录>`，只恢复所需紧凑证据，不展开旧大 trace。

```
python3 accel/lookahead/fpga_decoupled_front/verify_evidence.py
python3 accel/lookahead/fpga_decoupled_front/archive.py --verify
```

`verify_evidence.py` 独立重算每 wave touched/changed 汇总、真实对齐 row 请求、degree/零度/初始化计数、最终下界、57 项容量/周期直方图/请求守恒和冻结输出哈希。最终 frontend 从同源同参数重编译，与运行二进制 SHA256 完全一致。输入、source closure、编译命令、run 开始结束/退出码、输出和日志绑定均在归档；RTL 精确 wall-clock 完成时间未单独记录，保存原 MCP return=0 标记及 log mtime，不伪造时间。

紧凑证据根目录为 `results/fpga_decoupled_front_20261114/evidence_snapshot/`，manifest 包含每个原始文件的路径、大小、SHA256；大文件使用确定性 gzip 并验证解压哈希。包含初版负/中间证据、最终结果、完整输出、配置、source closure 和工具日志。17 条旧二进制波次仍按 base/manifest/hash 引用，未重复上传。

所有本轮实验已收到终态 receipt；没有需继续监督的实验。最终提交/远端一致性与受保护 refs 的核对记录单独保存于本地交付回执，避免将自身提交 SHA 写入同一个提交形成循环。未合并 main。下一轮若要继续，应先改变并验证导致 BNN 必要界失败的真实后端条件；不能仅扩大前端 context，也不能把 LSTM 的下界未失败视为已胜出。
