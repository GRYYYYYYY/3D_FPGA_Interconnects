"""Correct XML inventory metadata after the original prep owner exits; no solver retries."""
from collections import Counter
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import run_native_cpu_large as chain
from prepare import write_json
from scaling_common import verified

OUT, ROOT = chain.OUT, chain.ROOT


def count_graph(path):
    # Attribute order is irrelevant. Count VPR's one-per-line node/edge start tags.
    nodes = edges = 0
    with path.open('rb') as stream:
        for line in stream:
            line = line.lstrip()
            nodes += line.startswith(b'<node ')
            edges += line.startswith(b'<edge ')
    assert nodes > 0 and edges > 0, (nodes, edges)
    return nodes, edges


def geometry(directory):
    text = (directory/'fixed.place').read_text()
    coords, layers = [], Counter()
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 6 and fields[-1].startswith('#') and not line.startswith('#'):
            xyz = tuple(map(int, fields[1:5])); coords.append((fields[0], *xyz)); layers[xyz[-1]] += 1
    assert coords and set(layers) == {0,1}, dict(layers)
    nodes, edges = count_graph(directory/'rr_graph.xml')
    return dict(placed_blocks=len(coords), placement_layers=dict(layers),
                coordinate_sha256=hashlib.sha256(json.dumps(sorted(coords)).encode()).hexdigest(),
                grid=re.findall(r'Array size: (.+)',text), rr_nodes=nodes, rr_edges=edges,
                rr_bytes=(directory/'rr_graph.xml').stat().st_size)


def repair():
    original = chain.read(OUT/'preparation.json')
    protocol = chain.read(OUT/'protocol.json')
    spec = chain.read(chain.SPEC)
    assert len(original['runs']) == 6
    corrected = copy.deepcopy(original)
    corrected.update(status='running', correction='Only XML tag counting/derived metadata; original solver runs retained, no re-execution.',
                     source_receipt=chain.binding(OUT/'preparation.json'))
    destination = OUT/'prepared_verified'; destination.mkdir()
    for row, job in zip(corrected['runs'],protocol['preparation_jobs']):
        assert row['case'] == job['case'] and row['returncode'] == 0 and row['cpu_budget_audit']['verified']
        assert row.get('validation_error') == 'AssertionError()', 'Unexpected prep failure: requires review'
        directory = Path(row['directory'])
        text = (directory/'process.log').read_text(errors='replace')
        assert 'Completed placement consistency check successfully' in text
        row['original_validation_error'] = row.pop('validation_error')
        row['geometry'] = geometry(directory)
        names = {'architecture':Path(spec['architecture']['path']), 'circuit':Path(job['circuit']['path']),
                 'packed_netlist':directory/'packed.net', 'placement':directory/'fixed.place', 'rr_graph':directory/'rr_graph.xml'}
        case = dict(id=job['case'],circuit_id=job['circuit']['name'],placement_seed=job['seed'],seed=job['seed'],
                    route_chan_width=100,device_width=0,target_utilization=.6,inputs={k:chain.binding(v) for k,v in names.items()},
                    geometry=row['geometry'],scope='Original fresh pack/place artifacts; corrected XML inventory metadata only. No solver rerun or topology edit.')
        d=destination/job['case'];d.mkdir()
        write_json(d/'vpr_case.json',case)
        row.update(inputs_ready=True,case_binding=chain.binding(d/'vpr_case.json'))
        write_json(OUT/'preparation_verified.json',corrected)
    assert all(a['geometry']['coordinate_sha256'] != b['geometry']['coordinate_sha256']
               for a,b in zip(corrected['runs'][::2],corrected['runs'][1::2]))
    corrected.update(status='completed',different_layouts=True,finished_utc=chain.now())
    write_json(OUT/'preparation_verified.json',corrected)
    for stage in ['qualification','formal']:
        p=chain.read(OUT/f'{stage}_plan.json')
        p['derived_from']=chain.binding(OUT/f'{stage}_plan.json')
        p['metadata_correction']=chain.binding(OUT/'preparation_verified.json')
        p['runner_bindings'][Path(__file__).name]=chain.binding(Path(__file__))
        for c in p['lanes']['serial']['cases']:
            c['vpr_case']=str(destination/c['id']/'vpr_case.json')
        write_json(OUT/f'{stage}_verified_plan.json',p)


def main():
    with (OUT/'continuation.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUT/'continuation.json').exists():raise RuntimeError('Existing continuation; observe it, do not restart')
        state=dict(status='waiting_original_preparation',pid=os.getpid(),started_utc=chain.now(),current='wait_preparation',steps=[],
                   original_owner=chain.read(OUT/'supervisor.json')['pid'],
                   policy='Wait for original preparation owner, correct only known XML attribute-order inventory bug; no solver resubmission.',default_changed=False)
        write_json(OUT/'continuation.json',state)
        try:
            while True:
                try: original=chain.read(OUT/'supervisor.json')
                except json.JSONDecodeError: time.sleep(5);continue
                if original['status'] != 'running':break
                time.sleep(15)
            assert original['status']=='stopped_for_review' and original.get('error')=="RuntimeError('Preparation/geometry gate failed; formal matrix not admitted')", original
            # The previous owner releases this lock after writing its terminal receipt.
            with (OUT/'owner.lock').open('a+') as owner:
                fcntl.flock(owner,fcntl.LOCK_EX)
                for e in chain.read(OUT/'protocol.json')['runner_bindings'].values():verified(e)
                state.update(status='running',current='correct_inventory');write_json(OUT/'continuation.json',state)
                repair()
                os.sched_setaffinity(0,list(range(32,40)))

                def child(name,cmd):
                    step=dict(name=name,command=cmd,status='running');state['steps'].append(step);state['current']=name
                    with (OUT/f'{name}_continuation.log').open('x') as stream:
                        p=subprocess.Popen(cmd,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                        step['pid']=p.pid;write_json(OUT/'continuation.json',state);rc=p.wait()
                    step.update(returncode=rc,status='completed' if rc==0 else 'failed',finished_utc=chain.now())
                    write_json(OUT/'continuation.json',state)
                    if rc:raise RuntimeError(name+' failed; requires review')

                for stage in ['qualification','formal']:
                    (OUT/stage).mkdir()
                    plan=OUT/f'{stage}_verified_plan.json'
                    child(stage,[sys.executable,str(chain.WRAPPER),'--plan',str(plan),'--lane','serial'])
                    child(stage+'_audit',[sys.executable,str(ROOT/'scripts/verify_native_cpu_study.py'),'--plan',str(plan),'--output',str(OUT/f'{stage}_audit.json')])
                    if stage=='qualification' and not chain.gate():
                        state.update(status='complete_qualification_rejected',current=None,formal_started=False)
                        break
                else:
                    state.update(status='measurements_and_audit_complete',current=None,formal_started=True)
        except Exception as exc:
            state.update(status='stopped_for_review',error=repr(exc));raise
        finally:
            state['finished_utc']=chain.now();write_json(OUT/'continuation.json',state)


if __name__=='__main__':main()
