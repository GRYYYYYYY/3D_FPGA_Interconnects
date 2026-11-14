# enum2 / K8 / 公平分配候选执行报告

基点为 `1e312d6e4ffc5ea96f25c0b97931ad028e710584`，候选分支为 `accel/lookahead-balanced-enum-commit-20261114`。本轮按 `CODEX_FPGA_ENUM_COMMIT_AFTER_1E312D6.md` 实施，没有用旧 enum5/K1 no-go 阻止新结构。

最终完整模型为 `model_native_d`，已修正输出导出、PUB退休、cost读取和地址布局并通过完整验证。前端与后端均已取得真实布线报告；前端setup失败，后端最后修正通过setup但接口hold失败，均未取得整体200MHz资格。本轮结论是：公平分配的局部收益较小，enum2、scratch 快路和真实 K8 的局部机制有效，但完整新条件模型仍慢于已有 GPU resident 基线。完整核时序、完整服务逐周期资格尚未获得，不能报告 FPGA 胜出。

## 实际结果与允许的结论

| 完整输入 | sample 数 | 新模型周期 | conditional_predicted_seconds @200MHz | 复用 GPU resident 秒 |
|---|---:|---:|---:|---:|
| BNN | 40 | 52,265,602 | 0.261328010 | 0.151799969444 |
| LSTM | 40 | 52,888,942 | 0.264444710 | 0.15949799988888888 |

两组完整输出均逐 sample 精确对冻结 ALT/native golden；拼接全 batch SHA256 分别为 `a8ca4003a3b015145635a3f776bb62a3aec1ec2121a1fbfc8712d2a2dc1c8c3f`、`6b2acd7718d880075d653b3b83f1fa3abb5161f6f346ed39c3aa1285160a95cf`。STRICT 的不等价边界不变。GPU、旧模型、完整真实地址画像和 CUDA 补档证据仅复用，未重跑。

最终D版的对应条件模型/GPU时间比分别约1.722与1.658，均未达目标；这不是经过校准的硬件速度比，也不证明所有FPGA实现必输。

这些是 **完整条件模型**，不是已合格的 `simulated_resident_seconds`：完整 top、header/metadata/目录/返回路由的物理映射和若干服务周期校准仍缺失；`fpga_seconds=null`、`board_measured=false`。本轮的完整模型性能门槛不满足，不能因弱必要界低于 GPU 就扩成“成功”。是否进入完整 top/OOC 由新证据决定，旧完整核负结果不替代本轮判断。

## 同资源 lane 分配消融

全部配对使用相同输入、H/E/M/beat 槽和物理端口资源；输出、实际 operand 候选、parent、row/edge/metadata 请求数守恒。17 个 native wave 和两个已有连续窗口作为输入。

- 原全局 FIRST_FREE/LANE_RR 以及接收带宽 8 的两组共 76 次；19 项原带宽 FIRST_FREE 精确复现旧 B 周期和逐 lane 发射数。
- 每个八 lane 组每周期最多一次 E 写入的受限全局派发共 38 次；另 38 次追加统计，不能计作新架构。
- 最终结构是 **八个独立八 lane 组**，每组 fork/H/M/ready 各 16，64 lane 各 E4、beat 槽 8；每组每周期最多一个非空 parent 的 E 分配，组内 LANE_RR 仅在成功分配后推进。零度 parent 不占 E，但 row/metadata 成本保留。最终 FIRST_FREE/RR 38 次配对通过。

| 最终独立组局部输入 | FIRST_FREE 周期 | LANE_RR 周期 | 观察 |
|---|---:|---:|---|
| BNN 2/38 | 118660 | 117729 | 改善 0.785% |
| LSTM 7/36 | 121155 | 120281 | 改善 0.721% |
| BNN 35/53 | 897 | 905 | 负例保留 |
| BNN 连续压力窗口 | 458 | 458 | 无收益 |

