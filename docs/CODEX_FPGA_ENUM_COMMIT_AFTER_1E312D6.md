# Codex 执行指导：公平前端分配与枚举—提交闭环

**独立完整版，2026-11-14。基点：`1e312d6e4ffc5ea96f25c0b97931ad028e710584`。**

只需本文件和仓库已有源码、输入、归档即可执行。不依赖此前生成的指导文档、压缩包或聊天记录。请实际完成实现、验证和相应实验，按证据推进，不停留在计划。

## 1. 本轮目标与研究推进规则

最终研究目标保持：FPGA 优于有资格、同范围的 GPU、优化 CPU、原 VPR 多线程等基线；GPU 与 CPU 不要求排序。允许不上实板，以真实 RTL、实现时序和校准的有限模型研究加速。

本轮是一个新的、范围明确的候选，包含两个相互必要的改动：

1. 在同资源前端中修正低编号 lane 优先分配造成的利用率失衡。
2. 将现有五周期 resident 枚举、阻塞 scratch 路径、单事务 canonical 提交重构为有限流水与并发提交的完整服务链。

**旧 `enum5/200MHz` 的 BNN no-go 继续保留，但不能拿它作为“不实现本轮 enum2/并发提交候选”的理由。**改变导致必要界失败的真实结构，正是本轮任务。

同时修正停止规则的适用范围：

- 必要界只能否决符合其假设的配置。修改枚举间隔、服务并发或阶段依赖后，重新推导和验证。
- 一个输入的旧配置被否决，不自动禁止另一输入的合法实验或已明确授权的局部机制实现。
- 研究目标不附加“任何输入都必须获益，否则不得做任何 RTL”的前置条件。保留全部正负案例，逐案例报告。若只在部分案例胜出，只做限定主张；不能删去 BNN 或调松目标制造普遍成功。
- 实现错误不是架构负结果。修复正确性/构建问题并重新验证受影响部分；编译或测试失误应与有证据的架构 no-go 分开记录。
- 没有板卡不构成停止原因。模型、必要界、局部 RTL、完整核模拟、板测分别标注。

本轮不改变 ALT 数值语义，不人工拼接 workload，不减少 lane/端口计费，不自动改为新算法、缓存扫描或惰性初始化。先验证已发现的实际分配和提交限制。

## 2. 仓库与工作区

| 项目 | 值 |
|---|---|
| 仓库 | `https://github.com/GRYYYYYYY/3D_FPGA_Interconnects` |
| 本轮源码基点 | `1e312d6e4ffc5ea96f25c0b97931ad028e710584` |
| 上轮分支 | `accel/lookahead-inf-decoupled-front-20261114` |
| 建议新分支 | `accel/lookahead-balanced-enum-commit-20261114` |
| 建议源码目录 | `accel/lookahead/fpga_enum_commit/` |
| 建议报告 | `docs/lookahead_fpga_enum_commit.md` |
| 软件终态基点 | `a64c934956be6514a27f66fd1a46f09ef4a2fab9` |
| GPU 独立终态 | `cc71869709bcf3124ae81ebfdcd8f36819c4c90d` |

读取适用 AGENTS.md；检查 pwd、Git 状态、worktree、HEAD 和实际在途进程。已有正确工作区则接续；否则从完整基点建立独立 worktree。不要为了换名称重启实验。

保护 main、原稿、STRICT、旧 golden、历史正负归档、未跟踪指导文档及其他分支。新增结果使用唯一目录；不 reset/clean、强推、改历史或合并 main。完成后正常推送本轮分支并核对远端 SHA。

沿用现有 Vivado 2022.2 / `xcu280-fsvh2892-2L-e`，先核对实际安装和脚本。不要无说明换器件或把不同实现的频率拼在一起。

## 3. 已完成证据与本轮必须读取的入口

直接复用以下已完成工作，不重新排队 GPU，也不重做 CUDA 补档：

- GPU 254 项 receipts、六项旧 P8/F0 模型、CUDA `.cu` 补档。
- `1e312d6` 的四份完整参考输出、完整真实地址画像、最终 `front_b/front_stress_b` 的 57 项结果。
- 现有枚举 witness：不重置的两个 wave、共 128 次 final handshake，间隔五周期。这是局部枚举证据，不是两次完整 workload RTL。
- 原两 subbank 5 ns 局部 OOC、原完整核时序负结果。它们都不能授予新结构频率资格。

