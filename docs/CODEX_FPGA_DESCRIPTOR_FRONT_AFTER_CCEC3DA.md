# CODEX_FPGA_DESCRIPTOR_FRONT_AFTER_CCEC3DA

## 任务：在 ccec3da 上验证描述符融合、可实现的前端供给及完整 batch 收益

日期：2026-11-14。

这是完整、独立的执行指导。只需要本文件、现有仓库以及服务器已有输入和工具。不要寻找、要求上传或依赖任何未提供的旧指导文件、ZIP、聊天附件。仓库已有历史文件可以作为证据读取，但不是本文件缺失内容的补丁。

请直接完成下述已授权的代码修改、有限模型、必要 RTL 验证和符合条件的实现；修复正常实现问题后继续。使用独立 worktree/分支，不修改 main、原稿、STRICT、旧 golden、历史归档或未跟踪指导文档。复用已经完成且可核验的 GPU/旧模型证据。不要重新启动旧实验，不要因为没有开发板而停止本任务。

本轮目标仍是：在明确且一致的比较边界下，研究 FPGA 优于优化 CPU、基础/已测优化 CUDA、原 VPR 多线程等基线的可能性。GPU 与 CPU 不要求排序。不得预设实验必胜，也不得将单个配置失败扩大为整个 FPGA 路线不可行。

## 0. 基点、分支和已有状态

固定基点：

    ccec3da64b4c5be643809c2bdda94145c4bb8187

对应分支：

    accel/lookahead-balanced-enum-commit-20261114

建议新分支：

    accel/lookahead-descriptor-front-20261114

建议新代码目录：

    accel/lookahead/fpga_descriptor_front/

建议新结果目录：

    results/fpga_descriptor_front_20261114/

报告：

    docs/lookahead_fpga_descriptor_front.md

首次操作检查实际仓库、AGENTS.md、git 状态、worktree 和活动实验。获取远端基点并核对完整 SHA；新 worktree 必须从该 SHA 创建。若同名本轮 worktree 已存在，核对其祖先、源绑定、未提交内容和实际进程后续做，不能覆盖、强制重置或重复运行。

本文件不要求读取服务器以外的新附件。已有指导文件若未跟踪，原样保留。所有新代码和模型修复写入新目录/分支；历史 D 模型结果不能原地修改成新对照。

### 0.1 必须复用的已完成证据

- BNN/LSTM 各 40 个完整 sample 的冻结 ALT 输出。
- 已完成并归档的 CUDA 源码闭包、254 项 GPU 执行 receipt。
- 已完成的六项 P8/F0 原模型结果。
- ccec3da 的 final D 模型、前后端 RTL、实际时序失败及资源证据。
- 已有 ALT native 回接、map 身份与 QoR 资格链；新表示是否继承它，需要明确数据链证明。

不重新补 .cu；不重新跑 INF 与 prepared-POP 对照。新的表示若值得补软件基线，按第 10 节实施，而不是把旧实验重做一遍。

## 1. 已知事实与本轮要回答的问题

### 1.1 历史 final D 的实际范围

| 项目 | BNN | LSTM |
|---|---:|---:|
| 完整 batch 周期 | 52,265,602 | 52,888,942 |
| 初始化周期 | 1,283,840 | 1,303,880 |
| POP+expand 周期 | 39,827,941 | 40,289,728 |
| finalize（含 bitmap clear）周期 | 11,025,461 | 11,164,694 |
| 输出导出周期 | 126,320 | 128,600 |
| seed/bucket/其他周期 | 2,040 | 2,040 |
| 假设 200 MHz 的条件总时间 | 261.328010 ms | 264.444710 ms |
| 复用的强 CUDA 目标 | 151.799969444 ms | 159.49799988888888 ms |

这些是条件模型结果，不是完整核 RTL 周期或板测时间。其前端/目录/全局请求返回网络没有获得整体校准，不能称保守上界。

ccec3da 的后端 2.14–2.32 倍收益，来自同一物理端口条件下的两个 subbank、大 owner 投影的 RTL 完整退休闭环，不能当作全 batch 提速。新实验保留这项已完成贡献。

### 1.2 现在的关键判断

