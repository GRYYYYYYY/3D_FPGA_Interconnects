# DAC2027：以创新机制为主线的全文修订与有界补证

## 0. 任务及授权边界

用户最新要求：将论文组织成“领域进展 → However：关键问题 → 相关工作的贡献及未覆盖的具体问题 → 本文洞察、方法和结果”，突出可验证的创新与优势；利用用户给定的一天预算补最重要的证据，而不是继续扩大硬件设计。

本文件独立自包含。不依赖任何此前未上传的 Markdown、ZIP 或聊天记录。

审阅基准：`GRYYYYYYY/3D_FPGA_Interconnects`，提交 `986149c07bc7b8be54d99e8a2e2a47327ec143b5`。
投稿稿：`accel/lookahead/fpga_cpu_primary/submission/`。

这次授权允许在独立 paper worktree/分支中调整论证与章节组织，不再仅限旧的四个硬件终态更新文件。必须保留旧冻结稿、冻结回执和所有原始证据，生成新的修订记录，不覆盖旧冻结哈希。

现有 h EDA 作业不是本任务的执行对象。先核对实际状态，绝不重复启动、重置、中断或修改正在读取的输入。硬件后续仅使用另行已经授权的收尾链。本任务不引入新 RTL 架构、换器件、频率扫描或 GPU 调优。

目标不是保证录用、制造排序或证明所有既有论文都较差，而是提交一篇有明确问题、机制、可检验差异及恰当适用范围的完整论文。

## 1. 主立意

建议主题：**面向分层 FPGA 路由启发式构建的双粒度并行化：区分必须保留的上下文/代价关联与可以解除的执行顺序约束。**

不要把主线写成“先做 CPU，再加 GPU，最后尝试 FPGA”。三种平台应承担不同证据角色：

- STRICT：在限定条件下，不改变 sample 内原生遍历，解除组间不必要的屏障；以私有状态和原序归并维持 native wire-map。
- ALT：另行定义 whole-pair FP32、wave snapshot、strict improvement、same-bucket closure、source-relative target recording，暴露 sample 内并行；不继承 STRICT 等价性。
- FPGA：给 ALT 一个有限队列、有限端口、真实退休/排空的空间实现，展示算法并行度怎样受资源、反馈和物理连接约束。当前可报告 RTL、校准、模型及已完成实现阶段，不提前报告 FPGA 获胜。

候选题目（需要作者核对已登记题目与系统规则）：
`Dependency-Aware Parallel Lookahead Construction for 3D FPGA Routing`
亦可保留当前题目，先修改摘要和引言；无需为改题重做实验。

## 2. 三项贡献：写机制及其作用，不把审计当主要创新

### C1：保持源上下文的跨组任务解耦

输入、源层、目标层、相对位置、wire/segment 类型形成原生 sample 身份。私有搜索状态允许不同组 sample 同时执行；归并按原顺序保持 tie 行为。

不要将 oneTBB Pipeline 原语、线程库调用、workspace allocator 本身称为新理论。Flat 是必要且有利的对照：若 Flat 与 Pipeline 接近，说明收益来自跨组解耦，而非特定库函数。

### C2：保持整对代价的波次化搜索

独立定义 ALT；用 FP32 key 的粗桶调度扩大前沿，而不是量化存储的 delay。snapshot 扩边、whole-pair min、同桶重入/闭包、完成判据构成可执行方法。

不要宣称发明 bucket、atomicMin 或通用 GPU SSSP。不要宣称相对 native 完全等价，也不要宣称对所有 FP32 图全局词典序最短路最优。

### C3：依赖感知的异构执行与原生系统验证

共同原生任务接口连接 CPU/CUDA；有限硬件映射明确状态所有权、端口竞争、提交和排空。使用原生 E2/Process、输出、QoR，以及 RTL/有限模型证据验证方法的价值及边界。

验证是支撑创新的手段；“52 项通过/归档完整”不能单独充当核心科学创新。若硬件收尾失败，仍按有限架构评估定位，不将其提升为已实现性能贡献。