最终 RR 消除了完全未发射的 lane，但四个16-lane分区利用率仍明显偏斜：BNN约67.78/45.42/13.14/3.89%，LSTM约67.53/44.58/12.58/4.15%；固定请求/返回优先级仍有影响。平均物理口利用率不足以支持“持续带宽饱和”的断言，重试次数也不能唯一归因瓶颈。原始独立组JSON继承的旧全局mask布尔字段为false，不控制新组循环；实际每组最多一次分配由独立实现、configuration及绑定源规定，保留原始记录并在分析中解释。详细 lane 发射/空闲/等待/槽占用、端口与返回占用直方图及容量峰值在 `front_analysis_a/summary.json` 和原始每次结果中。这些局部模型有有效 POP 输入和理想 candidate sink；还保留旧局部模型同一物理口FIFO每拍可接受多个逻辑入队的抽象，虽总FIFO/credit和物理issue受限，也未实现该多写口。两组因果比较共享该条件，不能当完整 batch 时间。完整模型另有限制每口每拍一个逻辑入队。最终完整模型单独接入真实 POP、canonical、scratch、目录和输出路径。

前端leaf请求是相对edge beat的单一tagged通道，校准EDGE_BASE=0；物理base加法、line&31路由和完整返回仲裁不在leaf内。局部C++消融使用实际物理base与条带。前端 RTL 使用实际 `fp32_positive.sv::pair_lane`，输入边界是已完成 CSR row 读取的 parent。它验证 E 分配、有限 beat 槽、tag/generation 返回和实际 FP32；不包含 POP/fork/H/meta/reducer/epoch 屏障及全 64 lane 路由。独立逐周期回放覆盖两个 epoch 无 reset；微测试两模式使用不同确定性抖动相位，仅作功能/周期压力测试，公平性能结论取上述匹配 C++ 配对。

## 新后端及局部验证边界

`enum2_bank.sv` 保留 expand 单 RMW，finalize 用四级弹性状态、一个 raw 寄存器和容量 16 的 fragment FIFO。无背压枚举 launch II=2；launch 到外部 fragment 握手为 **7 拍**，不能把 II2 当两拍总延迟。已验证满波、背压、空波、单元素，以及连续波次。

`scratch_finalize.sv` 有一个 bitmap query、merge FIFO16、共用 commit FIFO16，没有额外免费 fast FIFO。无 spill 走快路；merge 仍只允许一笔在途读，expand 首 spill 写 ACK 后发布 ID。consumed bitmap 采用原子 OR 与同 word 转发，覆盖 A/A 和 A/B/A；残余扫描等待 resident/merge/commit/atomic 全部排空。ID 真容量 2048，2049 明确 HALT。外层 done 还等待 canonical、目录事件和物理接口排空。

`ec_pending_k8.sv` 每 subbank K=8，真实单 PV 读/写端口、每拍最多一个 APPLY、每事务最多四个预留目录事件槽。整 canonical word 锁贯穿读、可选写 ACK、PV 写入、**全部目录握手**和最后退休。队列入队不等于目录退休。generation/slot tag、同 word 不重叠、POP token 预留及陈旧 POP 都有实际验证。

`ec_tagged_port.sv` 是 DUT 内可综合共享接口，两个 canonical 和两个 scratch 客户端共享一笔 32B 物理口、32 tags/credits，具有有限请求/返回 FIFO、寄存边界、RR 和背压；不是只在 TB 的仲裁器。owner ID 参数化并检查地址条带。局部整链只投影一个 owner 的两个 subbank，不能独立授予完整 native wire-map 输出资格。

canonical 最终 F 用真实 14bit PV 地址、两 sample 实际初始化和高地址，1472 次冻结参考操作、1988 笔物理请求，覆盖 K8/事件槽/32 credit 饱和、乱序返回及 generation 回绕。RAM 推断修正前后的 17620 条接口/阶段记录逐字相同。最终 first-response 合同实测 16 拍。

