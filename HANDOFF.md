# 三维 FPGA 原生 CPU GPU 异构布线交接

## 集中补充113项已完成并复核（2026-11-05 12:20 UTC，最新终态）

用户授权“执行上述建议集中补充项”已完成：直接全局parallel_for原生对照、方法/等价性与任务宽度模型、阶段内存诊断、真正大型二维、统一主表及新目录复现入口。主链85项+大型二维28项=113项，903份产物独立复核。32项完整布线（8资格+24正式）全部原生合法并原版独立FULL/STA；其余81项为63阶段正式+12内存诊断+6pilot，一轮未布通尾部仅说明构建测量有效。两链共四组PDF/SVG/PNG已目视检查。远端owner1794061、旧solver4082089与旧监督4081932均已/proc确认退出；无活动实验或自动后续队列。终态finalization.json位于results/native_flat_baseline_20261105；勿重启任何旧owner/续接脚本。下文所有运行中状态均为历史。

新增大型二维使用原始KOIOS2D架构+BNN，seed1、通道120、目标util0.5，自动选择已有布局；实际177×177、5018311 RR节点，实际deviceutil0.48。无架构修改、人工扩图、换样或扩宽重试。同八物理核0–7，stock也使用原生parallel布线。4资格+12完整正式全部合法，CPD最大增幅0%、线长+0.1077815%，三修复版QoR相同。完整进程中位stock/group/pipeline/flat=105.68/81.46/77.08/79.08秒；配对速度比中位stock→pipeline1.371915、stock→flat1.318078、组内→pipeline1.057560、组内→flat1.030104、flat→pipeline1.026653。完整进程读冻结RR/net/place，不含pack/place或RR生成。

独立阶段正式group/pipeline/flat中位7.76/4.12/4.19秒，组内→pipeline1.901961、组内→flat1.883495、flat→pipeline1.016990（均配对中位，不是中位秒数之比）。完整运行内部flat→pipeline构建比值却为0.988426，故整体小差不能全归于调度。结合主链三维BNN/DLA8/16核flat→pipeline0.989429–1.020408，主要支持等价的跨组并行构建与原生集成，没有建立pipeline普遍独有优势或新调度原语；不改默认、无GPU收益主张。

二维内存入口约2196MiB，group/pipeline/flat观测阶段增长124.727/208.754/209.324MiB；wire标签容量78.966/157.933/157.933MiB、实际工作区4/8/8。4非空组×4样本共16，但两全局实现分配6张组表；样本表上界同为16。pipeline与flat观测峰值仅差0.57MiB，不声称稳定节省。该二维最大采样间隔11.781/5.051/2.163ms；跨主链最大254.124ms，均是近似采样、每臂1次，不是精确峰值/完整工作区/RSS硬上界。

本轮11:59磁盘预检停止发生在下一solver启动前。已完成parent归档去重逻辑回收11.05GiB（另有更早4.576GiB），路径和hash保持，不动历史源。续接只运行8个未启动任务，原计划参数与60GiB下限不变，已完成20条原样保留，未重跑solver。阶段repeat1的pipeline/flat间隔519.84秒，存储操作完全位于空档；完整正式全部此前结束。disk_stop_terminal.json、disk_continuation_plan.json/review.json、storage_event_audit.json保留过程；共享宿主/该暂停限制对小差异的因果解释。归档硬链接不可原地编辑。

终态依据：两链analysis.json、independent_review.json、review.md、conclusions.json、figures.json；大型二维terminal_owner_probe.json确认退出。统一docs/native_cpu_paper_tables.md/json现18条完整进程行，不跨样本/宿主/权重混总比；docs/native_cpu_paper_evidence_index.md为最新总索引；方法native_lookahead_method_argument.md、复现native_cpu_paper_reproduction.md。reproduce_native_lookahead.py支持--include-stock加入同预算原版，默认仅预览（已验证BNN2D四臂命令/env且无新solver/目录），--execute仅在新目录运行，stock不支持memory诊断。旧查新文档已注明历史时效，本轮未重新检索文献。

剩余研究边界：严格物理CPU独占仍未证明；完整分配开销和精确峰值未建立；大型二维新增只有1电路/1布局；首创性与论文录用充分性不能由性能独立保证。不要把所有113项称为合法路由，不要把阶段加速称全编译加速，不要将pipeline primitive写成新算法。


## 大型二维磁盘预检停止后的显式接续（2026-11-05 12:10 UTC，当前）

主链85项已复核见下一节。大型二维BNN已完成4资格+12完整正式，全部原生合法并独立FULL/STA；18组配对质量均过门，最大CPD增幅0%、线长+0.1077815%。177×177、5018311 RR节点。阶段正式完成前4项后，11:59在第五项component_formal_bnn_2d_w8_r1_flat启动前因60GiB磁盘下限停止；没有solver启动/日志/返回码，该目录只有输入文件。原solver4082089和监督4081932已远端/proc确认退出，stopped_owner_probe.json为据。

本轮已完成parent归档的剩余BNN/DLA网表逐份核验后硬链接去重，逻辑回收11.051GiB，所有路径和SHA256不变；不触及历史源文件。completed_input_deduplication_remaining.json记录，档案不可原地编辑。原disk_stop_terminal.json/plan保持，输入目录移存preflight_disk_stop/。新disk_continuation_plan.json绑定续接与审核脚本；唯一owner1794061，scripts/continue_native_large2d_disk.py run，远端fpgaacc2。只接续8个未启动的原计划测量，已完成20条逐字保留，原参数、执行顺序、60GiB保留线未变，无solver重试。实时summary.json、disk_continuation_status.json、disk_continuation_receipt.json；旧supervisor_continuation为停止历史，不可重启。

新owner完成后顺序执行独立review、Agg图表和统一主表，仍需主模型检查科学结论/PNG及远端退出。磁盘去重发生在停止后、不与测量重叠；新的时间间隔应如实记录，不把不同批次称连续无中断。qz刷新曾因认证域走proxy返回EOF，把keycloak-inspire-prod.sii.edu.cn加入NO_PROXY后恢复，无需重新授权；不要输出访问URL/token。当前还有8项后续计时/内存及终态检查未完成。


## flat主链85项已复核；真正大型二维BNN后续运行中（2026-11-05 11:09 UTC，当前）

results/native_flat_baseline_20261105主链已完成，原solver PID1655318与原监督PID2333060均已通过远端/proc确认退出。独立review通过85项、663份产物、18份不同输入：54正式阶段、9内存诊断、6pilot均构建有效（共69个一轮路由尾部不算合法流程），4资格+12clma完整正式全部合法且原版FULL/STA，map与命令/env/CPU预算一致。analysis.json、independent_review.json、conclusions.json、review.md为依据。两组PDF/SVG/PNG已生成且目视检查。

核心新结果：BNN8核组内/pipeline/flat中位17.41/9.38/9.36秒，16核17.83/5.38/5.50；DLA8核34.66/18.99/19.50，16核34.01/10.84/10.89。flat→pipeline配对比值中位依次0.989429、1.018587、1.020408、1.001845，不是中位时间之比。两种全局实现相近，不能主张pipeline明显独有优势；主要支持跨组并行增量。clma原版→pipeline/flat完整进程1.094447×/1.120403×，flat→pipeline0.993234×且单次跨1；小进程/三重复/共享宿主边界保留。

阶段RSS诊断已揭示RR加载历史峰值掩盖的后续增长：BNN组内/pipeline/flat相对入口增长162.0/231.7/241.1MiB；DLA238.4/378.4/393.0MiB。wire标签容量组内→全局64.56→129.11MiB、121.98→243.96MiB，实际工作区4→8。pipeline样本表上界16，flat40，但观测峰值差仅约9.4/14.8MiB，不能宣传大幅RSS节省。每臂仅1诊断、statm近似且最大观测间隔254.124ms，不能称精确峰值/严格2ms采样或硬上界。flat原始profile.tokens是共享函数未使用值，实际表界用storage.sample_map_count_bound=S。

原监督在parent review通过后，绘图因继承Jupyter的MPLBACKEND=module://matplotlib_inline.backend_inline而失败；没有启动BNN2D。原supervisor.json/plan保持。新plot_native_flat_baseline_v2.py在导入前设置Agg、为图例留空间，已在本机重绘并目视检查；原实验和review未重跑。显式supervisor_continuation_plan.json记录原因与绑定。当前唯一监督PID4081932，scripts/continue_native_flat_supervisor.py run；看supervisor_continuation.json而非旧supervisor.json。无luna接口、无自动重试。

监督于11:08:23Z唯一启动results/native_large2d_followup_20261105，solver owner PID4082089，fpgaacc2，回执remote_receipt.json；已进入BNN二维原生pack/place准备。当前约130310个逻辑块打包完成，最终网格/准备成功与否以日志和summary为准。该计划原始2d_architecture.xml/BNN、seed1、通道120、util0.5、自动选择原架构已有布局，不改架构/扩宽重试。准备1800秒；4资格、条件12完整正式、9正式阶段、3内存诊断。stock资格失败跳过其余完整流程；准备失败跳过全部28项并记录失败。当前尚未完成大型二维验证。监督正常结束后自动独立review、v2绘图、重建统一主表，仍需主模型科学解释及图表目视。

11:22更新：BNN二维准备已通过，一轮尾部rc2按协议保留；自动选择原架构125x125命名布局，实际177×177、5018311个RR节点、实际device utilization0.48（目标0.50）。准备原版lookahead28.28秒不计正式。stock/per_group/pipeline三资格已原生+独立FULL/STA通过，flat资格运行中，以实时summary为准。HDD余量曾69GiB，预计全部副本逼近60GiB保留线；已对**本轮已完成主链**10份相同DLA packed.net做哈希核验后硬链接去重（保留一份、替换9份），仅新归档输入、无历史源文件变化，全部路径/字节hash保持，逻辑回收4.576GiB，操作后余量约72GiB。completed_input_deduplication.json记录每个旧/新inode及前后hash；这些冻结归档不可原地编辑。操作结束时大型二维仍在资格阶段，没有重跑solver，也未降低60GiB门槛。

docs/native_lookahead_method_argument.md已补非NaN记录代价条件下的保序证明、40任务离散波次模型（16核等长任务自身1核上限13.33×，不是16×）、Amdahl/缓存边界和存储口径。docs/native_cpu_paper_tables.md/json已纳入主链新结果（13条完整进程表行），不把历史不同样本/宿主/计时边界混算。复现见docs/native_cpu_paper_reproduction.md，默认preview不启动solver。待大型二维终态后更新总索引/HANDOFF；默认不变、严格CPU独占仍未证实，无GPU收益或新调度原语主张。下节旧“主链运行中”状态过时，勿重启任何旧owner。

## 直接flat对照、阶段内存与大型二维补充执行中（2026-11-05，当前优先）

用户授权“执行上述建议集中补充项”。新主目录results/native_flat_baseline_20261105；独立二进制bin/vpr_flat SHA256 ad49e82282e8805271030091292086dd38708537501fcabbc6cce9cb1a948cd9。未改vendor源码/旧archive/默认ELF。build_native_flat_baseline.py通过原Make编译/链接参数隔离替换两个对象，源码、patch、构建绑定齐全，无编译警告。

新增VPR_CPU_GLOBAL_SCHEDULER=flat：全部原始组/样本一次parallel_for，随后原序归并；与pipeline使用相同任务选择、flood、表示和同ELF。VPR_CPU_STAGE_MEMORY仅独立诊断启用，在MapLookahead::compute内2ms目标间隔读取statm，记录入口/出口/观测峰值/采样间隔；另记标签vector容量及中间表结构计数，不含队列、分配器或单元条目负载。未改热路径TLS结构体。正式计时关闭诊断。

主协议plan.json：6小图pilot、4clma完整资格、条件12完整正式、54阶段正式（BNN/DLA/clma×8/16核×组内/pipeline/flat×3重复）、9内存诊断；另1次clma准备不计正式。fpgaacc2独立实例共享宿主，55CPU时间配额，同NUMA物理核0–15；仍非物理独占。6pilot均map等价，clma4资格+12正式均合法且原版独立FULL/STA，质量过门。clma自动44×44、阶段仍不足一秒，只是更大输入电路，不代表高成本二维RR。大图正式进行中，具体完成数读summary，不提前解读首轮接近的flat/pipeline时间。

初次owner PID1567168在stock clma已合法布通后因记录顺序停止：log_evidence依赖尚未写出的measurement.json，使final_overused_nodes为None；原生26轮末过用0。原script/plan和attempt1_terminal.json保持冻结。显式continuation_plan.json与continue_native_flat_baseline.py仅补stock缺少的独立检查，再续原任务；没有重跑已完成solver。旧PID已核验退出。当前唯一solver owner PID1655318，日志continuation_owner.log，回执continuation_receipt.json；勿重启旧run/continuation。

唯一远端依赖监督PID2333060，scripts/supervise_native_flat_baseline.py run；supervisor_plan.json绑定全部脚本，supervisor.json是实时状态，supervisor_receipt.json确认宿主。30秒观察，无重试/取消/重投。主链正常结束且owner退出后自动运行review_native_flat_baseline.py独立复核、plot_native_flat_baseline.py生成PDF/SVG/PNG、assemble_native_cpu_paper.py主表；审核通过才单次启动下述大型二维后续。没有luna委派接口，使用确定性监督，不能声称模型切换。qz一次GetNotebookAccessUrl瞬时失败后只读复查成功，无登录过期、不需新授权；后续观察优先共享文件，远端接入用inspect_native_cpu_notebooks.execute，token不落盘。

已冻结后续results/native_large2d_followup_20261105/plan.json，尚须主链终态复核才运行。使用现存Beyond-Flatland原始2d_architecture.xml（无显式layer，原始二维）与BNN127676 .names/125个two_mult_18x19，seed1、通道120、util0.5，自动选择原架构既有fixed_layout；不改架构、不人为扩宽。准备1800秒上限，随后4资格、条件12完整正式、9阶段正式、3内存诊断，同8核。stock资格失败跳过其余完整流程，仍可做有效构建；准备失败跳过28项，无换样/重试。runner run_native_large2d_followup.py；监督器负责唯一提交，恢复时必须查其状态和后续remote_receipt，不能另行提交。

方法已写docs/native_lookahead_method_argument.md（含非NaN记录代价前提下原序最小值等价、表存储关系、贡献边界）；统一表docs/native_cpu_paper_tables.md/json只纳入独立复核产物；docs/native_cpu_paper_reproduction.md与reproduce_native_lookahead.py提供新目录复现（默认仅预览，已验证不启动solver）。review脚本同时支持主链与大型二维目录，监督器终态仍需要主模型检查科学结论、图表目视、远端PID退出后更新本节。当前结果不算全部完成，不改默认，不主张pipeline特有优势或GPU收益。以下旧“无活动任务/缺flat未实施”状态均以本节为准。

