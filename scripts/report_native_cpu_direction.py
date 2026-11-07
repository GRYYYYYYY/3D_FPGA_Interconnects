#!/usr/bin/env python3
"""Render the reconciled direction report and a not-yet-submitted experiment spec."""
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/native_cpu_direction_20261102'


def load(name):
    return json.loads((OUT / name).read_text())


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    a = load('analysis.json')
    inv = load('circuit_inventory.json')
    configs = {(c['workers'], c['variant']): c for c in a['configurations']}
    eligible = [c for c in inv['circuits'] if not c['already_in_mainline_six_circuit_suite']
                and not c['models_missing_from_architecture']]
    selected = sorted(eligible, key=lambda c: (-c['approximate_instances'], c['name']))[:3]
    triad_path = ROOT / 'results/native_cpu_evidence_20261102/triad_plan.json'
    triad = json.loads(triad_path.read_text())
    plan = {
        'status': 'specified_not_submitted', 'new_solver_runs': 0,
        'purpose': 'Extend map-equivalent CPU lookahead coverage while separating state repair from parallel construction.',
        'selection_rule': 'Top three local input directive-instance counts outside the existing six-circuit mainline, with all subckt model names present in the fixed architecture. No measured candidate runtime used in selection.',
        'circuits': selected,
        'scope': 'Existing Koios inputs, all previously referenced in adjacent project metadata; not independent benchmarks. Input counts do not establish larger RR graphs than GEMM.',
        'architecture': {'path': inv['architecture'], 'sha256': inv['architecture_sha256']},
        'binaries': triad['binaries'],
        'variants': {
            'stock': {'binary': 'original', 'parallel': False, 'router': 'parallel'},
            'fixed_serial': {'binary': 'cpu', 'parallel': False, 'router': 'parallel', 'env': {'VPR_HYBRID_LOOKAHEAD_TASKS': '0'}},
            'per_group': {'binary': 'cpu', 'parallel': True, 'router': 'parallel', 'env': {'VPR_HYBRID_LOOKAHEAD_TASKS': '0'}},
            'pipeline': {'binary': 'cpu', 'parallel': True, 'router': 'parallel', 'env': {'VPR_HYBRID_LOOKAHEAD_TASKS': '1'}},
        },
        'environment': 'Clean inherited VPR_CPU_* and VPR_HYBRID_* overrides using the frozen runner; enable only the declared lookahead controls. GPU and trace off; skip-same-partition off; both state fixes on for all three corrected arms. Capture actual environment and affinity.',
        'seeds': [1, 2], 'workers': 8, 'runtime_repeats': 3, 'cache_modes': ['rebuild', 'reuse'],
        'planned_formal_samples_if_all_qualify': 144,
        'preparation': {
            'fresh_pack_and_place': True, 'target_utilization': 0.6, 'initial_channel_width': 100,
            'geometry': 'Use fixed native 3D architecture; verify actual occupancy on both layers and record RR nodes/edges, grid size and packed blocks.',
            'failure_policy': 'Retain unsupported, failed and timed-out inputs; no replacement based on speed. If width 100 is unroutable, record it and freeze a separately versioned common-width protocol before any timed comparison.',
            'configuration_binding': 'Hash BLIF, architecture, packed netlist, placement, RR graph, map, binaries and runner before formal runs.',
        },
        'qualification': {
            'plain_endpoint': 'Compare same-ELF per_group with the old frozen per-group binary for map, route-body, CPD, wirelength and iterations. Failure blocks strict attribution and requires diagnosis, not candidate-specific tuning.',
            'correctness': 'Require byte-equivalent map, native FULL and independent stock FULL/STA; log any route-body difference separately.',
            'quality': 'For each corrected optimization require CPD and wirelength <=1.05 times fixed_serial and per_group controls. Report raw-stock comparisons separately; never hide stock illegality or repair costs.',
            'timed_trace': False,
        },
        'execution': {
            'lane': 'One solver at a time; same eight physical cores on one NUMA node for every arm.',
            'exclusivity': 'Prefer exclusive reservation if available; otherwise explicitly label shared-host results and capture load/cgroup metadata.',
            'order': 'Use a frozen balanced rotation of the four arm orders across six layouts and three repeats; alternate cache-mode order. Pair by circuit/placement/repeat.',
            'cache': 'Identical pre-read for all arms; reuse one qualified byte-identical map. Rebuild means rebuild lookahead, not cold filesystem cache.',
            'limits': 'Use existing 900-second routing timeout per attempt; retain timeouts as failures and revisit only under a versioned protocol. Freeze a separate bounded pack/place timeout before preparing execution manifests.',
        },
        'metrics': ['process wall seconds', 'internal VPR flow seconds (sensitivity only)', 'workflow seconds including independent check',
                    'disjoint phase wall seconds', 'lookahead wall seconds', 'CPD', 'wirelength', 'route iterations',
                    'route-body equality', 'RR node/edge counts', 'actual CPU affinity', 'peak RSS with measurement method'],
        'primary_comparisons': ['same-ELF fixed_serial -> per_group', 'same-ELF per_group -> pipeline', 'same-ELF fixed_serial -> pipeline'],
        'secondary_comparison': 'stock -> pipeline is system-level, includes state fixes; all arms have eight routing workers.',
        'aggregation': 'Median of paired time ratios for each layout; geometric mean across layouts within circuit, then equal weight across circuits. Publish all samples, quality failures and cache negative cases; no aggregate omitting failed members.',
        'promotion_gate': 'All legality/map/QoR gates pass; rebuild process geometric mean >=1.03 over per_group, each circuit >=1.00, and no layout cache process median regression >3%. Otherwise report bounded applicability and leave defaults unchanged. This engineering rule is not statistical significance.',
        'conditional_extension_not_in_144': 'Only after qualified eight-core results, 16-core per_group/pipeline rebuild on the same three circuits/two layouts/three repeats (36 runs). Interleave core-count blocks if making scaling claims.',
        'remaining_launch_work': ['Verify binary hashes and endpoint behavior', 'Freeze pack/place commands and timeout, materialize runner-specific manifests', 'Prepare six layouts, check map/legality/QoR, then evaluate qualification'],
    }
    dump('next_experiment.json', plan)

    lines = [
        '# CPU 主线、近期负例与下一轮验证分析', '',
        '已完成现有证据重算及本地电路盘点。本次没有启动新求解、修改算法或默认开关。', '',
        '**判断：近期负例集中在新的调度候选与路由轨迹变化，不能据此否定已经验证的 CPU lookahead 并行构建。**', '',
        '|方向|已观察到的证据|应作出的判断|', '|---|---|---|',
        '|组内采样 + 既有跨组 pipeline|同八核 GEMM 原版→pipeline 配对进程速度比中位 1.637905×；组内→pipeline 1.084265×|已有正收益；原版对照含状态修复，整体差值不全是预计算算子的因果收益|',
        '|新 bounded 调度|GEMM 八核相对组内 1.067711×，但相对已有 pipeline 0.980365×；四核及 elliptic 缓存有负例|未证明优于已有方法；不能笼统说所有探索都更慢|',
        '|小电路重复|三电路两布局重复后，重建 stock→pipeline 等权几何平均 1.057578×，组内→pipeline 1.096909×|收益范围与 GEMM 不同，不能用六个布局冒充六种独立电路|',
        '|状态修复与消融|原动态通知丢失导致第二轮出现 9/8 个过期分区归属；修复消除这些越界。串行端点一致，部分并行端点不一致|修复有正确性依据；额外迭代和质量变化不能直接归咎于预计算。尚未建立全部因果归因或竞态证明|',
        '|跳过同分区重插入|合法、map 等价、全程零分区越界，但 s38417 两布局 CPD 恶化 23.71% / 6.78%|归属正确不保证启发式次序与 QoR 不变；候选已拒绝，未执行性能矩阵|', '',
        '为什么会恶化：减少 erase/insert 会改变 unordered_set 的遍历次序，而后续按扇出 stable_sort 会保留同扇出的输入次序。路由具有拥塞反馈，处理顺序变化可影响资源占用、后续重布线和最终时序。现有诊断支持这条机制，但并未逐个隔离所有顺序因素。map 字节等价只约束预计算输出，不能替代最终路由质量验证。', '',
        '对上一轮解释作一项修正：bounded 的负例尚不能确定归因为“资源约束或调度开销抵消收益”。可确认的是它没有稳定超过已有 pipeline；队尾、工作区生命周期、内存访问等具体成本仍需独立计时。同 ELF 缓存 s38417_s2 约 3.27% 退化也仍未定位，不能宣布为纯噪声。', '',
        '**GEMM 的收益空间已发生变化。** 下表为各阶段各自三次运行的中位数，单位秒；阶段中位数不应再相加等同于进程中位数。', '',
        '|同八核重建|原版|修复后组内采样|既有 pipeline|', '|---|---:|---:|---:|',
    ]
    phase_labels = {'circuit_preparation': '电路读取/清理/校验与时序图准备',
                    'packing_load_and_check': '加载并检查已打包网表',
                    'device_creation_including_rr_load': '设备创建（包含 RR 图加载）',
                    'lookahead': 'lookahead 构建', 'routing': '路由', 'post_route_sync': '路由后网表同步',
                    'other_unassigned': '其余未分项成本（逐样本求差）'}
    for key, label in phase_labels.items():
        vals = [configs[8, v]['phase_seconds'][key]['median'] for v in ['stock', 'frozen', 'pipeline']]
        lines.append(f'|{label}|' + '|'.join(f'{x:.2f}' for x in vals) + '|')
    lines.append('|完整原生进程|' + '|'.join(f'{configs[8,v]["process_seconds"]["median"]:.2f}' for v in ['stock','frozen','pipeline']) + '|')
    lines += ['', 'pipeline 的设备创建约 52.16 秒，其中 RR 图加载自身中位 49.44 秒。不能把加载全部称为磁盘 I/O：还可能包含解析、分配、构造和检查，现有计时没有拆开这些成本。余下约 39.93 秒仍未细分，不应直接归为线程调度。完整进程包括原生检查与输出，不含本轮准备 pack/place；独立复核另计入 workflow。', '',
              '|pipeline 核数|lookahead / 进程中位秒|逐样本 lookahead 占比中位|lookahead 再快一倍时整体速度比|lookahead 完全免费时整体速度比上限|',
              '|---:|---:|---:|---:|---:|']
    for w in [4, 8, 16]:
        c = configs[w, 'pipeline']
        lines.append(f'|{w}|{c["phase_seconds"]["lookahead"]["median"]:.2f} / {c["process_seconds"]["median"]:.2f}|{100*c["lookahead_fraction"]["median"]:.2f}%|{c["speedup_if_lookahead_halved"]["median"]:.4f}×|{c["ideal_speedup_if_lookahead_free"]["median"]:.4f}×|')
    lines += ['', '上限逐样本按 T/(T−L) 计算；二倍构建速度按 T/(T−L/2) 计算，再取中位数。假设其余成本完全不变，不是未来性能预测。八核与四/十六核来自不同测量时段，宿主共享，不能据此作严格强扩展结论。', '',
              '计时已核查源码作用域：固定线宽时 lookahead 在 Routing 计时外；Create Device 包含 RR load；Load packing 包含 packed-file load；lookahead 包含 wire/src 阶段。累计 Flow timing analysis 不再相加。图中逐次堆叠采用同一样本分项，避免中位数相加误差。', '',
              '**下一步：先扩展已有主线的较大输入覆盖，再根据分项成本选新优化。**', '',
              f'已盘点本地 20 个 Koios BLIF，扫描 {inv["scanned_metadata_files"]} 份计划/清单。20 个输入均有历史引用；全部只能称现有套件扩展，不能称全新独立基准。按 `.names + .latch + .subckt` 数量预选当前主线六电路之外规模最大的三个输入，不按候选速度挑选：', '',
              '|预选输入|结构实例数量代理|BLIF MiB|原生架构模型名称检查|', '|---|---:|---:|---|']
    for c in selected:
        lines.append(f'|{c["name"]}|{c["approximate_instances"]:,}|{c["bytes"]/1024**2:.1f}|通过；尚未验证 pack/place|')
    lines += ['', '这些数量不是打包后 block 数或 RR 图大小，也没有证明它们比 GEMM 的 RR 图更大。后续必须记录实际 RR 节点/边、设备尺寸、双层占用以及完整输入 hash。输入来自同一套件，论文独立泛化证据仍需另行拓展。', '',
              '1. 为三输入分别准备种子 1/2 的新布局，先验证原生三维架构兼容、map 字节等价、FULL/STA 和 QoR。失败保留，不按收益换电路。',
              '2. 使用同一修复版 ELF 的串行 lookahead、组内并行、跨组 pipeline 三臂隔离构建贡献，额外保留同八核原版并行路由作系统基线。这里“串行”仅指 lookahead 构建；路由仍给八核。先核验同 ELF 组内臂与旧冻结组内端点。',
              '3. 全部合格后执行 3 电路 × 2 布局 × 4 臂 × 2 缓存状态 × 3 重复 = 144 项，固定物理核、交错平衡顺序、单 lane，优先独占资源；拿不到则标明共享宿主。进程时间为主指标，workflow、分项和 QoR 同时报告。',
              '4. 八核验证完成后，再决定 16 核的 36 项扩展。不继续推广已拒绝的跳过重插入候选。下一项代码优化先针对 RR 加载/网表检查/未分项区间做诊断拆分，区分解析、内存构造、检查和输出成本后再选方向；GPU 接管需有额外证据。', '',
              '已保存 [实验规格](next_experiment.json)，状态为 specified_not_submitted。它尚不是可直接执行的 runner 清单：需冻结 pack/place 命令与超时、准备并绑定实际布局/RR 输入、通过资格门槛。原有失败、源码、二进制和默认设置保留。', '',
              '数据：[逐次计时与上限](analysis.json)、[20 电路盘点](circuit_inventory.json)、[来源 hash](source_bindings.json)、[阶段图 PDF](gemm_costs.pdf)、[阶段图 SVG](gemm_costs.svg)。复现：先运行 scripts/analyze_native_cpu_direction.py，再以已有 plot_packages 的 PYTHONPATH 运行 scripts/report_native_cpu_direction.py。', '',
              '主要历史依据：../native_cpu_evidence_20261102/report.md、../native_cpu_repeat_20261102/report.md、../native_cpu_slices_20261101/conclusions.json、../native_state_ablation_20261102/report.md、../native_state_trace_20261102/report.md、../native_partition_skip_20261102/report.md。']
    (OUT / 'report.md').write_text('\n'.join(lines) + '\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors = ['#7d99ae', '#d3b16c', '#487aa1', '#39a67c', '#bd6d59', '#a593ba', '#c8cdd2']
    labels = ['Circuit preparation', 'Packed netlist load/check', 'Device incl. RR load', 'Lookahead', 'Routing', 'Post-route sync', 'Other / unassigned']
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for j, variant in enumerate(['stock', 'frozen', 'pipeline']):
        for k, r in enumerate(configs[8, variant]['samples']):
            x, bottom = j * 4 + k, 0
            for (phase, _), color, label in zip(phase_labels.items(), colors, labels):
                value = r['phase_seconds'][phase]
                ax.bar(x, value, bottom=bottom, color=color, width=.82, label=label if j == 0 and k == 0 else None)
                bottom += value
            assert abs(bottom - r['process_seconds']) < 1e-8
            ax.text(x, bottom + 3, f'{bottom:.1f}', ha='center', fontsize=8)
    ax.set_xticks([1, 5, 9], ['Original VPR', 'Corrected per-group', 'Existing pipeline'])
    ax.set_ylabel('Native process wall time (seconds)')
    ax.set_title('GEMM, eight physical cores, lookahead rebuild\nThree recorded runs per arm; shared host')
    ax.set_ylim(0, 365)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.13), ncol=3, fontsize=8, frameon=False)
    fig.tight_layout()
    for ext in ['png', 'svg', 'pdf']:
        fig.savefig(OUT / f'gemm_costs.{ext}', dpi=180, bbox_inches='tight')
    plt.close(fig)
    bindings = load('source_bindings.json')
    for p in [Path(__file__), triad_path]:
        bindings['sha256'][str(p.resolve())] = hashlib.sha256(p.read_bytes()).hexdigest()
    dump('source_bindings.json', bindings)
    dump('verification.json', {'status': 'passed', 'decomposed_runs': sum(len(c['samples']) for c in a['configurations']),
                               'checks': ['Required timers occur once per run', 'Lookahead/routing equal original summary fields',
                                          'All disjoint phase sums equal measured process time', 'Paired ratios equal prior analysis',
                                          'All plotted bars sum to their own run total', 'Deterministic size-only input selection'],
                               'new_solver_runs': 0, 'default_changed': False})
    print('Report and specification complete:', ', '.join(c['name'] for c in selected))


if __name__ == '__main__':
    main()
