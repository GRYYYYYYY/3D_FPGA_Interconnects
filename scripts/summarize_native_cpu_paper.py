"""Write the terminal experiment report without selecting only winning cases."""
import argparse
import json
import math
from pathlib import Path

from prepare import write_json


def number(value, digits=3):
    return f'{value:.{digits}f}' if value is not None else '—'


def center(item):
    return item['median'] if item else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    args = p.parse_args()
    root = args.root.resolve()
    names = ['analysis', 'architecture_analysis', 'tasks_analysis', 'tasks_extension_analysis',
             'clstm_quality_analysis', 'multiqueue_analysis', 'tasks_attribution_analysis']
    data = {name: json.loads((root / (name + '.json')).read_text()) for name in names}
    assert all(x['status'] == 'completed' for x in data.values())
    audit = json.loads((root / 'evidence_verification.json').read_text())
    assert audit['status'] == 'passed'
    base = data['analysis']
    pipeline = data['tasks_analysis']['contrast_summaries'] + data['tasks_extension_analysis']['contrast_summaries']
    extra4 = [x for x in pipeline if x['contrast'] == 'optimized:tasks' and x['workers'] == 4 and x['cache_mode'] == 'rebuild']
    extra8 = [x for x in pipeline if x['case'] == 'gemm' and x['contrast'] == 'optimized:tasks' and x['workers'] == 8 and x['cache_mode'] == 'rebuild']
    accepted4 = [x for x in extra4 if x['accepted'] >= 3]
    ratios = [center(x['process_speedup']) for x in accepted4]
    strong = [x for d in [base, data['architecture_analysis']] for x in d['contrast_summaries']
              if x['contrast'] in ['fixed_decomp:optimized', 'fixed_compressed:optimized']]
    facts = {'main': base['aggregates'], 'pipeline_4core': extra4, 'pipeline_gemm_8core': extra8,
             'pipeline_4core_geomean_process_speedup': math.exp(sum(map(math.log, ratios)) / len(ratios)) if ratios else None,
             'original_comparison': base['original_comparison'],
             'clstm_quality': data['clstm_quality_analysis']['contrast_summaries'],
             'pipeline_attribution': data['tasks_attribution_analysis']['contrast_summaries'],
             'strong_baseline_comparisons': strong,
             'audited_attempts': sum(x['attempted'] for x in audit['studies']),
             'audited_successes': sum(x['successful'] for x in audit['studies']),
             'audited_skips': sum(x['skipped'] for x in audit['studies']),
             'frozen_files_checked': audit['frozen_files_checked'],
             'gpu_jobs_this_round': 0, 'default_flags_changed': False,
             'strategy': {'primary': 'Retain the existing per-group sample implementation for lookahead-rebuild CPU experiments; share valid caches equally.',
                          'global_pipeline': 'Keep experimental: four-core GEMM regresses and eight-core whole-process gain is small and inconsistent.',
                          'next_diagnosis': 'Instrument unscoped work in the refactored build before changing global scheduling further; the same-binary pilot is not a replicated cause identification.',
                          'gpu': 'No new GPU work; retain existing evidence without making a GPU contribution a publication requirement.'},
             'interpretation': 'The demonstrated CPU optimization targets lookahead construction. Equal cache reuse removes this work. Original-router correctness/quality and stronger upstream modes are reported separately.'}
    write_json(root / 'conclusions.json', facts)
    lines = ['# CPU 主线实验报告', '',
             f'全部计划已终态并完成证据审计：{facts["audited_attempts"]}项正式/预检测量中{facts["audited_successes"]}项成功，另有{facts["audited_skips"]}项按原版失败门槛跳过；校验{audit["frozen_files_checked"]}个冻结文件。数值失败保留，不进入加速比。', '',
             '结论应定位为 **CPU lookahead 预计算优化**。计时包含加载固定打包/布局结果的成本，但不重新执行打包与布局算法，不能称为完整 FPGA 编译加速；共同缓存后也不能宣称路由搜索被加速。本轮未使用新 GPU 作业，所有新优化开关保持默认关闭。', '',
             '## 修复版与组内采样并行的六电路对照', '',
             '| 电路 | 重建 map 配对速度比中位数 | 共同缓存配对速度比中位数 | 重建合格配对数 |',
             '| --- | ---: | ---: | ---: |']
    for case in ['ex5p', 'softmax', 'clstm_large', 'reduction', 'gemm', 'elliptic']:
        entries = {x['cache_mode']: x for x in base['headline'] if x['case'] == case}
        cold, warm = entries.get('rebuild'), entries.get('reuse')
        lines.append(f'| {case} | {number(center(cold["process_speedup"]) if cold else None)}× | {number(center(warm["process_speedup"]) if warm else None)}× | {cold["accepted"] if cold else 0} |')
    lines += ['', f'六电路重建模式的几何平均配对速度比为 **{number(base["aggregates"]["rebuild"]["geomean_paired_process_speedup"])}×**，共同缓存为 **{number(base["aggregates"]["reuse"]["geomean_paired_process_speedup"])}×**。均为相同核组、相同四核预算下的比较，主要控制已经包含必要的正确性修复。逐次范围见 `analysis.json`；不能把几何平均当作所有电路均明显加速。', '',
              '原版 elliptic 并行在重建/复用模式都发生 SIGSEGV，后续对应重复停止，因此没有合法原版并行速度比。clstm_large 的修复版 parallel 虽合法，但 CPD 从原版6.58269ns变为7.71292ns（+17.17%），超过5%门槛；这组不能宣称质量合格地击败原版。', '',
              '| 电路 | 相对原版 parallel 的合格配对 | 进程速度比中位数 |',
              '| --- | ---: | ---: |']
    for x in base['original_comparison']:
        lines.append(f'| {x["case"]} | {x["quality_pass"]}/{x["pairs"]} | {number(center(x["process_speedup"]))}× |')
    lines += ['', '无合格配对的行不计算速度比；CLSTM恢复质量后的公平对照在下文单列。', '',
              '## 核数与分项成本', '',
              '| 电路 | 物理核 | 修复版进程中位秒 | 组内并行进程中位秒 | 同核配对速度比 | 合格配对 |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for case in ['gemm', 'elliptic']:
        for workers in [1, 2, 4, 8]:
            pair = next((x for x in base['contrast_summaries'] if (x['case'], x['workers'], x['cache_mode'], x['contrast'])
                         == (case, workers, 'rebuild', 'fixed:optimized')), None)
            entries = {x['variant']: x for x in base['summaries'] if (x['case'], x['workers'], x['cache_mode']) == (case, workers, 'rebuild')}
            if pair and 'fixed' in entries and 'optimized' in entries:
                lines.append(f'| {case} | {workers} | {number(center(entries["fixed"]["native_process_seconds"]))} | {number(center(entries["optimized"]["native_process_seconds"]))} | {number(center(pair["process_speedup"]))}× | {pair["accepted"]} |')
    lines += ['', '速度比先逐重复配对再取中位数，不必等于两列中位时间之比。这些是相同核数下的算法消融；不同核数可能改变路由调度、迭代数和质量，不能将其时间差全部解释为lookahead并行效率。完整CPD、线长、迭代数、Routing和峰值内存见分析文件。', '',
              '| GEMM四核重建配置 | lookahead中位秒 | Routing中位秒 | 进程中位秒 | VPR峰值RSS中位MiB |',
              '| --- | ---: | ---: | ---: | ---: |']
    for x in base['summaries']:
        if (x['case'], x['workers'], x['cache_mode']) == ('gemm', 4, 'rebuild') and x['variant'] in ['original', 'fixed', 'optimized']:
            lines.append(f'| {x["variant"]} | {number(center(x["lookahead_seconds"]))} | {number(center(x["routing_seconds"]))} | {number(center(x["native_process_seconds"]))} | {number(center(x["vpr_reported_peak_rss_mib"]), 1)} |')
    lines += ['', '## 统一采样 pipeline 的增量结果', '',
              '统一队列跨层/线段组调度采样，保持严格归并与插值顺序；最多2P个在途结果，每线程独立工作区。所有计时变体对称写出 map，并逐字节对照原版串行结果。这里的基线是已有组内采样并行，不能直接与另一研究的原版时间相除。', '',
              '| 电路 | 核数 | 合格配对 | VPR进程速度比中位数 [最小,最大] | lookahead阶段速度比中位数 |',
              '| --- | ---: | ---: | ---: | ---: |']
    for x in sorted(extra4 + extra8, key=lambda x: (x['case'], x['workers'])):
        speed = x['process_speedup']
        interval = f'{number(speed["median"])} [{number(speed["min"])},{number(speed["max"])}]' if speed else '—'
        lines.append(f'| {x["case"]} | {x["workers"]} | {x["accepted"]} | {interval} | {number(center(x["lookahead_speedup"]))} |')
    lines += ['', f'速度比小于1表示新队列更慢。六电路四核增量速度比的几何平均为{number(facts["pipeline_4core_geomean_process_speedup"])}×。四核 GEMM 观察到退步，保留负结果；785个被审计源码中只有预期三个文件改变、关键编译选项一致。已检查的首批退步样本没有cgroup限流，额外耗时主要落在未覆盖的VPR工作，不能写成已经证明的分配器问题。1/2核只有探索性单次结果，见 `tasks_analysis.json`。', '',
              '另外保留一组四核GEMM探索性归因三元组：旧实现、重构后仍用组内并行、重构后启用pipeline。后两者二进制SHA完全相同，通过开关分离调度效果；具体结果见 `tasks_attribution_analysis.json`。单次归因不作为统计确认，也不替代旧实现这个实际端到端基线。', '',
              '| GEMM四核归因比较（各一次） | 进程速度比 | lookahead速度比 |',
              '| --- | ---: | ---: |']
    for x in data['tasks_attribution_analysis']['contrast_summaries']:
        lines.append(f'| {x["contrast"]} | {number(center(x["process_speedup"]))}× | {number(center(x["lookahead_speedup"]))}× |')
    lines += ['', '归因三元组中，重构后保留旧调度已经慢于旧实现；同一二进制开启pipeline只带来很小变化。因此不能把整个候选版本的退步全部归因于全局队列。此结论只是单次定位线索，尚未确定具体函数或分配器原因。', '',
              '完整构建核对：523条编译/链接命令在替换源码与构建路径后完全一致；1421个实际项目源码/生成依赖均配对，除预期三个源码文件外，生成文件差异只涉及路径、由路径生成的头文件保护名与构建时间。见 `build_command_comparison.json`、`compiled_input_comparison.json` 和 `generated_input_comparison.json`。', '',
              'VPR自己报告的整个flow时间与外部进程计时也作交叉核对；未覆盖成本是外部进程时间减去互不嵌套的顶层定时器之和。', '',
              '| GEMM配置 | 核数 | 未覆盖成本中位秒 | 外部计时减VPR整个flow中位秒 |',
              '| --- | ---: | ---: | ---: |']
    for x in data['tasks_analysis']['summaries']:
        if x['workers'] in [4, 8] and x['variant'] in ['optimized', 'tasks']:
            lines.append(f'| {x["variant"]} | {x["workers"]} | {number(center(x["unscoped_wall_seconds"]))} | {number(center(x["external_clock_gap_seconds"]))} |')
    lines += ['', '## clstm_large 的合法质量对照', '',
              '现有 upstream `parallel_decomp` 可恢复质量，因此单独做了原版 parallel、原版 decomp、修复版decomp和两种CPU优化decomp的三次确认。decomp本身不是我们的创新；采样优化的收益必须继续对比原版/修复版decomp。', '',
              '| 比较 | 缓存 | 合格配对 | 进程速度比中位数 | CPD变化中位数 |',
              '| --- | --- | ---: | ---: | ---: |']
    for x in data['clstm_quality_analysis']['contrast_summaries']:
        if x['contrast'] not in ['original_decomp:optimized', 'original_decomp:tasks', 'fixed:optimized', 'fixed:tasks']:
            continue
        lines.append(f'| {x["contrast"]} | {x["cache_mode"]} | {x["accepted"]} | {number(center(x["process_speedup"]))}× | {number(center(x["cpd_change_percent"]))}% |')
    lines += ['', '此处fixed/optimized/tasks都使用decomp，分别表示仅修复、组内采样、统一pipeline。不能将按结果挑选每个电路最佳模式包装成已验证的自动选择策略。', '',
              '## 架构与强基线', '',
              f'原生架构扩展共{data["architecture_analysis"]["attempted"]}项、{data["architecture_analysis"]["successful"]}项成功。单层Hecate与双层Hecate的80/100/120通道宽度分别成对比较；elliptic宽度80两侧均在600秒上限内未收敛。宽度100图除XML首行元数据外与原图相同，是重现控制，不是新增独立架构。宽度120更易收敛，不能跨宽度把资源增加的效果当成算法加速。', '',
              '锁定VPR的compressed_map明确不支持3D，SIGABRT预检已保存；只在2D做合法比较。parallel_decomp采用相同输入和核心预算。MultiQueue探索仅4项，3项成功，elliptic在200轮后剩1个超用节点；不计算失败样本速度比，也不据此宣布胜过整个MultiQueue算法族或已完成所有最优参数比较。', '',
              '| 输入 | 更强控制→组内采样并行 | 合格配对 | 进程速度比中位数 | CPD变化中位数 |',
              '| --- | --- | ---: | ---: | ---: |']
    for x in strong:
        lines.append(f'| {x["case"]} | {x["contrast"]} | {x["accepted"]}/{x["pairs"]} | {number(center(x["process_speedup"]))}× | {number(center(x["cpd_change_percent"]))}% |')
    lines += ['', '这些比较允许既有算法改变路径；仍执行5%质量门槛。decomp主扩展只有一次探索配对，二维compressed_map有三次；不能与CLSTM独立三次确认混为一组。', '',
              '## 计时、可复现性与边界', '',
              '对照锁定VTR提交 `0b912334fdd83bb754b302146ac0d1ec9edc9a0e`，使用GCC11.4、Release/O3、TBB、关闭IPO。原版已有parallel/decomp能力；本轮同核比较不把启用线程算作新贡献，也不声称覆盖未测试的更新版本。', '',
              '硬件为双路Intel Xeon Gold6530，64物理核/128逻辑CPU；本会话cgroup配额54核、内存上限300GiB。每次测量使用同一核组中的1/2/4/8个不同物理核，审计所有VPR线程。不同研究使用空闲CPU集合并可并发，宿主和内存系统共享，没有资源独占。三次重复是固定seed的运行重复，不是三个布局种子。', '',
              '主要指标包括读取固定网表/布局/RRG、lookahead、Routing和原生FULL/STA；独立原版回读另外报告workflow。输入同样预读，rebuild只表示重建lookahead，不表示磁盘冷缓存。计时汇总保留顶层定时器，不把Create Device与其内层RRG读取重复相加；未覆盖的墙钟时间明确标为unscoped，不擅自归因。峰值内存优先使用VPR报告的进程高水位，五秒/proc采样仅作补充。', '',
              '只有完整收敛、零超用、两次FULL/STA一致、路由回读前后SHA不变、CPU亲和性通过，并且CPD/线长退化各不超过5%的配对才能进入合格性能汇总。所有新pipeline map都要求与原版串行逐字节一致。', '',
              '首次缓存预检误将VPR未收敛返回码2当作异常，已修正并保留失败记录。首次架构输入准备误做完整路由，已仅中止本任务的准备进程并保留日志；第二次用一轮路由生成输入，不作为性能样本。它们不覆盖正式实验结果。', '',
              '论文方向可以转为CPU主线，但当前证据仍限于六个原有电路、Hecate单/双层及少量宽度变化；需要更广基准、多布局种子、独立确认以及充分的相关工作对照。新实现是具体可评审的调度实验，不据此保证论文新颖性或录用。GPU保留为后续扩展，不强行作为主贡献。', '',
              '## 本轮策略决定', '',
              '后续CPU主线保留现有组内采样并行实现：新资源图需要重建lookahead时衡量其收益，可复用时双方读取同一有效缓存。全局pipeline保持实验选项，四核GEMM退步，八核局部阶段加速尚未变为稳定的完整进程收益，不替换现有实现或自动按电路挑选。', '',
              '下一项优化应先定位重构版本中增加的未覆盖成本，再决定保留哪些结构变化。CPU论文需要同时扩大独立电路/架构和布局种子验证，并突出预计算方法；当前没有新增GPU优化或GPU默认接管。', '',
              '## 文件入口', '',
              '- `conclusions.json`：核心数字与比较结果。',
              '- `analysis.json`、`tasks_analysis.json`、`tasks_extension_analysis.json`：六电路/核数与新队列的完整逐次比较。',
              '- `clstm_quality_analysis.json`、`architecture_analysis.json`、`multiqueue_analysis.json`：质量、架构、强基线。',
              '- `tasks_attribution_analysis.json`：同二进制的重构/调度归因探索。',
              '- `evidence_verification.json`：终态日志、路由、map、输入、二进制及脚本来源审计。',
              '- `implementation_verification.json`、`acceptance.json`：构建依赖核对及最终验收。',
              '- `cpu_changes.patch`、`tasks_changes.patch`、`source_provenance.json`、`tasks_provenance.json`、`tasks_source_audit.json`：源码和构建。',
              '- `figures/cpu_study.pdf`、`figures/cpu_study.svg`、`figures/cpu_study.png`：可分享图表；误差线为实测范围，不是置信区间。',
              '- `docs/native_cpu_paper_study.md`、`docs/native_cpu_sample_pipeline.md`：工程根目录下的方法说明。', '']
    (root / 'report.md').write_text('\n'.join(lines).replace('—×', '—'))
    print(root / 'report.md')


if __name__ == '__main__':
    main()