先读：

```text
docs/lookahead_fpga_decoupled_front.md
docs/lookahead_fpga_pending_stream.md
docs/lookahead_pending17_invariant.md
docs/lookahead_fpga_inf_followup.md

accel/lookahead/fpga_decoupled_front/frontend_model.cpp
accel/lookahead/fpga_decoupled_front/graph.hpp
accel/lookahead/fpga_decoupled_front/physical_profile.hpp
accel/lookahead/fpga_decoupled_front/configuration.json
accel/lookahead/fpga_decoupled_front/analyze.py
accel/lookahead/fpga_decoupled_front/enum_interval_tb.sv
accel/lookahead/fpga_decoupled_front/archive.py
accel/lookahead/fpga_decoupled_front/verify_evidence.py

accel/lookahead/fpga_sparse_stream_r2/pending17.hpp
accel/lookahead/fpga_sparse_stream_r2/pending17_reference.cpp
accel/lookahead/fpga_sparse_stream_r2/inf_finite_reference.cpp
accel/lookahead/fpga_sparse_stream_r2/inf_finite_service.hpp
accel/lookahead/fpga_sparse_stream_r2/rtl/inf_flat_bank.sv
accel/lookahead/fpga_sparse_stream_r2/rtl/inf_combo_owner.sv
accel/lookahead/fpga_sparse_stream_r2/rtl/inf_scratch_boundary.sv
accel/lookahead/fpga_sparse_stream_r2/rtl/pending17_service.sv
accel/lookahead/fpga_sparse_stream_r2/rtl/frontend.sv
accel/lookahead/fpga_sparse_stream_r2/rtl/external_tile.sv
accel/lookahead/fpga_sparse_stream_r2/rtl/shared_fabric.sv
```

沿构建列表、include/module 读取实际 `pair_lane`、POP fork、cell reducer、目录和 FIFO 代码。不要混用同名副本。

本轮完整证据入口为 `results/fpga_decoupled_front_20261114/evidence_snapshot/`。按 manifest/hash 恢复需要的 `profile_a`、`front_b`、`front_stress_b`、`analysis_b`。正式前端结论使用 b 版本，不能混入旧 `front_a` 中等待输出归约才解除 metadata 依赖的周期。

枚举 witness 的归档在 `analysis_b/enum_{compile,elaborate,simulate}.log` 和 `bindings/enum/`（receipt、vivado.log、编译列表、Tcl、glbl 等），冻结源也在 `bindings/final_delivery_source/`。`enum_rtl_a/project/` 是服务器原始运行路径，按 receipt 定位；snapshot 没有完整 Vivado 工程，不能要求从归档恢复一个并不存在的目录。

较早证据位于 `results/fpga_sparse_stream_r2_20261112/evidence_snapshot/`：

- GPU：`software_private_inf_gpu_b_terminal/software/private_inf_gpu_b/{summary,binding}.json`。
- 旧完整 INF B：`inf_followup_combination2317/accumulator/inf_finite_native_b/{bnn_export,lstm_s2}/`。
- 旧局部 RTL/OOC：同一 INF 归档中的 `accumulator/inf_combo_rtl_e/`、`accumulator/inf_combo_rtl_h/`、`timing/inf_combo_c_5ns/`。

服务器原工作目录可用时按冻结路径和哈希读取；不能假定某个 sibling worktree 永远存在。归档缺项应先定位 Git 对象、manifest 和已存在的服务器目录，不要求用户补交旧指导文件。

## 4. 已知数据与计时目标

主边界为 `RESIDENT_COMPLETE_BATCH_V2`。每个完整输入包含 40 个真实 sample；图和输入已驻留设备内存，但初始化、运行中的图访问、队列、FP32、归约、scratch、canonical 提交、目录、输出和最终 ACK/fence 都计入。

| 固定量 | BNN | LSTM |
|---|---:|---:|
| GPU 较强目标，秒 | 0.151799969444 | 0.15949799988888888 |
| nodes | 4,102,608 | 4,166,724 |
| output cells | 25,088 | 25,538 |
| parents | 102,918,965 | 104,730,480 |
| 非空 parents | 58,250,255 | 59,300,519 |
| candidates N | 1,286,937,147 | 1,309,512,712 |
| canonical 初始化 32B 请求 I | 41,026,080 | 41,667,240 |
| 每 wave 不同 touched line 的总和 U | 118,725,942 | 121,154,080 |
| 每 wave 改善 canonical line 的总和 V | 51,973,592 | 53,038,572 |
| wave 数 W | 2,161 | 2,200 |