1. POP+expand 占完整模型约 76.2%。从旧调度中删除全部 finalize，仍需 206.200705/208.621240 ms，超过 CUDA。
2. 64 个 II1 算术 lane 对实际候选数的无气泡时间为 100.541965/102.305681 ms。加旧 finalize 和其他阶段仍需 162.730270/165.301751 ms。前端和最终提交必须共同改善，或改变阶段之间的合法重叠方式。
3. 上述“删除/替换旧阶段”的计算是诊断，不是另一架构的必要界。新到达顺序会改变 spill、冲突和阶段时间。
4. 现有每 8-lane leaf 只有一个 EDGE 请求/返回口；D 模型未限制每组只能一笔 EDGE 请求。不得把 D 模型直接解释成已实现 leaf 复制八份的结果。
5. 没有证据支持直接增加 E context、K 或 cache 容量。要先减少明确的重复访问，冻结真实服务拓扑，并核查端口/返回/目录的因果等待。

本轮主候选是：

- 将 ROW 与 sample-dependent metadata 合为一个精确节点描述符；
- 在总 64 算术 lane、总 E/beat 容量不变的条件下，比较 8×8 与 16×4 前端分组；
- 给请求、返回、FP32、目录和后端边界加入真实的有限服务和寄存级；
- 先保留 enum2、K8 和既有正确提交协议；
- 若仍存在明确缺口，只选择一个有因果依据的补充候选，不同时铺开多个硬件重写。

## 2. 执行顺序与交付原则

顺序如下：

A. 核验基点和最终 D；补齐服务契约、描述符准入与因果计数。

B. 实现精确描述符转换和四格有限对照，找出净收益来源。

C. 并行完成前端关键路径修复、真实接口 context、必要服务 RTL 校准。

D. 运行最有依据候选的完整原生 batch；需要时执行一个条件补充实验。

E. 候选具备性能依据后，完成完整小图 top、完整配置 OOC 和新模型校准；补齐对应软件对照及报告。

A/B/C 的可独立工作可以并行。依赖关系、同一结果目录写入、归档和推送保持顺序。CPU 多进程仅加速模拟，不代表 FPGA 多 sample 并行。仅 D 节明确实现的交错调度才能计入硬件重叠。

不要为扩大审计数量而添加无关测试。优先保留可复现的代码、输入哈希、命令、状态、关键 trace、完整输出、周期分解和原始时序报告。状态说明必须区分实现错误、工具错误、容量失败、时序失败、性能失败和未验证。

## 3. 阶段 A：建立能与 RTL 对齐的新服务契约

先读以下实际代码和证据：

    docs/lookahead_fpga_enum_commit.md
    accel/lookahead/fpga_enum_commit/model/README.md
    accel/lookahead/fpga_enum_commit/model/configuration_final.json
    accel/lookahead/fpga_enum_commit/model/finite.hpp
    accel/lookahead/fpga_enum_commit/front/frontend_group.sv
    accel/lookahead/fpga_enum_commit/integration/README.md
    accel/lookahead/fpga_enum_commit/canonical/MODEL_AUDIT.md
    accel/lookahead/fpga_decoupled_front/graph.hpp
    accel/lookahead/include/workload.hpp

MODEL_AUDIT 前部是历史 A 的问题，后续已有修复记录。不要把 held publication、PV capture、同沿复用等已修复问题再次报成 final D 缺陷。

### 3.1 写 service_contract.json

至少明确：

- 每个组、每个服务每周期的请求生成、入队、发出、返回接收、状态写回数量；
- 每级 FIFO/holding register 的深度、真实占用、预留以及反压；
- 物理端口数量、32B beat、credit/tag 数量和归还时刻；
- 从入队到物理 issue、从物理返回到用户消费的寄存级数；
- ROW 跨 beat 时的两次读取；
- header/descriptor 与 EDGE 是否使用独立状态 RAM 和真实写口；
- 64 lane 到 64 accumulator bank 的有界候选路由；
- 目录 head/tail/member/free-list/min-selection 的同步 RAM、前递和每周期服务；
- enum、scratch、canonical、PV、publication、输出 ACK 的阶段边界；
- 同沿出队/入队、slot/word/tag 重用的精确定义。

新模型必须显式限制每组请求/返回宽度，不能只依赖全局 accepted_port 数组。

物理服务保持 32 个共享端口，每端口 32 credits，每周期最多一笔物理 issue；新增 DESC/EDGE 通道是逻辑来源，不增加外存端口或带宽。统一选择并实现一种队列/tag/return 组织，使模型与 RTL 一致。不能混用 D 的全局 FIFO64/tag-at-enqueue 与局部 RTL 的每客户 FIFO4/physical-issue-tag 资格。

