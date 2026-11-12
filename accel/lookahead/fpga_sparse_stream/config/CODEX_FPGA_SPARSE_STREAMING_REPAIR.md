# FPGA 下一轮：稀疏调度、并发供数与同步存储实现

日期：2026-11-12。直接交给服务器 Codex 执行。

本任务基于 fe659f008fc58c913bb1c0232d9898caf79fd524 的实际代码与证据。它取代上一轮将缓存作为首要优化对象的执行顺序，不覆盖历史结论。本包只有代码审阅、既有证据的派生计算及下一轮设计指导，没有运行新 FPGA 性能实验。

## 0. 本轮目的与授权

继续无实板 FPGA 方法研究，目标仍为争取超过基础 GPU、优化 CPU、原 VPR 多线程等匹配基线；GPU 与 CPU 不要求排序。保留 compact CUDA 这一已测强参考，不能为了得到优势删掉它。

没有板卡、XRT 设备或完整平台不是 RTL/OOC 启动门槛。允许独立 RTL、HLS、有限存储模型、Verilator/XSim、模块实现与经 RTL 校准的架构仿真。保持 board_measured=false。

这次主要任务是把全图扫描、逐请求阻塞和一条共享候选总线替换成有界的稀疏并行执行路径，并把大数据阵列改为同步存储流水。不得只增加 owner/cache/context 数，也不得只对旧核降频或重跑布局布线。

先交付新的完整小图 RTL 原型，不以“尚未证明大图必胜”为开始实现的条件。完成后按实际吞吐、流量和时序决定是否扩展；不把目标加速比写成结果。

### 基点与保护

- 源码基点：fe659f008fc58c913bb1c0232d9898caf79fd524。
- 新分支建议：accel/lookahead-sparse-stream-r1-20261112。
- 建立独立 worktree；新代码放 accel/lookahead/fpga_sparse_stream/。
- 不修改 main、STRICT、旧 golden、已整合稿、历史证据及未跟踪指导文档。
- 本次可新增必要的 CPU/GPU 表示消融与计时；不重复已经完成的 GPU 授权和 96 次同范围测量。
- 通过技术阶段后自主继续，不逐阶段询问用户。只管理本任务作业，不终止别人的实验。

## 1. 已经核实的失败原因

### 1.1 数量级

| 指标 | BNN | LSTM |
|---|---:|---:|
| 旧 F1 完整周期 | 3,011,527,924,278 | 3,108,929,429,228 |
| cycles / 假设 200 MHz | 15,057.6396 s | 15,544.6471 s |
| 新 compact CUDA resident 均值 | 0.304680242 s | 0.306053250 s |
| 旧预测 / CUDA | 约 49,421 | 约 50,791 |

旧 FPGA 的 200 MHz 未通过实现，因此这一比值是诊断性的条件比较，不能写成板测慢多少倍。

### 1.2 真实串行点

graph_control.sv 只有一个 IO_SEND→IO_WAIT 阻塞请求。每条边还串行读取 edge、destination node 和 cost；graph_top.sv 的 64 个真实 FP32 lane 共用一个候选输出总线，每周期全核最多传一个候选。

MIN、ACTIVE、COMMIT、CLOSE 都扫描全部 N 个节点。其中 BNN 的 MIN、COMMIT、CLOSE 占总周期约 70.795%，ACTIVE 阶段另外还含一次全图扫描。

BNN 实际候选为 1,286,937,147；即使完全消除内存延迟，单候选/周期 @200MHz 也至少需 6.4347 s。这不是调 cache 参数可以补救的瓶颈。

### 1.3 流量与并发

BNN F1 总流量为 1,496,253,264,672 B；旧中央模型有效总带宽为 102.4 GB/s，理想字节量下界仍为 14.612 s。每个 4B/8B 标量经常重新读取一整条 32B 行，未复用同一行其它字段。

缓存命中率 85.45%，全 batch 周期减少仅 0.016375%；每 owner MSHR 高水位 1，同地址在途合并为 0（旧模型调度域下的派生计数），front backpressure=0。说明完整任务没有激活设计所依赖的并发合并机制。

BNN/LSTM 代价表各只有 80B，即 10 个 FP32 pair；旧实现却为每个候选发起一次 blocking COST 外存请求。把运行时表一次加载到片上是本轮必做项，不是新的缓存参数搜索。

### 1.4 物理实现