固定条件资源：64 subbanks、64 条实际 pair lanes（目标 II1）、32 个物理 32B 端口、每端口 32 个共享 credit、80 ns latency、5 ns 最小请求间隔。200 MHz 只作为初始条件；尚无新完整核资格。

当前 `final_read/final_write` 是语义上的 touched/changed line 计数，不是已完成的新硬件流量。它们不含 scratch、目录等额外请求；新实际流量仍须重数。

BNN 保留较强历史 GPU 目标，不换成较慢 INF CUDA。已有统计按独立进程分组，不把九个正式值当九个独立进程。只有真实输入/算法/边界改变导致失配时，才补必要软件测量。

## 5. 为什么本轮必须同时处理前端和后端

### 5.1 分配失衡已有具体证据

最终 B 配置的两个代表性大 wave：

| 量 | BNN wave_2_38_B | LSTM wave_7_36_B |
|---|---:|---:|
| cycles | 118,360 | 121,175 |
| candidate/cycle | 20.7245 | 20.4630 |
| lane 0–15 平均利用率 | 92.9175% | 92.1500% |
| lane 16–31 平均利用率 | 36.3179% | 35.3855% |
| lane 32–47 平均利用率 | 0.2930% | 0.3581% |
| lane 48–63 平均利用率 | 0 | 0 |
| 全程零发射 lane 数 | 22，编号 42–63 | 18，编号 46–63 |
| E 平均占用 /256 | 85.269 | 84.315 |
| 全部端口合计请求/cycle /32 | 7.0848 | 7.0657 |

`frontend_model.cpp` 的 ready→E 分配每次从 `i=0` 查找第一个空 descriptor，连续四项又绑定同一 lane；低编号空位不断被重用。每 lane 的八个 beat 槽是局部资源，其余 lane 的空槽不能帮助热点。这是可证伪的具体分配问题，不能把当前约 32% 总利用率当成所有 64-lane 前端的固有限制。

这些局部数字也不能外推为完整 batch 时间。它们说明“只差 0.972% 就能赢”的解读不成立：153 ms 的界假设理想 64-lane 消费，而当前局部前端离这个条件还有明显距离。

### 5.2 五周期枚举是一个限制，单事务提交是另一个限制

旧必要界：

```text
C_old >= I/32 + N/64 + 5*U/64 - 5*W
```

BNN/LSTM 在条件 200 MHz 下分别为 153.275586/156.086999 ms。这个界已省略许多真实成本，不能将 BNN 超过目标的 1.475616 ms 当作完整实现的实际差距。

`pending17_service.sv` 现在仍是整 subbank 单事务：只有 IDLE 可接收，canonical read→可能的 write ACK→PV/event retirement 完成后才返回 IDLE。配置中的 K=8 没有自动变成真实八事务硬件。

如果完整候选沿用当前“一笔事务/subbank”且每 touched line 读一次 canonical、每 changed line 写一次，最终阶段仅内存往返占用就有：

```text
C_final_RMW >= 16 * (U + V) / (64 * K), K=1
```

| 必要项（假设 200 MHz） | BNN | LSTM |
|---|---:|---:|
| 理想初始化＋候选消费 | 106.952290 ms | 108.816187 ms |
| 为达到 GPU 目标剩余的 finalize 时间上限 | 44.847680 ms | 50.681813 ms |
| 现有 K1 的 final canonical 往返占用界 | 213.374418 ms | 217.740815 ms |
| 上述 K1 加初始化/消费的弱总界 | 320.326707 ms | 326.557002 ms |
| K4 加初始化/消费的弱总界 | 160.295894 ms | 163.251391 ms |

这些是保留相应服务协议的下界，不是已实现的新 K8 模型结果。K4 的最乐观占用仍不够；K8 是本轮明确需要实现/验证的设计点，不是成功保证。

仅把 enum 的 II5 改为 II2，并保留 K1 canonical 服务，不会解决以上限制。

### 5.3 新候选仍有一个不能省略的内存界

即使具备 K8，最终 canonical 读写也要共享 32 个端口：

