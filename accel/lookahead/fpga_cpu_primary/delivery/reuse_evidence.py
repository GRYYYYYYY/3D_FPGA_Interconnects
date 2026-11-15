#!/usr/bin/env python3
"""Read-only historical verification; write only a new content-addressed index.

No compilation, benchmark, model or VPR execution. Existing final index is immutable.
Large original inputs stay external with verified hashes; selected raw records,
source closure, complete ALT outputs and binary bytes are copied into objects/.
"""
from pathlib import Path
import argparse, collections, datetime, gzip, hashlib, json, statistics, struct, subprocess

ROOT = Path(__file__).resolve().parents[4]
BASE = '3c7f96e6037030949b729240977c2ced373843c6'
LF = 'results/fpga_local_fabric_20261115'
DF = 'results/fpga_descriptor_front_20261114'
R2 = 'results/fpga_sparse_stream_r2_20261112/evidence_snapshot/'
SUP = 'results/fpga_pending_stream_20261114/evidence_snapshot/stage_a_v2/cuda_source_supplement/'
DEFAULT = ROOT / 'results/fpga_cpu_primary_20261115/reused_evidence'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def require(ok, detail):
    if not ok:
        raise RuntimeError(detail)


class Evidence:
    def __init__(self, out):
        self.out = out
        self.files = {}
        self.external = {}
        self.archives = {}
        require(not (out / 'index.json').exists(), 'index already complete; use --verify')
        out.mkdir(parents=True, exist_ok=True)
        self.tree = {}
        raw = subprocess.check_output(['git', 'ls-tree', '-rz', BASE], cwd=ROOT)
        for row in raw.split(b'\0'):
            if row:
                meta, path = row.split(b'\t', 1)
                self.tree[path.decode()] = meta.split()[2].decode()

    def put(self, name, data, provenance):
        digest = sha(data)
        z = gzip.compress(data, compresslevel=6, mtime=0)
        compressed = len(z) + 64 < len(data)
        obj = f'objects/{digest[:2]}/{digest}' + ('.gz' if compressed else '.raw')
        path = self.out / obj
        payload = z if compressed else data
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            require(path.read_bytes() == payload, 'object collision ' + name)
        else:
            with path.open('xb') as f:
                f.write(payload)
        row = {'sha256': digest, 'bytes': len(data), 'object': obj,
               'compression': 'gzip' if compressed else 'identity', **provenance}
        if name in self.files:
            require(self.files[name]['sha256'] == digest, 'changed evidence ' + name)
        self.files[name] = row
        return data

    def git(self, path):
        data = (ROOT / path).read_bytes()
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(oid == self.tree[path], 'not frozen Git blob: ' + path)
        return self.put(path, data, {'git_commit': BASE, 'git_path': path, 'git_blob': oid})

    def archived(self, prefix, name):
        if prefix not in self.archives:
            mp = prefix + '/manifest.json'
            rows = json.loads(self.git(mp))['files']
            self.archives[prefix] = {x['original_path']: x for x in rows}
        x = self.archives[prefix][name]
        data = (ROOT / prefix / x['archive']).read_bytes()
        data = gzip.decompress(data) if x['compression'] == 'gzip' else data
        require(sha(data) == x['sha256'] and len(data) == x['bytes'], 'archive mismatch ' + name)
        return self.put(name, data, {'manifest': prefix + '/manifest.json',
                                    'archive_object': x['archive'], 'original_path': name})

    def lf(self, name):
        return self.archived(LF + '/evidence_snapshot', LF + '/' + name)

    def df(self, name):
        return self.archived(DF + '/evidence_snapshot_final_a', DF + '/' + name)

    def local(self, path, expected=None, copy=True, note='current bytes; historical binding identified separately'):
        p = Path(path)
        if str(p) in self.external:
            row = self.external[str(p)]
            require(expected is None or row['sha256'] == expected, 'inconsistent hash ' + str(p))
            return row
        digest = file_sha(p)
        require(expected is None or digest == expected, 'external mismatch ' + str(p))
        row = {'path': str(p), 'sha256': digest, 'bytes': p.stat().st_size,
               'expected_sha256': expected, 'hash_verified_now': True, 'binding_note': note}
        if copy:
            key = 'external/' + str(p).lstrip('/')
            self.put(key, p.read_bytes(), {'original_path': str(p), 'binding_note': note})
            row['raw_key'] = key
        self.external[str(p)] = row
        return row


