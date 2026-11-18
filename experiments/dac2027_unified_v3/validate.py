"""Verify cohort integrity without running VPR."""
from collections import Counter
from pathlib import Path
import csv,hashlib,json,statistics
here=Path(__file__).resolve().parent
from cohort import audit
cases=('gemm','bnn','lstm')
full=('stock','pipeline','alt_cpu','alt_cuda')
controls=('group','flat')
def read(p):return json.loads(p.read_text())
def rows(p):return list(csv.DictReader((audit/p).open()))
from cohort import run
finished = (run/'finished.json').is_file()
if not finished:
    stopped = read(audit/'allocation_stop.json')
    assert stopped['status'] == 'job_stopped'
    assert read(run/'environment.json')['host'] in {i['name'] for i in stopped['instances']}
env=read(run/'environment.json')
records={}
for p in (run/'formal').glob('*/*/*/record.json'):
    r=read(p);k=(r['case'],r['arm'],r['repeat']);assert k not in records
    records[k]=r
    assert (r['host'],r['gpu'])==(env['host'],env['gpu'].split(',')[0])
    assert r['before']['cpus']==r['after']['cpus']==env['cpus']
    assert r['before']['compute']==r['after']['compute']==''
    assert not any(k in r['environment'] for k in ['R61_CAPTURE','R61_VERIFY_CPU','VPR_HYBRID_LOOKAHEAD_REPORT'])
    assert not any('R61_IDENTITY' in l or 'R61_NATIVE_PAIR_VERIFY' in l for l in r['dispatch'])
    assert r['wall_ns']==r['end_ns']-r['begin_ns'] and r['e2_ns']>0
    assert r['matches_archived_map']
    rb=read(p.parent/'readback/record.json')
    assert rb['original_sha']==r['route_sha256']
    if r['native_e2_s']:
        assert len(r['native_e2_s'])==1
    cb=r['command']
    for flag,value in [('--check_route','full'),('--num_workers','8'),('--router_algorithm','parallel'),('--router_lookahead','map')]:
        assert cb[cb.index(flag)+1]==value
    assert '--route' in cb and '--analysis' in cb and not {'--place','--pack','--read_router_lookahead'}&set(cb)
    if r['arm'].startswith('alt_'):assert 'VPR_LA_BACKEND' in r['environment']
status={}
for c in cases:
    gate_path = run/'qualification'/c/'gate.json'
    gate = read(gate_path) if gate_path.exists() else {}
    if finished:
        assert gate, c
    status[c]=dict(qualification=gate,formal=sum(k[0]==c for k in records))
    if gate and all(gate.values()):
        for rep in range(3):
            for family in (full,controls):
                subset=[(a,records[c,a,rep]) for a in family if (c,a,rep) in records]
                order=[a for a,r in sorted(subset,key=lambda x:x[1]['begin_ns'])]
                off=rep%len(family);expected=family[off:]+family[:off]
                assert order==list(expected[:len(order)])
for row in rows('paired.csv'):
    c,a,b=row['case'],row['numerator'],row['denominator']
    m='e2_ns' if row['metric']=='E2' else 'wall_ns'
    ratios=[records[c,a,i][m]/records[c,b,i][m] for i in range(3)]
    assert abs(float(row['mean'])-statistics.mean(ratios))<1e-12 and abs(float(row['sd'])-statistics.stdev(ratios))<1e-12
intervals=sorted((r['begin_ns'],r['end_ns']) for r in records.values())
assert all(b<=c for (_,b),(c,_) in zip(intervals,intervals[1:]))
qor=rows('qor.csv')
attempts = []
for invocation in sorted(run.glob('*/*/*/*/invocation.json')):
    iv = read(invocation)
    record_path = invocation.parent/'record.json'
    route_status = 'interrupted' if not record_path.is_file() else (
        'passed_local_checks' if read(record_path)['local_pass'] else 'failed_local_checks')
    attempts.append({**{k:iv[k] for k in ('phase','case','repeat','arm')}, 'status':route_status})
for row in qor:
    d = run/row['phase']/row['case']/row['repeat']/row['arm']
    rb = d/'readback/record.json'
    if rb.is_file():
        r = read(rb)
        assert r['original_sha']==row['original_route_sha']
        if r['passed']:
            assert r['returncode']==0 and r['metrics']['full_check']
            assert r['metrics']['critical_path_ns']==float(row['CPD_ns'])
            assert r['metrics']['wirelength']==int(row['WL'])
            assert (rb.parent/'report_timing.setup.rpt').stat().st_size > 0
            assert (rb.parent/'report_timing.hold.rpt').stat().st_size > 0
receipt=dict(worker_finished=finished, attempts=attempts, cases=status,formal_records=len(records),full_invocations=sum(r['arm'] in full for r in records.values()),
             controls=sum(r['arm'] in controls for r in records.values()),recorded_routes=len(qor),independently_passed_routes=sum(r['independent_FULL_STA']=='True' for r in qor),
             independent_failures=[(r['case'],r['arm'],r['phase'],r['repeat']) for r in qor if r['independent_FULL_STA']=='False'],
             missing_readbacks=[(r['case'],r['arm'],r['phase'],r['repeat']) for r in qor if not r['independent_FULL_STA']],
             stock_threshold_failures=[(r['case'],r['arm'],r['phase'],r['repeat']) for r in qor if r['stock_gate']!='True'],
             concurrency_overlaps=0,distinct_worker_count=len(set(r['host'] for r in records.values())),
             gold_maps_passed=sum(r['matches_archived_map'] for r in records.values()),
             speedup_rows_recomputed=len(rows('paired.csv')),archive_sha256=hashlib.sha256((audit/'native_process_records.zip').read_bytes()).hexdigest())
(audit/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