```text
C_final_mem >= (U + V) / 32
```

其对应 BNN/LSTM 26.671802/27.217602 ms。以 enum II2、K8 为条件，单就这些理想项，新总下界仍至少约 133.624092/136.033789 ms。**它们不是新 FPGA 时间或速度预测。**POP、实际前端、scratch、事件、路由、冲突和尾部尚未加入。

本轮选择 II2 作为 resident 枚举的首要目标；II1 不是一开始就必须达到的条件。实际瓶颈可能已转到内存或事件退休，必须测完整退休吞吐。

## 6. 执行线 F：同资源修正 lane 分配

先保持 D=1 和上轮 B 的所有容量/语义：H128、E256、M128、L64、512 beat 槽、fork/ready 各128、8×4096×65-bit 输出状态、32 物理端口及其请求/返回/credit 限制。

实现两个模式：

- `FIRST_FREE`：冻结的旧分配规则。
- `LANE_RR`：持久轮转指针先选择有空 context 的 lane，再选择该 lane 的局部 context；真实分配成功才推进指针。

零度 parent 仍完成原 row/metadata/输出语义，不制造 edge；不用新过滤、cache 或 degree 预知改变工作量。先保留其他请求优先级和返回写配额，以便归因。

进行同口径对照：17 个冻结原生 wave 和两个已有连续压力窗口。旧 FIRST_FREE 证据在源码行为/参数/输入完全一致时可引用，但至少用一个小图和一个大 wave 复现同源兼容模式；任何相关服务变化都要重新配对。

输出每 lane 的工作、闲置、占用、排队、分配次数、per-lane beat 槽压力与整段 elapsed cycles。利用率更均衡本身不是加速结论，必须看完成时间和资源/流量。

特别检查三类后续偏置，但不同时无差别修改：

1. metadata→edge→header 的固定 request 入队先后顺序。
2. edge descriptor 按低编号优先申请 credit。
3. row/meta/edge 共用 `wrote[lane]` 的一次返回写额度。

只有 LANE_RR 后的日志仍支持某一限制，才做对应的独立消融，例如 work-conserving 的每 port 服务类 RR。不能直接删除返回 RAM 端口约束；新增独立端口必须有 RTL/资源依据。

分配接收带宽在控制组和候选组保持相同。完成行为层因果比较后，为实际 RTL 明确每 cycle 能接受多少 parent、选择树级数和 FIFO；任何新增 pipeline/吞吐限制回灌两组模型。不得让无界 C++ while 循环成为完整硬件中的免费多路分配器。

也不能在 RTL 化时将它简化成全局一 parent/cycle。按整个 GPU deadline 和200MHz计算，全部 parent 的共同 fork/header/ready 处理入口，仅弱必要峰值就至少为4 parents/cycle；只为非空 parent 写入 E 的入口至少为2/cycle。扣除初始化和finalize后要求还会提高。这些不是充分配置。

分组 dispatch 可先以合计8 parents/cycle为待实现设计点，例如多个有限的lane组各自接收；必须按实际阶段预算、路由和资源验证，并让两组对照使用相同带宽。零度 parent 不消耗 E 状态写入，但保留其真实 row/metadata 工作。分配分组不改变物理line条带映射，不为每个lane组额外提供32个端口。

最终 front 必须具备真实、有限、可实现的分组仲裁。可以用分层 RR；无需改变物理 line→port 映射或复制图数据。改善前端不会授予完整核频率资格。

## 7. 执行线 B：实现枚举—scratch—canonical—事件闭环

执行线 F 与本节的源码审阅/局部实现可独立推进。本节不能因为旧 enum5 已失败而停在“建议流水化”。优先沿用已有 SystemVerilog，不要求迁移到 HLS。

### 7.1 Resident 枚举：II2 目标，保留有限背压

现有状态为 `ENUM_READ→ENUM_META→ENUM_SELECT→ENUM_PAYLOAD→ENUM_SEND`。Flush 后 candidate pipeline 已排空，occupied/meta/payload 的独立条目读取可以重叠。

实现真实弹性流水，明确 occupied 读、metadata 读/选择、payload 读、输出各自的 RAM 延迟、有效位和停顿条件。延迟可以超过两周期，目标是独立条目的启动间隔不超过两周期。

先给有限 fragment FIFO（建议16项/subbank，容量要进模型与账本），避免一个下游 ready 信号冻结全部前级。满时正确回压，不允许无界积累。

