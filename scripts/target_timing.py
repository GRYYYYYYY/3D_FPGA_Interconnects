"""Delay sidecars and per-connection priorities derived from native VPR STA.

The additive delay model is explicitly limited to RRGs with zero node and
switch resistance (the frozen Hecate cases). Priorities use -slack/CPD,
clipped to [0,.99], and are not a claim of bit-identical VPR criticalities.
"""
import argparse
import csv
import json
import math
import re
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET

from prepare import sha256, terminals, write_json
from scaling_common import metrics


def physical_slots(rr_graph):
    """Resolve SINK class PTC to physical subtiles, including co-located IOs."""
    classes={};grid={}
    for event,el in ET.iterparse(rr_graph,events=('start','end')):
        if event=='start' and el.tag=='rr_nodes':break
        if event!='end':continue
        if el.tag=='block_type':
            slots=[]
            for pc in el.findall('pin_class'):
                group=set()
                for pin in pc.findall('pin'):
                    prefix=(pin.text or '').split('.',1)[0]
                    match=re.fullmatch(r'[^\[\]]+\[(\d+)\]',prefix)
                    if match:group.add(int(match[1]))
                    elif prefix==el.get('name'):group.add(0)
                    else:raise ValueError('Unrecognized physical pin/subtile name: '+str(pin.text))
                slots.append(group)
            classes[int(el.get('id'))]=slots;el.clear()
        elif el.tag=='grid_loc':
            grid[(int(el.get('x')),int(el.get('y')),int(el.get('layer','0')))]=int(el.get('block_type_id'));el.clear()
    return classes,grid


