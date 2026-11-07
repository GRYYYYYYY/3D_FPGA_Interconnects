#!/usr/bin/env python3
"""Independent directed-tree/capacity audit of h3d_route JSON results."""
import argparse
from collections import Counter
import json
from pathlib import Path
from prepare import sha256, write_json


def audit(graph_path, nets_path, result_path):
    result = json.loads(Path(result_path).read_text())
    routes = result['routes']
    wanted_nodes = {v for r in routes for v in r['nodes']}
    wanted_edges = {v for r in routes for v in r['edges']}
    node_map, nodes, edges = [], {}, {}
    with open(graph_path) as f:
        magic, version, n, m = f.readline().split()
        if magic != 'H3DRRG' or version != '1':
            raise ValueError('Invalid graph header')
        for _ in range(int(n)):
            fields = f.readline().split(None, 1)
            node_id = int(fields[0]);node_map.append(node_id)
            if node_id in wanted_nodes:
                nodes[node_id] = (node_id, *map(int, fields[1].split()))
        for _ in range(int(m)):
            fields = f.readline().split(None, 1)
            edge_id = int(fields[0])
            if edge_id in wanted_edges:
                row = tuple(map(int, fields[1].split()))
                edges[edge_id] = (node_map[row[0]], node_map[row[1]], *row[2:])
    if wanted_nodes != nodes.keys() or wanted_edges != edges.keys():
        raise ValueError('Unknown node or edge')
    expected = {}
    with open(nets_path) as f:
        magic, version, count = f.readline().split()
        if magic != 'H3DNETS' or version != '1':
            raise ValueError('Invalid net header')
        for _ in range(int(count)):
            ni, src, ns, *sinks = map(int, f.readline().split())
            if ns != len(sinks) or ni in expected:
                raise ValueError('Invalid terminals')
            expected[ni] = (node_map[src], {node_map[s] for s in sinks})
    if len(routes) != len(expected) or {r['net'] for r in routes} != expected.keys():
        raise ValueError('Missing/duplicated/unexpected nets')
    occupancy, total_wire, vertical_nodes, vertical_entries, unrouted = Counter(), 0, 0, 0, 0
    for r in routes:
        if not r['connected']:
            if r['nodes'] or r['edges']:
                raise ValueError('Failed net retains partial resources')
            unrouted += 1
            continue
        src, sinks = expected[r['net']]
        vertices = set(r['nodes'])
        if len(vertices) != len(r['nodes']) or len(set(r['edges'])) != len(r['edges']):
            raise ValueError('Duplicate resource in net')
        reached, parent, adjacency = {src}, {}, {}
        for ei in r['edges']:
            u, v, _, _, vertical = edges[ei]
            if u not in vertices or v not in vertices or v in parent or v == src:
                raise ValueError('Invalid tree endpoint/multiple parents/root cycle')
            parent[v] = u
            adjacency.setdefault(u, []).append(v)
            vertical_entries += vertical
        stack = [src]
        while stack:
            for v in adjacency.get(stack.pop(), []):
                if v in reached:
                    raise ValueError('Directed cycle')
                reached.add(v)
                stack.append(v)
        if reached != vertices or not sinks <= reached:
            raise ValueError('Disconnected tree or missing sink')
        occupancy.update(vertices)
        for v in vertices:
            row = nodes[v]
            if row[1] in (4,5,6):
                total_wire += abs(row[6]-row[3])+abs(row[7]-row[4])+abs(row[8]-row[5])+1
            vertical_nodes += row[1] == 6
    overflow = sum(max(0, count-nodes[v][2]) for v, count in occupancy.items())
    legal = overflow == 0 and unrouted == 0
    if result['success'] != legal:
        raise ValueError('Reported success disagrees with independent audit')
    if result['iterations'][-1]['overflow'] != overflow or result['iterations'][-1]['unrouted'] != unrouted:
        raise ValueError('Reported iteration counters disagree with audit')
    return {'audit_passed': True, 'legal_in_projection': legal, 'overflow': overflow, 'unrouted': unrouted,
            'wire_units_proxy': total_wire, 'chanz_uses_per_net': vertical_nodes,
            'vertical_entries_per_net': vertical_entries, 'net_count': len(routes),
            'vpr_full_check': False, 'critical_path_ns': None,
            'result_sha256': sha256(result_path)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('graph', type=Path)
    p.add_argument('nets', type=Path)
    p.add_argument('result', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    report = audit(a.graph, a.nets, a.result)
    if a.output:
        write_json(a.output, report)
    print(json.dumps(report))