metadata 清除必须与数据已安全进入有限输出存储/退休的协议一致。输出 stall、flush 保持、空/满 occupied、同 set 不同 way、最后一项、连续 wave 都不能漏发、重复或过早 done。使用真正 BRAM/URAM 读口；不能把 payload 改成无代价组合数组。

保留旧 enum5 作为匹配对照。分别记录扫描启动、fragment 接收和最终提交退休，不能只展示空载枚举 II。

### 7.2 Scratch：先去掉所有 resident line 的共同阻塞路径

旧 `inf_scratch_boundary` 即使某个 resident line 没有 spill，也经过 IDLE→LOOKUP→DECIDE→COMMIT；下游阻塞会让全部工作停在一个事务上。

本轮最小安全改动：

1. Expand 阶段先保留现有单在途 spill RMW，防止一次改变所有机制。
2. 进入 finalize 前，等待该 wave 的 expand spill 写 ACK 完成。此后 spilled bitmap 在 finalize 中只读。
3. Resident 枚举进入有限 bitmap 查询流水。未 spilled 的 line 可直接进入有限 canonical commit FIFO（建议16项/subbank）；已 spilled 的 line 进入独立有限 merge 队列（建议16项/subbank）。
4. Merge 起步仍允许每 subbank 一笔 scratch read。它等待外存时，未 spilled 的快路可以继续；FIFO 满则真实背压。
5. 合并后的 whole-pair line 与快路共用公平的有限 commit 仲裁，不为两个支路虚增端口。

**Consumed bitmap 是必须单独处理的依赖。**当前每128-bit bitmap word 含64个 line 的 spilled/consumed 位。不同 canonical line 可能修改同一 bitmap word。不能并发读取旧整字、各自改一位再写回，否则会丢位。

可用有限的原子 OR/前递流水或短程 bitmap-word scoreboard 维护 consumed。不要为了改一个 bit 持有整个 bitmap-word 锁跨越80ns外存往返；同时不能假设任意多位更新免费并发。

只有 resident 枚举及其 merge/commit 入队、相应 consumed 更新都已可靠完成，才启动剩余 spill ID 的枚举。保留 resident/spilled 交集恰好一次提交；未进入 canonical 队列的数据不能提前标成已消费后丢掉。

若新完整调度的实际 spill 数、merge 队列背压或热点证明单在途 scratch read 仍是决定性限制，再增加一个明确的2/4并发 scratch 候选，加入真实 tags、line 依赖、bitmap-word 依赖和容量。不得从旧模型八笔 fragment 并发直接获得资格。

旧次序的 spill 计数只能用于定位，不能搬作新吞吐/流量。当前变更足以改变替换和归约顺序，所有实际访问重数。

### 7.3 Canonical/pending：真正实现每 subbank K=8

把 `pending17_service` 从整 bank 单事务改成有限的按 whole word 保留依赖的服务。每 subbank 允许最多八个不同 canonical word 在途；同 word 的读、POP、SEED、COMMIT 遵守原语义顺序。

每事务保存 word/node/sector、opcode、whole-pair operand、旧 label/PV、读写状态、tag/generation、最多四个事件及退休状态。只增加有限事务记录，不复制整份 pending 存储来假装多端口。

现有四个 sector 共用32B canonical line、68-bit pending word。保持 frozen `pending17_transform` 的版本、Present、bucket、wrap、whole-pair 比较和 opcode7 行提交语义。Present 不由 version==0 推导，delay/congestion 不可分开取最小。

读取 RAM、apply、写 ACK、PV 更新、事件发布分别为有边界的服务；明确每个真实 BRAM/URAM 端口及依赖。PV/事件处理可流水，但不能绕过同 word reservation。

**只有 canonical 写 ACK（若有）、PV 写回、该事务全部目录事件或有效 POP token 可靠发布都退休后，才释放 word reservation。**未 changed 的 line 也需正确退休，不能为统计吞吐直接忽略。

对于最多四事件的 full-line update，在接收/推进事务前预留足够的有限退休存储；建议总32个事件槽/subbank作为起点，实际目录 append 服务有明确吞吐/背压。事件槽不是目录容量，目录还需要真实有限成员结构。

