#!/usr/bin/env python3
"""Reconcile existing native CPU evidence; never execute a solver or alter inputs."""
import collections
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/native_cpu_direction_20261102'
EVIDENCE = ROOT / 'results/native_cpu_evidence_20261102'
BINDINGS = {}


def bind(path):
    path = path.resolve()
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    BINDINGS[str(path)] = h.hexdigest()
    return h.hexdigest()


def read(path):
    bind(path)
    return json.loads(path.read_text())


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def stats(values):
    return dict(median=statistics.median(values), min=min(values), max=max(values), values=values)


def phases():
    groups = collections.defaultdict(list)
    # Only disjoint outer timers enter the decomposition. Nested timers remain detail.
    names = {
        'circuit_preparation': ['Load circuit', 'Clean circuit', 'Compress circuit',
                                'Verify circuit', 'Build Timing Graph', 'Load Timing Constraints'],
        'packing_load_and_check': ['Load packing'],
        'device_creation_including_rr_load': ['Create Device'],
        'lookahead': ['Computing router lookahead map'],
        'routing': ['Routing'],
        'post_route_sync': ['Synchronize the packed netlist to routing optimization'],
    }
    for stage in ['triad', 'scaling']:
        summary = read(EVIDENCE / stage / 'serial/summary.json')
        for m in summary['measurements']:
            if m['cache_mode'] != 'rebuild':
                continue
            assert m['success'] and m['full_check'] and m['wire_map_matches_serial']
            log = Path(m['directory']) / 'process.log'
            bind(log)
            all_timers = collections.defaultdict(list)
            for name, val in re.findall(r'^#+ (.+?) took ([0-9.]+) seconds', log.read_text(), re.M):
                all_timers[name].append(float(val))
            for ns in names.values():
                for n in ns:
                    assert len(all_timers[n]) == 1, (m['key'], n, all_timers[n])
            timing = {k: sum(all_timers[n][0] for n in ns) for k, ns in names.items()}
            total = m['process_seconds']
            timing['other_unassigned'] = total - sum(timing.values())
            assert timing['other_unassigned'] >= 0
            assert abs(sum(timing.values()) - total) < 1e-8
            for key, name in [('lookahead', 'lookahead_build'), ('routing', 'routing')]:
                assert timing[key] == m['log_evidence']['stage_seconds'][name]
            look = timing['lookahead']
            groups[(m['workers'], m['variant'])].append({
                'key': m['key'], 'repeat': m['repeat'], 'process_seconds': total,
                'workflow_seconds': m['workflow_seconds'], 'phase_seconds': timing,
                'rr_load_nested_seconds': all_timers['Loading routing resource graph'][0],
                'all_timers_seconds': dict(all_timers),
                'lookahead_fraction': look / total,
                'ideal_speedup_if_lookahead_free': total / (total - look),
                'speedup_if_lookahead_halved': total / (total - look / 2),
            })
    configurations = []
    for (workers, variant), rows in sorted(groups.items()):
        assert len(rows) == 3
        configurations.append({
            'workers': workers, 'variant': variant, 'samples': rows,
            'process_seconds': stats([r['process_seconds'] for r in rows]),
            'phase_seconds': {k: stats([r['phase_seconds'][k] for r in rows]) for k in rows[0]['phase_seconds']},
            'rr_load_nested_seconds': stats([r['rr_load_nested_seconds'] for r in rows]),
            **{k: stats([r[k] for r in rows]) for k in [
                'lookahead_fraction', 'ideal_speedup_if_lookahead_free', 'speedup_if_lookahead_halved']},
        })
    evidence = read(EVIDENCE / 'analysis.json')
    comparisons = [c for c in evidence['comparisons'] if c['case'] == 'gemm']
    for c in comparisons:
        if c['cache'] != 'rebuild':
            continue
        a = {r['repeat']: r for r in groups[c['workers'], c['control']]}
        b = {r['repeat']: r for r in groups[c['workers'], c['candidate']]}
        ratios = [a[r]['process_seconds'] / b[r]['process_seconds'] for r in sorted(a)]
        assert abs(statistics.median(ratios) - c['process_ratio']['median']) < 1e-10
    return {'configurations': configurations, 'existing_paired_comparisons': comparisons,
            'accounting': 'Per-run outer timers, then summary. RR load is nested in Create Device; packed-file load in Load packing; wire/src in lookahead. Cumulative Flow timing analysis is not added. Other includes all unassigned work and process boundary overhead. Conditional headroom holds all other costs fixed.'}


