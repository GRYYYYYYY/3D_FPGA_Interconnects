# CODEX_FPGA_LOCAL_FABRIC_AFTER_7DD79B2

## 独立执行指导：专用访存网络、独立前端记录与流水发布

日期：2026-11-15（Asia/Shanghai）。

本文件完整自包含，只依赖现有仓库、服务器已有输入/工具和下面列出的基点。不要寻找未上传的旧 Markdown 或 ZIP。请直接实施已授权的独立实验，正常实现错误修复后继续；无开发板不构成停止 RTL、OOC 或架构模拟的理由。

研究目标保持：FPGA 优于各个合格软件基线，GPU 与 CPU 不要求排序。当前没有已验证方案保证超过 H100；本轮检验三个具体结构问题，并据实际结果推进完整核。不得预设必胜、降低软件基线，或将单个实现失败扩大为所有 FPGA 方案失败。

## 0. 工作区、基点与保护范围

固定基点：

    7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec

现有分支：

    accel/lookahead-descriptor-front-20261114

建议新分支与目录：

    accel/lookahead-local-fabric-20261115
    accel/lookahead/fpga_local_fabric/
    results/fpga_local_fabric_20261115/
    docs/lookahead_fpga_local_fabric.md

先检查适用 AGENTS.md、Git/worktree 状态、完整 SHA、实际活动进程。已有本轮正确 worktree 时接续，不重复创建或重跑；否则从固定 SHA 创建独立 worktree。main、原稿、STRICT、旧 golden、历史正负证据、旧实验源码和未跟踪指导文档保持不变。对旧模块的修改在新目录复制/派生，不能原地改变已有证据绑定。

复用：已有 CUDA 254 项 receipts、六项旧 P8/F0 完整模型、CUDA 源码闭包、7dd79b2 的完整 C0/F2、已验证 descriptor ABI、native 回接身份、已有局部 RTL/时序证据。不要重新排队旧 GPU 实验。post-push receipt 可以在服务器结果目录独立存在，不用制造提交哈希自包含循环。

## 1. 本轮事实基础

### 1.1 当前完整结果

| 指标 | BNN40 | LSTM40 |
|---|---:|---:|
| 7dd79b2 C0 cycles | 72,347,012 | 73,374,604 |
| 7dd79b2 F2 cycles | 71,238,001 | 72,236,324 |
| F2 POP+expand cycles | 47,780,276 | 48,472,608 |
| F2 finalize cycles | 22,011,170 | 22,294,255 |
| F2 条件时间，假设200MHz | 356.190005 ms | 361.181620 ms |
| 强 CUDA resident 均值 | 151.79996944444446 ms | 159.49799988888888 ms |

两套完整配置输出均正确。F2 仅减少约1.53%/1.55%周期。相比目标仍需减少约57.38%/55.84%；当前不存在完整核频率资格。旧 ccec 约52M周期采用不同服务契约，不能与本轮72M直接解释为相同硬件退化。

删除旧F2调度中的整个finalize后仍需246.134155/249.710345ms，说明仅优化finalize不足。该相减是阶段诊断，不是新架构的必要界。

### 1.2 面积问题的具体来源

当前 df_rr_router 对每个输出复制一整棵包含宽payload的选择树：

- 请求208源→128个(port,class)出口，payload329bit；
- 返回128入口→208源，payload288bit；
- wrapper只固定class，大量实际不可达的地址/写通路仍可变。

实际映射9,736,935个逻辑LUT primitive；即使按每物理LUT容纳两个逻辑函数的极乐观界，仍需至少4,868,468个物理LUT，超过器件1,303,680的373.44%。512条分布式RAM属性被忽略应修正，但它不能解释或解决主要全互连面积。

这份网表映射足以否决该通用网络实例。原 synth_design 导入被中止，没有完整utilization/DCP/布线资格，原报告的限定保持。

### 1.3 F3负结果的范围需要准确表述

F3的128个token同时承担POP、DESC等待、decoded-ready状态；解码后等待实际allocate_E成功及target分支交接，才释放原token。C0/F2则拥有独立H128、M128、ready128，工作交接后可较早释放POP token。

因此，本轮F3测试同时改变了表示和独立缓冲/驻留生命周期。它是有效实现对照，但不是保持独立缓冲能力相同的纯格式消融。不得把约17%变慢扩展成“描述符融合无用”；也不得预告解耦后必胜。