POP 的有效 token 要在清 pending 前取得可靠存储，stale POP 不发 token。SEED、POP、单值更新、opcode7 和连续 wave 必须共同验证，不能只加速全为独立 changed-line 的特殊数据。

### 7.4 带 tag 的共享物理接口必须进入闭环

先做一个 owner、两个 subbank 的局部闭环，两个 subbank 各 K8。全部 scratch/canonical 客户端共享**一个**物理32B端口、32个总credit，80ns/5ns合同。

旧接口无 transaction ID 是因为单事务。并发版本必须增加 local ID；物理 tag table 恢复 `{service,subbank,transaction,generation}`，乱序返回能正确找到事务。不能继续用无 tag 接口假装八笔在途。

物理响应接受后归还端口 credit；事务仍可能持有返回数据、word reservation 和事件额度。它们的释放条件分别实现。

请求与返回都有有限队列、寄存边界、公平仲裁和 backpressure。最终若 arbiter 仍只在 TB，不得把它计作 DUT 已过 OOC 的部分；应交付可综合的实际共享接口。

局部 owner0 的地址检查要保留；完整32 owners/64 subbanks集成时，将 owner ID 正确参数化，不能将 hardcoded owner0 复制64次而仍丢弃高 owner 地址。

## 8. 局部闭环验证与 OOC：本轮应产生的真实硬件证据

先对比：

- 旧 enum5/K1/串行 scratch 的相同输入基线。
- 新 enum2/K8/有限 no-spill 快路与 merge 支路。
- 必要时增加“仅 enum2、保留 K1”的诊断，展示输出被下游限制的原因；不展开大规模参数扫描。

测试覆盖由风险决定，不追求用测试数量替代证据：

1. 全 resident、全部 changed/全部 unchanged、不同 changed fraction。
2. First spill、重复 spill、resident+spilled 交集、只在 scratch 的 line，spill ID 接近/达到/超过容量时明确行为。
3. 同 canonical word 不同 sector、相同 word 混合 opcode；不同 line 但同 bitmap word 的并发 consumed 更新。
4. 响应乱序、同周期返回、tag 满、event FIFO 满、目录长背压、scratch merge等待时快路继续。
5. Flush 前最后一次候选、expand spill未ACK、最后一个 resident merge、最后 spill ID，防止过早done。
6. 连续至少两个 wave、两个 sample 的状态转换；不靠TB免费重置跳过真实初始化。
7. 原生代表 trace，包含热点 set/word、真实 spill/merge与目录事件分布；不能只用均匀独立地址。

局部测试比较该 owner/subbank 投影内的 canonical label、pending17、目录成员/事件和适用的局部输出与冻结 reference。两个 subbank 的后端原型不必独立产生完整 native wire-map；完整图输出核对在第10节完成，投影一致不能升级为完整输出资格。每个请求/响应/ACK/事件都可核对，最终状态的 hash 不能替代不丢事件与排空检查。

报告四种不同指标：枚举发射间隔、commit接收间隔、事务反馈延迟、**完成 ACK+PV+目录事件后的退休间隔**。真实后端加速以完整处理时间与退休吞吐为准。

模型使用相同输入、内存合同、FIFO、RAM延迟和仲裁，逐周期校准服务交接与排空。可做到精确一致时要求一致；抽象误差按阶段解释，不能靠总周期抵消。调整后重新验证受影响路径。

随后对这个完整局部链做200MHz OOC，包含真实共享arbiter、FIFO和接口时序约束；检查setup/hold/pulse、未约束路径和资源。旧局部+0.635ns不迁移到新核。若失败，修复实际路径；增加寄存级数后把服务延迟/II更新回模型。

本轮前端若采用新RR/预取服务，也需交付相应缩小配置RTL和实际FP32、返回/分配校准，才能进入完整核资格。C++ pair计算通过不等于64条RTL流水已过时序。

## 9. 联合预算：用它发现下一个真实限制，不用它制造成功

为新候选建立按sample/wave、subbank、物理port的统一服务账本，至少包含：

- init、seed/POP、row/edge/meta、真实FP32、owner/set归约；
- expand spill RMW、resident枚举、final scratch merge/残余扫描；
- canonical read/write、PV端口、目录 append、目标输出、所有fence/尾部。

需要的同时在途数由生命周期和吞吐共同约束，不能只看请求tag数。新增FIFO只能隐藏有限等待，不能增加最终瓶颈服务率。