def input_sections(a, b, expected):
    with Path(a).open('rb') as fa, Path(b).open('rb') as fb:
        ha, hb = fa.read(56), fb.read(56)
        require(ha == hb and sha(ha) == expected['header_sha256'], 'native header')
        _, n, e, jobs, costs, cells, _ = struct.unpack('<7Q', ha)
        for name, size in [('row', (n+1)*8), ('node', n*16), ('edge', e*8),
                           ('cost', costs*8), ('job', jobs*24), ('cell', jobs*n*4)]:
            h = hashlib.sha256()
            left = size
            while left:
                x = fa.read(min(left, 8 << 20))
                require(bool(x) and x == fb.read(len(x)), 'native section ' + name)
                h.update(x)
                left -= len(x)
            require(h.hexdigest() == expected['sections'][name]['sha256'], 'native section hash ' + name)
        ta, tb = fa.read(), fb.read()
        require(len(ta) == len(tb) == jobs*cells*8, 'native tail size')
        require(sha(ta) == expected['original_embedded_golden_sha256'], 'original tail')
        require(sha(tb) == expected['native_ALT_tail_sha256'], 'native ALT tail')


def main(out):
    ev = Evidence(out)
    mb = json.loads(ev.lf('model_d/binding.json'))
    native = json.loads(ev.df('software_reuse_a/native_identity.json'))
    software = json.loads(ev.df('software_reuse_a/software_baselines.json'))
    for p, expected in mb['source_sha256'].items():
        require(sha(ev.lf('model_d/source/' + p)) == expected, 'model source ' + p)
    ev.local(mb['build_command'][-1], mb['binary_sha256'])
    for case in ['bnn_export', 'lstm_s2']:
        inp = mb['inputs'][case]
        for kind in ['workload', 'golden']:
            ev.local(inp[kind], inp[kind + '_sha256'], copy=kind == 'golden', note='frozen LF model input binding')
    print('verified LF source/binary/input closure', flush=True)

    cohorts = {
        'prepared': R2 + 'software_gpu_transform_complete/prepared_pop_gpu_b/',
        'control': R2 + 'software_private_inf_gpu_b_terminal/software/private_inf_gpu_b/',
    }
    bindings, summaries = {}, {}
    counts = {}
    for cohort, prefix in cohorts.items():
        bindings[cohort] = json.loads(ev.git(prefix + 'binding.json'))
        summaries[cohort] = json.loads(ev.git(prefix + 'summary.json'))
        ev.git(prefix + 'environment.json')
        names = sorted(n for n in ev.tree if n.startswith(prefix) and n.endswith('.receipt.json'))
        require(len(names) == summaries[cohort]['receipt_count'], 'receipt count')
        counts[cohort] = len(names)
        for n in names:
            require(json.loads(ev.git(n))['returncode'] == 0, 'failed frozen receipt ' + n)
        for name, expected in bindings[cohort]['source_sha256'].items():
            path = prefix + 'source/' + name
            if path not in ev.tree:
                path = SUP + name
            require(sha(ev.git(path)) == expected, 'GPU source ' + path)
    ev.git(SUP + 'manifest.json')
    # Include actual common headers from the fully bound control cohort for the
    # earlier prepared build, whose binding lists only its translation units.
    for name in ['bucket61.hpp', 'compact61.hpp', 'directory61.hpp', 'workload.hpp', 'io.hpp', 'backend.hpp']:
        ev.git(cohorts['control'] + 'source/' + name)
    gpu = {}
    for case, cohort, variant in [('bnn_export', 'prepared', 'compact'), ('lstm_s2', 'control', 'control_basic')]:
        prefix = cohorts[cohort]
        groups = []
        for process in range(3):
            stem = f'{case}_{variant}_p{process}'
            rec = json.loads(ev.git(prefix + stem + '.receipt.json'))
            rows = [json.loads(s) for s in ev.git(prefix + stem + '.jsonl').decode().splitlines()]
            ev.git(prefix + stem + '.stderr')
            require(len(rows) == 4 and rows[0]['warmup'] and all(not x['warmup'] for x in rows[1:]), 'warmup/repetitions')
            require([x['rep'] for x in rows] == list(range(4)), 'repeat order')
            require(all(x['scope'] == 'RESIDENT_COMPLETE_BATCH_V2' and x['output_equal'] and x['jobs'] == 40 and x['measured_GPU'] for x in rows), 'GPU scope/output')
            cmd = rec['command']
            require(cmd[1] == mb['inputs'][case]['workload'] and cmd[3] == mb['inputs'][case]['golden'], 'GPU input identity')
            require(cmd[5:] == ['4', 'basic' if cohort == 'control' else 'compact'], 'GPU command')
            binary_expected = bindings[cohort].get('binary_sha256', {}).get(Path(cmd[0]).name)
            binary = ev.local(cmd[0], binary_expected, note='historic binary binding' if binary_expected else 'original receipt names executable but omits historical binary digest; current bytes archived, not a retroactive execution-time hash')
            prep = json.loads(Path(cmd[2]).with_suffix('.json').read_text())
            ev.local(Path(cmd[2]).with_suffix('.json'))
            require(prep['workload_sha256'] == mb['inputs'][case]['workload_sha256'], 'prepared workload')
            ev.local(cmd[2], prep['prepared_sha256'], copy=False, note='prepared-CSR producer receipt')
            output_sha = mb['inputs'][case]['golden_sha256']
            op = prefix + stem + '.bin'
            if op in ev.tree:
                data = ev.git(op)
            elif op + '.gz' in ev.tree:
                data = gzip.decompress(ev.git(op + '.gz'))
            else:
                ev.local(cmd[4], output_sha)
                data = Path(cmd[4]).read_bytes()
            require(sha(data) == output_sha, 'GPU complete output')
            vals = [x['resident_s'] for x in rows[1:]]
            groups.append({'process': process, 'receipt': prefix + stem + '.receipt.json',
                           'raw_jsonl': prefix + stem + '.jsonl', 'raw_seconds': vals,
                           'mean_s': statistics.mean(vals), 'median_s': statistics.median(vals),
                           'start_unix': rec['start_unix'], 'end_unix': rec['end_unix'],
                           'waves': rows[1]['waves'], 'device_bytes': rows[1]['device_bytes'],
                           'binary_sha256': binary['sha256'], 'historically_bound_binary': binary_expected is not None})
        flat = [v for p in groups for v in p['raw_seconds']]
        hist = summaries[cohort]['cases'][case + '_' + variant]
        require(sorted(flat) == sorted(hist['raw_samples_s']), 'summary versus raw samples')
        means = [p['mean_s'] for p in groups]
        require(abs(statistics.mean(means) - hist['mean_s']) < 1e-14, 'summary mean')
        gpu[case] = {'cohort': cohort, 'variant': variant, 'scope': 'RESIDENT_COMPLETE_BATCH_V2',
                     'independent_processes': 3, 'formal_repeats_per_process': 3, 'processes': groups,
                     'mean_s': hist['mean_s'], 'pooled_repeat_median_s': statistics.median(flat),
                     'median_process_mean_s': statistics.median(means), 'process_mean_stdev_s': statistics.stdev(means),
                     'historical_pooled_repeat_stdev_s': hist['sample_stdev_s'],
                     'full_ALT_output_sha256': mb['inputs'][case]['golden_sha256']}
    print('verified 472 historical software receipts and strongest GPU 3x3 raw results', flush=True)

    ev.git(native['adapter_path'])
    require(sha((ROOT / native['adapter_path']).read_bytes()) == native['adapter_sha256'], 'native adapter')
    native_rows = []
    for x in native['cases']:
        for pathkey, hashkey in [('reused_import_receipt', 'reused_import_receipt_sha256'), ('qor_receipt', 'qor_receipt_sha256')]:
            ev.local(x[pathkey], x[hashkey])
        receipt = json.loads(Path(x['reused_import_receipt']).read_text())
        require(receipt['returncode'] == 0 and receipt['import_marker'] and receipt['map_equal'] and receipt['full_route_check'], 'native import')
        parent = Path(x['reused_import_receipt']).parent
        ev.local(parent / 'wire_map.bin', x['wire_map_sha256'])
        ev.local(parent / 'process.log')
        require('LA_IMPORT verified samples=40' in (parent / 'process.log').read_text(errors='replace'), 'native log marker')
        ev.local(receipt['effective_env']['VPR_LA_IMPORT'], x['new_output_sha256'])
        input_sections(x['workload_path'], x['native_input_path'], x['native_sections'])
        qor = json.loads(Path(x['qor_receipt']).read_text())
        require(qor['full_check_passed'], 'native FULL check')
        native_rows.append({'case': x['case'], 'ALT_sha256': x['new_output_sha256'],
                            'input_sections_verified_now': True, 'wire_map_sha256': x['wire_map_sha256'],
                            'critical_path_ns': qor['critical_path_ns'], 'wirelength': qor['wirelength'],
                            'STRICT_equivalent': False, 'new_VPR_runs': 0})
    # Original measured native scopes and qualification, including counterexamples.
    for path, info in software['sources'].items():
        if Path(path).is_absolute():
            ev.local(path, info['sha256'])
    for name in ['docs/lookahead_accel_round6_screen.md', 'docs/lookahead_accel_round6_1_native_compact.md',
                 'docs/lookahead_accel_round6_2_closeout.md', 'docs/lookahead_fpga_local_fabric.md']:
        ev.git(name)
    print('verified native input arrays, imports, maps and QoR without VPR execution', flush=True)

    prior = {}
    for case in ['bnn_export', 'lstm_s2']:
        summary = json.loads(ev.lf(f'model_d/L1_{case}_summary.json'))
        require(summary['complete_batch'] and summary['all_pass'] and len(summary['sample_receipts']) == 40, 'LF full batch')
        whole = bytearray()
        for sr in sorted(summary['sample_receipts'], key=lambda x: x['sample']):
            require(sr['returncode'] == 0 and sr['output_exact'] and sr['binary_sha256'] == mb['binary_sha256'], 'LF sample')
            require(sr['workload_sha256'] == mb['inputs'][case]['workload_sha256'] and sr['golden_sha256'] == mb['inputs'][case]['golden_sha256'], 'LF sample input')
            rel = sr['output_path'].split('/' + LF + '/', 1)[1]
            data = ev.lf(rel)
            require(sha(data) == sr['output_sha256'], 'LF sample output')
            whole.extend(data)
            for suffix in ['finite.json', 'pool_service.json', 'radix_service.json', 'capacity.csv', 'waves.csv']:
                ev.lf(str(Path(rel).parent / suffix))
        outdata = ev.lf(f'model_d/L1_{case}_output.bin')
        require(bytes(whole) == outdata and sha(outdata) == summary['full_output_sha256'] == mb['inputs'][case]['golden_sha256'], 'LF full output')
        ev.lf(f'full_pool_{case}.json')
        prior[case] = {k: v for k, v in summary.items() if k not in ['sample_receipts', 'traffic', 'per_sample_cycles']}
        counts0, phases = summary['counts'], summary['phase_cycles']
        require(sum(phases.values()) == summary['conditional_cycles'], 'LF phase sum')
        prior[case]['diagnostic'] = {
            'expand_fraction': phases['pop_expand'] / summary['conditional_cycles'],
            'finalize_fraction': phases['finalize'] / summary['conditional_cycles'],
            'candidate_per_expand_cycle': counts0['candidates'] / phases['pop_expand'],
            'fraction_of_64_lane_peak': counts0['candidates'] / phases['pop_expand'] / 64,
            'fixed_64_II1_lane_200MHz_edge_bound_s': counts0['candidates'] / (64 * 200e6),
            'assumed_LF_over_measured_GPU_time': summary['conditional_seconds'] / gpu[case]['mean_s'],
            'universal_FPGA_lower_bound': False}
    contrasts = json.loads(ev.lf('representative_analysis.json'))
    for cfg in ['L0', 'FS', 'L1', 'L2']:
        for case in ['bnn_export', 'lstm_s2']:
            ev.lf(f'model_d/{cfg}_{case}_representatives.json')
    for name in ['reused_evidence.json', 'native_identity_reuse.json', 'resource_budget.json', 'qualification.json',
                 'local_evidence_summary.json', 'timing_summary.json', 'representative_gate.json',
                 'model_d/full_L1_terminal.json', 'model_d/representative_L0L1L2FS_terminal.json']:
        ev.lf(name)
    for cfg in ['C0', 'F2']:
        for case in ['bnn_export', 'lstm_s2']:
            ev.df(f'model_d/{cfg}_{case}_summary.json')
    ev.df('model_d/binding.json')
    for service in ['large_l16_g1', 'large_l16_g2', 'large_l60_g2']:
        for case in ['bnn_export', 'lstm_s2']:
            name = R2 + f'checkpoint_20261114T042325Z_recovered_native/model/many32_p8_f0_request_model_a/{service}/{case}/receipt.json'
            rec = json.loads(ev.git(name))
            require(rec['returncode'] == 0 and rec['status'] == 'passed' and rec['whole_native_batch'] and rec['output_sha256'] == rec['golden_sha256'], 'old P8F0 receipt')
    result = {'schema': 'CPU_PRIMARY_REUSED_EVIDENCE_V1', 'base_commit': BASE,
              'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'research_goal': 'CPU_PRIMARY_GPU_COMPARATOR', 'requires_gpu_win': False,
              'new_GPU_runs': 0, 'new_old_model_runs': 0, 'new_native_VPR_runs': 0,
              'historical_files_modified': False, 'GPU_receipt_counts': counts,
              'strongest_GPU': gpu, 'native_identity': native_rows, 'prior_LF_full_models': prior,
              'prior_mechanism_contrasts': contrasts, 'native_E2_Process_rows': software['native_VPR_E2_Process'],
              'closure_limitations': ['Earlier prepared_pop_gpu_b execution receipts omit contemporaneous executable SHA; current retained binary is copied/hash-observed, source/build and raw outputs are frozen. Later LSTM control has historical binary SHA.',
                  'Earlier prepared build only binds two translation units; common headers are archived and verified against later control binding, not falsely backdated.',
                  'Native input section identity and unchanged adapter support transitive ALT map reuse, not a new native run or STRICT equivalence.',
                  'Historical LF timings are unqualified 200MHz architectural predictions; do not substitute them for newly integrated CPU_PRIMARY RTL/model.'],
              'scope_boundaries': {'resident_GPU_includes': ['mutable state/output initialization', 'all concurrent40-sample waves', 'kernel launch/host loop', 'per-wave completion D2H', 'final error D2H and event synchronize'],
                  'resident_GPU_excludes': ['input loading/CSR reconstruction/validation', 'allocation/H2D', 'full output D2H', 'INF-to-MISSING normalization', 'golden comparison/output file write'],
                  'E2': 'Required preparation+transfer+core+postprocessing on actual timeline; do not double count launch/control already inside resident; no invented FPGA transfer measurements.',
                  'Process': 'Native VPR whole-process scope including graph setup/build/route/FULL/STA; separate from resident and E2; stock resident timer absent.'},
              'files': ev.files, 'external_files': list(ev.external.values()),
              'script_sha256': file_sha(__file__), 'status': 'PASS'}
    with (out / 'index.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print('REUSE_EVIDENCE_PASS', len(ev.files), 'raw records;', len(ev.external), 'external hashes;', out / 'index.json')


def verify(out):
    x = json.loads((out / 'index.json').read_text())
    require(x['status'] == 'PASS', 'not final')
    seen = set()
    for row in x['files'].values():
        if row['object'] in seen:
            continue
        b = (out / row['object']).read_bytes()
        b = gzip.decompress(b) if row['compression'] == 'gzip' else b
        require(sha(b) == row['sha256'] and len(b) == row['bytes'], 'raw archive object')
        seen.add(row['object'])
    for row in x['external_files']:
        require(file_sha(row['path']) == row['sha256'], 'external changed ' + row['path'])
    require(file_sha(__file__) == x['script_sha256'], 'verification script changed')
    print('REUSE_ARCHIVE_VERIFY_PASS', len(x['files']), 'records', len(seen), 'unique objects')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=DEFAULT)
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()
    (verify if args.verify else main)(args.out.resolve())