### 1.4 publication的实际串行链

当前目录bank是单命令同步FSM；APPEND需要多个RAM步骤并等响应消费。发布wrapper又逐事件执行捕获、提交、等真实响应、deferred ACK、再捕获。

源码推导目录APPEND接受间隔约6拍，wrapper连续事件约8拍；这些数字先由本轮微回放确认，不直接作为新测量。79.6%/79.9%的publication-held观察器是优先编码状态占用，不能直接当可删除的纯停顿比例。

未发现可以从模型中直接删除的重复计费。要实现新的有限流水，再计新时间。

## 2. 本轮主线与工作顺序

主线一：利用合法连接关系，替换巨大通用访存网络。先全尺寸综合和有限协议验证，再大图。

主线二：保留F2基线，补一个真实独立D池和ready交接的融合候选；隔离生命周期问题。

主线三：保留K8与word lock，分离发布入队和最终退休，验证有界publication journal＋目录APPEND流水。

三者的小型实现/验证可并行；完整集成、模型比较和最终资格按依赖推进。每条主线只保留明确的小集合对照。继续使用单活跃sample，不在本轮同时引入双sample调度、K16、更多算术lane、不同数值算法或新cache策略。

## 3. 阶段A：合法连接表与实际source adapter

先读：

    docs/lookahead_fpga_descriptor_front.md
    accel/lookahead/fpga_descriptor_front/service_contract.json
    accel/lookahead/fpga_descriptor_front/model/finite.hpp
    accel/lookahead/fpga_descriptor_front/services/df_memory_network.sv
    accel/lookahead/fpga_descriptor_front/services/df_memory_network_full.sv
    accel/lookahead/fpga_descriptor_front/services/df_rr_router.sv
    accel/lookahead/fpga_descriptor_front/services/df_tagged_port.sv
    accel/lookahead/fpga_descriptor_front/front/df_front_group.sv
    accel/lookahead/fpga_descriptor_front/services/df_directory_bank.sv
    accel/lookahead/fpga_descriptor_front/backend/df_context_slices.sv

从实际地址/源码生成并检查source_legality.json：

| Source | 实际类别 | 连接 |
|---|---|---|
| 0..15 | EDGE，只读 | 动态物理port |
| 16..31 | ROW/DESC，只读 | 动态物理port |
| 32..47 | META，只读 | 动态物理port |
| 48..111 | 64 canonical banks | 每bank唯一port |
| 112..175 | 64 scratch banks | 每bank唯一port |
| 176..207 | INIT/output/cost | source自身对应唯一port |

在当前地址契约中：

    bank(line) = 2*(line & 31) + ((line >> 5) & 1)
    canonical/scratch port(bank) = bank >> 1

这一关系依赖真实基址按32条line对齐。对所有地址种类、样本范围、最高合法地址执行检查；runtime不符合时明确失败，不允许静默截断地址或强制送错owner。

本轮要交付真正可综合的source-specific pack/unpack adapter：

- 明确kind、local ID、generation、读写类别和返回目的的位域；
- 可以先保留32bit local identity，不为窄化而冒险截断；
- 固定连接通过生成参数/结构实现，不能只在文档中声明；
- 只读前端没有256bit写payload通路；
- canonical/scratch读数据留在本地返回；
- 写ACK保留真实identity/status和计数，不传递无用的256bit返回数据；
- cost-load属于本地admin读操作，仍须返回真实256bit数据并核对；不能将全部admin返回都窄化为无数据ACK；
- 非echo真实返回payload必须端到端核对；
- 证明每条实际请求/ACK的连接与旧语义一致。

不是只把通用模块的几个输入接零，再假定综合器能消除所有无用宽树。

## 4. 阶段B：32个本地port服务＋动态只读网络

### 4.1 本地服务

每个物理port本地接入：

- 它的两个canonical bank；
- 两个scratch bank；
- 对应INIT/output/cost来源；
- 动态前端EDGE与ROW/META/DESC请求。

保持32个物理32B端口、每端口32个credits、真实tag分配/归还、OOO返回、有限响应FIFO、写ACK和公平性。额外逻辑来源不增加物理issue数量。

本地canonical/scratch/admin请求和返回不经过全局208-source网络。不同来源仍共享该port，任何新增仲裁、FIFO、寄存和阻塞都计入模型。没有第二套隐含credits。

