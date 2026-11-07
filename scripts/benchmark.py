#!/usr/bin/env python3
"""Sequential, paired runs; retains failures and includes process startup/I/O."""
import argparse
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
from audit import audit
from prepare import sha256, write_json

VARIANTS = {
    'serial': ['--threads','1','--batch','1'],
    'batch_serial': ['--threads','1','--batch','8'],
    'parallel': ['--threads','4','--batch','8'],
    'portal': ['--threads','4','--batch','8','--portal-k','32','--schedule','portal'],
    'vertical_cost': ['--threads','4','--batch','8','--vertical-penalty','8'],
    'cuda': ['--backend','cuda','--threads','1','--batch','8'],
    'cuda_dense': ['--backend','cuda_dense','--threads','1','--batch','8'],
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--binary', type=Path, default=Path('build/h3d_route'))
    p.add_argument('--variants', nargs='+', choices=VARIANTS, default=['serial','batch_serial','parallel','portal'])
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--timeout', type=float, default=300)
    a = p.parse_args()
    if a.repeats < 1 or a.timeout <= 0:
        p.error('repeats and timeout must be positive')
    a.output.mkdir(parents=True, exist_ok=False)
    graph, nets = a.case/'graph.rrg', a.case/'nets.txt'
    case_manifest = json.loads((a.case/'manifest.json').read_text())
    inputs = {'graph': sha256(graph), 'nets': sha256(nets), 'binary': sha256(a.binary)}
    if inputs['graph'] != case_manifest['files']['graph.rrg'] or inputs['nets'] != case_manifest['files']['nets.txt']:
        raise ValueError('Case input hash mismatch')
    report = {'schema_version': 1, 'machine': platform.platform(), 'input_hashes': inputs,
              'case_manifest': case_manifest, 'runs': [], 'summary': {},
              'timing_scope': 'process_seconds includes graph loading, context setup, routing, result output; audit time excluded',
              'comparison_scope': 'serial changes scheduling; parallel vs batch_serial isolates worker count',
              'gpu_kernel_seconds': None, 'gpu_transfer_seconds': None, 'fpga_board_seconds': None}
    for repeat in range(a.repeats):
        # Rotate order to reduce a fixed first-run/cache bias, without concurrent runs.
        order = a.variants[repeat % len(a.variants):] + a.variants[:repeat % len(a.variants)]
        for variant in order:
            stem = f'{variant}_{repeat}'
            result = a.output/f'{stem}.json'
            cmd = [str(a.binary.resolve()), str(graph.resolve()), str(nets.resolve()), str(result.resolve()), *VARIANTS[variant]]
            row = {'variant':variant, 'repeat':repeat, 'command':cmd}
            start = time.perf_counter()
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=a.timeout)
                row['returncode'] = proc.returncode
                (a.output/f'{stem}.log').write_text(proc.stdout)
                row['status'] = 'completed' if proc.returncode in (0,2) else 'error'
            except subprocess.TimeoutExpired as exc:
                row['status'] = 'timeout'
                (a.output/f'{stem}.log').write_bytes(exc.stdout or b'')
            row['process_seconds'] = time.perf_counter()-start
            if row['status'] == 'completed':
                try:
                    row['audit'] = audit(graph, nets, result)
                    raw = json.loads(result.read_text())
                    row.update({k:raw[k] for k in ('success','routing_seconds','expansions','fallbacks')})
                    row['gpu_metrics'] = raw.get('gpu_metrics')
                    row['iterations'] = len(raw['iterations'])
                    row['conflicts'] = sum(i['conflicts'] for i in raw['iterations'])
                    row['repairs'] = sum(i['repairs'] for i in raw['iterations'])
                    row['route_fingerprint'] = __import__('hashlib').sha256(json.dumps(raw['routes'],sort_keys=True).encode()).hexdigest()
                except (ValueError, KeyError, IndexError) as exc:
                    row['status'], row['audit_error'] = 'audit_failed', str(exc)
            report['runs'].append(row)
            write_json(a.output/'summary.json', report)
            print(stem, row['status'], 'success='+str(row.get('success')), round(row['process_seconds'],3), flush=True)
    for variant in a.variants:
        runs = [r for r in report['runs'] if r['variant']==variant]
        completed = [r for r in runs if r['status']=='completed']
        report['summary'][variant] = {
            'runs':len(runs), 'completed':len(completed), 'successes':sum(r.get('success',False) for r in runs),
            'median_process_seconds':statistics.median(r['process_seconds'] for r in runs),
            'median_routing_seconds':statistics.median(r['routing_seconds'] for r in completed) if completed else None,
            'all_audited':all(r.get('audit',{}).get('audit_passed',False) for r in runs),
        }
    if all(k in report['summary'] for k in ('batch_serial','parallel')):
        pairs = []
        for repeat in range(a.repeats):
            pair = {r['variant']:r for r in report['runs'] if r['repeat']==repeat}
            left, right = pair['batch_serial'], pair['parallel']
            pairs.append({'repeat':repeat, 'identical_routes':left.get('route_fingerprint') is not None and left.get('route_fingerprint')==right.get('route_fingerprint'),
                          'process_speedup':left['process_seconds']/right['process_seconds']})
        report['worker_comparison'] = pairs
    report['cuda_comparison'] = []
    for repeat in range(a.repeats):
        pair = {r['variant']:r for r in report['runs'] if r['repeat']==repeat}
        fast = pair.get('cuda')
        if not fast or not fast.get('success'):
            continue
        for baseline in ('batch_serial','parallel','cuda_dense'):
            reference = pair.get(baseline)
            if reference and reference.get('success'):
                report['cuda_comparison'].append({'repeat':repeat,'baseline':baseline,
                    'process_speedup':reference['process_seconds']/fast['process_seconds'],
                    'identical_routes':reference['route_fingerprint']==fast['route_fingerprint']})
    if inputs != {'graph':sha256(graph),'nets':sha256(nets),'binary':sha256(a.binary)}:
        raise ValueError('Inputs or binary changed during experiment')
    write_json(a.output/'summary.json', report)


if __name__ == '__main__':
    main()
