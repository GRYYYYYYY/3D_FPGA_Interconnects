"""Check archived confirmation routes against solver/readback logs and bindings."""
import argparse
import json
from pathlib import Path
from prepare import sha256, write_json
from scaling_common import metrics
from report_native_joint import log_evidence


def verify(audit, pointer):
    root = Path(audit['metadata_directory'])
    run = root / 'run'
    bundle = Path(pointer['bundle'])
    assert audit['bootstrap']['status'] == 'completed' and audit['bootstrap']['returncode'] == 0
    overall = json.loads((run / 'summary.json').read_text())
    assert overall['status'] == 'completed'
    assert overall['elliptic_quality_passed'] and overall['elliptic_repeats_quality_passed']
    library_hash = audit['content_sha256']['run/library/libh3d_native_gpu.so']
    original_hash = json.loads((bundle / 'vpr.lock.json').read_text())['binary']['sha256']
    assert sha256(bundle / 'baseline/vpr') == original_hash
    candidate_hash = sha256(bundle / 'vpr')
    sets = set()
    inputs = {}
    verified = []
    for name in ['elliptic_initial', 'elliptic_repeats', 'gemm', 'gemm_cpu_control']:
        matrix = json.loads((run / name / 'summary.json').read_text())
        assert matrix['status'] == 'completed' and matrix['all_routes_successful']
        assert matrix['bindings'][str(bundle / 'vpr')] == candidate_hash
        assert matrix['bindings'][matrix['library']] == library_hash
        cpu = matrix['cpu_budget']
        topology = {t['cpu']: t for t in cpu['topology']}
        assert len({(topology[c]['socket'], topology[c]['core']) for c in cpu['cpu_set']}) == 4
        for row in matrix['measurements']:
            assert row['success'] and row['returncode'] == 0 and not row['diagnostic']
            directory = run / name / Path(row['directory']).name
            logged = metrics((directory / 'process.log').read_text(errors='replace'))
            checked = metrics((directory / 'independent_check.log').read_text(errors='replace'))
            assert logged['routing_success'] and logged['full_check'] and checked['full_check']
            for key in ['critical_path_ns', 'wirelength']:
                assert row[key] == logged[key] == checked[key] == row['independent_metrics'][key]
            assert row['independent_check']['returncode'] == 0
            assert row['independent_check']['command'][0] == str(bundle / 'baseline/vpr')
            assert log_evidence(directory)['final_overused_nodes'] == 0
            route = str(directory.relative_to(root) / 'routed.route')
            assert audit['content_sha256'][route] == row['route_sha256']
            settings = row['execution_settings']
            assert settings['gpu_timing'] == settings['diagnostics'] == '0' and not settings['capture']
            original = row['variant'] in ['original_vpr', 'original_parallel']
            assert settings['parallel_lookahead'] == ('0' if original else '1')
            assert row['command'][0] == str(bundle / ('baseline/vpr' if original else 'vpr'))
            command = row['command']
            assert command[command.index('--num_workers') + 1] == ('1' if row['variant'] == 'original_vpr' else '4')
            if row['variant'] != 'original_vpr':
                assert command[command.index('--router_algorithm') + 1] == 'parallel'
            solver = row['cpu_budget_audit']
            readback = row['independent_check']['cpu_budget_audit']
            for resources in [solver, readback]:
                assert resources['verified'] and not resources['affinity_violations']
                assert resources['permitted_cpu_set'] == cpu['cpu_set']
            assert settings['cpu_affinity'] == cpu['cpu_set']
            sets.add(tuple(cpu['cpu_set']))
            hashes = {k: v['sha256'] for k, v in row['inputs'].items()}
            assert inputs.setdefault(row['case'], hashes) == hashes
            frozen_case = json.loads((bundle / 'inputs' / row['case'] / 'vpr_case.json').read_text())
            assert hashes == {k: v['sha256'] for k, v in frozen_case['inputs'].items()}
            hybrid = row.get('hybrid', {})
            assert not hybrid.get('errors') and not hybrid.get('fallbacks')
            if row['variant'] == 'batch':
                assert hybrid['gpu_initialized'] and hybrid['committed'] > 0 and hybrid['spatial_ownership']
            verified.append({'case': row['case'], 'variant': row['variant'], 'repeat': row['repeat'],
                             'route': route, 'sha256': row['route_sha256'], 'gpu_commits': hybrid.get('committed', 0)})
    assert len(verified) == 12 and len(sets) == 1
    oracle = json.loads((run / 'library/summary.json').read_text())
    assert oracle['status'] == 'completed'
    assert all(b['returncode'] == 0 for c in oracle['cases'] for b in c['batches'])
    paths = sum(b['validated_queries'] for c in oracle['cases'] for b in c['batches'])
    return {'status': 'passed', 'measurements': len(verified), 'routes': verified,
            'cuda_library_sha256': library_hash, 'candidate_sha256': candidate_hash,
            'original_sha256': original_hash, 'oracle_validated_paths': paths,
            'input_hashes': inputs, 'cpu_set': list(next(iter(sets))), 'physical_cores': 4,
            'frozen_files_verified': audit['bundle_bindings_verified']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--pointer', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = verify(json.loads(args.audit.read_text()), json.loads(args.pointer.read_text()))
    write_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ['routes', 'input_hashes']}))


if __name__ == '__main__':
    main()