## 论文扩展性90+6项已完成并独立复核（2026-11-05，最新终态）

用户随后指定fpgaacc2（e6e06586-4338-4d74-8ecc-72bfa719011c）用于可连接时的探索任务。已通过qz/Jupyter短寿命自有kernel成功连接，核验共享工作目录；物理宿主cpu-nat-465，55CPU时间配额/500GiB，128逻辑/64物理核可见，cpuset0-127、partition=member，未证实物理核独占。3秒宿主忙碌快照约3.9%，仅即时观察。后续探索优先此实例，同NUMA固定物理核集合、双方同预算顺序测量；仍标“另一低负载共享CPU实例”，不称独占CPU。platform/fpgaacc2_exploration_probe.json、fpgaacc2_provider_check.json、fpgaacc2_exploration_policy.json为依据；此探测未启动新solver，已关闭自有kernel，不动其他任务。

results/native_paper_closure_20261105/scaling已于05:36:51Z完成，远端PID2086391已退出且无同runner活动进程，原本机监督PID3393000也已退出。新scripts/review_native_cpu_allocated_scaling.py独立复核通过：90正式+6诊断、582份产物、335项既有输入/source/runtime/ELF及产物绑定、实际命令/env/同NUMA物理核0–15、执行顺序与非重叠、原生timer、map hash和全部配对统计一致。全部96项按预定1轮路由rc2未布通，只计lookahead阶段有效，不计合法路由或全流程加速。independent_review.json、review.md、conclusions.json已写；scaling_review与memory_review的PDF/SVG/PNG已生成并目视检查。

阶段时间中位：BNN组内4/16核17.80/17.76秒，pipeline16核5.74秒；DLA组内4/16核34.59/35.18秒，pipeline16核11.27秒。pipeline相对自身1核的16核配对加速分别11.9321×/12.1671×，相对同16核组内3.1263×/3.1236×。两大图8/16核每组全部更快；DLA4核三次全部退步，中位0.9526×。原生日志0.01秒精度，小图tseng阶段仅0.1–0.3秒，不能外推精细小百分比。不能将约12×表述为相对原版或完整流程。

新诊断确认BNN/DLA10组×4样本、pipeline40样本/8工作区；tseng仅2组×4样本/共8任务。线程累计搜索时间/调度墙钟只是重叠线索，不是硬件CPU利用率或任务尾部等待测量。

内存修正：外部5秒采样漏掉全部30个短正式tseng进程的峰值；原始极小值保留，不能当实际内存占用。新增原生日志getrusage(RUSAGE_SELF)历史峰值：BNN约7263MiB、DLA13714MiB、tseng163MiB，所有正式峰值在RR加载已达到、lookahead delta_max_rss=0。这不能证明零新增工作区、内存节省或阶段RSS上限。所有测量cgroup区间无新增throttle/OOM，但仍不证明资源独占。

平台HPC探测hpc-job-53b8d9d1-09bc-4c0e-ae60-04cecb7dd0b3实时状态STOPPED、无cpu_instance_probe.json；停止原因未建立，未重启/复制/取消。platform/probe_status_latest.json为当前回执。严格隔离测量仍缺；本轮正式仍是另一共享宿主CPU实例，不能称物理核独占。

本机先前208项合法与1034产物复核保持，已再验证local_review绑定。总索引docs/native_cpu_paper_evidence_index.md；根finalization.json状态planned_runs_reviewed_with_open_research_gaps，记录所有轮次及未解决缺口。直接flat parallel_for对照、严格隔离CPU和lookahead独立工作区内存仍未补齐。默认未改，无GPU收益主张；无活动求解、监督或自动后续队列。以下历史运行状态均已过时，勿重启owner。

## 论文补齐1/2/3/4执行中（2026-11-05，当前优先）

本机第1/2/4项已终态复核：208/208合法、96正式、1034产物重核，2份不同RR图；主进程重建stock→pipeline1.136867×、组内→pipeline1.040204×；缓存组内→pipeline0.972745×。内部flow辅助分别1.152040×/1.045253×/0.982165×，小进程约1–2秒，几百分点差异受完成检测粒度影响。18个实际长度5批次：stock→pipeline tseng K1/K5=1.123454/0.991886、des=1.126599/1.061124；前缀相关且同设计重复，不是5个独立设计。6个compressed_map均合法质量过门，des CPD+3.9543%，未建立整体加速。local_review.json、report.md及PDF/SVG/PNG已生成并目视检查；大图摊销仅情景模型。原本机owner已退出。

远端扩展性仍运行。唯一只读监督scripts/supervise_native_paper_closure.py，工具会话9696，PID见supervisor.json；无重投能力，结束自动运行report_native_cpu_allocated_scaling.py并生成终态审计，仍须主模型审阅。勿重复提交scaling。

用户明确授权执行：方法/消融整理、独立架构泛化、核数与内存、真实缓存摊销；另指示用qz调用其他CPU实例。新目录results/native_paper_closure_20261105，原生默认与solver二进制均未变。

第1项method_and_ablation.md、mechanism.json已生成。源码表明既有pipeline本身已全局展开任务；GEMM/elliptic诊断均10组×4样本，组内搜索并行宽度上限4，不能声称新pipeline原语。尚无直接flat parallel_for原生对照，不声称优于所有直接展开策略；bounded负例保留。

第2/4项唯一本机owner PID2904620、工具会话21025，scripts/run_native_paper_closure.py run。四个新布局为原生k6_N10_mem32K_40nm、tseng/des两留出电路、seed1/2、网格宽30/40、通道100。4准备、16资格、条件96正式、6个compressed_map替代模型、18个真实长度5批次（90进程）；总计208项路由测量，不含准备和独立检查。全部四资格已通过。观察summary.json后再判断终态，勿重投。每条原生/独立FULL/STA、map/QoR/实际命令env/亲和性审计；批次每臂自己第一次构建cache，后四次读取，K1/2/5是相关前缀、同固定设计重复请求，不叫5个独立设计。

第3项脚本scripts/run_native_cpu_allocated_scaling.py，plan在scaling/：3不同图tseng2D、BNN/DLA宽120；同修复ELF组内/pipeline×1/2/4/8/16物理核×3repeat共90正式+6诊断。通过qz授权已从Jupyter短寿命自有kernel启动到另一现有CPU实例fpgaacc1，notebook_id24b4a633-9ad2-4133-9174-cfc8cd109508、hostname fpgaacc1--cfc8cd109508-jnnrja5s7q、唯一远端owner PID2086391。launch回执platform/scaling_remote_receipt.json，日志scaling/remote_owner.log，summary为唯一实时进度。远端54CPU配额、cpuset0-127，非独占宿主/物理核；classification.json明确strict_isolated_measurement=false。这一批只能补另一实例受控扩展性，不能声称严格隔离缺口已补齐。

平台另有唯一短HPC资源探测作业hpc-job-53b8d9d1-09bc-4c0e-ae60-04cecb7dd0b3（20CPU100GB），当前因Insufficient cpu/memory排队/创建波动；没有自动扩展性下游。entrypoint仅probe_native_cpu_instance.py、无solver，结束TTL600。首次CreateJob明确InvalidParameter镜像ID，已保留拒绝；HPC要求镜像地址，修正后唯一次成功jobID如上，不是重复提交。不自动取消/复制，先qz GetJob确认。qz必须对qz.sii.edu.cn绕过proxy；凭据已设备授权，不能输出令牌或访问URLtoken。

所有现有实例已通过只读短kernel探测，tokens仅在内存，四个probe在platform/，自有kernels已关闭。脚本inspect_native_cpu_notebooks.py可复用execute接口；websocket必须http_no_proxy并同时设置大小写NO_PROXY。现有实例还有其他工作，勿停止它们。qz-cli命名技能未找到，使用inspire-gpu-submit技能及qz实时schema；当前CPU HPC不是GPU作业。long-run-supervision保持单一owner，无luna接口，不声称模型切换。

后续：持续读取两summary，数值失败立即诊断。结束后运行report_native_paper_closure.py、report_native_cpu_allocated_scaling.py独立重核，再用.venv-report/bin/python scripts/plot_native_paper_closure.py绘图并目视检查。当前共享宿主下新架构96正式已全合法，但终态审计未完，不提前作为最终结论。更新本节终态，明确严格独占资源、精确阶段RSS和直接flat基线仍未建立。历史旧owner都已退出，不要重启。

## 完整流程72项已全部完成并独立复核（2026-11-05，最新终态）

results/native_cpu_width120_endtoend_20261104于2026-11-04 22:56:18Z完成，原PID2778840/会话1748已退出，勿重启。本轮新review_native_width120_endtoend.py独立核验通过：12项资格+72项正式全部合法，全部使用输入、源/runner/ELF、588份产物、实际命令/env/八物理核、执行顺序与不重叠、原生及原版独立FULL/STA、map/route hash、所有冻结质量门槛及配对统计重算一致。review.md、independent_review.json、conclusions.json、evidence_summary.json、finalization.json为终态；两组PDF/SVG/PNG已生成并目视检查。没有活动求解/审计或自动后续队列，无新求解提交、默认不变。

同八核完整native进程配对速度比中位的布局等权几何平均：重建stock→pipeline1.699916×，同修复ELF串行→pipeline1.688641×，组内→pipeline1.099108×；共享缓存分别1.014490×/0.996093×/0.997694×。重建stock→pipeline与组内→pipeline各九组全部更快，范围1.590919–1.778441×与1.054784–1.116383×；缓存组内→pipeline仅4/9更快（0.983030–1.016713×），未建立缓存增量。内部flow方向一致；重建组内→pipeline纯routing阶段约1.001646×，支持收益主要来自预计算，但不作严格全因果隔离。

完整进程中位秒（stock/fixed_serial/per_group/pipeline）：LSTM_s2为148.59/149.55/97.28/90.38，BNN_s1为138.54/139.14/90.27/81.73，BNN_s2为141.84/140.09/90.23/81.63。布局级stock→pipeline配对中位1.661422/1.700542/1.738661×，组内→pipeline1.076340/1.115336/1.106028×。中位时间之比不替代配对统计。重建workflow（native+独立检查进程wall，排除copy/hash/preflight）stock→pipeline1.391364×、组内→pipeline1.052477×，不能与native主指标混用。

质量全部满足预设5%门槛，但并非逐路由相同：pipeline相对stock最大CPD退化0%、WL退化0.090772%；相对组内最大CPD退化0.164887%、WL退化0.041202%，来自BNN_s2 rebuild repeat1。原版对照含状态修复/轨迹差异，不能全归因pipeline；同ELF组内→pipeline是更直接的增量对照。所有wire map等价不扩大为所有派生src/opin表都序列化验证，也不主张routing确定性。

适用边界保持：预先按修复基线合法性选定的3布局、2电路、2独立RR图，BNN两布局权重2/3、LSTM一布局1/3；非原六布局全部通过，原宽120仍3合法/3失败，DLA两布局与LSTM_s1负例保留，宽100旧资格拒绝与原144项未启动保持。共享宿主、每臂三次，不称普遍或独占性能。先前3图阶段7.40×与本轮完整流程1.70×的计时边界、样本集合不同，不能相乘；分别作为阶段与条件子集整体证据。

本轮结论：CPU预计算主线得到完整流程支持，pipeline在组内并行之上有可重复的重建增量；缓存路径未建立新增收益。低核数负例、bounded拒绝及路由质量负例不撤销；默认保持。无GPU收益、三维专属新寻路或论文新颖性充分证明主张。evidence_summary.json已汇总阶段/完整流程/缓存边界。下一步可据此整理方法与结果章节；若扩大适用范围，先独立预选新架构/电路或独占资源协议，不继续自动扩宽失败布局。下方历史活动状态全部以本节为准。

## 九项基线已全部复核；四臂完整流程资格与条件72项正式链已启动（2026-11-04，当前）

results/native_cpu_width120_baseline_20261104于18:05:32Z完成，原PID137169已退出勿重启。9/9合法、9/9质量通过；新independent_review.json/conclusions.json/finalization.json重新验证63份产物、全部使用输入、实际命令/env/八核、原生及原版独立FULL/STA、map及route hash。LSTM_s2三次20轮/11.7483ns/1714427；BNN_s1三次19轮/11.0943ns/1538209；BNN_s2三次17轮/11.4813ns，线长1643787/1643783/1643787（仅差4）。路由主体种类1/2/2，不声称确定性，原宽100严格端点失败保持。

用户“继续”后新冻结results/native_cpu_width120_endtoend_20261104/plan.json，唯一owner scripts/run_native_width120_endtoend.py run，PID2778840、工具会话1748，19:00:51Z开始。恢复前查summary/PID/子进程，不重投。先3布局×4臂rebuild资格共12项；全部通过冻结门槛后，同owner条件推进72项新正式：3布局×4臂×rebuild/reuse×3重复。当前起始qualification_lstm_s2_rebuild_r0_stock。没有默认改变或GPU作业；原宽100的144项始终未启动，本轮是独立新协议。

范围明确见scope_clarification.json：条件子集LSTM_s2/BNN_s1/BNN_s2是3布局、2电路、2份独立RR图；不同于已完成阶段实验的3图。整体分母仍原六布局3合法/3失败。主统计按布局等权，BNN占2/3、LSTM占1/3，不当作按电路/图等权泛化。

四臂stock/fixed_serial/per_group/pipeline同八个物理核32–39、原生parallel路由；后三臂同修复ELF仅lookahead开关不同。每次使用同已有宽120 RR、packed/place，200轮/900秒，64GiBAS、core0、60GiB磁盘下限，顺序轮换case/arm/cache mode，捕获实际env/command/CPU/cgroup/load。统一map写出计入进程时间；缓存仍重算src/opin。合法后原版独立FULL/STA及原路由不变核验。没有生成RR、重pack/place或延长预算。

12项资格必须全合法/map一致/零过用/独立FULL-STA，修复三臂各自CPD/WL不劣于原宽120修复基线5%；组内不劣于同ELF串行5%，pipeline同时不劣于串行与组内5%。route主体变化明确记录、不强制identity；stock相对质量另行评价，stock速度主张还须对应全部配对通过5%质量。资格失败则不启动72项正式，无重试/换样。资格通过后正式样本仍全部复核，任何数值失败或修复版质量门槛失败阻止完整子集加速汇总；保留所有失败，不挑选好配对。

