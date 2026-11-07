# 八核 pipeline 顺序确认

36项全部合法及map等价，独立FULL/STA通过。预设选型门槛：通过。

相对既有优化CPU的三次配对完整进程速度比；大于1表示更快。

|电路|缓存|中位数|范围|门槛|
|---|---|---:|---|---|
|gemm|rebuild|1.094192|1.081642–1.097591|True|
|gemm|reuse|1.014944|1.000553–1.018511|True|
|softmax|rebuild|1.128641|1.088191–1.147396|True|
|softmax|reuse|1.000166|0.965004–1.029394|True|
|reduction|rebuild|1.092956|1.082867–1.098851|True|
|reduction|reuse|1.000007|0.990678–1.002779|True|

Single serial lane, eight distinct physical CPUs 32-39 on one NUMA node; eliminates own experiment concurrency, host not exclusive.

Fixed placement runtime repeats, shared host, extensions are prior project circuits held out from previous eight-core selection; no new independent benchmark claim.

所有实验串行使用同一八核集合，排除本轮自身并发；不声称宿主独占。默认策略未变。完整记录见 analysis.json 与 evidence_verification.json。

GEMM重建三次均加速，两个扩展电路的三次重建也均加速；共同缓存条件整体接近持平，支持收益主要来自预计算构建。缓存中的小幅变化不归因于跳过的构建计算。

GEMM部分配对路由主体不同，质量门槛仍通过；完整进程速度比包含并行布线波动，不是严格相同搜索工作量的单核算子对比。

本轮通过工程门槛，支持八核pipeline候选；不外推至四核、更多布局或独占硬件，也不证明论文新颖性。此前bounded未通过选型的结论保持。

|电路|实现|重建lookahead中位秒|
|---|---|---:|
|gemm|frozen|39.490|
|gemm|pipeline|23.340|
|softmax|frozen|2.490|
|softmax|pipeline|1.090|
|reduction|frozen|12.820|
|reduction|pipeline|6.940|
