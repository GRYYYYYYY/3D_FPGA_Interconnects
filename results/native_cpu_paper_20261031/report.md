# CPU 主线实验报告

全部计划已终态并完成证据审计：290项正式/预检测量中284项成功，另有4项按原版失败门槛跳过；校验503个冻结文件。数值失败保留，不进入加速比。

结论应定位为 **CPU lookahead 预计算优化**。计时包含加载固定打包/布局结果的成本，但不重新执行打包与布局算法，不能称为完整 FPGA 编译加速；共同缓存后也不能宣称路由搜索被加速。本轮未使用新 GPU 作业，所有新优化开关保持默认关闭。

## 修复版与组内采样并行的六电路对照

| 电路 | 重建 map 配对速度比中位数 | 共同缓存配对速度比中位数 | 重建合格配对数 |
| --- | ---: | ---: | ---: |
| ex5p | 1.363× | 1.000× | 3 |
| softmax | 1.389× | 0.994× | 3 |
| clstm_large | 1.402× | 0.970× | 3 |
| reduction | 1.491× | 1.002× | 3 |
| gemm | 1.494× | 1.009× | 3 |
| elliptic | 1.029× | 0.993× | 3 |

六电路重建模式的几何平均配对速度比为 **1.351×**，共同缓存为 **0.995×**。均为相同核组、相同四核预算下的比较，主要控制已经包含必要的正确性修复。逐次范围见 `analysis.json`；不能把几何平均当作所有电路均明显加速。

原版 elliptic 并行在重建/复用模式都发生 SIGSEGV，后续对应重复停止，因此没有合法原版并行速度比。clstm_large 的修复版 parallel 虽合法，但 CPD 从原版6.58269ns变为7.71292ns（+17.17%），超过5%门槛；这组不能宣称质量合格地击败原版。

| 电路 | 相对原版 parallel 的合格配对 | 进程速度比中位数 |
| --- | ---: | ---: |
| clstm_large | 0/3 | — |
| elliptic | 0/1 | — |
| ex5p | 3/3 | 1.408× |
| gemm | 3/3 | 1.503× |
| reduction | 3/3 | 1.509× |
| softmax | 3/3 | 1.376× |

无合格配对的行不计算速度比；CLSTM恢复质量后的公平对照在下文单列。

## 核数与分项成本

| 电路 | 物理核 | 修复版进程中位秒 | 组内并行进程中位秒 | 同核配对速度比 | 合格配对 |
| --- | ---: | ---: | ---: | ---: | ---: |
| gemm | 1 | 397.468 | 400.530 | 0.982× | 3 |
| gemm | 2 | 368.547 | 287.775 | 1.269× | 3 |
| gemm | 4 | 361.185 | 240.488 | 1.494× | 3 |
| gemm | 8 | 344.306 | 230.102 | 1.496× | 3 |
| elliptic | 1 | 153.999 | 153.498 | 1.006× | 3 |
| elliptic | 2 | 145.418 | 145.538 | 0.999× | 3 |
| elliptic | 4 | 144.697 | 140.692 | 1.029× | 3 |
| elliptic | 8 | 142.792 | 140.909 | 1.026× | 3 |

速度比先逐重复配对再取中位数，不必等于两列中位时间之比。这些是相同核数下的算法消融；不同核数可能改变路由调度、迭代数和质量，不能将其时间差全部解释为lookahead并行效率。完整CPD、线长、迭代数、Routing和峰值内存见分析文件。

| GEMM四核重建配置 | lookahead中位秒 | Routing中位秒 | 进程中位秒 | VPR峰值RSS中位MiB |
| --- | ---: | ---: | ---: | ---: |
| fixed | 162.140 | 37.190 | 361.185 | 16012.6 |
| optimized | 42.600 | 37.060 | 240.488 | 16013.0 |
| original | 163.460 | 36.520 | 360.905 | 16013.1 |

## 统一采样 pipeline 的增量结果

统一队列跨层/线段组调度采样，保持严格归并与插值顺序；最多2P个在途结果，每线程独立工作区。所有计时变体对称写出 map，并逐字节对照原版串行结果。这里的基线是已有组内采样并行，不能直接与另一研究的原版时间相除。

| 电路 | 核数 | 合格配对 | VPR进程速度比中位数 [最小,最大] | lookahead阶段速度比中位数 |
| --- | ---: | ---: | ---: | ---: |
| clstm_large | 4 | 3 | 1.070 [0.900,1.080] | 1.130 |
| elliptic | 4 | 3 | 1.014 [1.013,1.024] | 1.775 |
| ex5p | 4 | 3 | 1.222 [1.122,1.226] | 1.653 |
| gemm | 4 | 3 | 0.937 [0.932,0.942] | 0.914 |
| gemm | 8 | 3 | 1.010 [0.998,1.015] | 1.924 |
| reduction | 4 | 3 | 0.981 [0.936,0.994] | 1.067 |
| softmax | 4 | 3 | 1.015 [0.845,1.074] | 1.365 |

