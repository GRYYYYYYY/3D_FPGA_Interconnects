"""Single-owner, fail-closed preparation/qualification/formal native CPU chain."""
import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys

from native_cpu_budget import audited_process, pin_budget
from prepare import sha256, write_json
from scaling_common import verified, vpr_environment

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/native_cpu_large_20261102'
SPEC = ROOT / 'results/native_cpu_direction_20261102/next_experiment.json'
WRAPPER = ROOT / 'scripts/run_native_cpu_large_lane.py'


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def binding(path):
    return {'path': str(path.resolve()), 'sha256': sha256(path)}


def freeze():
    OUT.mkdir(exist_ok=False)
    shutil.copyfile(ROOT / 'HANDOFF.md', OUT / 'HANDOFF.before_study.md')
    spec = read(SPEC)
    base = read(ROOT / 'results/native_cpu_evidence_20261102/triad_plan.json')
    # Verify legacy provenance once before admitting any new process.
    for entry in [spec['architecture'], *spec['circuits'], *spec['binaries'].values(), *base['runner_bindings'].values()]:
        verified(entry)
    cases = [(f'{c["name"]}_s{s}', c, s) for c in spec['circuits'] for s in spec['seeds']]
    protocol = dict(status='frozen', started_utc=now(), source_spec=binding(SPEC),
                    preparation_timeout_seconds=3600, routing_timeout_seconds=900,
                    preparation_scope='Original-VPR pack/place only, default annealing settings, one physical core; explicit place channel width 100 creates and writes native RR graph. No preparatory routing quality is assumed.',
                    cpu_pool=list(range(32, 40)), exclusivity=False, luna_delegation_available=False,
                    memory_limit_gib=64, core_dump_limit_mib=512, default_changed=False,
                    qualification_samples=30, conditional_formal_samples=144,
                    conditional_16core='Not automatically queued; requires eight-core analysis.',
                    qualification_failure='Stop before the entire formal matrix on any failed input/endpoint/map/legality/QoR gate; no width, circuit or seed replacement.',
                    preparation_jobs=[], runtime=base['runtime'],
                    binary_bindings=spec['binaries'], runner_bindings=copy.deepcopy(base['runner_bindings']))
    for p in [Path(__file__), WRAPPER, ROOT / 'scripts/verify_native_cpu_study.py']:
        protocol['runner_bindings'][p.name] = binding(p)
    for case_id, circuit, seed in cases:
        d = OUT / 'prepared' / case_id
        cmd = [spec['binaries']['original']['path'], spec['architecture']['path'], circuit['path'],
               '--pack', '--place', '--route_chan_width', '100', '--place_chan_width', '100',
               '--device_width', '0', '--target_utilization', '0.6', '--seed', str(seed),
               '--num_workers', '1', '--flat_routing', 'off', '--check_route', 'full',
               '--net_file', str(d / 'packed.net'), '--place_file', str(d / 'fixed.place'),
               '--write_rr_graph', str(d / 'rr_graph.xml'), '--timing_report_npaths', '10']
        protocol['preparation_jobs'].append(dict(case=case_id, circuit=circuit, seed=seed, directory=str(d), command=cmd))
    for stage, variants, repeats, caches in [
        ('qualification', ['reference', 'stock', 'fixed_serial', 'per_group', 'pipeline'], 1, ['rebuild']),
        ('formal', ['stock', 'fixed_serial', 'per_group', 'pipeline'], 3, ['rebuild', 'reuse'])]:
        plan = copy.deepcopy(base)
        plan.update(output=str(OUT / stage), binaries=spec['binaries'], variants=copy.deepcopy(spec['variants']),
                    timeout_seconds=900, max_active_cpu_cores=8, diagnostics=False,
                    runner_bindings=protocol['runner_bindings'], qualification_env={},
                    planned_samples=len(cases)*len(variants)*repeats*len(caches),
                    concurrency_scope='One owned solver at a time on physical CPUs32-39, shared host including adjacent project activity; no exclusivity.',
                    repeats_scope='Two fresh layouts per circuit; formal has three runtime repeats per layout. Qualification is not performance evidence.',
                    promotion_rule=spec['promotion_gate'],
                    qualification_exception='Only deliberately unconverged cache setup disables overuse report; all measurement rows keep it enabled.')
        if stage == 'qualification':
            plan['variants']['reference'] = dict(binary='frozen', parallel=True, env={'VPR_HYBRID_LOOKAHEAD_TASKS': '0'})
        lane = dict(cpu_pool=list(range(32, 40)), cases=[])
        for index, (case_id, _, _) in enumerate(cases):
            phases = []
            for rep in range(repeats):
                shift = (index + rep) % len(variants)
                desired = variants[shift:] + variants[:shift]
                # The immutable runner rotates again by repeat, so undo that here.
                offset = rep % len(desired)
                declared = desired[-offset:] + desired[:-offset] if offset else desired
                for cache in (caches if (index+rep)%2 == 0 else caches[::-1]):
                    phases.append(dict(name=stage, variants=declared, workers=[8], cache_modes=[cache],
                                       repeats=1, repeat_start=rep, intended_execution_order=desired))
            lane['cases'].append(dict(id=case_id, vpr_case=str(OUT/'prepared'/case_id/'vpr_case.json'), phases=phases))
        plan['lanes'] = {'serial': lane}
        write_json(OUT / f'{stage}_plan.json', plan)
    write_json(OUT / 'protocol.json', protocol)
    print('Frozen:', OUT, flush=True)


