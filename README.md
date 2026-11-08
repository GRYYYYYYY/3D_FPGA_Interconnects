# 原生并行三维 FPGA 布线与硬件加速原型

> **公开仓库入口（2026-11-07）**：当前原生CPU主线见[论文证据索引](docs/native_cpu_paper_evidence_index.md)、[方法与等价性论证](docs/native_lookahead_method_argument.md)、[主表](docs/native_cpu_paper_tables.md)和[复现说明](docs/native_cpu_paper_reproduction.md)。原生GPU净加速尚未建立；下文较早的独立原型结果采用不同实现与计时范围。
>
> 仓库包含源码、论文材料、轻量结果与图表。大型输入、原始实验输出、环境和二进制保留在本地；完整范围与复现限制见[PUBLICATION.md](PUBLICATION.md)。VTR修改通过[固定版本补丁](vendor_patches/README.md)提供。

2026-11-08 的 [第三轮 lookahead FPGA 实验](docs/lookahead_accel_round3.md) 使用完整小型 3D 图，分别记录 CPU/CUDA 实测、功能 RTL、受限访存 RTL 和核心实现时序。FPGA 胜过各软件基线仍是待验证目标；历史 CPU 论文证据保持原有输入与计时口径。


对应选题 A：**Native Parallel Routing and Hardware Acceleration for Heterogeneous 3D FPGA Interconnects**。

这是独立的可运行研究原型：C++/OpenMP 三维布线器、可选 CUDA 搜索后端、候选代价 HLS 内核、VTR/LaZagna XML 导入、独立路由审计和原生 VPR FULL/STA 回验。相邻项目只作为冻结数据和工具来源，未修改。

此前 [原型加速实验](docs/results.md) 中，新 CUDA 完整进程约 3.65 秒，相对旧 CUDA 加速 16.86×、四线程 CPU 加速 7.91×，路径完全一致且 FULL/STA 通过。2026-10-25 的 [六电路 VPR–GPU 规模实验](docs/scaling_results.md) 已完成：同一 H100 节点测得原 VPR 路由主体从 0.65 到 164.08 秒，当时 GPU 实现没有出现质量约束下的加速交叉点，较大案例暴露全图搜索、状态更新和拥塞收敛瓶颈。FPGA 尚无上板实测。模型与接口见 [设计说明](docs/design.md)。

2026-10-27 新增 [时序驱动目标搜索后端](docs/target_router.md)：`cpu_target` / `cuda_target` 恢复逐连接 STA 派生关键度和树前缀延迟，采用局部窗口、合法停止下界、GPU 常驻占用/历史及稀疏更新，并区分有限拥塞代价与不可达。CUDA 使用 cooperative kernel 在设备端完成搜索迭代。后续增加设备空间索引、span 下界、跨 STA 常驻细化和合法子树保留。完整反馈实验入口为 `scripts/run_target_validation.py`，最新六电路结果入口为 [results/target_finalscale_run.json](results/target_finalscale_run.json)。本后端适用于已检查的零 RC 架构，新目标尚未移植到 HLS。

最新 [修复与实测报告](docs/target_results.md) 已完成六电路双轮复测和独立核验：6/6 合法、5/6 满足 CPD/线长各不超过 5% 的退化预算；CLSTM 的 CPD +9.41% 尚未达标。reduction/GEMM 已在 600 秒路由阶段预算内完成，GEMM 最终 CPD 比 VPR 改善 4.20%，但完整流程仍慢约 2.52 倍。五个规模案例均未端到端加速；小图高拥塞的 elliptic 试跑加速 2.169×、CPD −10.40%、线长 −25.91%。全部反馈、审计、导出、FULL/STA 和失败尝试都计时，规模增长的加速交叉点仍未确立。

