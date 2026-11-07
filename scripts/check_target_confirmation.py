#!/usr/bin/env python3
"""Evaluate every paired repeat against its predeclared full-workflow criteria."""
import argparse
import json
import math
from pathlib import Path
import statistics

from prepare import sha256, write_json
from verify_target_run import verify


def evaluate(summary, protocol):
    if summary['status'] != 'completed':
        raise ValueError('Confirmation experiment is still incomplete')
    actual = summary['protocol']
    fields = {'repeats': 'repeats', 'epochs': 'epochs',
              'refine_threshold': 'refine_threshold',
              'refine_connections': 'refine_connections',
              'bootstrap_congestion_mode': 'congestion_mode',
              'refine_mode': 'refine_mode'}
    if any(protocol[k] != actual[v] for k, v in fields.items()):
        raise ValueError('Measured configuration differs from declared protocol')
    if not actual['incremental_target'] or not protocol['all_pairs_must_pass']:
        raise ValueError('Expected persistent refinement and all-pair acceptance')
    if protocol['variant_order'] != 'rotate vpr,target each repeat':
        raise ValueError('Unsupported ordering protocol')
    if [c['id'] for c in summary['cases']] != [protocol['case']]:
        raise ValueError('Confirmation case mismatch')
    rows = summary['rows']
    expected = [(protocol['case'], variant, repeat)
                for repeat in range(protocol['repeats'])
                for variant in (['vpr', 'target'] if repeat % 2 == 0 else ['target', 'vpr'])]
    if [(r['case'], r['variant'], r['repeat']) for r in rows] != expected:
        raise ValueError('Missing, duplicated, or reordered attempts')
    pairs = []
    for repeat in range(protocol['repeats']):
        pair = {r['variant']: r for r in rows if r['repeat'] == repeat}
        baseline, target = pair['vpr'], pair['target']
        item = {'repeat': repeat, 'passed': False,
                'legal': all(r.get('success') and r.get('full_check') for r in pair.values())}
        if item['legal']:
            for row in pair.values():
                for key in ('workflow_seconds', 'critical_path_ns', 'wirelength'):
                    value = row[key]
                    if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                        raise ValueError('Invalid measurement: ' + key)
            item.update(
                vpr_workflow_seconds=baseline['workflow_seconds'],
                target_workflow_seconds=target['workflow_seconds'],
                workflow_speedup=baseline['workflow_seconds'] / target['workflow_seconds'],
                cpd_change_percent=100 * (target['critical_path_ns'] / baseline['critical_path_ns'] - 1),
                wire_change_percent=100 * (target['wirelength'] / baseline['wirelength'] - 1))
            limit = protocol['quality_budget_percent']
            item['quality_passed'] = all(target[k] <= baseline[k] * (1 + limit / 100)
                                         for k in ('critical_path_ns', 'wirelength'))
            item['speed_passed'] = item['workflow_speedup'] > 1
            item['passed'] = item['quality_passed'] and (item['speed_passed'] or not protocol['workflow_speedup_required'])
        pairs.append(item)
    speedups = [p['workflow_speedup'] for p in pairs if p['legal']]
    return {'status': 'passed' if all(p['passed'] for p in pairs) else 'failed',
            'case': protocol['case'], 'pairs': pairs,
            'median_paired_workflow_speedup': statistics.median(speedups) if speedups else None,
            'minimum_paired_workflow_speedup': min(speedups) if speedups else None,
            'quality_budget_percent': protocol['quality_budget_percent'],
            'not_a_scaling_crossover_claim': True}


def check(pointer_path):
    pointer = json.loads(Path(pointer_path).read_text())
    protocol_path = Path(pointer['protocol'])
    if sha256(protocol_path) != pointer['protocol_sha256']:
        raise ValueError('Predeclared protocol was modified')
    protocol = json.loads(protocol_path.read_text())
    run = Path(pointer['run'])
    summary = json.loads((run / 'summary.json').read_text())
    result = evaluate(summary, protocol)
    artifacts = verify(run)
    for repeat in range(protocol['repeats']):
        rows = {r['variant']: r for r in summary['rows'] if r['repeat'] == repeat}
        baseline = rows['vpr']
        if not baseline.get('success'):
            continue
        reference = baseline['command']
        for epoch in rows['target'].get('epochs', []):
            if not epoch.get('success'):
                continue
            command = epoch['validation']['command']
            if command[:3] != reference[:3]:
                raise ValueError('VPR binary, architecture, or circuit mismatch')
            for flag in ('--seed', '--route_chan_width', '--device_width', '--num_workers'):
                if command[command.index(flag) + 1] != reference[reference.index(flag) + 1]:
                    raise ValueError('Fixed constraint differs: ' + flag)
            for flag in ('--net_file', '--place_file', '--read_rr_graph'):
                left = Path(command[command.index(flag) + 1])
                right = Path(reference[reference.index(flag) + 1])
                if left.resolve() != right.resolve() and sha256(left) != sha256(right):
                    raise ValueError('Fixed input differs: ' + flag)
            initial = epoch['command']
            if int(initial[initial.index('--bootstrap-criticality') + 1]) != protocol['bootstrap_criticality']:
                raise ValueError('Bootstrap criticality mismatch')
    result.update(summary_sha256=artifacts['summary_sha256'],
                  protocol_sha256=pointer['protocol_sha256'],
                  artifact_verification_sha256=sha256(run / 'artifact_verification.json'),
                  job_id=pointer['job_id'], hostname=summary['hostname'],
                  timing_scope=protocol['timing_scope'], input_scope=protocol['input_scope'])
    write_json(run / 'confirmation.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pointer', type=Path, required=True)
    result = check(parser.parse_args().pointer)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)
