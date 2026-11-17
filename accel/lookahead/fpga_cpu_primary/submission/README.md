# 独立投稿稿：原生成果冻结，h 物理实现并行收尾

本目录在当前 CPU_PRIMARY 分支内新增，不修改 `paper/dac2027`、`paper/dac2027_integrated`、STRICT、golden 或历史证据。完整论证不以 FPGA 实现成功为前提。研究输入于 2026-11-17 00:25:11 UTC 冻结；正文在逐页检查后由 `manuscript_freeze.json` 固定。

- [匿名投稿 PDF](main.pdf)：6 页正文 + 1 页参考文献。
- [匿名 LaTeX 源码 ZIP](submission_source.zip)：只含编译所需正文、表格和参考文献；已在空目录重编译，抽取文本一致。
- [主张账本](claim_ledger.json)、[检查结果](review/checks.json)、[完整编译输出](build.log)、[PDF 抽取文本](main.txt)。
- [作者通读与提交检查](AUTHOR_REVIEW.md)。
- [当前物理资格](physical_qualification.json)、[布局证据快照](evidence/physical_snapshot_20261117_a.json)。

## 结果边界

STRICT 的 wire-map 等价性有明确的顺序与数值前提。ALT 是独立的 whole-pair FP32 bucket-wave 契约，不能以 CPU/CUDA 同输出推导 STRICT 等价。原生 LSTM 的 CUDA/Pipeline 结果为 E2 3.207±0.147×、Process 1.094±0.010×；小规模 s38417 的负结果保留。

64-worker resident CPU 是另一实验口径：BNN40 0.699624±0.026647 s，LSTM40 0.725510±0.021287 s。模型在**假设 200 MHz**、基础 80/5 ns 和保守 160/10 ns 服务下给出完整 batch 预测；这些不是布线频率结果或板测。52 次完整 RTL 执行、11 个拒绝配置和 160 个完整模型输出直接复用，没有新启动 CPU/GPU/模型实验。

h 已完成综合、标准 opt 和布局，布局后资源为 1,212,828 LUT、749,091 FF、1,148 BRAM36 等效、640 URAM、0 DSP；CLB site 使用率 99.86%。这些资源不含板卡 shell/PCIe/HBM 控制器。尚无合格完整核布线频率，正式 FPGA 时间和相对 CPU 加速比均为空。当前 h 在原会话中继续报告/实现，不重启。

## 编译和复核

在本目录执行：

```bash
python3 build.py --tectonic /path/to/tectonic
```

已使用 Tectonic 0.17.0 和 Poppler。脚本仅检查证据、编译论文、独立重建 ZIP 和生成预览，不运行 solver 或 EDA。内部证据检查需要当前仓库及其已归档原始结果；仅重编译匿名源码 ZIP 不依赖仓库或实验数据：解压后执行 `tectonic main.tex` 即可。

首次逐页确认后执行同一命令加 `--freeze`，以排他创建正文冻结回执；后续普通构建自动验证固定科学内容，不能覆盖冻结回执。构建可能保留 TeX underfull 排版提示和上游 algorithm.sty 注释的 UTF-8 警告；检查不允许溢出框或未解析引用。所有字体嵌入，无 Type 3 字体。

官方规则要求的独立 AI 内容披露节已补入；其单独修订回执为 `submission_compliance_addendum.json`，其排版长度修订由 `submission_compliance_layout.json` 继续绑定。原正文冻结回执保留，方法、实验数字与结论未改；后续构建同时验证该固定补充。

## h 终态和内部截止点

新增 FPGA 成功主张截止：**北京时间 2026-11-18 09:00 = UTC 2026-11-18 01:00**。这与会议系统的官方提交截止不同。

仅允许在 h 终态后更新以下四个正文文件，且只修改相关实现/资格语句：

1. `tables/implementation.tex`
2. `sections/performance_qualification.tex`
3. `sections/abstract_hardware.tex`
4. `sections/conclusion_hardware.tex`

完整核 route、setup/hold、约束和实际 clk 连通均合格后才能给出频率。不能把 reset/enable BUFG 当作核心时钟，也不能把局部模块或失败 route 的 WNS 换算为合格频率。原频率、服务和源码绑定成立时复用现有证据；条件改变则按纳秒服务重新离散化，补必要校准与完整 BNN40/LSTM40 模型，不能直接缩放旧周期。需同步更新内部资格、账本、证据索引和恢复说明；固定科学正文哈希保持不变。

h 失败时保留 DCP、终态、日志、资源、路径和告警解释，不自动开始大规模新架构。内部截止后不新增 FPGA 成功主张，优先作者通读与提交检查；不要求停止仍有价值的在途研究。未取得合格频率时当前完整稿即可成立，不留“等待硬件成功后补结论”的占位内容。

## 归档与匿名范围

`research_scope_freeze.json` 与 `evidence/additional_frozen_inputs.json` 绑定原生、CPU/GPU、源码、RTL 校准和完整模型输入；物理布局快照单独绑定。旧 `native_claims_accel.json` 是历史输入副本，当前主张以 `claim_ledger.json` 为准。原始结果由候选目录的 `delivery/archive.py` 内容寻址归档，完整 DCP 留在原工作区并保存哈希/重放脚本。

Git 中的内部回执、绝对路径和机器日志用于研究恢复，**匿名提交包只取 PDF 和源码 ZIP**。尚未代作者执行外部投稿。
