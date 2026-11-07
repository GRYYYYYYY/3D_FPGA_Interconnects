# 缓存诊断的独立复核结果

以本复核和verified_summary.json为准；原summary.json、measurement.json与自动report.md保留。
八项诊断中已验证合法 6 项；输出审计状态 passed。

冻结执行器在measurement.json写出前调用了依赖该文件的log_evidence，导致成功路由的末轮零过用被记为null、success误记false。此处依据已保存原生日志、独立FULL/STA、路由hash和CPU审计重算；未重跑求解、修改路由或放宽合法性条件。

|任务|退出码|复核合法|完成轮数/最后观察轮数|CPD ns|线长|末轮过用|
|---|---:|---|---:|---:|---:|---:|
|bnn_s1_parallel_cached|2|False|200|10.8646|1557232|1|
|bnn_s1_serial_cached|2|False|200|10.8646|1559304|1|
|bnn_s2_cached_tasks0_r0|0|True|75|11.4776|1668374|0|
|bnn_s2_cached_tasks1_r0|0|True|121|11.4776|1668046|0|
|bnn_s2_cached_tasks1_r1|0|True|121|11.4776|1668046|0|
|bnn_s2_cached_tasks0_r1|0|True|75|11.4776|1668374|0|
|bnn_s2_cached_tasks0_r2|0|True|121|11.4776|1668046|0|
|bnn_s2_cached_tasks1_r2|0|True|121|11.4776|1668046|0|

BNN_s2各TASKS模式下合法路由主体种类数：{'0': 2, '1': 1}。
本轮仅检查轨迹重复性，不报告性能速度比。缓存跳过wire map构建，仍有src/opin预处理；观察到变化不直接证明路由竞态，未观察到变化也不证明确定性。
BNN_s1串行和并行是否布通，应分别依据上表合法性；不得把未收敛样本视为加速证据。原30项资格拒绝与144项正式未启动保持。

主模型复核：TASKS0三重复为75/75/121轮，TASKS1为121/121/121轮；TASKS0第三次路由主体与旧reference完全相同。确认同配置重复可返回两类合法端点，不证明具体竞态。下一步使用单独的线宽120基线可布通性协议，全部六布局统一探测，原线宽100资格失败保持。详见conclusions.json。
