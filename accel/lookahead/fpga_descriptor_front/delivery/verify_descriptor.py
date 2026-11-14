"""Independent verification of conversion receipts and complete CPU outputs."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
R = ROOT / 'results/fpga_descriptor_front_20261114'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    d = R / 'descriptor_a'
    binding = json.loads((d / 'binding.json').read_text())
    terminal = json.loads((d / 'terminal.json').read_text())
    assert terminal['all_pass'] and terminal['native_samples'] == 100
    for name, expected in binding['source_sha256'].items():
        assert sha(d / 'source' / name) == expected, name
    for name, expected in binding['binary_sha256'].items():
        assert sha(d / 'bin' / name) == expected, name
    records = []
    for path in sorted((d / 'receipts').glob('*_conversion.json')):
        receipt = json.loads(path.read_text())
        assert receipt['returncode'] == 0
        for name, expected in receipt['output_sha256'].items():
            assert sha(name) == expected, name
        a = receipt['full_input_admission']
        assert a['independently_decoded_records'] == a['nodes'] * a['samples']
        assert a['eligible_sequence_exact'] and a['offset_arithmetic_bits'] == 64
        assert a['prepared_edges'] <= 0xffffffff and a['cells'] <= 32768
        assert a['descriptor_bytes'] == a['sample_stride_bytes'] * a['samples']
        assert a['descriptor_end_bytes_exclusive'] == a['descriptor_base_bytes'] + a['descriptor_bytes']
        assert a['sample_stride_bytes'] % 1024 == 0
        assert a['raw_descriptor_bytes'] == a['nodes'] * a['actual_format_bytes'] * a['samples']
        for i, sample in enumerate(a['sample_admission']):
            assert sample['sample'] == i
            assert sample['maximum_valid_cell'] < a['cells']
            assert sample['begin_byte'] == a['descriptor_base_bytes'] + i * a['sample_stride_bytes']
            assert sample['end_byte_exclusive'] <= a['descriptor_end_bytes_exclusive']
        records.append({'receipt': str(path.relative_to(ROOT)), 'case': receipt['case'],
                        'format_bytes': a['actual_format_bytes'], 'samples': a['samples'],
                        'bytes': a['descriptor_bytes'], 'records': a['independently_decoded_records']})
    assert len(records) == 6
    for receipt in terminal['functional_receipts']:
        assert receipt['returncode'] == 0 and receipt['output_exact']
        for path, expected in receipt['output_sha256'].items():
            assert sha(path) == expected, path
            if path.endswith('/output.bin'):
                assert expected == binding['inputs'][receipt['case']]['golden_sha256']
    result = {'status': 'PASS', 'conversion_bindings': records,
              'all_frozen_source_and_binary_hashes_verified': True,
              'all_persisted_descriptor_and_complete_output_hashes_verified': True,
              'native_samples': 100, 'additional_fallback_samples': 20,
              'qualified_CPU_performance': False}
    out = R / 'descriptor_independent_verification.json'
    with out.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print('DESCRIPTOR_VERIFIED: six persisted layouts, 120 exact sample outputs, source/binary bindings')


if __name__ == '__main__':
    main()
