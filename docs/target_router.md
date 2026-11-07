# 时序驱动、目标导向的 CPU/CUDA 后端

2026-10-27 实现的 `cpu_target` / `cuda_target` 保留真实三维 RRG 的有向边、并行开关、容量和跨层资源。CPU 协商拥塞并提交每棵树，GPU 并行搜索单个连接。旧 `cpu` / `cuda` / `cuda_dense` 保留用于历史对照。

## 关键度和树前缀

每个连接独立使用 0–990 的整数关键度（分母 1000）。首轮统一为 500；合法候选树导回锁定原版 VPR，执行 FULL/STA 并导出 atom-pin slack。适配器通过 packed.net、固定 placement、物理 pin class 和 SINK PTC 将 slack 映射到 cluster sink，按同一物理连接的最大关键度聚合。全部连接必须有覆盖，缺失、重复、NaN、非 FULL 结果均拒绝。

当前反馈公式为 `clamp(round(-slack / CPD * 1000), 0, 990)`，正无穷 slack 视为无约束、关键度为零。它是本原型的 STA 派生优先级，不等于原 VPR 内部所有时钟、slack 归一化和指数参数的实现。下一轮仅使用自身上一轮合法结果的 STA；基线 VPR 的路径中间节点和 slack 不参与初始化。

树节点记录实际 `source → node` 的累计开关延迟。搜索的每个树上种子以 `criticality × prefix_delay_ps` 初始化，避免把已有慢前缀当成免费路径。新支路禁止进入已有树节点，避免环与无意改写树前缀。代价包含关键度加权的延迟、剩余权重加权的资源长度/当前拥塞/历史拥塞，且每条边严格为正。

延迟侧文件由冻结 RRG 的 switch Tdel 生成，量化到 1 ps。准备脚本检查 node R/C、switch R 和可加性所需的 buffered switch 条件；不支持的 RC 架构直接拒绝。本次六个 Hecate/Koios 案例满足已检查范围。树前缀是该零 RC 模型中的开关延迟和，并未实现一般 RC 树的下游电容更新。最终 CPD 始终来自原生 VPR STA。

## 目标导向搜索与合法停止

CPU 使用带多个非零前缀种子的 A*。GPU 使用带优先级区间的并行 label-correcting 搜索，按 `g + h` 限制当前展开。只有全部待处理标签的最小下界不小于已知 sink 代价时才结束，不能以首次到达 sink 结束。

原有 `--heuristic hop` 下界来自锚点曼哈顿距离、最大单边跨距和最小合法边代价。当前默认 `span` 在其上取更强下界的最大值。令 `s(v)` 为节点 XYZ 跨度和，`d(v,t)` 为低端锚点的曼哈顿距离。对每个关键度，按所有实际边的零拥塞代价求向下取整的定点比例 `a`，使 `a × (step(u,v) - s(u) + s(v)) ≤ cost(u,v)`；非正分母不约束比例。新增下界为 `floor(a × max(0,d(v,t)-s(v)))`。这扣除了已进入长线段所支付的范围，避免便宜的长通道出口压低全图的距离估计。由三角不等式和边约束可得一致性；测试另外检查实际边上的一致性及独立 Bellman–Ford 最优代价。它仍不是完整 VPR lookahead。

GPU 将轮间循环放入 cooperative kernel，设备上的 grid barrier 替代每轮 CPU 往返。主机逐轮版本保留为测试对照。构建开启 CUDA separate compilation/device link；设备必须支持 cooperative launch。驻留 block 数按 occupancy 限制，不能随图规模无限增加。

空间索引从 source/sink 包围盒及 margin 获取局部窗口，保留所有层。当前 CUDA 默认将 CSR tile 索引常驻 GPU，按 16 字节 XY 包围盒生成窗口；跨多个 tile 的节点由窗口交集的最小 XY tile 唯一初始化。`--window-mode host` 保留原主机窗口实现用于对照。窗口不可达时逐步扩大到全图；拥塞迭代也逐步扩大窗口，停滞时轮转网络顺序并对冲突网络解除窗口限制。这避免“局部可达但局部无法容纳所有网络”时永远不扩窗。

当前默认 `--incremental-congestion 1` 保留未经过超用资源的终端及其祖先，只重建受到拥塞影响的分支，并保留实际源到树节点延迟。保留集合按终端回溯裁剪，避免留下非终端悬空叶子。全局停滞恢复仍允许完整重布。`--incremental-congestion 0` 保留此前整网 rip-up 策略；六电路实测状态见 `results/target_subtree_run.json`，不能将小图测试当成完整电路验收。

