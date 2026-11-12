# Codex 执行指导：SPARSE_STREAM_R2

## 0. 目标、基点与本轮决定

在 `GRYYYYYYY/3D_FPGA_Interconnects` 的固定提交 **`5651a34abb97939bee6402c5af585753ab07f64b`** 上继续 FPGA 加速研究。该提交所在分支为 `accel/lookahead-sparse-stream-r1-20261112`，它的基点是 `fe659f008fc58c913bb1c0232d9898caf79fd524`。**新工作从 5651a34 开始，复用 R1 已完成的 RTL、协议验证和归档，不退回 fe659f0 重做。**

最终目标保持为：在明确的同范围实验中，FPGA 优于基础 GPU、优化 CPU、原 VPR 多线程等基线；GPU 和 CPU 之间不要求排序。保留 compact CUDA 作为更强的参考。首先围绕完整 BNN/LSTM 的真实 40-sample batch 解决硬件瓶颈；保留小图结果，不把大图收益推广成所有输入均加速。

本轮主要实现：

1. **有效 POP 时在线 whole-pair cell 归约，仍在原桶闭合点判断结束，消除独立 closed 节点扫描。**
2. **真正可重叠的 owner 流水线、changed 事件服务及提交服务。**
3. **有快照/版本协议的 bucket 选择流水和分层控制。**
4. **数百万节点的有限外存状态路径、实际物理通道共享、完整 batch job/output 控制。**

这些修改改变旧 P3 必要界的前提。保留 R1 固定结构的 no-go，不把它延伸为整个 FPGA 研究 no-go。

无需实板即可继续 RTL、OOC、有限内存架构模拟。没有实板不构成停止条件。完整核 OOC 和模拟可以支撑明确标注条件的模拟性能研究，不能改称实板测量。`board_measured=false` 保持真实。

建议新分支：`accel/lookahead-sparse-stream-r2-20261112`。建立独立 worktree；若同名分支或目录已存在，先检查并安全续跑，不能覆盖用户修改。main、原稿、STRICT、旧 golden、历史证据、未跟踪指导文件保持不变。完成后按项目既有授权推送独立分支，不合并 main。

## 1. 已核对的 R1 事实：不需要重做的部分与需要改变的部分

固定证据入口：

- [R1 完整报告](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/5651a34abb97939bee6402c5af585753ab07f64b/docs/lookahead_fpga_sparse_stream.md)
- [R1 实现和运行说明](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/5651a34abb97939bee6402c5af585753ab07f64b/accel/lookahead/fpga_sparse_stream/README.md)
- `results/fpga_sparse_stream_20261112/evidence_snapshot/analysis.json`
- `results/fpga_sparse_stream_20261112/evidence_snapshot/physical_audit.json`
- `results/fpga_sparse_stream_20261112/evidence_snapshot/{bnn_export,lstm_s2}/waves.csv.gz`

| 项目 | R1 已有证据 | R2 的处理 |
|---|---|---|
| 8-lane 小图 RTL | 完整输出、有限队列、容量、驱逐与 ACK；18 组校准一致 | 保留原证据；只对修改路径重新校准 |
| 大图功能 | BNN/LSTM 各 40 sample 与 ALT 输出一致 | 复用输入和 golden；新输出变换再次做完整差分 |
| GPU | V2 resident 完整 batch 基线已测，登录阻塞已解除 | 复用对应版本；新表示/通用变换补软件对照 |
| Owner | 单个当前请求上下文；多个 MSHR 隐藏 miss，但 hit 数据路径仍串行 | 分离各流水级上下文，测真实退休吞吐 |
| Commit | 16 个返回上下文，但后续 metadata/append 共用 FSM | 分离读请求并发和实际提交吞吐 |
| Closure | 全部 closed 节点进入中心 FSM，再过滤 type/cell | 实现本文精确 POP 归约，删除独立扫描 |
| 初始化 | 每个 proposal line 发写后等待 ACK | 改成有界多笔写入及最后统一 ACK 栅栏 |
| 物理实现 | 8-lane 路由完成，200/125 MHz 都未闭合 | 修复已定位结构，再重新实现；不从负 slack 推算已支持频率 |
| 容量 | RTL 4096 节点、每 sample 64 cells | 落实大图状态 backing 与输出路径 |

在 60-cycle 受限内存配置中：

| 完整小图 batch | 总周期 | 初始化 | expansion+fence | commit | closure |
|---|---:|---:|---:|---:|---:|
| d3，8 jobs | 134,729 | 75,518 | 17,987 | 3,587 | 37,533 |
| d4，12 jobs | 406,588 | 113,208 | 60,033 | 13,345 | 219,764 |