正式主指标完整native进程wall，按布局/cache/repeat配对取三次中位与范围，再布局等权几何平均；资格与旧样本绝不混入。workflow为native+独立检查进程wall（排除copy/hash/preflight），内部flow及routing为敏感性。Stock对照含修复/轨迹差异，增量主归因用同ELF组内→pipeline。终态自动audit.json/analysis.json/report.md，但需主模型复核，不自动改默认。共享宿主，非独占。

执行前已验证12/72完整唯一覆盖、24个case/arm/cache单元各3次、实际命令读取同一路由；针对性检查覆盖非法样本不可算速度、缺臂拒绝、5%质量拒绝、route变化允许但不称identity、stock质量与同ELF质量分开、配对中位不同于中位时间之比、坏样本阻止汇总。以下历史运行中/未提交状态以本节为准。

首项qualification_lstm_s2_rebuild_r0_stock已完成原生及独立FULL/STA：22轮、CPD11.7483ns、WL1713833，map/实际命令/env/八核与独立检查未改route hash复核通过，见first_completed_review.json。现已推进qualification_lstm_s2_rebuild_r0_fixed_serial；总资格仍pending，72正式尚未开始。原版22轮与此前修复基线20轮是轨迹差异观测，不据单次差异宣称严格修复因果或加速，资格样本不并入正式性能。

## 三图阶段36项已完成复核；条件子集九项基线资格运行中（2026-11-04，当前）

results/native_lookahead_component_20261104已于16:46:32Z完成，原PID4171926退出，不要重启。4pilot+36正式均component_valid，40项原生路由尾部均按预定1轮未布通rc2；不计为合法路由。audit.json与新independent_review.json、conclusions.json、finalization.json终态通过：160份产物、全部使用输入、源/runner/ELF、实际命令/env/八物理核及40项执行顺序/时间不重叠重核，正式配对统计独立重算无差异。component_results.pdf/svg/png已生成并目视检查，report.md已附图。

同八核、三份不同RR图（六布局按图hash去重）、三runtime重复的完整lookahead阶段结果：原版→pipeline等权几何平均配对中位7.404136×，同修复ELF串行→组内3.888000×，串行→pipeline7.579864×，组内→pipeline1.943252×。九组增量配对全部更快，范围1.87095–2.02093×。构建秒数中位stock/fixed_serial/per_group/pipeline：DLA130.63/131.42/33.65/17.73；LSTM65.75/67.47/17.31/8.90；BNN65.86/67.18/17.38/8.74。各比值分别按配对取中位，不能把中位时间之比或多个汇总比值乘积当相同统计。仅阶段收益，无进程/端到端加速主张；同架构三个图规模、共享宿主、每臂3次，wire文件等价不扩大为所有派生表等价。

用户“继续”后已冻结并启动results/native_cpu_width120_baseline_20261104/plan.json：此前已声明的LSTM_s2、BNN_s1、BNN_s2各三次，共9次全流程基线资格。唯一owner scripts/qualify_native_cpu_width120.py run，PID137169、工具会话40695，17:43:10Z开始，当前首项lstm_s2_cached_baseline_r0。恢复前查summary/PID/子进程，不重复提交。只用修复ELF、缓存wire map（src/opin仍计算）、原生parallel路由八核32–39，TASKS/PARALLEL=0/0，固定原宽120图/布局，200轮/900秒、64GiBAS、core0、60GiB磁盘下限。实际命令/env/CPU捕获；合法后原版独立FULL/STA在independent子目录执行，其冻结命令仍读取父目录原packed/place/route绝对路径，原路由hash须保持。

资格要求9/9原生合法、零过用、map一致、原版独立FULL/STA及CPD/WL匹配，并且每次相对既有宽120修复基线的CPD和WL均不劣于5%。同模式route-body变化单独统计，不误称identity；原宽100严格端点失败不回填。全部数值失败保留，无重试/换样，来源/env/CPU/map漂移停止。控制器终态自动audit.json、acceptance.json、report.md；通过只说明条件子集基线资格，不自动提交候选资格或性能矩阵。完整六布局仍3合法/3失败分母，原144项与新的候选性能均未启动，默认不变。

脚本已核验9条无重复/各case3次命令、宽120/8workers/200轮/cache、独立读同一路由，以及数值失败不得通过质量门槛、CPD/WL两个5%边界分别执行。沿用单一确定性owner，无GPU/Vivado或luna切换。以下历史状态以本节为准。

首项lstm_s2_cached_baseline_r0已完成：20轮、CPD11.7483ns、WL1714427，与既有宽120基线CPD/WL完全相同。原生与原版独立FULL/STA通过，map一致，实际两进程命令/env/CPU及独立检查未改路由hash复核通过，见first_completed_review.json。当前后续bnn_s1_cached_baseline_r0已启动；9项总资格仍pending，不能用1项完成宣称整个子集通过。恢复时读取最新summary/acceptance，保留原owner继续。

## 三份独立RR图的lookahead阶段实验已冻结并启动（2026-11-04，当前）

用户“继续”后回到CPU预计算主线。新结果目录results/native_lookahead_component_20261104，唯一owner为scripts/run_native_lookahead_component.py run，PID4171926、工具会话61924，summary开始15:28:51Z。恢复前查summary.json、PID及子进程，不要重复提交。当前4项BNN流程pilot后条件执行36项正式阶段测量；pilot全部通过才推进，未知来源/env/CPU/map异常停止，数值正式失败保留，无自动重试。控制器终态自动写analysis.json、report.md、audit.json，须主模型终态审阅，不直接推广默认。

新发现已按hash确认：原宽120六布局的RR和wire map在每电路两种子之间逐字节一致，实际只有3份独立RR图（DLA/LSTM/BNN）。预计算按图去重、固定选最小布局id即各s1代表，全部三图纳入，包括路由失败图；不能叫六个独立图，也不能按可布通性筛选预计算。plan.json保留六布局对应关系与既有合法性分母。

同物理八核32–39，四臂stock/fixed_serial/per_group/pipeline，后三臂同修复ELF，仅改变LOOKAHEAD_TASKS/PARALLEL。三图×四臂×三runtime重复=36正式；4pilot排除于统计。按图/重复配对速度比中位与范围，再三图等权几何平均；仅完整36项且终态审计通过才报告完整队列比值。共享宿主，非独占。整个任务输入/二进制/source/runner冻结；实际子进程命令、env与CPU亲和性均捕获。

利用既有原生路径，无新solver构建：完整Computing router lookahead map计时（wire+src/opin+minima）在Routing前结束；随后路由统一最多1轮，关闭显式analysis和overuse报告。不读缓存、不改RR/布局、不pack/place。map必须逐字节匹配既有宽120完整运行的修复串行reference；序列化仅覆盖wire map，不扩大为所有派生表都被文件验证。正常1轮未布通rc2可记component_valid，但明确routing_success_observed=false；超时/崩溃/未完成timer/map错均无效，不计算进程或端到端速度比、不用失败路径作QoR。900秒/项、64GiBAS、core0、60GiB磁盘下限。

脚本针对性验证通过：预期rc2只能归为阶段有效，timeout/map错/缺完整timer拒绝；36正式覆盖无重复且每图每臂3次；实际一轮/八核命令正确。端到端计划仅为plan.json内specified_not_submitted规格：历史基线可布通子集LSTM_s2/BNN_s1/BNN_s2，必须先重新验证重复可布通性及原生/独立FULL/STA和5%QoR门槛，再单独冻结精确执行计划。候选计时前公开子集范围、保留六布局全分母，不回填原宽100门槛；原144项和新的端到端矩阵都未提交。

long-run-supervision沿用单一确定性owner，环境无luna委派接口，不声称模型切换。没有GPU或Vivado任务。以下历史“无活动”以本节为准。

四项BNN pilot现已全部通过，pilot_gate.json及pilot_review.json为回执；原版/修复串行/组内/pipeline的完整构建分别67.20/67.63/17.53/9.59秒，四份wire map与既有完整运行reference一致，实际命令/env/CPU32–39核验通过。四项均1轮未布通rc2，component_valid=true与routing_success_observed=false同时保留，不能当合法路由或正式速度证据。原owner已自动进入冻结36项正式测量（起始formal_bnn_r0_stock），无需另行提交；仍需等待全队列和终态审计，禁止把pilot并入正式重复。恢复时重新读summary，勿以此快照判断完成数量。

## 宽120复核与LSTM串行诊断全部完成（2026-11-04，最新终态）

本轮无活动求解或分析队列，勿重启历史owner。results/native_cpu_width120_20261104/review.json、review.md、review_execution.json与六布局width_congestion.pdf/svg/png已完成并检查；41份绑定产物及六份新RR图重新验证通过。全部六布局仍3合法/3失败：LSTM_s2、BNN_s1、BNN_s2合法且独立FULL/STA通过；DLA_s1/s2为900秒超时（最后完整轮78/81，最后观察过用97/62），LSTM_s1为200轮3过用。第50轮后DLA过用分别95–103和62–75；LSTM并行最后51轮均3。扩宽缓解拥塞但没有恢复全部布局，不能只挑成功者宣称六布局泛化加速或稳定可布通率。

results/native_lstm_width120_serial_20261104已完成，原PID3637747/会话58056退出；summary.json、audit.json、independent_review.json、conclusions.json、report.md为终态。一项同修复ELF、同宽120 RR/布局/缓存、timing_driven单物理核32诊断，200轮仍3过用，returncode2，进程669.42秒；没有独立合法路由检查（因为原生失败），六份终态产物重新审计通过。串行节点3619283/3619421/3619499，与并行3619305/3619470/3619539不同，但均层0 x=73 CHANY、容量1占用2。不能用失败路径CPD/WL作质量基线，不作一核对八核速度比。

并行残余冲突附近三个DSP局部引脚集合的直接邻居单位容量匹配全部成功：64输入/212邻居匹配64，30输出/52邻居匹配30，64输入/212邻居匹配64。lstm_pin_access.json和所选edge XML保留；物理tile高宽均1。此检查按块与方向独立，未扣其他网络占用、未求多跳互不冲突路径、未涵盖所有串行残余引脚；仅排除这三个集合的直接邻居数量不足，不能证明全图可布通。串行失败不支持仅切换串行即可解决，不能据此证明竞态、垂直瓶颈或图本身无解。

停止本轮自动扩宽/超时延长/进一步求解，不启动原144项正式矩阵。下一轮回到已验证CPU lookahead主线，先明确大图预计算等价性/阶段计时与完整路由合法性/QoR的独立评价协议；如采用可布通子集做端到端对照，必须候选计时前声明条件范围、保留全部六布局结果，不能回填旧门槛。该下一轮尚未冻结或提交。宽100负例及默认算法不变，没有GPU收益主张。

离线复核曾因XML同一行含node/loc而解析失败，已修复并做针对性检查；随后系统Python缺matplotlib，改用现有.venv-report环境完成绘图。仅分析重跑，求解未重启；review_execution.json保留原因。以下历史“运行中”均以本节终态为准。

## 线宽120六项已完成；LSTM串行定点诊断运行中（2026-11-04，当前）

results/native_cpu_width120_20261104于03:41:32Z完成，原owner1447474已退出，勿重启。6/6执行、3/6合法，audit.json通过41份产物。DLA_s1/s2均900秒超时，最后完成78/81轮、最后观察97/62过用；LSTM_s1完成200轮仍3过用；LSTM_s2为20轮、CPD11.7483ns、WL1714427，BNN_s1为19轮、11.0943ns、1538209，BNN_s2为17轮、11.4813ns、1643783，后三项原生及独立FULL/STA通过。扩宽缓解拥塞并在本次恢复两个布局合法，但没有恢复全部六布局；不可只挑成功者报告泛化加速。超时末次观测不是最终合法终点；失败路由的CPD/WL不能作为有效质量结果。

已新增只读复核scripts/review_native_cpu_width120.py（工具会话82787），重新核验41份绑定产物和六份RR图，生成review.json/md、lstm_pin_access.json、六布局拥塞PDF/SVG/PNG。LSTM三冲突均层0 x=73 CHANY（3619305/3619470/3619539），涉及DSP附近输入/输出；尚未证明垂直互连瓶颈。图扫描按三个DSP局部引脚集合分别做单位容量直接邻居匹配，不等于全图可布通性证明。查看工具会话与产物判定复核是否完成，勿并发重复执行。

唯一新求解：scripts/diagnose_lstm_width120.py run，PID3637747、工具会话58056，10:41:43Z开始；results/native_lstm_width120_serial_20261104/plan.json与summary.json为冻结计划/回执。同修复ELF、LSTM_s1原宽120 RR/布局/缓存，timing_driven单物理核32，200轮/900秒，缓存仍重算src/opin。只执行一次，保持两状态修复，不重pack/place、不扩宽、不启动性能矩阵。新runner先写measurement再取log_evidence以避免旧元数据误判；map/CPU/输入hash、合法时独立FULL/STA核验。第95轮仍3过用是运行中快照，最终须重读summary。诊断不报告一核对八核速度比；成功仅证明存在路由，失败也不证明图本身无解。

原宽100失败、全部宽120负例、默认算法及正式矩阵未启动状态保持。以下历史活动描述以本节为准。

## 八项诊断已审计；六布局统一线宽120基线探测运行中（2026-11-04，优先）

旧诊断results/native_cpu_large_diagnostic_20261103已完成，原求解和审计owner均退出，勿重启。以verified_summary.json、verified_analysis.json、verified_report.md、audit.json及conclusions.json为准：8项完成，6项合法，57份产物审计通过。BNN_s2的TASKS0三次为75/75/121轮，TASKS1为121/121/121轮，均独立FULL/STA通过；TASKS0最后一次恢复旧reference路由主体。同配置存在轨迹变化，不能把单次75轮当作稳定优化收益，也未证明竞态根因。BNN_s1串行和并行均200轮未收敛、各剩1过用节点。缓存只跳过wire map构建，仍重算src/opin。原runner成功分类错误已在verified派生结果中纠正，原始记录保留，不重跑。

用户“继续”后已冻结并启动独立协议results/native_cpu_width120_20261104/plan.json。唯一控制器scripts/probe_native_cpu_width120.py run，PID1447474、工具会话38141，开始2026-11-04T02:49:26Z。恢复前先查summary.json、原PID及子进程，不能重复提交。六个原固定布局DLA/LSTM/BNN各s1/s2顺序执行，统一线宽120，仅同修复ELF串行lookahead构建+原生parallel路由八物理核32–39；900秒/200轮，64GiB地址空间，core dump禁用，每项前80GiB磁盘下限。没有新pack/place，没有图编辑，没有候选速度比较或自动扩宽/重试。