搜索 oracle 检查的是给定窗口、占用快照和树前缀下的最小目标代价。窗口本身属于启发式：局部搜索成功不等于全图无约束最优。也不保证协商拥塞能在指定迭代上限内找到合法全局解。

## 常驻状态与有限代价

在每个布线进程内，图、occupancy、history 和树状态数组驻留 GPU。CPU 只上传 rip-up、commit、历史惩罚变更涉及的去重节点，记录 `{node, occupancy, history}`；树按新增前缀增量更新。窗口采用代际标记，只初始化当前窗口，避免逐网清零全图。

`state_updates × 12` 是稀疏占用/历史上传字节数；`h2d_bytes` 还含静态图、空间索引、窗口描述和树前缀。设备窗口的 `window_h2d_bytes` 统计包围盒参数的逻辑载荷，未声称测量 CUDA 驱动全部实际 PCIe 流量。`spatial_index_bytes` 单列首次索引上传；主机窗口模式继续统计完整节点编号列表。

## 跨 STA 反馈的常驻细化

`scripts/run_target_validation.py --incremental --epochs N` 通过 `TargetSession` 保持同一个 C++ 进程和 GPU 上下文。每轮候选先写文件并发送检查点确认，Python 独立审计、导出、执行原生 FULL/STA，再发送自身关键度文件和下一候选路径。进程退出码与检查点状态分开记录；每次路由阶段单独执行既有超时，所有阶段墙钟都累计到完整流程。

细化默认选择关键度不低于 0.7 的最多 2048 个连接，按关键度排序；可用 `--refine-threshold` / `--refine-connections` 调整。保留未选终端的全部祖先，仅删除选中连接独占的分支。下一轮不重新加载 RRG 或空间索引。

`--refine-mode legal` 使用硬容量搜索；只有所有选中连接的模型延迟均不增加且至少一个严格减少时才接受该网的新树，否则恢复原树及占用。此规则可能因其他合法网络占用而无法找到更快路径。elliptic 的双轮、三轮试跑都停留在 CPD +5.40%，增加一轮没有解决该限制。

`--refine-mode negotiate` 允许选中连接暂时占用其他网络已使用的资源，随后只修复冲突分支，并保留安全子树。这样可让非关键连接让出较快路径。每次细化先保留整片合法路由森林；若迭代预算内不能消除超用和未连通，恢复上一合法森林及设备占用，记录失败时的超用/未连通计数。失败细化的全部时间仍计入流程。该模式不保证每条连接的模型延迟都改善，`refinement_accepted` 表示协商收敛后接受的选中连接数量，不是原生 STA 改善数量。最终仍按原生 STA 选择检查点。

完整重布模式继续按 CPD×线长选择合法检查点；增量模式预先规定按最小 CPD、再按线长选择。最终质量仍来自原生 STA，不能由量化模型延迟替代。未指定 `--incremental` 时保留原先每轮新进程、完整重布的对照流程。

## 诊断计时

`--trace-file FILE` 写逐连接 begin/end CSV，保留超时前完成的查询。标准错误每五秒记录查询位置，并分别记录图读取、时序模型、GPU 上下文和空间索引初始化。GPU 指标拆分 CPU 窗口生成、窗口上传/初始化、松弛、回溯、状态更新和树更新；这些是同步阶段的主机墙钟，不是纯 kernel 事件时间。启用逐连接文件的运行属于诊断实验，不用于端到端加速声明。入口为 `scripts/profile_target.py`。

图加载器对外部节点/边 ID 严格递增的输入直接证明唯一性，省去逐项平衡树插入；无序输入继续执行完整重复检查。CSR 顺序和资源字段保持不变。独立审计仍扫描全部 RRG 记录的 ID，只解析候选实际使用的资源字段；导出器批量读取原始 SQLite 资源并保留 switch ID。reduction 的导出文件与旧实现字节相同，审计结果也相同，证据为 `results/target_adapter_equivalence_reduction.json`。这些是主机端开销优化，速度结论必须使用完整同机实验。

旧版的问题是拥塞乘积饱和到“不可达”值，使软惩罚变成禁止通过。新后端将有限边代价上限 `(1<<30)-2` 与 64 位不可达哨兵 `(1<<62)-1` 分离，并限制 present 的增长（默认上限 1000），不会因为软拥塞饱和把边判成不可达。有限惩罚仍可触及上限并失去大小差异；这里没有声称使用无界精度代价。输入范围与树前缀乘积有溢出检查。硬容量禁用只出现在明确请求 hard 模式或容量为零时。

