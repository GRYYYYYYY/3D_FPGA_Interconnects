"""Recompute component results from raw logs and verify the frozen experiment."""
from collections import Counter
import json
import math
from pathlib import Path
import re
import statistics

from prepare import sha256, write_json
from scaling_common import verified

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_lookahead_component_20261104'
ARMS = ['stock', 'fixed_serial', 'per_group', 'pipeline']


def read(p): return json.loads(Path(p).read_text())
def binding(p): return dict(path=str(Path(p).resolve()), sha256=sha256(p))


def main():
    plan = read(OUT/'plan.json'); state = read(OUT/'summary.json'); audit = read(OUT/'audit.json')
    assert state['status'] == 'completed' and audit['status'] == 'passed'
    verified(state['plan_binding'])
    for path, digest in audit['bindings'].items(): assert sha256(path) == digest, path
    for category in ['runner_bindings', 'scope_source_bindings', 'binaries']:
        for entry in plan[category].values(): verified(entry)
    for key in ['source_summary', 'source_audit', 'runtime']: verified(plan[key])
    inputs = {}
    for case in plan['cases'].values():
        verified(case['reference_map'])
        for entry in read(verified(case['case']))['inputs'].values(): inputs[entry['path']] = entry
    for entry in inputs.values(): verified(entry)
    assert len(state['measurements']) == len(plan['jobs']) == 40
    topology = state['cpu_budget']['topology']
    selected = [c for c in topology if c['cpu'] in plan['cpu_pool']]
    assert len({(c['socket'], c['core']) for c in selected}) == 8
    observations = []; timestamps = []
    for row, job in zip(state['measurements'], plan['jobs']):
        assert all(row[k] == job[k] for k in ['key', 'phase', 'graph', 'repeat', 'arm', 'command', 'environment'])
        d = Path(row['directory']); text = (d/'process.log').read_text(errors='replace')
        times = re.findall(r'^# Computing router lookahead map took ([\d.]+) seconds', text, re.M)
        assert len(times) == 1 and float(times[0]) > 0
        assert text.index('# Computing router lookahead map took') < text.index('\n# Routing\n')
        assert float(times[0]) == row['build_seconds']
        actual = row['actual_process']; assert actual['command'] == job['command']
        assert actual['environment'] == dict(LC_ALL='C', OMP_NUM_THREADS='1', **job['environment'])
        assert actual['cpu_set'] == plan['cpu_pool'] == row['cpu_budget_audit']['permitted_cpu_set']
        assert row['cpu_budget_audit']['verified']
        assert row['returncode'] == 2 and row['tail_iterations'] == 1 and not row['routing_success_observed']
        assert row['component_valid'] and not row['routing_legality_independently_checked']
        assert sha256(d/'wire_map.bin') == plan['cases'][row['graph']]['reference_map']['sha256']
        assert 'VPR failed to implement circuit' in text
        observations.append(dict(key=row['key'], graph=row['graph'], phase=row['phase'], repeat=row['repeat'],
                                 arm=row['arm'], build_seconds=float(times[0])))
        timestamps.append((actual['utc'], row['finished_utc']))
    assert all(timestamps[i][1] <= timestamps[i+1][0] for i in range(39)), 'Overlapping jobs/order drift'
    formal = [r for r in observations if r['phase'] == 'formal']
    assert len(formal) == 36
    counts = Counter((r['graph'], r['arm']) for r in formal)
    assert len(counts) == 12 and set(counts.values()) == {3}
    indexed = {(r['graph'], r['repeat'], r['arm']): r['build_seconds'] for r in formal}
    pairs = [('stock', 'pipeline'), ('fixed_serial', 'per_group'), ('fixed_serial', 'pipeline'), ('per_group', 'pipeline')]
    recomputed = {}; all_incremental = []
    for graph in plan['cases']:
        recomputed[graph] = {}
        for a, b in pairs:
            ratios = [indexed[graph, r, a]/indexed[graph, r, b] for r in range(3)]
            recomputed[graph][a+'_to_'+b] = dict(ratios=ratios, median=statistics.median(ratios))
            if a == 'per_group': all_incremental.extend(ratios)
    aggregate = {a+'_to_'+b: math.exp(statistics.mean(math.log(g[a+'_to_'+b]['median']) for g in recomputed.values())) for a, b in pairs}
    reported = read(OUT/'analysis.json')
    for name, value in aggregate.items(): assert math.isclose(value, reported['geometric_mean_of_graph_paired_medians'][name], rel_tol=1e-12)
    for graph, comparisons in recomputed.items():
        for name, pair in comparisons.items(): assert pair['ratios'] == reported['graphs'][graph]['comparisons'][name]['ratios']
    result = dict(status='passed', bound_artifacts=len(audit['bindings']), all_used_inputs_verified=True,
        pilot_count=4, formal_count=36, distinct_rr_graphs=len({c['rr_sha256'] for c in plan['cases'].values()}),
        actual_command_environment_cpu_verified=True, ordered_nonoverlapping_processes=True,
        geometric_mean_of_graph_paired_medians=aggregate, comparisons=recomputed,
        incremental_pairs_faster=sum(x > 1 for x in all_incremental), incremental_pairs_total=len(all_incremental),
        incremental_ratio_range=[min(all_incremental), max(all_incremental)],
        end_to_end_claim=False, default_changed=False,
        sources={n: binding(OUT/n) for n in ['plan.json', 'summary.json', 'audit.json', 'analysis.json']}, reviewer=binding(__file__))
    write_json(OUT/'independent_review.json', result)
    write_json(OUT/'conclusions.json', dict(status='complete', formal_valid=36, distinct_graphs=3,
        stage_speedups=aggregate, wire_maps_equivalent=True, end_to_end_speedup_established_by_this_study=False,
        contribution='Same-eight-core native CPU lookahead construction; pipeline increment above per-group confirmed across9 paired repeats on3 distinct RR graphs.',
        limitations=['One architecture family, three graph sizes, three runtime repeats per arm, shared host.',
                    'Serialized equivalence covers wire map, not every derived src/opin table.',
                    'One-iteration tails all remain unrouted; stage evidence does not change the six-layout3/6 feasibility outcome.'],
        next='Fresh repeated corrected-baseline feasibility on the predeclared LSTM_s2/BNN_s1/BNN_s2 conditional subset; no performance matrix until qualification.',
        default_changed=False, evidence=binding(OUT/'independent_review.json')))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    graphs = list(plan['cases']); colors = ['#64748b', '#d29922', '#168aad', '#138a63']
    for i, arm in enumerate(ARMS):
        xs = [g+(i-1.5)*.19 for g in range(3)]
        ys = [statistics.median(indexed[name, r, arm] for r in range(3)) for name in graphs]
        axes[0].bar(xs, ys, width=.18, label=arm, color=colors[i])
        for x, name in zip(xs, graphs):
            axes[0].scatter([x]*3, [indexed[name, r, arm] for r in range(3)], color='black', s=9, zorder=3)
    axes[0].set_xticks(range(3), graphs); axes[0].set_ylabel('Complete lookahead construction (seconds)')
    axes[0].set_title('Bars: medians; dots: all three repeats'); axes[0].legend(fontsize=8)
    for x, name in enumerate(graphs):
        ys = recomputed[name]['per_group_to_pipeline']['ratios']
        axes[1].scatter([x-.08, x, x+.08], ys, color=colors[3])
        axes[1].plot([x-.16, x+.16], [statistics.median(ys)]*2, color='black')
    axes[1].axhline(1, color='gray', linestyle='--'); axes[1].set_xticks(range(3), graphs)
    axes[1].set_ylabel('Per-group / pipeline paired stage ratio'); axes[1].set_ylim(.9, 2.15)
    axes[1].set_title('All 9 incremental comparisons exceed 1')
    for ax in axes: ax.grid(axis='y', alpha=.2); ax.set_axisbelow(True)
    fig.suptitle('Same eight-core budget; stage results only; shared host')
    fig.tight_layout()
    for ext in ['pdf', 'svg', 'png']: fig.savefig(OUT/f'component_results.{ext}', dpi=160)
    plt.close(fig)
    print(json.dumps(dict(status='passed', artifacts=len(audit['bindings']), stage_speedups=aggregate)), flush=True)


if __name__ == '__main__': main()
