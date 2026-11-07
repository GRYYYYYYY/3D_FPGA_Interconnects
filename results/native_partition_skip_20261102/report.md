# 跳过同分区无效重插入：候选未通过质量门槛

候选已实现并验证，结论是不采用。保留动态BB通知、全量重载通知和必要跨分区迁移，仅在old==new时跳过erase/insert与重复映射赋值。开关默认关闭，历史源/库/二进制不变。

|布局|控制CPD ns|候选CPD ns|CPD变化|线长变化|轮数 控制→候选|质量门槛|
|---|---:|---:|---:|---:|---|---|
|s38417_s1|6.96051|8.61087|+23.71%|+2.70%|68→65|未通过|
|s38417_s2|7.7556|8.28151|+6.78%|-1.61%|47→54|未通过|

两布局候选均超过预声明CPD最多恶化5%的门槛。门槛实验每臂一次，未进行性能重复，因此不报告速度比。s1轮数减少不代表优化成功；s2轮数反而增加。

## 正确性与归因

6项未诊断门槛（两布局×reference/control/candidate）：新同ELF控制与既有修复版路由主体、CPD、线长、轮数相同。4项正确启用诊断的补充运行与对应plain端点也一致。所有14次原生运行均合法，map逐字节等价、原生及独立FULL/STA通过；合法不能替代质量门槛。

|布局|诊断臂|检查轮数|网络边界检查数|越界数|首五轮跳过重插入数|
|---|---|---:|---:|---:|---:|
|s38417_s1|tracectrl|68|302260|0|0|
|s38417_s1|traceskip|65|288925|0|851|
|s38417_s2|tracectrl|47|208915|0|0|
|s38417_s2|traceskip|54|240030|0|785|

保持分区归属正确，并不意味着启发式路由顺序和质量不变。这个候选移除了同分区重插入所带来的容器顺序变化，实际改变了后续路径选择；不能将其视为严格语义不变的性能优化。没有撤销任何正确性修复。

## 保留的执行问题

最初4个diag_control/diag_candidate臂因旧包装器按后缀选变体，与control/candidate冲突，实际未开启trace。原记录及env保留，不用于边界诊断结论。改为不冲突的tracectrl/traceskip后仅补4项；已有plain门槛不重跑。监督器因此留下stopped_for_review原回执；final_status.json记录复核后的拒绝终态。原冻结runner未修改。

elliptic预定案例路径在提交前发现不存在，按既有数据修正，原计划与planning_correction.json保留；由于s38417质量失败，elliptic guard及72项正式性能矩阵均未启动。这是按门槛停止推广，不是性能工作遗漏。

## 结论与后续

拒绝本候选，保留既有CPU lookahead主线和两处状态修复。若继续研究确定性同扇出排序，应作为独立的QoR敏感算法变更重新设门槛；不能以本次跳过重插入结果宣称加速。优先扩展已有lookahead主线的大图独立验证。

复现：build_native_partition_skip.py、run_native_partition_skip.py、finalize_native_partition_skip.py；修改仅candidate.patch，来源build_provenance.json，原生审计evidence_verification.json，详细env/失败门槛/trace绑定analysis.json。本报告不改变此前CPU主线测量结论。