def geometry(directory):
    text = (directory / 'fixed.place').read_text()
    coords, layers = [], Counter()
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 6 and fields[-1].startswith('#') and not line.startswith('#'):
            xyz = tuple(map(int, fields[1:5]))
            coords.append((fields[0], *xyz))
            layers[xyz[-1]] += 1
    assert coords and set(layers) == {0, 1}, layers
    rr = directory / 'rr_graph.xml'
    nodes = edges = 0
    # Streaming lexical inventory of VPR's own XML; native VPR validates on reload.
    with rr.open('rb') as f:
        for line in f:
            nodes += bool(re.match(rb'\s*<node\s+id=', line))
            edges += bool(re.match(rb'\s*<edge\s+', line))
    assert nodes > 0 and edges > 0
    return dict(placed_blocks=len(coords), placement_layers=dict(layers),
                coordinate_sha256=hashlib.sha256(json.dumps(sorted(coords)).encode()).hexdigest(),
                grid=re.findall(r'Array size: (.+)', text), rr_nodes=nodes, rr_edges=edges, rr_bytes=rr.stat().st_size)


def prepare(protocol, state):
    spec = read(SPEC)
    for entry in protocol['binary_bindings'].values():
        verified(entry)
    verified(spec['architecture'])
    env = vpr_environment(read(Path(protocol['runtime'])))
    env = {k: v for k, v in env.items() if not k.startswith(('VPR_CPU_', 'VPR_HYBRID_', 'H3D_GPU_'))}
    resource.setrlimit(resource.RLIMIT_AS, (64*1024**3, 64*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (512*1024**2, 512*1024**2))
    os.sched_setaffinity(0, protocol['cpu_pool'])
    budget = pin_budget(1)
    receipt = dict(status='running', started_utc=now(), cpu_budget=budget, runs=[])
    (OUT / 'prepared').mkdir()
    for job in protocol['preparation_jobs']:
        assert shutil.disk_usage(OUT).free > 80*1024**3, 'Less than 80GiB free; review capacity before proceeding'
        verified(job['circuit'])
        directory = Path(job['directory']); directory.mkdir()
        row = dict(case=job['case'], directory=str(directory), command=job['command'], status='running', started_utc=now())
        receipt['runs'].append(row)
        state['current_case'] = job['case']; write_json(OUT/'supervisor.json', state)
        write_json(OUT/'preparation.json', receipt)
        row.update(audited_process(job['command'], directory, env, protocol['preparation_timeout_seconds']))
        text = (directory/'process.log').read_text(errors='replace')
        names = {'architecture': Path(spec['architecture']['path']), 'circuit': Path(job['circuit']['path']),
                 'packed_netlist': directory/'packed.net', 'placement': directory/'fixed.place', 'rr_graph': directory/'rr_graph.xml'}
        ready = (row['returncode'] == 0 and row['cpu_budget_audit']['verified']
                 and 'Completed placement consistency check successfully' in text
                 and all(p.exists() and p.stat().st_size for p in names.values()))
        row['inputs_ready'] = bool(ready)
        if ready:
            try:
                row['geometry'] = geometry(directory)
                case = dict(id=job['case'], circuit_id=job['circuit']['name'], placement_seed=job['seed'], seed=job['seed'],
                            route_chan_width=100, device_width=0, target_utilization=.6,
                            inputs={k: binding(p) for k, p in names.items()},
                            geometry=row['geometry'], scope='Fresh original pack/place and native RR generation; fixed inputs reused by all arms. No routing legality assumed until qualification.')
                write_json(directory/'vpr_case.json', case)
                row['case_binding'] = binding(directory/'vpr_case.json')
            except Exception as exc:
                row.update(inputs_ready=False, validation_error=repr(exc))
        row['finished_utc'] = now()
        write_json(directory/'preparation_receipt.json', row)
        write_json(OUT/'preparation.json', receipt)
        print(json.dumps({k: row.get(k) for k in ['case', 'inputs_ready', 'process_seconds', 'validation_error']}), flush=True)
    receipt['different_layouts'] = all(
        a.get('geometry', {}).get('coordinate_sha256') != b.get('geometry', {}).get('coordinate_sha256')
        for a, b in zip(receipt['runs'][::2], receipt['runs'][1::2]))
    receipt['status'] = 'completed' if all(r['inputs_ready'] for r in receipt['runs']) and receipt['different_layouts'] else 'failed'
    receipt['finished_utc'] = now(); write_json(OUT/'preparation.json', receipt)
    if receipt['status'] != 'completed':
        raise RuntimeError('Preparation/geometry gate failed; formal matrix not admitted')


def gate():
    summary = read(OUT/'qualification/serial/summary.json')
    rows = summary['measurements']
    report = dict(status='passed', total=len(rows), failures=[], cases=[])
    assert len(rows) == 30 and summary['status'] == 'completed'
    for case in read(OUT/'qualification_plan.json')['lanes']['serial']['cases']:
        arms = {r['variant']: r for r in rows if r['case'] == case['id']}
        record = {'case': case['id'], 'legal': all(r['success'] and r.get('wire_map_matches_serial') for r in arms.values()), 'comparisons': []}
        keys = ['route_body_sha256', 'critical_path_ns', 'wirelength', 'iterations']
        record['old_endpoint_identical'] = all(arms['reference'].get(k) == arms['per_group'].get(k) for k in keys)
        for control, candidate in [('fixed_serial','per_group'), ('fixed_serial','pipeline'), ('per_group','pipeline')]:
            x, y = arms[control], arms[candidate]
            ratios = {k: y[k]/x[k] if x.get(k) and y.get(k) else None for k in ['critical_path_ns','wirelength']}
            passed = x['success'] and y['success'] and all(v is not None and v <= 1.05+1e-12 for v in ratios.values())
            record['comparisons'].append(dict(control=control, candidate=candidate, quality_passed=passed, ratios=ratios,
                                              same_route=x.get('route_body_sha256') == y.get('route_body_sha256')))
        record['passed'] = record['legal'] and record['old_endpoint_identical'] and all(c['quality_passed'] for c in record['comparisons'])
        report['cases'].append(record)
        if not record['passed']: report['failures'].append(case['id'])
    report['status'] = 'passed' if not report['failures'] else 'failed'
    write_json(OUT/'qualification_gate.json', report)
    return report['status'] == 'passed'


def run():
    protocol = read(OUT/'protocol.json')
    verified(protocol['source_spec'])
    for entry in protocol['runner_bindings'].values(): verified(entry)
    with (OUT/'owner.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUT/'supervisor.json').exists(): raise RuntimeError('Existing chain: inspect original owner; no implicit restart')
        state = dict(status='running', pid=os.getpid(), started_utc=now(), current='prepare', steps=[],
                     default_changed=False, policy='One owner, no automatic retries, no solver overlaps, no default promotion.')
        write_json(OUT/'supervisor.json', state)

        def child(name, command):
            state.update(current=name, current_case=None)
            step = dict(name=name, command=command, status='running'); state['steps'].append(step)
            with (OUT/f'{name}.log').open('x') as log:
                process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                step['pid'] = process.pid; write_json(OUT/'supervisor.json', state)
                rc = process.wait()
            step.update(returncode=rc, status='completed' if rc == 0 else 'failed', finished_utc=now())
            write_json(OUT/'supervisor.json', state)
            if rc: raise RuntimeError(name + ' failed; preserve logs and review')

        try:
            prepare(protocol, state)
            # Restore the full pool after the one-core preparation worker.
            os.sched_setaffinity(0, protocol['cpu_pool'])
            for stage in ['qualification', 'formal']:
                (OUT/stage).mkdir()
                path = OUT/f'{stage}_plan.json'
                child(stage, [sys.executable, str(WRAPPER), '--plan', str(path), '--lane', 'serial'])
                child(stage+'_audit', [sys.executable, str(ROOT/'scripts/verify_native_cpu_study.py'), '--plan', str(path), '--output', str(OUT/f'{stage}_audit.json')])
                if stage == 'qualification' and not gate():
                    state.update(status='complete_qualification_rejected', current=None, formal_started=False)
                    return
            state.update(status='measurements_and_audit_complete', current=None, formal_started=True,
                         next='Analyze all 144 formal samples, including failures, before any 16-core extension or promotion.')
        except Exception as exc:
            state.update(status='stopped_for_review', error=repr(exc))
            raise
        finally:
            state['finished_utc'] = now()
            write_json(OUT/'supervisor.json', state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'run'])
    args = parser.parse_args()
    freeze() if args.action == 'freeze' else run()
