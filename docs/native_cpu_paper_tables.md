# 原生CPU lookahead论文主表

以下主表由独立复核产物生成。完整进程、构建阶段、内存诊断和缓存批次分别报告；不同宿主、架构、样本权重不混成一个总加速比。

|样本集合|核数|缓存模式|对照|完整布线进程速度比|
|---|---:|---|---|---:|
|3D width120 conditional subset|8|rebuild|stock_to_pipeline|1.6999×|
|Native k6 tseng/des|8|rebuild|stock_to_pipeline|1.1369×|
|3D width120 conditional subset|8|rebuild|per_group_to_pipeline|1.0991×|
|Native k6 tseng/des|8|rebuild|per_group_to_pipeline|1.0402×|
|3D width120 conditional subset|8|reuse|stock_to_pipeline|1.0145×|
|Native k6 tseng/des|8|reuse|stock_to_pipeline|0.9789×|
|3D width120 conditional subset|8|reuse|per_group_to_pipeline|0.9977×|
|Native k6 tseng/des|8|reuse|per_group_to_pipeline|0.9727×|
|clma native k6|8|rebuild|stock_to_pipeline|1.0944×|
|clma native k6|8|rebuild|stock_to_flat|1.1204×|
|clma native k6|8|rebuild|per_group_to_pipeline|1.0202×|
|clma native k6|8|rebuild|per_group_to_flat|1.0703×|
|clma native k6|8|rebuild|flat_to_pipeline|0.9932×|
|BNN original KOIOS2D|8|rebuild|stock_to_pipeline|1.3719×|
|BNN original KOIOS2D|8|rebuild|stock_to_flat|1.3181×|
|BNN original KOIOS2D|8|rebuild|per_group_to_pipeline|1.0576×|
|BNN original KOIOS2D|8|rebuild|per_group_to_flat|1.0301×|
|BNN original KOIOS2D|8|rebuild|flat_to_pipeline|1.0267×|

三维条件子集有2电路/3布局/2份不同RR图，BNN布局占2/3权重；原6布局3成功3失败保持。k6 tseng/des为2电路/4布局/2份不同RR图。新增各二维集合只含1个电路/1个布局，不能冒充多电路泛化。
这里的原版stock也获得相同CPU预算，并采用原生parallel布线；stock对照包含状态修复差异。同修复ELF的组内/flat/pipeline对照更直接解释构建增量。读冻结RR/packed/place的进程不等于包含综合/pack/place的完整编译。

|已复核扩展性（另一共享宿主）|同方法1→16核|同16核组内→pipeline|
|---|---:|---:|
|bnn|11.9321×|3.1263×|
|dla_like.medium|12.1671×|3.1236×|

这一表仅是lookahead阶段；96项一轮路由均未布通。DLA四核组内→pipeline仍为0.9526×，保留负例。

|新增研究|状态|
|---|---|
|native_flat_baseline_20261105|reviewed；独立复核=True|
|native_large2d_followup_20261105|reviewed；独立复核=True|

|native_flat_baseline_20261105：阶段对照|配对速度比中位|范围|
|---|---:|---:|
|bnn/8/per_group_to_flat|1.8423×|1.8259–1.9388|
|bnn/8/flat_to_pipeline|0.9894×|0.9892–1.0075|
|bnn/16/per_group_to_flat|3.2184×|3.1588–3.2564|
|bnn/16/flat_to_pipeline|1.0186×|1.0109–1.0338|
|clma_2d/8/per_group_to_flat|1.4091×|0.9394–2.2000|
|clma_2d/8/flat_to_pipeline|1.0476×|0.9524–1.5000|
|clma_2d/16/per_group_to_flat|1.4762×|1.4545–1.4762|
|clma_2d/16/flat_to_pipeline|1.0000×|1.0000–1.0476|
|dla_like.medium/8/per_group_to_flat|1.8046×|1.7139–1.8281|
|dla_like.medium/8/flat_to_pipeline|1.0204×|1.0042–1.0637|
|dla_like.medium/16/per_group_to_flat|3.1230×|3.0457–3.1897|
|dla_like.medium/16/flat_to_pipeline|1.0018×|1.0000–1.0120|

该研究的阶段RSS、标签容量和中间表结构计数见对应review.md；诊断样本不进入本表速度比。

|native_large2d_followup_20261105：阶段对照|配对速度比中位|范围|
|---|---:|---:|
|bnn_2d/8/per_group_to_flat|1.8835×|1.7117–1.9117|
|bnn_2d/8/flat_to_pipeline|1.0170×|1.0098–1.0234|

该研究的阶段RSS、标签容量和中间表结构计数见对应review.md；诊断样本不进入本表速度比。

|真实缓存序列|K=1 stock→pipeline|K=5 stock→pipeline|
|---|---:|---:|
|tseng_s1|1.1235×|0.9919×|
|des_s1|1.1266×|1.0611×|

K=1/2/5是同一实际长度5序列的相关前缀；同固定设计重复请求，不是5个独立设计。大图缓存摊销的历史情景计算不当成实测批次。

剩余边界：物理CPU独占尚未证明；RSS采样不是精确峰值，工作区标签计数不含队列/分配器；wire map字节一致不扩大为所有派生表或最终路由确定性。方法新颖性不能由更多重复测量单独建立。

方法：[等价构建论证](native_lookahead_method_argument.md)。复现：[命令与证据入口](native_cpu_paper_reproduction.md)。逐表来源和SHA256见native_cpu_paper_tables.json。
