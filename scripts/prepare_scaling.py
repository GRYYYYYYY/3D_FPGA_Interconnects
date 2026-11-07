#!/usr/bin/env python3
"""Freeze real, previously routed circuits for paired VPR/CUDA scale experiments.

Sibling inputs are read-only. Graph projection and endpoint extraction are
offline preparation, recorded separately from online process measurements.
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import time

from prepare import convert, sha256, terminals, write_json, xml_database

ROOT = Path(__file__).resolve().parents[1]
SIBLING = ROOT.parent/'3D_FPGA_routing'
G_ROOT = ROOT.parent/'FPGA_accelerate_FPGA/G_3d_routing'
CASES = [
    ('ex5p', 'control', 'runs/fixture_ex5p_a0'),
    ('softmax', 'scale', 'runs/koios_a0a4_seed1_softmax_a0'),
    ('clstm_large', 'scale', 'runs/koios_a0a4_seed1_clstm_like.large_a0'),
    ('reduction', 'scale', 'runs/koios_a0a4_seed1_reduction_layer_a0'),
    ('gemm', 'scale', 'runs/koios_a0a4_seed1_gemm_layer_a0'),
    ('elliptic', 'congestion', 'failure_diagnosis/runs/off200__elliptic_seed1__a0'),
]


def prepare_one(item, output):
    name, category, source = item
    start = time.perf_counter()
    directory = output/name
    directory.mkdir()
    manifest_path = SIBLING/'results'/source/'manifest.json'
    original = json.loads(manifest_path.read_text())
    if not original['metrics']['native_full_check_passed'] or original.get('experimental_environment'):
        raise ValueError('Expected clean original VPR with a FULL-checked route')
    inputs = {k:v for k,v in original['inputs'].items() if k != 'binary'}
    for record in [original['inputs']['binary'], *inputs.values()]:
        if sha256(record['path']) != record['sha256']:
            raise ValueError(f'Frozen input changed: {record["path"]}')
    reference = manifest_path.parent/'routed.route'
    if sha256(reference) != original['outputs']['routed.route']['sha256']:
        raise ValueError('Frozen reference route changed')
    nets, excluded = terminals(reference)
    def setting(name, flag, cast, default):
        if name in original:
            return original[name]
        cmd = original['command']
        return cast(cmd[cmd.index(flag)+1]) if flag in cmd else default
    frozen = {
        'id': name, 'category': category, 'inputs': inputs,
        'route_chan_width': setting('route_chan_width','--route_chan_width',int,100),
        'device_width': setting('device_width','--device_width',int,0),
        'seed': setting('seed','--seed',int,1),
        'target_utilization': setting('target_utilization','--target_utilization',float,0.1),
        'reference': {'route': {'path': str(reference), 'sha256': sha256(reference)},
                      'manifest': {'path': str(manifest_path), 'sha256': sha256(manifest_path)},
                      'metrics': original['metrics']},
        'nets': len(nets), 'sinks': sum(len(n['sinks']) for n in nets),
        'max_fanout': max(len(n['sinks']) for n in nets),
        'scope': 'Exact fixed architecture, placement, packed netlist and RRG; reference intermediate paths are not routing inputs.',
    }
    write_json(directory/'vpr_case.json', frozen)
    if name in ('ex5p', 'elliptic'):
        database = G_ROOT/'data/derived/ex5p_w100/rr_graph.sqlite'
        # Both circuits use the exact same native graph; confirm by content.
        import sqlite3
        with sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True) as db:
            graph_source = json.loads(db.execute("SELECT value FROM metadata WHERE key='summary'").fetchone()[0])['source']
        if graph_source['sha256'] != inputs['rr_graph']['sha256']:
            raise ValueError('Shared graph hash mismatch')
    else:
        database = directory/'rr_graph.sqlite'
        xml_database(Path(inputs['rr_graph']['path']), database)
        if sha256(inputs['rr_graph']['path']) != inputs['rr_graph']['sha256']:
            raise ValueError('Graph changed during conversion')
    for cost in ('unit', 'delay_proxy'):
        convert(database, reference, directory/cost, cost=cost, baseline=manifest_path)
    frozen['preparation_seconds'] = time.perf_counter()-start
    frozen['projection'] = {cost: str(directory/cost) for cost in ('unit','delay_proxy')}
    write_json(directory/'prepared.json', frozen)
    print(name, 'prepared', round(frozen['preparation_seconds'], 2), flush=True)
    return frozen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--workers', type=int, default=2)
    p.add_argument('--cases', nargs='+', choices=[x[0] for x in CASES])
    a = p.parse_args()
    output = a.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    selected = [x for x in CASES if a.cases is None or x[0] in a.cases]
    plan = {'status':'preparing', 'cases':[], 'errors':[],
            'vpr_lock': str(G_ROOT/'configs/vpr.lock.json'),
            'quality_budgets_percent':[5,10,20],
            'max_router_iterations':200,
            'timing_scope': 'Fixed-placement route-through-FULL/STA. Offline graph projection reported separately; GPU workflow includes route process, audit, export, VPR FULL/STA.'}
    write_json(output/'suite.json', plan)
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as executor:
        futures = {executor.submit(prepare_one, item, output):item[0] for item in selected}
        for future in concurrent.futures.as_completed(futures):
            try:
                value = future.result()
                plan['cases'].append({'id':value['id'], 'category':value['category'],
                                      'vpr_case':str(output/value['id']/'vpr_case.json'),
                                      'prepared':str(output/value['id']/'prepared.json'),
                                      'projection':value['projection']})
            except Exception as exc:
                plan['errors'].append({'id':futures[future],'error':str(exc)})
            write_json(output/'suite.json', plan)
    plan['cases'].sort(key=lambda x:[i[0] for i in selected].index(x['id']))
    plan['status'] = 'failed' if plan['errors'] else 'prepared'
    write_json(output/'suite.json', plan)
    return 1 if plan['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
