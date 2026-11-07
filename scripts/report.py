#!/usr/bin/env python3
"""Generate the concise Chinese research status from retained measurements."""
import json
import statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    matrix=json.loads((ROOT/'results/ex5p_matrix/summary.json').read_text())
    hardware=json.loads((ROOT/'results/hardware/summary.json').read_text())
    native=json.loads((ROOT/'results/vpr_validation/validation.json').read_text())
    portal=json.loads((ROOT/'results/vpr_validation_portal/validation.json').read_text())
    rows=[]
    for variant,metrics in matrix['summary'].items():
        rows.append(f"| {variant} | {metrics['successes']}/{metrics['runs']} | {metrics['median_routing_seconds']:.3f} | {metrics['median_process_seconds']:.3f} | {metrics['all_audited']} |")
    speeds=', '.join(f"{r['process_speedup']:.3f}×" for r in matrix['worker_comparison'])
    resources=hardware['resources']
    gpu_section=''
    pointer=ROOT/'results/gpu_latest.json'
    if pointer.exists():
        latest=json.loads(pointer.read_text())
        gpu=json.loads((ROOT/latest['run']/'matrix/summary.json').read_text())
        full=json.loads((ROOT/latest['host_validation']/'summary.json').read_text())
        gpu_rows=[]
        for variant,metrics in gpu['summary'].items():
            gpu_rows.append(f"| {variant} | {metrics['successes']}/{metrics['runs']} | {metrics['median_routing_seconds']:.3f} | {metrics['median_process_seconds']:.3f} |")
        speed={name:statistics.median(r['process_speedup'] for r in gpu['cuda_comparison'] if r['baseline']==name)
               for name in ('batch_serial','parallel','cuda_dense')}
        gpu_section=f'''## H100 活跃前沿优化：2026-10-25

任务 `{latest['job_id']}`，H100 80GB、CUDA 12.8，三轮轮换顺序配对测量。新旧 CUDA 使用相同整数代价；新版本增加去重活跃前沿、树内增量多源距离复用、设备端代价计算和仅回传目标路径。

| 后端 | 成功/运行 | 路由中位数（秒） | 完整进程中位数（秒） |
|---|---:|---:|---:|
{chr(10).join(gpu_rows)}

逐轮完整进程加速比的中位数：相对旧 CUDA **{speed['cuda_dense']:.2f}×**，相对四线程 CPU **{speed['parallel']:.2f}×**，相对单线程 CPU **{speed['batch_serial']:.2f}×**。进程耗时包含初始化、图加载、传输、路由和结果输出，不含独立审计与 VPR 回验；只有一个电路、三次重复，不能外推到其他规模。

12/12 次布线成功，所有路径指纹一致。GPU 侧完成 120 组随机最短路以及 18,600 次增量多源路径 oracle，对汇聚竞争、拥塞快照切换、64 位距离和候选回退进行验证。CPU 侧 FULL/STA 完成：**{full['vpr_full_check_passed']}**；全部结果的 CPD=7.80663 ns、VPR 总线长=21904，优化未新增质量退化，但相对原 VPR 仍分别增加 39.1% 和 11.4%。新 GPU 路由约 1.54 秒，仍高于原 VPR 留存的 0.53 秒，不能声称已经加速原 VPR。

缺库修复采用 GPU/CPU 分阶段验证：GPU 状态 `gpu_passed_pending_vpr`，结束后由 CPU 主机验证哈希并执行冻结 VPR。最终闭环结果独立保存在 host_vpr，原始 GPU 记录不被改写。首版作业因缺少 libtcl8.6.so 而失败的记录继续保留。

- [三轮配对结果](../{latest['run']}/matrix/summary.json)
- [CPU FULL/STA 汇总](../{latest['host_validation']}/summary.json)
- [GPU 执行及源码哈希](../{latest['run']}/validation.json)

'''
    text=f'''# 首版实现与实测结果

本报告由 `python3 scripts/report.py` 从本目录保留的 JSON 结果生成。CPU/HLS 初测日期：2026-10-23；H100 优化测量日期：2026-10-25。

## 交付范围

已实现原生有向 RRG 上的多终端布线、OpenMP 批次搜索、共享垂直节点容量、候选回退、协商重布线、冲突修复、独立审计、VPR trace 导出及 FULL/STA 回验；另外提供可选 CUDA 搜索源码与 HLS 候选代价内核。

CUDA 已在启智 H100 编译并实测，详见后文。FPGA 无上板实测，也尚无 XRT 主机驱动。现有结果不证明优于原始 VPR 或复现 H3D/InstantGR/RouterAcc 论文。

## 正确性验证

- CTest：布线不变量、120 组随机图与独立 Bellman–Ford 比较、整数代价边界与饱和测试。
- Python：稀疏原始 ID、XML 多重边、不可支持开关拒绝、断路/非法边/重复占用/遗漏 Net/伪造成功等错误注入。
- 真实图：264,994 节点、2,366,014 条有向边、6,658 个 CHANZ；完整 679 个 Net，其中 460 个跨层。采用人工平衡 CLB 层分配的固定布局。
- 三种变体各执行两轮，6/6 成功，独立审计全部连通、overflow=0。
- `batch_serial` 与 `parallel` 两轮均逐边输出一致；线程数变化没有改变路径结果。
- 原生 VPR 提交 `0b912334fdd83bb754b302146ac0d1ec9edc9a0e` 的 FULL 检查：parallel={native['vpr_full_check']}，portal={portal['vpr_full_check']}；未运行 VPR 重新布线。

## CPU 初步测量

| 变体 | 成功/运行 | 路由时间中位数（秒） | 完整进程中位数（秒） | 全部通过独立审计 |
|---|---:|---:|---:|---|
{chr(10).join(rows)}

同批次策略下，单线程/四线程的两次完整进程耗时比分别为 {speeds}。进程时间包含图加载、后端初始化、路由与结果写出，不含独立审计。部分测量期间并发运行了 HLS/XSim 验证，共享服务器其他负载也不受控；只有两轮，是探索性数据，不能外推为稳定加速。portal 同时打开候选和调度，不能将差异单独归因于其中一个机制。

原始 VPR 留存基线 CPD=5.61388 ns；本原型 parallel 的 VPR STA CPD={native['critical_path_ns']} ns，portal={portal['critical_path_ns']} ns。当前单位代价目标缺少 RC/时序关键度，质量明显弱于该基线。研究目标是在允许小幅质量退化的条件下获得端到端加速，不要求 CPU 算法先全面优于 VPR。当前候选剪枝在这个样本上进一步损害时序；原 VPR 留存路由约 0.53 秒，尚未证明加速原 VPR。

{gpu_section}## HLS 实测状态

- Vitis HLS 2022.2，U280 `xcu280-fsvh2892-2L-e`，目标周期 {hardware['clock_target_ns']} ns。
- C 仿真：3,401 条边界/随机向量、重复两轮；另有 4,096 条真实 RRG 属性配合合成拥塞状态的 C 模型回放。
- 综合资源估计：LUT={resources['LUT']}，FF={resources['FF']}，DSP={resources['DSP']}，BRAM_18K={resources['BRAM_18K']}，URAM={resources['URAM']}。
- 综合估计周期 {hardware['estimated_clock_ns']} ns；不是布局布线后的时钟，也不是板卡频率。
- 计算循环 II=1、写回 II=1、读取 II=2。读取是当前流水线吞吐限制，不能把计算 II=1 当作整个内核每周期一条候选。
- 原生 `cosim_design` 报告通过：**{hardware['native_cosim_passed']}**。
- 实际 RTL 输出与 C 参考逐字节相同：**{hardware['rtl_output_matches_c']}**；独立执行生成的 C post-check 返回码：**{hardware['postcheck_returncode']}**。

原生联合仿真驱动若报告失败，仍保留这一失败；输出一致和 post-check 通过是独立证据，不能把原报告改写成 PASS。原始日志和综合/联合仿真报告保存在 `results/hardware/`，没有将仿真时间作为硬件加速比。

## 开发中发现的问题

早期并行版本硬容量修复失败后保留旧占用快照，导致 6 个 Net 反复竞争 OPIN/通道，留下 7 个 overflow。修改为实时协商代价重搜后，完整实验通过。旧失败保留在 `results/ex5p_balanced/cpu_parallel.json`，不属于最终六次矩阵。

HLS testbench 原先只分配 count 大小，而联合仿真 AXI 接口按 depth=4096 序列化；已分配完整缓冲区并检查未使用区域。曾逐项检查显式 main 返回值、二进制/文本向量、零长度调用与显式 argv；原生驱动状态以最终报告为准。

## 证据入口与下一步

- [配对实验 JSON](../results/ex5p_matrix/summary.json)
- [parallel 的原生 VPR 检查与 STA](../results/vpr_validation/validation.json)
- [portal 的原生 VPR 检查与 STA](../results/vpr_validation_portal/validation.json)
- [HLS 汇总](../results/hardware/summary.json)
- [设计与接口](design.md)

优先接入时序驱动代价并保持 FULL 检查闭环，缩小相对原 VPR 的质量差距。GPU 后续减少同步和初始化开销，扩展架构/电路与配对种子；HLS 继续图存储和主机接口的平台集成。
'''
    (ROOT/'docs/results.md').write_text(text)
    print(ROOT/'docs/results.md')


if __name__=='__main__':main()