新进程生成并保存原生RR图，旧宽100测量读取已有图，计时边界不同，不能用进程时间比宣称加速。每项核验输入、实际120图头、CPU预算、原生FULL、零过用及原版独立FULL/STA；单次合法仅为可布通证据，不证明稳定性、质量等价或跨实现map等价。全部失败保留；数值失败继续预定六项，来源/资源异常停止复核。控制器终态自动写summary.json、analysis.json、report.md与audit.json，主模型仍须审阅；禁止从本探测自动进入正式矩阵。

执行前已核验六条命令（宽120/8workers/parallel，无pack/place/read_rr_graph）、原合法日志元数据回归（先写measurement再调用log_evidence）、超时不得记合法、XML属性乱序和截断图拒绝。原线宽100六布局资格失败及144项正式未启动结论保留，默认不变。无GPU/Vivado作业；long-run-supervision沿用唯一确定性owner，无可用luna委派接口。以下历史“活动链”均以本节为准。

启动实测见startup_verification.json：首项DLA新RR文件6434537315字节，XML闭合、x/y/max宽均120，求解PID1448230实际亲和性32–39。CHANZ无入边日志新旧均1818条，检查源码对应分支仅记录错误；不能据相同计数推断图节点完全相同或证明其无影响。首项已进入路由，第60轮宽100旧修复串行构建基线过用2123，新宽120为101；第62轮仍98，尚未合法。interim_congestion_observation.json保留同轮单次观察，仅支持拥塞缓解，不证明稳定可布通性或速度收益。六项最终状态须重新读取summary.json，不能把本段运行中快照当终态。

## 大图资格失败已复核；八项缓存路由诊断正在运行（最新）

2026-11-03：原results/native_cpu_large_20261102链已终止，原三owner均不再运行，不要重启。六个pack/place均成功；preparation_verified.json纠正XML计数后输入完整。30/30资格完成、30份map字节等价、90文件审计通过，但仅5项合法：17项900秒超时（DLA/LSTM）、2项原版DLA SIGSEGV、1项原版LSTM_s2 SIGABRT/std::bad_alloc、5项BNN_s1在200轮未收敛、5项BNN_s2合法且独立FULL/STA通过。144项正式和16核扩展均未启动，默认不变。

新复核review_20261103.md/json区分阶段收益和完整收敛：DLA_s1同修复ELF构建114.40/28.96/15.43秒（串行/组内/pipeline），LSTM_s1为58.88/15.06/7.61秒；这些只是单次资格阶段计时，失败运行不能算整体加速。DLA/LSTM拥塞停滞，50轮后冲突模式扩大BB与末轮工作量增加一致。BNN_s1修复版末轮仅层0 CHANY3329379容量1占用2，涉及DSP输出网络1270/1278，不能直接归为垂直容量不足或图不可布通。原版崩溃根因未定位；bad_alloc不是已证实的系统OOM（cgroup OOM计数无新增）。

BNN_s2五臂质量都合格；旧冻结/reference、同ELF串行构建、pipeline均121轮/11.4776ns/1668046，per_group为75轮/相同CPD/1668374。严格端点不一致导致资格失败，不能称质量恶化或75轮稳定收益。原gate缺失hash的None==None误显示相等，新review将不可观察端点置null，原记录保留；拒绝结果不受影响。

用户“继续”后已启动独立八项诊断：results/native_cpu_large_diagnostic_20261103，scripts/diagnose_native_cpu_large.py run，唯一owner PID1689980、工具会话12339。恢复前检查summary.json、PID和子进程，不能重复提交。任务为BNN_s1同图缓存并行8核/串行timing_driven1核各一次，BNN_s2同ELF同缓存TASKS0/1各三次交错，共八项；线宽100、原布局/RR、900秒/200轮不变。map/CPU/FULL/独立STA核验，数值失败保留且继续预定诊断，输入/二进制/map漂移停止；终态自动写analysis.json/report.md。诊断不报告速度比、不替换原负例。当前第一项并行缓存仍在运行；原正式矩阵保持未启动。

诊断补充：BNN_s1缓存并行与串行均完成200轮仍各一个过用节点（分别CHANY3329379和3329367），串行没有解决该布局。原冲突DSP的32个有效输出存在32个不同直接邻居的匹配（bnn_s1_pin_access.json），仅排除直接出口数不足，不能证明全图可布通。BNN_s2首个TASKS0缓存重复75轮且原生/独立FULL/STA通过。缓存仍有src/opin预处理，不能说排除所有预计算。

诊断元数据修正已登记classification_correction.json：新runner在measurement.json写出前调用依赖该文件的log_evidence，成功路由末轮过用被记null，success误标false。原程序保持冻结，求解不重跑；独立audit_native_cpu_large_diagnostic.py将依原始日志/路由/独立复核重算verified_summary.json、verified_analysis.json、verified_report.md，保留原始记录。等待审计器finish_native_cpu_large_diagnostic.py已运行，PID2173553、工具会话84634，audit_supervisor.json为回执；不提交求解，原owner完成后自动执行独立审计。最终以verified_*和audit.json为准，不能使用原自动report.md的成功数量。

## 较大输入 CPU 扩展已启动（当前活动链）

results/native_cpu_large_20261102：用户授权“继续下一轮”。protocol.json、qualification_plan.json（30项）、formal_plan.json（条件144项）已经冻结。唯一控制器为 scripts/run_native_cpu_large.py run，PID 2963438，工具会话85004；启动时间2026-11-02T18:42:03Z。恢复观察前必须查询supervisor.json和原PID/子进程，不能重复启动；owner.lock防重入。当前起始阶段是dla_like.medium_s1原版pack/place，后续六布局→资格审计/门槛→正式矩阵由原控制器顺序推进，未知异常停于stopped_for_review，无自动重试。

启动后的预检查发现新增几何统计器假设`<node id=...>`，实际VPR输出为`<node capacity=... id=...>`，会漏计节点；原求解未受影响，冻结控制器保持不变。已启动显式后处理接续器 scripts/continue_native_cpu_large.py，PID3119945、工具会话97686；当前只等待原准备owner，不运行任何求解。它只接受六项求解returncode0、布局校验成功、原统计器AssertionError()这一已知条件，待原owner退出并取得同一owner.lock后重核原产物，写preparation_verified.json / prepared_verified案例 / *_verified_plan.json，再接管资格和正式阶段；其他失败停止复核。原始preparation.json、protocol和plan不覆盖，布局不重跑、RR不修改。原XML节点属性顺序与段标签排除的针对性检查已通过。之后优先读continuation.json判断链终态；report_native_cpu_large.py已支持原始/派生准备来源和终态报告。

另有只读观察器 scripts/observe_native_cpu_large.py，PID3613870、工具会话61967，observer.json为实时回执；每15秒查询现有owner，绝不提交或重启求解。接续链终态后自动执行已hash绑定的report_native_cpu_large.py，生成analysis.json/report.md；owner失联只记录owner_lost_requires_review，不恢复未知停止。阶段资格/性能解释仍需主模型审阅报告，不能把报告存在等同于推广通过。2026-11-02T18:53Z核验首个求解PID2964120仍正常运行，已完成原生RR生成（约5.3GiB）并进入默认布局退火；当时尚无已完成输入或正式测量。

三输入dla_like.medium/lstm/bnn，各种子1/2；原版默认布局参数，单物理核准备，每项3600秒，显式place/route宽100，pack/place阶段写原生RR图，不把准备阶段当路由合法性证明。准备核验双层占用、两布局坐标不同、RR节点/边和输入hash。资格原版/旧冻结端点/同ELF串行lookahead/组内/pipeline共五臂，每布局一次；全部map/FULL/STA/QoR与旧端点通过才进入正式四臂两缓存三重复。路由每项900秒，实际八核32–39；新wrapper清除继承实验开关，仅在单轮缓存准备关闭已知有断言风险的overuse报告，正式参数不变。新wrapper唯一变体匹配、执行顺序及30/144计数已核验。

共享宿主上存在相邻工程活动，无可用srun，不能称独占。初始可用磁盘约519GB；准备每项前检查至少80GiB空闲。没有GPU或Vivado任务。long-run-supervision已应用，没有可选luna委派接口，使用现有模型与唯一确定性控制器；不因缺少委派而重启任务。16核扩展未提交、默认算法未修改。阶段完成或失败须主模型解释并写最终报告，当前尚无本轮性能结论。

首个输入已完成实际核验：dla_like.medium_s1原版pack/place成功801.46秒，154×154双层布局，28507个放置块（层0=13457、层1=15050），RR节点7312040、边64251424、文件5633292633字节。first_input_check.json为修正统计器的只读核验，非路由资格/性能样本；原控制器仍在按冻结流程整理并继续其他布局。

## CPU 主线与近期负例综合分析完成（最新）

results/native_cpu_direction_20261102：report.md、analysis.json、circuit_inventory.json、next_experiment.json、source_bindings.json、verification.json 与 GEMM 分项 PDF/SVG/PNG。新增脚本 analyze_native_cpu_direction.py / report_native_cpu_direction.py。本轮仅分析已有证据，无新求解、无默认或算法修改。

21项GEMM重建样本逐项重算并核查源码计时作用域：八核pipeline进程中位202.17秒，lookahead20.82、设备创建52.16（内含RR加载49.44）、已打包网表加载检查29.18、电路准备21.62、路由31.68、路由后同步6.62；逐样本剩余未分项成本中位39.93秒。各项中位数不可直接相加。加载不是已证实的纯I/O瓶颈，剩余成本也不能直接归因于调度。

逐样本计算后取中位：八核pipeline lookahead占10.36%，再快一倍整体仅1.054633×，完全免费条件上限1.115580×；十六核占6.70%，对应1.034664×和1.071818×。上限假设其余成本固定，不是预测。此前同八核原版→pipeline1.637905×和组内→pipeline1.084265×仍有效；原版对照含状态修复，不能全归因于构建。近期跳过重插入是QoR敏感变化，拒绝结论保持。bounded没有稳定超过旧pipeline，但具体退步成本尚未隔离，不能确定为资源约束或调度开销。缓存同ELF小幅退化仍未解决。

本地20个Koios BLIF均有历史元数据引用（扫描4538份计划/清单），不能称独立新基准。按结构实例数量代理预选当前六电路主线之外的dla_like.medium/lstm/bnn，模型名称检查通过；尚未验证pack/place与RR规模，未证明比GEMM大。next_experiment.json为specified_not_submitted规格：三输入两新布局、同八核、原版外部基线+同修复ELF串行lookahead/组内/pipeline四臂、重建/缓存各三重复，共144项，先严格map/FULL/STA/QoR与旧冻结端点资格。串行仅指lookahead，路由仍八核。后续16核36项为条件扩展，未提交。

下一执行需先冻结pack/place命令与超时、准备六布局与RR输入、绑定hash并通过资格，再生成可执行runner清单。本轮未启动这些步骤。优先扩展已验证主线；新代码优化先拆RR加载、网表检查和未分项成本，不继续推广已拒绝的路由顺序候选。以下旧“下一步”以本节为准。

## 同分区无效重插入候选已拒绝（最新）

results/native_partition_skip_20261102：候选实现完成但质量门槛失败，不推广、不改默认。report.md、analysis.json、acceptance.json、final_status.json为终态，无活动求解/队列。原supervisor.json保留诊断包装器异常的stopped_for_review，不要重启。

s38417_s1控制→候选CPD6.96051→8.61087ns（+23.71%），轮数68→65；s2为7.7556→8.28151ns（+6.78%），轮数47→54。均超过CPD/WL最多5%退化门槛。跳过old==new删除再插入保持分区归属正确，但改变启发式顺序，不能当严格语义不变优化。

14次原生运行全部合法且map字节等价、原生/独立FULL/STA通过：6项plain门槛、最初4项错误未启用trace的诊断（保留并排除）、补4项正确诊断。旧wrapper按后缀匹配diag_control/candidate撞上control/candidate；改名tracectrl/traceskip补跑，未修改冻结runner。有效诊断control/candidate的68/65与47/54轮均零分区越界，候选首5轮跳过851/785次重插入，plain/diag最终路由质量一致。新control与既有frozen端点一致。

质量失败后按冻结协议未启动elliptic guard和72项正式性能矩阵，不报告速度比。guard的错误case路径在提交前修正并留planning_correction.json，仍未执行。当前两处正确性修复保留，跳过开关默认0；隔离构建未改变历史source/library/ELF。

下一步建议回到已验证的CPU lookahead大图泛化；若研究显式同扇出排序，需独立QoR门槛，不能沿用此候选的加速主张。此前同ELF缓存小幅退化仍未解决，旧无修复端点门槛失败保持。以下历史状态以本节为准。

## 逐轮BB与分区顺序诊断已完成（最新）

results/native_state_trace_20261102：24/24诊断样本合法，map字节等价、原生及独立FULL/STA通过，八份trace日志结构/env/CPU核验通过。report.md、analysis.json、conclusions.json、acceptance.json与evidence_verification.json；无活动求解/监督队列，勿重启。全部诊断不算正式速度比，默认未变。

两布局两重复的最早机制已定位：首轮BB/归属/分区内顺序一致；首轮后动态通知s1=151、s2=139，无修复均未送达；第二轮开始BB仍同，但无修复有9/8个网络超出所属分区，修复均0。无修复前五轮越界数s1=[0,9,19,28,32]，s2=[0,8,14,21,27]，修复全0。第三轮起BB也分化。此为原二维分区包含条件，不等于最终非法；明确遗漏通知导致过期分区，不能据其快而撤销修复。

首轮通知中仅9/8次实际迁移，142/131次同分区erase/insert。通知集合重复一致但顺序可变；s1修复模式第2轮出现分区内次序变化，归属/BB仍相同。源码unordered_set转vector后按扇出stable_sort，会继承同扇出容器顺序。下一候选：保留通知/迁移，仅跳过old==new重插入；再独立验证显式同扇出排序。尚未实现或证明性能收益。

扰动：both四组旧ELF/off/on路由质量轮数全同；none有一组off/on不一致（51轮8.33758ns vs49轮7.05387ns），不能排除诊断扰动，旧并行端点门槛失败保持。仅前5轮，未记录RR前驱写入，不证明竞态或完整根因；先前同ELF缓存小幅退化仍未解决。隔离两对象构建，首次overlay重复头文件失败日志保留，优先include路径修正后通过，历史源/库/ELF不改。

## 并行状态修复消融已完成，归因门槛未通过（最新）

results/native_state_ablation_20261102：36项同八核缓存消融+12项追加单线程timing_driven诊断，48项全部合法且map字节等价、原生及独立FULL/STA通过。报告report.md、analysis.json、acceptance.json、conclusions.json；独立两份evidence_verification.json和serial_evidence_verification.json。无待运行求解/队列，勿重启owner。默认源码/二进制不改。

