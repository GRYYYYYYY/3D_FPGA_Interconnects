"""Append tables from a fully archived P1 run once."""
from pathlib import Path
import csv
import json

here=Path(__file__).resolve().parent
root=here.parents[2]
out=here/'results'
report=root/'docs/dac2027_mechanism_ablation_20261118.md'
result=json.loads((out/'paired_statistics.json').read_text())
raw=list(csv.DictReader((out/'raw_seconds_and_qor.csv').open()))
env=json.loads((out/'worker_records/environment.json').read_text())
lines=['## Completed allocation','',
       f"The allocation used {env['gpu_model']}, eight physical cores {env['affinity']} on NUMA {env['numa_node']}, with MPOL_BIND. Its GPU identity is {env['gpu_uuid']}.",
       '', 'Case | State | Qualification processes | Formal processes | Successful independent readbacks',
       '---|---|---:|---:|---:']
for case,state in result['states'].items():
    rows=[r for r in raw if r['case']==case]
    lines.append(f"{case.upper()} | {state} | {sum(r['phase']=='qualification' for r in rows)} | {sum(r['phase']=='formal' for r in rows)} | {sum(r['independent_FULL_STA']=='True' for r in rows)}")
lines+=['','Fresh formal processes run sequentially. The performance denominator and QoR control come from this allocation. The original Stock table stays on its original cohort.','',
        'Case / scope | Pipeline seconds | ALT CPU seconds | ALT CUDA seconds | Pipeline / ALT CPU | ALT CPU / ALT CUDA | Pipeline / ALT CUDA',
        '---|---:|---:|---:|---:|---:|---:']
for case,stats in result['statistics'].items():
    for field,label in [('E2_s','E2'),('Process_wall_s','Process')]:
        cells=[]
        for key in ('pipeline','alt_cpu','alt_cuda','pipeline/alt_cpu','alt_cpu/alt_cuda','pipeline/alt_cuda'):
            d=stats[field][key]
            cells.append(f"{d['mean']:.3f} ± {d['sd']:.3f}")
        lines.append(' | '.join([case.upper()+' / '+label]+cells))
lines+=['','Each entry gives mean and sample SD over three fresh processes or three direct within-repeat ratios. Raw measurements for every repeat follow.','',
        'Case | Repeat | Arm | E2 s | Process s | Independent readback s | CPD ns | Wirelength | Iterations | CPD vs Pipeline % | WL vs Pipeline %',
        '---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:']
for r in raw:
    if r['phase']=='formal':
        vals=[r['case'],str(int(r['repeat'])+1),r['arm']]
        for k in ('E2_s','Process_s','readback_s','CPD_ns','wirelength','iterations','CPD_delta_pct','WL_delta_pct'):
            x=r[k]
            vals.append(f"{float(x):.4f}" if x and k not in ('wirelength','iterations') else x)
        lines.append(' | '.join(vals))
lines+=['','The raw CSV also includes the qualification processes, map/route digests and per-run pass flags. Each accepted ALT map and capture matched its predeclared identity. The archive index binds original small records, review copies and large worker artifacts. The complete unmodified raw files remain on shared storage.']
s=report.read_text()
if '## Completed allocation' in s:
    s=s[:s.index('## Completed allocation')].rstrip()+'\n'
report.write_text(s+'\n'+'\n'.join(lines)+'\n')