动态部分只处理48个只读前端source。F3不用的META来源在其实际配置中恒无效，F2的ROW/META/EDGE配额保留。

### 4.2 优先生成专用稀疏连接网络

第一版根据合法来源列表生成请求/返回选择，不实例化208×128和128×208通用payload树。局部源直连，动态读请求仅携带地址和返回身份，动态返回携带实际数据和身份。

先全32port/全合法source规模、带实际5ns时钟约束综合。仅一个port的面积乘32不覆盖全局网络，不能代替这一步。

如果这个专用静态结构仍明显超过完整剩余资源或关键选择路径不可接受，允许下一节一种明确fallback。不扩展成拓扑/参数大扫描。

### 4.3 唯一结构fallback：三层radix-4只读网络

请求源：48个有效源padding为64，其他源永久invalid。

请求目的：

    dest = 2*physical_port + front_class
    front_class = 0 for EDGE
    front_class = 1 for ROW/META/DESC

64个出口接入32个物理port的两类前端队列，不是64个物理内存端口。本地admin与class1的合并/返回身份区分必须真实实现。

返回使用另一张独立有向网络：入口为64个(port,front_class)只读返回端点，目的为原source0..47；48..63禁止。local admin ACK直接送本地消费者。

三层各16个4×4交换器。固定自路由连接的一种实现：

- stage0使用dest[5:4]；
- stage1使用dest[3:2]；
- stage2使用dest[1:0]；
- 前两级输出线j接下级输入shuffle(j)=((j<<2)&63)|(j>>4)。

末级输出编号对应dest。实际实现必须核对全部4096个source/destination组合，不能将交换器逐组直连后声称全可达。选择高位先路由也避免固定class位在首级制造明显偏斜；仍须验证真实流量。

第一版每input一个真实FIFO4，每output一个真实holding位置，RR只在成功握手后推进。该网络有HOL及中间链路冲突，不能称nonblocking。

若选择每input四个VOQ，则必须真实实现每周期grant矩阵行/列约束或独立多读路径；不能在模型各output独立仲裁时偷偷从同一个input取多笔，资源表却只算一个读口。为控制范围，默认先采用单FIFO4，不自动增加VOQ扫描。

请求/返回网络分离；禁止组合ready环。记录所有hop/FIFO/holding延迟，不沿用旧单层RR的往返周期。48/64个逻辑端点不能增加外存issue或credits。

### 4.4 用实际流量检查链路需求

用真实运行生成的source、dest和class统计：

- 各级各link的实际载荷和热点；
- 每link一拍一包必要界；
- 同时请求冲突、HOL与反压；
- 返回/context容量预留；
- 本地canonical/scratch能否在前端返回受阻时推进。

初筛trace可以用于路由服务对照。最终性能必须重新运行真实算法，不能从冻结trace拼接大图周期。新到达顺序会改变spill。

### 4.5 资源预算与停止点

现有账本去掉巨大common memory network后的公共模块约735,014 LUT；加16个已综合F3前端context约885,222 LUT。相对1,303,680 LUT剩418,458，仍需adapter、控制和实现余量。F2完整前端面积未取得，不能直接套用F3值。

新访存网络200–250K LUT可作设计目标，不是预测结果或任意硬门槛。按实际完整组合判断：LUT、FF、BRAM、URAM、时钟、FIFO和未覆盖模块都列清。

64×64 candidate网络已有250,969 LUT证据，本轮先保留，避免同时改变候选路由与replacement行为；其资源必须实际计入。若新memory网络仍使完整组合确定超限，停止该网络配置的扩大实现，不重复等待大规模网表导入，不宣称整个算法不可行。

完成实际synth_design/report_utilization才称完整综合成功。若提前从映射lower bound判定超限，准确记录停止阶段。后续OOC/place/route使用真实约束，不能以资源-only synthesis充当频率资格。

## 5. 阶段C：一个独立缓冲的融合对照

### 5.1 固定对照范围

在同一获选专用网络下比较：

- S：原分离ROW/META的F2前端；
- F-shared：7dd的融合共享token前端；
- F-decoupled：新独立记录的融合前端。

F-shared用于解释已有负结果；不要求再跑其全部40sample。算术lane64、E256、beat512、输出8banks、全局POP admission上限8保持。

初始显式物理池：