速度比小于1表示新队列更慢。六电路四核增量速度比的几何平均为1.036×。四核 GEMM 观察到退步，保留负结果；785个被审计源码中只有预期三个文件改变、关键编译选项一致。已检查的首批退步样本没有cgroup限流，额外耗时主要落在未覆盖的VPR工作，不能写成已经证明的分配器问题。1/2核只有探索性单次结果，见 `tasks_analysis.json`。

另外保留一组四核GEMM探索性归因三元组：旧实现、重构后仍用组内并行、重构后启用pipeline。后两者二进制SHA完全相同，通过开关分离调度效果；具体结果见 `tasks_attribution_analysis.json`。单次归因不作为统计确认，也不替代旧实现这个实际端到端基线。

| GEMM四核归因比较（各一次） | 进程速度比 | lookahead速度比 |
| --- | ---: | ---: |
| optimized:refactored | 0.946× | 1.009× |
| optimized:tasks | 0.955× | 1.018× |
| refactored:tasks | 1.010× | 1.008× |

归因三元组中，重构后保留旧调度已经慢于旧实现；同一二进制开启pipeline只带来很小变化。因此不能把整个候选版本的退步全部归因于全局队列。此结论只是单次定位线索，尚未确定具体函数或分配器原因。

完整构建核对：523条编译/链接命令在替换源码与构建路径后完全一致；1421个实际项目源码/生成依赖均配对，除预期三个源码文件外，生成文件差异只涉及路径、由路径生成的头文件保护名与构建时间。见 `build_command_comparison.json`、`compiled_input_comparison.json` 和 `generated_input_comparison.json`。

VPR自己报告的整个flow时间与外部进程计时也作交叉核对；未覆盖成本是外部进程时间减去互不嵌套的顶层定时器之和。

| GEMM配置 | 核数 | 未覆盖成本中位秒 | 外部计时减VPR整个flow中位秒 |
| --- | ---: | ---: | ---: |
| optimized | 4 | 42.283 | 0.503 |
| tasks | 4 | 54.377 | 0.528 |
| optimized | 8 | 40.610 | 0.520 |
| tasks | 8 | 54.593 | 0.573 |

## clstm_large 的合法质量对照

现有 upstream `parallel_decomp` 可恢复质量，因此单独做了原版 parallel、原版 decomp、修复版decomp和两种CPU优化decomp的三次确认。decomp本身不是我们的创新；采样优化的收益必须继续对比原版/修复版decomp。

| 比较 | 缓存 | 合格配对 | 进程速度比中位数 | CPD变化中位数 |
| --- | --- | ---: | ---: | ---: |
| fixed:optimized | rebuild | 3 | 1.401× | 0.000% |
| fixed:tasks | rebuild | 3 | 1.406× | 0.000% |
| original_decomp:optimized | rebuild | 3 | 1.320× | -1.685% |
| original_decomp:tasks | rebuild | 3 | 1.269× | -1.685% |
| fixed:tasks | reuse | 3 | 0.987× | 0.000% |

此处fixed/optimized/tasks都使用decomp，分别表示仅修复、组内采样、统一pipeline。不能将按结果挑选每个电路最佳模式包装成已验证的自动选择策略。

## 架构与强基线

原生架构扩展共44项、42项成功。单层Hecate与双层Hecate的80/100/120通道宽度分别成对比较；elliptic宽度80两侧均在600秒上限内未收敛。宽度100图除XML首行元数据外与原图相同，是重现控制，不是新增独立架构。宽度120更易收敛，不能跨宽度把资源增加的效果当成算法加速。

锁定VPR的compressed_map明确不支持3D，SIGABRT预检已保存；只在2D做合法比较。parallel_decomp采用相同输入和核心预算。MultiQueue探索仅4项，3项成功，elliptic在200轮后剩1个超用节点；不计算失败样本速度比，也不据此宣布胜过整个MultiQueue算法族或已完成所有最优参数比较。

