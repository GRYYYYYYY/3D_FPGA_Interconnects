"""Compare only completed, quality-qualified, matched native CPU trials."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import re
from statistics import median

from prepare import write_json


def compare(reference, candidate):
    result = {'reference': reference['key'], 'candidate': candidate['key'], 'eligible': False}
    for row in [reference, candidate]:
        if not row.get('success') or row.get('log_evidence', {}).get('final_overused_nodes') != 0:
            return result | {'reason': 'Both solutions must complete independent FULL/STA and have zero overuse.'}
    for field in ['case', 'workers', 'cache_mode', 'repeat', 'lane', 'hostname']:
        if reference[field] != candidate[field]:
            return result | {'reason': 'Unmatched ' + field}
    if reference['cpu_budget']['cpu_set'] != candidate['cpu_budget']['cpu_set']:
        return result | {'reason': 'Different CPU affinity'}
    if {k: x['sha256'] for k, x in reference['inputs'].items()} != {k: x['sha256'] for k, x in candidate['inputs'].items()}:
        return result | {'reason': 'Different frozen inputs'}
    if reference['lookahead_cache_sha256'] != candidate['lookahead_cache_sha256']:
        return result | {'reason': 'Different shared cache'}
    cpd = 100 * (candidate['critical_path_ns'] / reference['critical_path_ns'] - 1)
    wire = 100 * (candidate['wirelength'] / reference['wirelength'] - 1)
    result.update(eligible=True, quality_pass=cpd <= 5 + 1e-9 and wire <= 5 + 1e-9,
                  cpd_change_percent=cpd, wire_change_percent=wire,
                  process_speedup=reference['native_process_seconds'] / candidate['native_process_seconds'],
                  workflow_speedup=reference['workflow_seconds'] / candidate['workflow_seconds'],
                  routing_speedup=reference['routing_seconds'] / candidate['routing_seconds'],
                  route_body_equal=reference['route_body_sha256'] == candidate['route_body_sha256'])
    first = reference['log_evidence'].get('stage_seconds', {}).get('lookahead_build')
    second = candidate['log_evidence'].get('stage_seconds', {}).get('lookahead_build')
    result['lookahead_speedup'] = first / second if first and second else None
    return result


def describe(values):
    values = [v for v in values if v is not None]
    return {'n': len(values), 'median': median(values), 'min': min(values), 'max': max(values)} if values else None


def top_level_timings(text, process_seconds):
    """Keep parent timers, excluding nested ## timers from the additive sum."""
    stages = defaultdict(float)
    for name, value in re.findall(r'^# ([^\n]+?) took ([\d.eE+-]+) seconds', text, re.MULTILINE):
        stages[name] += float(value)
    remainder = process_seconds - sum(stages.values())
    return {'top_level_seconds': dict(stages), 'unscoped_seconds': remainder,
            'rounding_or_overlap_warning': remainder < -.2}


