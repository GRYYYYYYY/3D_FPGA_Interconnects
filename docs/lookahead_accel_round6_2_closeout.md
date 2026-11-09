# R6.2 原生证据与硬件服务结项

基线 e68ff9584324deb3de808815c0bc7f35ac3fed23；分支 accel/lookahead-round6_2-closeout-20261110。原始证据：results/lookahead_r6_2_20261109T191213Z；可提交的小型快照位于其 evidence_snapshot/。

本轮严格 CPU 与 ALT 扩展分开。原始表示 shift20 复用 R6.1 CPU/live CUDA，未修改 STRICT、旧 golden、main、历史实验或任务包。compact/direct 的 native 资格不继承。

## P0 输入与归因边界

|图|最终 N|最终 E|零入度 CHANZ|零出度 CHANZ|历史 no-fanin 行|
|---|---:|---:|---:|---:|---:|
|s38417|121,180|1,019,215|266|266|229|
|bnn|4,102,608|39,480,616|1338|1338|1315|
|lstm_s2|4,166,724|40,142,314|1350|1350|新日志保留|

完整 XML SHA256 匹配原输入；旧 geometry 记录的是加入 CHANZ 前的中间计数。所有零入度 CHANZ 都是跨层0–1的 BI_DIR 节点，位于最外顶边/右边；逐节点按实际函数重算四侧坐标，全部无合法相邻 channel。生成器在通道为空时将 gather/scatter 清零，但仍保留可能接 OPIN/IPIN 的候选 link。最终 XML 证实它们既无入边也无出边，不能提供可用路径。完整节点/坐标/方向/层/度数清单在 zero_fanin_chanz.tsv。

s38417 的229行是228个 CHANZ error 加1个 CHANY warning（103827）；BNN 的1315行是1314个 CHANZ error 加1个 CHANZ warning。is_wire 例外只包括 CHANX/CHANY/MUX，且允许分支只打印第一个 warning，解释了集合差异。该诊断子集归类为保留的边界空资源/检查器例外不完整；不把结论扩大为整张 RRG clean。未过滤日志、关闭检查或改图。

R6.1 与 build_cpu_slices 的 route.cpp.o、partition_tree.cpp.o 哈希相同；历史 archive、compile_commands、link、librrgraph 哈希一致。两项包围盒通知修复已进入 C1/ALT。wire map 相同排除了这一对象的变化，未排除 SOURCE/OPIN 派生状态与路由轨迹。已有逐轮 trace 支持通知送达后分区归属分化，但旧无修复并行端点未完全复现 stock，因此不宣称唯一完整根因。本轮无新增归因路由实验。

## P1 预先冻结的真实3D留出

LSTM seed2 在新算法计时前冻结：双层、width120、N=4,166,724<2^23、E=40,142,314、J=40、原始表示 shift20。选择基于规模、既有合法 placement 和未参与 shift/cache/selector 调参。元数据观察器只读取 ABI 并按约定退出86，没有搜索或路由。没有换图、额外 seed 或 selector。两个层分别放置9,110/8,322个块，合格ALT CUDA路由实际使用23,217个不同CHANZ节点（holdout_3d_scope.json）。

新 H100 worker，8个不同物理核、一个NUMA pool、quota10核，所有求解顺序执行；3次独立进程并旋转arm。固定 net/place/RRG，E2 是完整 MapLookahead::compute，Process 包含读图/初始化/构建/路由/FULL/STA，不包含预先生成图或placement；文件缓存不受控，不声称冷盘。候选自身route SHA保持不变，独立 FULL/STA、零overuse，CPD/WL对同组Flat及stock均+5%门槛。诊断capture和完整CPU/CUDA pair核对不进入正式计时。

|案例|方法|E2中位数(s)|Process中位数(s)|n|全部通过|
|---|---|---:|---:|---:|---|
|bnn|pipeline|9.064393|72.456575|3|True|
|lstm_s2|alt_cpu|9.805994|80.815870|3|True|
|lstm_s2|alt_cuda|3.083965|74.304932|3|True|
|lstm_s2|flat|9.965118|80.966792|3|True|
|lstm_s2|pipeline|9.848020|80.866670|3|True|
|lstm_s2|stock|67.360000|139.827246|3|True|
|s38417|pipeline|0.150474|6.023436|3|True|

旧s38417/BNN仅补Pipeline各3次，并核对冻结Flat map/QoR。它们位于新worker，不能与旧worker时间相除；旧BNN GPU加速主张仍限定为已测Flat对照。新LSTM才提供同机Pipeline比较。

