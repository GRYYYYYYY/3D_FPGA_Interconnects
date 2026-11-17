"""Rebuild the historical batch timings and fixed-remainder estimates."""
import csv
import json
from pathlib import Path
from statistics import mean, median

paper = Path(__file__).resolve().parent
archive = json.loads((paper / 'evidence/r6_bnn40.json').read_text())
times = {}
for config in archive['matched_summary']:
    shift, backend = config['shift'], config['kind']
    rows = sorted((r for r in archive['formal_measurements']
                   if (r['shift'], r['kind']) == (shift, backend)), key=lambda r: r['process'])
    assert [r['process'] for r in rows] == [0, 1, 2]
    medians = []
    for process in rows:
        batches = process['measurements']
        assert [b['repeat'] for b in batches] == [0, 1, 2, 3]
        assert all(b['status'] == 0 and b.get('deterministic', b.get('cpp_match')) for b in batches)
        medians.append(median(b['E1_s'] for b in batches[1:]))
    assert sorted(medians) == sorted(config['process_medians_s']) and median(medians) == config['median_s']
    times[backend, shift] = median(medians)

profiles = json.loads((paper / 'evidence/wave_statistics.json').read_text())['profiles']
for summary, profile in zip(archive['profiles'], profiles):
    assert [summary[k] for k in ('J','wave_count','max_qid_waves','eligible_edges')] == [
        profile[k] for k in ('samples','waves','max_qid_waves','eligible_edges')]
    assert abs(summary['frontier_work_weighted_mean'] - profile['weighted_frontier']) < 1e-6
table = []
for backend, label in [('cpu', 'ALT CPU, 8 cores (s)'), ('cuda', 'ALT CUDA (s)')]:
    table.append(f"{label} & {times[backend,0]:.3f} & {times[backend,20]:.3f}" + r" \\")
(paper/'tables/batch_seconds.tex').write_text('\n'.join(table)+'\n')
rows = list(csv.DictReader((paper/'evidence/matched_native/raw_seconds.csv').open()))
macros = []
estimates = {}
for case in ['gemm','bnn']:
    arms = {}
    for arm in ['pipeline','alt_cuda']:
        group = sorted([r for r in rows if r['case']==case and r['arm']==arm and r['formal']=='True'], key=lambda r:int(r['repeat']))
        assert len(group)==3 and all(r['qualified']=='True' for r in group)
        arms[arm] = group
    cpu, cuda = arms.values()
    assert [r['repeat'] for r in cpu] == [r['repeat'] for r in cuda]
    process = mean(float(r['Process_s']) for r in cpu)
    build = mean(float(r['E2_s']) for r in cpu)
    replacement = mean(float(r['E2_s']) for r in cuda)
    estimates[case] = dict(share=build/process, zero=process/(process-build),
                           replaced=process/(process-build+replacement),
                           measured=mean(float(a['Process_s'])/float(b['Process_s']) for a,b in zip(cpu,cuda)))
    for key,value in estimates[case].items():
        display = f'{100*value:.2f}\\%' if key=='share' else f'{value:.3f}\\times'
        macros.append(r'\newcommand{\Estimate'+case.title()+key.title()+'}{$'+display+'$}')
for backend in ('cpu','cuda'):
    speed = times[backend,0]/times[backend,20]
    macros.append(r'\newcommand{\Batch'+backend.title()+'Gain}{$'+f'{speed:.3f}'+r'\times$}')
(paper/'tables/mechanism_macros.tex').write_text('\n'.join(macros)+'\n')
print('BNN40 process medians and profiles agree with R6; fixed-remainder estimates:', estimates)