### 3.2 新对照 C0 不是历史 D 重新贴标签

建立 C0：保留旧表示、8×8 lane，加入真实的组请求/返回配额及新公共服务契约。

- C0 的性能需重新运行，不能直接填写旧 52M cycles。
- 历史 D 保留在表中，注明契约不同，不把修正产生的周期差称架构加速。
- 对尚无 RTL 的目录，先实现有限同步服务，说明每个 RAM 访问和 forwarding。用有反压的小闭环验证后再让它承担资格；不能添加一个未经实现的任意固定延迟后称完整校准。
- C0 和后续候选共享同一目录、物理内存和输出契约，除明确的实验变量外不变。

现有 8 组单 EDGE 口的必要预算也应复算。EDGE 请求数分别为 209,255,671/215,954,269；仅该服务的界为 ceil(EDGE/8) 个周期。与初始化、final canonical 相加前，核对它们确实是不能重叠的阶段。此界只约束该结构，不能套用到新 16 组或跨 sample 交错架构。

### 3.3 增加能解释实际关键等待的计数

输出按 sample、wave、group、bank、physical port 的统计：

- 有效候选、实际发出的各类请求、物理返回、最终退休；
- 每组 DESC/H/M/EDGE 口利用率和 request/return stall；
- H/D、fork、ready、E、beat slots 的占用时间分布；
- lane valid/emit/backpressure、候选路由、同 set/word 冲突；
- output bank 冲突、return HOL、credit 使用与目录/PUB 等待；
- expand scratch、final merge、commit/K8 占用及关键等待；
- 所有互斥阶段的 wall cycles，保证相加等于完整周期。

禁止直接累加不同 bank 的重试次数并除频率当耗时。一个周期可有多个服务同时停顿。使用两种互补证据：固定观察点的互斥归因，以及仅改变一个有限服务的实际对照。将 lane_block 等已有但未导出的计数真正写入结果。

## 4. 阶段 B1：精确描述符融合

### 4.1 先做全输入准入

检查全部现有支持输入，包括小图、BNN、LSTM：

- prepared node/edge 数和所有 row 边界；
- prepared 最大 degree；
- 每个 sample 的输出 cells 数及 valid cell 范围；
- 原始 eligible 图转换和 cost index 域；
- 新表示所有 sample 的实际字节数和设备地址区间。

prepared graph 的转换规则保持原样：过滤、遇到终止节点的 break 语义、edge 次序、cost index、父节点 pair 和全 pair 比较均不变。不能用新描述符顺便改 ALT 算法。

### 4.2 主格式：满足准入时使用 8B

精确 64-bit 描述符：

    bit  0..31 : edge_begin，uint32
    bit 32..47 : degree，uint16
    bit 48..62 : target_cell，15 bits
    bit     63 : target_valid

其中：

    target_valid = (node.type == IPIN && cell[sample,node] >= 0)

要求：

- 所有 degree <= 65535；
- cells <= 32768；有效 cell <= 32767；
- 使用至少 64-bit 中间加法检查 edge_begin + degree；
- 开始与结束位置均落在已支持的 prepared 32-bit offset 域内；
- invalid 时 cell bits 规范化为零，解码后不得参与 target 更新。

这是整数数据表示优化，不是 FP32 精度降低。FP32 whole-pair 运算、正数/+0 支持范围、RNE、错误处理和比较顺序都继承冻结契约。

每个 32B beat 存四条记录。没有实现有限 coalescer 时，一次请求只服务其对应的 parent；不能把另外三条自动视为免费命中。

### 4.3 精确 fallback：16B

若某图的 degree 无法使用 8B，整图选择：

    uint32 edge_begin
    uint32 edge_end
    int32  target_cell
    uint32 flags

每个 beat 两条。fallback 只处理 degree/packing 限制，不放宽 offset32、目标容量和其他硬件准入。保持正常输出一致；未支持图清楚返回容量/格式状态，不能截断。

BNN/LSTM 按现有 node 数各 40 sample 的原始描述符空间：

| 格式 | BNN | LSTM |
|---|---:|---:|
| 8B | 1,312,834,560 bytes | 1,333,351,680 bytes |
| 16B | 2,625,669,120 bytes | 2,666,703,360 bytes |