|LSTM 对照/候选|范围|配对均值±样本SD|中位数之比|
|---|---|---:|---:|
|stock/alt_cpu|E2_s|6.684±0.304×|6.869×|
|stock/alt_cpu|Process_wall_s|1.691±0.045×|1.730×|
|stock/alt_cuda|E2_s|21.182±1.342×|21.842×|
|stock/alt_cuda|Process_wall_s|1.839±0.049×|1.882×|
|flat/alt_cpu|E2_s|1.013±0.041×|1.016×|
|flat/alt_cpu|Process_wall_s|1.004±0.007×|1.002×|
|flat/alt_cuda|E2_s|3.208±0.165×|3.231×|
|flat/alt_cuda|Process_wall_s|1.092±0.007×|1.090×|
|pipeline/alt_cpu|E2_s|1.012±0.039×|1.004×|
|pipeline/alt_cpu|Process_wall_s|1.006±0.010×|1.001×|
|pipeline/alt_cuda|E2_s|3.207±0.147×|3.193×|
|pipeline/alt_cuda|Process_wall_s|1.094±0.010×|1.088×|
|alt_cpu/alt_cuda|E2_s|3.167±0.071×|3.180×|
|alt_cpu/alt_cuda|Process_wall_s|1.088±0.000×|1.088×|

比值>1表示候选更快；三次进程不是三个独立电路/placement。全部原始样本见 holdout_results.json。Stock E2 来自原生日志的0.01s精度；其它E2使用高精度计时输出，打印精度不等于测量准确度。

|LSTM map对照|条目|delay差异|congestion差异|missing差异|
|---|---:|---:|---:|---:|
|pipeline_vs_flat|459684|0|0|0|
|stock_vs_flat|459684|0|0|0|
|alt_cpu_vs_flat|459684|0|23111|0|
|alt_cuda_vs_alt_cpu|459684|0|0|0|

|LSTM资格臂|CPD(ns)|wirelength|路由迭代|
|---|---:|---:|---:|
|stock|11.7483|1713833|22|
|flat|11.7483|1714423|20|
|pipeline|11.7483|1714423|20|
|alt_cpu|11.7483|1712223|20|
|alt_cuda|11.7483|1712223|20|

完整live CPU/CUDA输入前缀和输出SHA256相等：True。sample输出与native map是不同对象。旧map的166/24434个congestion差异和旧离线BNN133798个sample差异均保留；不宣称STRICT逐位等价。

## P2 同进程阶段与唯一优化决策

旧BNN Flat/CUDA E2中位数之比3.348×、Process1.095×；同一批原样本的配对均值±SD为3.274±0.222×和1.091±0.011×。s38417 CUDA负结果保持，ALT CPU更适合其构建，但stock完整Process仍最快。统计改口径没有重跑历史实验，也不混合host。

旧BNN repeat1：E2=3.104359912s，conversion=1.334836056s，prepare=0.876456587s，E1=0.363794840s，E2内/LA_LIVE外=0.512592457s，Process=67.304850295s。E1占11.72%；仅消除E1而其他项不变，条件上限是E2 1.132744×、Process1.005434×。native_stage_attribution.json逐进程验证父子分区，没有相加不同列中位数。

仅一次非正式BNN画像，kernel phase profiling关闭；细分CSR分配/构造、dense mapping、输入/targets准备、首次context/capacity、device分配与H2D。E1/service仍在最终ABI memcpy前结束，E2包含handoff，未暗改历史范围。

画像原始行：

    R62_INPUT_PREP numeric_validation_s=0.009926065 target_count_s=0.256312932
    R62_TRANSFERS device_allocation_s=0.001523183 H2D_s=0.118766436
    R62_PREPARE validation_targets_s=0.266307122 context_capacity_s=0.400624830 device_alloc_h2d_s=0.120343338 prepare_s=0.787265559
    R61_BACKEND backend=CUDA shift=20 representation=original E1_wall_s=0.365164475 complete=1 fallback=0 device=0 pci_bus=0000:87:00.0 stats=not_collected device_name=NVIDIA H100 80GB HBM3
    R62_CONVERSION graph_csr_allocation_copy_s=0.619274104 dense_mapping_job_cost_s=0.811779686 output_allocation_s=0.003938035 conversion_s=1.435082386
    LA_LIVE kind=2 samples=40 contexts=8 conversion_s=1.435082386 prepare_s=0.787265559 resident_s=0.362987795 readback_s=0.002176585 release_s=0.003532469 service_s=1.159345893 merge_s=0.006449142 total_s=2.605129243 cold_service=1
    R61_NATIVE_BUILD scope_version=R6_1_NATIVE_BUILD_V1 E2_wall_s=3.142659651

P2状态：completed_qualified_measured。Profile confirms dense mapping construction0.811779686s is the largest actionable slice. Pre-index IPIN IDs once and bulk-initialize the same qid*N dense buffer; no layout/value/semantics change. Only this one candidate is implemented.