最终子树配置已通过 [三次重复确认](results/h3d-target-confirm-subtree-20261027-221003/confirmation.json)：elliptic 完整流程加速 **2.181–2.247×**，中位数为 GPU **76.042 秒**、原 VPR **167.951 秒**，CPD −10.40%、线长 −25.91%，三次最终路径一致。此前整网配置的 [1.409–1.421× 确认](results/h3d-target-confirm5-20261027-211729/confirmation.json) 单独保留。[CPU/CUDA 对照](results/target_cpuref_run.json) 中，整网配置的一次试跑 CUDA 完整流程比 CPU target 快 6.515×，两者都满足相对原 VPR 的 5% 门槛，但 CUDA 的 CPD 比该 CPU 候选长 14.18%，路径不同。这些不同配置和质量口径分别报告。

本轮结果入口为 [results/target_latest.json](results/target_latest.json)，过程与逐项验收见 [工作记录](results/target_improvement_work.json) 和 [验收记录](results/target_improvement_audit.json)。第一轮 4/6 合法、旧算术对照及单轮 10% 质量预算实验仍保留在报告中。

2026-10-28 开始验证 **VPR 原生 CPU–GPU 异构路由**，与上述独立 target 后端分别统计。代码位于 `vendor/vtr_hybrid`（锁定原始 VTR 提交的独立副本）和 `native/`；原生 STA、关键度、MapLookahead、路由树提交及拥塞协商留在 CPU。CPU 超过搜索预算后可把未展开的堆前沿交给常驻 GPU，完整标签保留已搜索路径的代价和前驱。GPU 使用原生浮点目标，不再采用早期原型的整数拥塞代价。

`VPR_HYBRID_MODE=select` 逐查询接管；`pair` 从相同部分搜索状态分别测量原生 CPU 剩余搜索与 GPU 全部交接开销，保留 CPU 路径；`batch` 使用 VPR 的 `--router_algorithm parallel` 和独立 GPU 服务线程，将不同网络的独立查询组批。整网空间所有权覆盖当前搜索框及保留旧树的资源，在 `should_route_net` 读取占用之前取得，持续到拆线、搜索和提交结束；同一棵树的连接保持顺序。占用/历史变化在修改点保存不可变增量，服务线程只在批次之间更新设备状态。`guard` 使用相同所有权保护运行纯 CPU 对照，不加载 CUDA。并行模式目前要求没有非配置跨区资源组、没有随扇出变化的基本代价；CUDA 仅支持已经核验的零 RC 架构和 SM90，其他原生 VPR 用法保持 CPU 路径。

本轮逐项验收见 [hybrid_work.json](results/hybrid_work.json)，完整测量及失败记录见 [native_hybrid_comparison_final.json](results/native_hybrid_comparison_final.json)。真实独立网络组批、CPU/GPU 重叠和原 VPR FULL/STA 回验均已运行：低阈值 softmax 验证出现 95 个多查询批次、最大批次 4，GPU 工作期间 CPU 完成 18,356 个查询。这证明调度确实并发执行，不代表端到端加速。ex5p/softmax 共 60 个迭代屏障及 elliptic 的 168 个屏障通过了全部节点占用/历史状态逐项对照；这些带状态审计的运行只作正确性诊断。

六电路主实验的 VPR **完整进程秒数**如下（包括图加载、路由、原生 FULL/STA；另行回读验证的时间见 JSON）。每行各变体在同一 H100 工作节点顺序运行；固定架构、网表、布局和 RRG。

| 电路 | 原 VPR 单线程 | 选择性 GPU | 原 VPR 四线程 | 批量异构 |
| --- | ---: | ---: | ---: | ---: |
| ex5p | 5.723 | 5.723 | 5.572 | 6.323 |
| softmax | 16.539 | 16.585 | 15.083 | 15.584 |
| CLSTM | 61.542 | 62.491 | 55.882 | 56.690 |
| reduction | 118.263 | 120.320 | 110.448 | 113.604 |
| GEMM | 401.353 | 406.503 | 356.545 | 362.105 |
| elliptic | 167.921 | 600 秒超时 | 150.106 | 旧树所有权检查失败 |

