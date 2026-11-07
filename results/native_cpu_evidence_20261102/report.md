# CPU 三方基线、泛化与核数扩展

完成 66/66 个正式样本，合法 66 项；三方主门槛通过。

stock为锁定原版VPR的原生并行路由，frozen为已有组内采样CPU，pipeline为已有跨组调度。每一比较CPU预算相同。速度比=控制时间/候选时间；运行时间中位数之比不等于配对速度比中位数。

## GEMM 同八核三方对照

|缓存|控制→候选|配对进程速度比中位 [范围]|合法质量配对|
|---|---|---:|---:|
|rebuild|stock→frozen|1.5091 [1.5064, 1.5160]|3/3|
|rebuild|stock→pipeline|1.6379 [1.6333, 1.6437]|3/3|
|rebuild|frozen→pipeline|1.0843 [1.0842, 1.0854]|3/3|
|reuse|stock→frozen|0.9916 [0.9524, 1.0093]|3/3|
|reuse|stock→pipeline|0.9981 [0.9923, 1.0099]|3/3|
|reuse|frozen→pipeline|1.0007 [1.0006, 1.0479]|3/3|

各阶段墙钟与完整进程中位数（秒）：

|缓存|实现|RR图载入|lookahead构建|布线|完整进程|含独立复核的workflow|
|---|---|---:|---:|---:|---:|---:|
|rebuild|stock|49.96|148.83|30.57|330.31|502.14|
|rebuild|frozen|48.61|37.90|31.93|219.20|391.22|
|rebuild|pipeline|49.44|20.82|31.68|202.17|375.78|
|reuse|stock|49.13|—|30.65|180.89|352.62|
|reuse|frozen|48.96|—|31.05|181.91|354.28|
|reuse|pipeline|49.20|—|31.40|181.35|352.94|

阶段计时仅覆盖日志已有的阶段；不能相加冒充完整进程。完整进程包含原生FULL/STA与map写出，workflow另外包含独立原版FULL/STA复核；均不含本轮新电路的pack/place准备。缓存场景跳过lookahead构建。只在合法样本内计算本表中位数；失败保留在完整数据中。

## 新电路与新布局

alu4、diffeq、s38417按输入逻辑规模与时序结构预选，种子1/2均重新打包布局，实际坐标已核验不同。每个布局每个变体/缓存只有一次运行，不把它们包装为三次运行重复，也不把两个布局计成两种电路。

|电路布局|缓存|控制→候选|进程速度比|质量合格|
|---|---|---|---:|---|
|alu4_s1|rebuild|stock→frozen|0.9233 [0.9233, 0.9233]|True|
|alu4_s1|rebuild|stock→pipeline|1.0429 [1.0429, 1.0429]|True|
|alu4_s1|rebuild|frozen→pipeline|1.1295 [1.1295, 1.1295]|True|
|alu4_s1|reuse|stock→frozen|1.0474 [1.0474, 1.0474]|True|
|alu4_s1|reuse|stock→pipeline|1.0005 [1.0005, 1.0005]|True|
|alu4_s1|reuse|frozen→pipeline|0.9552 [0.9552, 0.9552]|True|
|alu4_s2|rebuild|stock→frozen|0.9267 [0.9267, 0.9267]|True|
|alu4_s2|rebuild|stock→pipeline|1.0856 [1.0856, 1.0856]|True|
|alu4_s2|rebuild|frozen→pipeline|1.1714 [1.1714, 1.1714]|True|
|alu4_s2|reuse|stock→frozen|1.0450 [1.0450, 1.0450]|True|
|alu4_s2|reuse|stock→pipeline|1.0448 [1.0448, 1.0448]|True|
|alu4_s2|reuse|frozen→pipeline|0.9998 [0.9998, 0.9998]|True|
|diffeq_s1|rebuild|stock→frozen|0.9264 [0.9264, 0.9264]|True|
|diffeq_s1|rebuild|stock→pipeline|1.0856 [1.0856, 1.0856]|True|
|diffeq_s1|rebuild|frozen→pipeline|1.1718 [1.1718, 1.1718]|True|
|diffeq_s1|reuse|stock→frozen|0.9587 [0.9587, 0.9587]|True|
|diffeq_s1|reuse|stock→pipeline|1.0442 [1.0442, 1.0442]|True|
|diffeq_s1|reuse|frozen→pipeline|1.0891 [1.0891, 1.0891]|True|
|diffeq_s2|rebuild|stock→frozen|0.9637 [0.9637, 0.9637]|True|
|diffeq_s2|rebuild|stock→pipeline|1.0827 [1.0827, 1.0827]|True|
|diffeq_s2|rebuild|frozen→pipeline|1.1235 [1.1235, 1.1235]|True|
|diffeq_s2|reuse|stock→frozen|1.0004 [1.0004, 1.0004]|True|
|diffeq_s2|reuse|stock→pipeline|1.1413 [1.1413, 1.1413]|True|
|diffeq_s2|reuse|frozen→pipeline|1.1408 [1.1408, 1.1408]|True|
|s38417_s1|rebuild|stock→frozen|0.9790 [0.9790, 0.9790]|True|
|s38417_s1|rebuild|stock→pipeline|1.0572 [1.0572, 1.0572]|True|
|s38417_s1|rebuild|frozen→pipeline|1.0799 [1.0799, 1.0799]|True|
|s38417_s1|reuse|stock→frozen|0.8730 [0.8730, 0.8730]|True|
|s38417_s1|reuse|stock→pipeline|0.8533 [0.8533, 0.8533]|True|
|s38417_s1|reuse|frozen→pipeline|0.9774 [0.9774, 0.9774]|True|
|s38417_s2|rebuild|stock→frozen|1.0705 [1.0705, 1.0705]|True|
|s38417_s2|rebuild|stock→pipeline|1.1303 [1.1303, 1.1303]|True|
|s38417_s2|rebuild|frozen→pipeline|1.0558 [1.0558, 1.0558]|True|
|s38417_s2|reuse|stock→frozen|1.0382 [1.0382, 1.0382]|True|
|s38417_s2|reuse|stock→pipeline|1.0187 [1.0187, 1.0187]|True|
|s38417_s2|reuse|frozen→pipeline|0.9812 [0.9812, 0.9812]|True|