这些周期是现有小图 RTL 的结果；不是大图 FPGA 秒数。尤其 d4，初始化和 closure 合计占约 81.9%。不应只盯着边运算数量或瞬时发射峰值。

## 2. 第一项实现：在有效 POP 时归约输出，取消 closed 扫描

### 2.1 当前语义与证明范围

阅读：

- `accel/lookahead/fpga_sparse_stream/reference.cpp`
- `accel/lookahead/round6_1/bucket61.hpp`
- `accel/lookahead/include/workload.hpp`

当前 `closed/in_closed` 只用于桶结束时归约目标 cell 和清理去重标记；不参与边松弛、禁止节点重入或选择下一桶。有效 POP 已经能提供 `node` 和该 wave 的 `label` 快照。

证明仅适用于现有 ALT 的合法数值域、whole-pair 顺序、单调 bucket key、原 wave 栅栏和相同目标 cell 定义。**不改变 ALT 相对 STRICT 的语义边界，不宣称 STRICT 等价。**

合法 numeric 域沿用当前实现：正的有限正规 FP32 或 +0；不默许负零、NaN、无穷、非正规数进入候选运算。内部 INF 和最终 missing 编码按原契约处理。

### 2.2 等价性依据

设节点 u 在桶 b 被有效 POP。此时其 delay key 为 b，pending 被清空。若此后标签再次发生 whole-pair 严格改善，新 delay 不大于原 delay，因此新 key 不大于 b；现有 `NONMONOTONE` 检查又要求新 key 不小于 b。于是新 key 仍为 b。

这次改善会重新插入桶 b，或合并到已经存在的 b pending 项。桶 b 闭合之前，该节点必定再次被处理，最后一次有效 POP 会观察到桶闭合时的最终标签。标签只会改善，所以对该节点所有有效 POP 快照取 whole-pair min，等于原 closed 扫描读取的最终标签；再对同 cell 的节点做 min，输出相同。

此变换只调整已计算标签的归约时机，**不重排 FP32 路径加法**。

必须在代码和测试中验证这些条件，不能仅把本文证明当作已经通过 native/RTL 验证的结果。

### 2.3 首选实现：内部 output 在线更新，完成判定留在原闭包点

建议新增独立候选路径，保留 R1 原实现作对照：

```text
每个有效 POP（通过原 pending/version 检查后）：
    parent := 本 wave 的 label[u]
    可靠地产生 (qid, bucket_epoch, u, parent) 事件
    正常展开 u 的全部 eligible 边，仍只修改 proposal

目标事件处理：
    读取运行时 node.type 和 cell[qid][u]
    若 type == 1 且 cell >= 0：
        对内部 output[cell] 做完整 pair 的 min
        第一次由 missing 变为有效时，首次计数增加一次

每个 wave：
    保留原 proposal fence / changed commit / pending 发布栅栏

桶 b 闭合时：
    等待所有属于 b 的 metadata、归约事件和写回完成
    在原来的位置检查 recorded == targets
    否则选择下一桶
```

输出寄存数组不被搜索松弛读取，因此可以在内部提前更新。外部只在完整调用成功后发布 map；错误路径丢弃整个结果。这样不需要新增“每桶清一次全 cell 数组”或“每桶扫描全部 cells”的隐性工作。

若实现选择 per-bucket accumulator + dirty-cell publish，也可以，但必须计入额外数组、dirty-list、清理和发布周期；不可假定这些工作免费。

### 2.4 具体硬件要求

1. 有效 POP 的事件必须由 POP 产生，不能由第一条 edge 发射产生；零出度目标也必须归约。stale POP 不得发事件。
2. 不能只取第一次 POP，必须观察每次有效 POP，包括仅 congestion 改善之后的再次处理。
3. parent 发往 edge 前端和 cell 归约两路时，使用原子 credit 预约或分别记录两路已接收状态；任一路背压不得造成重复或丢失。
4. metadata 请求使用带 qid/epoch/node/pair 的有限上下文，允许返回乱序；pair 必须来自 POP 快照，不在返回时重新读取已改变的 label。
5. 每 qid 的 output 按 cell bank 化；从 8 个 reducer bank 起，实际数量按冲突和资源调整。每 bank 使用同步 RAM、有限输入 FIFO、同 cell forwarding/scoreboard。
6. whole-pair 比较保留 delay 优先、congestion 次优先。只在已验证 numeric 域内，才可用正确打包后的 64-bit 无符号比较。最终 missing 用 valid/seen 单独管理。
7. first-visit 计数与 output 更新必须原子化。建议各 reducer bank 维护本地计数，桶闭合且完全 drain 后用注册归约树汇总，避免每次事件更新高扇出全局计数器。
8. 保留原 wave 栅栏。下一桶开始和 `done` 前，必须排空 POP 分支、metadata 返回、reducer FIFO、RAW 重放及输出写 ACK。
9. qid/epoch 变化、epoch wrap、错误恢复必须有明确协议。不要用固定等待若干周期替代 drain 条件。

