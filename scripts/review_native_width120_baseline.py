"""Independent terminal review of the nine conditional-subset baseline runs."""
from collections import defaultdict
import json
from pathlib import Path

from prepare import sha256, write_json
from qualify_native_cpu_width120 import quality
from report_native_joint import log_evidence
from run_native_hybrid import route_body
from scaling_common import metrics, verified

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_cpu_width120_baseline_20261104'


def read(p): return json.loads(Path(p).read_text())
def binding(p): return dict(path=str(Path(p).resolve()), sha256=sha256(p))


def main():
    state = read(OUT/'summary.json'); plan = read(OUT/'plan.json'); audit = read(OUT/'audit.json')
    assert state['status'] == 'completed' and audit['status'] == 'passed'
    assert read(OUT/'acceptance.json')['status'] == 'passed'
    assert len(state['measurements']) == len(plan['jobs']) == 9
    verified(state['plan_binding'])
    for path, digest in audit['bindings'].items(): assert sha256(path) == digest, path
    for category in ['runner_bindings', 'binaries']:
        for entry in plan[category].values(): verified(entry)
    for key in ['runtime', 'source_component_plan', 'source_component_review', 'source_six_layout_summary']: verified(plan[key])
    inputs = {}
    for entry in plan['cases'].values():
        for key in ['case', 'cache', 'reference']: verified(entry[key])
        for e in read(entry['case']['path'])['inputs'].values(): inputs[e['path']] = e
    for e in inputs.values(): verified(e)
    groups = defaultdict(list)
    for row, job in zip(state['measurements'], plan['jobs']):
        assert all(row[k] == job[k] for k in ['key', 'case', 'repeat', 'command', 'independent_command'])
        d = Path(row['directory']); native = metrics((d/'process.log').read_text())
        independent = metrics((d/'independent/process.log').read_text())
        assert row['success'] and row['returncode'] == row['independent_check']['returncode'] == 0
        assert native['routing_success'] and native['full_check'] and independent['full_check']
        assert all(native[k] == independent[k] == row[k] for k in ['critical_path_ns', 'wirelength'])
        assert native['iterations'] == row['iterations'] and log_evidence(d)['final_overused_nodes'] == 0
        assert sha256(d/'wire_map.bin') == plan['cases'][row['case']]['cache']['sha256']
        assert sha256(d/'routed.route') == row['route_sha256'] and route_body(d/'routed.route') == row['route_body_sha256']
        for proc, command in [(row, job['command']), (row['independent_check'], job['independent_command'])]:
            assert proc['actual_process']['command'] == command
            assert proc['actual_process']['environment'] == dict(LC_ALL='C', OMP_NUM_THREADS='1', **plan['environment'])
            assert proc['actual_process']['cpu_set'] == proc['cpu_budget_audit']['permitted_cpu_set'] == plan['cpu_pool']
            assert proc['cpu_budget_audit']['verified']
        q = quality(row, plan['cases'][row['case']]['reference_metrics'])
        assert q == row['quality'] and q['passed']
        groups[row['case']].append(row)
    observed = {case: dict(repeats=len(rs), iterations=[r['iterations'] for r in rs],
        critical_paths=sorted({r['critical_path_ns'] for r in rs}), wirelengths=sorted({r['wirelength'] for r in rs}),
        route_body_variants=len({r['route_body_sha256'] for r in rs})) for case, rs in groups.items()}
    assert all(g['repeats'] == 3 for g in observed.values())
    result = dict(status='passed', artifacts=len(audit['bindings']), legal=9, quality_passed=9, groups=observed,
        route_determinism_claim=False, performance_claim=False, default_changed=False,
        interpretation='Repeated conditional feasibility and QoR passed. BNN route bodies vary; BNN_s2 wirelength differs by4. Do not require or claim route identity, and do not change the original width100 gate.',
        next='Freeze12 four-arm rebuild qualifications, then conditionally72 fresh rebuild/reuse paired measurements on the exact same three layouts. No failed-layout replacement.',
        sources={n: binding(OUT/n) for n in ['summary.json', 'plan.json', 'acceptance.json', 'audit.json']}, reviewer=binding(__file__))
    write_json(OUT/'independent_review.json', result)
    write_json(OUT/'conclusions.json', result)
    print(json.dumps(dict(status='passed', artifacts=len(audit['bindings']), groups=observed)), flush=True)


if __name__ == '__main__': main()