def analyze(plan_path):
    plan = json.loads(plan_path.read_text())
    root = Path(plan['output'])
    lanes = {}
    rows = []
    for name in plan['lanes']:
        path = root / name / 'summary.json'
        if not path.exists():
            lanes[name] = {'status': 'not_started'}
            continue
        lane = json.loads(path.read_text())
        lanes[name] = {k: lane.get(k) for k in ['status', 'error', 'cache_qualifications', 'skipped', 'hostname']}
        rows.extend(row | {'lane': name, 'hostname': lane['hostname']} for row in lane['measurements'] if 'finished_utc' in row)
    grouped = defaultdict(list)
    matched = defaultdict(dict)
    for row in rows:
        grouped[(row['case'], row['workers'], row['cache_mode'], row['variant'])].append(row)
        matched[(row['lane'], row['case'], row['workers'], row['cache_mode'], row['repeat'])][row['variant']] = row
    summaries = []
    for (case, workers, cache_mode, variant), group in sorted(grouped.items()):
        good = [x for x in group if x['success']]
        item = {'case': case, 'workers': workers, 'cache_mode': cache_mode, 'variant': variant,
                'attempted': len(group), 'passed': len(good)}
        for field in ['native_process_seconds', 'workflow_seconds', 'routing_seconds', 'critical_path_ns', 'wirelength', 'iterations']:
            item[field] = describe([x[field] for x in good])
        item['lookahead_seconds'] = describe([x['log_evidence']['stage_seconds']['lookahead_build'] for x in good])
        item['peak_rss_mib'] = describe([x['cpu_budget_audit']['peak_observed_hwm_kib'] / 1024 for x in good])
        # Five-second /proc sampling can miss a short run's peak. VPR also
        # reports its own process high-water mark at phase boundaries.
        native_peaks = []
        phase_values = defaultdict(list)
        remainders = []
        flow_values, external_gaps = [], []
        for row in good:
            text = (Path(row['directory']) / 'process.log').read_text(errors='replace')
            values = [float(v) for v in re.findall(r'max_rss ([\d.]+) MiB', text)]
            if values:
                native_peaks.append(max(values))
            flow = re.findall(r'The entire flow of VPR took ([\d.]+) seconds', text)
            if flow:
                flow_values.append(float(flow[-1]))
                external_gaps.append(row['native_process_seconds'] - float(flow[-1]))
            timed = top_level_timings(text, row['native_process_seconds'])
            for name, value in timed['top_level_seconds'].items():
                phase_values[name].append(value)
            remainders.append(timed['unscoped_seconds'])
        item['vpr_reported_peak_rss_mib'] = describe(native_peaks)
        item['top_level_timer_seconds'] = {name: describe(values) for name, values in phase_values.items()}
        item['unscoped_wall_seconds'] = describe(remainders)
        item['vpr_reported_flow_seconds'] = describe(flow_values)
        item['external_clock_gap_seconds'] = describe(external_gaps)
        summaries.append(item)
    pairs = []
    for (lane, case, workers, cache_mode, repeat), variants in sorted(matched.items()):
        for ref, cand in [('fixed', 'optimized'), ('original', 'fixed'), ('original', 'optimized'),
                          ('fixed', 'fixed_decomp'), ('fixed', 'fixed_compressed'),
                          ('fixed', 'fixed_mq'), ('optimized', 'tasks'), ('fixed', 'tasks'),
                          ('original', 'tasks'), ('original_decomp', 'fixed'),
                          ('original_decomp', 'optimized'), ('original_decomp', 'tasks'),
                          ('optimized', 'refactored'), ('refactored', 'tasks'),
                          ('fixed_decomp', 'optimized'), ('fixed_compressed', 'optimized')]:
            if ref in variants and cand in variants:
                pairs.append({'case': case, 'workers': workers, 'cache_mode': cache_mode,
                              'lane': lane, 'repeat': repeat, 'contrast': ref + ':' + cand,
                              **compare(variants[ref], variants[cand])})
    headline = []
    for case in sorted({x['case'] for x in rows}):
        for mode in ['rebuild', 'reuse']:
            group = [x for x in pairs if x['case'] == case and x['workers'] == 4 and x['cache_mode'] == mode and x['contrast'] == 'fixed:optimized']
            accepted = [x for x in group if x['eligible'] and x['quality_pass']]
            headline.append({'case': case, 'cache_mode': mode, 'pairs': len(group), 'accepted': len(accepted),
                             'process_speedup': describe([x['process_speedup'] for x in accepted]),
                             'workflow_speedup': describe([x['workflow_speedup'] for x in accepted]),
                             'route_bodies_equal': all(x['route_body_equal'] for x in accepted) if accepted else None})
    aggregates = {}
    for mode in ['rebuild', 'reuse']:
        eligible = [x for x in headline if x['cache_mode'] == mode and x['accepted'] >= 3]
        speedups = [x['process_speedup']['median'] for x in eligible]
        aggregates[mode] = {'cases': [x['case'] for x in eligible], 'geomean_paired_process_speedup': math.exp(sum(map(math.log, speedups)) / len(speedups)) if speedups else None,
                            'worst_case_median_speedup': min(speedups) if speedups else None}
    original_comparison = []
    for case in sorted({x['case'] for x in rows}):
        group = [x for x in pairs if x['case'] == case and x['workers'] == 4
                 and x['cache_mode'] == 'rebuild' and x['contrast'] == 'original:optimized']
        valid = [x for x in group if x['eligible']]
        accepted = [x for x in valid if x['quality_pass']]
        original_comparison.append({'case': case, 'pairs': len(group), 'valid': len(valid), 'quality_pass': len(accepted),
                                    'process_speedup': describe([x['process_speedup'] for x in accepted]),
                                    'cpd_change_percent': describe([x['cpd_change_percent'] for x in valid]),
                                    'wire_change_percent': describe([x['wire_change_percent'] for x in valid])})
    by_contrast = defaultdict(list)
    for pair in pairs:
        by_contrast[(pair['case'], pair['workers'], pair['cache_mode'], pair['contrast'])].append(pair)
    contrast_summaries = []
    for (case, workers, cache_mode, contrast), group in sorted(by_contrast.items()):
        valid = [x for x in group if x['eligible']]
        accepted = [x for x in valid if x['quality_pass']]
        contrast_summaries.append({'case': case, 'workers': workers, 'cache_mode': cache_mode, 'contrast': contrast,
                                   'pairs': len(group), 'valid': len(valid), 'accepted': len(accepted),
                                   'process_speedup': describe([x['process_speedup'] for x in accepted]),
                                   'workflow_speedup': describe([x['workflow_speedup'] for x in accepted]),
                                   'routing_speedup': describe([x['routing_speedup'] for x in accepted]),
                                   'lookahead_speedup': describe([x.get('lookahead_speedup') for x in accepted]),
                                   'cpd_change_percent': describe([x['cpd_change_percent'] for x in valid]),
                                   'wire_change_percent': describe([x['wire_change_percent'] for x in valid]),
                                   'route_bodies_equal': all(x['route_body_equal'] for x in valid) if valid else None})
    return {'plan': str(plan_path), 'status': 'completed' if all(x['status'] == 'completed' for x in lanes.values()) else 'incomplete',
            'planned': plan['planned_samples'], 'attempted': len(rows), 'successful': sum(x['success'] for x in rows),
            'failed': [{'lane': x['lane'], 'key': x['key'], 'returncode': x['returncode'], 'status': x['status'], 'directory': x['directory']} for x in rows if not x['success']],
            'lanes': lanes, 'summaries': summaries, 'pairs': pairs, 'headline': headline, 'aggregates': aggregates,
            'original_comparison': original_comparison,
            'contrast_summaries': contrast_summaries,
            'caveats': [plan['measurement_scope'], plan['concurrency_scope'], plan['repeats_scope'],
                        'Build-cache improvements are not routing-kernel acceleration; cache reuse is provided equally.',
                        'Failed routes are excluded from speedup ratios and remain part of the robustness result.']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = analyze(args.plan.resolve())
    write_json(args.output, report)
    print(json.dumps({k: report[k] for k in ['status', 'planned', 'attempted', 'successful', 'aggregates']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
