"""Reconstruct the finite native40 backing allocated by the frozen harness.

This is source/header-derived capacity, not measured traffic or FPGA resources.
Usage: OUTPUT.json. No simulator, workload or original evidence is modified.
"""
from pathlib import Path
import datetime
import hashlib
import json
import struct
import sys

root = Path(__file__).resolve().parents[4]
r = root / 'results/fpga_sparse_stream_r2_20261112'
out = r / 'analysis' / sys.argv[1]
if Path(sys.argv[1]).name != sys.argv[1] or out.exists():
    raise RuntimeError('new local output name required')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def align(lines):
    return (lines + 255) & ~255


models = ['many32_request_model_c', 'many32_p8_request_model_a']
source_hashes = {}
for model in models:
    folder = r / 'model' / model
    binding = json.loads((folder / 'source_binding.json').read_text())
    source = folder / 'source/many_tile_driver.cpp'
    sha = digest(source)
    assert sha == binding['source_sha256'][source.name]
    source_hashes[str(source.relative_to(r))] = sha
    macros = dict(x[2:].split('=', 1) for x in binding['command'] if x.startswith('-D') and '=' in x)
    assert int(macros['TILE_L']) == 32
    text = source.read_text()
    assert 'std::vector<Line> memory(OB+w.h.jobs*OS)' in text
    assert 'addr>=memory.size()||addr%P!=c' in text
assert len(set(source_hashes.values())) == 1, 'P32/P8 use different frozen harnesses'

rows = []
for case in ['bnn_export', 'lstm_s2']:
    prep = r / 'semantics/large_prepared' / (case + '.bin')
    receipt = json.loads(prep.with_suffix('.json').read_text())
    workload = Path(receipt['command'][1])
    assert receipt['returncode'] == 0
    assert digest(workload) == receipt['workload_sha256']
    assert digest(prep) == receipt['prepared_sha256']
    with workload.open('rb') as f:
        magic, nodes, edges, jobs, costs, cells, groups = struct.unpack('<7Q', f.read(56))
    with prep.open('rb') as f:
        header = struct.unpack('<6Q', f.read(48))
    assert magic == 0x31414c5443495254 and header[0] == 0x5350415253455632
    assert header[1] == nodes and jobs == 40 and nodes <= 4194304
    assert 0 < cells <= 32768 and 0 < costs <= 16
    L, prepared_edges = 32, header[2]
    SB = align((nodes + 4 * L - 1) // (4 * L) * L)
    RB = align(SB + (nodes + 4 * L - 1) // (4 * L) * 2 * L)
    EB = align(RB + ((nodes + 1) * 8 + 31) // 32)
    CB = align(EB + (prepared_edges * 4 + 31) // 32)
    MB = align(CB + (costs * 8 + 31) // 32)
    CS = align((nodes * 8 + 31) // 32)
    JB = MB + jobs * CS
    OB = align(JB + jobs)
    OS = (cells + 3) // 4
    end = OB + jobs * OS
    boundaries = [0, SB, RB, EB, CB, MB, JB, OB, end]
    names = ['proposal', 'node_state', 'CSR_rows', 'prepared_edges', 'cost',
             'qid_type_cell_metadata', 'jobs', 'batch_output']
    used = [nodes * 8, nodes * 16, (nodes + 1) * 8, prepared_edges * 4,
            costs * 8, jobs * nodes * 8, jobs * 32, jobs * cells * 8]
    regions = []
    for name, start, stop, useful in zip(names, boundaries, boundaries[1:], used):
        assert start <= stop and (stop - start) * 32 >= useful
        regions.append({'array': name, 'first_line': start, 'end_line_exclusive': stop,
                        'reserved_bytes': (stop - start) * 32, 'payload_bytes': useful,
                        'alignment_or_partial_line_bytes': (stop - start) * 32 - useful})
    summary_path = r / 'model/many32_request_model_c/large_l60_g2' / case / 'summary.json'
    summary = json.loads(summary_path.read_text())
    traffic = summary['array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read']
    assert summary['all_outputs_exact'] and summary['jobs'] == jobs
    assert traffic[6] == jobs and traffic[7] == jobs * OS
    assert sum(x['reserved_bytes'] for x in regions) == end * 32
    rows.append({'case': case, 'nodes': nodes, 'raw_edges': edges, 'prepared_edges': prepared_edges,
                 'jobs': jobs, 'costs': costs, 'cells': cells, 'regions': regions,
                 'allocated_backing_lines': end, 'allocated_backing_bytes': end * 32,
                 'metadata_sample_stride_bytes': CS * 32, 'output_sample_stride_bytes': OS * 32,
                 'ports8_reserved_bytes': [((end + 7 - p) // 8) * 32 for p in range(8)],
                 'ports32_reserved_bytes': [((end + 31 - p) // 32) * 32 for p in range(32)],
                 'checked_complete_job_and_output_traffic_summary': str(summary_path.relative_to(r)),
                 'summary_sha256': digest(summary_path),
                 'workload_sha256': receipt['workload_sha256'], 'prepared_sha256': receipt['prepared_sha256']})
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'all_pass': True,
          'scope': 'exact source/header-derived finite backing allocation for existing native40 harnesses; not a new experiment, board-memory qualification or measured traffic',
          # Alignment applies to region bases; final output lines may be partial.
          'line_bytes': 32, 'regions_aligned_in_lines': 256, 'owner_count': 32,
          'physical_mapping': 'port=global_line modulo P; every accepted address must be below allocated backing lines; all logical arrays share these ports',
          'source_sha256': source_hashes, 'rows': rows,
          'host_oracle_storage_excluded': 'original decoded workload, reference output, wave snapshots and verification sets are testbench-only; device arrays are exactly the listed backing plus separately synthesized on-chip state',
          'board_measured': False}
out.write_text(json.dumps(result, indent=2) + '\n')
for row in rows:
    print(row['case'], row['allocated_backing_bytes'], 'finite backing bytes')
