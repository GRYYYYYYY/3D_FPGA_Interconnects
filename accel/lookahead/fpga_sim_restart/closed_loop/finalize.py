import pathlib,json,re,hashlib,csv
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z';c=r/'closed_loop'
cal=json.load(open(c/'calibration.json'));assert cal['total_cycle_gate'],'complete 64-owner holdout calibration required'
large={p.stem:json.load(open(p)) for p in (c/'large').glob('*.json') if p.name!='execution_plan.json' and not p.name.endswith('.receipt.json')};assert len(large)==12 and all(x['output_equal'] and x['jobs']==40 and x['front_backpressure']==0 for x in large.values())
qor=json.load(open(c/'native_summary.json'));assert all(x['map_equal'] and x['full_check_passed'] for x in qor)
def timing(p):
 s=p.read_text();m=re.search(r'WNS\(ns\).*?\n\s*[- ]+\n\s*([-\d.]+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)',s,re.S)
 assert m,p
 return {'wns_ns':float(m[1]),'tns_ns':float(m[2]),'setup_failing_endpoints':int(m[3]),'whs_ns':float(m[5]),'all_constraints_met':'Timing constraints are met.' in s}
ooc=c/'ooc_64_fixed';t200=timing(ooc/'timing.rpt');t125=timing(ooc/'timing_125MHz.rpt')
s=(ooc/'routed_utilization.rpt').read_text();match=re.search(r'\| graph_top\s*\|.*?\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)',s);assert match
res=dict(zip(['luts','logic_luts','lutram','ffs','ramb36','ramb18','uram','dsp'],map(int,match.groups())))
gpu=(c/'gpu_v2/completed.json').exists()
status={'candidate':'ALT_LINE_OWNER_REDUCE_V1','source_base':'7e63b917f37273f80c03327e024d86b797ee221b','branch':'accel/lookahead-fpga-sim-restart-20261112','overall_task_complete':False,'first_artifact_delivery_complete':True,'complete_small_batch_RTL':True,'fpga_method_rtl_verified':{'value':True,'scope':'whole d3/d4 batches, 64-owner complete scan-controller RTL; shared candidate bus, serial graph front end'},'fpga_full_kernel_ooc':{'resources':res,'timing_200MHz':t200,'timing_125MHz':t125,'complete_top_routed':True,'interface':'32 bounded ready/valid transaction channels; no AXI4/shell/board claim'},'architecture_model_rtl_calibrated':{'value':cal['total_cycle_gate'],'scope':'F1 complete 64-owner small batches, total and phase comparisons; saturated owner service separately tested','F0_complete_RTL_calibrated':False},'complete_BNN_LSTM_architecture_simulation':True,'large_complete_runs':12,'jobs_each':40,'large_performance_label':'projected_at_assumed_200MHz','resident_batch_superiority_under_declared_model':False,'board_measured':False,'native_bridge_checked_this_round':True,'final_wire_maps_exact':True,'new_GPU_cohort_complete':gpu,'pending':['new basic CUDA and LSTM warm resident cohort: Inspire authentication expired; prepared worker not run' if not gpu else '','original VPR and best native STRICT CPU matched V2 interval: not_evaluated_same_scope','full-kernel timing closure' if not (t200['all_constraints_met'] or t125['all_constraints_met']) else '']}
status['pending']=[x for x in status['pending'] if x];(r/'status.json').write_text(json.dumps(status,indent=2)+'\n');(c/'status.json').write_text(json.dumps(status,indent=2)+'\n')
base=json.load(open(c/'baselines/summary.json'));software=[x for x in base if x['case'] in ['bnn_export','lstm_s2']]
# Build tables from values; do not report host simulation runtime as FPGA runtime.
table=[f"| {name} | {j['cycles']:,} | {j['cycles']/2e8:,.3f} | {100*j['hits']/j['candidates']:.3f}% | {sum(x['reads32B']+x['writes32B'] for x in j['traffic'].values())*32/1e12:.6f} | exact |" for name,j in sorted(large.items())]
small=[f"| {x['case']} | {x['rtl_cycles']:,} | {x['model_cycles']:,} | {100*x['relative_total_error']:.4f}% | exact |" for x in cal['rows']]
sw=[f"| {x['case']} | {x['backend']} | {x['mean_s']:.9f} ± {x['sample_sd_s']:.9f} | {x['cohort']} |" for x in software]
qr=[f"| {x['case']} | exact | {x['critical_path_ns']:.4f} | {x['wirelength']:,} | FULL pass |" for x in qor]
report=f'''# 无实板 FPGA 方法重启：实际交付与负结果

本轮完成了单 owner RTL、8/64-owner 完整小图闭环、对应 F1 模型校准、BNN/LSTM 各完整 40 个 sample 的 12 项有限架构模拟，以及实际 native bridge/final-map 回接。**当前实现没有性能优势；整轮请求仍有未完成项**，见末节。没有把板卡、XRT、XPFM 或 shell 缺失用作实验停止条件。

基点 `7e63b917f37273f80c03327e024d86b797ee221b`；独立 worktree `{root}`；分支 `{status['branch']}`。首项交付提交 `857bfce454a86947965f7dd706f643bc376f6cf9` 已单独推送。main、原稿、STRICT、旧 golden 和历史证据未修改。配置依据用户 YAML，模板、执行合同、输入路径/SHA 和全部正负尝试均保留。

## 实现与完整工作范围

固定 Q=1；64 个 `pair_lane` 实例和 64 个实际 owner；每 owner 为 4-way×32 sets×32B、32 MSHR、16 dirty slots、请求/响应 FIFO 各64。owner/set 地址公式正确，同行合并、全 pair FP32 最小值、脏写确认前 RAW 阻塞、全局 fence 均实体化。FP32 正数/+0 RN 加法另通过 100,006 对 XSim 独立核对。运行时输入从真实 CSR/node/cost/jobs/cell 数据生成；golden 只供输出检查，未提供硬件前沿。

**图前端每次只有一个 blocking 访存请求**，轮转给 lane，候选总线每周期最多一次传输。目录采用显式 `pending[N]` 扫描与 `closed[N]` 状态，4096 key 范围和524288 live member 上限；模板提出的 chunk pool 未采用。初始化、扫描、图访存、commit、closure、输出和 drain 全部计入。这是一个完整但低并行度的实现，不声称持续64边/周期，也不把其结果推论为所有 owner-reduce 架构都慢。相关实现选择与限制作出了公开记录。

32 个共享物理服务通道承担所有数组流量，64 owner 不被当成64个独立端口。cache/queue/tag 状态均为实际 RTL。全核接口是带 ID/确认/背压的32B事务协议，非完整平台 AXI4/shell；外存参数是明确的 assumed 情景，`board_measured=false`。

## RTL、校准与保留的失败

首个单元交付包括完整有限存储 TB、五项功能回归、五种非法数拒绝、所有内存差分和周期日志；最初空闲 way 优先级不一致及修复前结果见首项证据。没有用单元周期冒充完整图周期。

完整 d3：8 jobs、42 waves；完整 d4：12 jobs、106 waves。8-owner XSim 与 Verilator 在相同情景的输出及周期一致；64-owner 最终原型使用 Verilator。d4 未用于模型调节；冻结签名和阶段误差保留。

| 校准 | RTL cycles | 模型 cycles | 总误差 | 全输出、读写事务 |
|---|---:|---:|---:|---|
{chr(10).join(small)}

模型直接执行 labels/proposals/pending 的闭环，不读预先的 golden frontier。每数组的读写、通道预算、RAW、write ack、outstanding、dirty slot 和 fence 均计时。无竞争阻塞扫描仅在条件满足时精确聚合其连续事务；没有免费复制/清空 N。覆盖的大图调度每 owner 最大一个在途 miss、模型 front backpressure=0；该稀疏请求域之外的饱和负载只具备单 owner 校准。F0 是同前端/存储的显式行 RMW 模型消融，**没有独立完整 F0 RTL 校准**。模型 fence 仲裁是有报告误差的事件近似。

## 完整候选 OOC

Vivado2022.2，`xcu280-fsvh2892-2L-e`。最终64-owner顶层资源：`{res}`。全部内部图控制、算术、owner 与互连已纳入此 OOC。没有沿用旧核或 tile 频率。20% shell 预留仅为假设，不代表已验证配额。

| 同一最终 routed top | setup WNS ns | hold WHS ns | 全约束通过 |
|---|---:|---:|---|
| 200 MHz | {t200['wns_ns']} | {t200['whs_ns']} | {t200['all_constraints_met']} |
| 125 MHz 同 route 回退检查 | {t125['wns_ns']} | {t125['whs_ns']} | {t125['all_constraints_met']} |

报告包含 setup/hold、unconstrained、DRC、route status 和约束；未添加 false paths 掩盖依赖。早期8-owner互连资源偏大，随后限制为实际 owner/channel 映射。被替代的64-owner全连接仲裁综合尝试明确中止，保留原因和日志，未写成工具/资源失败。先前 libudev/WebTalk 路由退出问题采用进程级 preload 解决，初次失败及复跑都保留。

## 全量架构模型与敏感性

下表每行均为真实40个 sample，完整原始 ALT 输出逐字一致。周期可复现；秒数是 **cycles/假设200MHz，projected**，不是板测、不是 CPU 模型执行时间，也不是已通过全核时序的实测服务时间。

| 情景 | 完整 cycles | projected s @200MHz | F1命中率 | 全数组读写 TB | 输出 |
|---|---:|---:|---:|---:|---|
{chr(10).join(table)}

中央 read/write latency300ns；150/600ns为单因素敏感性。请求的64/128/192GB/s经整数周期 link gap 得到有效51.2/102.4/102.4GB/s，均低于32×32B×200MHz接口上限。128/192两项在本模型中重合，未伪造带宽收益。全部数组共享读写链路，等待已在周期中，没有再次叠加 bytes/bandwidth。

BNN 中央 F1命中率约85.45%，完整周期只比F0少约0.015%。全局按节点扫描的顺序与先前原目录软件事务重放顺序不同，因此命中率也不同；没有继承旧46%或更早20.87%数据。主要瓶颈是串行图读取和全图 pending/commit/closure 扫描。当前实现未达到 FPGA 优势，负结果保留。

## RESIDENT_COMPLETE_BATCH_V2 软件边界

起止为各平台输入可消费到全部真实 sample 输出提交；排除外部转换、首次H2D/最终D2H；内部访存、初始化、波次控制、冲突、提交和排空计入。新 ALT CPU 为3独立进程×预热1次+测量3次，全部原始值保存。下列误差为9个实际 warm 值的 sample SD；另存进程身份和进程均值间SD。模型确定周期没有虚构SD。

| 输入 | 软件参考 | resident mean ± sample SD，s | cohort |
|---|---|---:|---|
{chr(10).join(sw)}

历史compact CUDA/STRICT wrapper只读取真实`resident_s`字段，并核查源码计时边界。旧基础CUDA6的E1和device timeline都包含最终D2H，明确排除于V2比值；旧0.309712337s未改名。原始ALT CPU本轮host与历史GPU host不同，不进行跨cohort配对统计。STRICT wrapper为额外参考，不等同于已补齐最佳 native STRICT/VPR 同范围计时。完整历史原始数据仍保存。

## native 回接与 QoR

使用模型实际输出、原始 ALT native输入捕获和现有 import bridge。没有改写旧golden，也没有把ALT差异声称为STRICT等价。每次回接都完整核对40个sample，完成native FULL检查/STA，最终wire map SHA与既有ALT资格完全相同。回接为离线正确性实验，非FPGA live backend计时。

| 输入 | 最终 wire map | CPD ns | wirelength | 检查 |
|---|---|---:|---:|---|
{chr(10).join(qr)}

## 未完成项与证据范围

- 新基础 CUDA 及 LSTM warm GPU cohort：启智 CLI 实际返回 `invalid_grant/session expired`，未提交作业；timer-only源码变体和执行脚本已准备，未冒充已编译/运行。
- 原 VPR 多线程与最佳 native STRICT CPU 的匹配 V2核心区间仍为 `not_evaluated_same_scope`，不拿其E2与模型相除。
- 当前全核的时序结论见上表；若未闭合，频率保持假设，不能提升为物理支持的 FPGA服务时间。图前端仍是主要性能限制。

可复现代码：[closed_loop](../accel/lookahead/fpga_sim_restart/closed_loop/README.md)。完整差分、原始计时、周期/事务、OOC、native日志及全输出见 `results/{r.name}/evidence_snapshot/closed_loop`；大DCP仅保留本机路径及SHA，未伪称已经上传Git。所有尝试与未完成项都有机器可读状态。

![完整batch，条件性FPGA模型](../results/{r.name}/evidence_snapshot/closed_loop/figures/resident_complete_batch.png)

![外存敏感性](../results/{r.name}/evidence_snapshot/closed_loop/figures/memory_sensitivity.png)

![周期分解](../results/{r.name}/evidence_snapshot/closed_loop/figures/cycle_breakdown.png)
'''
(root/'docs/lookahead_fpga_sim_restart.md').write_text(report)
# Final status does not change the supplied template or invented supported clocks.
p=root/'accel/lookahead/fpga_sim_restart/config/experiment_spec.simulation_restart.yaml';s=p.read_text().replace('status: executing_complete_closed_loop_validation','status: delivered_with_negative_performance_and_GPU_timing_auth_block').replace('routed_component_coverage: one_owner_service_only','routed_component_coverage: full_64_owner_graph_top_with_serial_graph_front_end');p.write_text(s)
print(json.dumps(status,indent=2))
