"""Reduce only qualified complete cases from this worker. Preserve each paired ratio."""
import csv
import json
from pathlib import Path
from statistics import mean, stdev
from math import isfinite

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT/'results/native_alt_cpu_ablation_20261118/worker_a'
OUT = HERE/'results'
OUT.mkdir(exist_ok=True)
plan = json.loads((HERE/'plan.json').read_text())
golden = json.loads((HERE/'golden.json').read_text())
budget = json.loads((HERE/'p1_budget.json').read_text())
states = json.loads((RUN/'states.json').read_text())
rows = json.loads((RUN/'rows.json').read_text())
environment = json.loads((RUN/'environment.json').read_text()) if (RUN/'environment.json').exists() else {}
stats = {}
quality = []
for case,state in states.items():
    cohort = [r for r in rows if r['case']==case]
    formal = [r for r in cohort if r['formal']]
    for r in cohort:
        quality.append(dict(case=case,cohort=r['cohort_id'],arm=r['arm'],phase='formal' if r['formal'] else 'qualification',
                            repeat=r['label'],E2_s=r.get('E2_s'),Process_s=r['Process_wall_s'],
                            readback_s=r.get('independent',{}).get('Process_wall_s'),qualified=r['qualified'],
                            map_sha256=r.get('map_sha256'),route_sha256=r.get('route_sha256'),
                            iterations=r['metrics'].get('iterations'),CPD_ns=r['metrics'].get('critical_path_ns'),
                            wirelength=r['metrics'].get('wirelength'),overuse_zero=r['zero_overuse'],
                            independent_FULL_STA=r.get('readback_identity') and r.get('independent',{}).get('metrics',{}).get('full_check'),
                            paired_qor_passed=r.get('paired_qor_passed'),CPD_delta_pct=r.get('quality_delta_pct',{}).get('critical_path_ns'),
                            WL_delta_pct=r.get('quality_delta_pct',{}).get('wirelength')))
    if state!='COMPLETE':
        continue
    assert environment['MPOL_BIND'] and len(set(environment['affinity']))==8
    assert environment['admitted_at'] < budget['admission_deadline']['epoch']
    assert len(cohort)==12 and len(formal)==9
    quals = {r['arm']:r for r in cohort if not r['formal']}
    assert set(quals)==set(plan['arms'])
    for r in cohort:
        assert r['cohort_id']==environment['cohort'] and r['gpu_uuid']==environment['gpu_uuid']
        assert r['affinity']==environment['affinity'] and r['qualified']
        assert r['dispatch_verified'] and r['readback_identity'] and r['zero_overuse']
        assert r['returncode']==r['independent']['returncode']==0
        assert r['independent']['metrics']['full_check'] and r['metrics']['full_check']
        assert r['map_sha256']==golden[case][r['arm']]['map_sha256']
        assert r['finish_epoch']<=budget['end']['epoch']
        assert all(r['metrics'][k]==r['independent']['metrics'][k] for k in ('critical_path_ns','wirelength'))
    for arm in ['alt_cpu','alt_cuda']:
        assert quals[arm]['native_capture']['sha256']==golden[case][arm]['capture_sha256']
    lookup={}
    for repeat,order in enumerate(plan['rotations']):
        group=[r for r in formal if r['repeat']==repeat]
        assert [r['arm'] for r in group]==order
        control=next(r for r in group if r['arm']=='pipeline')
        for r in group:
            assert r['paired_qor_passed'] and r['qualification_map_equal']
            assert all(r['metrics'][k]<=1.05*control['metrics'][k] for k in ('critical_path_ns','wirelength'))
            assert all(isfinite(r[k]) and r[k]>0 for k in ('E2_s','Process_wall_s'))
            assert not any(k in r['environment'] for k in ('R61_CAPTURE','R61_VERIFY_CPU'))
            lookup[repeat,r['arm']]=r
    stats[case]={}
    for field in ['E2_s','Process_wall_s']:
        scope={}
        for arm in plan['arms']:
            values=[lookup[i,arm][field] for i in range(3)]
            scope[arm]=dict(values=values,mean=mean(values),sd=stdev(values))
        for a,b in [('pipeline','alt_cpu'),('alt_cpu','alt_cuda'),('pipeline','alt_cuda')]:
            values=[lookup[i,a][field]/lookup[i,b][field] for i in range(3)]
            scope[a+'/'+b]=dict(values=values,mean=mean(values),sd=stdev(values))
        stats[case][field]=scope

(OUT/'paired_statistics.json').write_text(json.dumps(dict(states=states,statistics=stats),indent=2)+'\n')
if quality:
    with (OUT/'raw_seconds_and_qor.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(quality[0]),lineterminator='\n')
        writer.writeheader()
        writer.writerows(quality)
print('Complete cases:',list(stats),'captured processes:',len(rows))

