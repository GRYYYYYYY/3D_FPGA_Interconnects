# 宽120条件子集四臂完整布线实验

固定此前声明的LSTM_s2、BNN_s1、BNN_s2，原六布局3合法/3失败保持；不是六布局全部成功。原版与三个修复版配置均原生parallel路由、八物理核，后三者同ELF。共享宿主。
12项rebuild资格通过后才运行72项独立正式样本：四臂、重建/缓存、各三次。资格和既有样本不并入。全体使用已有RR图和固定布局，进程计时包含统一map写出；不与旧生成RR的进程相除。

状态：completed；正式执行72/72，合法72。
完整审计队列：True；修复版质量门槛：True。

|缓存模式|对照→候选|完整进程配对中位几何平均|含独立检查的workflow|
|---|---|---:|---:|
|rebuild|stock_to_fixed_serial|1.001660×|1.001053×|
|rebuild|stock_to_per_group|1.546435×|1.315686×|
|rebuild|stock_to_pipeline|1.699916×|1.391364×|
|rebuild|fixed_serial_to_per_group|1.540629×|1.316095×|
|rebuild|fixed_serial_to_pipeline|1.688641×|1.384749×|
|rebuild|per_group_to_pipeline|1.099108×|1.052477×|
|reuse|stock_to_fixed_serial|1.013684×|1.006648×|
|reuse|stock_to_per_group|1.018108×|1.010623×|
|reuse|stock_to_pipeline|1.014490×|1.004782×|
|reuse|fixed_serial_to_per_group|1.002467×|1.001556×|
|reuse|fixed_serial_to_pipeline|0.996093×|0.996338×|
|reuse|per_group_to_pipeline|0.997694×|0.997555×|

全部单次配对、范围、CPD/WL质量差异及内部flow/routing敏感性见analysis.json。Stock对照含正确性修复/轨迹差异，不能全归因于lookahead；同ELF组内→pipeline用于增量归因。
缓存仍重算src/opin，缓存差异不自动等于纯路由差异。缺少stock相对比值表示该质量门槛不通过，不得丢掉坏配对再汇总。

默认不改，无GPU收益主张。原宽100严格端点失败和144项未启动保持。本协议以合法性/5%质量评价新条件子集，并显式记录route-body变化，不回填旧门槛。

独立终态报告及全部重复点图表见[review.md](review.md)；588份产物、全部使用输入和配对统计复核通过，见independent_review.json。结论与主张边界见conclusions.json、evidence_summary.json；本链已终止，无活动求解。