以上尚需加入 sample stride padding、其他数组和 backing。以实际转换结果重算总容量。地址计算使用足够宽度，特别是 16B 全 batch 超过 2 GiB 时，不能使用有符号 32-bit 字节 offset。

### 4.4 消费语义

沿用现有顺序：先预留有限 fork/token，再发起 POP 读取及 pending17/stale 判断；stale POP 归还预留 token，合法 POP 才读取一次 descriptor。返回后分为：

- 邻接分支：非零度才分配 E 并访问 edge；零度直接完成该分支。
- 目标分支：依原始 valid 条件更新 seen/whole-pair min/recorded，等待实际输出 bank 服务。

descriptor/token 必须保持到两个分支分别交接一次。不能丢失、重复、提前释放，也不能在背压下覆盖不可变 parent pair。

零出度 parent 占约 43.4%，但不能整体删除。零度 target、invalid target、重复 target、同输出 bank 冲突必须覆盖。

### 4.5 请求收益的正确口径

在冻结原生工作量下，每个合法 parent 从“一或两次 ROW + 一次 META”变成一次 DESC：

| 请求 | BNN | LSTM |
|---|---:|---:|
| 原 ROW+META | 231,550,884 | 235,574,370 |
| 新 DESC，无 cache 假设 | 102,918,965 | 104,730,480 |
| 少发 32B 请求 | 128,631,919 | 130,843,890 |

这是对应两类请求减少约 55.5%，不是总时间减少 55.5%。按旧完整交通量，它约占全部请求的 16.6%；依赖链变短可能另有收益，需要实测有限模型。

旧计数只用于准入预测。新执行必须重新生成所有请求、spill、scratch、峰值和输出，不从旧 trace 导入这些结果来获得性能。

## 5. 阶段 B2：固定算术资源，改变前端分组

主候选 F3：

| 资源/服务 | 规格 |
|---|---|
| 算术 lane | 总 64 |
| 组 | 16 组，每组 4 lane |
| E contexts | 每 lane 4，总 256 |
| EDGE beat slots | 每 lane 8，总 512 |
| 每 parent edge 在途 | D1，先不改变 |
| fork/token slots | 总 128，每组 8；不得隐含扩成 256 |
| 统一 descriptor slots | 总 128，每组 8 |
| ready 总容量 | 128，按组分配并实际实现 |
| POP/token 新 admission | 全局最多 8/cycle；仍受实际 canonical 完成和槽位约束 |
| 每组 EDGE 请求/返回 | 各最多 1/cycle |
| 每组 DESC 请求/返回 | 各最多 1/cycle，独立真实状态写路径 |
| 物理端口/credits | 32 ports，32 credits/port，所有流量共享 |
| 输出 | 仍 8 banks，每 bank 每周期最多一次 update |
| accumulator/enum/canonical | 初始保持 ccec 的容量、enum2、K8 协议 |

每组 DESC 与 EDGE 两路返回需要两套真实写路径。如果共用 RAM 或状态端口，加入仲裁，不准免费双写。

采用可综合、有限的分层 RR 请求/返回网络，游标只在真实成功握手后推进。写清各级 FIFO 和寄存层。每条逻辑请求最多消费一次 credit；请求被拒绝时保持 payload、tag、地址和 generation。不能用即时遍历所有客户的 C++ 顺序代替已声称实现的注册网络。

返回到组内后依 tag/generation 找到实际 slot；同 bank/同组写口冲突要反压或进入有限队列。新增流水带来的延迟和容量都计入模型。

### 5.1 四格对照

| 配置 | 节点表示 | 分组 | 总 lane | H/M 或 D 容量 |
|---|---|---|---:|---|
| C0 | 旧 ROW+META | 8×8 | 64 | H128、M128 |
| F1 | 融合 DESC | 8×8 | 64 | D128 |
| F2 | 旧 ROW+META | 16×4 | 64 | H128、M128，各组8 |
| F3 | 融合 DESC | 16×4 | 64 | D128，各组8 |

C0/F1 使用每组单 EDGE 口；F2/F3 用同样的单口 leaf，但增加组数。额外控制、FIFO、网络和实际面积如实计账。因此这里只称“固定总算术 lane 和 E/beat 容量”，不能事先称 FPGA 总资源完全相同。

四格共享全局 POP admission 上限、物理内存、输出、目录、后端协议和统一控制流水。ROW/META 的单组服务宽度也要明确，不能在 C0/F2 默许无限并发。

### 5.2 运行规模