旧/新局部整链使用相同实际物理端口及相同目录退休 adapter，覆盖 13 个原生投影和 3 个压力 fixture、每版本 19 个 wave，包括四个大 native wave。核对 canonical label、pending17、事件参数和最终状态，并检查 ACK/PV/事件排空。完整状态 hash 只是附加证据，不替代逐事务守恒检查。

固定延迟早期 sim_a/b 因 TB 半拍调度实际为 17 拍，已标记 superseded；不能将其当 80ns 主条件。最终 `fpga_enum_commit_integration_20261114_fixed/sim_c` 每版本75868笔响应的延迟直方图均为 `{16:75868}`，11309拍代表性物理端口回放精确一致；另有2048请求的饱和压力测试，四个客户端FIFO4、返回FIFO4及32credit同时到达容量，2741个乱序对，2905个非reset周期独立回放精确一致并最终排空。两次RAM推断修正均已包含。最后同周期changed-flag修正后的 `sim_d` 已再次通过，8份关键波形/事务/统计与 `sim_c` 逐字一致，具体绑定见 `cycle_equivalence_to_sim_c.json`。

| 原生 owner 投影 | 旧链周期 | 新链周期 | 局部加速 |
|---|---:|---:|---:|
| BNN19/32 | 201847 | 94408 | 2.138倍 |
| BNN2/38 | 175665 | 79107 | 2.221倍 |
| LSTM19/30 | 188854 | 81476 | 2.318倍 |
| LSTM7/36 | 175468 | 77586 | 2.262倍 |

大型投影的逐bank平均枚举输出间隔由32.70–35.53降为4.84–5.61拍；commit接收间隔由33.17–35.95降为6.02–7.22拍；**完整退休间隔**由33.17–35.95降为6.03–7.23拍。事务平均反馈延迟反而从30.93–33.47升为36.33–39.10拍：并发提高吞吐，不等于每笔事务更快。无背压单元II2与整链带背压平均间隔分别报告。每事务反馈/完整退休CSV及所有热点、小波次负例均保存。

## 局部时序终态与门槛

前端最终RTL的恢复运行 `front_ooc_e` 已完成实际布线并保存DCP：5ns下setup WNS **−1.036ns**、TNS −2864.653ns（8403个端点），hold **+0.043ns**，pulse **+1.968ns**。最差路径为 `pos_reg[29][7] → slot_state_reg[56][0]/R`，18级逻辑、6个CARRY8，数据延迟5.917ns，其中布线4.186ns（70.7%）。另外实际FP32至error路径仍有约−1.0ns违例。它是内部同钟路径，不能通过忽略外部接口或放宽false path解决。前端200MHz资格未获得。

前端实际布线资源为26,196LUT、8,653FF，其中3,008LUT作存储，BRAM/URAM/DSP为0；它只覆盖上述leaf。所有12类check_timing检查为0，包括未约束端点和缺失I/O delay；覆盖完整不等于setup通过。前端I/O min/max均为0.5ns，这一明确的OOC假设触发XDCH-2提示，不是板级接口已验证。TIMING-16保留真实setup失败；未使用waiver。后端恢复C的setup−0.413ns、hold−0.135ns，以及一次物理优化后的setup−0.298ns均保留。最后采用已证明等价的changed-flag写法，避免“min结果再做256bit equality”的组合链；73728个opcode/边界案例及完整F的17620条阶段记录一致，整链sim_d也与sim_c逐字相同，协议、容量和周期未变。

最终 `fpga_enum_commit_integration_20261114_ooc_d` 实际5ns布线：setup **+0.024ns**、TNS0，hold **−0.135ns**、THS−71.713ns（669个端点），pulse **+1.800ns**。最差setup路径为pending state到new_pvs RAM输入，13级逻辑/1个CARRY8，4.777ns，其中布线3.671ns。全部669条负hold路径经对象查询均为INPUT_INTERFACE，没有内部reg→reg负hold；全部674条RTSTAT相关net均为EXTERNAL_OUTPUT_ONLY，没有缺失内部消费者。仍保留警告和原0.8ns max/0.1ns min接口预算，不放宽输入delay、不加waiver；整体OOC仍是**timing fail**，不能把setup通过升级为整体200MHz资格。全部check_timing覆盖检查为0，零未约束端点也不能替代hold通过。

