# SPARSE_STREAM_R2 续跑包

请将整个压缩包上传到服务器，让 Codex 首先完整读取 `CODEX_FPGA_SPARSE_STREAM_R2_GUIDE.md`。新工作基点为 `5651a34abb97939bee6402c5af585753ab07f64b`。

## 文件

- `CODEX_FPGA_SPARSE_STREAM_R2_GUIDE.md`：完整实现、验证、性能边界和持续执行指导。
- `audit_bounds.py`、`bound_review.json`：从真实逐 wave 归档复算原必要界和条件反事实界。所有反事实值都不是 FPGA 预测。
- `semantic_validation/validate_pop_reduce.py`：POP 输出归约的小型算法差分脚本，标准库即可运行。
- `semantic_validation/{cases,results,failures}.json`：实际输入、180 项差分结果及失败归档；四个刻意错误变体的结果在 results 中。
- `SHA256SUMS.json`：包内文件校验值。

## 复算命令

在本包目录执行，替换 REPO_ROOT 为包含 R1 归档的仓库路径；输出到新的目录以保留原审查记录：

```bash
python3 audit_bounds.py --repo-root REPO_ROOT --output rerun/bound_review.json
python3 semantic_validation/validate_pop_reduce.py --outdir rerun/semantic_validation
```

小型模型检查只隔离输出归约变换，不模拟真实 VPR eligibility、完整原生大图、有限硬件队列和访存，也不证明 RTL 正确或加速。新方向仍须按指导完成 C++、native、RTL、OOC 和完整有限架构模拟。

本包是对 R1 代码和证据的审查及下一步指导，没有运行新的服务器 GPU、RTL、HLS 或 OOC 作业，没有修改或推送项目仓库。