- POP/fork token：128，独立；
- D issue records：128，独立；
- decoded-ready FIFO：总128，独立；
- target待交接缓冲：有界，总最多128，独立计账；
- 16组，每组的真实分配、请求和写口明确。

与分离H/M实现对比实际存储bit、端口和资源；不能称总资源天然相等。

### 5.2 正确生命周期

1. 发起POP前预留有限token。
2. stale POP归还token。
3. valid POP将node、不可变parent pair、必要身份，真实交接到已预留D entry。
4. 交接完成后下一合法边沿释放POP token；D entry继续存在。
5. DESC请求与返回使用D index＋generation，不能依赖已回收POP token。
6. 解码后分别交接到真实ready队列与target待服务缓冲；零度立即完成邻接分支，但保留target语义。
7. 两分支都安全交接后释放D；ready等待E，target等待输出bank，各自持有完整不可变数据。
8. wave/bucket/target/finish屏障等待所有相关池和真实输出完成。

仅添加一个decoded-ready FIFO，仍保留POP RTT与DESC RTT占用同一token，不足以检验本候选。增加普通FIFO也不能免费增加多写口；所有新增仲裁/延迟进入RTL和模型。

8B ABI、degree/offset/cell检查和16B fallback复用已通过的实现。native最大degree<=249已被测得，不重新发明表示。保持无cache时一条DESC请求服务一个parent；同beat其他记录没有免费命中。

### 5.3 有依据的信用容量诊断

先用128/128独立池完成对照，输出各类entry从分配到交接的实际寿命分布、占用、reserve失败和下游可用性。

对目标parent速率r与实际占槽时间L，可用Q≈r×L作为容量诊断，不能当性能预测。所需速率由软件总预算扣除已测必要阶段后计算，不要求无理由填满64lane。POP token覆盖含stale的总POP尝试，D只覆盖合法parent，分别使用对应分母。记录低拥塞服务延迟、队列等待和下游反压，当前拥塞均值不能直接当新配置硬界。区分POP token、D、E，不能把它们都叫context。

若具体池持续阻塞关键路径，且下游确有接收空间，允许最多一个基于计数选择的有限容量点，例如仅瓶颈POP或D从128到256；需要时同时扩二者必须说明为何两个独立服务都受限。保持E256、beat512、K8、物理端口/credits不变，所有位宽、generation、状态RAM写口和新增面积重新验证。

先定位最下游真实限制：D满可能反压成T满，ready/E满也可能造成D满，不能见两个full计数就同时扩两个池。逐组核对可用容量与到达率，不能用全局总数假设闲置槽自动跨组借用。没有上述证据就保持128，不扫2/4/8倍配置。该条件点不继承旧L4的5ns资格。

## 6. 阶段D：K8下的publication journal＋真实APPEND流水

这是本轮有针对性的后端候选。先用一个bank与真实目录完成闭环，再用native owner投影。先确认旧目录APPEND与wrapper的实际接受/退休间隔。

### 6.1 必须拆开两个接口

当前pending输出的ready同时代表事务退休。不能只在它外面接一个FIFO：

- 入队就返回旧ready会提前释放word；
- 等目录完成才返回旧ready，又保留原单pub_slot阻塞。

请在新pending副本内部加入journal，或实现两个独立接口：

    publish_enqueue {slot, generation, payload_reference}
    retire_ack      {slot, generation}

enqueue仅将事务置为PUB_QUEUED，释放发布选择器；Tx槽位与whole-word lock继续保留。retire_ack达到真正完成条件后才允许下一合法边沿复用。

### 6.2 有限容量与顺序

- journal最多8条事务记录/bank；
- 每条最多4个事件，总事件预留不超过32；
- 记录保存slot/generation、原始mask、issued mask、ACK mask、completion/POP handoff状态；
- 可引用仍锁定Tx中的不可变参数，避免无必要的payload复制；
- 所有引用保持到最终退休，不能被下一Tx覆盖。

设置issue cursor与retire head：

- 事件按确定的bank内FIFO记录顺序发出；
- 一条记录的全部事件被实际目录命令口接受后，可以发下一记录；
- 不等每个ACK才允许issue下个event；
- 只有最老记录全部事件已实际目录完成、其他completion条件满足，才能退休；
- 零事件记录不能越过未完成的早先记录；
- POP必须完成预留token的真实交接；
- 不改变same-word保护和有限容量反压。

