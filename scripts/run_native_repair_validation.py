"""Validate elliptic after partition repair, then profile GEMM lookahead."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare import sha256, write_json
from scaling_common import run_process


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
              'scope': 'Elliptic correctness/quality qualification; GEMM lookahead diagnosis. No speedup ratio against a failed original parallel route.'}

    def run(name, command, timeout):
        result = run_process(command, out, env, timeout, name + '.log')
        record['steps'].append({'name': name, **result})
        write_json(out / 'summary.json', record)
        if result['returncode']:
            raise RuntimeError(name + ' failed; retained logs')

    write_json(out / 'summary.json', record)
    try:
        run('library_oracle', [sys.executable, '-B', str(bundle / 'scripts/run_native_replay.py'),
                              '--source', str(bundle / 'native'), '--resident', '--cooperative-blocks', '64',
                              '--capture', str(bundle / 'legacy_oracle'), '--output', str(out / 'library')], 600)
        run('elliptic', [sys.executable, '-B', str(bundle / 'scripts/run_native_hybrid.py'),
                         '--binary', str(bundle / 'vpr'), '--library', str(out / 'library/libh3d_native_gpu.so'),
                         '--suite', str(args.suite), '--runtime', str(bundle / 'runtime/runtime.json'),
                         '--vpr-lock', str(bundle / 'vpr.lock.json'), '--output', str(out / 'elliptic'),
                         '--cases', 'elliptic', '--variants', 'original_vpr,native_parallel,guard,batch',
                         '--budget', '2048', '--workers', '4', '--batch-size', '4', '--batch-wait-us', '50',
                         '--cooperative-blocks', '64', '--cpu-cores', '4', '--prewarm-inputs',
                         '--overuse-report', '--repeats', '1', '--timeout', '600'], 5000)
        rows = json.loads((out / 'elliptic/summary.json').read_text())['measurements']
        ref = rows[0]
        record['elliptic_quality_passed'] = ref['success'] and all(
            r['success'] and r['critical_path_ns'] <= 1.05 * ref['critical_path_ns']
            and r['wirelength'] <= 1.05 * ref['wirelength'] and not r.get('hybrid', {}).get('errors', 0) for r in rows)
        write_json(out / 'summary.json', record)
        run('gemm_profile', [sys.executable, '-B', str(bundle / 'scripts/run_predecessor_probe.py'),
                             '--binary', str(bundle / 'vpr'), '--suite', str(args.suite),
                             '--runtime', str(bundle / 'runtime/runtime.json'), '--vpr-lock', str(bundle / 'vpr.lock.json'),
                             '--case', 'gemm', '--mode', 'parallel', '--lookahead-profile', '--write-lookahead',
                             '--output', str(out / 'gemm_profile'), '--timeout', '900'], 1900)
        record['gemm_success'] = json.loads((out / 'gemm_profile/summary.json').read_text())['success']
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
