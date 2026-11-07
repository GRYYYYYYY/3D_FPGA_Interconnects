#!/usr/bin/env python3
"""Bounded diagnostic runs, retaining partial per-connection data on timeout.

These traced runs are diagnostic evidence, not end-to-end speedup measurements.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import platform

from prepare import sha256, write_json
from scaling_common import run_process


def summarize_trace(path):
    totals = {key: 0.0 for key in ('cpu_window_seconds', 'prepare_seconds',
              'relaxation_seconds', 'traceback_seconds', 'search_seconds')}
    totals.update(completed_queries=0, visits=0, rounds=0, h2d_bytes=0, window_vertices=0)
    last_begin = last_end = None
    if path.exists():
        with path.open() as f:
            for row in csv.DictReader(f):
                if row['event'] == 'begin':
                    last_begin = row
                elif row['event'] == 'end':
                    try:
                        values = {k: float(row[k]) for k in totals if k != 'completed_queries'}
                    except (ValueError, TypeError):
                        continue  # interrupted final record, never count as completed
                    for k, v in values.items():
                        totals[k] += v
                    totals['completed_queries'] += 1
                    last_end = row
    return dict(totals, last_begin=last_begin, last_end=last_end,
                scope='completed queries only; excludes any interrupted query and initialization')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--suite', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cases', nargs='+', default=['reduction', 'gemm'])
    p.add_argument('--timeout', type=float, default=600)
    p.add_argument('--window-mode', choices=['host', 'device'])
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    cases = [c for c in json.loads(a.suite.read_text())['cases'] if c['id'] in a.cases]
    if {c['id'] for c in cases} != set(a.cases):
        raise ValueError('Unknown diagnostic case')
    source = {str(f.relative_to(root)): sha256(f) for d in ['src','include','scripts','hardware','tests']
              for f in (root/d).glob('*') if f.is_file()}
    source['CMakeLists.txt'] = sha256(root/'CMakeLists.txt')
    rec = dict(status='running', hostname=platform.node(), rows=[], source_sha256=source,
               purpose='timeout diagnosis, profiling enabled; no speedup claim')
    write_json(out/'profile.json', rec)
    try:
        for name, cmd in [
            ('device', ['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv']),
            ('configure', ['cmake', '-S', root, '-B', out/'build', '-DH3D_CUDA=ON', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CUDA_ARCHITECTURES=90']),
            ('build', ['cmake', '--build', out/'build', '-j4']),
            ('oracle', ['ctest', '--test-dir', out/'build', '--output-on-failure', '--timeout', '180'])]:
            result = run_process(cmd, out, os.environ.copy(), 600, name+'.log')
            if result['returncode'] != 0:
                raise RuntimeError(name+' failed')
        rec['binary_sha256'] = sha256(out/'build/h3d_route')
        for case in cases:
            directory = out/case['id']; directory.mkdir()
            projection = Path(case['projection'])
            manifest = json.loads((projection/'manifest.json').read_text())
            inputs = {str(projection/f): manifest['files'][f] for f in ('graph.rrg','nets.txt')}
            inputs[case['delays']] = case['delays_sha256']
            for f, h in inputs.items():
                if sha256(f) != h: raise ValueError('Input drift: '+f)
            row = dict(case=case['id'], status='running', input_sha256=inputs)
            rec['rows'].append(row); write_json(out/'profile.json', rec)
            cmd = [out/'build/h3d_route', projection/'graph.rrg', projection/'nets.txt', directory/'result.json',
                   '--backend', 'cuda_target', '--delay-file', case['delays'], '--present','1',
                   '--present-cap','1000','--iterations','200','--bbox-margin','3','--bucket-width','65536',
                   '--trace-file', directory/'connections.csv']
            if a.window_mode: cmd += ['--window-mode', a.window_mode]
            row.update(run_process(cmd, directory, os.environ.copy(), a.timeout))
            row['partial_trace'] = summarize_trace(directory/'connections.csv')
            row['inputs_unchanged'] = all(sha256(f) == h for f,h in inputs.items())
            write_json(directory/'measurement.json', row); write_json(out/'profile.json', rec)
            print(case['id'], row['status'], row['partial_trace']['completed_queries'], flush=True)
        rec['source_unchanged'] = all(sha256(root/f) == h for f,h in source.items())
        rec['status'] = 'completed' if rec['source_unchanged'] and all(r['inputs_unchanged'] for r in rec['rows']) else 'provenance_changed'
    except Exception as exc:
        rec.update(status='infrastructure_error', error=str(exc)); raise
    finally:
        write_json(out/'profile.json', rec)


if __name__ == '__main__': main()
