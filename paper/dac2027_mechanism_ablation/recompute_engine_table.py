"""Render the independent engine/backend table from eligible new paired rows."""
from pathlib import Path
import csv
import json
from statistics import mean, stdev

paper = Path(__file__).resolve().parent
evidence = paper / 'evidence/native_engine'
summary = json.loads((evidence/'paired_statistics.json').read_text())
rows = list(csv.DictReader((evidence/'raw_seconds_and_qor.csv').open()))
lines = []
for case in ('gemm', 'bnn'):
    if case not in summary['statistics']:
        continue
    assert summary['states'][case]=='COMPLETE'
    group = [r for r in rows if r['case']==case and r['phase']=='formal']
    assert len(group)==9 and len({r['cohort'] for r in group})==1
    assert all(r['qualified']==r['paired_qor_passed']==r['independent_FULL_STA']=='True' for r in group)
    keyed = {(int(r['repeat']),r['arm']):r for r in group}
    for column,field,label in [('E2_s','E2_s','E2'),('Process_s','Process_wall_s','Process')]:
        values = []
        for a,b in [('pipeline','alt_cpu'),('alt_cpu','alt_cuda'),('pipeline','alt_cuda')]:
            ratios = [float(keyed[i,a][column])/float(keyed[i,b][column]) for i in range(3)]
            known = summary['statistics'][case][field][a+'/'+b]
            assert ratios==known['values'] and mean(ratios)==known['mean'] and stdev(ratios)==known['sd']
            values.append(f'${mean(ratios):.3f}\\pm{stdev(ratios):.3f}$')
        lines.append(' & '.join([case.upper()+' '+label]+values)+r' \\')
assert lines
(paper/'tables/engine_ratios.tex').write_text('\n'.join(lines)+'\n')