该主实验使用单 CTA 搜索与 2,048 次 CPU 堆弹出接管阈值。前五例选择性版本 CPD 与原串行 VPR 一致；ex5p、softmax、reduction 没有触发 GPU，不能把四线程 CPU 的收益或测量噪声归因于 GPU。CLSTM/GEMM 分别提交了 10/129 个 GPU 搜索结果，仍未抵消交接开销。

elliptic 后续采用 64 个 cooperative blocks、warp 聚合入队并修复保留旧树超出当前搜索框的所有权范围。一次同机选择性比较为 **190.944 秒 vs 原 VPR 159.120 秒**，CPD **10.4304 ns vs 11.2895 ns**，线长 **97,267 vs 99,232**。最新批量比较为 **215.723 秒 vs 原串行 VPR 167.121 秒**，CPD **10.66 ns vs 11.2895 ns**，线长 **97,448 vs 99,232**，均通过 FULL/STA。不同轮次的时间不能拼接计算加速比。相同保护机制的纯 CPU `guard` 在 200 轮后仍有一个超用节点，不能作为加速比分母。原版四线程重复实验中的崩溃、终止及超时另保留在 [CPU 重复记录](results/native_parallel_cpu_repeats_20261028/summary.json)，其本机运行时间不与 H100 时间混算。

**目前没有证明原生异构后端的端到端 GPU 加速。** 六电路大多数原生查询仅数微秒；elliptic 虽有长查询，但能同时调度的独立长查询很少，最新批量运行实际全部为单查询批次。同状态配对测量中单 CTA 的 141 个热查询没有胜出；64-block 的两个配对版本分别为 6/141、15/141 胜出，不能据此建立稳定的接管交叉点。设备占用/历史稀疏更新已降至最新 elliptic 全程约 21.8 MB，但仍有约 964 MB 查询种子等逻辑上传，不能把稀疏状态量称作全部传输量。

因此默认保持原生 CPU：不设置 `VPR_HYBRID_LIBRARY` 时不启用 GPU。2,048 次弹出、最多 4 个查询、50 µs 组批窗口和可选 `H3D_GPU_COOPERATIVE_BLOCKS=64` 均为实验配置，不是已证明更快的自动调度策略。后续若继续优化，应先让同状态配对查询获得可重复的净收益，再启用相应查询类别。此前独立 target 后端在 elliptic 上的约 2.2× 加速单独保留，不能移作本后端的性能结论。

异构实验入口为 `scripts/submit_native_hybrid.py` / `scripts/run_native_hybrid.py`，报告入口为 `scripts/report_native_hybrid.py`。每次提交冻结 VPR 二进制、CUDA 库、源码补丁和脚本，并记录输入哈希。CUDA 库实际构建源码由独立回放构建记录绑定；[完整性审计](results/native_artifact_audit_20261028.json) 验证了 18 份快照、5 个 CUDA 构建及 26 个独立输入。`native_process_seconds` 包含图加载、原生路由、FULL 和 STA；`workflow_seconds` 另包含对所有变体统一执行的锁定原 VPR 独立回读。并行搜索时间是各路由器计时器之和，包含排队/设备等待，属于 worker-seconds，不是并行墙钟时间；最终报告重新解析日志，纠正旧摘要仅取最后一个计时器的问题，原始文件保留。`pair`、全状态审计及 `--max-offloads` 有限接管检查不能作为完整性能结果。

此前采用 [VPR–GPU 规模实验协议](docs/scaling_protocol.md)：六个真实案例、同一 H100 节点顺序测量，
同时记录路由进程、包含导出/FULL/STA 的完整固定端点流程、CPD、线长和失败。
`--tree-objective source` 增加保留源点距离的构树对照，默认仍为 `incremental`。
CPU 试跑和 H100 三轮对照均确认，开关延迟代价配合源点树使 ex5p CPD 降到 6.61819 ns，但线长增至 29,432；
相对原 VPR 分别退化 17.9% 和 49.7%，尚不满足 20% 综合质量预算。该方案也没有获得完整流程加速。
规模实验入口为 `scripts/prepare_scaling.py`、`scripts/run_scaling.py`、`scripts/report_scaling.py`。

