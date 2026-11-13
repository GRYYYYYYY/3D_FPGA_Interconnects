"""Identity and complete-stage checks for append-only candidate recovery."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / 'results/fpga_sparse_stream_r2_20261112'
REUSED = {'build_identity', 'native2', 'fixtures91', 'stress2', 'address2',
          'calibration97', 'fixed36', 'batch40x2'}
TAIL = {'hot8192_8193', 'boundary4', 'fixed10ns18'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def path_name(path):
    path = Path(path).resolve()
    return str(path.relative_to(RESULTS)) if path.is_relative_to(RESULTS) else str(path)


def load(path):
    return json.loads(Path(path).read_text())


def verify_hashes(hashes):
    for name, digest in hashes.items():
        assert sha(RESULTS / name) == digest, 'recovery evidence changed: ' + name


def inspect_reusable(plan):
    hashes = {}
    def remember(path):
        path = Path(path)
        key = path_name(path)
        if key not in hashes:
            hashes[key] = sha(path)
        return hashes[key]
    def read(rel):
        p = RESULTS / rel
        remember(p)
        return load(p)
    def exact(a, b):
        assert remember(a) == remember(b), 'recovery byte mismatch: ' + str(a)
    v, m = plan['RTL'], plan['model']
    old = read(f'rtl/{v}_pipeline_receipt.json')
    assert old['variant'] == v and old['model'] == m
    assert len(old['steps']) >= 8 and all(x['returncode'] == 0 for x in old['steps'][:8])
    context = read(plan['binding'])
    rows = [x for x in context['bindings'] if x['RTL'] == v and x['OOC'] == plan['OOC']]
    assert context['all_pass'] and len(rows) == 1 and rows[0]['all_pass']
    params = rows[0]['effective_RTL_parameters']
    assert params == rows[0]['effective_physical_parameters']
    for folder in [Path('rtl')/(v+'_build'), Path('model')/m, Path('timing')/plan['OOC']]:
        binding = read(folder/'source_binding.json')
        for name, digest in binding['source_sha256'].items():
            assert remember(RESULTS/folder/'source'/name) == digest
    mb = read(Path('model')/m/'source_binding.json')
    macros = dict(x[2:].split('=', 1) for x in mb['command'] if x.startswith('-D') and '=' in x)
    for macro, param in [('TILE_L','L'),('TILE_P','PHYS'),('TILE_MC','MEMBER_CAP'),
                         ('TILE_CC','CHANGED_LIMIT'),('TILE_CACHE','CACHE_ENABLE'),('R2_REQUEST_STAGE','REQUEST_STAGE')]:
        assert int(macros[macro]) == params[param], 'recovery parameter mismatch'
    rtl_exe = RESULTS/'rtl'/(v+'_build')/'Vr2_many_tile'
    model_exe = RESULTS/'model'/m/'model'
    exe_hash = [remember(rtl_exe), remember(model_exe)]
    for suffix, count in [('native_l60',2),('fixtures_l60',91),
                          ('stress,stress_random_l120',2),('external_nodes_65536,external_nodes_4194304_l60',2)]:
        summary = read(f'rtl/{v}_{suffix}/summary.json')
        assert summary['all_pass'] and len(summary['results']) == count
        for row in summary['results']:
            assert row['returncode'] == 0 and Path(row['command'][0]) == rtl_exe
            dest = Path(row['command'][4])
            actual = read(dest/'summary.json')
            assert actual['all_outputs_exact'] and actual['batch_starts'] == 1
            exact(dest/'output.bin', Path(row['command'][3]))
            read(dest/'receipt.json')
    full = read(f'model/{m}/{plan["calibration"]}/calibration.json')
    assert full['all_pass'] and full['expected_cases'] == len(full['results']) == 97
    assert full['model_executable_sha256'] == exe_hash[1]
    for row in full['results']:
        assert row['returncode'] == 0 and row['cycle_log_exact'] and row['outputs_exact'] and row['all_traffic_histogram_phase_summary_exact']
        dest, ref = Path(row['command'][4]), Path(row['reference']).parent
        assert ref.relative_to(RESULTS/'rtl').parts[0].startswith(v+'_')
        for name in ['cycles.csv','output.bin']:
            exact(dest/name, ref/name)
        a, b = read(dest/'summary.json'), read(ref/'summary.json')
        a.pop('scope', None); b.pop('scope', None)
        assert a == b
    fixed = read(f'rtl/{v}_fixed_time/calibration.json')
    assert fixed['all_pass'] and fixed['cases'] == len(fixed['results']) == 36
    for row in fixed['results']:
        assert row['all_pass']
        assert [x['executable_sha256'] for x in row['results']] == exe_hash
        assert all(x['returncode'] == 0 for x in row['results'])
        dirs = [Path(x['command'][4]) for x in row['results']]
        for name in ['cycles.csv','output.bin','physical_time_contract.json']:
            exact(dirs[0]/name, dirs[1]/name)
    for case in ['max_node_max_cell_q40','partial_line_missing_q40']:
        d = RESULTS/'rtl'/(v+'_batch_capacity')/case
        rec = read(d/'receipt2.json'); assert rec['returncode'] == 0
        assert Path(rec['command'][0]) == rtl_exe
        summary = read(d/'rtl/summary.json')
        assert summary['all_outputs_exact'] and summary['jobs'] == 40 and summary['batch_starts'] == 1
        exact(d/'rtl/output.bin', Path(rec['command'][3]))
    # Keep every interrupted artifact byte-identical; no causal claim about exit.
    partial = RESULTS/'rtl'/(v+'_hot_capacity8192')
    for p in sorted(partial.rglob('*')):
        if p.is_file(): remember(p)
    return {'RTL':v,'model':m,'OOC':plan['OOC'],'parameters':params,
            'reused_stages':sorted(REUSED),'evidence_sha256':hashes,
            'rtl_executable_sha256':exe_hash[0],'model_executable_sha256':exe_hash[1],
            'old_receipt_status_preserved':old['status'],'interruption_cause':'unknown'}


def validate_recovery(rel, plan, require_terminal=True):
    q = load(RESULTS/rel)
    if require_terminal:
        terminal = load((RESULTS/rel).parent/'terminal.json')
        assert terminal['status'] == 'passed' and terminal['qualification_sha256'] == sha(RESULTS/rel)
    assert q['status'] == 'passed', 'recovery not passed'
    assert all(q[k] == plan[k] for k in ['RTL','model','OOC']), 'wrong recovery candidate'
    inv = load(RESULTS/q['inventory'])
    assert sha(RESULTS/q['inventory']) == q['inventory_sha256']
    assert all(inv[k] == plan[k] for k in ['RTL','model','OOC'])
    assert set(inv['reused_stages']) == REUSED and set(q['tail_stages']) == TAIL
    verify_hashes(inv['evidence_sha256']); verify_hashes(q['evidence_sha256'])
    for rel in q['tail_stages'].values():
        record = load(RESULTS/rel)
        assert record['returncode'] == 0 and record['passed']
    hot = load(RESULTS/q['hot_summary'])
    assert hot['all_pass'] and [x['unique_changes_on_owner0'] for x in hot['results']] == [8192,8193]
    assert all(x['passed'] and x['cycle_log_exact'] for x in hot['results'])
    boundary = load(RESULTS/q['boundary_calibration'])
    assert boundary['all_pass'] and len(boundary['results']) == 4
    assert boundary['executable_sha256'] == inv['model_executable_sha256']
    assert all(x['passed'] and x['cycle_log_exact'] for x in boundary['results'])
    fixed = load(RESULTS/q['fixed10ns_calibration'])
    assert fixed['all_pass'] and fixed['cases'] == len(fixed['results']) == 18
    assert all(x['all_pass'] and [z['executable_sha256'] for z in x['results']] ==
               [inv['rtl_executable_sha256'],inv['model_executable_sha256']] for x in fixed['results'])
    return q