BNN/LSTM 每 qid cell 数为 25,088/25,538：64-bit 累计值分别约 200,704/204,304 B，seen 位约 3,136/3,193 B，另计 bank 对齐和控制。先用 Q=1 串行执行原生 40 个 sample，动态状态可复用；不要为了吞吐伪造额外 batch，也不需要立刻并发 40 份大图状态。

### 2.5 必要验证

随本指导附带 `semantic_validation/validate_pop_reduce.py`：10 个定向图、80 个固定种子随机图、shift0/20，共 180 项小型模型差分通过，四个错误变体被识别。其局限明确记录在 `results.json`：共享搜索控制、未覆盖 VPR eligibility、完整 native 图、有限硬件队列、溢出和真实访存。**它是新方向的快速语义检查，不能替代服务器上的 C++/native/RTL 验证。**

实现 C++ 新版本后，比较每桶闭合时的输出、recorded、每 wave active/changed/commit 及最终输出，覆盖现有真实小图和 BNN/LSTM 各 40 sample。针对性 fixtures 至少包括：

- 同桶重复 delay 改善、同 delay 的 congestion 改善。
- 零出度目标、source 为目标、targets=0、不可达目标与 missing 编码。
- 同 cell 不同 pair、同周期首次写入、连续同 cell RAW。
- pending 已存在且 key 不变、bucket migration 的 stale 项。
- 最后一个目标在桶中途出现，随后同桶仍有改善，禁止过早结束。
- metadata 乱序、随机背压、跨 qid 缓存残留、容量恰满和溢出。

若某输入违反证明前提，归档反例并在该输入上拒绝/回退，不能修改 golden 掩盖差异。退路是保留原闭合语义，先做 target-only closed 登记加多笔 metadata 请求的流水 closure；这也是独立候选，不要结束全部 FPGA 工作。

## 3. 第二项实现：owner、changed 和 commit 真正流水化

### 3.1 Owner

`rtl/owner_sync.sv` 当前只有一组当前请求状态，普通 hit 经过 `IDLE/TAG/READ/APPLY`，更新后还要等待 EVENT。32 个 MSHR 不等于多个 hit 更新同时推进。

实现每级独立 valid/ready 和请求载荷的弹性流水：

- 解码、tag/MSHR 查找、资源预约。
- 同步 cache RAM 读取。
- whole-pair 比较、旁路、写回或 miss 合并。
- changed 事件进入独立有限 FIFO。

处理同 line/set/way 的 RAW/WAW、MSHR 同行合并、miss fill 与普通 hit 的端口竞争、dirty victim 和 writeback 槽位的原子预约。更新被接受前，必须能可靠保留对应 changed 事件，不能 RAM 已更新而事件丢失。

目标是互不冲突的 hit 流达到每周期启动/退休一项的可验证稳态服务；有冲突时允许背压。**流水深度、FIFO 入队率、MSHR 返回一次退休多项、普通请求持续退休率要分开报告。**

给出独立 hit、同 line 热点、同 set 不同 tag、工作集超过 cache、fill/eviction/ACK 混合、fence 边界等有针对性的 RTL 计数。测量最小、稳态平均和真实 trace 加权服务率，不能只报告某周期的峰值。

### 3.2 Changed 事件

当前 changed queue 对一个 line 的四位 mask 串行处理，并有 busy 退出周期。Owner 改快后该服务可能立即反压。

在 owner 与去重服务之间设置有限事件 FIFO；再实现按 sector/node bank 的去重与入队资源预约，或可重叠的 mask 解包。必须保留：同 node 每 wave 至多一个 changed ID、跨 cache 驱逐不丢标记、容量不足无部分成功、commit ACK 清标记的正确时序。

单纯加深 FIFO 不算提高持续服务能力；服务率以退休和排空日志为证。

### 3.3 Commit 和 bucket append

16 个 read contexts 已经是 R1 的实际修复，不重复计为新贡献。读取返回后仍共用 `COMMIT/CMETA/CWRITE/APPEND/.../CACK`。