## 构建与小例子

依赖 CMake、C++17、Python 3；CPU 并行使用 OpenMP。无需 Python 第三方包。

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4
ctest --test-dir build --output-on-failure
python3 -m unittest discover -s tests -p 'test_*.py' -v

mkdir -p results/demo
build/h3d_route examples/two_tier.rrg examples/two_tier.nets \
  results/demo/route.json --threads 4 --batch 2
python3 scripts/audit.py examples/two_tier.rrg examples/two_tier.nets \
  results/demo/route.json
```

小例子包含两个共享垂直节点、两个 Net 和一个多终端树，能触发并行容量冲突与修复。CLI 返回码：0=成功，2=预算内未完成合法布线，1=输入或运行错误。失败结果照常输出，不能从统计中剔除。

## 已有真实 VTR 数据

本机相邻工程保留了固定版本 VTR 和 ex5p 的两层 Hecate RRG。这里使用同一 RRG 与人工平衡层分配的固定布局；它是软件架构模型与压力布局，不是物理三维芯片。

```bash
python3 scripts/prepare.py \
  --graph ../FPGA_accelerate_FPGA/G_3d_routing/data/derived/ex5p_w100/rr_graph.sqlite \
  --route ../3D_FPGA_routing/results/runs/fixture_ex5p_a0/routed.route \
  --baseline-manifest ../3D_FPGA_routing/results/runs/fixture_ex5p_a0/manifest.json \
  --output data/generated/ex5p_balanced_new

python3 scripts/benchmark.py --case data/generated/ex5p_balanced_new \
  --output results/new_matrix --variants batch_serial parallel portal --repeats 3
```

导入器保留全部有向边、并行边的 switch ID、节点容量和 CHANZ 跨层区间；只从参考 `.route` 提取 SOURCE/SINK 端点，不复用中间路径。`--graph` 也接受 VPR/LaZagna XML。所有输入及转换结果有 SHA256；输出目录必须是新的。

`--limit-nets N` 可做子集实验，manifest 会标明 subset；子集不允许冒充完整电路导回 VPR。`--cost delay_proxy` 使用正整数单位代价加 switch Tdel 的皮秒量化项，仍然不是 RC 时序模型。

## VPR FULL 检查与 STA

在原生 CHANZ SQLite 案例上，将完整候选树转换成 VPR trace，使用锁定的原版 VPR 执行 `--analysis --check_route full`。检查器不会重新布线，验证的是导出的候选路径。打包网表和布局复制到本项目的输出目录。

```bash
python3 scripts/vpr_validate.py \
  --case data/generated/ex5p_balanced \
  --result results/ex5p_matrix/parallel_0.json \
  --vpr-case ../FPGA_accelerate_FPGA/G_3d_routing/data/raw/ex5p_balanced.json \
  --vpr-lock ../FPGA_accelerate_FPGA/G_3d_routing/configs/vpr.lock.json \
  --output results/new_vpr_validation
```

`validation.json` 单独记录 FULL 检查、CPD、原始输入哈希及是否保持不变；独立图审计 JSON 自身仍标为 `vpr_full_check=false`，不能混淆这两层证据。

## GPU 接口

```bash
cmake -S . -B build_cuda -DCMAKE_BUILD_TYPE=Release -DH3D_CUDA=ON
cmake --build build_cuda -j4
ctest --test-dir build_cuda --output-on-failure
build_cuda/h3d_route examples/two_tier.rrg examples/two_tier.nets \
  results/demo/cuda.json --backend cuda --threads 1 --batch 2