## 3. 四段式 Introduction

1. **现状与需求。** 3D/multi-die 架构与 CAD 工具使跨层资源探索成为实际任务；路由器依赖与资源图/代价匹配的 lookahead。限定关注首次构建或旧表不再兼容时的构建，不声称每次编译都必须重建。
2. **However：有证据的问题。** 锁定 VPR 的 lookahead 构建仍有两个粒度的串行约束：少量 sample 的组间屏障；单搜索细粒度优先顺序。加入已测 GEMM 149.56 s 构建与约 45% Process 的诊断，但明确是一个指定输入/版本的观察。
3. **相关工作的实际贡献与差距。** 路由器并行不等于构建器并行；通用 bucket/SSSP 已解决排序与并行度的权衡，但仍需落实源相对表项、层信息、成对代价及原生消费接口；已有多 die lookahead 改善启发式，不应被描写成没有考虑层间连接。加入缓存/稀疏采样的适用边界。
4. **我们的洞察、两项方法、结果。** 将逻辑 sample 身份与执行顺序分离，在严格兼容路径与另行定义的波次路径之间明确分工。以实际 CPU 与原生 CUDA 结果收尾。FPGA 放在一句实现扩展中；未合格时不写硬件加速倍数。

表达原则：强调“我们解除哪个依赖、为什么仍然正确/可接受、证据是什么”。将重复的否定句移到一次性 semantic guarantee 表、实验方法和 limitations，不删除必要限制。

## 4. 必须回应的相关工作和现成替代方案

### 4.1 资料来源（外部事实与本项目结果分开）

- LaZagna：架构生成和评价。参考现有 `lazagna` 引用并核对正式发表版本。
- Escaping Flatland：3D placement，不是本文的直接构建速度基线。
- Poolad et al., Modeling, Optimizing and Exploring Multi-Die FPGA Routing Architectures，FPL 2026 作者稿：`https://arxiv.org/html/2606.06421v3`，特别是 IV-B2。
- MultiQueue-Based FPGA Routing, FPT 2024：`https://www.alex-singer.com/publications/conference-papers/multiqueuebasedfpgarouting/`。部分算法已有确定性与 serial equivalence，不能说前人均放弃正确性。
- Davidson et al., Work-Efficient Parallel GPU Methods for Single-Source Shortest Paths, IPDPS 2014，现有 `gpu_sssp` 引用。避免把 bucket 和“少量额外工作换并行度”当全新普适原理。
- SPLAG / Accelerating SSSP for Power-Law Graphs, FPGA 2022：已有 coarse priority queue 和 vertex cache；若保留硬件方法小节，应补相关引用与区别。
- VPR 官方当前命令说明：`https://docs.verilogtorouting.org/en/latest/vpr/command_line_usage/`。

**版本警告：** 最新文档不能证明锁定实验二进制具有某项功能或对当前 3D 图支持正确。先检查该二进制 `--help`、源码分支与图处理范围，保存结果。不要为了增加基线而在一天预算内升级整个 VTR。

### 4.2 两个特别重要的替代方案

- `--read_router_lookahead`：兼容输入可以直接加载旧表。本文解决首次构建/不兼容输入下的构建，不与合法缓存命中竞争。不能暗示改变网表就必然改变 lookahead 输入；应以 RRG、cost、sample/context、schema/构建配置等实际身份为准。
- `compressed_map`：官方说明其通过稀疏采样降低构建时间与内存。它比无关 routing 加速器更接近本文问题。若锁定版本与 3D 输入支持，应做小范围对照；若不支持，明确具体技术原因，不把失败标成性能无穷慢，不推导本文优于它。

`separable` 等当前新模式只做文献/源码适用性核查，不为本次投稿启动移植工程。

## 5. 立即可复用的因果证据：不要新跑已完成实验

### 5.1 跨组解耦证据

