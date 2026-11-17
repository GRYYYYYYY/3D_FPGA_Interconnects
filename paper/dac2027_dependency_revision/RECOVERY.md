# 恢复与终止边界

本修订分支的范围仅为 `paper/dac2027_dependency_revision/`。从 README 与 review/checks.json 进入，勿重建重复 paper worktree。旧冻结稿在 `accel/lookahead/fpga_cpu_primary/submission/`，其 61 个文件通过原 SHA 核对。全部新图表可由 `recompute.py` 重算；当前任务的补证到此结束，不自动开始下一轮。

h 的实际 project/run/session/PID/birth 身份见 `evidence/h_readonly_snapshot.json`；该文件是观察快照，不是恢复/启动指令。现有 observer 最新输出和 run_receipt 快照分别保存在 `h_existing_observer_last.json`、`h_run_receipt_snapshot.txt`。h 在单独 CPU_PRIMARY worktree 的原收尾链继续，paper 分支不含启动命令或新输入。

未合格的完整核频率、实际 FPGA 时间和 achieved CPU/FPGA speedup 为“尚未建立”，没有用目标频率、局部 RTL 或条件模型补空。若另一授权链后续交付终态，再按截止和 source/service/frequency 资格决定是否另行修改实现表与相关结论；本修订已经可独立交付。