先在小图完成完整输出验证。随后按旧工作量选择少量代表性完整 sample，至少包含：

- BNN sample 2、19 和包含已知短任务负例的 sample；
- LSTM sample 7、19；
- 大展开、大 final、稀疏尾部各一类。

若编号与实际 manifest 不一致，以 manifest 确认后记录替代；不得虚构路径。选择依据用旧工作量，在看到新性能之前固定。每个性能样本从真实初始化开始，不以理想 warm checkpoint 偷去 POP/目录/输出成本。

局部 native wave/投影可以用于 RTL 诊断，但不能替代完整 sample 或最终 40-sample batch。

四格初筛后，只将有依据的候选推进完整 batch。不得要求每个短样本都加速才允许继续；保留负例，关注声明范围内的完整 batch。

## 6. 阶段 C：时序修复与局部闭环

### 6.1 前端至少有两条独立的已知关键路径

旧 front：

- pos 到 slot_state：WNS -1.036 ns，18 级、6 CARRY8，布线占主要部分；
- 实际 FP32 到 sticky error：约 -1.018 ns，30 级、9 CARRY8。

修一个比较器并不等于修好整个前端。建议实现：

1. 在已验证的 offset32 域内使用合适宽度；beat 编号可由 offset 确认其宽度，禁止未检查截断。
2. 每 context 预计算 last-edge/last-beat，避免大动态选择、加法、边界比较和跨组 slot 释放串成一条路径。
3. 有限可反压 operand bundle，携带 dst、parent、cost、context/slot、generation、last 标志。
4. 局部 one-hot 或分级状态更新，避免大动态数组写回。
5. 将实际 FP32 add 分成可综合、弹性的 align/sticky、add/normalize、round/pack 等阶段；确保既定数值域逐位一致。
6. error/legality 随事务传播，检查实际寄存结果；不得删掉错误检测或给内部真实路径设置 false path。

FP32 改动需针对舍入、规格化/非规格化边界、carry、+0 和既定异常域做有意义的定向差分，再用真实输入覆盖；测试的目的是保护数值契约，不追求无关测试数量。

新增级数会影响 token 生命周期、E/beat 释放和排空。模型同步加入，不能仍沿用旧 pair latency=2。

### 6.2 后端 hold 用真实接口 context 解决

旧 backend D：

- setup +0.024 ns；
- hold -0.135 ns；
- 669 条失败均在 INPUT_INTERFACE；
- 最差 op_arg 到内部 RAM 直接路径的数据延迟为零。

不能仅把 input min 从 0.100 ns 调大到能过线，不能把降频当作同沿 hold 的解决方案。

制作可综合的小型真实父级 context：输入有真实 launch registers，输出有真实 capture registers 和握手消费者，请求/返回/目录路径都有负载及反压。register slice 的容量、延迟和 backpressure 加入模型。将原接口失败与 context 实现结果分别保留。

若按具体真实接口采用新的约束，必须给出 launch/capture 依据。所有真实内部路径均受检查，不隐藏最差路径。修 hold 后重查 setup、hold、pulse、约束覆盖与实际 RAM inference。已有 aggressive hold fix 的失败记录保留，不把同一命令重复描述成新架构。

### 6.3 校准范围

小闭环需要覆盖：

- descriptor decode、两分支一次性交接、零度目标；
- 组请求/返回带宽、pipeline、credit、tag/generation、反压；
- group/port collision、return HOL、乱序响应和有限 FIFO 排空；
- 实际 FP32 候选到 accumulator；
- canonical whole-word lock、PV、目录实际接受、完成退休；
- 真实 directory RAM 同 bucket head/tail、free-list 和 min-selection 的同步行为；
- 输出 bank 冲突和 ACK。

记录 accepted request、physical issue/return、候选、目录事件和最终退休。优先在小规模几何下做到逐事件/逐周期一致，然后扩大拓扑。不能把 enum 的 258 个匹配事件写成整个新核已校准。

## 7. 阶段 D：完整 batch 与一个有依据的补充候选

### 7.1 完整执行

在修正后的公共契约下，至少完成 C0 和最佳主候选各自的 BNN40/LSTM40：

- 输入来自真实 native，运行实际算法全部波次；
- 不以冻结 parent、candidate 或 spill trace 驱动性能路径；
- 每 sample 的初始化、cost load、目录/bitmap/输出状态清理计费；
- 实际候选、replacement、spill、scratch RMW、全部目录事件；
- target 完成条件和必要 drain；
- 输出写入 backing 并完成所有 ACK；
- 完整 pair/output 与冻结 golden 比较。

