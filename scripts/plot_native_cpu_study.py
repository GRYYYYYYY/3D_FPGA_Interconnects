"""Export paper-style figures; ranges are observed repeats, not confidence intervals."""
import argparse
import json
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read(path):
    return json.loads(path.read_text())


def raw_rows(plan_path):
    plan = read(plan_path)
    rows = []
    for name in plan['lanes']:
        s = read(Path(plan['output']) / name / 'summary.json')
        rows.extend(row | {'lane': name} for row in s['measurements'] if row.get('success'))
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    args = p.parse_args()
    root = args.root.resolve()
    main_data = read(root / 'analysis.json')
    pipeline = [read(root / 'tasks_analysis.json'), read(root / 'tasks_extension_analysis.json')]
    assert main_data['status'] == 'completed' and all(x['status'] == 'completed' for x in pipeline)
    out = root / 'figures'
    out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 10, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    cases = ['ex5p', 'softmax', 'clstm_large', 'reduction', 'gemm', 'elliptic']
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)

    def bars(ax, datasets, title):
        width = .34 if len(datasets) == 2 else .6
        for number, (label, mode, source, color) in enumerate(datasets):
            values, low, high, positions = [], [], [], []
            for i, case in enumerate(cases):
                matches = [x for x in source if x['case'] == case and x['workers'] == 4
                           and x['cache_mode'] == mode and x['accepted'] >= 3]
                if not matches:
                    continue
                item = matches[0]['process_speedup']
                positions.append(i + (number - (len(datasets) - 1) / 2) * width)
                values.append(item['median'])
                low.append(item['median'] - item['min'])
                high.append(item['max'] - item['median'])
            ax.bar(positions, values, width=width, yerr=[low, high], capsize=3, label=label, color=color)
        ax.axhline(1, color='#444444', linewidth=.9, linestyle='--')
        ax.set_xticks(range(len(cases)), cases, rotation=25, ha='right')
        ax.set_ylabel('Paired VPR process speedup')
        ax.set_title(title)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.18)
        ax.legend(frameon=False, fontsize=9)
        ax.grid(axis='y', alpha=.18)
        ax.set_axisbelow(True)

    base = [x for x in main_data['contrast_summaries'] if x['contrast'] == 'fixed:optimized']
    bars(axes[0, 0], [('Rebuild map', 'rebuild', base, '#36759a'), ('Common cache', 'reuse', base, '#e1a452')],
         'A. Per-group samples vs corrected CPU')
    extra = [x for d in pipeline for x in d['contrast_summaries'] if x['contrast'] == 'optimized:tasks']
    bars(axes[0, 1], [('Rebuild map', 'rebuild', extra, '#4f9176')],
         'B. Global pipeline vs per-group samples')

    ax = axes[1, 0]
    gemm = [x for x in pipeline[0]['contrast_summaries'] if x['case'] == 'gemm'
            and x['cache_mode'] == 'rebuild' and x['contrast'] == 'optimized:tasks']
    for field, label, color in [('lookahead_speedup', 'Lookahead phase', '#4f9176'),
                                ('process_speedup', 'VPR process', '#815ca2')]:
        points = sorted([x for x in gemm if x['accepted'] and x[field]], key=lambda x: x['workers'])
        cpus = [x['workers'] for x in points]
        values = [x[field]['median'] for x in points]
        errors = [[x[field]['median'] - x[field]['min'] for x in points],
                  [x[field]['max'] - x[field]['median'] for x in points]]
        ax.errorbar(cpus, values, yerr=errors, marker='o', capsize=3, color=color, label=label)
    ax.axhline(1, color='#444444', linewidth=.9, linestyle='--')
    ax.set_xticks([1, 2, 4, 8], ['1\n(n=1)', '2\n(n=1)', '4\n(n=3)', '8\n(n=3)'])
    ax.set_xlabel('Physical CPU cores; paired repetitions')
    ax.set_ylabel('Global pipeline speedup vs per-group samples')
    ax.set_title('C. GEMM: phase gain vs process gain')
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=.18)

    rows = raw_rows(root / 'plan.json')
    ax = axes[1, 1]
    for case in ['gemm', 'elliptic']:
        for variant, label, color in [('fixed', 'Corrected CPU', '#7b7b7b'), ('optimized', 'Per-group samples', '#36759a')]:
            series, lower, upper, cpus = [], [], [], []
            ones = {(x['lane'], x['repeat']): x for x in rows if x['case'] == case and x['variant'] == variant
                    and x['cache_mode'] == 'rebuild' and x['workers'] == 1}
            for cores in [1, 2, 4, 8]:
                ratios = []
                for row in rows:
                    if (row['case'], row['variant'], row['cache_mode'], row['workers']) != (case, variant, 'rebuild', cores):
                        continue
                    reference = ones.get((row['lane'], row['repeat']))
                    if reference and row['critical_path_ns'] <= 1.05 * reference['critical_path_ns'] and row['wirelength'] <= 1.05 * reference['wirelength']:
                        ratios.append(reference['native_process_seconds'] / row['native_process_seconds'])
                if ratios:
                    center = median(ratios)
                    cpus.append(cores)
                    series.append(center)
                    lower.append(center - min(ratios))
                    upper.append(max(ratios) - center)
            ax.errorbar(cpus, series, yerr=[lower, upper], marker='o' if case == 'gemm' else 's',
                        linestyle='-' if case == 'gemm' else '--', capsize=3,
                        label=case + ': ' + label, color=color)
    ax.axhline(1, color='#444444', linewidth=.9, linestyle='--')
    ax.set_xticks([1, 2, 4, 8])
    ax.set_xlabel('Physical CPU cores')
    ax.set_ylabel('Process speedup vs same variant at 1 core')
    ax.set_title('D. GEMM and elliptic: core scaling')
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=.18)
    fig.suptitle('CPU routing-flow study: matched controls and observed repeat ranges', fontsize=13)
    for suffix in ['png', 'pdf', 'svg']:
        fig.savefig(out / ('cpu_study.' + suffix), dpi=180)
    (out / 'caption.txt').write_text(
        'Bars and points show median paired ratios; error bars show observed minimum/maximum, not confidence intervals. '
        'Only complete, independently checked, zero-overuse results within the 5% quality budget are included. '
        'A compares corrected CPU controls, not the buggy original. B is a separate study with symmetric map serialization. '
        'C compares the two CPU optimizations at matched core count and block; 1/2-core points are single-run pilots. '
        'D pairs each core count with the same variant, repeat and CPU block at one core. '
        'Input netlist/placement/RRG are fixed; VPR process time includes RRG loading, lookahead, routing and native checks, '
        'includes loading fixed packed/placed inputs, and excludes rerunning packing/placement algorithms and independent readback. '
        'Shared host, no exclusive resources claimed.\n')
    print(out / 'cpu_study.png')


if __name__ == '__main__':
    main()