旧全核有 767,925 LUT、295,808 LUTRAM、159,828 FF，BRAM/URAM 均为 0。最差内部路径为 request FIFO 读指针到 dirty 状态，13.299 ns，其中 route 11.103 ns、约 83.49%。SLR0/1 CLBM 占用 91.42%/97.65%。

125 MHz 的 -5.417 ns 是同一最终 route 的回退检查，不是已经完成另一套低频优化。不能据此推导“74.5 MHz 已经可用”。缺少寄存器切分、异步大数组读和宽扇出需要结构修改。

## 2. 只做一个结构修复候选

候选名称：SPARSE_STREAMED_ALT_V2。

维持 Q=1 和 ALT_BUCKET_FP32_V1、shift=20，完成每张真实图全部 sample。采用 8-lane/8-owner tile 起步；最终目标为 8 个 tile、64 条实际展开通路、64 个行 owner。最终规模须根据 tile 资源、实测服务率和闭环预算确认；不盲目复制。

若最终采用 32 条算术通路、64 个 owner，必须称 32-lane，而不是沿用“64-lane”。不能通过只乘并行度把旧模型变快。

本轮组成：

1. 有界桶目录与分 bank 的 active、changed、closed 工作列表；
2. 保留语义的准备后 CSR，以及一次加载的只读 cost 表；
3. 多 parent descriptor、多在途访存、整行消费的图前端；
4. 多路候选交换与同步 RAM 的 owner 更新流水；
5. wave 屏障后的并行 changed-only 提交及同 bucket 闭包。

## 3. 稀疏调度必须恢复，且不能再次串行化

算法参考是 accel/lookahead/round6_1/bucket61.hpp。CPU 已有 directory、active、touched、closed；全图扫描不是 ALT 正确性的要求。

### 3.1 桶目录

支持已有 4096 key 范围。使用分层 nonempty bitmap/priority tree 选择当前最小桶，不扫描 pending[N]。每桶成员采用有限 chunk/队列，按 tile/owner 分区，以批量 ID 读取或多 bank 并行出队。

pending key/version 是成员有效性的依据。保留 lazy deletion 时，容量必须统计仍占物理位置的 stale entries，不能只统计 live pending。chunk/free-list 的分配、回收、读写端口和失败返回必须真实存在。

旧 524288 live-member 上限不能自动变成所有新列表的容量。分别统计 member、active、changed、closed 的峰值，并限定总物理池；不能把 pending 峰值借给 changed/closed 作为容量证明。不得以无限 vector/map 作为硬件存储。

### 3.2 active 与 closed

一次 wave 取出的有效 active 节点，其 parent label 在整个 wave 内固定。按 owner/tile 批量取得 active IDs，形成并行 parent descriptors。一个桶的 closed list 记录真实展开过的节点，使用独立 membership 标记去重。

当同 bucket 的新 pending 全部处理完才闭包；闭包仅遍历 closed list，正确归并 target cells 并处理 early-stop。不得提早记录每 wave 的暂态 target，也不得跳过原有 eligible<0 的行终止语义。

### 3.3 changed-only commit：本轮推荐采用的精确优化

简单参考先可使用 touched-only commit；最终候选建议只提交本 wave 真正发生 proposal 改善的节点。它保持 ALT 语义，不引入 FP16、近似或不同路径分量拼接。

不变量：

- wave 开始时，对每个节点，持久 proposal home 与 label 相同；
- wave 内 label 不变；
- proposal 只通过完整 pair 的严格字典序 min 单调下降；
- wave 末所有 proposal 写入完成后，才提交 label。

因此，“本 wave 至少改善一次的节点集合”恰好等于“最终 proposal 严格小于 wave-start label 的节点集合”。每个这样的节点仅进入 changed list 一次，最终读其完整 final proposal 并提交即可。

BNN 既有工作量：全部 touched 合计 335,766,497，而最终成功提交节点合计 104,210,988。这个数字是既有软件画像，不是新硬件已实现的周期收益。

实现要求：

1. 独立于 cache residency 的每节点 changed membership bit/epoch。缓存驱逐、重填不能丢失“已经登记”的信息。
2. first-mark 与列表空间/信用预留原子化；队列满时背压，不能先标记后丢 ID。
3. hit 时比较新旧完整 pair；纯 cache fill 不算改善。
4. miss/MSHR 合并需在 baseline home 返回后比较每个 sector；不能把“有 pending candidate”直接当改善。
5. 同一节点多次改善只产生一个列表项；提交时读取最终值，而不是首次改善值。
6. fence 等待候选、MSHR、脏写确认、changed append 和前端所有读响应；提交后才清 membership 并进入下一 wave。
7. 可保留最终 proposal-vs-label 检查作为实现核验，但不需要再扫描未改变节点。