隔离构建只替换route.cpp.o（单ELF四模式none/dynamic/reload/both），使用原编译/链接参数与只读旧库，补丁及build_provenance.json留存。外部stock/frozen端点作校验。both与frozen6/6路由/CPD/WL/轮数一致；none与stock仅3/6，预声明整体并行归因门槛失败，不作严格因果定位。none s1第三轮CPD8.33758ns对stock7.05387ns退化约18.2%，不能把合法都当作质量合格。

动态通知开启的模式均稳定s1=68轮、s2=47轮；关闭时s1=49/51、s2=60/61。重载通知不是完全无影响：s1仅dynamic线长87885，both87893，均68轮。串行追加12项每布局六模式路由主体完全相同（s1 55轮/7.52035ns/88168；s2 56轮/7.9263ns/89800），支持并行通知/分区执行敏感性，但未证明竞态或完整根因；串行每臂仅一次。

下一步：记录每轮BB通知、网络分区归属与执行顺序，定位最早分歧；保持两修复默认开启，不以不稳定无修复路径作为速度优化。上一轮同ELF缓存小幅退化仍未解决，不能宣称全是噪声。以下旧状态以本节为准。

## 新电路重复与缓存退化复查已完成（最新）

results/native_cpu_repeat_20261102：120/120正式新样本合法，108项三方重复+12项同ELF缓存开关对照。独立FULL/STA、map字节等价、实际env/顺序/八核32–39核验通过，审计296文件。报告report.md、analysis.json、acceptance.json、conclusions.json。旧单次结果不并入；没有新solver构建，无默认改变。supervisor.json为measurements_and_audit_complete，勿重启。

三轮新电路重建配对中位等权几何平均：stock→pipeline1.057578×、frozen→pipeline1.096909×、stock→frozen0.955245×；VPR内部flow敏感性方向一致，但不同于进程计时边界。共享宿主、固定六布局各三次，不称普遍或独占性能。

s38417_s1缓存退化可重复：stock→pipeline中位0.882411（时间+13.33%），原版49轮，两个改进版68轮且路由相同；frozen→pipeline中位0.999989。主要差异与修改后的路由轨迹/工作量一致，不是pipeline独有。两处状态修复的各自因果尚未隔离。

同ELF缓存TASKS开关s1中位0.993856（0.972730–1.028907），s2中位0.968331（0.962276–0.974975），六对最终路由相同。s2小幅一致退化未定位，不能宣布纯噪声或调度成本已排除。下一步做保持合法质量的状态修复消融和独占资源缓存交错对照，不为速度撤销正确性修复。以下历史状态以本节为准。

## CPU 三方基线、泛化与核数扩展已完成（最新）

结果目录results/native_cpu_evidence_20261102；报告report.md、analysis.json、acceptance.json及四组PDF/SVG/PNG图已生成。66/66正式样本合法，map逐字节等价，原生及独立FULL/STA通过；完整证据审计通过，源码复用15文件核验通过。六次新pack/place均成功，三电路各两布局坐标不同且使用双层。无活动求解/推进器、无GPU任务、无需授权；勿重启旧队列。recovery.json为measurements_and_audit_complete，solver_process_check.json为终态。

同八核GEMM三轮重建配对速度比中位：原版→组内采样1.509058×，原版→pipeline1.637905×，组内→pipeline1.084265×。lookahead中位148.83/37.90/20.82秒，进程330.31/219.20/202.17秒。原版也是八核原生parallel路由。共同缓存原版→pipeline0.998084×，收益主要来自预计算；原版对照同时含此前状态修复，路由轨迹并非完全相同。

GEMM pipeline相对组内采样同核配对中位4/8/16核为1.010138×/1.084265×/1.137698×；pipeline构建37.88/20.82/12.76秒，组内39.05/37.90/38.04秒。核数组间时段不同，宿主共享，不宣称硬件独占或严格隔离的强扩展。

新alu4/diffeq/s38417两布局重建等权几何平均：原版→pipeline1.080351×，组内→pipeline1.121147×；原版→组内0.9636×。每布局每臂只有一次runtime，小电路秒级且执行器退出轮询最大sleep50毫秒，不能据小幅差值宣称稳定增益。s38417_s1缓存相对原版慢17.20%，负例保留。默认不变；当前支持大图多核预计算CPU主线，不等于普遍加速或论文新颖性已证明，新bounded此前未达标结论不变。

保留异常：旧推进器SIGTERM来源未知，只恢复观察/推进，无求解重启。泛化原阶段24项后，s38417_s1单轮缓存资格在map成功写出后因overuse_report.cpp:366断言失败；只对剩余两布局的资格准备关闭拥塞报告，正式参数保持on。原24项不重测，补12项后由generalization_complete派生视图合并；generalization_join.json绑定所有来源和失败证据，原generalization仍failed。原失败map与补充原版/优化资格map等价。正式样本零失败，另有一次保留的资格失败，不能混淆。

后续建议：针对新电路补runtime重复并隔离s38417缓存退化；补较大独立电路及独占节点，再决定有限范围默认策略。论文主张限于原生lookahead采样并行、跨组调度及等价集成，不宣称三维专属新寻路算法或GPU贡献。以下历史当前状态以本节为准。

## 八核 pipeline 顺序确认已完成（最新，优先）

用户授权的下一步已完成。先读 [报告](results/native_pipeline_confirm_20261102/report.md)、[完整数据](results/native_pipeline_confirm_20261102/analysis.json)、[证据审计](results/native_pipeline_confirm_20261102/evidence_verification.json)。36/36项合法、map逐字节等价、原生及独立FULL/STA通过，108个冻结文件核验通过；无重投、无GPU任务。唯一supervisor会话18260已退出，runs/supervisor.json为completed，不要重启。

单lane顺序使用同一NUMA的8个物理核32–39，排除本轮自身并发，但宿主/内存/存储仍共享，不能称硬件独占。GEMM/softmax/reduction各三次rebuild/reuse，frozen/pipeline双变体。后二者是上一轮八核选型的留出电路，来自已有项目，并非新独立基准；只有固定布局的运行重复。

本轮通过预先声明的工程门槛。相对既有优化组内CPU，pipeline的重建配对进程速度比中位：GEMM1.094192×（1.081642–1.097591）、softmax1.128641×（1.088191–1.147396）、reduction1.092956×（1.082867–1.098851）；九次重建配对全部更快。缓存中位分别1.014944×/1.000166×/1.000007×，整体接近持平，不能把缓存波动归因于构建计算。GEMM重建workflow中位1.055066×。

lookahead重建中位秒frozen/pipeline：GEMM39.49/23.34，softmax2.49/1.09，reduction12.82/6.94。GEMM CPD13.2667ns、线长4094294/4095178、15/16轮，部分配对主体不同，全部质量门槛合格；softmax7.63947ns/138983/14轮，reduction11.2973ns/963471/15轮，主体一致。完整进程差异包含并行路由变化，不能当作严格相同工作量的算子计时。

选型：支持已有八核跨组pipeline进入后续候选验证，未改默认；四核不外推。此前新bounded未通过选型的结论保持，不将本轮收益归为新bounded或GPU贡献。本轮未建立论文首创性。后续优先拓展真正独立电路、布局种子与可独占节点，补公平原版八核对照，再考虑有限范围部署；本轮没有启动这些新增实验。历史约12秒重构退步根因仍未确认。下方上一轮“下一步尚未启动”以本节为准。

## 2026-11-01 切片、标量存储与有界调度实验已完成（当前，优先）

D0–D3 与补充布局隔离全部完成。先读 [最终报告](results/native_cpu_slices_20261101/report.md)、[验收](results/native_cpu_slices_20261101/acceptance.json)、[结论](results/native_cpu_slices_20261101/conclusions.json) 和 [对照图](results/native_cpu_slices_20261101/figures/paired_process.pdf)。本轮无待运行求解、监督器或GPU任务，无需设备授权；`solver_process_check.json` 已核验。不要重启旧 `continue_native_cpu_slices.py` 或重复提交任何已完成计划。

共171个主运行样本，全部合法、零超用，map与原版串行资格产物逐字节一致，原生及独立原版FULL/STA均通过。另有24组缓存资格，不计入171个主样本。正式性能矩阵120项：frozen/slice/compact/pipeline/bounded五变体，GEMM/elliptic，4/8物理核，rebuild/reuse，三次固定布局的运行重复。前序51项分项/语义门槛不混入正式性能。标量夹具100000组、1551076次字段逐位比较零差异。

**选型：新 bounded 未过预先冻结的整体门槛，不替换既有组内采样CPU主线，默认开关不变。** 本轮frozen是已经优化的CPU，不是原版VPR。GEMM重建，新bounded的四核/八核配对进程速度比中位0.986119× / 1.067711×；八核范围1.007569–1.097116，workflow中位1.032917×。旧pipeline八核进程1.093606×（1.089096–1.095578），workflow1.053725×；bounded相对它0.980365×（0.921328–1.001403），未建立新增方法的稳定增量。旧pipeline四核本轮0.986776×。所有单次数据保留，不能把本轮速度比与历史原版对照直接相乘。

另外一个未过门槛的条件是elliptic四核reuse：bounded进程0.968536×，时间退化约3.25%。缓存路径跳过构建，不能将这个差值直接归因于bounded搜索/插值；共享宿主与其他阶段波动未隔离，但按预定规则保留结果。时间中位数之比不等于配对速度比中位数，报告分别给出。八核GEMM lookahead中位frozen39.34秒、bounded23.34秒、旧pipeline23.28秒，阶段收益不等于完整进程收益。

质量：elliptic全部正式样本CPD10.841ns、线长97461、160轮，路由主体相同。GEMM CPD均13.2667ns；四核线长4095178、15轮，主体相同；八核有4094294/4095178两种线长及15/16轮、两种主体，冻结控制和候选均出现。差异约0.022%，全部合法且符合配对质量门槛；map等价不意味着所有并行路由主体逐字节相同，也不能声称这是lookahead带来的质量改进。

诊断：D0未复现历史约12秒重构退步，不能宣布分配器根因已定位或历史问题已修复。每个大电路仍40次flood、36个不同起点；重复来自跨源层CHANZ，未实现起点复用。原十次GEMM插值累计约0.011秒，重排主要解除了提交依赖。本轮计数器使连续工作区增至168字节，布局隔离同二进制GEMM四核未对齐/对齐调度62.951/37.826秒，计数/map/路由主体相同，支持诊断引发或放大的缓存行争用；这项1.664×不是未诊断算法收益，且未采硬件cache-to-cache计数器。

实现：独立 `vendor/vtr_cpu_slices` 实现切片独立提交、12字节SMALLEST标量单元、有界组批、工作区复用/隔离、原序归并。GCC11对齐fallback128字节，槽stride256。临时预算固定2GiB、工作区估计85MiB；限制结果表和工作区对象数量，不硬性限制整个进程RSS、队列增长或分配器保留。最终 `bin/vpr_aligned` SHA为 `a02448d32451882e5d765f10aeed75d528932aff2a634cf689fcdd1361dd74ab`，来源在 `aligned_source/`。`candidate.patch` 与 `workspace_alignment.patch` 保留。原有solver与GPU默认不变，没有提交git或PR。

审计：`evidence_verification.json` 通过428个冻结文件、24组缓存资格、171个map及路由/质量/亲和性核验；`formal_attribution_audit.json` 通过完整120项覆盖、实际env/顺序、共享缓存、48个互不重叠物理核与同NUMA核组、最终9个源码绑定。PDF/SVG/PNG已生成并检查。`analysis.json`、`acceptance.json`、`conclusions.json` 为终态；`analysis.partial.json` 是保留的中间状态，不作当前结论。进程终态见 `confirmation/supervisor.json` 与 `solver_process_check.json`。早先运行中HANDOFF存于 `HANDOFF.before_finalization.md`。

下一步建议（尚未启动）：先隔离资源确认既有八核pipeline，并扩展留出电路/布局；如继续bounded，再单独定位八核批次尾部等待和工作区生命周期开销。重复起点复用需先精确语义验证。本轮已建立语义等价和临时表数量上界，尚未建立新bounded的稳定整体增益或论文新颖性，不能称为三维专属新寻路算法。方法见 `docs/native_cpu_slices.md`，查新边界沿用下节。下方历史“当前/下一步”以本节为准。

## 2026-11-01 方法查新与可行性分析已完成

用户要求执行创新点分析方案。本轮完成查新、源码依赖分析、历史分项重算和独立语义验证；未修改 solver 源码/二进制、默认开关或既有冻结结果，未启动原生布线/GPU作业。先读[分析报告](docs/native_lookahead_novelty_analysis.md)、[文献与贡献对照](results/native_lookahead_analysis_20261101/prior_work.json)和[下一轮实验规格](results/native_lookahead_analysis_20261101/next_experiment.json)。

贡献边界：FPL2016已有采样式map模型；FPT2024已有搜索内部确定性并行及lookahead应用展望；2026多芯粒论文已有CHANZ和2.5D lookahead代价分解；oneTBB已有有界token/按序输出。BB列表按值传递问题已由上游#3751在2026-08-06报告，不主张首次发现。第二处全量重载漏通知的首发归属未确认。当前不能宣称首创三维lookahead、确定性并行或新pipeline原语。

新发现：三个插值函数始终在固定(from_layer,to_layer,channel,segment)二维切片内读写；原调用全层遍历造成写入冲突，但不代表跨切片数值依赖。此前“必须全局保序”的说法过强，已更正文档，实验实现仍保留原样。两种重排在原生函数提取的2400个合成表、4800次字段逐位比较中零差异；故意改xy顺序和漏填未采样层分别检出1905/1902个失败夹具。覆盖1/2/3/4/8层合成表，不代表已验证任意原生多层器件，也不是新布线性能结果。稳定最小值样本序号检查21825种排列通过；简单最近来源多源合并有丢失相对坐标桶的反例。

历史诊断重算：GEMM串行init0.240893秒/search160.782565秒，init仅占累计工作约0.150%；另一组内并行诊断merge0.066193秒/组墙钟43.126509秒。勿混用线程累计时间与墙钟。历史三元组旧实现/重构组内/pipeline在既有顶层计时之外残差为41.825/53.713/53.189秒，尚未定位具体函数或排除宿主波动。当前pipeline的2P token不限制预分配的G个组结果表。

