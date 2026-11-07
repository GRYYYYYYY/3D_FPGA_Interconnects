"""Audit formal-mode attribution and summarize completed native slice experiments.

This is an offline consumer. It never starts a solver or changes a frozen plan.
Run report_native_cpu_slices.py and verify_native_cpu_study.py first.
"""
from collections import defaultdict
from datetime import datetime, timezone
import itertools
import json
from pathlib import Path
import statistics

from prepare import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/native_cpu_slices_20261101'


def load(path):
    return json.loads(path.read_text())


def counters(text):
    return {k: int(v) for k, v in (line.split() for line in text.splitlines())}


def main():
    analysis = load(OUT / 'analysis.json')
    evidence = load(OUT / 'evidence_verification.json')
    plan = load(OUT / 'confirmation_plan.json')
    if analysis['status'] != 'complete' or evidence['status'] != 'passed':
        raise RuntimeError('Complete analysis and successful retained-evidence audit required')
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    check(sum(s['planned'] for s in analysis['stages']) == 171, 'Unexpected full study size')
    check(all(s['completed'] == s['planned'] for s in analysis['stages']), 'Incomplete preceding stage')
    check(analysis['successful_maps'] == analysis['successful_routes'] == 171, 'Full study equivalence/legality incomplete')
    formal = []
    actual_orders = {}
    lane_physical_cores = {}
    for lane, spec in plan['lanes'].items():
        summary = load(Path(plan['output']) / lane / 'summary.json')
        check(summary['status'] == 'completed', 'Unfinished lane: ' + lane)
        rows = summary['measurements']
        formal.extend(rows)
        topology = rows[0]['cpu_budget']['topology']
        lane_physical_cores[lane] = {(t['socket'], t['core']) for t in topology}
        check(len(lane_physical_cores[lane]) == len(spec['cpu_pool']), 'SMT duplicate within lane: ' + lane)
        check(len({t['node'] for t in topology}) == 1, 'Lane crosses NUMA nodes: ' + lane)
        expected = []
        for case in spec['cases']:
            for phase in case['phases']:
                for repeat in range(phase.get('repeat_start', 0), phase.get('repeat_start', 0) + phase['repeats']):
                    for workers in phase['workers']:
                        for cache in phase['cache_modes']:
                            for variant in phase['intended_execution_order']:
                                expected.append((case['id'], workers, cache, repeat, variant))
        observed = [(r['case'], r['workers'], r['cache_mode'], r['repeat'], r['variant']) for r in rows]
        check(observed == expected, 'Execution order differs from declared order: ' + lane)
        actual_orders[lane] = observed
        for row in rows:
            check(row['cpu_budget']['cpu_set'] == spec['cpu_pool'], 'CPU set mismatch: ' + row['key'])
    physical_union = set().union(*lane_physical_cores.values())
    check(len(physical_union) == sum(map(len, lane_physical_cores.values())) == 48,
          'Formal lanes overlap physical cores or exceed declared budget')
    dimensions = ('case', 'workers', 'cache_mode', 'repeat', 'variant')
    actual = [tuple(row[k] for k in dimensions) for row in formal]
    expected = set(itertools.product(['gemm', 'elliptic'], [4, 8], ['rebuild', 'reuse'], range(3),
                                    ['frozen', 'slice', 'compact', 'pipeline', 'bounded']))
    check(len(actual) == 120 and len(set(actual)) == 120 and set(actual) == expected, 'Formal matrix coverage')
    maps = defaultdict(set)
    quality = defaultdict(lambda: defaultdict(set))
    by_config = defaultdict(list)
    resource_deltas = []
    for row in formal:
        key = row['key']
        check(row['success'], 'Unsuccessful native sample: ' + key)
        check(not row['diagnostic_sample'] and not row['execution_settings']['diagnostics'], 'Diagnostic formal row: ' + key)
        expected_env = {'VPR_HYBRID_LOOKAHEAD_PARALLEL': '1', **plan['variants'][row['variant']].get('env', {})}
        check(row['candidate_environment'] == expected_env, 'Environment attribution mismatch: ' + key)
        check(not (Path(row['directory']) / 'cpu_trace.jsonl').exists(), 'Unexpected trace: ' + key)
        check(not (Path(row['directory']) / 'lookahead_profile.jsonl').exists(), 'Unexpected profile: ' + key)
        check(not row['execution_settings']['gpu_enabled'], 'Unexpected GPU mode: ' + key)
        cache = row['lookahead_cache_sha256']
        check((cache is None) if row['cache_mode'] == 'rebuild' else cache == row['wire_map_sha256'],
              'Cache input/output mismatch: ' + key)
        maps[row['case']].add(row['wire_map_sha256'])
        for field in ['critical_path_ns', 'wirelength', 'route_body_sha256', 'iterations']:
            quality[(row['case'], row['workers'])][field].add(row[field])
        by_config[(row['case'], row['workers'], row['cache_mode'], row['variant'])].append(row)
        audit = row['cpu_budget_audit']
        delta = {'key': key}
        for filename in ['cpu.stat', 'memory.events']:
            name = '/sys/fs/cgroup/' + filename
            before = counters(audit['cgroup_before'][name])
            after = counters(audit['cgroup_after'][name])
            delta[filename] = {k: after[k] - v for k, v in before.items() if k in after}
        resource_deltas.append(delta)
    check(all(len(hashes) == 1 for hashes in maps.values()), 'Maps differ between lanes/variants for one case')
    check(all(p['valid_pairs'] == 3 for p in analysis['paired_comparisons'])
          and len(analysis['paired_comparisons']) == 56, 'Incomplete paired comparisons')
    bindings = load(OUT / 'aligned_source/bindings.json')
    for relative, expected_hash in bindings.items():
        for directory in [OUT / 'aligned_source', ROOT / 'vendor/vtr_cpu_slices']:
            check(sha256(directory / relative) == expected_hash, 'Changed aligned source: ' + str(directory / relative))
    layout = load(OUT / 'aligned_implementation_audit.json')
    check(layout['status'] == 'passed', 'Alignment implementation audit failed')
    check(sha256(OUT / 'aligned_source/bindings.json') == layout['source_bindings_sha256'], 'Changed source binding file')
    check(sha256(OUT / 'workspace_alignment.patch') == layout['patch_sha256'], 'Changed alignment patch')

    configs = []
    for (case, workers, cache, variant), rows in sorted(by_config.items()):
        stages = defaultdict(list)
        for row in rows:
            for name, value in row['log_evidence']['stage_seconds'].items():
                if value is not None:
                    stages[name].append(value)
        configs.append({'case': case, 'workers': workers, 'cache_mode': cache, 'variant': variant,
                        'n': len(rows), 'process_median_seconds': statistics.median(r['native_process_seconds'] for r in rows),
                        'workflow_median_seconds': statistics.median(r['workflow_seconds'] for r in rows),
                        'stage_medians_seconds': {k: statistics.median(v) for k, v in stages.items()},
                        'peak_hwm_kib': [r['cpu_budget_audit']['peak_observed_hwm_kib'] for r in rows]})
    supplemental = {
        'status': 'passed' if not errors else 'failed', 'errors': errors,
        'formal_samples': len(formal), 'distinct_configurations': len(configs),
        'distinct_physical_cores': len(physical_union),
        'lane_physical_cores': {k: sorted(v) for k, v in lane_physical_cores.items()},
        'actual_execution_orders': actual_orders, 'effective_environments_match_frozen_plan': not errors,
        'all_formal_diagnostics_disabled': all(not r['diagnostic_sample'] for r in formal),
        'maps_by_case': {k: sorted(v) for k, v in maps.items()},
        'quality_by_case_workers': [dict(case=k[0], workers=k[1], **{f: sorted(v) for f, v in fields.items()})
                                   for k, fields in sorted(quality.items())],
        'configurations': configs, 'resource_deltas': resource_deltas,
        'resource_note': 'Cgroup counters cover all overlapping jobs. Intervals overlap; do not sum per-row deltas. HWM is sampled, not a temporary-map allocation counter.',
        'aligned_source_files_checked': len(bindings),
    }
    write_json(OUT / 'formal_attribution_audit.json', supplemental)
    if errors:
        raise RuntimeError('; '.join(errors))

    primary = [p for p in analysis['paired_comparisons'] if p['control'] == 'frozen' and p['candidate'] == 'bounded']
    decision_rows = []
    for p in primary:
        main = p['case'] == 'gemm' and p['cache_mode'] == 'rebuild'
        passed = (p['process_ratio']['min'] > 1 and p['process_ratio']['median'] > 1.02) if main else p['process_ratio']['median'] >= 1 / 1.02
        decision_rows.append({k: p[k] for k in ['case', 'workers', 'cache_mode', 'process_ratio']} |
                             {'passed': passed, 'criterion': 'all three >1 and median >1.02' if main else 'median >= 1/1.02'})
    recomputed_promotion = all(r['passed'] for r in decision_rows) and not analysis['failures']
    if recomputed_promotion != analysis['promotion_rule_passed']:
        raise RuntimeError('Promotion rule disagrees with independent recomputation')
    acceptance = {
        'status': 'complete', 'completed_utc': datetime.now(timezone.utc).isoformat(),
        'planned_native_samples': sum(s['planned'] for s in analysis['stages']),
        'completed_native_samples': sum(s['completed'] for s in analysis['stages']),
        'successful_native_samples': analysis['successful_routes'], 'formal_samples': len(formal),
        'maps_equal_to_original_serial': analysis['successful_maps'],
        'retained_evidence_audit': evidence['status'], 'formal_attribution_audit': supplemental['status'],
        'promotion_rule_passed': recomputed_promotion, 'promotion_checks': decision_rows,
        'default_changed': False, 'gpu_jobs_submitted': 0,
        'control_identity': 'Frozen improved CPU implementation with per-group parallel sampling, not raw original VPR',
        'selection_scope': 'Predeclared conservative engineering gate; shared-host runtime repeats are not a statistical confidence interval',
    }
    write_json(OUT / 'acceptance.json', acceptance)
    selected = [p for p in analysis['paired_comparisons']
                if (p['control'], p['candidate']) in [('frozen', 'bounded'), ('frozen', 'pipeline'), ('pipeline', 'bounded')]]
    conclusions = {
        'status': 'complete', 'selection': 'retain_existing_per_group_cpu_mainline' if not recomputed_promotion else 'bounded_eligible_for_independent_confirmation',
        'default_changed': False, 'promotion_rule_passed': recomputed_promotion,
        'control_identity': acceptance['control_identity'],
        'selected_comparisons': selected,
        'established': ['Native slice reordering and scalar SMALLEST representation preserve serialized maps in tested cases',
                        'Bounded implementation limits active map and workspace object counts, not total RSS',
                        'The historical approximately 12-second refactoring regression was not reproduced in D0',
                        'Same-binary layout isolation supports contention from diagnostic counters; this is not unprofiled algorithm acceleration'],
        'not_established': ['New bounded method consistently outperforms existing global pipeline',
                            'A new 3D pathfinding algorithm or a first-in-literature claim',
                            'Root cause of the historical approximately 12-second regression',
                            'GPU-specific improvement or an automatic CPU/GPU takeover rule'],
        'proposed_next_work_not_started': ['Independently confirm the existing 8-core pipeline on isolated resources and held-out circuits/placements',
                                          'If bounded scheduling remains a candidate, measure 8-core batch-tail and workspace lifetime costs separately from diagnostics overhead',
                                          'Treat repeated-start reuse as an unimplemented candidate requiring exact semantic and complete-process validation'],
        'limitations': analysis['limitations'],
    }
    write_json(OUT / 'conclusions.json', conclusions)
    print(json.dumps({'audit': supplemental['status'], 'formal_samples': len(formal),
                      'all_native_samples': acceptance['completed_native_samples'],
                      'promotion_rule_passed': recomputed_promotion}, ensure_ascii=False))


if __name__ == '__main__':
    main()