下一 wave 的启动还须等待 label 写确认、pending/目录插入完成以及本 wave changed 标记清理；“发出 commit 请求”不等于恢复了不变量。

旧画像只有逐 wave touched 数与逐 sample updates 总数，不能凭总计104,210,988猜出每个 wave 的 changed 数。新增功能计数必须记录每个 wave 的 changed 数、峰值与 changed-line 数。可后续将同一32B行的changed IDs合成一个行ID+4sector mask，减少事务；不能预设有4倍收益。

记录 wave-start 不变量、末态差分、逐 wave changed 集合与参考成功提交集合的一致性。若这一优化尚未通过，先保留 touched-only 正确路径，不冒充已经降低到 changed 工作量。

### 3.4 并行提交是必要项

在旧 BNN 工作量下，按 compact GPU 0.30468s、假设 200MHz，完整 batch 只有约 60.94M cycles 预算：

- 候选平均至少 21.12/cycle；
- active parent 平均至少 1.69/cycle；
- touched 提交平均至少 5.51 IDs/cycle；
- changed-only 成功提交平均至少 1.71 IDs/cycle。

这些仅是全 batch 平均必要条件；expand 与 commit 受 wave 屏障分隔，还需要更高的阶段内服务率。例如 64-lane II1 + 8 touched IDs/cycle 的理想串行阶段总下界约 0.3104s，已慢于 compact GPU。不能使用 max(expand,commit) 假装两阶段完全重叠。

实现分 bank 的队列、标记和提交。changed-only 的初始全核设计目标可取至少 16 IDs/cycle 的提交服务能力；8-lane tile 对应至少 2 条可并行提交通路。最终按实际冲突、外存和逐 wave 计数验证，不把这个设计目标当达成值。

active parent 出队/调度的初始全核设计目标为至少8 IDs/cycle，不能保留单一逐节点调度器。展开和父节点准备可在有限descriptor/FIFO条件下重叠；闭包与提交仍遵守所需屏障。

## 4. 输入准备与运行时本地 cost 表

### 4.1 runtime cost table

一次加载当前 graph 的全部 cost pair，向所需 tile 复制或 bank 化。BNN/LSTM 仅 10 个 pair，可直接用寄存器或小 RAM；不硬编码数值和输入。声明支持容量和超容量行为。

cost 表从设备内存加载到片上的开销计入每个完整 batch 的 resident 初始化，不能在每轮计时前免费填好。首次主机 H2D 仍按 V2 规则另列。

### 4.2 准备后 CSR

eligible(a,b) 只依赖不可变 node 字段，可在输入准备阶段：

1. 按原行、原邻接顺序调用现有 eligible；
2. 返回 0 时跳过；
3. 返回 -1 时终止该行剩余边；
4. 只为 +1 生成 dst + cost_index 描述符。

禁止仅“滤掉不合法边”而继续处理原本 break 后的边。并行硬件也必须保持这个可消费前缀的语义。

默认准备一个显式准入的 32-bit 描述符：低 28 位 dst，高 4 位 cost_index；先检查节点 ID 和 cost 数量范围。超范围走明确的 64-bit 兼容格式或返回 unsupported，不能截断。当前两图满足该范围并不等于所有 RRG 都满足。

保留原 node/cell 数据用于 closure/target 等必要阶段。不能因为展开已预解码就免费删除下游仍使用的输入。

转换保持图通用、运行时可加载，并记录输入/表示哈希、转换时间和字节数。转换在 resident 外，在 E2/cold-call 中列明；不声称压缩/过滤单独就是硬件贡献。

给同算法 CPU 提供新表示功能参考。若该准备步骤也降低了 GPU 的算法工作，补一个最小 prepared CUDA 对照或明确分离表示收益，保留更快参考；不要隐去新的软件收益。现有 GPU 结果仍作为固定历史基线，不需要先重测它才能开发 RTL。

## 5. 图前端必须真正多在途、多候选

实现独立、有限队列隔开的 parent descriptor、CSR row/edge line fetch、beat unpack、FP32 candidate generation、tile routing。