按每个电路内两布局、再三个电路等权几何平均；有任一质量不合格配对时不报告完整集合平均。

|缓存|控制→候选|三电路等权几何平均|
|---|---|---:|
|rebuild|stock→frozen|0.9636|
|rebuild|stock→pipeline|1.0804|
|rebuild|frozen→pipeline|1.1211|
|reuse|stock→frozen|0.9918|
|reuse|stock→pipeline|1.0134|
|reuse|frozen→pipeline|1.0218|

各布局完整进程的绝对时间（秒；每项一次）：

|电路布局|缓存|stock|frozen|pipeline|
|---|---|---:|---:|---:|
|alu4_s1|rebuild|1.22|1.32|1.17|
|alu4_s1|reuse|1.12|1.07|1.12|
|alu4_s2|rebuild|1.27|1.37|1.17|
|alu4_s2|reuse|1.17|1.12|1.12|
|diffeq_s1|rebuild|1.27|1.37|1.17|
|diffeq_s1|reuse|1.17|1.22|1.12|
|diffeq_s2|rebuild|1.32|1.37|1.22|
|diffeq_s2|reuse|1.22|1.22|1.07|
|s38417_s1|rebuild|9.28|9.47|8.77|
|s38417_s1|reuse|7.57|8.67|8.87|
|s38417_s2|rebuild|9.12|8.52|8.07|
|s38417_s2|reuse|8.17|7.87|8.02|

小电路只有秒级运行时间。冻结执行器使用Python的带超时wait，当前POSIX实现的退出轮询sleep最大为50毫秒，实测进程时间包含退出检测等待及监督开销；共享调度还可增加波动。这不是严格误差上界。未事后扣除这些开销，也未改用另一个指标挑选结果；单次的小幅百分比差异不能视为稳定加速。

## 核数与资源

|物理核|pipeline相对frozen重建速度比|配对数|
|---:|---:|---:|
|4|1.0101 [1.0070, 1.0168]|3/3|
|8|1.0843 [1.0842, 1.0854]|3/3|
|16|1.1377 [1.1375, 1.1381]|3/3|

绝对时间中位数（秒）：

|物理核|frozen构建|pipeline构建|frozen进程|pipeline进程|
|---:|---:|---:|---:|---:|
|4|39.05|37.88|224.40|222.15|
|8|37.90|20.82|219.20|202.17|
|16|38.04|12.76|216.47|190.20|

八核来自本轮三方阶段，四/十六核来自后续扩展；每个核数内配对公平，跨核数时间仍可能受时段变化影响。RSS为每五秒观察的进程HWM，可能被RR XML载入支配，不代表临时map内存；各项原值见analysis.json。

## 贡献与限制

当前主线是原生lookahead预计算的采样并行与跨组调度，保留map字节等价和原生路由/STA接口。已有文献中的采样map、确定性并行与pipeline原语不作首次贡献。新bounded仍为上一轮未建立稳定增量的候选。

stock与两种改进CPU之间还包含此前的并行状态修复，原生路由轨迹可能不同；不能将完整进程差值全部归于单个lookahead调度算子，也不将路由质量变化归因于map优化。frozen与pipeline对照和共同缓存用于补充归因。

本轮未启用GPU，未改变默认调度。节点无独占调度入口；所有本轮准备和求解顺序执行，但宿主、存储和内存共享。只有三种新电路、每种两个布局，不能外推为全面超过SOTA或论文新颖性已成立。存在失败或质量超门槛的配对时保留记录并排除其速度比。

泛化初始执行在24项正式测量后，s38417_s1的单轮缓存资格准备触发overuse_report.cpp:366断言，map已成功写出。原失败目录和回执保留。复核后，仅剩余两布局的缓存准备关闭拥塞报告输出，正式测量的该参数仍为on，二进制、调度和输入不变；保留24项，补完未执行的12项，没有重跑正式样本。原失败map与重做资格的原版/优化map字节相同。generalization_complete为可追溯的合并证据视图，原generalization状态仍为failed。

完整证据：analysis.json、acceptance.json、evidence_verification.json、generalization_join.json、protocol.json、原始及补充*_plan.json、preparation.json与measurement_resolution.json。前序查新见../../docs/native_lookahead_novelty_analysis.md。

缓存场景最差的原版→pipeline泛化配对为s38417_s1：速度比0.8533，候选时间变化+17.20%。该单项不能被集合平均掩盖；本轮没有据此启用普遍默认策略。