入口：`paper/dac2027/tables/expanded_flat.tex`，先追溯生成器及原始 run 的列顺序、host、binary、scope。

已存表中的独立八核 BNN 构建对照：Group 17.41±0.33 s、Flat 9.32±0.15 s、Pipeline 9.36±0.11 s。

这支持两种全局任务执行都快于组内执行，不支持 Pipeline 原语普遍优于 Flat。旧表还有 16 核 BNN/DLA 及 2D 对照，优先复用。

图输出建议：同 cohort 的 Group/Flat/Pipeline 核数曲线；若已有 task trace，再画 worker 活跃时间线。禁止用理论排程生成“实测”利用率；无 trace 就只报告时间和原生组宽。

### 5.2 波次机制证据

入口：`docs/lookahead_accel_round6_screen.md`；原始数据根 `results/lookahead_accel_round6_20261109T150000Z/`。

BNN 原始表示、40-sample、shift0/20：

| 项目 | shift0 | shift20 |
|---|---:|---:|
| 所有 sample 的 wave 总数 | 19,691 | 2,161 |
| max-qid waves / 当时 GPU batch rounds | 627 | 59 |
| eligible edges | 1,282,443,890 | 1,286,937,147 |
| edge-work-weighted frontier | 16,061 | 106,780 |

派生数：总 wave 比 9.111985×，全局 rounds 比 10.627119×，边工作增加 0.350367%，weighted frontier 比 6.648403×。

原 R6 CPU/CUDA 时间为各自历史 median 口径，不与后期 prepared-POP resident V2 或 mean±SD 结果混写。优先展示上述操作计数；要加入时间，就重算原始进程数据并在独立 cohort 中标注统计定义。

约 9× CUDA 改善是历史实现同 shift 对照的结果；不能直接用于最新内核或 LSTM。wave 计数下降解释的是同步机会变化，不等于 profiler 证明所有时间都来自 launch，也不等于 occupancy。

### 5.3 语义与 QoR

入口：`submission/tables/qor.tex`、`results/lookahead_r6_2_20261109T191213Z/evidence_snapshot/holdout_results.json`，以及 R6 的 509 fixtures。

LSTM 资格结果：ALT CPU/CUDA sample/map 相同；相对 Flat 的 delay/congestion/missing 差异 0/23,111/0；CPD 11.7483 ns；Flat/ALT wirelength 1,714,423/1,712,223。

这是已测案例事实，不是任何图的 QoR 上界。congestion 差异是相对 native 代表值的语义差异，不是相对物理真值的预测误差。

从已有 counterexample 中选择最小可解释实例，说明独立 min 或不完整源身份为什么不能直接替代原生构建。作为解释性反例，不作为被故意削弱的性能基线。

### 5.4 2D/3D 范围

旧 Flat 表已包含 `clma_2d`、`bnn_2d`。核实输入和实验后可报告方法并非仅对 3D 有效；3D 的特殊要求在 source/target layer 与跨层连接语义。

这些图若不是受控等尺寸配对，不得把速度差异归因于“仅增加层数”。重复 seed 或共享同一 RRG 的不同电路不自动成为独立架构案例。

## 6. 一天预算的补证优先级

这是一份预算内任务选择规则，不是保证完成时间的预测。最终必须留下编辑、作者通读和提交检查的资源。先复用，再补缺；不要求完成所有可选任务。

### P0：必做，原则上不运行新 solver

- 形成 claim–mechanism–evidence 表，逐条对应 C1/C2/C3。
- 复原 Group/Flat/Pipeline 因果图和 shift0/20 工作量表。
- 改正文中的 LSTM 选择时间：未参与此前 ALT 调参，在自身新资格/计时前冻结；不要写全部 ALT 调参前预选。
- 改共同接口：共同的是逻辑 sample/context；STRICT 访问 native RRGraphView，ALT 导出 CSR/其他表示。以固定实现为准复核。
- 将不必要的 R6/R6.1/P1/P2、进程身份、哈希统计移出正文，详细记录留 artifact。
- 保留原生8核 E2/Process 与64-worker resident 两套结果；不得伪造强CPU的native E2。
- CPU强度核对：8核原生 headline 必须有线程限定；近期64-worker resident结果不能证明原生64-worker E2。若现有强线程 native记录已经存在且同范围，可复用。