核对上游master提交4b4a3a8e1597dbbe94250e2ec16ad625c3ea4170（2026-10-30）：保存的map采样仍串行，三个插值函数体与本地相同；不外推至所有分支。脚本`scripts/analyze_native_lookahead_semantics.py`可重现分析；独立C++夹具、编译日志、来源哈希及证据在结果目录。曾遇到GPFS短暂写入等待，验证在本机/tmp完成后归档；初次夹具编译失败日志保留于development，修正NdMatrix遍历接口后通过。

下一步优先诊断GEMM/elliptic的未覆盖阶段、起点重复率和真实峰值内存，再做最小插值重排的原生map等价验证，随后单独比较连续标量表和有界活跃组调度。现有数据不支持把epoch清零或单独归并优化作为主要加速点。论文候选需建立具体方法差异、资源上界和稳定完整流程收益；本轮分析完成不等于新算法已集成或论文创新已成立。

## 2026-10-31 CPU主线证据矩阵已完成（当前，优先）

用户授权的CPU研究方案已执行完成。先读 [最终报告](results/native_cpu_paper_20261031/report.md)、[验收](results/native_cpu_paper_20261031/acceptance.json)、[核心结论](results/native_cpu_paper_20261031/conclusions.json) 和 [PDF图表](results/native_cpu_paper_20261031/figures/cpu_study.pdf)。全部本机CPU实验，无新GPU作业、活动求解或待登录授权；先前GPU结果未改。

九个计划合计294项计划条目，实际290项、284项合法且独立FULL/STA通过，4项按原版失败门槛跳过。6项失败/超时完整保留：原版elliptic重建/缓存两次SIGSEGV，3D compressed_map不支持的SIGABRT预检，MultiQueue elliptic不收敛，以及宽度80 elliptic两侧600秒超时。失败不计算加速比。主矩阵实际146/144合法；架构44/42、pipeline GEMM16/16、五电路扩展30/30、CLSTM质量21/21、同二进制归因3/3、MQ4/3、两组预检8/7和18/18。

主要结果：同四物理核，修复控制到组内采样并行，六电路重建map配对速度比中位数的几何平均为1.350921×，共同缓存为0.994556×。GEMM对原版parallel三次配对中位1.502675×，原版/优化进程中位360.905/240.488秒；lookahead163.46→42.60秒，Routing36.52→37.06秒。因此应定位CPU预计算优化，不称为路由搜索或完整打包布局编译加速。GEMM对修复控制在1/2/4/8核分别0.982/1.269/1.494/1.496×，组内四采样限制扩展性；所有重复保留。

质量：CLSTM修复parallel的CPD7.71292ns相对原版6.58269ns退化17.17%，不能算质量合格地击败原版。独立decomp三次确认恢复至6.42742ns，相对原版decomp6.53755ns改善1.685%，组内采样对原版decomp进程中位1.320012×。decomp是上游已有模式，不算我们的质量创新，也未实现按电路自动挑选模式。elliptic修复/采样在1/2/4/8核均复现10.841ns、线长97461、160轮；原版parallel无合法速度基线。

新候选：`vendor/vtr_cpu_tasks`实现跨组有界pipeline、每线程工作区、原序归并及插值，开关`VPR_HYBRID_LOOKAHEAD_TASKS=1`默认关闭。四核GEMM相对已有组内并行三次中位0.937017×，八核阶段1.924339×但进程仅1.009777×（0.997503–1.015403）、workflow0.995881×。五电路扩展性能不一致，ex5p中位1.222×但reduction0.981×。不替换现有实现，不设按本轮电路结果挑选的自动阈值。

归因单次三元组：旧实现233.235秒、重构后旧调度246.583秒、相同二进制开启pipeline244.159秒；lookahead40.58/40.20/39.88秒。重构控制自身已有额外未覆盖成本，不能把整个候选退步都归因于全局调度，尚未证明分配器或具体函数根因。

审计：`evidence_verification.json`通过503个冻结文件、30组缓存资格、88个计时map的原版串行字节对照，以及合法路由/零超用/独立FULL与STA/亲和性/路由SHA。`implementation_verification.json`记录13项源码补丁及CMake绑定、523条归一化后相同的编译链接命令、1421个实际项目依赖；除预期三个源码文件外只有生成路径、头文件保护名和构建时间差异。6项报告/计时测试通过，PNG/PDF/SVG已生成并检查。`solver_process_check.json`无本轮活动求解。全部进程和收集器均已退出，历史会话ID只作回执。

源码/二进制：干净CPU快照`vendor/vtr_cpu_paper`来自锁定提交`0b912334fdd83bb754b302146ac0d1ec9edc9a0e`，仅两处通知修复和原有lookahead采样并行，无GPU钩子；`bin/vpr_cpu` SHA `5dee5a46baa87f602640d861c778657a20065b0ddf5cd7814f4716dfc7619c62`。新候选`bin/vpr_tasks` SHA `b8c71632175d26ca90862242326aea90ebbcffb1656b11e17cf73cba6ea30003`；`vpr_tasks_samples`是相同内容硬链接，用于单次同二进制归因。补丁、来源、构建命令和依赖清单在结果目录；tasks源码的便利build链接已指向实际独立`build_cpu_tasks`，未改变实验源码或二进制。所有优化及GPU默认开关未改变。

边界：只有六个原有电路和固定布局seed的运行重复；Hecate单/双层、宽度80/100/120是配置变化，不是新独立电路。W100图除XML首行元数据外与原输入相同。compressed_map只在2D比较，MQ仅探索；不宣称全面胜过SOTA。CPU核组配对且使用不同物理核，但宿主/内存共享，没有资源独占；最终论文确认仍需更多独立基准、架构、布局种子和隔离测量。方法见`docs/native_cpu_paper_study.md`、`docs/native_cpu_sample_pipeline.md`。

下一步：保留组内采样为CPU主线候选，公平复用有效缓存；先给重构版本新增的未覆盖成本做分项定位，诊断样本与正式计时分开，再决定结构/调度改进。CPU可以独立作为研究主线，GPU保留后续扩展，不以GPU单独获胜为论文门槛；本轮不保证新颖性或论文就绪。下方历史“当前/下一步”状态以上述终态为准。

## 2026-10-31 前驱修复、elliptic质量与GEMM优化已完成（优先）

先读 [最终报告](results/native_repair_20261031/report.md)、[验收](results/native_repair_20261031/acceptance.json)、[完整分析](results/native_repair_20261031/repair_analysis.json) 和 [方法说明](docs/native_repair_and_lookahead.md)。本轮按用户指定顺序执行完成，没有活动求解/作业或待授权登录。

两处并行状态根因已修复：`dynamic_update_bounding_boxes` 输出列表按值传递丢通知；拥塞模式全量 `load_route_bb` 在分区更新之后发生且漏通知。诊断捕获网络1120/1473同时写RR207790；仅修第一处后第51轮分区包含检查失败，完整失败/core保留。现在引用输出并在所有框变化后更新分区归属。加入可关闭标签审计、分区包含与无效前驱/循环链检查。不能倒推旧core的精确写者；历史native CPU SIGKILL原因仍未知。

elliptic CPU修复诊断、关闭诊断并行、guard及新lookahead+审计均复现160轮、CPD10.841ns/线长97461，路由主体SHA相同。最终同轮原版串行质量参考11.2895ns/99232；batch三次CPD9.47146/9.34943/9.85051ns、线长97503/95686/96207，均合法且独立FULL/STA通过。batch进程中位214.610s，慢于guard单次145.586s；质量恢复，不声明elliptic加速，也不以串行替代原版并行速度基线。

GEMM同一H100节点、相同4物理核[48,49,50,51]，GPU服务线程也计入该集合，三轮原版四线程/联合batch均合法。进程中位368.612→250.490s，约1.472×、缩短32.0%；统一独立回验workflow中位552.072→432.367s，约1.277×、缩短21.7%。三轮进程加速1.468/1.472/1.482×，workflow1.273/1.277/1.278×，CPD均13.2667ns，线长略降。符合本电路联合收益目标，不要求GPU独立胜过改进CPU。补充单次改进CPU239.298s/workflow421.457s，比batch快，尚未证明GPU额外收益。

主要收益来自 `VPR_HYBRID_LOOKAHEAD_PARALLEL=1` 的独立采样并行，lookahead中位170.02→41.67s；Routing36.50→46.33s。分项诊断40次搜索约160.783s、初始化0.241s；独立工作区、按原顺序合并保留相同delay时首个congestion。ex5p/GEMM串并行wire map逐字节相同、CPU路由主体相同；GEMM wire map SHA `458b7439c7fb2bd2ffae133d2d5cb89e3d3428c8893f83afc3aa4a8cc7501e8e`。候选二进制SHA `e170ffd67fc3f5967812c766de7441f1e1a809d8c7edcda9043b40880caf2fb1`，冻结源码/二进制在 `lookahead_source/`。新开关默认关闭，GPU默认仍关闭，阈值/窗口/kernel/所有权保护未改。

最终作业 `job-24c95d0b-ea7b-4519-8d27-5c51344b8a4b` 已job_succeeded；12/12归档路由哈希、独立FULL/STA、零超用、输入SHA和CPU亲和性通过，152冻结文件及345条CUDA oracle路径通过。GEMM真实提交325次且全单查询；elliptic提交24679次、仅3个双查询批次；全程零GPU error/fallback。首轮诊断作业 `job-15c01245-26c7-4ef8-b6d6-ec309a84a079` 也已成功；首次最终确认 `job-931b0f52-b1dd-4641-aa72-f3efb21d9ac1` 在归档预留时配额失败，零求解样本，所有回执保留。

最终作业遇到1651次live镜像配额错误，约18:14起镜像停更，但求解继续并成功归档。`live_status.json` 的终态记录仍只有9项可见结果，**完整12项以 `phase2_metadata/run`、`final_status.json`、`evidence_verification.json` 为准**。归档1056050939字节，SHA `6213c60b7de7ef449d3ce96fdbccd73ed4dc8890a736c37836047ad16ef04ac6`，终态后验证迁入 `results/native_archive_store_20261031/archives/phase2_artifacts.tar.gz`，原项目路径保留链接；未来worker需重新暂存global_user归档。当前冻结输入包仍worker可见。见归档审计、迁移及镜像诊断记录；相邻源码项目未改。

下一步优先做改进CPU重复和多电路验证，确定新lookahead默认策略；GPU再优化准备成本和独立长查询释放，用真实接管回放及同核完整流程验收。不要把本轮结果泛化成所有电路或GPU独立加速。构建及22项脚本回归通过；所有测量、失败、完整归档和来源绑定见本轮结果目录。下方历史“当前/下一步”状态按本段覆盖。

## 2026-10-30 四核联合确认已完成（当前状态，优先）

本轮预声明分析与实验已完成，研究目标“同 CPU 核预算下联合方案端到端优于原版并行 VPR”尚未达到。先读 [最终报告](results/native_joint_confirmation_20261030/report.md)、[验收](results/native_joint_confirmation_20261030/acceptance.json)、[完整数据](results/native_joint_confirmation_20261030/analysis.json) 与 [当前目标](docs/native_joint_objective.md)。不要求 GPU 独立胜过改进 CPU；本轮不达标来自全流程实测与质量结果。

同一 H100 节点、相同四个物理核 `[32,33,34,35]`，原版并行/native CPU/guard/batch 共完成 GEMM 三轮 12 项和 elliptic 初筛 4 项。GPU 服务线程也计入四核集合；关闭重型诊断，算法源码、二进制和接管参数未改。13 项成功结果通过独立 FULL/STA 及归档路由哈希校验；全部 16 项 CPU 亲和性检查通过。计时边界见 [实验说明](docs/native_joint_confirmation.md)。

GEMM 全部合法，原版/native CPU/guard/batch 进程中位数分别 **337.638 / 346.238 / 347.497 / 349.797 秒**，workflow 为 **494.892 / 506.959 / 507.490 / 508.377 秒**。batch 三轮分别比同轮原版慢 **8.22%、1.30%、2.04%**；CPD 均 13.2667 ns，线长略降。没有已证明的 CPU 算法收益或当前联合加速。batch 共提交 328 查询、327 批，仅一批大小 2；GPU 准备每次约 3.58 秒，去重后的搜索主机调用累计每次约 0.36–0.43 秒。原版 lookahead 中位数 164.76 秒，布线仅 34.65 秒，应从全流程选择优化位置。

elliptic 原版 SIGSEGV（104.481 秒）、native CPU SIGKILL（467.785 秒，未达到 900 秒超时，原因未定）；guard 到 200 轮仍有 1 个超用 `CHANY 245362`，涉及网络 353/2529。batch 在 157 轮零超用且独立 FULL/STA 通过，进程 182.037 秒、workflow 184.429 秒，CPD **13.6102 ns**、线长 98,441。它提交 7,264 次 GPU 结果，全部单查询，无错误/fallback。原版同轮未合法完成，不能计算有效加速比。另核对五项输入 SHA256，与此前合法串行参考完全一致；相对其 11.2895 ns，CPD 增加 **20.56%**。历史质量对照不替代同轮并行基线，不计算跨作业时间比。按预声明门槛跳过 elliptic 后两轮性能重复。

原版 core 已保存并离线定位：`RouteTree::add_subtree_from_heap(...)+602` 使用 `0xffffffff` 无效边索引，计算地址与 SIGSEGV 故障地址一致。另一线程同时扩展搜索邻居。上游无效前驱的来源仍未证明；并发状态干扰是待验证假设。详见 [崩溃分析](results/native_joint_confirmation_20261030/crash_analysis.json)、[堆栈](results/native_joint_confirmation_20261030/diagnostic_core/backtrace.log)。调试器位于本轮 `debugger/sysroot/usr/bin/gdb`，只解包到项目目录；官方软件包哈希已校验。不得将 native CPU 的 SIGKILL 写成已证明的 OOM/死锁。

当前保留既有 CPU 默认和所有权保护，不启用本轮 batch 为默认。下一轮先记录并行前驱写入归属/版本、无效边和循环链，以及峰值内存/cgroup memory events，恢复 elliptic 稳定性和 CPD；GEMM 分解 lookahead 内部成本，评估 CPU 并行、数据结构或粗粒度 GPU 预计算；之后复用已验证 H3DTAK2 快照优化 kernel 与受保护任务释放。缓存公平提供给原版，规则使用上线可取得的特征和独立留出样本，最后按联合全流程收益验收。

两个本轮作业均已终态：[作业登记](results/native_joint_confirmation_20261030/job_registry.json)。首次 `job-062be586-84f5-4b1f-b470-cee751d0d6d4` 因配额导致镜像异常失败，零可用完整测量；正式作业 `job-40d82c0f-83d1-46c0-a4f3-cb73fa2ceaa5` 为 `job_succeeded`，没有待观察的运行作业。正式作业仍记录 19 次镜像配额错误，但修复后的镜像不会中断求解，完整归档与校验成功。