分离以下有界服务：proposal line 读、label/pending metadata RMW、成员分配、bucket tail 追加、pending 发布/ACK。不同节点可以重叠；同节点和同 bucket tail 通过 forwarding、scoreboard 或显式顺序保证正确。下一 wave 不得看到 label 已更新但成员/pending 尚未发布的半提交状态。

增加提交分支计数与退休间隔，区分“pending 已在同 key，无需 append”和“需要新成员”的成本。

真实 per-wave 统计中，BNN/LSTM changed node 总数约 104.21M/106.14M，而 changed line 总数约 51.97M/53.04M。可以研究每个 32B proposal line 只读一次并携带四个 sector 的 mask；它约有 2 倍的读事务合并空间，**不代表 node metadata 更新工作也减少 2 倍，更不是固定 4 倍收益**。

### 3.4 初始化

将逐 line 写后等 ACK 改成有限 outstanding 的顺序写流。每笔写记录 ID；只有本 sample 全部必要初始化写可见且 ACK 收齐，才发布 source 和开始搜索。初始化周期仍计入 resident complete batch。

lazy epoch 初始化可作为后续候选，但必须同时实现旧数据遮蔽、首读默认值、epoch wrap 和额外 metadata 成本。第一版优先用容易核对的多笔顺序写流，不用未经实现的 lazy reset 参数改善模型。

## 4. 并行推进：8-lane 时序结构修复

R1 最坏路径从 bank 的 `groups` 到顶层 command CE，约 11.930 ns、52 个逻辑层级，路由约占 62.1%。200 MHz WNS −7.035 ns；同路由 125 MHz WNS −4.035 ns；hold −0.048 ns。降频不能解决 hold。

### 4.1 有协议的 bucket 选择流水

优先在 commit 完成且目录稳定的边界选择 bucket：

1. 排空所有改变 bitmap/pending/member 的提交。
2. 冻结目录或记录 snapshot epoch。
3. 每 bank 用平衡树选择非空 group，并寄存。
4. 读取对应 bitmap word、编码局部最小 bucket，再寄存。
5. 分层、带寄存器的全局 min 归约。
6. 全部结果 valid 且 epoch 一致后发布下一次 POP command。

不得用保留线性优先链的组合 for-loop 仅包一层输出寄存器冒充已缩短内部路径。目录若仍可写，必须有快照或版本重试机制，不能读取旧 min。

若每 bank 编码器复制仍使资源过大，可改为分层 OR 所有 bank 的 64-bit group 向量，先确定全局 group；再收集该 group 的各 bank bitmap word，OR 后编码 bucket。它仍需要两轮有限握手与注册树，不能用无寄存长跨区线路完成。

### 4.2 控制树与 RAM

- 将全局 reset/command 分层注册分发，done/idle/fence 分层汇总。
- 配套 reset-complete、command-accepted、phase epoch；不能假设所有 leaf 在同一周期收到命令。
- 对 payload RAM 使用有效位/地址初始化，避免把大数组复位写成大量寄存器。
- 当前 output 的逻辑容量 4096×64b 并未按预期映射到 BRAM，顶层存在大量 LUTRAM。把计算期间更新与最终导出读分开，按 reducer bank 和实际双口 RAM 协议实现；仅写 `ram_style="block"` 不够。
- 使用真实输入/输出约束和注册接口修复 hold，保留 check_timing 与 DRC。不得删 I/O delay、添加无依据 false path 或 multicycle 掩盖问题。

先在修改后的完整 8-lane tile 做 routed OOC，得到一个真实通过 setup/hold 的频率及其范围。200 MHz 是设计目标，不是已有事实；125 MHz 不是默认安全值。一个频率失败后，依据路径修复或选择有效频率，不把“200 MHz 未过”自动解释为所有结构停止。

AMD UG949 对长组合路径流水、按层次复制高扇出控制及 RAM 输入/输出寄存给出官方指导，链接见文末。新延迟必须进入功能协议和周期模型。

## 5. 大图存储必须落到实际可执行路径

### 5.1 容量与资源事实

当前 8-bank RTL 节点容量为 4096；原样扩到 64 banks 也只有 32768。BNN/LSTM 有 4,102,608/4,166,724 个节点。BNN 仅 64-bit label 加 32-bit pending 就是 49,231,296 B，尚未计 proposal、versions/epochs、成员、目录、cache 等。

当前 8-lane routed top 为 243,739 LUT、184 BRAM tile。U280 对应器件报告中可用 LUT 为 1,303,680；原样复制八份需要 1,949,912 LUT，已超容量。**Full64 不能定义为八份原 tile 的直接复制。**