### P1：优先处理最接近方案的适用性与一个匹配对照

**先做兼容性预检，不直接发一串长任务。**

1. 在锁定二进制和真实2层图上检查 `compressed_map` 和 read/write lookahead。
2. 有可靠记录则复用；若不支持当前图，记录具体退出、源码检查及限制，停止移植。
3. 支持时，预先冻结 BNN 与 LSTM 中的最多两个输入、sample/层身份、原有 QoR 门槛、线程/NUMA设置、host与缓存状态。
4. 新成对正式比较最多3个独立进程/arm/input，轮换顺序；所有本次新比值必须来自同一实验批次，不直接除以旧主机的秒数。
5. 表的行可为最佳已测全球CPU构建模式与compressed_map；是否追加ALT CUDA取决于已有同cohort输出/计时能否合法复用。不同语义方法以E2和QoR作方案对照，不混成STRICT等价消融。
6. 构建模式改变时，原native QoR不自动继承。完整route/FULL/STA使用实际候选结果，不能用单迭代检查代替。
7. timeout/unsupported/failed都有记录；未完成不写成慢到无限。若pilot显示需要基础设施迁移，则立即转成适用性说明并结束。

read-cache 小对照用于说明边界，不与重建混为一个速度排名。只有输入身份实际兼容时才允许加载，不能用旧答案冒充新构建；不要免费摊销未观察到的跨构建重复。

### P2：只有现有机制数据缺失时才补微型归因

若旧波次原始记录足够，跳过新实验。若缺关键指标，可固定一个BNN完整batch，shift0/20各执行一个非计时profile；对每轮expand/commit/closure及host反馈计数。正式性能与profile分开。

不扩大shift扫描；不新增GPU优化来寻找最好数字；不把同一次profile当正式重复。GPU无法访问时继续利用已有正确绑定数据，不阻挡稿件。

### P3：额外泛化/强CPU控制二选一，可选

只有P0/P1已完成且有独立计算资源时，选择一个实际风险：

- 缺少输入覆盖：从已有可重放、已合格但未用于ALT参数选择的真实输入中预选一个，固定参数后跑 matched CPU/CUDA 与必要QoR。不能临时称当前反复调过的LSTM是整个研究的新盲测。
- 主headline被怀疑CPU不足：在当前同一native实验平台上补一个预选强线程点与CUDA匹配对照；样本只有40时不要无限线程扫描。无相同host/配置则保留原8核限定，不拼接历史数据。

不得同时展开上述两项，也不启动新4层/8层大RRG生成、重新pack/place或大型native测试矩阵。

## 7. 资源隔离与统计

- 不干预当前h。不要在其共享CPU配额中直接跑正式CPU计时并称环境安静。
- 有独立worker优先用独立worker；若没有可靠隔离，则只做只读归档分析，正式新增计时可以不纳入本稿。
- 小图fixture、profile与正式计时分开。
- 三个独立进程各三次重复，不等于九个独立实验或九个benchmark。
- 各cohort只在自身内部做paired比值；汇总跨cohort时每点明确分母、host与scope。
- 只进行计时消融时保持输入、线程、NUMA、数值、范围与QoR条件不变。
- 图中不同证据类型（软件实测、RTL周期、条件大图模型、布局资源）必须有明确区分。
- 不将所有setup/backend/导出stalls直接相加；重叠区间以实际时间线为准。

## 8. 建议正文结构与六页预算