对已经由真实wave屏障分开的部分可以相加；可重叠服务取必要的最大约束，不把各模块busy/context-cycles直接相加。按热点port/bank计算，不能只用总量平均。

一个可复核的弱筛选式是：

```text
C >= I/32 + N/64
     + max(r*U/64 - r*W,
           16*(U+V)/(64*K),
           (U+V)/32)
```

这里的示例采用实际最短枚举间隔固定为 r=2、K=8 的候选；r 必须取实际实现及协议保证的最短服务间隔。“目标II≤2”本身不能证明r=2下界，若实现能II1则用r=1重算。当前示例由canonical端口界主导，II1并不使其自动降到纯枚举算术值。这个式子省略了scratch、真实前端和其他代价；它既不证明可实现，也不能代替完整模型。若final协议改变了读写次数或枚举方式，用实际依赖重推。

时钟变化时80ns和5ns要重算；若接口使用其他时钟域，需要真实CDC/接口模型。不要把200MHz旧周期直接除以202MHz绕过0.972%门槛。初期固定200MHz，优先改变实际结构。

不要为“保险”添加未经推导的所有模块逐wave全局排空。Canonical修改需等待该wave候选归约完成，下一wave需要相关label/PV/目录状态有效。Metadata/目标输出携带不可变node/pair/qid/bucket-epoch，可沿已验证语义在同bucket内独立推进；targets判断、bucket/qid切换和导出前必须排空。

## 10. 完整模型、完整输入与最终核资格

局部结构稳定后，接入公平前端和新后端，建立**连续完整**的有限架构模型。原 `frontend_model.cpp` 的理想POP来源、永远ready的candidate sink、每wave重建目标状态都不能保留为完整性能路径。

实际建模全64 lanes、64 subbanks、32物理端口及其路由、仲裁、注册化返回，有限H/E/M、beat槽、pending K8、scratch和目录。不要用无界map替代累加器，不继承旧八fragment并发或旧spill计数。

完整BNN/LSTM各40sample必须执行，输出逐一对 frozen ALT/native golden。保留STRICT不等价边界。固定一个完整候选先做完，避免同时运行大量参数组合。

实现高效模拟以控制实验时间：维护active index/就绪队列/直接slot索引，避免每cycle对全部descriptor再扫描全部512槽。可使用event-driven推进，但不能跳过竞争/背压。只有证明sample状态独立、每sample初始状态和所有初始化/结束成本一致，才可并行模拟不同sample再按硬件顺序求和；不能把CPU模拟并行度算成FPGA加速。Wave间有状态依赖，不能随意独立外推。

长任务要有进度、checkpoint、源码/input/config绑定和真实终态receipt。逐候选大trace只保存必要校准案例；完整batch用可复现输入、完整输出、流式计数与摘要，不为归档重复制造数十GB日志。

完整模型有合理性能空间、服务已校准、资源可容纳后，再实现完整top并做OOC。资源包括所有FP32、PV、metadata/output、FIFO、tags、路由、目录、控制和实际RAM映射；旧864URAM/1888BRAM账本不可机械复用。声明32个外部物理服务口的时序和内存合同，不把未包含的板级控制器伪称已验证。

完整核频率、有限服务、正确输出和适用RTL校准齐备后，才报告 `simulated_resident_seconds` 与模拟加速比。仅条件模型则单列 `conditional_predicted_seconds`；必要界列 `lower_bound_seconds`。全程无实板时 `board_measured=false`。

如果要声称同时优于优化CPU/原VPR多线程，再补其真正同范围、同输入的资格。现有ALT CPU resident结果不能替代native STRICT或原VPR的计时。E2和Process分开报告，不用resident替代全流程。

## 11. 结果门槛与交付

允许本轮产生以下任一真实结论，但推进不能停在重复旧已知限制：

- **局部机制有效**：分配更均衡且局部elapsed改善，或完整后端退休吞吐/时间改善；限定到实际验证范围。
- **局部RTL合格**：功能、有限容量、周期、时序成立，完整核仍未完成。
- **完整条件模型**：完整输出/服务正确，但完整核频率或部分校准缺失；不给硬件胜出资格。
- **模拟结果合格**：完整核时序、完整有限模型、适用校准和输出齐备；逐案例给出收益、负例和敏感性。
- **新候选负结果**：本轮实际修改后的结构仍被有效下界、物理资源或完整模型否决；明确哪个新条件失败。