|唯一优化 原始/候选|范围|配对均值±SD|中位数之比|
|---|---|---:|---:|
|s38417|E2_s|0.983±0.085×|1.014×|
|s38417|Process_wall_s|1.014±0.032×|0.992×|
|bnn|E2_s|1.082±0.037×|1.093×|
|bnn|Process_wall_s|1.009±0.019×|1.007×|

唯一候选为 ORIGINAL_DENSE_IPIN_FILL_V1：先建立IPIN索引，再填充预分配的原始qid×N数组，所有输入/输出字节与冻结R6.1相同。worker中的reserve仅为候选槽名称。两个旧native case的CPU/CUDA共四项受影响资格通过；性能只测三次新旧CUDA配对，未作CPU优化性能主张。新LSTM没有继承这个优化的资格。负结果不触发第二种优化。

s38417 E2_s: 0.983±0.085×（三对方向不一致，未证明一致收益）。 s38417 Process_wall_s: 1.014±0.032×（三对方向不一致，未证明一致收益）。 bnn E2_s: 1.082±0.037×（三对均加速）。 bnn Process_wall_s: 1.009±0.019×（三对方向不一致，未证明一致收益）。 唯一候选保留为独立实验，不改默认路径；本轮P2到此结束。

首次候选编译因输出相对路径与编译工作目录不一致而失败；保留完整日志并仅修正路径，以相同候选源码重新构建成功。没有运行失败ELF，没有追加优化方案。汇总阶段还修正了launch-request哈希字段误指向capture文件的问题；校验器发现并阻止该错误进入最终快照，修正记录见postprocessing_correction.json，原始实验记录未变。

## H0/H1 有限资源与服务停止

实际Vivado2022.2只读查询U280：960 URAM、2016 BRAM36、3 SLR。XRT发现0 FPGA，platforminfo发现0平台。会话已关闭；无可复用且校准范围清楚的32B随机whole-pair RMW服务设施。未启动HLS/RTL/OOC、探针或新全图缓存重放。

URAM为4096×72，16MiB members一字一member需1024个，超过整片960；双member打包需512，仍要解决部分写/RAW/端口。[AMD UG573](https://www.amd.com/content/dam/xilinx/support/documents/user_guides/ug573-ultrascale-memory-resources.pdf)

参考base_1的SLR0有320 URAM与600 BRAM36，约13.887MiB，放不下全部22.043MiB；文档不是当前安装shell的可用配额。[AMD UG1120](https://docs.amd.com/r/en-US/ug1120-alveo-platforms/U280-Gen3x16-XDMA-base_1-Platform)

明确容量例子为656 URAM、1217 BRAM36、32768 LUTRAM及512 bitmap FF，仍缺关联查找、LRU、控制、跨SLR流水与shell预算。每物理bank32MSHR/16dirty buffer/64request/64response是有限接口提案，未实现或验证II。若把32bit tag、7bit LRU rank与valid/dirty全放FF，需2,686,976，超过整片2,607,360。64×8 qid-bank状态不等于512个物理服务端口。不同映射仍unknown，未换cache策略或借用命中率证明硬件。

32B对齐事务、masked write和读写切换需实际服务证据。[AMD PG276](https://docs.amd.com/r/en-US/pg276-axi-hbm/AXI-Considerations)

固定0.309712337s门槛来自完整离线compact CUDA，和original native E2分开。proposal的36,545,890,272B对应117.999GB/s打平必要界、147.499GB/s工程余量必要界、4.609G事务/s。118–147.5GB/s仅不满足20%余量，不能据此否定打平；其余图/label/pending/seen/reset/output/drain尚未全计。300ns仅敏感性假设，约1233在途reads。64lanes/200MHz下，非隐藏II≥3失败的是余量，II≥4才失败打平。

最终 UNRESOLVED_NO_SUPPORTED_MEMORY_EVIDENCE；只否定列出的具体容量映射。fpga_superiority_verified=false，board_measured=false。无测得频率/随机RMW服务；H1到此结束，不自动启动下一轮。

## 交付边界

必需JSON均位于本轮结果目录与evidence_snapshot：input_and_baseline_audit、holdout_plan、holdout_results、native_stage_attribution、targeted_optimization、physical_memory_service_contract、hardware_service_decision。完整输入、ELF、源码、对象和route有哈希绑定，所有失败/诊断日志保留。

严格CPU主论文与ALT扩展分开，不将新契约写为严格等价，不从三例推广至所有3D规模；compact/direct仍仅离线，FPGA仅资源/服务必要条件分析。

关闭状态：受管运行43项完成；GPU作业job-24e8ac10-a0a0-45fe-95df-cdb8afc72489为job_succeeded，节点占用0；本地实验与Vivado会话均为0。工作区保全检查通过，旧tracked文件、main和任务包保持不变。