```

需要 NVIDIA GPU 和 CUDA Toolkit。本地 CPU 节点没有该设备，启智 H100 已成功编译运行首版 CUDA。CPU 构建请求 `--backend cuda` 会明确失败，不静默退回 CPU。CUDA 测试同时覆盖最短路 oracle、增量多源搜索、拥塞快照切换、并发汇聚和 64 位路径距离。

`--backend cuda` 使用去重活跃前沿和 64 位原子距离松弛。图驻留 GPU；每棵树上传节点占用、历史拥塞和候选掩码，在 GPU 计算边代价。同一代价快照内，后续终端只新增零距离树节点并增量传播；收敛后回溯目标路径，只回传路径边。CPU 负责构树和容量提交。`--backend cuda_dense` 保留首版全图同步松弛，供同机配对测量。两者使用相同整数目标，等代价路径的选择可能不同，需比较 VPR 时序和线长。

启智平台的远端 GPU 可以通过已安装的 `inspire-gpu-submit` 技能和 `qz` 查询、调度。本机没有 GPU 不代表平台没有可用 GPU；查询前需要有效的 `qz login` 设备授权。工作空间、项目、镜像和 GPU 规格应从服务实时查询，不能复用过期 ID。选择含 `nvcc`、CMake、C++ 编译器和 Python 3 的 CUDA 开发镜像，并确认任务能访问本项目与相邻冻结 VPR 数据所在的共享目录。

GPU 工作节点上的统一验证入口如下（输出目录必须不存在）：

```bash
python3 scripts/run_gpu_validation.py --output results/gpu_validation_run1
```

该入口记录设备/驱动/工具链，独立构建 CUDA，执行 oracle、小图 CUDA 布线及完整 ex5p 的单线程 CPU、四线程 CPU、旧 CUDA、新 CUDA 配对实验。每一步保留日志，失败或超时返回非零；默认一轮，可用 `--repeats 3` 增加重复次数。每次布线默认限时 600 秒，修改使用 `--route-timeout`。进程耗时包含初始化和传输；`gpu_metrics` 另记传输字节、活跃节点和轮数，prepare/search 时间是同步完成的主机墙钟时间，不是纯 kernel 时间。

默认 `--vpr-mode deferred`：GPU 计算结束后记录 `gpu_passed_pending_vpr`、FULL 状态为 null，并结束 GPU 作业。随后在有完整 VPR/Tcl 依赖的 CPU 节点执行：

```bash
python3 scripts/complete_gpu_validation.py --run results/gpu_validation_run1 --output results/gpu_validation_run1/host_vpr
```

此步骤验证 GPU 汇总与路径哈希，对每种不同路径执行冻结 VPR FULL/STA，独立保存结果；不会修改原 GPU 记录。只有 CPU 回验通过才算完整闭环。`--vpr-mode local` 可在依赖完整的 GPU 镜像内执行回验；旧 `--skip-vpr` 参数现在等价于延后回验。两个脚本本身均不提交平台作业。

2026-10-23 已经通过该技能登录并查询平台，提交了一次单卡 H100 验证：`job-4d87ce2a-b414-4a91-b696-4874b6182b7d`。任务配置见 [jobs/h100_validation.json](jobs/h100_validation.json)，提交回执及最近查询见 `results/inspire/`；是否运行成功必须查看任务状态和实际验证结果。该次配置使用公共科研项目、1 卡 10 核、CUDA 12.8 NGC 镜像，运行上限 30 分钟。服务实测要求保留时间为正值，且本次官方镜像应传镜像地址；仅通过 CLI dry run 不代表服务接受全部参数。复用配置时重新查询资源，并更换任务名和结果目录，避免重复提交或覆盖。

2026-10-25 优化重提任务 `job-3e9c3f0f-5e0c-4e3e-9b89-c1c827a2fd8d` 已完成 GPU 三轮测量和 CPU 回验。配置见 [jobs/h100_frontier_validation.json](jobs/h100_frontier_validation.json)，最新结果入口为 [results/gpu_latest.json](results/gpu_latest.json)。原失败由 GPU 镜像找不到 Tcl 运行库引起；新任务默认延后 VPR 回验，避免重复出现该环境错误。

## HLS 内核

```bash
python3 scripts/run_hls.py csynth
python3 scripts/run_hls.py cosim
build/test_cost data/generated/ex5p_balanced/candidates.txt
```

使用 2022.2 经典 Tcl 流程，目标 `xcu280-fsvh2892-2L-e`、5 ns。内核是 `load_candidates → compute_cost → store_costs`，输入/输出使用不同 AXI master bundle，阶段间为深度 32 FIFO。旧 `cpu` / `cuda` / `cuda_dense` 与 HLS 共用整数代价定义；新的 target 后端另用时序代价。测试另外实现标量参考公式，覆盖溢出饱和和无效容量。

运行脚本沿用本机相邻工程的 `libudev.so.1` preload，仅作用于 HLS 子进程，不修改系统库。通过 `--binary` 或 `H3D_HLS_BIN` 可以指定其他安装位置。

`H3D_HLS_VECTORS` 可指定候选记录文本，字段为 `base history occupancy capacity present vertical_penalty vertical`。4096 条真实图派生向量使用合成拥塞快照，不能称为捕获的 VPR 运行轨迹。HLS 功能、综合和联合仿真的实际状态见实验结果；没有 XRT 主机驱动、xclbin 或上板性能结果。

## 主要文件

| 文件 | 作用 |
|---|---|
| [src/router.cpp](src/router.cpp) | 多源 Dijkstra、多终端树、稀疏垂直候选、协商拥塞、批次提交 |
| [src/search_cuda.cu](src/search_cuda.cu) | 可选 GPU 同步并行松弛 |
| [src/target_router.cpp](src/target_router.cpp) | 时序树前缀、逐连接关键度、目标窗口及稀疏状态提交 |
| [src/search_target_cuda.cu](src/search_target_cuda.cu) | GPU 优先级区间搜索与设备端协作迭代 |
| [scripts/target_timing.py](scripts/target_timing.py) | 零 RC 延迟侧文件、物理端点映射、原生 STA 反馈 |
| [scripts/target_pipeline.py](scripts/target_pipeline.py) | 多轮布线/FULL/STA、合法检查点选择、全流程计时 |
| [hardware/cost.hpp](hardware/cost.hpp) | 公共整数代价与饱和规则 |
| [hardware/candidate_cost.cpp](hardware/candidate_cost.cpp) | AXI/FIFO HLS 数据流内核 |
| [scripts/prepare.py](scripts/prepare.py) | XML/SQLite 导入、端点抽取与溯源 |
| [scripts/audit.py](scripts/audit.py) | 独立图合法性检查与错误注入验证 |
| [scripts/vpr_validate.py](scripts/vpr_validate.py) | 原生 VPR trace 导出、FULL 检查、STA |
| [scripts/benchmark.py](scripts/benchmark.py) | 顺序执行配对实验，保留失败和完整进程计时 |

## 后续研究

1. 把相邻 `3D_FPGA_routing` 已有的 H3D 启发式 A3/A4 规划器与本项目搜索后端对接，保持 VPR RC 代价和关键度；当前最近邻 CHANZ 候选不等于 H3D 动态规划。
2. 扩展自然三维布局、多电路、垂直密度和配对种子；用 VPR FULL/STA 检查每种新拓扑结果。
3. 已实现目标导向搜索、常驻状态和有限/不可达代价分离；继续减少每终端窗口上传及细粒度调用开销，并以完整反馈流程验证质量约束下的交叉点。
4. HLS 后续加速邻接读取与状态访问，完成 XRT/PCIe/HBM 集成后再测板卡端到端加速。