Q=1 的 cell accumulator 约 200 KB 可以单独规划；完整 40-sample 输出约 8.03/8.17 MB，使用外部输出缓冲和实际写 ACK，不把所有 sample 输出都强塞进当前 4096-pair 数组。

### 5.2 推荐的第一版状态组织

保持 Q=1 和原生 40 个 sample 顺序，先把大地址空间做真实：

| 状态 | 第一版建议 | 必须验证 |
|---|---|---|
| prepared CSR、cost、node type、qid-cell mapping | runtime 预加载到外部设备内存；cost 小表片上 | 地址宽度、eligible skip/break 保持、实际 read 事务 |
| label、proposal | 外存 backing，分别有明确 owner/cache 和 wave 可见性 | fence 后 proposal/label 一致、回写 ACK、无 alias |
| pending、version/epoch | 外存 node-state backing + 有限 bank cache | 随机 RMW、同 node 顺序、stale filter、回写可见性 |
| bucket head/tail/bitmap | 片上 bank 化，有限端口 | 同 bucket append、snapshot、空桶判定 |
| physical member pool/free-list | 按资源选择片上或外存，有限容量 | 分配回收、峰值热点、stale 成员实际占位 |
| changed ID/line masks、去重标记 | 有限 bank 队列 + 明确 backing/epoch | 跨驱逐去重、容量预约、commit ACK 清理 |
| cell min/seen | Q=1 片上 banked accumulator | 同 cell RAW、首次计数、RAM 推断 |
| 全 batch 输出 | 外部连续输出缓冲 | 每 sample 写出、最终 ACK 后 done |

允许把 label+pending+epoch 打包成同节点记录以减少随机 metadata 访问，但必须在字节账本和端口模型中计入对齐、读改写放大；不能直接借用小图全片上访问周期。保持 proposal 与 wave-start label 的逻辑隔离；不能把 proposal 的即时改善直接当作下一 parent 的 label。

落实可综合的 node-state 服务、初始化服务、有限缓存和通道请求接口，再做小容量同接口 RTL 校准；同时用实际大地址范围验证最高 node ID、跨 bank 访问、缓存容量外工作集及输出排列。外存大数组由 testbench/model 提供，硬件只实例化有限片上状态；不能把数百万节点的数组隐藏为综合不到的零延迟 C++ 容器。

统一参数化 node→owner→local index→line→physical channel 的映射。当前 `global_node`、init line 地址、changed queue base 有硬编码 8-bank 映射；必须做正反映射和无别名检查。

### 5.3 物理端口共享

R1 tile 模型使用 25 个服务：8 owner + 8 frontend + 8 init/commit + 1 cost/closure。每服务 64 outstanding、32B、最短两周期发射；它不是实测 HBM。复制八个 tile 不能获得 200 个独立物理服务。

目标模型采用明确的有限物理端口数（继续 U280 方向时可沿用 32 个逻辑化物理通道接口，但必须声明这是模型与接口假设），实现所有逻辑客户端到这些端口的共享：

- 每端口请求/返回队列、ID 名空间、outstanding 总量。
- 读写竞争、ACK、乱序返回、bank 热点、仲裁公平性。
- CSR、proposal、node-state、metadata、初始化和最终 output 的竞争。
- 分层互连和跨区域寄存器；避免默认全连大 crossbar 免费。

没有板端随机 RMW 实测时，继续做**明确参数化的有限内存模型及敏感性分析**，不再用“没有可用板卡/随机 RMW 实测”结束全部研究。结论必须写成该内存服务假设下的模拟性能；不把参数当实测。

时钟变化时明确 memory latency 用 ns 还是 kernel cycles，物理服务时钟是否独立及是否有 CDC；不能提高 kernel 频率后同时暗中减少固定物理延迟。当前 16/60/120 cycles 是 200 MHz 参考假设下 80/300/600 ns，若用于其他频率，换算规则必须公开。

## 6. 重新建立性能界：用于筛选，不是结果图中的 FPGA 性能

### 6.1 旧界为什么只否定固定结构

R1 旧式乐观必要界按 wave 累加：

```text
ceil(2 * candidates / 64)
+ 在 bucket 结束的 wave 上 ceil(3 * closed_nodes / 8)
```

结果 BNN/LSTM 为 78,748,700/80,129,990 cycles，即假设 200 MHz 下 0.3937435/0.40064995 s。它已经忽略初始化、commit、访存和大量控制成本，因此能否定固定 II2 owner + II3 closure 的扩张。

**这些值是下界，不是实际预测；不能说“实际只比 GPU 慢约 30%”。**

### 6.2 新结构的条件算术检查

