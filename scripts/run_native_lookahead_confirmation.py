"""Same-worker confirmation of the repaired router and parallel lookahead."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare import sha256, write_json
from scaling_common import run_process
from report_native_joint import analyze


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--suite', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    bundle = args.bundle.resolve()
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('VPR_HYBRID_', 'H3D_GPU_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'status': 'running', 'steps': [], 'hostname': subprocess.check_output(['hostname'], text=True).strip(),
              'device': subprocess.check_output(['nvidia-smi'], text=True),
              'plan': 'Elliptic quality first. GEMM three rotated original-parallel/batch pairs and one CPU attribution control. Four physical cores include GPU service threads. Original lookahead unchanged; all builds are cold, with identical prewarmed graph inputs and no lookahead cache.'}

    def run(name, command, timeout):
        result = run_process(command, out, env, timeout, name + '.log')
        record['steps'].append({'name': name, **result})
        write_json(out / 'summary.json', record)
        if result['returncode']:
            raise RuntimeError(name + ' failed; retained logs')

    def matrix(name, case, variants, repeats, start=0):
        run(name, [sys.executable, '-B', str(bundle / 'scripts/run_native_hybrid.py'),
                   '--binary', str(bundle / 'vpr'), '--library', str(out / 'library/libh3d_native_gpu.so'),
                   '--suite', str(args.suite), '--runtime', str(bundle / 'runtime/runtime.json'),
                   '--vpr-lock', str(bundle / 'vpr.lock.json'), '--output', str(out / name),
                   '--cases', case, '--variants', variants, '--budget', '2048', '--workers', '4',
                   '--batch-size', '4', '--batch-wait-us', '50', '--cooperative-blocks', '64',
                   '--cpu-cores', '4', '--prewarm-inputs', '--overuse-report', '--parallel-lookahead',
                   '--repeats', str(repeats), '--repeat-start', str(start), '--timeout', '900'], 7200)
        result = json.loads((out / name / 'summary.json').read_text())
        if result['status'] != 'completed' or len(result['measurements']) != len(variants.split(',')) * repeats:
            raise RuntimeError('Incomplete matrix')
        for row in result['measurements']:
            settings = row['execution_settings']
            expected = '0' if row['variant'] in ['original_vpr', 'original_parallel'] else '1'
            if settings['parallel_lookahead'] != expected:
                raise RuntimeError('Lookahead control contamination')
            if row['diagnostic'] or settings['gpu_timing'] != '0' or settings['diagnostics'] != '0' or settings['capture']:
                raise RuntimeError('Diagnostics leaked into confirmation')
            if not row.get('cpu_budget_audit', {}).get('verified'):
                raise RuntimeError('CPU budget audit failed')
        return result['measurements']

    write_json(out / 'summary.json', record)
    try:
        run('library_oracle', [sys.executable, '-B', str(bundle / 'scripts/run_native_replay.py'),
                              '--source', str(bundle / 'native'), '--resident', '--cooperative-blocks', '64',
                              '--capture', str(bundle / 'legacy_oracle'), '--output', str(out / 'library')], 600)
        rows = matrix('elliptic_initial', 'elliptic', 'original_vpr,guard,batch', 1)
        ref = rows[0]
        record['elliptic_quality_passed'] = ref['success'] and all(
            r['success'] and r['critical_path_ns'] <= 1.05 * ref['critical_path_ns']
            and r['wirelength'] <= 1.05 * ref['wirelength'] and not r.get('hybrid', {}).get('errors', 0) for r in rows)
        if not record['elliptic_quality_passed']:
            raise RuntimeError('Elliptic quality gate failed; diagnose before broader confirmation')
        repeats = matrix('elliptic_repeats', 'elliptic', 'batch', 2, 1)
        record['elliptic_repeats_quality_passed'] = all(
            r['success'] and r['critical_path_ns'] <= 1.05 * ref['critical_path_ns']
            and r['wirelength'] <= 1.05 * ref['wirelength'] and not r.get('hybrid', {}).get('errors', 0) for r in repeats)
        if not record['elliptic_repeats_quality_passed']:
            raise RuntimeError('Elliptic repeated quality gate failed')
        matrix('gemm', 'gemm', 'original_parallel,batch', 3)
        matrix('gemm_cpu_control', 'gemm', 'native_parallel', 1)
        write_json(out / 'analysis.json', analyze(out))
        frozen = json.loads((bundle / 'bindings.json').read_text())
        if any(sha256(bundle / k) != v for k, v in frozen['files'].items()):
            raise RuntimeError('Frozen bundle changed')
        record['status'] = 'completed'
    except Exception as e:
        record.update(status='failed', error=repr(e))
        raise
    finally:
        write_json(out / 'summary.json', record)


if __name__ == '__main__':
    main()
