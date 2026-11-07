#!/usr/bin/env python3
"""Import a VTR/LaZagna XML RRG or the existing G-project SQLite projection.

Output costs are positive integer surrogates, not VPR RC timing. Switch identity,
directed parallel edges, layer spans and per-RR-node capacities are preserved.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import tempfile
import xml.etree.ElementTree as ET

KINDS = {name: i for i, name in enumerate(('SOURCE', 'SINK', 'IPIN', 'OPIN', 'CHANX', 'CHANY', 'CHANZ'))}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def xml_database(path, database):
    """Bounded XML memory; use a temporary SQLite spool for large graphs."""
    db = sqlite3.connect(database)
    db.executescript('''
    CREATE TABLE nodes(id INTEGER PRIMARY KEY,kind TEXT,capacity INTEGER,
      xlow INTEGER,ylow INTEGER,layer_low INTEGER,xhigh INTEGER,yhigh INTEGER,layer_high INTEGER,
      ptc TEXT,r_ohm REAL,c_farad REAL);
    CREATE TABLE switches(id INTEGER PRIMARY KEY,kind TEXT,tdel_seconds REAL,r_ohm REAL);
    CREATE TABLE edges(id INTEGER PRIMARY KEY,src INTEGER,dst INTEGER,switch_id INTEGER);
    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
    ''')
    stack, count, batch = [], 0, []
    for event, el in ET.iterparse(path, events=('start', 'end')):
        if event == 'start':
            stack.append(el)
            if len(stack) == 1 and el.tag != 'rr_graph':
                raise ValueError('Expected rr_graph XML')
            continue
        if len(stack) == 3:
            section, a = stack[1].tag, el.attrib
            if section == 'rr_nodes' and el.tag == 'node':
                loc = el.find('loc').attrib
                low = int(loc.get('layer_low', loc.get('layer', '0')))
                high = int(loc.get('layer_high', loc.get('layer', '0')))
                timing = el.find('timing')
                timing = {} if timing is None else timing.attrib
                db.execute('INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                           (int(a['id']), a['type'], int(a['capacity']), int(loc['xlow']), int(loc['ylow']),
                            low, int(loc['xhigh']), int(loc['yhigh']), high, loc.get('ptc'),
                            float(timing['R']) if 'R' in timing else None,
                            float(timing['C']) if 'C' in timing else None))
            elif section == 'switches' and el.tag == 'switch':
                timing = el.find('timing')
                delay = None if timing is None or 'Tdel' not in timing.attrib else float(timing.get('Tdel'))
                resistance = None if timing is None or 'R' not in timing.attrib else float(timing.get('R'))
                db.execute('INSERT INTO switches VALUES (?,?,?,?)', (int(a['id']), a['type'], delay, resistance))
            elif section == 'rr_edges' and el.tag == 'edge':
                batch.append((count, int(a['src_node']), int(a['sink_node']), int(a['switch_id'])))
                count += 1
                if len(batch) >= 8192:
                    db.executemany('INSERT INTO edges VALUES (?,?,?,?)', batch)
                    batch.clear()
            stack[1].remove(el)
        elif len(stack) == 2:
            stack[0].remove(el)
        stack.pop()
    db.executemany('INSERT INTO edges VALUES (?,?,?,?)', batch)
    db.execute('INSERT INTO metadata VALUES (?,?)', ('summary', json.dumps({
        'source': {'path': str(Path(path).resolve()), 'sha256': sha256(path)},
        'edges': count, 'schema_version': 2})))
    db.commit()
    db.close()


def terminals(path):
    """Use only SOURCE/SINK endpoints, never reference route intermediate nodes."""
    nets, current, excluded = [], None, 0
    for line in Path(path).read_text().splitlines():
        header = re.match(r'^Net\s+(\d+)\s+\((.*)\)(.*)$', line)
        if header:
            current = None
            if 'global net' in header[3]:
                excluded += 1
            else:
                current = {'id': int(header[1]), 'name': header[2], 'sources': [], 'sinks': []}
                nets.append(current)
        node = re.match(r'^Node:\s*(\d+)\s+(SOURCE|SINK)\b', line)
        if node and current is not None:
            current['sources' if node[2] == 'SOURCE' else 'sinks'].append(int(node[1]))
    selected = []
    for net in nets:
        if not net['sources'] and not net['sinks']:
            excluded += 1
            continue
        if len(set(net['sources'])) != 1 or len(set(net['sinks'])) != len(net['sinks']):
            raise ValueError(f"Net {net['id']}: ambiguous driver or repeated SINK class; use pin-aware VPR integration")
        net['source'] = net.pop('sources')[0]
        if net['sinks']:
            selected.append(net)
        else:
            excluded += 1
    if not selected:
        raise ValueError('No routable nets')
    if len({n['id'] for n in selected}) != len(selected):
        raise ValueError('Duplicate net ID')
    return selected, excluded


def convert(source, route, output, limit=0, cost='unit', baseline=None):
    source, route, output = Path(source).resolve(), Path(route).resolve(), Path(output)
    digest = sha256(source)
    route_digest = sha256(route)
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='h3d_rrg_') as temp:
        database = source
        if source.suffix == '.xml':
            database = Path(temp) / 'graph.sqlite'
            xml_database(source, database)
        db = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
        try:
            rows = db.execute('SELECT id,kind,capacity,xlow,ylow,layer_low,xhigh,yhigh,layer_high FROM nodes ORDER BY id').fetchall()
            if not rows:
                raise ValueError('Empty RRG')
            index = {n[0]: i for i, n in enumerate(rows)}
            switches = {i: (kind, delay) for i, kind, delay in db.execute('SELECT id,kind,tdel_seconds FROM switches')}
            def base_cost(dst, sw):
                if cost == 'unit':
                    return 1
                delay = switches[sw][1] or 0
                return 1 + round(delay*1e12)
            if any(kind not in ('mux', 'tristate') for kind, delay in switches.values()):
                raise ValueError('Non-configurable/pass-gate switches need closure semantics; unsupported in this prototype')
            for _, delay in switches.values():
                if delay is not None and (not math.isfinite(delay) or delay < 0):
                    raise ValueError('Invalid switch delay')
            nets, excluded = terminals(route)
            all_count = len(nets)
            if limit:
                nets = nets[:limit]
            for net in nets:
                if net['source'] not in index or rows[index[net['source']]][1] != 'SOURCE':
                    raise ValueError('SOURCE missing/mismatched with RRG')
                for sink in net['sinks']:
                    if sink not in index or rows[index[sink]][1] != 'SINK':
                        raise ValueError('SINK missing/mismatched with RRG')
            edge_count = db.execute('SELECT count(*) FROM edges').fetchone()[0]
            vertical_count = 0
            with (output / 'graph.rrg').open('w') as out:
                out.write(f'H3DRRG 1 {len(rows)} {edge_count}\n')
                for n in rows:
                    if n[1] not in KINDS or n[2] < 0 or n[5] < 0 or n[8] < n[5]:
                        raise ValueError(f'Invalid node {n[0]}')
                    out.write(' '.join(map(str, (n[0], KINDS[n[1]], *n[2:]))) + '\n')
                for eid, src, dst, sw in db.execute('SELECT id,src,dst,switch_id FROM edges ORDER BY id'):
                    a, b = rows[index[src]], rows[index[dst]]
                    kind, delay = switches[sw]
                    vertical = int(b[1] == 'CHANZ' or (a[1] != 'CHANZ' and a[5] != b[5]))
                    vertical_count += vertical
                    base = base_cost(dst, sw)
                    if base >= 0x3fffffff:
                        raise ValueError('Cost exceeds integer representation')
                    out.write(f'{eid} {index[src]} {index[dst]} {sw} {base} {vertical}\n')
            with (output / 'nets.txt').open('w') as out:
                out.write(f'H3DNETS 1 {len(nets)}\n')
                for n in nets:
                    out.write(' '.join(map(str, (n['id'], index[n['source']], len(n['sinks']), *(index[s] for s in n['sinks'])))) + '\n')
            with (output / 'candidates.txt').open('w') as out:
                # Reproducible hardware replay inputs from real directed edges,
                # plus synthetic congestion snapshots; not captured VPR state.
                for eid, src, dst, sw in db.execute('SELECT id,src,dst,switch_id FROM edges ORDER BY id LIMIT 4096'):
                    a, b = rows[index[src]], rows[index[dst]]
                    vertical = int(b[1] == 'CHANZ' or (a[1] != 'CHANZ' and a[5] != b[5]))
                    base = base_cost(dst, sw)
                    out.write(f'{base} {eid%5} {eid%4} {b[2]} 16 7 {vertical}\n')
            manifest = {
                'schema_version': 1, 'execution_kind': 'rrg_projection',
                'source': {'path': str(source), 'sha256': digest},
                'endpoint_route': {'path': str(route), 'sha256': route_digest},
                'nodes': len(rows), 'edges': edge_count, 'nodes_by_type': dict(Counter(r[1] for r in rows)),
                'vertical_entry_edges': vertical_count, 'nets': len(nets), 'available_nets': all_count,
                'excluded_global_empty_nets': excluded, 'subset': len(nets) != all_count,
                'cross_layer_nets': sum(any(rows[index[s]][5] != rows[index[n['source']]][5] for s in n['sinks']) for n in nets),
                'cost_model': cost, 'missing_switch_delay_ids': [i for i, (_, d) in switches.items() if d is None],
                'scope': 'Directed RRG connectivity and per-net node capacity; excludes local OPIN reservation, pin mapping, RC STA and physical bus-mux groups.',
                'hardware_vectors': 'real edge attributes with synthetic congestion states',
                'files': {name: sha256(output/name) for name in ('graph.rrg', 'nets.txt', 'candidates.txt')},
            }
            if baseline:
                bp = Path(baseline).resolve()
                bm = json.loads(bp.read_text())
                manifest['reference_vpr'] = {'manifest_path': str(bp), 'manifest_sha256': sha256(bp),
                                             'metrics': bm.get('metrics'), 'comparison': 'context only; objectives and checker scope differ'}
            if sha256(source) != digest or sha256(route) != route_digest:
                raise ValueError('Inputs changed during conversion')
            write_json(output / 'manifest.json', manifest)
            print(json.dumps({k: manifest[k] for k in ('nodes','edges','nets','cross_layer_nets','subset')}))
        finally:
            db.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graph', type=Path, required=True)
    p.add_argument('--route', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--limit-nets', type=int, default=0)
    p.add_argument('--cost', choices=('unit','delay_proxy'), default='unit')
    p.add_argument('--baseline-manifest', type=Path)
    a = p.parse_args()
    if a.limit_nets < 0:
        p.error('limit-nets must be nonnegative')
    convert(a.graph, a.route, a.output, a.limit_nets, a.cost, a.baseline_manifest)


if __name__ == '__main__':
    main()