随附 `audit_bounds.py` 从归档逐 wave CSV 重算。下表都假设 200 MHz；只有第一行是旧报告界。后续行明确指定假想服务：全局 parent 上限 8/cycle、commit 上限 16 changed nodes/cycle。它们不是已实现吞吐。

| 条件服务结构 | BNN 必要时间(s) | LSTM 必要时间(s) |
|---|---:|---:|
| 原报告旧界：64 owner II2 + 8 closure II3，不计 parent/commit | 0.393744 | 0.400650 |
| 64 owner II1、closure 仍 II3，计理想 parent/commit | 0.331867 | 0.337668 |
| 64 owner II1、8 closure II1，计理想 parent/commit | 0.203432 | 0.206980 |
| POP 在线归约，无独立 closed scan；32 owner II1，计理想 parent/commit | 0.237873 | 0.241942 |
| POP 在线归约，无独立 closed scan；64 owner II1，计理想 parent/commit | 0.139212 | 0.141633 |
| compact H100，真实 V2 resident 均值 | 0.304680 | 0.306053 |

无 closed scan 的公式为：

```text
sum_over_waves(
    max(ceil(edges / owner_rate), ceil(active / parent_rate))
    + ceil(changed_nodes / commit_rate)
)
```

它假设 cell 归约能与 parent/edge 处理重叠，且足够快。实际模型必须加入 reducer 有限服务、metadata、RAW、目录、初始化、共享内存和 drain。若 reducer 成为瓶颈，在重叠阶段加入其真实限制；不要继续把它设为零成本。

这些数只说明新结构值得实现，不能据此宣传 2.2× FPGA 加速。必要界小于 GPU 是继续筛选的必要条件之一，不是足够条件。

### 6.3 宽度选择

不先固定“必须 64 lanes”。在 edge 数不变时，16 个每周期一候选的引擎即使 200 MHz，BNN/LSTM 仅边工作分别约 0.402168/0.409223 s，已经慢于 compact GPU。在候选边工作量不变、每 lane 每周期至多处理一个候选且实现频率不超过 200 MHz 的条件下，不继续扩展这个 16-lane 候选。若新结构通过更高频率或减少了实际候选工作量，应重新计算必要界，不沿用本条 no-go。

若 8-lane 服务原型已形成真实 II1，优先评估 **32-owner + POP 归约** 的资源和完整模型；它在算术上尚未被排除、资源压力低于直接 full64。若完整服务模型表明 32 路不足，且实际资源支持，再扩 64；不能继续使用旧 FSM 的 II2 代替所需 II1。

64-owner II1 + POP 归约的上述算术界在 125 MHz 下约 0.222739/0.226613 s；32-owner II1 对应约 0.380597/0.387107 s。它说明频率和宽度必须一起选择，也说明“先闭合到 125 MHz”只是物理阶段成果，未必已具备性能余量。

每次 no-go 指明绑定项：工作量、服务上限、资源、容量、共享带宽、频率或语义。停止扩大该固定候选；有能够改变绑定项的具体实现时自动继续。不得把观测平均吞吐直接当作不可突破的硬上限，也不得把假想 II1 当已实现结果。

## 7. 执行次序与阶段交付

### M0：定位与建分支

核对本地/远端 SHA、未跟踪文件和已有进程；建立从 5651a34 出发的新 worktree。记录输入、golden、工具版本和 R1 证据路径。不要重新测已经完全相同的 GPU V2 数据，不创建新无关基线工程。

### M1：立即写出并跑通 POP 归约的软件版本

实现独立 C++ path，跑定向 fixtures、真实小图、BNN/LSTM 各 40 sample 的完整差分。补充实际统计：target-valid POP 数、每桶 unique target cells、重复更新、cell bank 分布、metadata line 工作集。保留每 wave 工作量相同的证明。

这一步与 bucket/control RTL 修复可并行，由不同文件负责人处理。不能只交付证明或继续写可行性账本而没有新代码。

### M2：8-lane 完整闭环 RTL

接入 POP 两路 fork、metadata 服务、banked reducer、完整 drain 和真实 batch controller；删除新路径中的 closed scan。实现初始化多 outstanding 和 bucket min/control 修复。跑原 d3/d4、压力用例及新语义/背压用例；与旧 F0/F1 保持可比较。

在这里完成新的 routed OOC。若最坏路径转移到 owner/commit，按新路径修复，保留每次失败。不要先花数小时实现旧 full64。

### M3：owner/changed/commit 独立流水与完整 tile 集成