## 完整有限模型与预算

固定 64 subbanks、64 lanes、32 个物理 32B 端口、每端口共享 32 credit、80ns/5ns。模型有有限 H/E/M、fork、ready、beat 槽、candidate 路由 FIFO、4way/1024sets 累加器、enum2、scratch merge/commit、K8、banked 目录和最终 output ACK。没有旧 POP/candidate trace 作为完整性能路径，没有无界 map 累加器，没有继承旧 fragment 并发或 spill 数。

每 sample 显式初始化并完成所有输出 ACK；最终输出由8个RAM bank每拍最多读8个pair，形成最多两个32B beat，经容量16的打包FIFO与两拍寄存边界送出。可观察输出取自实际写请求建立且已ACK的外部输出backing。每sample输出区独立；10个cost项共3个32B读取，cost区位于全部sample输出区之后。硬件周期按 sample 顺序求和。12 个 CPU worker 只并行模拟相互独立 sample，wave 保持依赖，CPU 并行度不计作硬件加速。初始化含 sample_clear、PV16384、output4096、目录/free pool8192、累加器1024及 bitmap256 拍，独立 RAM 初始化允许重叠；所有 canonical 初始化写及 ACK 计入。每 wave 清空全部 spilled/consumed 位，明确支付256拍。

最终D版小图 d3 八 sample、d4 十二 sample，各正常与抖动共40次通过；完整 BNN/LSTM 共80次通过。独立交付复核检查源码和二进制绑定、所有输出哈希、实际流量、容量和排空守恒。全 batch 的 parents/N/U/V 均与完整旧画像吻合，spill 则由本轮实际到达顺序重新产生：BNN 9,231,456，LSTM 9,426,716；final scratch reads 分别 6,986,159 / 7,142,555。spill ID 单 bank 峰值880/834，目录每 bank 峰值3495/3531，均在2048/8192容量内。

POP+expand 是最大墙钟阶段：BNN39,827,941拍（199.140ms），LSTM40,289,728拍（201.449ms）；finalize含bitmap清空分别11,025,461/11,164,694拍（55.127/55.823ms）。它把POP、fork、图访问、FP32、路由/set冲突和expand spill综合在一起，不等于已经定位单一因果模块。若仅把本次调度的整个finalize阶段扣掉，仍需206.201/208.621ms，高于GPU；这是阶段诊断，不是另一架构的必要下界。现有新spill/队列峰值及重试次数不足以证明单在途scratch是决定性依赖，因此未启动2/4并发参数扫描。

此前A（导出/PUB问题）、B（仅导出修正的小图）、C（cost读取与布局待修正）全部保留并明确被D替代；没有把中间完整跑完等同最终正确性能结果。

完整模型与 RTL 共享 `enum_clock`，两组64元素及单元素的 scan/fragment 共258条事件逐周期一致。其余服务的全局优先级、目录 head/tail 转发、top 返回路由等尚未整链精确校准；局部 canonical/port 的回放不能自动转授完整模型资格。最终配置为 `model/configuration_final.json`；冻结早期 `architecture.json` 为实施草案，非运行输入。

联合预算使用实际 canonical 端口热点和新 r/K 重新计算：r2/K8 的弱必要界为 BNN **133.705784609ms**、LSTM **136.088186875ms**。旧 r5/K1、r2/K1、r2/K4、r1/K8 分列，保留其假设。该界省略真实前端、scratch、事件/路由和尾部开销，仅说明新结构不能被旧界否决，绝不是预测结果。

