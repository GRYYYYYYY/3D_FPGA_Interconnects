#!/usr/bin/env python3
"""Run CUDA correctness checks and paired routing on a GPU worker.

Uses an existing shared-filesystem case; never allocates a GPU or submits a job.
Each invocation requires a new output directory and preserves failure logs.
"""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from prepare import sha256, write_json


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', type=Path, default=root/'data/generated/ex5p_balanced')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--route-timeout', type=int, default=600)
    parser.add_argument('--build-jobs', type=int, default=4)
    parser.add_argument('--cuda-architectures', help='Optional CMake CUDA architecture list, e.g. 80;90')
    parser.add_argument('--variants', nargs='+', choices=['batch_serial','parallel','cuda_dense','cuda'],
                        default=['batch_serial','parallel','cuda_dense','cuda'])
    parser.add_argument('--vpr-mode', choices=['local','deferred'], default='deferred',
                        help='Default: release GPU after routing, then run complete_gpu_validation.py on the CPU host')
    parser.add_argument('--skip-vpr', action='store_true', help='Legacy alias for --vpr-mode deferred; FULL check remains pending')
    args = parser.parse_args()
    if min(args.repeats, args.route_timeout, args.build_jobs) < 1:
        parser.error('repeats, route-timeout and build-jobs must be positive')
    if 'cuda' not in args.variants or len(set(args.variants))!=len(args.variants):
        parser.error('variants must be unique and include cuda')
    if args.skip_vpr:
        args.vpr_mode='deferred'
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    build = output/'build'
    report = {'status': 'running', 'machine': platform.platform(), 'stages': [],
              'gpu_execution_passed': False, 'vpr_full_check_passed': None,
              'vpr_mode': args.vpr_mode, 'case': str(args.case.resolve()),
              'performance_scope': 'Paired prototype CPU/CUDA process times; no speedup claim versus native VPR'}
    source_paths = [root/'CMakeLists.txt']
    for directory in ('src', 'include', 'hardware', 'scripts', 'tests'):
        source_paths += [p for p in (root/directory).iterdir() if p.is_file()]
    report['source_sha256'] = {str(p.relative_to(root)): sha256(p) for p in sorted(source_paths)}
    write_json(output/'validation.json', report)

    def run(name, command, timeout):
        command = [str(value) for value in command]
        stage = {'name': name, 'command': command, 'status': 'running'}
        report['stages'].append(stage)
        write_json(output/'validation.json', report)
        print(f'{name}: running (log: {output/name}.log)', flush=True)
        started = time.perf_counter()
        try:
            with (output/f'{name}.log').open('w') as log:
                result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            stage['returncode'] = result.returncode
            stage['status'] = 'passed' if result.returncode == 0 else 'failed'
        except subprocess.TimeoutExpired:
            stage['status'] = 'timeout'
        except OSError as exc:
            stage.update(status='failed', error=str(exc))
        stage['seconds'] = time.perf_counter()-started
        write_json(output/'validation.json', report)
        if stage['status'] != 'passed':
            raise RuntimeError(f'{name}: {stage["status"]}; inspect {output/name}.log')
        print(f'{name}: passed ({stage["seconds"]:.3f}s)', flush=True)

    try:
        run('device', ['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv'], 30)
        run('toolkit', ['nvcc', '--version'], 30)
        configure = ['cmake', '-S', root, '-B', build, '-DCMAKE_BUILD_TYPE=Release', '-DH3D_CUDA=ON']
        if args.cuda_architectures:
            configure.append(f'-DCMAKE_CUDA_ARCHITECTURES={args.cuda_architectures}')
        run('configure', configure, 180)
        run('build', ['cmake', '--build', build, '-j', args.build_jobs], 600)
        run('oracle', ['ctest', '--test-dir', build, '--output-on-failure', '--timeout', '180'], 400)
        run('adapters', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v'], 180)
        demo = output/'demo.json'
        run('cuda_demo', [build/'h3d_route', root/'examples/two_tier.rrg', root/'examples/two_tier.nets',
                          demo, '--backend', 'cuda', '--threads', '1', '--batch', '2'], 60)
        run('demo_audit', [sys.executable, root/'scripts/audit.py', root/'examples/two_tier.rrg',
                           root/'examples/two_tier.nets', demo, '--output', output/'demo_audit.json'], 60)
        if not json.loads((output/'demo_audit.json').read_text())['legal_in_projection']:
            raise RuntimeError('CUDA demo did not produce legal routing')
        matrix = output/'matrix'
        run('benchmark', [sys.executable, root/'scripts/benchmark.py', '--case', args.case.resolve(),
                          '--output', matrix, '--binary', build/'h3d_route',
                          '--variants', *args.variants, '--repeats', args.repeats,
                          '--timeout', args.route_timeout], args.repeats*len(args.variants)*(args.route_timeout+120)+60)
        runs = json.loads((matrix/'summary.json').read_text())['runs']
        if len(runs) != args.repeats*len(args.variants) or not all(
                row.get('status') == 'completed' and row.get('returncode') == 0
                and row.get('success') and row.get('audit', {}).get('legal_in_projection')
                for row in runs):
            raise RuntimeError('Some benchmark runs failed or timed out; inspect matrix/summary.json')
        report['gpu_execution_passed'] = True
        report['matrix_sha256'] = sha256(matrix/'summary.json')
        report['vpr_completion_command'] = [sys.executable, str(root/'scripts/complete_gpu_validation.py'),
                                             '--run',str(output),'--output',str(output/'host_vpr')]
        if args.vpr_mode == 'local':
            reference = root.parent/'FPGA_accelerate_FPGA/G_3d_routing'
            for repeat in range(args.repeats):
                name = f'vpr_cuda_{repeat}'
                run(name, [sys.executable, root/'scripts/vpr_validate.py', '--case', args.case.resolve(),
                           '--result', matrix/f'cuda_{repeat}.json', '--vpr-case', reference/'data/raw/ex5p_balanced.json',
                           '--vpr-lock', reference/'configs/vpr.lock.json', '--output', output/name], 300)
                if not json.loads((output/name/'validation.json').read_text())['vpr_full_check']:
                    raise RuntimeError(f'{name}: FULL check did not pass')
            report['vpr_full_check_passed'] = True
        if any(sha256(root/path) != digest for path, digest in report['source_sha256'].items()):
            raise RuntimeError('Source files changed during validation')
        report['status'] = 'passed' if args.vpr_mode == 'local' else 'gpu_passed_pending_vpr'
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        report.update(status='failed', error=str(exc))
    write_json(output/'validation.json', report)
    print(json.dumps({key: report[key] for key in ('status', 'gpu_execution_passed', 'vpr_full_check_passed')}, ensure_ascii=False))
    return 0 if report['status'] in ('passed','gpu_passed_pending_vpr') else 1


if __name__ == '__main__':
    raise SystemExit(main())