先验证服务率和冲突行为，再接入完整 tile。所有跨模块 FIFO 和依赖都计入 cycle model。修改后的 model 必须重新对 RTL 校准；小图旧 18 项零误差仅属于 R1 配置。

优先测新的瓶颈，不做没有原因的大规模参数扫描。必要时用 changed-line 提交、bucket-tail forwarding、parent dequeue 流水解决后续瓶颈。每次改变结构都保留消融版本。

### M4：大图地址/状态服务 + 共享通道模型

实现第 5 节的实际路径，而不只写资源账本。小容量 RTL 使用相同外存接口、有限 cache、同地址宽度和冲突规则；大地址测试验证真实最大 node ID 和 qid-cell 范围。记录每类访问的读/写字节、cache hit/miss、最大 outstanding、队列峰值与停顿原因。

在已实现的服务合同上选择 32 或 64 路拓扑。先综合实际分层模块，确认资源和 RAM 映射，再做候选完整核 OOC。32/64 路不要求机械逐个全流程扫描。

### M5：完整大图逐周期/等价事件驱动架构仿真

通过前述资格后，运行完整 BNN/LSTM 各 40 sample；动态计算 frontier/proposal/commit，不从 golden 读取中间调度。允许在无事件区间精确跳周期以加快模型，但不能用统计采样取代完整依赖。

核查完整输出、容量、全部 ACK 和 batch done。用独立小图及热点/容量压力配置校准相关模块、共享通道和完整拓扑。给出校准范围和误差；增加 32/64 路后不能继续引用 8-lane 误差等于零作为全部规模校准。

秒数主列只使用对应完整加速核通过 OOC 的频率，并明确未含板卡 shell / 实板资格及内存服务假设。尚未通过的频率只出现在“假设/筛选”列。

### M6：软件对照、native 回接和论文证据

补 prepared CSR、POP 归约等通用变换的软件对照，至少优化 CPU 和基础/compact CUDA 对应路径；若原 CUDA 已有等价输出流优化，检查并复用。不得把软件也能获得的表示收益全部算成 FPGA 架构收益。

完成原 VPR 多线程、最佳 native STRICT/优化 CPU、ALT CPU、基础 CUDA 的明确同范围结果。无法映射到同算法 E1 的原 VPR 用 native lookahead E2/Process 表，不把不同输出语义或计时范围硬放进一个 speedup 分母。缺失项不阻止此前 RTL 研究，但限制最终结论。

新输出 byte-exact 等于已有合格 ALT 输出时，复用既有 QoR 证据并完成必要 native 身份/回接核验；只有输出或相关路径改变时才扩大 FULL/STA 重跑。仍明确 ALT 与 STRICT 的 congestion 差异历史。

## 8. 实验边界和消融

主边界继续为 `RESIDENT_COMPLETE_BATCH_V2`：一次真实调用、全部输入和 immutable metadata 预驻留，所有 mutable 初始化、cost preload、搜索、提交、归约、设备内部存储访问、sample 切换与完整输出写回完成均计入。CPU/GPU/FPGA 工作范围一致。Host 初次转换/装载、PCIe H2D/D2H 可独立列入 E2，不放入 resident 核心主表；不得把设备内部 HBM 访问排除。

每 sample 由真正有限 job controller 发起，不能由 host 在每个 sample 间免费初始化、装载 metadata 或读出结果。最终输出到设备缓冲后必要 ACK 才能 done；host readback单列但不能提前宣布设备输出完成。

最小消融保留：

- R1 冻结基线。
- 仅 bucket/control/接口时序修复。
- 加 POP 在线归约。
- 加 owner/changed/commit/初始化流水。
- 相同大图状态/通道下的 cache F0/F1 对照。

不必做所有开关的笛卡尔积；每次对照回答一个具体收益来源。小图周期比较和各自实现频率分别列出，需要相同时钟比较时用两者都真正支持的频率。

最终对模拟结果给出内存参数敏感性、队列/容量峰值、主要停顿组成。仿真 seed 变化反映模型中的调度变化，不称为板卡测量置信区间。CPU/GPU 真实测量继续保留独立进程和原始样本。

## 9. 持续执行规则：失败候选不等于结束研究

本指导替代旧 P3 被解释成“固定结构下界失败就结束全部 FPGA 工作”的执行方式，保留其拒绝无效规模扩张的作用。

