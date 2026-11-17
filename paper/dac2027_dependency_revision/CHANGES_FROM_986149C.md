# 相对冻结基准的变更

基准完整 SHA：986149c07bc7b8be54d99e8a2e2a47327ec143b5。开始时 CPU_PRIMARY 分支 HEAD 与该基准一致，工作区无后续修改；没有回退。新建 paper/dac2027-dependency-revision-20261117 worktree/分支。

所有交付位于 paper/dac2027_dependency_revision。旧 submission、原冻结回执/哈希、main、STRICT、golden 和历史数据不改。

1. 全文组织从平台/开发顺序改为源上下文与双粒度依赖；同步摘要、四段引言、贡献、方法、有限映射、实验、结论。
2. 增加 Group/Flat/Pipeline 误差棒图、完整 shift0/20 工作量表、语义保证表；保留 native QoR 表、小图负结果及独立 resident/conditional/physical 表。
3. 修正 LSTM chronology、共同接口的 CSR 误述、八核 native 与 64-worker resident 边界；加入已有 16 核 native 记录的限定。
4. 最近工作尊重各自实际贡献；LaZagna 更新正式版本，补 SPLAG；加入锁定 compressed_map 单层限制与有效 map-cache 路径。
5. 压缩内部轮次/流程审计文字，将完整证据绑定、进程身份与失败详情移至 artifact；不改变历史实验、数值或冻结哈希。
6. h 仅更新新稿的实际状态为 post-place/phys_opt 完成、route 在途。目标 200 MHz、模型内存假设与合格频率明确分开。
7. 独立匿名源码包只含实际排版依赖，原路径/账号/内部报告不进入包；增加本轮可复算脚本、验证报告和作者审核项。

本轮没有制造新 formal solver/GPU/RTL 性能结果。新证据是只读重算和有界兼容性预检。

## 作者终审增量：相对 bffa5626ac7e984f3018b5e9be9f4b95ac18541b

仅两类文字编辑：摘要明确使用 achieves … speedup over the eight-thread CPU Pipeline baseline，保持 3.207/1.094、construction/complete-process 与 native LSTM same-family tuning holdout；正文移除无独立配额、未新增 solver/EDA/shift sweep、未升级 VTR 等修稿执行说明，保留补证文档中的执行事实。实际实验条件、适用性及限制不变。更新 PDF/匿名源码包/编译检查；不改原冻结回执，不开展新研究实验。h 身份核验和后续监督另行记录。
