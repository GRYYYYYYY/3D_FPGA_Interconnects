# 较大输入原生 CPU 扩展

所有输入来自既有 Koios 套件；不是独立新基准。原版默认参数重新打包布局。共享宿主、单 lane；正式路由各臂八个物理核，串行仅指 lookahead 构建。

链终态：`complete_qualification_rejected`。默认算法未改变。

|准备输入|状态|准备秒|打包后放置块数|RR 节点|RR 边|
|---|---|---:|---:|---:|---:|
|dla_like.medium_s1|True|801.68|28507|7312040|64251424|
|dla_like.medium_s2|True|816.88|28507|7312040|64251424|
|lstm_s1|True|391.65|17432|3929844|34459546|
|lstm_s2|True|392.40|17432|3929844|34459546|
|bnn_s1|True|359.60|15331|3869928|33889468|
|bnn_s2|True|360.06|15331|3869928|33889468|

qualification：计划 30，已尝试 30，合法 5；状态 completed。

资格门槛：failed；失败输入：['dla_like.medium_s1', 'dla_like.medium_s2', 'lstm_s1', 'lstm_s2', 'bnn_s1', 'bnn_s2']。

正式性能矩阵未完成，不报告新的加速比。

准备后处理修正：原 XML 计数器假设 id 是 node 的首个属性，漏计节点；原始失败收据完整保留。修正器只按标签统计并重新核验既有输出，未重跑布局、修改 RR 图或更换输入。

实际环境检查错误：[]。资格不通过时保留所有失败，不更换电路或调宽线宽来筛选正例。

详见 protocol.json、preparation.json、qualification_gate.json、qualification_audit.json、formal_audit.json（存在的阶段）、analysis.json。