- 同时保留多个 active parent；parent label 每 wave 只读快照。
- 多个带 ID 的读请求在途；request/response 不使用全局一进一出的 blocking FSM。
- 读一个 32B beat 后消费所有有效描述符，32-bit 格式每 beat 最多 8 个，不为每个元素重读一行。
- 对 row/label 等元数据也使用行缓冲或成组访问，记录实际节省，不能只优化 edge 数组。
- 同周期能够向不同 owner 发出多个候选；取消全核一条 one-wide candidate bus。
- 分 tile 仲裁、有限 FIFO、实际目标冲突和背压，不能假定无代价 crossbar。
- 32 个物理通道共享所有数组的总带宽；owner 数不等于独享通道数。

按带宽延迟积估计所需在途额度：O >= B*L/32B。例如 102.4GB/s、300ns 对全部流量约需 960 个同时在途 32B 事务才有可能隐藏延迟。它是必要容量量级，不是无冲突吞吐保证；各服务划分额度并核算物理存储。

计数至少包括：每周期候选发射/接受/退休直方图、active ID 出队数、changed commit 数、frontend starvation、downstream full、未使用 beat sectors、每通道 outstanding、owner MSHR、路由冲突及控制周期。

不能用“有64个lane实例”替代这些证据。

## 6. owner 存储与关键路径修复

保留既有同行归属、4-way×32sets、32B 行和有限 MSHR 基本参数；此轮不扫缓存容量。

优先将大 payload 数组、FIFO payload 和 cache data 映射为同步 RAM。标签、valid、dirty、少量关联 metadata 可根据实际端口需求保留 LUT/FF。不能只加 ram_style 属性而不改变异步读写协议。

建议流水级：

1. 注册 FIFO head / 接收请求；
2. tag、MSHR、dirty RAW 匹配；
3. 选中 way 的同步数据读；
4. FP32 whole-pair min、changed 判定；
5. 数据写回、列表登记与退休。

同地址 RAW 通过 scoreboard/forwarding 或有记录的 stall 处理。跨级状态更新、response 填充、请求竞争、dirty eviction 和 flush 都要计入，不把流水依赖声明成 false path。

修复既有 mem_valid 的握手气泡：在输出被接受的同周期允许填入下一条命令，同时保持背压时稳定。原代码的旧值条件导致 outgoing command 最多一条/两周期；这是命令接口约束，不是所有 cache hit 的统一 II2。

请求/响应共用写端口的服务策略需要显式仲裁。移入 BRAM 后端口数减少，不能继续假设原来所有组合数组操作同周期完成。

先看 one owner / 8-owner tile 的综合资源，核对真正推断出的 BRAM/URAM、端口、复制和碎片开销，再做 tile place/route。不能仅按逻辑256KiB声称物理容量够用。

reset/fence/done 使用按 tile 分层的寄存器树，关键返回路径也寄存。针对真实 fanout/route 报告修复，不全局滥加 MAX_FANOUT/DONT_TOUCH。

## 7. 执行顺序与首个必须交付的产物

### P0：一次性冻结证据与预算

复用现有输入、输出、GPU V2和 native bridge。读取本包 review_metrics.json 并从仓库源文件复算关键数字；无需重跑旧749/114项归档或整轮实验。

输出短的 prior_diagnosis.json 与新配置签名，列清 actual lanes、owners、commit width、member/changed/closed 容量、RAM端口、memory service 和准备后格式。

这一阶段不能作为本轮最终交付；紧接着写硬件。

### P1：稀疏功能闭环 + 一个真正工作的8-lane tile

并行开发：

- 有界目录/active/changed/closed 的 C++ 功能参考与硬件服务；
- 运行时 cost 表、准备后 CSR、多在途8-lane图前端；
- 同步 RAM owner 流水与多路路由。

先在小图接成完整闭环。golden 只能核对输出，不能供给 frontier/changed IDs。至少两个完整原生小图 batch 输出一致。

高负载定向测试覆盖：连续多行、多父节点、同目的/同行冲突、多 miss 同时在途、响应乱序、dirty回访、FIFO满、边界beat、eligible break、同bucket重入、列表重复、epoch/清理以及运行中容量溢出。

溢出测试可缩小参数制造真实运行中溢出，不需要真的生成极大图。未排空时不能返回成功，不能发布部分 map。

首份阶段交付必须包含集成RTL、完整小图输出/周期、发射与提交吞吐、各数组事务、BRAM资源和tile OOC时序；不能只交报告、资源估算或一个外部trace驱动的cache。

### P2：并发域模型校准与完整工作量账目

旧模型 Owners::candidate 使用单 busy[owner]，大图域每owner最多1个miss，不能通过乘64改成新模型。

