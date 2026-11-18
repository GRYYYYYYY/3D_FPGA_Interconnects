"""Generate V3 statistics from immutable per-process records."""
import csv, json, statistics, sys
from pathlib import Path
here=Path(__file__).resolve().parent
from cohort import run
from cohort import audit
def write(name,fields,rows):
    with (audit/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def read(p): return json.loads(p.read_text())
full=['stock','pipeline','alt_cpu','alt_cuda']
arms=full+['group','flat']
cases=['gemm','bnn','lstm']
def construction_valid(r):
    if not r.get('e2_ns') or not (0 < r['e2_ns'] < r['wall_ns']) or not r['matches_archived_map']:
        return False
    if r['local_pass']:
        return True
    # Stock has no alternate dispatch. A serialized golden map and the scope timer
    # establish completed construction independently of a subsequent router failure.
    return r['arm'] == 'stock' and not r['dispatch']

def metric_valid(r, metric):
    return r is not None and (construction_valid(r) if metric == 'E2' else r['local_pass'])

data={};qor=[];raw=[]
for phase in ('qualification','formal'):
    for p in sorted((run/phase).glob('*/*/*/record.json')):
        r=read(p);key=(r['case'],r['arm'],r['repeat']);m=r['metrics']
        rb=p.parent/'readback/record.json';rb=read(rb) if rb.exists() else {}
        ref=p.parents[1]/'stock/record.json'
        if not ref.exists() and phase=='formal': ref=run/'formal'/r['case']/str(r['repeat'])/'stock/record.json'
        reference=read(ref) if ref.exists() else None
        ctrl=reference['metrics'] if reference and reference['local_pass'] else {}
        def change(k):
            return 100*(m[k]/ctrl[k]-1) if m.get(k) and ctrl.get(k) else None
        delta=[change(k) for k in ('critical_path_ns','wirelength')]
        valid=all(x<=5.00000001 for x in delta) if all(x is not None for x in delta) and r['local_pass'] else None
        qor.append(dict(case=r['case'],arm=r['arm'],phase=phase,repeat=r['repeat'],CPD_ns=m['critical_path_ns'],WL=m['wirelength'],
                        CPD_delta_pct=delta[0],WL_delta_pct=delta[1],stock_gate=valid,overuse=r['overuse'],original_FULL=m['full_check'],
                        independent_FULL_STA=rb.get('passed'),original_route_sha=r['route_sha256'],map_sha=r['map_sha256'],
                        capture_sha=r['capture_sha256'],matches_golden=r['matches_archived_map']))
        if phase!='formal': continue
        assert key not in data
        data[key]=r
        raw.append(dict(case=r['case'],arm=r['arm'],repeat=r['repeat'],E2_ns=r['e2_ns'],
                        Process_ns=r['wall_ns'] if r['arm'] in full and r['local_pass'] else None,
                        elapsed_to_exit_ns=r['wall_ns'],returncode=r['returncode'],E2_valid=construction_valid(r),host=r['host'],gpu=r['gpu'],
                        begin_ns=r['begin_ns'],end_ns=r['end_ns'],local_pass=r['local_pass'],stock_gate=valid,
                        native_timer_s=','.join(r['native_e2_s']),internal_e2_s=','.join(r['internal_e2_s'])))
write('raw_timing.csv','case arm repeat E2_ns Process_ns elapsed_to_exit_ns returncode E2_valid host gpu begin_ns end_ns local_pass stock_gate native_timer_s internal_e2_s'.split(),raw)
write('qor.csv','case arm phase repeat CPD_ns WL CPD_delta_pct WL_delta_pct stock_gate overuse original_FULL independent_FULL_STA original_route_sha map_sha capture_sha matches_golden'.split(),qor)
intervals=sorted((r['begin_ns'],r['end_ns']) for r in data.values())
assert all(b<=c for (_,b),(c,_) in zip(intervals,intervals[1:]))
assert len(set((r['host'],r['gpu']) for r in data.values()))<=1
summ=[];pairs=[];coverage=[]
for case in cases:
    for arm in arms:
        rr=[data.get((case,arm,i)) for i in range(3)]
        coverage.append(dict(case=case,arm=arm,planned=3,invoked=sum((run/'formal'/case/str(i)/arm/'invocation.json').exists() for i in range(3)),recorded=sum(r is not None for r in rr),passed=sum(bool(r and r['local_pass']) for r in rr)))
        for metric,key in [('E2','e2_ns'),('Process','wall_ns')]:
            if metric=='Process' and arm not in full:continue
            if not all(metric_valid(r,metric) for r in rr): continue
            times=[r[key]*1e-9 for r in rr]
            summ.append(dict(case=case,arm=arm,metric=metric,n=3,r0=times[0],r1=times[1],r2=times[2],mean=statistics.mean(times),sd=statistics.stdev(times)))
    for a,b in [('stock','pipeline'),('stock','alt_cuda'),('pipeline','alt_cuda'),('alt_cpu','alt_cuda'),('pipeline','alt_cpu'),('group','flat'),('group','pipeline'),('flat','pipeline')]:
        for metric,key in [('E2','e2_ns'),('Process','wall_ns')]:
            if metric=='Process' and (a not in full or b not in full): continue
            rr=[(data.get((case,a,i)),data.get((case,b,i))) for i in range(3)]
            if not all(metric_valid(x,metric) and metric_valid(y,metric) for x,y in rr): continue
            ratios=[x[key]/y[key] for x,y in rr]
            pairs.append(dict(case=case,numerator=a,denominator=b,metric=metric,n=3,r0=ratios[0],r1=ratios[1],r2=ratios[2],mean=statistics.mean(ratios),sd=statistics.stdev(ratios)))
write('coverage.csv','case arm planned invoked recorded passed'.split(),coverage)
write('seconds.csv','case arm metric n r0 r1 r2 mean sd'.split(),summ)
write('paired.csv','case numerator denominator metric n r0 r1 r2 mean sd'.split(),pairs)
print(len(raw),'formal records;',len(qor),'route records')