若已经核验的 C0 source-bound 完整结果存在，直接复用。每个 sample 是可复现 checkpoint；失败重跑写新 attempt，不覆盖历史。

初始一活跃 sample 模式仍按 sample 顺序相加，CPU 模拟进程并发不能抵扣 FPGA 周期。

### 7.2 不自动增加 K 或 scratch 数量

如果 F3 仍慢，先重新计算完整阶段预算及关键等待。只允许选择一个额外低成本有限候选：

- 仅在关键 wall-cycle 确实持续受 K8 满载限制、物理口/目录/PUB 不是主阻塞时，测试 K16；
- 仅在 final merge 单在途依赖确实位于关键等待时，测试 merge2；
- 若缺口主要来自展开与 finalize 必须串行的阶段关系，并且 F3 的展开本身已明显下降，才测试下一节的双 sample 交错。

K16 不是改一个常数：原 RTL 数组、循环和 tag 位宽硬编码 K8。merge2 也必须有两个真实 slot、generation、返回路由和有限 shared FIFO。若采用 merge2 对照，仅增加 finalize merge 槽位；expand scratch 仍保持一个在途，避免同时改变两个变量。模型不得获得额外物理带宽；没有上述因果证据不启动这些 RTL。

不要求任意 1.2 倍或固定 20% 优势才继续，也不因单个小图变慢而否决大图候选。对差距很小的结果，报告模型误差和条件，不把它写成已确认优势。

### 7.3 条件候选：两个真实 sample 的阶段交错

这是利用原生完整 batch 中已有的 40 个独立 sample，不复制同一任务凑吞吐。每个 sample 自己的 wave barrier、版本、early-stop 和输出语义不变。

允许的结构：

- 一套总 64 lane 展开服务处理 A 的波次；
- 在资源允许时，另一真实 sample B 的 finalize/目录退休并行推进；
- 仍共享 64-bank canonical 服务、总 K8/subbank、每 bank 一个 PV read/write 服务、32 物理端口和 credits；
- 每个 slot 的前一 sample 全部输出 ACK 后才能初始化下一 sample；
- 所有地址、锁、tag、generation、目录、token、输出和完成计数具有真实 job 身份；
- sample 初始化不能用全局 sample_clear 清掉另一个活跃 sample。

不得使用 max(旧 expand, 旧 finalize) 直接生成新时间。必须实际运行共享资源的有限模型，产生新的 spill、访问序列、竞争和 makespan。新 batch 时间是所有 40 个原生 sample 真正完成的全局时间。

#### 资源先验证，不能按逻辑 bit 数假装容量减半

目标器件以现有工程为准：xcu280-fsvh2892-2L-e；当前报告给出 960 URAM、2016 BRAM36 可用。

现两个 subbank backend 用 16 URAM。简单复制全 64-bank 两套约需 1024 URAM，已超过 960，且还没有完整目录/路由。

即使每 job accumulator 从 1024 sets 减到 512 sets，独立的 2048×64 payload 数组仍可能各占一个 URAM，不能因此自动宣称总计降为 768。

如果尝试约 768 URAM 的布局，必须：

- 两个 job 的 payload 显式打包到同一组 4096×64 RAM，地址含 job slot；
- 分别维护两套 PV；
- 对 expand read、expand write、另一个 job enum read 的三类访问，按真实双口 RAM 仲裁或时分；
- 不同时继承两个独立数组的 II；
- 重新生成每 job 半容量导致的 spill、bitmap、ID 和 FIFO 峰值；
- 另计目录、输出、控制、时钟和路由资源。

目录可以有界共享原 8192 members/subbank 池，同时分开 job head/tail；旧单 sample 峰值 3495/3531 提供画像依据，但不能直接证明新调度一定不溢出。必须重新检查动态容量和无死锁回压。

先做上述关键 RAM/接口的实际综合推断与有限模型。容量/端口不成立时停止这一交错配置，保留 F3 和负结果；不能以缺少板卡为理由停止，也不能把它说成 FPGA 总体不可行。

若进入交错实验，固定三个对照：一活跃 sample/1024 sets；一活跃 sample/512 sets；两活跃 sample/各512 sets。第二、第三组采用同一总服务能力和实际打包 RAM，区分减容量损失与交错收益。共享 member pool 的分配/释放必须加真实端口仲裁，不能同一 free-list 同拍免费被两个 job 修改。其他 scratch、enum、目录和输出服务也不能随状态复制而自动翻倍。