def prepare_case(item, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    projection=Path(item['projection']['unit'])
    manifest=json.loads((projection/'manifest.json').read_text())
    database=Path(manifest['source']['path'])
    if sha256(database)!=manifest['source']['sha256']:raise ValueError('RRG database changed')
    case=json.loads(Path(item['vpr_case']).read_text())
    classes,grid=physical_slots(case['inputs']['rr_graph']['path'])
    for record in [*case['inputs'].values(),case['reference']['route']]:
        if sha256(record['path'])!=record['sha256']:raise ValueError('Frozen input changed')
    db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
    try:
        if db.execute('SELECT count(*) FROM nodes WHERE coalesce(r_ohm,0)!=0 OR coalesce(c_farad,0)!=0').fetchone()[0]:
            raise ValueError('Nonzero node RC requires a full RC timing model; additive sidecar refused')
        switches={}
        for sid,kind,tdel,resistance in db.execute('SELECT id,kind,tdel_seconds,r_ohm FROM switches'):
            if kind not in ('mux','tristate') or (resistance or 0)!=0:raise ValueError('Unsupported switch resistance/type')
            delay=tdel or 0
            if not math.isfinite(delay) or delay<0:raise ValueError('Invalid switch delay')
            switches[sid]=round(delay*1e12)
        path=output/'delays.txt'
        with path.open('w') as f:
            f.write(f"H3DDELAYS 1 {manifest['edges']}\n")
            for eid,switch in db.execute('SELECT id,switch_id FROM edges ORDER BY id'):
                f.write(f'{eid} {switches[switch]}\n')
        sink_coords={i:((x,y,z),int(ptc)) for i,x,y,z,ptc in db.execute("SELECT id,xlow,ylow,layer_low,ptc FROM nodes WHERE kind='SINK'")}
    finally:db.close()
    placement={}
    for line in Path(case['inputs']['placement']['path']).read_text().splitlines():
        fields=line.split()
        if len(fields)>=6 and fields[-1].startswith('#') and not line.startswith('#'):
            placement[fields[0]]=tuple(int(fields[i]) for i in (1,2,4,3))
    root=ET.parse(case['inputs']['packed_netlist']['path']).getroot()
    atoms={};input_clusters={}
    for cluster in root.findall('block'):
        name=cluster.get('name')
        if name=='open':continue
        if name not in placement:raise ValueError('Cluster missing from placement')
        for block in cluster.iter('block'):
            if not block.findall('block') and block.get('name')!='open':
                atom=block.get('name')
                if atom in atoms and atoms[atom]!=name:raise ValueError('Ambiguous atom cluster')
                atoms[atom]=name
        for group in ('inputs','clocks'):
            for port in cluster.findall(f'{group}/port'):
                for net in (port.text or '').split():
                    if net!='open':input_clusters.setdefault((net,placement[name]),set()).add(name)
    nets,_=terminals(case['reference']['route']['path']);connections=[]
    for net in nets:
        for sink in net['sinks']:
            coords,ptc=sink_coords[sink];matches=set()
            for slot in classes[grid[coords]][ptc]:matches.update(input_clusters.get((net['name'],(*coords,slot)),set()))
            if len(matches)!=1:raise ValueError(f"Ambiguous/missing packed sink: {net['name']} / {sink}: {matches}")
            connections.append({'net':net['id'],'name':net['name'],'sink':sink,'cluster':next(iter(matches))})
    write_json(output/'connections.json',{'atoms':atoms,'connections':connections})
    record={'id':item['id'],'category':item['category'],'projection':str(projection),'vpr_case':item['vpr_case'],
            'prepared':item['prepared'],'delays':str(path.resolve()),'delays_sha256':sha256(path),
            'connections':str((output/'connections.json').resolve()),'connections_sha256':sha256(output/'connections.json'),
            'scope':'Zero-RC buffered RRG; rounded switch delay in ps. Full STA remains native VPR.',
            'source':manifest['source'],'endpoint_route':manifest['endpoint_route']}
    write_json(output/'manifest.json',record);return record


def criticalities(connection_file, net_report, timing_log, output):
    mapping=json.loads(Path(connection_file).read_text());atoms=mapping['atoms']
    native=metrics(Path(timing_log).read_text(errors='replace'))
    if not native['full_check'] or not native['critical_path_ns']:raise ValueError('A complete FULL/STA result is required')
    cpd=native['critical_path_ns']*1e-9
    wanted={(c['name'],c['cluster']) for c in mapping['connections']};names=wanted_names(mapping);values={}
    def cluster_for(pin):
        name=pin
        while '.' in name:
            name=name.rsplit('.',1)[0]
            if name in atoms:return atoms[name]
        raise ValueError(f'Unmapped STA atom pin: {pin}')
    csv.field_size_limit(1024*1024*1024)
    with Path(net_report).open() as f:
        for row in csv.DictReader(f):
            name=row['netname']
            # Internal nets have no route connection in this projection.
            if name not in names:continue
            for sink in row['sinks'].split(';'):
                if not sink:continue
                pin,slack,_=sink.rsplit(',',2);key=(name,cluster_for(pin))
                if key not in wanted:continue
                slack=float(slack)
                if math.isnan(slack):raise ValueError('NaN STA slack')
                # +inf is an unconstrained sink. It gets zero priority.
                value=0 if slack==math.inf else min(990,max(0,round(-slack/cpd*1000)))
                values[key]=max(value,values.get(key,0))
    missing=wanted-values.keys()
    if missing:raise ValueError(f'Criticality coverage incomplete: {list(missing)[:5]} ({len(missing)} total)')
    output=Path(output)
    with output.open('w') as f:
        f.write(f"H3DCRITICALITY 1 {len(mapping['connections'])}\n")
        for c in mapping['connections']:f.write(f"{c['net']} {c['sink']} {values[c['name'],c['cluster']]}\n")
    record={'scope':'Per-cluster-connection max of native atom-pin -slack/CPD, clipped to [0,.99]; refreshed between legal routing epochs.',
            'critical_path_ns':native['critical_path_ns'],'connections':len(mapping['connections']),
            'sources':{str(Path(p).resolve()):sha256(p) for p in (connection_file,net_report,timing_log)},
            'file_sha256':sha256(output),'minimum':min(values.values()),'maximum':max(values.values())}
    write_json(output.with_suffix('.json'),record);return record


def wanted_names(mapping):return {c['name'] for c in mapping['connections']}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--suite',type=Path,required=True);prep.add_argument('--output',type=Path,required=True);prep.add_argument('--cases',nargs='+')
    crit=sub.add_parser('criticality');crit.add_argument('--connections',required=True);crit.add_argument('--report',required=True);crit.add_argument('--log',required=True);crit.add_argument('--output',required=True)
    a=p.parse_args()
    if a.action=='criticality':print(json.dumps(criticalities(a.connections,a.report,a.log,a.output)));return
    suite=json.loads(a.suite.read_text());a.output.mkdir(parents=True,exist_ok=False)
    out={'status':'preparing','source_suite':{'path':str(a.suite.resolve()),'sha256':sha256(a.suite)},'cases':[]}
    write_json(a.output/'suite.json',out)
    for item in suite['cases']:
        if a.cases and item['id'] not in a.cases:continue
        out['cases'].append(prepare_case(item,a.output/item['id']));write_json(a.output/'suite.json',out)
        print(item['id'],'prepared',flush=True)
    out['status']='prepared';write_json(a.output/'suite.json',out)


if __name__=='__main__':main()