发完事件、进入FIFO、分配member都不等于最终退休。

### 6.3 APPEND先以真实II2为实现目标

现next_ptr需要写新节点NIL和旧tail link。保留单写口时，明确安排到两拍，不能免费给II1。

实现有限同步流水，覆盖：

- 同bucket连续A/A和A/B/A的head/tail前递；
- 同bitmap word的OR与upper bit维护；
- 空链到非空链，读到未落RAM状态时的前递；
- free-list在途预留，不能向两条APPEND分配同一member；
- 接受APPEND前同时预留member及响应位置；
- 背压下各流水级valid/payload保持；
- 真实RAM写完payload/link/head-tail/bitmap后才产生ACK；
- ACK带record/slot generation和event index，或已证明的严格有序对应；
- TAKE/RELEASE/MIN与APPEND的阶段切换要先排空，在单sample算法下保留真实屏障。

保留一条PV读和一条PV写服务/bank，以及原外存带宽；不增加K。II2只是无相关冲突/背压时的目标，需要实际RTL测得。

### 6.4 校准观察点

至少比较旧/新同输入的：

- bundle capture/enqueue；
- APPEND command accept；
- 目录RAM-visible完成；
- event ACK；
- bundle/word实际退休；
- 反馈延迟、持续接受间隔与持续退休间隔；
- FIFO/预留峰值与排空。

覆盖0/1/4事件、同word、同bucket、同bitmap word、free-list满、响应背压、generation边界、stale POP、连续波次。不能只测“FIFO每拍能进一笔”。

final_done、MIN/TAKE、下一wave、sample clear、export/finish必须等待journal、目录流水、响应和所有真实退休全部完成。严禁以入队代替这项屏障。

## 7. 阶段E：有限模型与集成顺序

### 7.1 替换公共服务，不叠加两套网络

新专用网络替代旧transport。所有新增hop/FIFO/adapter/响应队列和本地返回路径进入模型，旧通用fabric不再暗中串联；也不删除现有必要的memory服务。

采用真实物理32B地址；80ns从实际external issue算起，5ns issue间隔是现有模拟假设。频率变化时重新离散/实现相应服务，不能将旧200MHz周期直接除新频率。

尽可能让模型和RTL使用同一明确定义的pre-edge/handshake契约，并用独立对照检查。不能由同一错误实现生成“expected”后自证。

### 7.2 最小有效消融

先复用7dd旧完整F2作为已知条件参考，不重跑同源配置。

新网络后使用以下小集合，不做全笛卡尔积：

| 配置 | 网络 | 前端 | publication |
|---|---|---|---|
| L0 | 专用 | F2分离 | 旧串行 |
| L1 | 同专用 | F-decoupled，或实测更好的F2 | 旧串行 |
| L2 | 同专用 | 同L1 | journal＋APPEND流水 |

另在固定代表样本比较F-shared，定位生命周期贡献。若条件信用点被选择，单列其增配代价，不能混入“仅格式优化”倍数。

初筛复用预先固定完整sample：BNN2/19/35/31，LSTM7/19/18，按实际manifest核对编号。每个从实际初始化开始；保留尾部和负例。不要看新成绩后只选有利样本。

以新请求顺序实际运行完整算法，产生新spill、目录事件、峰值、成本和输出；旧golden只用于核对，不能驱动性能路径。小型trace可诊断服务但不能替代完整原生batch。

### 7.3 何时运行40sample与完整top

新网络先取得全尺寸实际资源依据和局部协议资格。面积明确改善并具备实际可行的组合预算后，L0本身即可运行BNN40/LSTM40，以建立真正可实现结构的完整基线，不要求前端和publication同时获益。局部前端/目录改动功能正确且有净收益线索时，再运行获选组合；已完成且源绑定一致的样本复用。

完整比较包括初始化、cost load、真实请求/返回、所有wave、target条件、目录/PV、输出backing和全部ACK。单sample配置的硬件cycles依sample顺序相加，CPU多进程模拟墙钟不能当硬件batch时间。

若至少一个目标案例出现同范围软件优势预测，并有完整资源与关键服务依据，推进完整小图top、实际全配置OOC及大图模型校准；允许另一案例保持负结果。没有开发板不阻止这条仿真资格链。