新逻辑账本 `model_logical_ledger_d.json` 列出35类固定存储，明确FP32、全局路由、目录RAM端口/打包/布局等未知物理开销；逻辑bit总数不是器件资源占用。新资源账本以最终实际 RAM 推断和逻辑容量为依据，不搬用旧864URAM/1888BRAM。最后D实际布线两个subbank连共享接口为16024LUT（5264作存储）、14853FF、12RAMB36+4RAMB18、16URAM、0DSP；单纯32倍记账为512768LUT、475296FF、448BRAM36等效及512URAM，不能当完整核资源或实际布局结果。初次RAM修正后的OOCb综合16410LUT记录也保留，最终采用D实际报告。PV 每 bank 16384×68 实测4URAM；resident payload 及 occupied-list 等需按本轮综合层次报告计入。目录、完整返回路由及全部64 FP32的集成还没有完整物理账本闭合，因此不宣布全核可容纳或频率合格。

## 保留的修复与失败

本轮保留所有初次编译/TB 路径、ACK 竞态、模型 ready 唤醒、consumed 清空、输出导出带宽、PUB 持有与复用以及cost加载/地址布局等失败及修正；这些不是架构 no-go。初版 PV 多个语法写口导致 LUTRAM，改为单写口模板后每 bank 4URAM，周期保持。occupied-list 改为明确同步 RAM 模板，独立 probe 实测1RAMB36+1RAMB18，全部输入/输出 pin trace 不变。

前端 A/B/C 的长选择链、统计计数器及 offset/ready 路径负结果保留；不能用 false path 隐藏。32bit edge offset 优化只允许经检查的地址域，CSR 存储仍64bit，越界显式 error，真实图 prepared edges 小于2^32。后端OOCb和前端OOCd在router完成后发生Vivado2022.2进程异常退出（signal6，`mremap_chunk(): invalid pointer`）；栈指向Webtalk/主机信息收集的libudev/realloc，未保存route DCP和正式终态时序报告，必须归为工具失败而非RTL时序结论，并从综合checkpoint恢复。恢复仅对新进程设置 `LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1`；既有Webtalk user/install设置本来关闭，未更改全局配置或vendor二进制。被新实现替代的运行若受控结束，以 CANCELLED_SUPERSEDED 标注，不能冒充正常完成或工具失败。

## 复现与证据入口

代码：`accel/lookahead/fpga_enum_commit/`。公共原始结果：`results/fpga_enum_commit_20261114/`，单元/整链原始运行位于同级 `fpga_enum_commit_canonical_*`、`fpga_enum_commit_enum_*`、`fpga_enum_commit_integration_*`。最终紧凑归档为公共目录下 `evidence_snapshot/manifest.json`，每项记录原始路径、原始字节数、SHA256和归档位置；不声称归档包含完整 Vivado 工程或 DCP。

运行完整模型：`python3 accel/lookahead/fpga_enum_commit/model/run.py small`，随后 `full`；脚本复用已通过的 sample receipt，不覆盖原失败尝试；交付版增加整个OUT与每sample的flock和PID/argv/启动身份检查，遇到在途任务拒绝重复提交。10项轻量守护测试通过，未为此重跑完整模型，D的冻结二进制和核心源码未变。首次运行需要 binding 指明的冻结 workload/golden；归档引用旧证据，不重复复制大图。

独立校验：`python3 accel/lookahead/fpga_enum_commit/delivery/verify_model.py`、`front/verify_front.py`、`delivery/verify_front.py`；局部 Tcl、输入生成器与 trace 回放脚本随代码交付。Vivado 使用2022.2、xcu280-fsvh2892-2L-e，终态报告绑定实际源、XDC、工具及命令。

归档验证：`python3 accel/lookahead/fpga_enum_commit/delivery/archive.py evidence_snapshot --verify`。历史 manifest/read-only 基线、main/原稿/STRICT/旧 golden 不改；最终候选正常 push 后核对远端 SHA。最终提交与进程终态以交付 receipt 为准。

本轮实际实验均已终止并有真实receipt，`delivery_terminal.json` 核对本候选无在途Vivado/XSim/模型进程，17个受保护本地分支引用未变。未启动完整top：新完整条件模型的性能门槛与局部整体时序门槛均未满足。旧no-go原样保留，结论依据本轮实现与测量，不把它推广成所有FPGA结构的必然失败。
