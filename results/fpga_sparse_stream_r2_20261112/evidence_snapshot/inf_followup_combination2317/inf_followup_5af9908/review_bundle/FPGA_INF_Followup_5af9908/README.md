# INF 接续指导与审阅依据

主入口：`CODEX_FPGA_INF_FOLLOWUP_5af9908.md`。

本包基于固定提交 `5af99087a9d7055d468cc5269326d985b911919d` 的只读代码、报告和归档审阅。没有操作服务器作业，没有运行新GPU/FPGA实验。运行状态为固定快照，执行时需刷新。

- `inf_r2_continuation_audit.json`：两个执行脚本缺陷、任务范围和软件统计口径。
- `inf_r2_physical_review_5af9908.json`：微核实际时序/资源、最坏路径与拟议RAM组织。
- `inf_r2_pending17_review_5af9908.json`：pending17不变量与原子性边界。
- `derived_layout_screen.json`：对原逐wave统计的算术复算，新增布局尚未实现。
- `recompute_layout_screen.py`：复算入口；只读原归档，校验输入SHA并精确复现原hybrid下界。
- `SHA256SUMS.txt`：包内校验。

## 复算

大图原始逐wave文件已在项目仓库归档，本包不重复收录。准备一个input目录，放以下三个解压后的文件：

1. `bnn_wave_lines.jsonl`：来自 `results/fpga_sparse_stream_r2_20261112/evidence_snapshot/checkpoint_20261113T2135/accumulator/private_inf_bounded_a/bnn_export/wave_lines.jsonl.gz`。
2. `lstm_wave_lines.jsonl`：同上 `lstm_s2/wave_lines.jsonl.gz`。
3. `wave_accumulator_bounded_a.json`：来自 `results/fpga_sparse_stream_r2_20261112/evidence_snapshot/continuation_tail_2158/analysis/wave_accumulator_bounded_a.json.gz`。

使用固定审阅SHA的文件；服务器保留的相同原始文件也可直接使用，脚本会校验逐wave字节SHA。

```bash
python3 recompute_layout_screen.py --input-dir /absolute/path/to/review_inputs --output recomputed.json
```

本次已运行复算入口，并核对输出与 `derived_layout_screen.json` 完全一致。该验证不构成硬件模型校准或性能实测。文件中的200MHz、P32/gap1等是条件；0.143656/0.145130s不是完整预测，也没有证明胜过软件。已计初始化的规划项仍采用理想并行服务，需要新有限实现确认。