归档 SHA256 为 `ba4197c7ad0ef35f55e4d237ac6b6ffa782fcf6716e9f6e0509df1deecb2d0d8`，实际 CUDA 库为 `a928e2c8a65f470e293ee3147189b9814d1c62a38902eb150b42063cb3ae36a5`，CPU 二进制仍为 `fb0379ea7f4bced9ec5312c395930e6ceeca12aeb5a5ac3804cccdcef0bd1b3e`。证据见 [归档审计](results/native_joint_confirmation_20261030/archive_audit.json)、[来源绑定](results/native_joint_confirmation_20261030/provenance.json)。已结束的大型生成归档及既存旧 core 经 SHA256 验证移到 `results/native_archive_store_20261030/`，原项目路径保留软链接，相邻源码工程未改；未来 GPU worker 需重新暂存这些 global_user 归档。迁移、硬链接去重及旧 core 的记录均在该目录，详见本轮报告。

本轮之前与运行中的 HANDOFF 分别保存在 `results/native_joint_confirmation_20261030/HANDOFF.before_confirmation.md` 和 `HANDOFF.running.md`。下方历史记录保留，其“下一步/当前作业”状态按本段覆盖。

## 2026-10-30 公平基线补充（优先于下方早先表述）

已从源码及旧作业核实：锁定原 VPR 本身支持 `--router_algorithm parallel --num_workers 4`，当前 batch 复用它的分区树/TBB 并行框架。启用四工作线程不能作为我们的新算法贡献。主对照应是相同 CPU 核预算的原版并行 VPR，明确额外 GPU；单线程作为补充。GPU 服务线程也要计入总 CPU 预算。

联合优化目标保持不变：CPU 改进与 GPU 改进都算整体收益，不要求 GPU 独立获胜；但不能只击败人为选定的原版单线程，就宣称超过原版已有并行能力。旧同一 GEMM 作业 `20261028-002456` 为原版单线程 401.353 秒、原版四线程 356.545 秒、当时 batch 362.105 秒。不得把这些旧时间与新作业 318.183 秒混算。

下一步 GEMM 确认以同节点、同 CPU 预算的原版并行/我们的 CPU 控制/联合方案为主矩阵，关闭诊断并重复测量；单线程补充报告。详见 [当前目标与计划](docs/native_joint_objective.md)、[并行能力及对照证据](results/native_objective_20261030/fairness.json)。前一版文件保存在 `results/native_objective_20261030/HANDOFF.before_fairness.md`，历史实验记录保持不变。

## 2026-10-30 用户澄清：以 CPU–GPU 联合收益为主目标

优先读 [联合优化目标与调整后的计划](docs/native_joint_objective.md)。CPU 算法/并行调度和 GPU 的收益都计入联合方案；理想是 `T_joint < T_improved_cpu < T_original`，可接受目标是质量合格且 `T_joint < T_original`。不要求 GPU 必须单独胜过我们的改进 CPU，才能认可联合方案收益。CPU/guard 对照用于归因和选型，不是新增 GPU 独立贡献的验收门槛。

GEMM 单次诊断中，原 VPR 单线程 349.626 秒、四 CPU 加 GPU 的 batch 318.183 秒（观测进程时间短约 8.99%）；统一独立回验 workflow 501.989/472.605 秒（短约 5.85%）。结果合法，应作为联合收益候选。下一步优先关闭诊断后做同节点重复确认，并报告原版四线程与 CPU 控制；当前缺的是稳定的正式确认，不是必须排除 CPU 贡献。优化范围包括 CPU 调度、lookahead/数据处理与 GPU kernel，按全流程收益安排优先级。

以下历史结论中的“不能归因为 GPU”仅限制对 GPU 独立增益的解释，不能据此否定 CPU–GPU 联合收益。原始数据、旧报告及其绑定保持不变。本次记录见 [clarification.json](results/native_objective_20261030/clarification.json)，修改前的交接见 [HANDOFF.before_clarification.md](results/native_objective_20261030/HANDOFF.before_clarification.md)。

## 2026-10-29 原生诊断接续结果（实验状态保留，目标以上方为准）

分项计时、真实接管捕获、组批原因诊断已实现，并完成 elliptic/GEMM 的 H100 验证。先读 [本轮实测报告](results/native_diagnostics_20261029/report.md)、[验收记录](results/native_diagnostics_20261029/acceptance.json)、[实现与计时口径](docs/native_diagnostics.md)。本轮五个新作业全部终态，见 [新作业登记](results/native_diagnostics_20261029/job_registry.json)；前轮 25 作业登记保持原样。

默认仍为原生 CPU，未证明端到端 GPU 加速。未额外捕获的同状态配对样本中，elliptic CPU 剩余搜索累计 122.851 秒、GPU kernel 183.044 秒、完整交接 193.563 秒；GEMM 为 0.230372/0.408514/0.687763 秒。GPU execute 内 kernel 占比约 99.3%/96.2%，暂不优先做 pinned/异步复制。

真实捕获格式为 **H3DTAK2**，GPU ABI 为 **3**。576 个完整快照、1,728 次原生 CPU 重复和 2,304 条 GPU 回放路径全部通过；CPU 路径与原版一致，独立 FULL/STA 通过。早期 v1 漏树根的失败已保留，v2 拒绝 v1；不要用旧快照冒充完整状态，也不要混配 ABI。当前 VPR SHA256 为 `fb0379ea7f4bced9ec5312c395930e6ceeca12aeb5a5ac3804cccdcef0bd1b3e`；最终 CUDA 库、冻结源码和大型快照在 [归档审计](results/native_diagnostics_20261029/archive_audit_v2.json) 指向的工作包/归档中，本地只提取小型证据。

elliptic/GEMM batch 分别 7,872/118 批，全部大小 1；elliptic 97.7% 出现在父分区尚未释放子分区时。elliptic batch 在 200 轮仍有 5 个超用节点，不能计算成功加速；GEMM batch 合法，但四线程 CPU 贡献未隔离，不能称为 GPU 收益。保护范围、接管阈值及路由算法均未改动。

下一步应基于这批可重复快照定位 kernel 内部扫描/扩展/跨 block 同步的成本，再研究现有保护下更细的独立任务发布。不盲扫既有 block/阈值参数，不删除所有权保护。任何新接管规则都要用可在线取得的特征、独立留出样本和同节点原版/四 CPU guard 对照，满足合法零超用、CPD/线长 +5% 门槛及完整重复确认后再考虑启用。GEMM lookahead 构建约 143.55 秒，若另做复用，必须公平复用基线。

当前本机构建与针对性测试通过，最终 GPU 作业成功，无待运行作业。源码和新报告绑定见 [provenance.json](results/native_diagnostics_20261029/provenance.json)。原始交接文本完整保存在 [HANDOFF.previous.md](results/native_diagnostics_20261029/HANDOFF.previous.md)。

## 以下为本轮开始前的交接原文（历史状态）

以下“尚未实施”“当前二进制”等描述对应本轮开始前；以本文件上方和本轮报告为当前状态。

交接日期：2026-10-29。工作目录：`/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects`。

用户要求做好交接，在新对话继续。本轮只整理记录和保存源码快照，没有修改路由算法、迁移工程或提交新任务。上一轮实现与验证计划已经完成；研究目标“相对原 VPR 获得质量可接受的端到端 GPU 加速”在原生异构后端上仍未达到。

## 接续时先读

1. 本文件，尤其是“下一轮具体工作”和“计时与正确性边界”。
2. [上轮验收](results/native_hybrid_acceptance_20261028.json)、[逐项工作记录](results/hybrid_work.json)。其中 `complete` 指上轮计划执行完毕，不表示性能目标已达到。
3. [最终对照报告](results/native_hybrid_comparison_final.json)、[项目说明](README.md)。最终报告含 18 轮 H100 原生异构实验中的 91 项测量，另附 6 次本机 CPU 重复诊断。不能把不同配置的数据拼成同一次实验。
4. [本次交接快照与校验](results/handoff_20261029/bindings.json)、[最新讨论的数据依据](results/handoff_20261029/followup_analysis.json)。

25 个已提交原生 GPU 作业均有终态回执，见 [作业登记](results/native_job_registry.json)。交接时检查本项目没有遗留路由、编译或实验脚本进程；检查排除了检查脚本自身。相邻项目可能仍有其他任务，不属于本任务，不能停止。没有待完成的设备登录步骤或需恢复的监控会话。

## 用户目标与已有结论

目标是在真实三维 FPGA 架构、固定网表、布局和资源约束下，保留可接受的质量，以原 VPR 为基线验证端到端加速。当前采用关键路径和线长各不超过 5% 退化的门槛；连接合法、零超用和 VPR FULL/STA 回验必须通过。用户接受轻微质量退化，但要求加速明显、对比公平。

工程有三条不同实现，必须分清：

| 实现 | 状态与结论 |
| --- | --- |
| 早期整数代价 CPU/CUDA/HLS 原型 | 曾相对旧 CUDA 加速 16.86×、四线程原型 CPU 加速 7.91×；不是超过原 VPR 的证据。 |
| 独立 `cpu_target` / `cuda_target` 后端 | elliptic 子树配置有三次完整流程约 2.181–2.247× 的确认；见 `docs/target_results.md`、`results/h3d-target-confirm-subtree-20261027-221003/confirmation.json`。这条后端与当前原生集成不同。 |
| 当前 VPR 原生 CPU/GPU 后端 | 保留原生 STA、关键度、MapLookahead、路由树与拥塞协商，实际选择性接管、独立网络组批和 CPU/GPU 重叠均已实现；尚未证明端到端 GPU 加速。 |

默认继续使用原生 CPU。不设置 `VPR_HYBRID_LIBRARY` 时不会启用 GPU。2048 次 CPU 堆弹出的接管阈值是实验参数，不是已经验证有收益的自动调度策略，见 [调度结论](results/native_dispatch_policy_20261028.json)。

## 已实现的原生架构

CPU 先执行原生 A*。超过预算后，传给 GPU 的是未展开的活跃堆前沿，以及已访问标签、原生代价、前驱和树前缀信息。GPU 返回后，CPU 验证路径连通性、前缀、边界和代价，再交回 VPR 原生路由树与时序更新。异常时保留 CPU 原堆以继续搜索，报告 fallback/error，不能静默把失败算作 GPU 成功。

资源图、MapLookahead 模型、占用与历史拥塞驻留 GPU。CPU 在修改点记录不可变状态增量；GPU 服务线程只在批次之间应用增量，不在执行期间读取并发修改的 CPU 状态。原生分支使用浮点目标，不再使用早期原型的饱和整数拥塞代价。

| 模式 | 用途 |
| --- | --- |
| `select` | CPU 超预算后逐查询接管并提交 GPU 路径。实验脚本中的变体名为 `hybrid`。 |
| `pair` | 同一部分搜索状态交替 CPU→GPU/GPU→CPU 测量，保留 CPU 路径，不提交 GPU 路径。属于诊断。 |
| `batch` | 原生四线程空间分区路由加独立 GPU 服务线程，最多 4 个不同网络的独立查询，默认 50 µs 组批窗口。 |
| `guard` | 使用与 batch 相同资源所有权保护的纯 CPU 控制，不初始化 CUDA。 |

资源所有权覆盖当前网络搜索框与保留旧路由树的资源。在 `should_route_net` 读取占用之前取得，持有到拆线、搜索、校验、提交及占用更新结束。冲突等待，同一网络的树上连接仍顺序处理。曾经只覆盖当前搜索框，在 elliptic 后期遇到旧树越界；已修复，并保留了失败运行。

CUDA 使用惰性 epoch 标签、128 位 CAS、原生启发代价缓存、warp 聚合入队。普通批次每查询一 CTA；设置 `H3D_GPU_COOPERATIVE_BLOCKS=64` 后，单查询且种子数达到门槛时使用多 block cooperative 搜索。每批多个查询仍采用每查询一 CTA。8/16/64 block 已测量，不要重新盲扫相同参数。

限制：GPU 支持已核验的零节点 RC、零开关 R、非 flat MapLookahead、SM90/H100；不支持通用 RC、RCV/bus-mux 或 interposer lookahead。并行模式还要求无非配置跨区资源组、基本代价不随扇出变化。不能把已验证结论外推到所有三维 FPGA 架构。

## 关键实验结果

六电路主实验使用同一接管配置，记录原 VPR 单线程、原生 CPU 控制、选择性 GPU、原 VPR 四线程、原生四线程控制和 batch。每个案例各变体在同一 GPU 工作节点顺序测量，输入固定。完整矩阵见 [主实验索引](results/native_hybrid_matrix_20261028.json)。

| 案例 | 原 VPR 单线程秒 | 选择性 GPU 秒 | 原 VPR 四线程秒 | batch 秒 |
| --- | ---: | ---: | ---: | ---: |
| ex5p | 5.723 | 5.723 | 5.572 | 6.323 |
| softmax | 16.539 | 16.585 | 15.083 | 15.584 |
| CLSTM | 61.542 | 62.491 | 55.882 | 56.690 |
| reduction | 118.263 | 120.320 | 110.448 | 113.604 |
| GEMM | 401.353 | 406.503 | 356.545 | 362.105 |
| elliptic | 167.921 | 600 秒超时 | 150.106 | 旧树所有权检查失败 |

这些是完整 VPR 进程时间，含输入加载、路由和原生 FULL/STA，不是仅内核时间。前五例选择性版本 CPD 与原串行 VPR 一致。ex5p/softmax/reduction 没触发 GPU；CLSTM/GEMM 分别提交 10/129 个 GPU 搜索结果。四线程 CPU 带来的收益不能归因于 GPU。

elliptic 后续优化的同机配对：

| 运行 | 原 VPR 秒 | 异构秒 | CPD 原版→异构 ns | 线长原版→异构 |
| --- | ---: | ---: | --- | --- |
| `004249`，64-block 选择性接管 | 159.120 | 190.944 | 11.2895→10.4304 | 99232→97267 |
| `012018`，最新所有权修复后的 batch | 167.121 | 215.723 | 11.2895→10.66 | 99232→97448 |

运行完整前缀是 `results/h3d-native-hybrid-20261028-`。这两项候选通过 FULL/STA；`004249` 整个实验脚本标记 failed，是当时严格比较原版/原生四线程路径哈希的检查触发，且其旧 batch 还有所有权检查失败，不能隐藏这些情况。