新模型需实现实际 request/response FIFO、并发 MSHR、dirty slots、多个 parent、router arbitration、RAM端口、changed queues和wave完成事件。

先校准高负载组件，再校准完整小图与未调参的小图。报告阶段周期、请求数、事务、high-water和stall误差；不能只因总误差<1%就忽略重要阶段失配。

使用真实全部 sample 的功能运行产生新的 per-wave counts/traffic 和有限服务模型，确认实际列表工作量、字节量与容量。不要把旧85.45% hit、旧−0.25%误差或旧200MHz当新候选事实。

### P3：有限扩展与全核物理实现

8-lane tile完成后，根据真实服务率和资源选择最终宽度，默认目标64展开lane/64owner，不做大范围扫描。

在已知40sample工作量上，计算逐wave：

    expansion_time >= max(edge_work / structural_max_expand_rate,
                          parent_work / structural_max_parent_rate,
                          expansion_bytes / declared_memory_service_cap)
    commit_time >= max(changed_work / structural_max_commit_rate,
                       commit_bytes / declared_memory_service_cap)
    total >= sum(expansion_time + commit_time + required_fences)
             + init + closure + output + drain

上述只是固定候选/频率/存储情景下的乐观必要界；分母须是由lane数、最小服务间隔、RAM端口、接口等结构证明的最大能力。测得的平均服务率不是可证明的最大能力，不能直接用它构造“必定失败”的下界。实测服务率用于条件性能模型和工程预算，实际模型仍须使用完整队列和依赖，不能直接将下界当预测结果。

即使旧完整扫描版本必要界失败，也不阻止本轮P1的新原型。P1/P2完成后，若新候选上述可证明的乐观必要界仍超过最快匹配软件，则不继续堆大规模OOC。若只是经RTL校准的具体模型较慢，先指出真实阻塞并做一项有依据的针对性修复，不把一次实测平均率称为不可逾越的上限。最终交付具体剩余瓶颈和该候选结果，不能泛化成所有FPGA不可行。

若预算有余量，完成最终顶层OOC以及相同配置完整小图RTL校准。tile频率不能冒充全核频率；64owner模型不能只继承8owner校准。setup/hold失败保留，目标频率仅用于projected。

### P4：最终大图与软件对照

先跑BNN完整40sample的F1中央情景；通过后固定设计跑LSTM完整40sample。LSTM是本次设计验证输入，不称为项目从未使用的独立跨家族留出。

F0使用同一个新前端、同一个新稀疏调度和有限内存，仅关闭owner cache/merge；若要给出硬件消融，使用新F0 RTL在小完整图/高负载域校准。无需补旧no-go F0的全部历史缺项。

最后再跑有区分度的memory sensitivity；没有必要在候选明显失败时重复12项全量模型。

## 8. 存储模型与计时边界

保持 RESIDENT_COMPLETE_BATCH_V2。所有真实sample都完成；每batch reset、runtime cost预载、内核访存、队列、必要控制、commit和排空都计入。外部表示转换、首次H2D、最终D2H另列。不得追加人工重复batch来摊销，也不能把模拟器墙钟时间当FPGA时间。

旧中央requested128GB/s与requested192GB/s因为整数gap均成为effective102.4GB/s。继续使用时只视为同一个有效点，不能画成独立带宽收益。若改为有理credit/token调度，必须同时改RTL测试平台与模型并重新校准；这属于可选的模型精度修复，不是制造加速的手段。

所有参数含来源状态。没有板测允许assumed，但同地址RAW、读写共用带宽、队列上限、每通道争用、写确认与背压不能省略。

频率改变时，以ns和B/s为基准重新换算服务周期、时钟接口上限和相对时序；禁止只把旧cycles除以新频率而保留不同物理延迟。

新增表示的转换时间纳入cold/E2补充。如果GPU准备后实现更快，保留它。原VPR/最佳native STRICT的同范围计时在最终优势评估阶段补齐；它们不应阻断P1，但未补齐就不能宣称超过这两个基线。

## 9. 最小消融和论文定位

保留旧扫描实现的负结果，来源明确。新候选最低需要：

- 新稀疏调度/准备后数据路径的功能与工作量验证；
- 同一新路径下F0/F1的cache/merge消融；
- 多在途前端的真实发射率、退休率和访存占比；
- changed-only相对touched-only的正确性及提交数量对照；
- 对应OOC资源和时序；
- 完整batch对匹配CPU/GPU的结果和内存条件。

