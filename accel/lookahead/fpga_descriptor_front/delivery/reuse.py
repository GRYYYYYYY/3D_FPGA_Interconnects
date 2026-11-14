"""Verify frozen software/model receipts from Git; never rerun an experiment."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASE = 'ccec3da64b4c5be643809c2bdda94145c4bb8187'
PREFIX = 'results/fpga_sparse_stream_r2_20261112/evidence_snapshot/'
OUT = ROOT / 'results/fpga_descriptor_front_20261114/reused_evidence.json'


def blob(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    refs = {}

    def read(path):
        data = blob(path)
        refs[path] = {'sha256': digest(data), 'bytes': len(data)}
        return json.loads(data)

    gpu = PREFIX + 'software_private_inf_gpu_b_terminal/software/private_inf_gpu_b/'
    summary = read(gpu + 'summary.json')
    binding = read(gpu + 'binding.json')
    assert summary['all_receipts_pass'] and summary['receipt_count'] == 254
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, gpu], cwd=ROOT, text=True).splitlines()
    receipts = [p for p in names if p.endswith('.receipt.json')]
    assert len(receipts) == 254
    for name in receipts:
        r = read(name)
        assert r['returncode'] == 0, name
    # The missing CUDA sources were already supplemented and hash-bound previously.
    supplement = 'results/fpga_pending_stream_20261114/evidence_snapshot/stage_a_v2/cuda_source_supplement/'
    for name in ('cuda_private_inf.cu', 'cuda_prepared_pop.cu'):
        data = blob(supplement + name)
        assert digest(data) == binding['source_sha256'][name]
        refs[supplement + name] = {'sha256': digest(data), 'bytes': len(data)}
    old = PREFIX + 'checkpoint_20261114T042325Z_recovered_native/model/many32_p8_f0_request_model_a/'
    old_runs = []
    for service in ('large_l16_g1', 'large_l16_g2', 'large_l60_g2'):
        for case in ('bnn_export', 'lstm_s2'):
            path = old + service + '/' + case + '/receipt.json'
            r = read(path)
            assert r['returncode'] == 0 and r['status'] == 'passed' and r['whole_native_batch']
            assert r['output_sha256'] == r['golden_sha256']
            old_runs.append({'path': path, 'output_sha256': r['output_sha256'], 'executable_sha256': r['executable_sha256']})
    prep_path = PREFIX + 'software_gpu_transform_complete/prepared_pop_gpu_b/summary.json'
    prep = read(prep_path)
    targets = {
        'bnn_export': {'summary': prep_path, 'case': 'bnn_export_compact', **prep['cases']['bnn_export_compact']},
        'lstm_s2': {'summary': gpu + 'summary.json', 'case': 'lstm_s2_control_basic', **summary['cases']['lstm_s2_control_basic']},
    }
    assert abs(targets['bnn_export']['mean_s'] - .15179996944444446) < 1e-14
    assert abs(targets['lstm_s2']['mean_s'] - .15949799988888888) < 1e-14
    # Verify final D outputs directly against both the manifest and frozen golden.
    previous = ROOT.parent / '3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_20261114'
    d_binding = json.loads((previous / 'model_native_d/binding.json').read_text())
    goldens = {}
    for case, spec in d_binding['inputs'].items():
        data = Path(spec['golden']).read_bytes()
        assert digest(data) == spec['golden_sha256']
        goldens[case] = {'path': spec['golden'], 'sha256': digest(data), 'bytes': len(data), 'jobs': spec['jobs']}
    archive = read('results/fpga_enum_commit_20261114/evidence_snapshot/manifest.json')
    historical = {x['original_path']: x for x in archive['files']}
    for relative in ('model_native_d/binding.json', 'model_d_independent_verification.json', 'model_final_summary_d.json', 'qualification.json', 'delivery_terminal.json'):
        path = previous / relative
        expected = historical['results/fpga_enum_commit_20261114/' + relative]
        assert digest(path.read_bytes()) == expected['sha256']
    result = {
        'base_commit': BASE, 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'RESIDENT_COMPLETE_BATCH_V2; reuse only, no new software measurement',
        'GPU_receipts_verified': len(receipts), 'old_P8_F0_batches': old_runs,
        'strong_GPU_targets': targets, 'frozen_ALT_goldens': goldens, 'git_references': refs,
        'statistical_unit': 'raw_samples_s retains within-process repetitions; n=9 is not nine independent processes',
        'new_GPU_runs': 0, 'new_old_model_runs': 0, 'new_CUDA_supplement': False,
        'historical_D_verified_against_manifest': True,
    }
    with OUT.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print('REUSE_PASS: 254 receipts, 6 old batches, both CUDA sources, final D and four golden hashes')


if __name__ == '__main__':
    main()
