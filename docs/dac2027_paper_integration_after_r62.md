# R6.2 后 CPU/ALT 论文整合结项

基点 ea1d0d793f7655d421595fcf2ee961c9cdc9af92；独立分支 paper/dac2027-cpu-alt-integration-20261110。
新稿位于 paper/dac2027_integrated，原 paper/dac2027、STRICT、golden、算法默认路径与全部旧实验证据均保持原状态。

## 交付

- frontmatter.md / abstract.txt：题目、99词摘要与三项贡献。
- main.tex / main.pdf：IEEEtran conference 10pt 双栏，submission 模式，6页正文+1页纯参考文献。
- generate.py / tables / figures：复用旧 CPU paper_statistics.summary 与 R6.2 小SD格式逻辑；从既有ALT扩展抽取方法/证据进入正文，不直接input独立文档。
- claims_accel.json / computed_statistics.json / data_bindings.json / method_binding.json：逐主张数据、cohort、原始行ID、host、输入/二进制哈希及源码绑定。
- check_paper.py / format_check.json / visual_review.json / preview：实际限页、匿名、嵌入字体、引用、超栏及7页逐页视觉检查。
- build.py / BUILD.txt / README.md / submission_source.zip / source_archive_build_check.json：完整再生流程及干净临时目录源码包复建。
- citation_review.json：新增Delta-stepping/GPU SSSP原始来源和最接近MultiQueue routing的范围核对。

源码ZIP是匿名排版输入，含全部非标准正文/表图文件、参考文献及构建说明；带服务器身份的内部claim ledger保留在仓库中，不进入该匿名ZIP。再生脚本及其全部冻结数据依赖位于指定基点和本paper提交的仓库中，统计再生无需实验工具。

## 主线与结果边界

三项贡献为STRICT跨样本等价构建、独立ALT whole-pair FP32桶/波次搜索、原生分层时间与语义/QoR验证。保留source identity反例、STRICT命题within-flood visitation不变前提、原顺序归并及插值边界；ALT明确列出输入域、整体pair选择、bit-key/shift、snapshot、重入/闭包、严格改进与停止条件。

主结果采用LSTM同机同组Pipeline/ALT CUDA：E2 3.207±0.147×、Process 1.094±0.010×。LSTM是已用于CPU项目的同架构家族ALT调参留出，不是跨架构泛化。CPU/CUDA sample与wire map一致，但route SHA不同；各route独立通过身份保持的FULL/STA和QoR。相对Flat有23111个congestion word差异，delay/missing为0。原生边界空CHANZ诊断已解释，不能推广为完整RRG clean。

BNN只使用R6.1同组Flat对照，E2 3.274±0.222×、Process 1.091±0.011×。s38417保留CUDA负结果（Flat/CUDA E2 0.274±0.032×、Process 0.912±0.016×）。R6.2 P1旧案例Pipeline和P2 CUDA不事后配对。转换候选只作次要消融，BNN E2 1.082±0.037×，Process方向不一致，不继承LSTM资格、不相乘倍数。

旧CPU603 formal仍为414 legal full-flow+189 construction-only。R6.2的43 managed仍为33正式计时+9资格+1画像，不合并为646 formal。旧CPU pairs派生表含scope为空与full的重复视图；本稿GEMM显式取scope=full的3对原始ID，并绑定6个原始measurement，而非把重复视图当6对。CPU scaling逐点核对原始冻结summary计时；历史GEMM每次measurement没有hostname字段，账本明确记录cohort host A及该缺失，不伪造主机名。

Stock/CUDA大倍率是整个声明过的实现组合；共享修复底座的Pipeline/Flat/ALT优先用于归因。源码/对象绑定没有解释全部下游路线分化；图边界诊断与Stock修复归因限制都保留。

## 验收与限制

完整再生、数据哈希/配对/小SD检查、TeX/BibTeX构建、真实6+1页检查、匿名、嵌入字体、引用及无超栏检查通过。全部7页实际逐页查看；最终重建页面raster哈希与已查看版本一致。源码ZIP在干净临时目录仅用归档排版输入重建，页数和抽取文本与交付PDF一致。仍有不导致超栏的underfull排版提示；algorithm.sty上游注释有UTF-8提示，交付PDF无替换字符或缺字。没有通过修改字体/边距绕过限页。

本轮未启动任何GPU/solver/native计时/HLS/RTL/OOC/FPGA探针；仅读取记录、复算、绘图、构建文稿。FPGA状态保持UNRESOLVED_NO_SUPPORTED_MEMORY_EVIDENCE，fpga_superiority_verified=false，board_measured=false。硬件成功仍缺实现频率与校准随机whole-pair RMW服务，不能靠文字填补。

未发现阻塞本次CPU/GPU论文成文的证据缺口；现有泛化与硬件限制已明确写入正文。作者身份/COI、原创性声明和正式投稿由作者处理，本任务未提交投稿，推送后结项，不自动启动实验。

官方格式于2026-11-10核对：[DAC2027 Research Manuscript Submissions](https://dac.com/2027/program/research-manuscript-submissions)。6+1仅是格式验收，不代表论文科学贡献已获外部评审通过。