若尚慢于GPU，仍交付已完成的可综合网络和局部机制结果，明确实际差距。只有具体、已经有实现/计数依据的剩余问题才在本轮修复；不自动开启新算法、多sample、lane/K/频率扫描。

## 8. 时序与物理资格

复用已通过的L4前端作为明确模块起点；接口、buffer大小、选择器或流水发生变化时重做对应资格，不继承旧+0.255ns。

后端当前内部reg-reg setup/hold已通过，负hold仍在外部输入边界。这可以指导真实集成，但整体OOC仍未过。使用具有实际launch/capture和ready/valid负载的集成context，依据真实接口约束；不为过线随意调大input min或给内部路径false path。

资源测试从综合前建立实际时钟约束。物理时序报告分别给setup、hold、pulse、未约束路径和真实内部负载。完整核需要其实际完整配置，而非仅把单bank频率外推。

收到Vivado映射/推断问题时先定位模板、端口和真实netlist。对已决定性超容量的网表无需继续昂贵import。工具崩溃、容量失败、时序失败、性能失败分别报告。

## 9. 软件比较与论文结果边界

继续使用最强已资格resident CUDA：

    BNN  0.15179996944444446 s
    LSTM 0.15949799988888888 s

保留其三独立进程、各三正式重复和源绑定，不把九次重复当九个独立进程。

CPU现有证据需分平台：

- H100 worker，Xeon8462Y+ prepared八线程：3.654426308/3.669705272s；
- FPGA工具服务器，Xeon6530 packed八线程：2.842626751333/2.933218058s。

不得跨主机把差值归因于descriptor格式。现有native E2/Process单列，不能与resident拼接成加速比。

新descriptor仍用原8B ABI，现有转换功能和native identity可按完整hash链复用；若新算术/输出adapter改变，补实际核对。只有融合候选进入完整核/真正接近比较目标，才补同表示正常CUDA对照。网络与publication改动本身不需要重做无关GPU优化。

明确三个范围：

1. Resident完整batch：设备输入驻留；包含本批必要初始化、device memory和输出ACK。
2. E2：实际需要的构造/校验、传输、运行与回接；没有真实多构建来源就不免费摊销。
3. VPR Process：单独测量与报告，不用kernel加速替代。

论文可使用明确标注的RTL/架构模拟结果及完整OOC证据。内存80ns/5ns仍是模拟假设；板测字段保持false/null。模型秒数、合格频率下估计秒数、实板秒数分开。ALT输出与STRICT的既有差异继续准确说明。

## 10. 交付、范围与完成状态

交付聚焦实际产物：

- source legality与真实pack/unpack adapter；
- 专用全尺寸network RTL、有限模型、实际资源/时序范围；
- F-shared与F-decoupled的独立存储、token生命周期、计数及功能对照；
- journal/APPEND流水RTL、事件/目录/真实退休trace；
- 最小消融与完整选中batch结果；
- 软件复用、native身份和当前资格；
- 一份可复现报告，关键失败记录、源码/输入/工具绑定和归档索引。

可以使用现有归档流程，避免重新打包所有旧证据或追求检查项数量。修复编译/协议bug后重跑受影响范围，不无理由重跑全部历史。

最后正常提交/推送独立分支并核对完整远端SHA。若长任务仍在运行，列出真实job/PID、日志和接续状态，不称整轮完成。若全部终态，明确无本轮在途任务。受保护分支、原稿和旧证据保持不变。

阶段结论分别回答：

1. 新网络是否实际装得下，面积节省来自哪些连接/位宽？
2. 独立缓冲是否改变parent速率与完整时间，收益是否抵得过新增资源？
3. 发布流水是否提高真正退休吞吐，是否保持word/目录正确性？
4. 哪个完整案例在何种仿真/频率/内存条件下达到或未达到软件目标？

## 11. 固定来源

- [完整报告](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec/docs/lookahead_fpga_descriptor_front.md)
- [完整模型](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec/accel/lookahead/fpga_descriptor_front/model/finite.hpp)
- [通用网络](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec/accel/lookahead/fpga_descriptor_front/services/df_memory_network.sv)
- [RR选择树](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec/accel/lookahead/fpga_descriptor_front/services/df_rr_router.sv)
- [融合前端](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec/accel/lookahead/fpga_descriptor_front/front/df_front_group.sv)
- [目录RTL](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec/accel/lookahead/fpga_descriptor_front/services/df_directory_bank.sv)

