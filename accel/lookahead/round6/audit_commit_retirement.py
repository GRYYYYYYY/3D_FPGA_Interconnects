#!/usr/bin/env python3
"""Read-only model retirement sensitivity, not a calibrated FPGA prediction."""
import argparse
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path

REPLACEMENT = '''                # Sensitivity: retirement does not consume another issue turn.
                if candidates:
                    candidate = candidates[0]
                    e = candidate['edge']
                    if candidate['phase'] == 'commit' and candidate['until'] <= t:
                        accepted = e['push'] is None or enqueue(x, 'U', e['push'], t)
                        if accepted:
                            assert e['ordinal'] == x['committed'] + 1
                            x['committed'] = e['ordinal']
                            stats['duplicate_dst_commits'] += e['dst'] in x['seen_dst']
                            x['seen_dst'].add(e['dst'])
                            candidates.popleft()
                            stats['commits'] += 1
                if candidates and commit_turn:
                    candidate = candidates[0]
                    if candidate['phase'] == 'ready' and candidate['until'] <= t and t >= commit_free:
                        candidate.update(phase='commit', until=t + c['commit_latency'])
                        commit_free = t + c.get('commit_issue_ii', c['commit_latency'])
'''


def main(root):
    source = root / 'scripts/la_accel_model5_1.py'
    spec = importlib.util.spec_from_file_location('r51_model', source)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    original = model.simulate
    text = inspect.getsource(original)
    start = text.index('                if candidates and commit_turn:')
    end = text.index("                if x['edge'] < len(edges):", start)
    exec(text[:start] + REPLACEMENT + text[end:], model.__dict__)
    snapshot = root / 'results/lookahead_accel_round5_1_20261109T072948Z/evidence_snapshot'
    data = json.loads((snapshot / 'model/parent_edge_service_model.json').read_text())
    manifest = json.loads((root / model.SNAPSHOT / 'workload_manifest.json').read_text())
    observer_path = snapshot / 'mechanism/observer_d_zero/result.json'
    observer = json.loads(observer_path.read_text())
    enqueue = [o['enqueue'] for o in observer['transactions'][0]['operations']
               if o['kind'] == 1 and o['qid'] == 0 and o['parent'] == 1]
    results = []
    for case, archive in [('native_d3_w8', 'lookahead_accel_round3_20261108T141500Z'),
                          ('native_d4_w8', 'lookahead_accel_round3_20261108T141500Z'),
                          ('native_d5_w8', 'lookahead_accel_round4_20261108T182500Z')]:
        row = next(x for x in data['candidates'] if x['case'] == case and
                   x['contract']['name'] == 'observer_d_baseline_pq_envelope_native_extrapolation')
        workload = dict(next(w for w in manifest if w['case'] == case))
        workload['path'] = str(root / 'results' / archive / 'evidence_snapshot' / case / 'workload.bin')
        queries, trace = model.read_trace(root, workload, snapshot / 'pq' / (case + '.csv.pop_path.csv'))
        baseline = original(queries, workload, row['contract'])
        assert baseline['batch_cycles'] == row['batch_cycles']
        changed = model.simulate(queries, workload, row['contract'])
        results.append(dict(case=case, original_model_cycles=row['batch_cycles'],
                            retirement_sensitivity_cycles=changed['batch_cycles'], trace=trace))
    return dict(
        source_commit='ab0a4afce89c567cf30f24c8a813d78884872f05',
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        observer_sha256=hashlib.sha256(observer_path.read_bytes()).hexdigest(),
        measured_rtl_enqueue_field='transactions[0].operations filtered by kind=1,qid=0,parent=1: enqueue',
        measured_rtl_same_qid_same_parent_enqueue_cycles=enqueue,
        evidence='Conditional model retirement sensitivity; no new hardware measurements',
        limits=[
            'Existing ready->commit and commit->retire both require the same round-robin issue turn.',
            'The replacement allows ordered retirement after latency independently of issue arbitration.',
            'This addresses one scheduling mismatch, but does not calibrate full native behavior or other model assumptions.',
            'Native hardware capacity, deep heap timing and frequency remain unverified.',
            'This is not a new performance candidate or evidence of CPU superiority.'
        ], results=results)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = main(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['results'], indent=2))
