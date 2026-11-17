# 实际补证与停止记录

P0 已落实：从 63 条 component_formal 原始记录复算 7 组 Group/Flat/Pipeline 配置和成对比值；从 BNN40 两个 shift 的逐波日志复算所有波次、边工作量与加权前沿；从 native formal rows 复算 LSTM E2/Process 和 paired ratios；核对 QoR 差异与完整 CPU/CUDA 输出。重算六个 resident CPU 配置及两服务情景的 160 个完整模型输出回执，复用 52 个完整 RTL/model 校准执行。没有重新运行这些求解实验。

**P1 执行**：冻结补证计划后，运行 SHA-256 为 `5d32c536b729d87ffd33a9c354ec157662b703f96dcc8ed02fcb522355de2355` 的锁定二进制 `--help`。第一次因未设置历史 runtime 路径退出 127（libtbb 缺失）；恢复已有 `LD_LIBRARY_PATH` 后退出 0，没有重编译。完整 stdout、首次失败、binary strings 和 compressed-map 源码保存在 evidence。`compute` 显式要求 `grid.get_num_layers()==1`，相同错误字符串存在于该二进制。冻结 BNN/LSTM 输入审计为两层。故静态适用性判定 unsupported；**没有执行完整 3D solver，不能报告 3D runtime exit code**。CompressedMap read 和二进制写出未实现，CSV 写出单列。没有移植、升级或填补无穷大时间。

**缓存复用**：复核历史 36 条 formal reuse 的读缓存命令、成功路由及独立 FULL/STA 返回状态。固定输入来源由同一历史 cohort 的输入绑定/qualification 提供，不把历史缓存与另一主机重建时间相除，也不免费摊销未来重复。可重算清单见 `evidence/cache_reuse_audit.json`。

**P2 跳过**：旧逐波数据完整，足以复算所需机制指标。加权前沿精确比值为 6.6484001103；任务书 6.648403 为显示舍入差异，不采用更大的近似值。

**P3 跳过**：自身和 h 同属 cgroup `0::/`，CPU quota 为 `5500000 100000`；无已确认独立计时 worker。因此不做新增强线程 native/CUDA 或泛化正式对照。既有 corpus 中 16 核 full-flow 是 GEMM Group/Pipeline 六条，不是 LSTM 或 BNN 的 matched CUDA cohort；64-worker 仅作为已测 resident 主对照，不能包装成 native 64-worker E2。

**h**：仅查询既有 MCP 会话并核对 PID/startticks/boot、原 project 与在途 Tcl。快照时 place、post-place reports、phys_opt 完成，route 运行中。没有启动、重置、中断、修改输入或重复 observer。本论文任务不接管另行授权的硬件收尾链。

停止扩展：最重要适用性缺口已补，全部可选新 solver/GPU/RTL 实验均未启动。继续研究不作为修订稿交付条件。

Separable 补充核查：锁定 help 确实列出此模式；当前源码具有 layer 索引和 CHANZ 维度，不把它误报为 compressed_map 的单层限制。其 read/write 明确未实现。当前源码与该二进制的逐文件对应未被证实，且本轮未做其两层 native 资格或正式计时，因此不作支持正确性/性能结论，不启动移植或新矩阵。

## 作者终审有限编辑（以 bffa5626 为基准）

本轮仅修改摘要的 speedup/baseline 措辞，并将正文中的修稿执行说明保留在本文档：没有新增 performance solver/EDA；没有独立 CPU 配额，因此没有新增 formal timing；旧完整 profile 足够，因此没有新增 shift 扫描；没有升级或移植 VTR。实际线程/NUMA/共享主机条件、计时边界和研究限制留在正文。没有重跑 CPU/GPU/模型/RTL 实验。重编译中的 recompute.py 仅核算归档数据，不启动实验。h 监督另行进行，论文结项不代表 h 收尾完成。