## 8. 何时推进完整核

按每个声明案例分别判断：

1. 功能和动态容量正确；
2. 基于真实服务宽度、有限资源及新 pipeline 的完整 batch 结果具有可解释的收益；
3. 若目标是宣称优于软件，至少一个目标案例在同口径下有胜出的预测依据，或仅剩一个已有具体实现依据的缺口；
4. 候选所依赖的局部时序、RAM inference 和关键接口已获得证据。

满足条件后，完成包含 descriptor、POP、目录、前端、真实 FP32、路由、accumulator、scratch、canonical、输出及 reset/drain 的完整小图 top。不能以绕过模块的 synthetic driver 替代完整核，也不能凭 leaf 频率宣称完整 top 频率。

先 RTL 完整小图校准，再实现实际最终资源配置的完整核 OOC。若一个案例过线而另一个失败，保留并推进有资格的案例，同时明确负例；不得强迫所有案例同时胜出才允许任何硬件验证。

若完整候选本身明确慢于目标，且没有本轮允许的有限补充改动能缩小缺口，归档当前候选、输出原因与下一研究问题，不无限扫描 context/频率/容量。常规编译或协议 bug 应修复重跑，不能当作 no-go。

## 9. 无开发板情况下的有效结果口径

允许以下论文证据链：

- 真实输出验证；
- RTL/cycle-model 在明确范围内校准；
- 完整核对应配置 OOC 的实际资源与 setup/hold/pulse；
- 明确内存服务假设的完整大图架构模拟；
- 与实测软件在相同 resident complete-batch 边界的比较；
- 另列转换、传输与 E2 敏感性。

没有板卡不妨碍做上述研究。也不能把它写成实板性能。

结果字段至少分开：

    conditional_cycles
    conditional_frequency_hz
    conditional_seconds
    memory_contract
    rtl_calibration_scope
    complete_kernel_clock_qualified
    estimated_seconds_at_qualified_clock
    board_measured
    board_measured_seconds

未获得相应资格的字段保持 null/false。即使完整核时序通过，只要外存服务是建模假设，仍须称架构模拟/估计结果。

内存初始契约为 80 ns 延迟、5 ns issue 间隔时，频率变化要重新映射到周期和实际流水。不能把 200 MHz 的整份周期数直接除以 250/125 MHz：

- 同时钟保守离散模型应使用不提前返回的时间换算；
- 若要使用异步内存时钟/非整数 issue cadence，必须实现 CDC/队列并计费；
- 不使用旧频率给新时序失败核填 FPGA 秒数；
- 不用 WNS 简单倒数当可实现频率。

内存敏感性选择少数有意义的服务点，服务变化重新运行有限模型；不需要大规模盲扫。所有配置注明仅为建模假设或已有证据支持，不能编造实测带宽。

## 10. 软件基线、表示成本与 native 闭环

### 10.1 复用冻结强 CUDA

固定比较目标：

- BNN：0.151799969444 s；
- LSTM：0.15949799988888888 s；
- 边界：RESIDENT_COMPLETE_BATCH_V2。

报告保留其硬件、输入、算法、预处理状态、统计量定义和源绑定。均值与中位数不得无说明混用；独立进程与进程内重复不得当成同一级独立样本。

正式 CPU/GPU 计时应避免同节点竞争性模型/Vivado 作业干扰，记录线程数、亲和性、预热与正式重复。模拟多进程和资源综合可以并行，但不能污染作为软件基线的实测运行。

### 10.2 新布局也给软件公平使用机会

先实现同语义 packed descriptor CPU 参考，测构造成本、功能与完整 batch；不要强制软件回退至笨重的旧表示。

当 F3 或补充候选真正缩小目标缺口/进入完整核阶段时，补一个正常的 descriptor CUDA 对照。允许沿用旧强 baseline 作为更强者；新表示没有更快也保留负结果。不能因为希望 FPGA 胜出而锁定较慢版本。

这不是重新开展无关 GPU 优化研究。只需避免把可直接共享的数据表示收益全写成硬件特有收益。

GPU 登录若到期，先完成不依赖 GPU 的转换、CPU、RTL和模型工作，单列唯一受阻项；不要重复开启旧 GPU 任务或把整项研究停在登录处。

