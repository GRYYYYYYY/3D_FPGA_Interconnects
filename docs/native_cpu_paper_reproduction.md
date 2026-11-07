# 论文实验与复现入口

工作目录为本工程根目录，使用 `python3`。绘图使用 `.venv-report/bin/python`。原生 VPR 是已冻结 ELF，运行所需动态库由 `data/vpr_runtime_20261025/runtime.json` 绑定。新实验必须写新目录；历史结果、二进制和已冻结脚本不覆盖。

## 阅读及复核

统一主表入口：

```bash
python3 scripts/assemble_native_cpu_paper.py
```

它生成 `docs/native_cpu_paper_tables.md` 和同名 JSON，只纳入已独立复核的数据；正在执行或尚未启动的集合仅显示状态。它不会启动求解。不同对照、计时范围和样本集合不合成总加速比。

新增研究达到终态后，可重新复核全部输入、产物、实际命令/env/CPU、map、合法性/STA、执行顺序与配对统计：

```bash
python3 scripts/review_native_flat_baseline.py
python3 scripts/review_native_flat_baseline.py results/native_large2d_followup_20261105
.venv-report/bin/python scripts/plot_native_flat_baseline_v2.py results/native_flat_baseline_20261105
.venv-report/bin/python scripts/plot_native_flat_baseline_v2.py results/native_large2d_followup_20261105
```

复核脚本拒绝把运行中的结果作为终态。大型二维准备失败时，只复核并报告失败，不输出速度比。图表导出 PDF/SVG/PNG，仍需目视检查版面。

## 在新目录复现三个修复版对照

默认只打印具体命令，不启动实验：

```bash
python3 scripts/reproduce_native_lookahead.py --output results/reproduce_bnn_w8_new --case bnn --workers 8 --repeats 3
```

加 `--execute` 才运行；三种方法依次轮换，读取相同冻结 RR/packed/place/reference map，使用同一修复 ELF和同一 NUMA节点内的物理核。`--kind component` 为默认，一轮路由尾部不算合法布线；`--kind full` 运行完整布线并独立 FULL/STA 检查；`--kind memory` 开启独立内存/分项诊断，不能纳入正式计时。

```bash
python3 scripts/reproduce_native_lookahead.py --output results/reproduce_bnn_w8_new --case bnn --workers 8 --repeats 3 --execute
```

案例：`tseng_2d`、`clma_2d`、`bnn`、`dla_like.medium`；`bnn_2d` 仅在大型二维准备成功后可用。新运行不自动混入论文历史统计；不同宿主尤其必须单独标注。若本宿主已有本轮主链运行，复现入口拒绝并发求解。

添加 `--include-stock` 可纳入相同CPU预算的原版VPR。它适用于阶段或完整进程比较，不能用于原版不支持的阶段内存诊断。以下命令预览四个对照的实际命令及方法选择环境；仍需显式 `--execute` 才启动新测量：

```bash
python3 scripts/reproduce_native_lookahead.py --output results/reproduce_bnn2d_full_new --case bnn_2d --workers 8 --repeats 3 --kind full --include-stock
```

## 源码与完整实验链

`results/native_flat_baseline_20261105/source/` 保存两个替换的原生 translation unit 和诊断头；逐文件 `.patch` 保存相对 `vendor/vtr_cpu_slices` 的差异。`build_inputs.json`、`build_provenance.json` 保存编译、归档、链接命令及 SHA256。构建通过 `make` 从 vendor 源码根目录调用，在独立 archive 副本中替换两个对象；原 vendor 源和默认 ELF不变。重新构建应先把构建脚本的 OUT 改到新的实验目录，或在独立工作区重放已保存命令，不对已冻结目录直接执行构建脚本。

主链计划为 `results/native_flat_baseline_20261105/plan.json`：6项诊断pilot、4项clma资格、条件12项完整进程正式、54项阶段正式、9项内存诊断；另一次pack/place/RR准备不计正式。六pilot及stock clma求解完成后曾出现记录顺序错误；`continuation_plan.json`和`attempt1_terminal.json`保留原因与原现场，只补缺少的检查，没有重跑完成的求解。不能再次运行旧owner或continuation脚本。

主链终态复核后，相同 `packed.net` 归档副本经逐份哈希核验后合并为硬链接。两次操作分别释放约4.6GiB和11.05GiB，所有路径和SHA256保持；仅本轮新增且已完成的归档涉及此操作，历史原始输入不受影响。记录见 `completed_input_deduplication.json` 与 `completed_input_deduplication_remaining.json`。这些文件不可原地编辑；复现入口会复制到新的结果目录，不在归档中重新pack/place。

大型二维后续计划为 `results/native_large2d_followup_20261105/plan.json`：原始 `2d_architecture.xml`、BNN、seed1、通道120、利用率0.5，自动选择既有布局；准备最多1800秒，单次布线最多900秒/200轮。4资格、条件12完整进程、9阶段正式、3内存诊断。参考资格失败时保留失败并跳过完整流程性能；不扩宽重试或换样。

两链共享fpgaacc2时必须顺序执行。CPU实例有55CPU时间配额，但未证明物理核独占。实际亲和性与cgroup记录是实验控制证据，不是独占证明。原监督在主链复核通过后因Jupyter继承的绘图backend停止，v2已在导入matplotlib前设置Agg修复。

大型二维链完成4资格、12完整正式和4阶段正式后，在下一次进程启动前触及60GiB磁盘保留线。原现场 `disk_stop_terminal.json` 保留；该条目只有两个输入文件，没有启动solver。核验旧solver/监督退出后，完成上述第二次归档去重，再按 `disk_continuation_plan.json` 接续8项未启动测量，实验参数、顺序和磁盘下限均未改变。原输入目录保存在 `preflight_disk_stop/`，已完成20条记录逐字保持；没有重跑任何已完成solver。续接复核见 `disk_continuation_review.json`。

两链现均已完成独立复核和图表目视检查。大型二维阶段repeat1跨越519.84秒预检暂停，相关配对完整保留；全部完整正式测量在此之前结束，存储操作没有与测量重叠，见 `storage_event_audit.json`。不把该阶段的微小时间差解释为完全隔离的调度因果。

此链当前/终态状态和唯一owner见 `results/native_large2d_followup_20261105/disk_continuation_status.json` 与同目录 `disk_continuation_receipt.json`。此前两个supervisor状态保留为历史停止记录。恢复前先读最新状态与远端回执，不能再次运行旧owner或续接脚本。

## 解释边界

`wire_map.bin` 字节一致仅覆盖序列化wire表。完整流程要求原生及原版独立FULL/STA；CPD、线长均按冻结的5%门槛判断。三次runtime重复报告全部配对比值、中位和范围，不声称统计显著性。内存是阶段内近似RSS采样和部分结构容量计数，不是硬上界；标签容量仅覆盖wire flood的expanded/visited数组，未统计src/opin工作区、队列和分配器，不能用它与RSS直接相减作完整分解。

诊断原始 `lookahead_profile.jsonl` 沿用了全局函数的 `tokens` 字段；当 `scheduler=flat_parallel_for` 时该值没有参与调度，不能解释成flat的存储上限。flat保留全部S张样本表，实际解释应使用 `stage_memory.jsonl` 中的 `sample_map_count_bound=S`。复核脚本和主表按这一规则处理，冻结原始记录不回写。

此前三维宽120、k6 tseng/des、fpgaacc1扩展性及真实缓存批次仍使用各自原始协议，入口见 [证据索引](native_cpu_paper_evidence_index.md)。首次贡献、GPU收益和三维新寻路算法都不是这些复现命令能够自动证明的结论。