| 输入 | 更强控制→组内采样并行 | 合格配对 | 进程速度比中位数 | CPD变化中位数 |
| --- | --- | ---: | ---: | ---: |
| clstm_large | fixed_decomp:optimized | 0/1 | — | 20.000% |
| elliptic | fixed_decomp:optimized | 1/1 | 1.017× | -2.470% |
| ex5p | fixed_decomp:optimized | 1/1 | 1.393× | -1.750% |
| gemm | fixed_decomp:optimized | 1/1 | 1.423× | -4.033% |
| reduction | fixed_decomp:optimized | 1/1 | 1.440× | -6.215% |
| softmax | fixed_decomp:optimized | 1/1 | 1.372× | 0.000% |
| elliptic_native_l1_w100 | fixed_compressed:optimized | 3/3 | 1.005× | 0.000% |
| elliptic_native_l1_w100 | fixed_decomp:optimized | 0/1 | — | 6.813% |
| ex5p_native_l1_w100 | fixed_compressed:optimized | 3/3 | 1.062× | 0.000% |
| ex5p_native_l1_w100 | fixed_decomp:optimized | 1/1 | 0.979× | -9.957% |

这些比较允许既有算法改变路径；仍执行5%质量门槛。decomp主扩展只有一次探索配对，二维compressed_map有三次；不能与CLSTM独立三次确认混为一组。

## 计时、可复现性与边界

对照锁定VTR提交 `0b912334fdd83bb754b302146ac0d1ec9edc9a0e`，使用GCC11.4、Release/O3、TBB、关闭IPO。原版已有parallel/decomp能力；本轮同核比较不把启用线程算作新贡献，也不声称覆盖未测试的更新版本。

硬件为双路Intel Xeon Gold6530，64物理核/128逻辑CPU；本会话cgroup配额54核、内存上限300GiB。每次测量使用同一核组中的1/2/4/8个不同物理核，审计所有VPR线程。不同研究使用空闲CPU集合并可并发，宿主和内存系统共享，没有资源独占。三次重复是固定seed的运行重复，不是三个布局种子。

主要指标包括读取固定网表/布局/RRG、lookahead、Routing和原生FULL/STA；独立原版回读另外报告workflow。输入同样预读，rebuild只表示重建lookahead，不表示磁盘冷缓存。计时汇总保留顶层定时器，不把Create Device与其内层RRG读取重复相加；未覆盖的墙钟时间明确标为unscoped，不擅自归因。峰值内存优先使用VPR报告的进程高水位，五秒/proc采样仅作补充。

只有完整收敛、零超用、两次FULL/STA一致、路由回读前后SHA不变、CPU亲和性通过，并且CPD/线长退化各不超过5%的配对才能进入合格性能汇总。所有新pipeline map都要求与原版串行逐字节一致。

首次缓存预检误将VPR未收敛返回码2当作异常，已修正并保留失败记录。首次架构输入准备误做完整路由，已仅中止本任务的准备进程并保留日志；第二次用一轮路由生成输入，不作为性能样本。它们不覆盖正式实验结果。

论文方向可以转为CPU主线，但当前证据仍限于六个原有电路、Hecate单/双层及少量宽度变化；需要更广基准、多布局种子、独立确认以及充分的相关工作对照。新实现是具体可评审的调度实验，不据此保证论文新颖性或录用。GPU保留为后续扩展，不强行作为主贡献。

## 本轮策略决定

后续CPU主线保留现有组内采样并行实现：新资源图需要重建lookahead时衡量其收益，可复用时双方读取同一有效缓存。全局pipeline保持实验选项，四核GEMM退步，八核局部阶段加速尚未变为稳定的完整进程收益，不替换现有实现或自动按电路挑选。

下一项优化应先定位重构版本中增加的未覆盖成本，再决定保留哪些结构变化。CPU论文需要同时扩大独立电路/架构和布局种子验证，并突出预计算方法；当前没有新增GPU优化或GPU默认接管。

## 文件入口

- `conclusions.json`：核心数字与比较结果。
- `analysis.json`、`tasks_analysis.json`、`tasks_extension_analysis.json`：六电路/核数与新队列的完整逐次比较。
- `clstm_quality_analysis.json`、`architecture_analysis.json`、`multiqueue_analysis.json`：质量、架构、强基线。
- `tasks_attribution_analysis.json`：同二进制的重构/调度归因探索。
- `evidence_verification.json`：终态日志、路由、map、输入、二进制及脚本来源审计。
- `implementation_verification.json`、`acceptance.json`：构建依赖核对及最终验收。
- `cpu_changes.patch`、`tasks_changes.patch`、`source_provenance.json`、`tasks_provenance.json`、`tasks_source_audit.json`：源码和构建。
- `figures/cpu_study.pdf`、`figures/cpu_study.svg`、`figures/cpu_study.png`：可分享图表；误差线为实测范围，不是置信区间。
- `docs/native_cpu_paper_study.md`、`docs/native_cpu_sample_pipeline.md`：工程根目录下的方法说明。