### 10.3 保留两个清楚的范围

1. Resident complete batch：输入已在设备，包含本批必要初始化、全部 sample 运算、device memory 访问与输出 ACK；不含主机到设备首传和预先构造。
2. E2：新表示构造/缓存检查、必要传输、运行、结果回接；一次构造是否复用、复用次数与真实来源明确。
3. VPR Process 若已有测量单列，不能用 kernel/resident 提速代替整进程加速。

warm 不能偷去每 sample 的 PV/目录/输出清理、版本状态或输出 ACK。不能由“已有 40 sample”推导跨多次独立 build 的预处理免费摊销。

优化 CPU、原 VPR 多线程须从已有证据查找同范围结果；缺失时补测需要的 CPU 区间，而不是假设赢 CUDA就自动赢所有 CPU。与 STRICT/原 VPR 的算法差异和既有 QoR 资格继续明确：ALT 不宣称 STRICT 逐位等价。

新 packed 输出与现有 ALT 完整输出逐位一致后，将它通过原 native 回接链核对最终 wire-map 身份。若该路径和已有资格链完全相同，可用明确哈希/转换证明复用；否则补实际 native/QoR 检查，不重写 golden。

## 11. 最终交付与停止条件

应交付：

1. 一份自包含报告，先回答本轮实际改变了什么、收益在哪、资格还缺什么。
2. 描述符 ABI/准入/转换代码及独立软件解码参考。
3. 新 service_contract，C0/F1/F2/F3 的实际配置和资源变化。
4. 功能、容量、请求/ACK/退休守恒证据。
5. 少量代表性四格对照及完整 C0/获选候选 batch 结果。
6. 前后端真实 context 的 RTL/时序报告，完整核仅在实际完成时列为通过。
7. 如运行条件补充候选，单列其共享资源、变更前提和净收益。
8. 最强同口径软件对照、构造/E2 成本与 native 身份结果。
9. 最小可复现运行说明、源/输入/工具绑定、失败记录及归档索引。
10. git 提交、推送、远端完整 SHA 核对和实际活动进程状态。

不用为了通过审计把全部旧工程、无关日志和重复二进制重新归档。保留支撑本轮关键结论的完整原始证据，并核验归档内容。

结论只能是与证据对应的状态，例如：

- FUSION_FUNCTIONALLY_VERIFIED；
- FINITE_MODEL_GAIN_ONLY；
- LOCAL_RTL_TIMING_QUALIFIED；
- COMPLETE_KERNEL_SIMULATION_QUALIFIED；
- SIMULATED_ADVANTAGE_UNDER_STATED_MEMORY_CONTRACT；
- NO_GO_THIS_CONFIGURATION；
- BLOCKED_SPECIFIC_DEPENDENCY。

这些是建议状态名，可以按项目习惯实现。不能把“分支已推送”视为硬件成功，不能把“模型变快”视为已过完整核时序。

若有长任务仍在运行，说明具体 PID/job、源绑定、日志、监督方式和剩余工作；不要一边称整轮完成一边依赖未完成任务。已有运行不要重复启动。所有运行终态后完成归档和推送。

## 12. 固定证据入口

以下均为本次指导实际依据的仓库文件，不要求外部旧附件：

- [本轮报告](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/ccec3da64b4c5be643809c2bdda94145c4bb8187/docs/lookahead_fpga_enum_commit.md)
- [最终完整模型说明](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/ccec3da64b4c5be643809c2bdda94145c4bb8187/accel/lookahead/fpga_enum_commit/model/README.md)
- [最终模型配置](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/ccec3da64b4c5be643809c2bdda94145c4bb8187/accel/lookahead/fpga_enum_commit/model/configuration_final.json)
- [完整有限模型源码](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/ccec3da64b4c5be643809c2bdda94145c4bb8187/accel/lookahead/fpga_enum_commit/model/finite.hpp)
- [前端 leaf](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/ccec3da64b4c5be643809c2bdda94145c4bb8187/accel/lookahead/fpga_enum_commit/front/frontend_group.sv)
- [后端实际集成与时序范围](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/ccec3da64b4c5be643809c2bdda94145c4bb8187/accel/lookahead/fpga_enum_commit/integration/README.md)
- [prepared 图及地址定义](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/ccec3da64b4c5be643809c2bdda94145c4bb8187/accel/lookahead/fpga_decoupled_front/graph.hpp)

