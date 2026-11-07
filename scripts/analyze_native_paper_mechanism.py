"""Evidence synthesis, preserving diagnostic/formal and claim boundaries."""
import json,statistics
from pathlib import Path
from prepare import sha256,write_json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105'
def bind(p):return dict(path=str(p.resolve()),sha256=sha256(p))
result={'status':'completed','diagnostic_only':True,'cases':{},'sources':{},'limitations':['No direct flat parallel_for native control exists. Current pipeline itself flattens jobs; no novel scheduler claim.','Group width upper bounds are structural, not measured CPU utilization.','Historical diagnostics do not constitute new formal performance samples.']}
for c in ['gemm','elliptic']:
 p=ROOT/f'results/native_cpu_slices_20261101/diagnostic/{c}/{c}_diagnostic_w4_r0_legacy_rebuild/lookahead_profile.jsonl'
 rows=[json.loads(l) for l in p.read_text().splitlines()];n=[r['samples'] for r in rows];wall=sum(r['wall_ns'] for r in rows)/1e9
 result['cases'][c]=dict(source=bind(p),groups=len(rows),samples=sum(n),samples_per_group=n,maximum_parallel_samples_per_group=max(n),worker_capacity_upper_bound={str(p):min(p,max(n))/p for p in [1,2,4,8,16]},group_wall_seconds=wall,merge_wall_seconds=sum(r['merge_ns'] for r in rows)/1e9,thread_accumulated_search_seconds=sum(r['search_ns'] for r in rows)/1e9)
for f in ['docs/native_lookahead_novelty_analysis.md','docs/native_cpu_slices.md','results/native_cpu_slices_20261101/report.md','results/native_cpu_slices_20261101/diagnostic_report.md','vendor/vtr_cpu_slices/vpr/src/route/router_lookahead/router_lookahead_map_utils.cpp','vendor/vtr_cpu_slices/vpr/src/route/router_lookahead/router_lookahead_map.cpp']:
 result['sources'][f]=bind(ROOT/f)
write_json(OUT/'mechanism.json',result)
text='''# 方法与消融证据整合

本轮以冻结源码和既有原生诊断为依据，不增加新的算法性能主张。

贡献候选：保持原生 map lookahead 采样、严格比较及查询语义，通过采样任务分解、线程私有搜索状态、跨组调度和原序归并，提高原生多核构建效率。三维 RR 图是验证场景；不是新寻路算法或新 pipeline 原语。

## 依赖与正确性

每个 flood 使用原生起点、堆和扩展顺序，工作区不跨工作线程共享。不同样本结果独立。每组按原始样本顺序归并，保留相等延迟时最早 congestion 胜者；不能随意改为完成顺序归并。插值依赖固定 (from_layer,to_layer,channel,segment) 切片内 x/y 顺序，不是所有切片的全局依赖。未采样层默认值必须补齐。

wire map 字节相同是已验证边界，不扩大为派生 src/opin 所有状态或最终路由确定性。理论语义、合成夹具、原生 map、合法性与独立 STA 分层报告。

## 机制解释与仍缺的对照

GEMM 和 elliptic 的既有逐组诊断都为10组、每组4个样本，总计40次 flood。组内实现一次只开放一组，因此**样本搜索部分**最多同时运行4个任务；即使分配8/16个线程，该部分可用并行宽度上界仍分别为50%/25%。这不是全进程CPU利用率测量，也不包含 src/opin 等其他阶段。

现有 pipeline 源码已把各组样本展开为全局 jobs 列表，由 oneTBB 的有序生产、并行搜索、有序归并执行；它本身就是一种全局任务展开。高核数收益可以由解除组边界的并行宽度限制解释，但不能据此主张发明新的调度算法。还没有“全部样本 parallel_for + 最后原序归并”的原生对照；它的全样本表保留与 pipeline 有限在途表还会同时改变内存成本。若论文主张 pipeline 比所有直接展开策略更优，必须补该对照；当前不作此主张。

## 已有消融如何使用

|对照|能隔离的因素|边界|
|同修复ELF串行 → 组内|样本并行开关|同CPU预算；保留状态修复|
|同ELF组内 → pipeline|现有跨组执行整体增量|包括工作区跨组复用与归并时序，不逐项归因|
|slice → compact|同二进制的存储表示|不能把数组字节变化等同进程RSS变化|
|compact → bounded|有界组批、复用、切片提交组合|不是各机制的独立消融|
|pipeline → bounded|新有界实现的整体增量|此前未通过选型门槛，保留负例|
|重建 → 双方共同缓存|移除wire构建后的行为|缓存仍重算src/opin；不是严格全因果证明|

既有全局 pipeline 预分配 G 组结果，另有至多2P在途样本和线程工作区。token 有限不等于整体 RSS 硬上限。当前没有可据以宣称新 bounded 稳定胜出的结果。

第1项证据整理完成，但“更强调度算法新颖性”仍未建立。后续实验的作用是检验范围和机制，不能用更多重复替代方法差异。
'''
(OUT/'method_and_ablation.md').write_text(text)
print(json.dumps(result['cases'],ensure_ascii=False))
