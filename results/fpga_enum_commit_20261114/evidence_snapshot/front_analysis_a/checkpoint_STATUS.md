# 执行线 F：阶段证据与范围

最终候选采用八个独立组，组内 LANE_RR。公平分配确实减少低编号偏置，但大型 native wave 的净收益有限，且保留了负例；这些局部周期不能外推完整 batch。

已完成：

- `results/fpga_enum_commit_20261114/front_compare_a/terminal.json`：17 native +2 已有连续窗口，FIRST_FREE/LANE_RR × 原接收带宽/8路带宽，共76次。19项 FIRST_FREE 原带宽复现旧 B 的周期和逐lane发射数。
- `front_grouped_a`：38次，每周期最多8派发且每8lane组至多一次非空E写入；`front_grouped_b` 同机制追加逐lane等待/槽占用统计，38次；均通过。
- `front_independent_a/terminal.json`：最终八个独立组，同资源FIRST_FREE/RR的38次匹配验证。fork/H/M/ready各组16；跳过满组的fork RR每周期全局最多8成功预留、每组最多1；组内H、M、ready服务各最多1/cycle；E组内RR仅真实非空分配成功推进。零度不占E。
- 最终两个大波次：BNN2_38 FIRST_FREE118660 / RR117729（改善0.7846%）；LSTM7_36 FIRST_FREE121155 / RR120281（改善0.7214%）。BNN35_53反例897→905；BNN压力窗口458→458。详表和lane/port数据在`front_analysis_a/summary.json`。
- `verify_front.py` 独立验证190次实际运行、95对结果/流量/容量/直方图守恒；该数量含为追加统计而重复执行的38次，不把它算新架构。
- `front_bindings_a` 绑定公共源码依赖和工具版本，最终独立组及global-group模型从同源重编译，与运行二进制SHA256相同。

RTL：

- `frontend_group.sv`：8lane×4 E、每lane8 beat槽，D1；每组1parent/cycle，输入边界为已经完成CSR row读取的parent。真实`fpga_sparse_stream/rtl/fp32_positive.sv::pair_lane`两级弹性算术，原descriptor/cost operands参与计算；单注册请求级，tag恢复generation/slot，有限返回槽与consume RR。
- `front_rtl_a`：首版两模式、两个epoch不reset，共144parent/2136结果/每模式378请求，849周期记录独立逐时钟校准通过。
- `front_rtl_b`：并行资格判定、局部选择、静态索引写入；零度即使E满也允许完成。两模式各784周期独立精确核对通过。
- `front_rtl_c`：对B的完成/发射计数增加一级pulse与平衡popcount，避免统计计数器成为长路径。核心请求/返回/FP32时序未变，B/C外部校准trace哈希完全一致，两个模式仍各784周期通过。
- `allocator_grouped.sv` / `front_allocator_rtl_a`：全64lane/256E/最多8grant的有限global-selector，1024周期/每模式1748grant精确校准。它属于保留的global因果设计，最终完整模型选择独立组；不给它授予最终组路由/时序资格。

仍需明确：

- 组RTL没有POP/fork/H/metadata/reducer/目录/全64lane返回路由，不能称whole-frontend校准。node/epoch在这个completed-header leaf中为注记，epoch屏障由外部驱动；合成会移除未使用的注记状态，不能声称已校准qid/epoch控制。
- RTL TB两个模式使用确定性但不同mode相位的响应抖动，目的是功能压力/周期模型核对，不把该TB的模式间差值当严格性能比较。严格性能比较使用上述同合同C++配对。
- 一笔共享物理口，最小16cycle、gap1；实测credit峰值22，未覆盖32credit饱和。非法generation响应有error路径，但尚未单独注入非法旧响应。
- `front_independent`仍是有效POP输入、理想candidate sink和每wave目标重建的局部模型。全模型另行接入；不能继承局部性能资格。
- leaf在实际RTL中有一拍注册请求，输入parent后最早两拍物理issue，response接收后下一拍可选候选，pair接受后两拍输出；完整模型需要保留该延迟。C的遥测pulse增加最多一拍统计排空，不省略真实pair/slot排空。