不是每个消融都要单独做一套全核place/route。报告模型/RTL覆盖范围，阶段配置变化只支持对应阶段结论。

潜在论文贡献应写为：针对有wave快照与bucket闭包约束的lookahead，用单调proposal驱动changed-only提交，以稀疏调度、准备后图流和有限合并流水共同减少控制与随机访问开销。不能将“用了FIFO/BRAM/64lane”本身当成新颖性。

是否形成FPGA加速主张取决于完整结果；仅比旧15,000秒原型快很多，不足以证明优于软件。单阶段加速、完整batch加速、E2/Process加速分别标注。

## 10. 复用与新增证据

可复用：输入身份、原ALT语义和输出检查、未改变的FP32单元测试、当前GPU V2测量、native bridge及输出完全相同条件下的QoR、旧负结果。

必须更新：准备后表示身份、changed协议、并发模型校准、新RTL周期/资源/时序、列表容量与动态溢出、完整batch流量/性能。

新状态分别记录：

- sparse_control_verified
- changed_commit_invariant_verified
- parallel_frontend_verified
- concurrent_owner_model_calibrated
- tile_ooc_timing_supported
- full_kernel_ooc_timing_supported
- full_batch_superiority_under_declared_model
- board_measured=false

首个回报重点是“扫描工作减少多少、每周期真正供给多少、实际提交率多少、同步存储后关键路径是什么”。归档条目数量不是性能进展。

## 11. 最短启动指令

请按本文件执行一次SPARSE_STREAMED_ALT_V2结构修复。以fe659f008fc58c913bb1c0232d9898caf79fd524新建独立分支；保留旧结果。先实现有界稀疏桶/工作列表、changed-only提交、runtime cost预载、多在途多候选图前端和同步RAM owner流水，交付8-lane完整小图RTL与tile OOC，再按实际吞吐/流量预算扩展和重新校准。GPU授权及V2补测已完成，不重复等待；无板卡不阻塞。不能继续保留全局单候选总线，不能把单ID串行队列当完成并行化，也不能只修旧扫描核时序。通过技术阶段后自主继续；最终按实际证据报告，不预设FPGA必胜。

## 12. 来源与复现

所有仓库来源固定到fe659f008fc58c913bb1c0232d9898caf79fd524：

- docs/lookahead_fpga_sim_restart.md
- accel/lookahead/fpga_sim_restart/closed_loop/graph_control.sv
- accel/lookahead/fpga_sim_restart/closed_loop/graph_top.sv
- accel/lookahead/fpga_sim_restart/closed_loop/model.cpp
- accel/lookahead/fpga_sim_restart/rtl/owner_service.sv
- accel/lookahead/round6_1/bucket61.hpp
- accel/lookahead/include/workload.hpp
- results/fpga_sim_restart_20261111T231000Z/evidence_snapshot/closed_loop/large/bnn_F1_central.json
- 同一large目录的lstm_F1_central.json
- 上一级closed_loop目录的mechanism_counters.json、memory_layouts.json、physical_audit.json和ooc_64_fixed/internal_setup_200MHz.rpt
- results/fpga_sim_restart_20261111T231000Z/gpu_v2_supplement/summary.json
- results/lookahead_accel_round6_20261109T150000Z/evidence_snapshot/profile_summary.json

相关方法/工具依据：

- GraphLily (ICCAD2021), https://huyuwei.github.io/files/graphlily-iccad2021.pdf ：稀疏图的独立流、局部bank与复制、流水仲裁，不能照搬其性能或数据集阈值。
- AMD UG949 2022.2, Replicate High Fanout Net Drivers, https://docs.amd.com/r/2022.2-English/ug949-vivado-design-methodology/Replicate-High-Fanout-Net-Drivers ：按层次构造平衡寄存器树。
- AMD UG1399 2022.2, set_directive_dataflow, https://docs.amd.com/r/2022.2-English/ug1399-vitis-hls/set_directive_dataflow ：任务/通道的并发需要实际结构，不是顶层标记即可。
- AMD UG901 2022.2, Choosing Between Distributed RAM and Dedicated Block RAM, https://docs.amd.com/r/2022.2-English/ug901-vivado-synthesis/Choosing-Between-Distributed-RAM-and-Dedicated-Block-RAM ：distributed RAM与block RAM的读接口分别为异步/同步，迁移时必须调整RTL时序。

本包review_metrics.json由上述既有JSON计算；所有新的优化、时序与性能仍待服务器实现。