def inventory():
    directory = ROOT.parent / '3D_FPGA_routing/benchmarks/downloads/beyond_flatland'
    arch = ROOT.parent / '3D_FPGA_routing/configs/architectures/koios_native3d_n6_f16_d1_v3.xml'
    bind(arch)
    models = {m.attrib['name'] for m in ET.parse(arch).getroot().findall('./models/model')}
    mainline = {'gemm_layer', 'clstm_like.large', 'softmax', 'reduction_layer'}
    rows = []
    for path in sorted(directory.glob('*.blif')):
        counts = collections.Counter()
        subckts = collections.Counter()
        h = hashlib.sha256()
        with path.open('rb') as f:
            for line in f:
                h.update(line)
                if line.startswith(b'.'):
                    fields = line.split(maxsplit=2)
                    directive = fields[0].decode()
                    counts[directive] += 1
                    if directive == '.subckt':
                        subckts[fields[1].decode()] += 1
        BINDINGS[str(path.resolve())] = h.hexdigest()
        rows.append(dict(name=path.stem, path=str(path.resolve()), sha256=h.hexdigest(),
                         bytes=path.stat().st_size, directives=dict(counts), subcircuit_models=dict(subckts),
                         approximate_instances=sum(counts[x] for x in ['.names', '.latch', '.subckt']),
                         models_missing_from_architecture=sorted(set(subckts) - models),
                         already_in_mainline_six_circuit_suite=path.stem in mainline,
                         historical_references=[]))
    # Positive evidence of previous use, not a claim of exhaustively searching every artifact.
    scopes = [ROOT / 'results', ROOT / 'data', ROOT.parent / '3D_FPGA_routing/results']
    cmd = ['rg', '--files', '--no-ignore', '-g', '*manifest*.json', '-g', '*plan*.json', '-g', 'vpr_case.json']
    listing = subprocess.run(cmd + list(map(str, scopes)), check=True, capture_output=True, text=True).stdout
    searched = 0
    for filename in sorted(listing.splitlines()):
        p = Path(filename)
        if OUT in p.parents:
            continue
        content = p.read_text(errors='replace')
        searched += 1
        used = [r for r in rows if r['name'] + '.blif' in content and len(r['historical_references']) < 3]
        if used:
            bind(p)
            for r in used:
                r['historical_references'].append(str(p.resolve()))
    for r in rows:
        r['prior_use_status'] = 'prior_reference_found_not_independent' if r['historical_references'] else 'not_found_in_scanned_manifests_not_proof_of_novelty'
    return dict(architecture=str(arch.resolve()), architecture_sha256=BINDINGS[str(arch.resolve())],
                architecture_models=sorted(models), scanned_metadata_files=searched, circuits=rows,
                limitation='Directive counts are only an input-size proxy, not packed block count or RR graph size. Model-name inclusion is necessary, not a pack/place compatibility test. References can be plans or runs and do not prove successful completion. This is the existing Koios suite, not an independent benchmark source.')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bind(Path(__file__))
    for name in ['base/vpr_api.cpp', 'base/read_circuit.cpp', 'pack/post_routing_pb_pin_fixup.cpp']:
        bind(ROOT / 'vendor/vtr_cpu_paper/vpr/src' / name)
    result = phases()
    result['status'] = 'existing_evidence_analysis_complete'
    result['default_changed'] = False
    result['new_solver_runs'] = 0
    result['repeat_study_aggregates'] = read(ROOT / 'results/native_cpu_repeat_20261102/analysis.json')['aggregates']
    for label, dirname in [('bounded_selection', 'native_cpu_slices_20261101'),
                            ('state_ablation', 'native_state_ablation_20261102'),
                            ('state_trace', 'native_state_trace_20261102')]:
        result[label] = read(ROOT / f'results/{dirname}/conclusions.json')
    result['skip_candidate'] = read(ROOT / 'results/native_partition_skip_20261102/analysis.json')
    save('analysis.json', result)
    save('circuit_inventory.json', inventory())
    save('source_bindings.json', {'sha256': BINDINGS, 'scope': 'Inputs actually used by this derived analysis; does not replace the original study audits.'})
    for c in result['configurations']:
        print(c['workers'], c['variant'], 'process', round(c['process_seconds']['median'], 3),
              'lookahead', round(c['phase_seconds']['lookahead']['median'], 3),
              'fraction', round(c['lookahead_fraction']['median'], 4),
              'ceiling', round(c['ideal_speedup_if_lookahead_free']['median'], 4))


if __name__ == '__main__':
    main()
