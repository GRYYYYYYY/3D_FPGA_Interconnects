# 原生接管诊断（2026-10-29）

本轮接续根目录 `HANDOFF.md`，先补测量、真实部分搜索快照和组批证据，再决定策略。默认仍为原生 CPU；未设置 `VPR_HYBRID_LIBRARY` 不启用 GPU。不能把诊断运行或早期独立 target 后端的收益当成原生 GPU 端到端收益。

## 数据与时间口径

GPU ABI 为 3。`H3D_GPU_TIMING=1` 才启用 CUDA events 和显式搜索完成等待；此配置用于诊断，会改变调用开销。每个 update/execute 批次只有一个唯一批次记录，位于 `hybrid.json.batches.csv`。查询记录通过 `batch_id` 关联，禁止将查询中重复的 `search_ns`、`update_ns` 直接相加。

- 查询主机时间：初始化、标签/前沿/基本代价整理、服务队列等待、GPU 后的路径/前缀/代价验证及标签提交。
- 批次主机时间：状态日志 drain、输入描述符整理、更新调用、execute 调用、结果整理，以及设备端分配、各方向复制 API、提交、显式同步和 event 收集。
- CUDA event 时间：状态 H2D、更新 kernel、查询 H2D、搜索 kernel、D2H。默认流上的更新和搜索有明确顺序；更新 kernel 不再仅用提交调用时间代替。
- `hybrid.json.commits.csv` 记录原生树插入、树前缀时序更新、占用更新和标签清理时间，按查询序号关联。整网 net delay 和迭代 STA 仍属于 VPR 路由阶段，不能误称已全部计入逐连接接管时间。

主机时长与设备事件区间是两个重叠的视角，不能相加。普通主机缓冲区的复制 event 区间可能包括 staging 或主机提交造成的空隙，不能当成硬件 DMA 带宽测量。显式等待时间主要包含内核运行，不是额外可消除的纯同步成本。字节数是 API/逻辑负载，不是链路实测流量。

完整进程、路由阶段、统一独立回验后的 workflow 沿用旧口径。资源图加载包括解析和建图；lookahead 构建另列。捕获和状态回放的诊断耗时从配对交接时间中单列，不从完整 VPR 进程时间中隐去。所有带 `--diagnostics`、捕获或有限接管的运行标记 diagnostic，不能被报告器提升为加速候选。

## 真实接管快照

`H3DTAK2` 与旧的 `H3DNQR1` 不同。文件保存图和模型版本、完整占用/历史、待应用稀疏增量、所有修改过的标签与前驱、原始堆顺序（含过期条目，省略无用 sentinel）、活跃前沿、树节点的父节点/延迟/RC/可展开标记、关键度、目标与边界、原生浮点参数、网络/引脚/迭代及堆 arity。图与模型各写一次，最终由清单 SHA256 绑定。v2 还记录全部原生 cost params（包括未用于串行搜索的 post-target 参数及可选 delay budget 字段）。

捕获仅允许串行 `pair` 或无 GPU 的 `capture` 模式。按接管序号固定间隔采样并设数量上限，选择发生在观察 CPU/GPU 胜负之前。CPU 重复搜索直接调用原生 `timing_driven_expand_cheapest`，保存并恢复原始堆、标签、修改列表和统计；采用原生路径清理语义。每次重复的路径/代价必须一致，随后真实 CPU 继续搜索也必须一致。范围仍限已核验的零 RC、非 flat、非 RCV/bus-mux。

`takeover_replay` 从文件恢复 GPU 状态，每次从原始标签和堆重新整理种子、前沿与前驱，再执行更新、搜索、回传及校验。它检查后缀和完整原生前缀。它不使用另写的 CPU 搜索器冒充原生 CPU。CPU 重复时间来自同节点 VPR 捕获时的原生继续搜索。GPU `repeat=-1` 是单列的预热，包含完整状态重置的影响；非负 repeat 才是常驻状态下的重复。离线重放的主机准备/校验与在线 VPR 不完全相同，二者分别报告。捕获前后的缓存效应意味着这些样本不能直接证明生产调度收益。

早期 H3DTAK1 导出误用了 `RouteTreeNode::all_nodes()`，该迭代器不含根，部分只有 SOURCE 的树被导出为空。严格离线校验拒绝了这些快照。对应失败与有效的在线计时保留；没有补造根或放宽验证。H3DTAK2 使用 `RouteTree::all_nodes()`，要求完整树恰有一个根，并重新实测。v2 reader 明确拒绝 v1 文件。

## 组批证据

在原生 `ParallelNetlistRouter` 的实际任务发布和执行处记录分区 ID/深度、当前分区剩余网络数、活跃及待执行分区、仍在处理网络的父分区、活跃连接搜索、所有权等待者和持有者。服务线程在组批截止点记录准确的队列深度和批次大小；其他原子计数是并发采样，不是全局原子快照。`ready_queries` 统计尚未返回的接管调用，可能包含结果完成但调用线程尚未返回的瞬间，准确的可组批数量以 `queue_depth` 为准。

观察分类是可并存的证据：父分区尚未释放子分区、存在保护冲突等待、其他原生搜索尚未达到接管点、分区任务仍排队、或当前证据不足。`expanded_only_conflicts` 只统计本次请求扩大旧树保护范围才引入的冲突，不代表所有保守保护冲突。没有删除或缩小所有权保护，也没有强行并行同树连接。

## 运行与验证

入口：`stage_native_diagnostics.py` → `submit_native_diagnostics.py` → GPU 节点上的 `bootstrap_native_diagnostics.py` / `run_native_diagnostics.py`。基线、pair、batch 对 elliptic/GEMM 使用相同节点、输入与存储条件，每个成功结果均由锁定原 VPR 独立 FULL/STA 回读。接管阈值仍为 2048，batch 上限 4、窗口 50 µs，单查询 cooperative blocks 为 64。

当前节点的 GPU 作业看不到 `global_user` 路径，首次作业在 Python 启动前失败。项目目录直接暂存 GEMM XML 又遇到配额；已保留失败日志，只清理本轮生成的未完成副本。有效工作包只包含必需输入，压缩暂存后在节点本地解压校验；日志记录暂存、解压与归档时间。节点目录是容器 overlay，没有证据将其称为 SSD/NVMe 实验。原始工程和相邻项目没有迁移或修改。

本轮已完成：[实测结论](../results/native_diagnostics_20261029/report.md)、[机器可读验收](../results/native_diagnostics_20261029/acceptance.json)。576 个 H3DTAK2 快照完成 1,728 次原生 CPU 重复及 2,304 条 GPU 路径校验，两个案例最终 CPU 路径与原版一致且通过独立 FULL/STA。默认仍保留 CPU，后续优先分析搜索 kernel 和受保护的原生任务发布；尚无可启用的自动接管规则。

本轮记录在 `results/native_diagnostics_20261029/`；`run.json` 保留最终 v2 作业的提交指针，终态以 `job_registry.json` 为准。五个新作业均已结束，旧格式回放失败和早期启动/预检失败均保留。CUDA 编译来源、二进制和输入清单随工作包冻结，`archive_audit_v2.json` 绑定最终完整归档与逐文件校验结果。