不能用旧enum5或旧K1的下界否决已经改为enum2/K8的新候选；也不能只因弱下界低于GPU就进入“成功”。出现单case负结果应保留，不自动删除其他有意义的验证。完整扩核是否值得继续，依据新结构的证据和明确的研究价值决定。

需要的交付：

1. 公平分配消融和lane/port/返回利用率；绑定实际源和输入。
2. 新后端可运行RTL、TB、旧/新匹配比较、完整退休统计、模型校准和OOC。
3. 关键不变量：whole-word依赖、bitmap-word更新、交集去重、所有ACK/PV/事件退休、wave/sample排空。
4. 联合预算与新资源账本；若进入则交付完整40-sample模型及完整核结果。
5. 独立报告、manifest/校验和、失败记录、最终Git提交和远端核对、真实进程状态。

报告首先说明实际瓶颈、改动、收益/代价和允许的结论，再列验证项目数量。确认没有在途任务才说全部结束；阶段性checkpoint不冒充整轮完成。历史归档只读引用，所有新失败也保留。

## 12. 本文件内可执行的算术复核

```python
from decimal import Decimal, getcontext
getcontext().prec = 36
for name, N, I, U, V, W, target in [
    ("BNN",1286937147,41026080,118725942,51973592,2161,"0.151799969444"),
    ("LSTM",1309512712,41667240,121154080,53038572,2200,"0.15949799988888888"),
]:
    f=Decimal(200000000)
    budget=Decimal(target)*f
    fixed=Decimal(I)/32+Decimal(N)/64
    enum5=Decimal(5)*U/64-5*W
    mem=Decimal(U+V)/32
    rmw1=Decimal(16)*(U+V)/64
    rmw8=rmw1/8
    enum2=Decimal(2)*U/64-2*W
    print(name, {
        "old_enum5_lower_bound_ms":str((fixed+enum5)/f*1000),
        "finalize_budget_after_ideal_init_compute_ms":str((budget-fixed)/f*1000),
        "retained_K1_RMW_only_lower_bound_ms":str(rmw1/f*1000),
        "retained_K1_weak_total_lower_bound_ms":str((fixed+rmw1)/f*1000),
        "K4_weak_total_lower_bound_ms":str((fixed+rmw1/4)/f*1000),
        "K8_context_lower_bound_ms":str(rmw8/f*1000),
        "final_memory_lower_bound_ms":str(mem/f*1000),
        "enum2_K8_weak_total_lower_bound_ms":str((fixed+max(enum2,rmw8,mem))/f*1000),
        "scope":"necessary arithmetic constraints, not FPGA predictions or measurements",
    })
```

## 13. 固定来源

- [本轮完成报告](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/1e312d6e4ffc5ea96f25c0b97931ad028e710584/docs/lookahead_fpga_decoupled_front.md)
- [当前前端分配与服务](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/1e312d6e4ffc5ea96f25c0b97931ad028e710584/accel/lookahead/fpga_decoupled_front/frontend_model.cpp)
- [本轮下界实现](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/1e312d6e4ffc5ea96f25c0b97931ad028e710584/accel/lookahead/fpga_decoupled_front/analyze.py)
- [现有resident枚举](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/1e312d6e4ffc5ea96f25c0b97931ad028e710584/accel/lookahead/fpga_sparse_stream_r2/rtl/inf_flat_bank.sv)
- [现有scratch服务](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/1e312d6e4ffc5ea96f25c0b97931ad028e710584/accel/lookahead/fpga_sparse_stream_r2/rtl/inf_scratch_boundary.sv)
- [现有canonical/pending服务](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/1e312d6e4ffc5ea96f25c0b97931ad028e710584/accel/lookahead/fpga_sparse_stream_r2/rtl/pending17_service.sv)
- [现有两subbank组合](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/1e312d6e4ffc5ea96f25c0b97931ad028e710584/accel/lookahead/fpga_sparse_stream_r2/rtl/inf_combo_owner.sv)
- [原生前端结果归档](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/tree/1e312d6e4ffc5ea96f25c0b97931ad028e710584/results/fpga_decoupled_front_20261114/evidence_snapshot/front_b)

如执行中发现本文与固定源码/receipt有差异，应记录并查明后修正新报告，不篡改旧证据使其符合本文。