`012018` 的相同保护机制纯 CPU `guard` 在 200 轮后仍有 1 个超用节点，145.089 秒是失败运行，不能用作合法加速比分母。该轮 batch 提交 8565 个 GPU 查询，全部批次大小为 1，CPU 在 GPU 工作期间完成 137 个独立查询；状态稀疏更新约 21.793 MB，逻辑查询上传约 964.086 MB，另外还有静态图和初始状态上传。

真实组批证据是 `002054` 的低阈值 softmax：95 个多查询批次、最大批次 4、GPU 工作时 CPU 完成 18356 个查询。它证明机制真实执行，不证明当前阈值下的端到端收益。

正确性证据包括最新 CUDA 回放 645 条路径验证，以及 ex5p/softmax 共 60 个、elliptic 168 个迭代屏障的全节点占用/历史对照。屏障审计属于诊断，不参与性能结论。

本机三次四线程重复：原版 VPR 为一次合法、一次 SIGKILL、一次 SIGSEGV；修改版纯 CPU 为一次 SIGKILL、两次超时。见 [CPU 重复记录](results/native_parallel_cpu_repeats_20261028/summary.json)。出现过高内存占用，但信号原因未查明，不能直接写成 OOM 或正常拥塞不收敛。本机时间不能与 H100 时间计算加速比。

## 最新讨论得到的判断

用户问过迁到 SSD 和集群 CPU/GPU 通信是否能解决性能问题。核验结论如下：

- 工程位于 GPFS 共享 HDD；CPU/GPU 在单实例作业内通过本机 CUDA 协作。数据通路是共享存储→节点内存↔同节点显存，不是每次搜索都跨节点 RPC。资源调度排队时间未计入路由进程时间。
- 资源图载入后在内存/显存访问。源码目录在 HDD 不等于每次图节点访问都读盘。
- `004249` elliptic 原版路由阶段 153.27 秒、异构 184.98 秒；进程差距约 31.82 秒中，路由阶段差距约 31.71 秒。仅改善输入加载无法消除差距。
- GEMM 资源图加载 51.92 秒，含解析/建图，不能全部算成磁盘等待；lookahead 构建另需 161.86 秒，主要是计算。缓存复用应同时给 CPU 基线和异构版本使用。
- `/inspire/ssd` 目录存在不等于当前节点已挂载本地 NVMe；本次对该目录的 `findmnt` 只显示 overlay 父挂载。SSD 对照需要在实际 GPU 节点核实设备/挂载、暂存全部实际输入路径并单独记录暂存时间。尚未做 SSD 性能实验，也未整体迁移项目。
- 当前 `native/gpu_engine.cu` 使用普通主机缓冲区、多次同步 `cudaMemcpy` 和默认流；没有完整的 pinned/异步传输流水。已有 `search_ns` 包含上传、执行、同步与回传，不能称为纯 kernel 时间，现有记录不足以确定传输占比。

新核验的 `004249/elliptic_0_pair/hybrid.json.queries.csv`：141 个热查询中 GPU 胜出 15 个。CPU 剩余耗时至少 30 ms 的 17 个查询中只胜出 6 个；该组 CPU 总计 0.954075 秒、GPU 完整交接总计 1.082372 秒。因此仅提高接管阈值仍无总体优势。详见 [计算结果](results/handoff_20261029/followup_analysis.json)。

此前“长查询存在资源依赖所以不能组批”的表述需要收紧：单查询批次只证明当前空间分区、保护范围和调度没有形成批量，并未证明所有长查询天然无法并行。下一轮要记录具体原因后再判断。

## 下一轮具体工作

以下是已向用户说明、尚未实施的新计划。新对话应从这里推进，不要把此处当成已完成结果。优先改测量和执行通路，再决定接管策略。

1. **完整拆分一次接管的时间。** 在 `h3d_native_runtime.cpp` 和 `gpu_engine.cu` 中区分 CPU 状态整理、排队、H2D、设备更新、搜索 kernel、D2H、同步等待及 CPU 校验提交。结合 CUDA events 与主机时序，避免把异步更新成本错归到后续同步调用。每批记录唯一批次 ID，避免多查询共享耗时被重复累加。可选小样本 Nsight Systems；诊断与正式测速分开。
2. **捕获真实 CPU 接管点并稳定回放。** 保存图/模型版本、占用历史状态、完整已访问标签、前驱、活跃堆前沿、树前缀时序、关键度、目标与边界、原生浮点参数。覆盖胜出和失败样本，在同样状态下重复原生 CPU 剩余搜索及 GPU 完整交接。不要只收集已知赢家。当前 `resident_replay.cpp` 的 1/4 copies 是重复槽位正确性 oracle，不是实际独立网络吞吐实验；旧快照格式/回放未完整表达当前 CPU 部分堆前沿，不能直接充当这一步已经完成。
3. **根据计时只改主要成本。** 若整理/传输/同步占主导，测试预分配复用、合并小传输、有限 pinned 缓冲区、依赖正确的异步流水；若纯 kernel 仍慢，优化重复展开、活跃前沿组织和多 block 同步。每次改动保留同状态 CPU 对照和原生代价/路径验证。不能预设 pinned 或 streams 一定有效，也不能给有依赖的同树搜索强行并行。
4. **诊断为什么没有组批。** 记录同时就绪的长查询数量、分区阶段、保护域冲突、等待者、工作线程可用性、队列深度及批次分布；区分原生分区调度没暴露工作、保护范围过于保守、就绪工作确实不足。先保留现有保护，证据充分后才考虑更细依赖检查或调度修改。不要直接删除锁来扩大批次。
5. **先 elliptic/GEMM，后六电路。** elliptic 检查长查询与组批；GEMM 检查初始化/传输和 lookahead 构建。SSD 为配套环境对照，原 VPR 与异构版用同一节点、同一存储条件，分别记录首次与缓存后运行；不优先复制整个工程。若考虑 lookahead 缓存，基线必须同等缓存。
6. **建立并验证接管规则。** 只能用接管前可获得的特征，如活跃前沿、扩展速率和独立就绪查询数；CPU 最终剩余时间是事后诊断数据，不可作为实际调度特征。调参和验证按网络/迭代隔离，避免同查询重复泄漏。先有留出样本中稳定的完整交接收益，再启用规则，回到完整流程至少三次重复。

接受条件：合法、零超用、FULL/STA 通过；CPD 与线长各在原版 +5% 内；原生完整进程和统一独立回验后的完整流程都要有可重复收益。失败、超时、GPU fallback/error 和暂存成本完整报告。若纯 GPU kernel 仍普遍慢于 CPU，应重新评估更粗粒度对象，例如批量 lookahead 预计算，并与缓存复用后的 CPU 基线公平比较，而不是无限调整接管阈值。

## 代码与工具入口

项目根目录不是 Git 仓库。原生 VPR 的独立可写 checkout 是 `vendor/vtr_hybrid`，保留了未提交改动及 4 个新文件，不要 reset/clean。

| 路径 | 作用 |
| --- | --- |
| `vendor/vtr_hybrid/vpr/src/route/h3d_native_runtime.cpp`、`.h` | 原生接管、所有权、服务队列、状态日志、路径校验、计时。 |
| `vendor/vtr_hybrid/vpr/src/route/h3d_native_profile.cpp`、`.h` | 查询统计、模型与快照导出。 |
| `serial_connection_router.cpp`、`route_net.tpp`、`route_common.cpp` | 部分堆交接、网络所有权生命周期、占用/历史更新钩子。 |
| `native/gpu_engine.cu`、`gpu_api.hpp` | CUDA 常驻模型、搜索、更新与 ABI（当前版本 2）。 |
| `native/hybrid_snapshot.hpp`、`model.hpp`、`model_io.hpp` | 快照及原生目标模型。 |
| `native/resident_replay.cpp`、`replay_cpu.cpp`、`replay_cuda.cu` | 回放与路径/代价验证。 |
| `scripts/run_native_hybrid.py` | 同节点基线/控制/异构全流程和独立回读。 |
| `scripts/submit_native_hybrid.py` | 冻结源码、二进制、实际 CUDA 构建来源；查询资源、验证并单次提交。 |
| `scripts/run_native_replay.py`、`submit_native_replay.py` | CUDA 编译和快照正确性回放。 |
| `scripts/report_native_hybrid.py`、`scaling_common.py` | 正确计时口径、同轮比较、排除虚假 GPU 收益。 |
| `scripts/check_native_jobs.py` | 只读、有限时状态观察；缓存终态，不重提或停止任务。 |
| `scripts/audit_native_artifacts.py` | 冻结源码、实际库构建来源和输入哈希审计。 |

原版 VTR 基准提交：`0b912334fdd83bb754b302146ac0d1ec9edc9a0e`。

- 基线锁：`../FPGA_accelerate_FPGA/G_3d_routing/configs/vpr.lock.json`。
- 原版可执行文件：`../3D_FPGA_routing/artifacts/bin/baseline/vpr`，SHA256 `37cc22c8b1b5d9d378e25379e85afcb7e56b5f1f6f72e3e9186e5e107ed5ce62`。
- 当前修改版：`build_native/vpr/vpr`，SHA256 `e824ffa54e493503ad7fd9c5e3484ca7932a612b30b8e688b9db8d256ee5869a`；交接时核验与 `results/native_hybrid_source_20261028-012018/vpr` 一致。
- 当前已验证 CUDA 库：`results/h3d-native-replay-20261028-003909/libh3d_native_gpu.so`，SHA256 `68755fcf0fcbd2e12b31ad6af253c229124db2024d29f6a88cc6a47607f3df35`。
- 该库实际构建源码：`results/hybrid_replay_source_20261028-003909/native/`。修改 CUDA 后必须重新构建/回放验证；不能把新源码配上旧库声称已测试。
- 实验集：`jobs/target_suite_20261027.json`；运行库配置：`data/vpr_runtime_20261025/runtime.json`。

已有配置的增量构建与针对性验证：

```bash
cmake --build build_native --target vpr -j12
python3 -m unittest discover -s tests -p test_native_hybrid_reporting.py -v
python3 -m unittest discover -s tests -p test_scaling.py -v
git -C vendor/vtr_hybrid diff --check
```

上一轮报告测试 8 项、scaling 测试 3 项通过，原生 CPU 构建及真实 GPU 回放/回验已完成。交接仅新增文档/快照，不重跑耗时实验。不要因为接续对话就重新跑全部测试或六电路基准。

需要重建 CMake 配置时，原配置为：

```bash
cmake -S vendor/vtr_hybrid -B build_native -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DVPR_USE_EZGL=off -DVPR_USE_SERVER=OFF \
  -DWITH_PARMYS=OFF -DWITH_MOSAIC=OFF -DSLANG_SYSTEMVERILOG=OFF \
  -DWITH_ABC=OFF -DVTR_IPO_BUILD=off -DVPR_ENABLE_INTERCHANGE=ON
```

GPU 提交前先用各脚本 `--help` 核对参数，先读 Inspire skill。不要直接重跑旧 manifest 或覆盖旧结果目录。提交器使用历史模板并查询实时资源，新对话仍须核实项目、镜像、规格可用。

## 计时与正确性边界

- `native_process_seconds`：完整 VPR 进程，包含加载、原生路由、FULL/STA。
- `workflow_seconds`：在上项基础上增加统一执行的锁定原 VPR 独立回读等流程。不要把两种时间混用。
- `routing_seconds`：VPR 的路由阶段；不能把这个时间与另一方案的完整流程比较。
- 旧摘要 `search_seconds` 对并行 VPR 曾只取最后一个工作线程计时器，可能严重偏小。最终报告已重新解析原始日志，使用各实例计时之和；这是含等待的 worker-seconds，不是并行关键路径墙钟或纯 CPU 时间。原始历史摘要未改写。
- GPU `search_ns` 是 execute 调用墙钟，含复制、执行、同步、回传；`update_ns` 也不能保证包含异步更新内核的完整执行。尚需下一轮分项测量。
- batch 的各查询可能记录同一个批次耗时，不能无条件逐查询相加。
- `state_bytes` 只是稀疏状态变化，不包含静态图、初始状态、种子/活跃前沿上传及结果。逻辑 payload 也不等于硬件测得的总线流量。
- `pair`、全状态审计和 `--max-offloads` 有限接管检查均属于诊断/冒烟，不作为完整性能结论。
- 基线不合法、超时、崩溃时不得计算加速比。CPU 并行收益、零 GPU 接管的计时噪声、独立回验偶然更快均不得称作 GPU 收益。
- 原版/修改版串行与 pair 要求保留 CPU 路径一致；原生四线程路径不稳定已留记录，不能忽视失败，也不能把任意路径差异直接归因为源码改坏。

## 工作范围与运行约束

相邻 `../3D_FPGA_routing` 和 `../FPGA_accelerate_FPGA` 仅作为冻结输入/基线来源，不修改。根目录现有 README 和验收报告有哈希绑定；本次未修改它们。后续若改文档/源码，应创建新轮次记录，不能回写旧结果来让审计“通过”。

GPU 工具技能：`/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/skills/inspire-gpu-submit/SKILL.md`；辅助 CLI 为同目录 `scripts/inspire_gpu.py`。长任务监督技能是 `.../skills/long-run-supervision/SKILL.md`。本机无 CUDA/GPU，通过 Inspire H100 作业构建运行。此前设备授权曾成功，当前有效性需按实际响应判断；不能沿用聊天中的旧设备码，更不能索要聊天密码/令牌。

前轮 Luna 自动监督能力不可用，已告知用户；有限时轮询，不自动重复提交或重启。提交响应不确定时按唯一作业名与回执核对，不能直接再次 CreateJob。不要停止其他任务。新任务须保存源码、输入、二进制与库来源，日志和终态回执。

用户要求 FPGA/RTL/Vivado/HLS 工作主动判断 Ross Skills 与 `vivado-mcp`，使用前读对应 SKILL.md。当前纯原生 CPU/CUDA 优化与日志分析无需启动 Vivado。未来使用 Vivado 时默认 2022.2：`/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado`；先查现有 MCP 会话并核实技能版本要求。

## 本次保存内容

[交接快照目录](results/handoff_20261029/) 保存当前 VPR tracked diff、4 个新增原生文件、`native/`、`scripts/`、`tests/` 的副本及 SHA256 清单，共 57 个快照文件。不包含巨大输入和重复二进制副本；它们由现有冻结路径及哈希指向。现有工作区改动仍留在原位，没有提交、回滚或清理。

新对话可使用以下开场指令：

> 请读取当前工程根目录 HANDOFF.md，接续原生 CPU–GPU 异构布线优化。先实现接管过程分项计时和真实接管状态捕获，并诊断单查询批次的形成原因；先用 elliptic/GEMM 验证，再决定优化和接管策略。保留原 VPR 基线、质量约束及全部失败记录，不要混用独立 target 后端的加速结果。