饱和乘法采用 `min(L, min(L,a) * min(L,b))`，对非负整数与 `min(L,a*b)` 等价；`L² < 2^60` 保证中间乘积安全。它替换最初实现中的逐因子 64 位除法，目标函数不变。六电路初始冻结实验使用除法版本，后续独立算术对照使用改写版本，两组耗时分别报告。

## 验证和复现

`tests/test_target.cpp` 用独立 Bellman–Ford 和独立宽整数代价公式检查随机有向图、稀疏状态切换、不同关键度、局部窗口、非零树前缀和 hard/soft 容量。还包含慢前缀/快尾巴、局部可达却拥塞、极大有限惩罚、保留合法子树、移动阻塞网络改善关键连接，以及协商失败后重复恢复森林和设备占用的案例。CUDA 构建同时测试持久化与主机逐轮两种 GPU 搜索。完整电路另经独立图审计及原生 FULL/STA。

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4
ctest --test-dir build --output-on-failure
python3 -m unittest discover -s tests -p 'test_target_timing.py' -v

# 已准备的冻结 ex5p 数据；输出文件使用新路径。
build/h3d_route data/scaling_20261025/ex5p/unit/graph.rrg \
  data/scaling_20261025/ex5p/unit/nets.txt results/new_target.json \
  --backend cpu_target --delay-file data/target_20261027/ex5p/delays.txt \
  --present 1 --present-cap 1000 --iterations 200 --bbox-margin 3
```

CUDA 节点上增加 `-DH3D_CUDA=ON`，路由参数改为 `--backend cuda_target`。完整同机实验入口：

```bash
python3 scripts/run_target_validation.py \
  --suite jobs/target_suite_20261027.json \
  --runtime data/vpr_runtime_20261025/runtime.json \
  --vpr-lock ../FPGA_accelerate_FPGA/G_3d_routing/configs/vpr.lock.json \
  --output results/new_target_validation \
  --epochs 2 --repeats 1 --timeout 600 --skip-legacy --incremental \
  --congestion-mode subtree --refine-mode negotiate
python3 scripts/report_target.py --run results/new_target_validation
```

输出目录必须不存在。脚本先执行 GPU oracle、Python 会话测试和运行库检查，再测同一 worker 的 VPR 和新 CUDA；去掉 `--skip-legacy` 可加入旧 CUDA，`--cpu-reference` 可加入第一个案例的 CPU 参考。若多次重复，变体顺序轮转。失败试跑保留且不继续重复。

`--epochs 1` 固定执行单轮，关键度统一初始化为 0.5，仅在结束后做 FULL/STA 验证，没有 STA 反馈重布线。它是独立的速度/质量配置，不能称为双轮反馈模式。`--skip-legacy` 可用于只比较 VPR 与新目标的确认实验；已完成的旧版对照仍保留在原记录中。

每轮候选都独立导出并回验，按上述模式预声明的规则选择合法检查点；若后续轮次失败，可保留此前合法树。计时必须累计所有尝试，包括失败细化、导出和 FULL/STA。选中某轮的 CPD 不允许配上该轮单独耗时来宣称端到端加速。离线投影和侧文件准备单独记录。`scripts/verify_target_run.py --run DIR` 复核候选哈希、原生日志、实际打包网表/布局副本、同一原生 RRG 和参数、检查点选择、跨轮时间及常驻进程复用。原始大输入的全量哈希使用运行器的前后校验记录。

报告同时输出 `workflow_phases.json`，将所有反馈轮次拆为路由进程、审计、导出、原生 FULL/STA、反馈生成和其他开销。`--plot` 需要可选的 matplotlib，输出独立 PNG/SVG；本次绘图环境为 `.venv-report/bin/python`，不会改变布线节点环境。图中按 RRG 节点数和原 VPR 布线耗时分别展示实测加速点，不连线推断未测量的交叉点。

三次 elliptic 质量确认使用 `--congestion-mode full`；最新六电路规模试跑使用 `subtree`，其余均来自同一冻结代码。两种初始修复策略分别报告，不把两组中各自较好的速度或质量拼成单一配置。确认完成后运行 `python3 scripts/check_target_confirmation.py --pointer results/target_confirm5_run.json`；检查预声明协议哈希、轮转顺序、固定输入、原生回验和每一组的完整流程速度与 5% 质量预算。单次规模试跑不支持稳定性声明。

这次修改涉及 C++/CUDA 算法和验证适配器。HLS 候选代价内核仍使用旧目标；尚未把新的时序代价或搜索状态映射到 FPGA，也没有新增板卡性能结论。
