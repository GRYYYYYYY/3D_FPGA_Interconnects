# R2 接续指导与复算依据

主入口：`CODEX_FPGA_R2_CONTINUATION_82860ce.md`。可直接交给服务器 Codex，在当前 R2 上续做。

本包为固定提交 `82860ced203bde54f1fa267446b3d0edc521a293` 的审阅与建议，不含新 FPGA 或软件实验，不代表现时服务器进程状态。已有完整输出、周期和流量取自该提交归档；wave 私有 accumulator 是尚待验证的提案。

文件：

- `sparse_r2_review_metrics.json`：P32诊断、P8八项模型、软件目标和规划下界。
- `sparse_r2_wave_accumulator_bounds.json`：现存逐wave计数推导的 touched-line 容量区间。
- `sparse_r2_wave_accumulator_traffic_screen.json`：两种候选布局的条件流量区间，含明确的未知与额外成本。
- `recompute_bounds.py`：Python标准库复算程序，不启动实验、不访问服务器。
- `review_bounds_200mhz.json`：以200MHz为假设输入生成的复算结果，200MHz并非已取得的完整核频率。
- `SHA256SUMS.txt`：本包文件校验。

运行：

```bash
python3 recompute_bounds.py --frequency-mhz 200 --output review_bounds_200mhz.json
```

改变频率时，脚本仍保持服务gap的cycles不变，因此服务速率假设也随之改变；它不替代固定纳秒内存合同校准。精确 touched-line 总数和实际新架构流量仍需新增画像。下界通过不等于实现成功。

项目和外部方法依据见指导第10节。使用本包时保留来源、同范围基线以及 board_measured=false 等证据边界。