| 内容 | 建议页数 |
|---|---:|
| Introduction：四段+三项贡献 | 0.70 |
| Problem / motivation / closest work | 0.80 |
| Dependency-aware two-granularity construction | 1.60 |
| Finite heterogeneous/FPGA mapping | 0.80 |
| Evaluation：主结果、机制、QoR、适用边界 | 1.80 |
| Limitations / conclusion / 必需披露 | 0.30 |
| 合计 | 6.00 |

这是版面预算，不是要求缩小字体。根据真实排版微调；参考文献另页。

优先图表：
1. 逻辑sample身份与两级依赖示意，说明跨层/相对坐标为何不能丢失。
2. Group/Flat/Pipeline 核数曲线和受控对照；不画伪造任务时间线。
3. shift0/20 波次—工作量—时间归因，旧cohort与新native结果明确分开。
4. 紧凑主表：native E2/Process；另一个小表列map/QoR和硬件证据边界。

方法正文少用内部轮次名、未证明的诊断flag和数千条receipt统计。硬件仅列选定配置和相关失败边界，不将所有f/g/h修复历史逐项写进正文。

## 9. 不能写的主张与积极替换

| 不支持的写法 | 可采用的写法 |
|---|---|
| 所有已有方法都不能支持3D | 既有3D架构/CAD工作提供基础，本文优化该流程中的指定构建阶段 |
| 前人并行都牺牲等价性 | 在特定native表项语义下建立跨sample重排条件，并为ALT另行定义规则 |
| 首个bucket/atomicMin加速器 | 针对layer/source-relative lookahead的两级依赖分解与整对代价波次执行 |
| 无质量损失 | 指定已测路由中CPD/WL观测值与合法性检查；另列congestion差异 |
| FPGA比CPU快1.4倍 | 200MHz与指定外存服务假设下的条件模型比值；正式实现资格未取得 |
| 所有场景都快 | 指明大案例收益，并保留小图启动/准备开销负例 |
| 603次证明广泛泛化 | 明确独立RRG/架构/电路/seed与重复进程的数量 |
| 缓存无用 | 兼容缓存应复用；本文针对首次构建/输入不兼容导致的构建 |

不在 Introduction 中不断自我削弱；但关键限制在首次相关结果出现时就要清楚。不能将硬件时序未通过藏在artifact。

## 10. 实际交付与结束条件

交付到独立paper修订分支，保持旧submission目录可恢复：

- `THESIS_AND_POSITIONING.md`：一句主命题、三项贡献、最近相关工作与适用性。
- `CLAIM_EVIDENCE_MATRIX.csv`：每一主张的实现/数据/统计/范围/反例。
- `SUPPLEMENT_PLAN_FROZEN.json`：新增输入/arm/资源/失败策略预先冻结；允许无新增实验。
- 可复算的机制图表脚本及源数据binding。
- 如有新增实验：完整正负结果、输出、native资格和同cohort统计。
- 改写Introduction、摘要、方法开头与conclusion；报告叙事变更，不篡改历史证据。
- 6+1页PDF、匿名源码包、作者审核项、AI使用披露更新。
- 保留h监控与终态链；h结果只按实际资格更新，不预填成功结果。

完成P0并补齐一个最重要缺口后，优先停止扩展并完成通读与提交检查。不能用新实验的完成作为整篇稿件交付的阻塞条件。

## 11. 审阅依据

冻结稿确切路径：
- `accel/lookahead/fpga_cpu_primary/submission/sections/introduction.tex`
- `.../sections/native_results.tex`
- `.../sections/fpga_architecture.tex`
- `.../sections/conditional_model.tex`
- `.../sections/methods.tex`
- `.../tables/qor.tex`
- `.../references.bib`
- `paper/dac2027/tables/expanded_flat.tex`
- `docs/lookahead_accel_round6_screen.md`

注意省略号仅用于上面的阅读索引：实际完整前缀均为
`accel/lookahead/fpga_cpu_primary/submission`，执行脚本不可使用字面量省略号。

本任务书没有运行新增solver、CUDA或FPGA实验；其新数字仅是上述冻结记录的算术复核。未经新增验证的实验与效果均是候选方案。