1. 已有具体修复依据时，直接实施、验证并继续；无需用户每做完一轮再次授权。
2. 单个候选失败，写清绑定项，保留证据，推进能改变绑定项的下一实现。不要反复复制同一 FSM、增加空 context 或只扫假想频率。
3. 没有实板、GPU 暂时不可用、CPU 基线未补齐，只暂停依赖该资源的分支；RTL、OOC、功能和模型工作继续。
4. 计算资源、上下文或当前会话不足时，保存可恢复 checkpoint、确切下一条命令和未完成项；状态应为“待继续”，不能写“目标已完成”。
5. 不以固定轮数、任意工作时长或无依据的倍数阈值结束研究；也不要求无方向地无限搜索。若相关候选已实质验证且没有剩余可论证改进，明确目标未达成与约束即可。
6. 不用模型下界、缓存命中率、资源估算或测试数量代替 FPGA 性能结果。保留正负结果，不改 golden，不挑有利 batch，不更换计时边界隐藏设备内部成本。

## 10. 必须交付的文件与状态

建议新增路径：

```text
accel/lookahead/fpga_sparse_stream_r2/
  reference_pop_reduce.cpp
  rtl/                 # 新服务与完整 top
  sim/                 # 有限内存、RTL harness、周期模型、校准
  config/              # 容量、端口、数值、时钟与计时边界
  tests/               # 针对性语义/协议 fixtures
docs/lookahead_fpga_sparse_stream_r2.md
results/fpga_sparse_stream_r2_20261112/
  provenance.json
  semantics/
  rtl/
  timing/
  large_state/
  full_batch_model/
  baselines/
  failures/
  checkpoint.json
```

可以沿用项目已有组织习惯，但旧目录/归档不覆盖。路径清单是新建目标，不声称这些文件已经存在。

`checkpoint.json` 分别记录，不用单个 PASS 混合证据层级：

```json
{
  "base_sha": "5651a34abb97939bee6402c5af585753ab07f64b",
  "board_measured": false,
  "pop_reduce_native_exact": false,
  "complete_small_rtl_verified": false,
  "owner_retirement_service_verified": false,
  "large_node_state_path_implemented": false,
  "physical_channel_sharing_implemented": false,
  "complete_batch_controller_implemented": false,
  "tile_timing_closed": false,
  "whole_kernel_timing_closed": false,
  "whole_kernel_clock_mhz": null,
  "clock_qualification_scope": null,
  "large_complete_batch_model_verified": false,
  "model_calibration_scope": [],
  "software_baselines_complete": false,
  "fpga_simulated_superiority_supported": false,
  "candidate_status": "in_progress",
  "next_action": "implement and validate POP-time cell reduction"
}
```

完成证据后逐项更新；数值、版本、配置、输出 hash、报告、命令、失败原因能追溯到同一实现。停止某个失败候选时 `candidate_status` 可标 no-go，并写绑定项及下一候选；不能借此把最终目标置为完成。

## 11. 官方实现参考

这些是实现方法参考，不是本项目频率或性能的证明：

- AMD UG949 2022.2，[Replicate High Fanout Net Drivers](https://docs.amd.com/r/2022.2-English/ug949-vivado-design-methodology/Replicate-High-Fanout-Net-Drivers)：按层次形成均衡控制树，避免不加区分的全局复制。
- AMD UG949 2022.2，[Pipelining Considerations](https://docs.amd.com/r/2022.2-English/ug949-vivado-design-methodology/Pipelining-Considerations?contentId=ZklDykL_UkjQUvNnRC4hxw)：分解长组合路径，并让控制协议反映新增延迟。
- AMD UG949 2022.2，[Performance Considerations When Implementing RAM](https://docs.amd.com/r/2022.2-English/ug949-vivado-design-methodology/Performance-Considerations-When-Implementing-RAM?contentId=xWA4jpEga87YF~xtJ_b6Lw)：同步 RAM 的输入/输出寄存、RAM 映射和地址控制路径。

## 12. 可直接给 Codex 的启动指令

请完整读取并执行本文件。从 5651a34abb97939bee6402c5af585753ab07f64b 建立独立 R2 worktree，保留 R1、main、原稿、STRICT、旧 golden 和指导文件。首先实现并验证“有效 POP 在线 whole-pair cell 归约、原桶闭合点结束”的精确变换，同时修复 bucket 选择流水和分层控制；随后实现真实 owner/changed/commit 服务、大图状态 backing、共享通道与完整 batch 控制。复用现有 GPU V2 证据，用修改后真实 RTL 服务重新校准，选择资源可行的 32/64 路结构继续完整模型和核 OOC。旧 P3 只停止旧固定候选的直接扩张；新结构有依据时自主继续，不以没有实板或完成一轮文档作为结束原因。报告中严格区分功能、RTL、OOC、模型、假设频率与实测；目标尚未证明时保留 false。请执行代码和验证，不只输出分析计划。
