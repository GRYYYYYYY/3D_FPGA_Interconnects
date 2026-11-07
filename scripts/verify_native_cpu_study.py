"""Audit terminal studies against retained logs, routes, maps and frozen files."""
import argparse
import json
from pathlib import Path

from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_hybrid import route_body
from scaling_common import metrics, verified


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--plan', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    bindings = {}
    receipt = {'status': 'running', 'studies': [], 'errors': []}

    def check(condition, message):
        if not condition:
            receipt['errors'].append(message)

    def bind(entry):
        path = str(Path(entry['path']).resolve())
        check(path not in bindings or bindings[path] == entry['sha256'], 'Conflicting binding: ' + path)
        bindings[path] = entry['sha256']

    for plan_path in args.plan:
        plan_path = plan_path.resolve()
        plan = json.loads(plan_path.read_text())
        root = Path(plan['output'])
        study = {'plan': str(plan_path), 'attempted': 0, 'successful': 0, 'skipped': 0,
                 'cache_qualifications': 0, 'maps_checked': 0, 'lanes': {}}
        receipt['studies'].append(study)
        for entry in list(plan['binaries'].values()) + list(plan.get('runner_bindings', {}).values()):
            bind(entry)
        runtime = json.loads(Path(plan['runtime']).read_text())
        for entry in runtime['libraries']:
            bind(entry)
        for name, lane_plan in plan['lanes'].items():
            summary = json.loads((root / name / 'summary.json').read_text())
            check(summary['status'] == 'completed', 'Unfinished lane: ' + name)
            check(summary['plan_sha256'] == sha256(plan_path), 'Changed plan: ' + str(plan_path))
            study['lanes'][name] = summary['status']
            study['skipped'] += len(summary['skipped'])
            cases = {c['id']: json.loads(Path(c['vpr_case']).read_text()) for c in lane_plan['cases']}
            serial_maps = {}
            for c in summary['cache_qualifications']:
                check(c['status'] == 'passed', 'Unqualified cache: ' + name + '/' + c['case'])
                hashes = []
                for b in c['builders']:
                    entry = {'path': b['cache'], 'sha256': b['sha256']}
                    bind(entry)
                    hashes.append(entry['sha256'])
                    check(b['cpu_budget_audit']['verified'], 'Cache builder affinity: ' + name)
                check(len(hashes) == 2 and len(set(hashes)) == 1, 'Cache byte mismatch: ' + name)
                if hashes:
                    serial_maps[c['case']] = hashes[0]
                study['cache_qualifications'] += 1
            for row in summary['measurements']:
                study['attempted'] += 1
                directory = Path(row['directory'])
                saved = json.loads((directory / 'measurement.json').read_text())
                check(saved == row, 'Summary differs from measurement: ' + row['key'])
                check(row['workers'] == row['cpu_budget']['cores'] == len(row['cpu_budget']['cpu_set']), 'CPU budget mismatch: ' + row['key'])
                check(row['cpu_budget_audit']['permitted_cpu_set'] == row['cpu_budget']['cpu_set'], 'Wrong affinity: ' + row['key'])
                check(row['cpu_budget_audit']['verified'], 'Affinity violation: ' + row['key'])
                for entry in row['inputs'].values():
                    bind(entry)
                command = row['command']
                for option, value in [('route_chan_width', cases[row['case']]['route_chan_width']),
                                      ('device_width', cases[row['case']]['device_width']),
                                      ('seed', cases[row['case']]['seed']), ('num_workers', row['workers'])]:
                    check(command[command.index('--' + option) + 1] == str(value), 'Command setting mismatch: ' + row['key'] + '/' + option)
                variant = plan['variants'][row['variant']]
                binary = plan['binaries'][variant['binary']]
                check(row['binary_sha256'] == binary['sha256'], 'Wrong binary: ' + row['key'])
                check(Path(row['command'][0]).resolve() == Path(binary['path']).resolve(), 'Wrong executable command: ' + row['key'])
                if 'lookahead_scheduler' in row:
                    task_mode = (Path(binary['path']).resolve() == Path(plan['binaries']['cpu']['path']).resolve()
                                 and variant['parallel'])
                    expected_scheduler = 'global_ordered_pipeline' if task_mode else 'per_group_samples' if variant['parallel'] else 'serial'
                    check(row['lookahead_scheduler'] == expected_scheduler, 'Wrong scheduler: ' + row['key'])
                if row.get('wire_map_sha256'):
                    command = row['command']
                    map_path = command[command.index('--write_router_lookahead') + 1]
                    bind({'path': map_path, 'sha256': row['wire_map_sha256']})
                    check(row['wire_map_matches_serial'], 'Non-equivalent map: ' + row['key'])
                    check(row['wire_map_sha256'] == serial_maps.get(row['case']), 'Wrong serial map reference: ' + row['key'])
                    study['maps_checked'] += 1
                if not row['success']:
                    # Numerical failures are part of the result, not audit failures.
                    continue
                study['successful'] += 1
                native = metrics((directory / 'process.log').read_text(errors='replace'))
                independent = metrics((directory / 'independent_check.log').read_text(errors='replace'))
                check(native['routing_success'] and native['full_check'] and independent['full_check'], 'Missing FULL pass: ' + row['key'])
                check(log_evidence(directory)['final_overused_nodes'] == 0, 'Nonzero overuse: ' + row['key'])
                check(row['independent_check']['returncode'] == 0 and row['independent_check']['cpu_budget_audit']['verified'], 'Bad independent check: ' + row['key'])
                for key in ['critical_path_ns', 'wirelength']:
                    check(native[key] == independent[key] == row[key], 'STA/quality mismatch: ' + row['key'])
                bind({'path': str(directory / 'routed.route'), 'sha256': row['route_sha256']})
                check(route_body(directory / 'routed.route') == row['route_body_sha256'], 'Changed route body: ' + row['key'])
        derived = sum(len(q['variants']) * len(q['workers']) * len(q['cache_modes']) * q['repeats']
                      for lane in plan['lanes'].values() for case in lane['cases'] for q in case['phases'])
        check(derived == plan.get('planned_samples', derived), 'Declared plan count mismatch: ' + str(plan_path))
        check(study['attempted'] + study['skipped'] == derived, 'Plan accounting mismatch: ' + str(plan_path))
    for path, expected in bindings.items():
        try:
            verified({'path': path, 'sha256': expected})
        except Exception as exc:
            receipt['errors'].append(str(exc))
    receipt.update(status='passed' if not receipt['errors'] else 'failed', frozen_files_checked=len(bindings), bindings=bindings)
    write_json(args.output, receipt)
    print(json.dumps({k: receipt[k] for k in ['status', 'studies', 'errors', 'frozen_files_checked']}, ensure_ascii=False))
    if receipt['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
