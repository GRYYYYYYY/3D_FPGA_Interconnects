#!/usr/bin/env python3
"""Export projected trees and run the pinned VPR FULL checker and STA.

Requires the native-CHANZ SQLite projection and a frozen G-project case/lock.
Never launches routing or modifies sibling projects. All VPR output is local.
"""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import time
from audit import audit
from prepare import sha256, write_json


def verified(record):
    p=Path(record['path']).resolve()
    if sha256(p)!=record['sha256']:
        raise ValueError(f'Pinned input changed: {p}')
    return p


def resource_rows(db, table, columns, identifiers):
    """Batch indexed, read-only lookups; preserve original edge/switch IDs."""
    identifiers=sorted(identifiers);rows={}
    for offset in range(0,len(identifiers),900):
        chunk=identifiers[offset:offset+900]
        placeholders=','.join('?' for _ in chunk)
        for row in db.execute(f'SELECT id,{columns} FROM {table} WHERE id IN ({placeholders})',chunk):
            rows[row[0]]=row[1:]
    if len(rows)!=len(identifiers):raise ValueError('Missing original '+table+' resource')
    return rows


def export(database, reference, result, output):
    routes={r['net']:r for r in result['routes']}
    lines=Path(reference).read_text().splitlines(keepends=True)
    preamble, sections, current=[],{},None
    for line in lines:
        h=re.match(r'^Net\s+(\d+)\s+\(',line)
        if h:
            current=int(h[1]);sections[current]=[]
        (preamble if current is None else sections[current]).append(line)
    if not routes.keys()<=sections.keys():
        raise ValueError('Unexpected result net IDs')
    db=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True)
    try:
        edges=resource_rows(db,'edges','src,dst,switch_id',{e for r in routes.values() for e in r['edges']})
        nodes=resource_rows(db,'nodes','kind,xlow,ylow,layer_low,xhigh,yhigh,layer_high,ptc',{v for r in routes.values() for v in r['nodes']})
        with Path(output).open('x') as out:
            out.writelines(preamble)
            for ni, reference_lines in sections.items():
                if ni not in routes:
                    # Only non-routed local/global nets may be retained.
                    if any(line.startswith('Node:') for line in reference_lines):
                        raise ValueError('Subset cannot be exported as a full circuit')
                    out.writelines(reference_lines)
                    continue
                r=routes[ni]
                if not r['connected']:
                    raise ValueError('Cannot export an incomplete route')
                pins={}
                for line in reference_lines:
                    m=re.match(r'Node:\s*(\d+)\s+SINK.*Net_pin_index:\s*(\d+)',line)
                    if m:pins[int(m[1])]=int(m[2])
                adjacency=defaultdict(list)
                indegree=set()
                for eid in r['edges']:
                    u,v,sw=edges[eid];adjacency[u].append((v,sw));indegree.add(v)
                roots=set(r['nodes'])-indegree
                if len(roots)!=1:raise ValueError('Expected one root')
                out.write(reference_lines[0]+'\n')
                # Stack of emit and expand events avoids recursive-depth limits.
                stack=[('expand',roots.pop(),-1)]
                while stack:
                    action,u,sw=stack.pop()
                    if action=='expand' and adjacency[u]:
                        for v,switch in reversed(adjacency[u]):
                            stack.append(('expand',v,-1));stack.append(('emit',u,switch))
                        continue
                    row=nodes[u]
                    kind,x,y,z,xh,yh,zh,ptc=row
                    span=f' to ({xh},{yh},{zh})' if (x,y,z)!=(xh,yh,zh) else ''
                    label='Track' if kind.startswith('CHAN') else ('Pin' if kind in ('IPIN','OPIN') else 'Class')
                    pin=f' Net_pin_index: {pins[u]}' if kind=='SINK' else ''
                    if action=='expand' and kind!='SINK':raise ValueError('Non-terminal dangling leaf')
                    out.write(f'Node: {u} {kind} ({x},{y},{z}){span} {label}: {ptc} Switch: {sw}{pin}\n')
                out.write('\n')
    finally:db.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',type=Path,required=True)
    p.add_argument('--result',type=Path,required=True)
    p.add_argument('--vpr-case',type=Path,required=True)
    p.add_argument('--vpr-lock',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--timeout',type=float,default=180)
    a=p.parse_args()
    cm=json.loads((a.case/'manifest.json').read_text())
    frozen=json.loads(a.vpr_case.read_text());lock=json.loads(a.vpr_lock.read_text())
    binary=verified(lock['binary'])
    original={k:verified(v) for k,v in frozen['inputs'].items()}
    reference=verified(frozen['reference']['route'])
    database=verified(cm['source'])
    if database.suffix!='.sqlite':raise ValueError('Native SQLite source is required by this validator')
    if sha256(reference)!=cm['endpoint_route']['sha256']:raise ValueError('Different placement/reference endpoints')
    db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
    summary=json.loads(db.execute("SELECT value FROM metadata WHERE key='summary'").fetchone()[0]);db.close()
    if summary['source']['sha256']!=frozen['inputs']['rr_graph']['sha256']:raise ValueError('RRG does not match native case')
    for name in ('graph.rrg','nets.txt'):
        if sha256(a.case/name)!=cm['files'][name]:raise ValueError('Projection changed')
    projection=audit(a.case/'graph.rrg',a.case/'nets.txt',a.result)
    if not projection['legal_in_projection']:raise ValueError('Projection audit failed')
    a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    files=dict(original)
    for key,name in (('packed_netlist','packed.net'),('placement','fixed.place')):
        files[key]=a.output/name;shutil.copyfile(original[key],files[key])
    exported=a.output/'routed.route'
    export(database,reference,json.loads(a.result.read_text()),exported)
    cmd=[str(binary),str(files['architecture']),str(files['circuit']),
         '--route_chan_width',str(frozen['route_chan_width']),'--device_width',str(frozen['device_width']),
         '--target_utilization',str(frozen['target_utilization']),'--seed',str(frozen['seed']),
         '--num_workers','1','--flat_routing','off','--check_route','full',
         '--net_file',str(files['packed_netlist']),'--place_file',str(files['placement']),
         '--route_file',str(exported),'--read_rr_graph',str(files['rr_graph']),
         '--timing_report_npaths','10','--analysis']
    env=os.environ.copy()
    for key in list(env):
        if key.startswith('VPR_H3D_'):del env[key]
    runtime_root=a.vpr_lock.resolve().parent.parent
    for library in lock['runtime']['libraries']:
        candidate=runtime_root/library['path']
        if sha256(candidate)!=library['sha256']:raise ValueError('Runtime library changed')
    env.update(OMP_NUM_THREADS='1',LC_ALL='C',LD_LIBRARY_PATH=str(runtime_root/lock['runtime']['library_directory']))
    record={'command':cmd,'binary_sha256':sha256(binary),'source_result_sha256':sha256(a.result),
            'exported_route_sha256':sha256(exported),'projection_audit':projection,
            'case_manifest_sha256':sha256(a.vpr_case),'lock_sha256':sha256(a.vpr_lock),
            'status':'running','vpr_full_check':False}
    write_json(a.output/'validation.json',record)
    start=time.perf_counter()
    with (a.output/'vpr.log').open('w') as log:
        try:
            proc=subprocess.run(cmd,cwd=a.output,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout)
            record.update(returncode=proc.returncode,status='completed' if proc.returncode==0 else 'failed')
        except subprocess.TimeoutExpired:
            record['status']='timeout'
    text=(a.output/'vpr.log').read_text(errors='replace')
    record['seconds']=time.perf_counter()-start
    record['vpr_full_check']=record.get('returncode')==0 and 'Completed routing consistency check successfully' in text
    match=re.search(r'Final critical path delay \(least slack\):\s*([\d.eE+-]+)\s*ns',text)
    record['critical_path_ns']=float(match[1]) if match else None
    record['input_files_unchanged']=all(sha256(v)==frozen['inputs'][k]['sha256'] for k,v in original.items())
    write_json(a.output/'validation.json',record)
    print(json.dumps({k:record[k] for k in ('status','vpr_full_check','critical_path_ns','seconds')}))
    return 0 if record['vpr_full_check'] else 2


if __name__=='__main__':raise SystemExit(main())
