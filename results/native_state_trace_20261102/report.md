# 逐轮 BB 通知、分区归属与执行顺序诊断

24项诊断运行全部合法，map字节等价、原生及独立FULL/STA通过。八份逐轮日志通过事件序号、首五轮覆盖、任务开始/结束配对、实际env/执行顺序/八核亲和性核验。全部运行仅作诊断，不报告性能加速。

## 最早分歧

两布局、两次重复均观察到：第一轮的BB、分区归属和分区内计划顺序一致。第一轮结束后，无修复模式丢弃动态更新通知；修复模式送达。第二轮开始，网络BB仍相同，但分区归属已经不同；第三轮起BB也随路由轨迹分化。

|布局|首轮通知生成数|无修复送达|修复送达|实际迁移|同分区删除再插入|无修复第1–5轮越界网络数|修复越界数|
|---|---:|---:|---:|---:|---:|---|---|
|s38417_s1|151|0|151|9|142|[0, 9, 19, 28, 32]|[0, 0, 0, 0, 0]|
|s38417_s2|139|0|139|8|131|[0, 8, 14, 21, 27]|[0, 0, 0, 0, 0]|

越界判定直接复用原PartitionTree的二维包含条件；不是最终布线非法的同义词。例：s1第二轮网络2850的BB x范围0–9，但仍分配在x范围0–8的分区2。修复后的归属满足边界条件；不能把遗漏通知保留旧分区作为提速策略。

## 顺序变化与可研究优化

PartitionTree::update_nets即使old==new仍erase/insert；ParallelNetlistRouter随后从unordered_set生成列表，再按扇出stable_sort。首轮s1有142次、s2有131次同分区重新插入。重复运行中通知集合相同但到达顺序可以不同；s1修复模式第二轮起出现分区内顺序差异，而BB和归属仍相同。该机制与容器顺序/同扇出排序敏感性一致，不代表全局线程启动顺序必须一致。

下一候选是保留所有必要通知与跨分区迁移，仅跳过old==new的删除再插入；另一个候选是显式稳定同扇出次序。两者都会改变既有启发式顺序，必须独立验证合法性、质量和未诊断完整进程收益；本轮尚未实现或证明它们有收益。

## 诊断扰动与边界

四组两修复对照中，旧ELF、trace关闭、trace开启的最终路由/质量/轮数均一致。无修复四组中有一组trace关闭/开启不一致：51轮/8.33758ns与49轮/7.05387ns。不能排除诊断扰动，也不能把旧的无修复端点等价失败改写为通过。

记录只覆盖前五轮，不能覆盖后期全量重载机制；没有记录RR前驱状态写入，不宣称证明了竞态或全部运行波动根因。上一轮同ELF缓存约3.3%退化仍未解决。默认两修复保持开启，历史源码/二进制不变。

## 重现与字段

build_native_state_trace.py构建隔离route.cpp.o和partition_tree.cpp.o；run_native_state_trace.py执行24项；analyze_native_state_trace.py分析日志；本脚本写结论。首次overlay头文件重复定义的编译失败保留在build_first_failed.log，增加优先include路径后构建通过。

state_trace.tsv各列：seq、iteration、kind、net、partition_path、aux、BB xmin/xmax/ymin/ymax/layer_min/layer_max、partition xmin/xmax/ymin/ymax。kind=0轮初快照、1分区内计划位置、2调用开始、3调用结束（aux为rerouted/retry/success位）、4通知送达、5迁移前、6迁移后、7动态更新列表。分区路径root=1,left=2p,right=2p+1。全局seq是观测点的原子线性化次序，不是确定性的完整路由执行顺序；按分区比较计划顺序才有意义。线程缓冲在barrier后输出。

证据：analysis.json、conclusions.json、acceptance.json、evidence_verification.json、build_provenance.json及runs/serial各measurement.json/state_trace.tsv。