200MHz OOC已按0.5ns输入/输出预算运行，使用Vivado2022.2/xcu280-fsvh2892-2L-e；A/B/C路径为`front_ooc_a/b/c`。A综合最差ending[0]→nextbeat[1]长优先链WNS -22.723ns；B去除此链后最差pos[11]→completed统计加法链WNS -17.143ns；C已修复此统计路径。负结果、精确源和全部报告保留。最终route状态见后续`front_analysis_a/timing_status.json`，在终态前本文件仅是F线checkpoint，不宣称全部完成或时序合格。


D补充：`front_rtl_d/calibration.json`及`front_offset_bounds_b`已通过。E offset现在只支持显式检查的32-bit范围；CSR输入/存储仍为64-bit，高32位非零拒绝并报错。BNN/LSTM frozen profile的prepared_edges分别38,342,776/38,985,028，满足此域。测试覆盖最大合法begin=0xfffffffe/end=0xffffffff和高32位拒绝，检查ceil(end/8)无溢出。D核心请求/返回/FP32逐周期记录与B/C哈希一致。C的真实综合关键路径为pos[15][6]→slot_state[28]/CE，83级，WNS -13.726ns；据此D将4context×8slot就绪判定并行化，避免跨context串行选择链。D尚待独立OOC，不授予时序资格。

`front_offset_bounds_a`为保留的构建路径失败：复制Vivado生成的相对prj路径到较浅目录导致找不到source；在b中将源路径按原生成目录解析为绝对路径后通过。它是构建错误，不是架构负结果。MCP实现会话均忙时，D和bounds采用Vivado已生成的XSim脚本，保存脚本来源、命令、开始结束和返回码；未切换模拟器。


物理接口范围：group leaf的`ml`为相对edge beat地址，本地校准采用EDGE_BASE=0的一笔共享服务口。完整图的base-add、line&31条带选择、全局返回仲裁与header/meta/fork/qid控制均在leaf之外；原生C++对照依然按真实declared bases和physical ports计费。不能将该leaf OOC升级为这些未包含模块的时序/功能资格。


公平性仍有边界：最终RR的BNN/LSTM代表wave总lane利用率仅32.56%/32.21%；四个16-lane区段的均值分别约67.78/45.42/13.14/3.89%与67.53/44.58/12.58/4.15%。分配RR消除全程零发射lane，未消除请求/返回优先级导致的服务失衡。H和fork平均均接近128，E平均约74/256；总port发请求约7.12/32 requests/cycle。阻塞尝试与context-cycles重叠，不相加为wall time，也不以这些统计证明某一个唯一瓶颈。


局部C++队列的继承抽象：`request()`保持旧代码的有限64-entry/32-credit约束和每port每cycle一次物理issue，但允许同tick多个逻辑客户端入该port队列。这项假设在匹配对照中相同，未作为完整可综合多写FIFO资格。完整模型的`accepted_port`限制单port每cycle一次入队，leaf本身也只有一次请求通道；因此不能把F局部周期直接当成完整注册化请求仲裁的校准结果。


最新环境恢复状态：D于router报告完成后在libudev/FlexNet/WebTalk主机枚举中SIGABRT6（proxy退出134），不是用户/agent stop；front_ooc_d/terminal.json保留FAILED_ENV_WEBTALK_SIGABRT和hs_err。当前front_ooc_e从D精确synth checkpoint接续，进程级LD_PRELOAD既有systemlibudev，未修改RTL/约束/安装或全局设置；已保存input/opt/place/physopt checkpoint，等待实际route终态与最终报告。公开同类2022.1 report与当前stack匹配，2022.2恢复的最终有效性以E回执为准。本状态仍为checkpoint。
