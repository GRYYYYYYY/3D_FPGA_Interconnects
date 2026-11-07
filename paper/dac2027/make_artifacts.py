#!/usr/bin/env python3
"""Freeze completed evidence and reproduce the paper's tables and vector figures.

Run with ../../.venv-report/bin/python make_artifacts.py from this directory.
No solver is launched. Existing snapshots are verified, never silently refreshed.
"""
import hashlib
import json
import math
import re
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from paper_statistics import build_statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EVIDENCE = HERE / 'evidence'
FIGURES = HERE / 'figures'
TABLES = HERE / 'tables'
for p in (EVIDENCE, FIGURES, TABLES):
    p.mkdir(exist_ok=True)

SOURCES = {
    'triad': 'results/native_cpu_evidence_20261102/analysis.json',
    'triad_audit': 'results/native_cpu_evidence_20261102/evidence_verification.json',
    'confirmation': 'results/native_pipeline_confirm_20261102/analysis.json',
    'confirmation_audit': 'results/native_pipeline_confirm_20261102/evidence_verification.json',
    'ablation': 'results/native_cpu_slices_20261101/analysis.json',
    'ablation_audit': 'results/native_cpu_slices_20261101/evidence_verification.json',
    'width120': 'results/native_cpu_width120_20261104/review.json',
    'large_qualification': 'results/native_cpu_large_20261102/analysis.json',
    'accounting': 'results/native_cpu_direction_20261102/analysis.json',
    'interpolation_semantics': 'results/native_lookahead_analysis_20261101/semantics.json',
    'source_reduction_checks': 'results/native_lookahead_analysis_20261101/reduction_checks.json',
    'gemm_input_preparation': 'data/scaling_20261025/gemm/prepared.json',
}
manifest = []
data = {}
for name, source in SOURCES.items():
    original = (ROOT / source).read_bytes()
    target = EVIDENCE / (name + '.json')
    if target.exists():
        assert target.read_bytes() == original, f'Evidence changed: {source}; create a new revision.'
    else:
        target.write_bytes(original)
    data[name] = json.loads(original)
    manifest.append(dict(id=name, source=source, snapshot=str(target.relative_to(HERE)),
                         sha256=hashlib.sha256(original).hexdigest()))
for name in ('triad_audit', 'confirmation_audit', 'ablation_audit'):
    assert data[name]['status'] == 'passed', name

for source in ('docs/native_cpu_slices.md', 'docs/native_lookahead_novelty_analysis.md',
               'results/native_cpu_slices_20261101/report.md',
               'results/native_cpu_large_20261102/review_20261103.md',
               'results/native_lstm_width120_serial_20261104/report.md'):
    raw=(ROOT/source).read_bytes()
    target=EVIDENCE/'documents'/source.replace('/','__')
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        assert target.read_bytes()==raw
    else:
        target.write_bytes(raw)
    manifest.append(dict(source=source,snapshot=str(target.relative_to(HERE)),sha256=hashlib.sha256(raw).hexdigest()))

# Verify paper ratios independently of rounded report text; additionally read
# all 18 original triad measurement records and bind those small records.
measurements = {}
for path in sorted((ROOT / 'results/native_cpu_evidence_20261102/triad').rglob('measurement.json')):
    record = json.loads(path.read_bytes())
    if record.get('phase') != 'triad':
        continue
    assert record['success'] and record['wire_map_matches_serial']
    assert record['log_evidence']['final_overused_nodes'] == 0
    assert record['full_check'] and record['routing_success']
    cmd=record['command']
    assert cmd[cmd.index('--num_workers')+1]=='8'
    assert cmd[cmd.index('--router_algorithm')+1]=='parallel'
    assert record['inputs']==data['gemm_input_preparation']['inputs']
    logpath=path.parent/'process.log'
    rawlog=logpath.read_bytes()
    log=rawlog.decode()
    assert 'Using up to 8 parallel worker(s)' in log
    assert 'Compiler: GNU 11.4.0' in log
    assert 'FPGA sized to 176 x 176: 61952 grid tiles' in log
    assert 'Successfully routed after' in log
    routing=float(re.search(r'# Routing took ([\d.]+) seconds',log).group(1))
    assert routing==record['routing_seconds']
    construction=re.search(r'# Computing router lookahead map took ([\d.]+) seconds',log)
    if record['cache_mode']=='rebuild':
        assert float(construction.group(1))==record['log_evidence']['stage_seconds']['lookahead_build']
    else:
        assert construction is None
    manifest.append(dict(source=str(logpath.relative_to(ROOT)),snapshot=None,
                         sha256=hashlib.sha256(rawlog).hexdigest(),scope='Original process log read and checked; not copied'))
    measurements[record['key']] = record
    target = EVIDENCE / 'measurements' / (record['key'] + '.json')
    target.parent.mkdir(exist_ok=True)
    raw = path.read_bytes()
    if target.exists():
        assert target.read_bytes() == raw
    else:
        target.write_bytes(raw)
    manifest.append(dict(id=record['key'], source=str(path.relative_to(ROOT)),
                         snapshot=str(target.relative_to(HERE)), sha256=hashlib.sha256(raw).hexdigest()))
assert len(measurements) == 18
checks = 0
for group in data['triad']['comparisons'] + data['ablation']['paired_comparisons']:
    for pair in group['pairs']:
        expected = pair['control_seconds'] / pair['candidate_seconds']
        assert math.isclose(expected, pair['process_ratio'], rel_tol=1e-12)
        if group.get('stage') == 'triad':
            c, p = measurements[pair['control_key']], measurements[pair['candidate_key']]
            assert c['cpu_budget']['cpu_set'] == p['cpu_budget']['cpu_set']
            assert c['inputs'] == p['inputs']
            assert c['wire_map_sha256'] == p['wire_map_sha256']
            assert math.isclose(c['process_seconds']/p['process_seconds'], expected, rel_tol=1e-12)
            assert p['critical_path_ns'] <= c['critical_path_ns'] * 1.05
            assert p['wirelength'] <= c['wirelength'] * 1.05
        checks += 1
    assert math.isclose(median([p['process_ratio'] for p in group['pairs']]),
                        group['process_ratio']['median'], rel_tol=1e-12)
for group in data['confirmation']['comparisons']:
    assert math.isclose(median(p['ratio'] for p in group['pairs']), group['median'], rel_tol=1e-12)

names = {'stock': 'Stock', 'frozen': 'Group', 'pipeline': 'Pipeline'}
statistics = build_statistics()
def absolute_stat(cohort, case, workers, cache, variant):
    return next(g for g in statistics['absolute'] if
                (g['cohort'],g['case'],g['workers'],g['cache'],g['variant'])==
                (cohort,case,workers,cache,variant))['metrics']
def comparison_stat(cohort, case, workers, cache, control, candidate):
    return next(g for g in statistics['comparisons'] if
                (g['cohort'],g['case'],g['workers'],g['cache'],g['control'],g['candidate'])==
                (cohort,case,workers,cache,control,candidate))['metrics']
def mean_sd(s, digits=2):
    if not s['n']:return '--'
    if s['sample_sd'] is None:return f"{s['mean']:.{digits}f} (N/A)"
    return f"${s['mean']:.{digits}f}\\pm{s['sample_sd']:.{digits}f}$"
def write_table(name, rows):
    (TABLES / (name + '.tex')).write_text('\n'.join(' & '.join(row) + r' \\' for row in rows) + '\n')

macros=[]
for cache in ['rebuild','reuse']:
    st=comparison_stat('evidence','gemm',8,cache,'stock','pipeline')['process_ratio']
    macros.append(r'\newcommand{\Gemm'+cache.title()+'MeanSD}{'+mean_sd(st,3)+'}')
for case in ['gemm','softmax','reduction']:
    st=comparison_stat('confirmation',case,8,'rebuild','frozen','pipeline')['process_ratio']
    macros.append(r'\newcommand{\Confirm'+case.title()+'MeanSD}{'+mean_sd(st,3)+'}')
(TABLES/'statistics_macros.tex').write_text('\n'.join(macros)+'\n')

rows = []
for cache in ('rebuild', 'reuse'):
    for variant in ('stock', 'frozen', 'pipeline'):
        g = next(g for g in data['triad']['configuration_summaries']
                 if (g['stage'],g['cache'],g['variant']) == ('triad', cache, variant))
        st=absolute_stat('evidence','gemm',8,cache,variant)
        proc=st['process_seconds']
        rows.append([cache.capitalize(),names[variant],mean_sd(st['lookahead_seconds']),
                     mean_sd(st['routing_seconds'])]+[f'{x:.2f}' for x in proc['values']]+
                    [mean_sd(proc),mean_sd(st['workflow_seconds'])])
write_table('triad', rows)

rows = []
for g in data['confirmation']['comparisons']:
    st=comparison_stat('confirmation',g['case'],8,g['cache'],'frozen','pipeline')['process_ratio']
    rows.append([g['case'].upper() if g['case']=='gemm' else g['case'],g['cache'],
                 f"{st['mean']:.3f}",f"{st['sample_sd']:.3f}"])
write_table('confirmation', rows)
rows = []
for case in ('gemm','elliptic'):
    for workers in (4,8):
        for cache in ('rebuild','reuse'):
            values=[]
            for candidate in ('slice','compact','pipeline','bounded'):
                g=next(g for g in data['ablation']['paired_comparisons'] if
                       (g['case'],g['workers'],g['cache_mode'],g['control'],g['candidate']) ==
                       (case,workers,cache,'frozen',candidate))
                st=comparison_stat('ablation',case,workers,cache,'frozen',candidate)['process_ratio']
                values.append(mean_sd(st,3))
            rows.append([case.upper() if case=='gemm' else case,str(workers),cache]+values)
write_table('ablation', rows)
rows=[]
for row in data['width120']['rows']:
    obs=row['last_observed']
    rows.append([row['case'].replace('dla_like.medium','DLA').replace('_',r'\_'),
                 'Legal' if row['legal'] else ('Timeout' if row['status']=='timeout' else 'Unrouted'),
                 str(obs['iteration']),str(obs['overused_nodes'])])
write_table('width120',rows)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,
    'axes.titlesize':9,'legend.fontsize':7,'xtick.labelsize':8,'ytick.labelsize':8,
    'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
blue,orange,green='#24577A','#B95B27','#32826A'
def save(fig, name):
    for ext in ('pdf','svg','png'):
        fig.savefig(FIGURES / f'{name}.{ext}',bbox_inches='tight',dpi=220)
    plt.close(fig)

fig,ax=plt.subplots(figsize=(3.35,2.15))
for cache,marker,color,offset in [('rebuild','o',blue,-0.08),('reuse','s',orange,0.08)]:
    groups=[comparison_stat('confirmation',case,8,cache,'frozen','pipeline')['process_ratio']
            for case in ('gemm','softmax','reduction')]
    xs=[i+offset for i in range(3)]
    ys=[g['mean'] for g in groups]
    ax.errorbar(xs,ys,yerr=[g['sample_sd'] for g in groups],
                fmt=marker,color=color,capsize=3,label=cache.capitalize(),markersize=5,
                markerfacecolor='white',zorder=3)
    for x,g in zip(xs,groups):
        values=g['values']
        ax.scatter([x+j for j in [-.035,0,.035]],values,s=12,color=color,alpha=.8,zorder=4)
ax.axhline(1,color='0.45',lw=.7,ls='--')
ax.set(xticks=range(3),xticklabels=['GEMM','softmax','reduction'],ylabel='Process speedup: Group / Pipeline',ylim=(.94,1.18))
ax.legend(frameon=False,loc='upper center',ncol=2)
ax.grid(axis='y',alpha=.15)
fig.tight_layout(pad=.3)
save(fig,'confirmation')

fig,axes=plt.subplots(1,2,figsize=(6.9,2.0))
for variant,color,marker in [('frozen',orange,'s'),('pipeline',blue,'o')]:
    groups=[absolute_stat('evidence','gemm',w,'rebuild',variant) for w in (4,8,16)]
    for ax,metric in zip(axes,['lookahead_seconds','process_seconds']):
        ax.errorbar([4,8,16],[g[metric]['mean'] for g in groups],
                    yerr=[g[metric]['sample_sd'] for g in groups],capsize=3,
                    marker=marker,color=color,label=names[variant])
    for w in (4,8,16):
        st=absolute_stat('evidence','gemm',w,'rebuild',variant)
        offset=-.4 if variant=='frozen' else .4
        for ax,metric in zip(axes,['lookahead_seconds','process_seconds']):
            ax.scatter([w+offset+j for j in [-.2,0,.2]],st[metric]['values'],color=color,
                       s=12,zorder=4,alpha=.75)
for ax,title,ylabel in zip(axes,['(a) Lookahead construction','(b) VPR process'],['Seconds','Seconds']):
    ax.set(xticks=[4,8,16],xlabel='Physical cores',ylabel=ylabel,title=title)
    ax.grid(axis='y',alpha=.18)
    ax.legend(frameon=False)
fig.tight_layout(pad=.4,w_pad=2)
save(fig,'scaling')

fig,ax=plt.subplots(figsize=(6.9,1.35))
fig.subplots_adjust(left=.01,right=.99,top=.98,bottom=.02)
ax.set(xlim=(0,10),ylim=(0,1.65));ax.axis('off')
boxes=[(.1,.8,1.8,.75,'Ordered samples\n(layer, wire type)',blue),
       (2.1,.8,1.8,.75,'Private Dijkstra\nworkers',blue),
       (4.1,.8,1.8,.75,'Ordered merge\nstrict delay ties',blue),
       (6.1,.8,1.8,.75,'Wire map\ninterpolation',blue),
       (8.1,.8,1.8,.75,'Native router\nFULL + STA',green)]
for x,y,w,h,label,color in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.02',facecolor=color,edgecolor='none'))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',color='white',fontsize=8.7)
for x1,x2 in [(1.92,2.08),(3.92,4.08),(5.92,6.08),(7.92,8.08)]:
    ax.annotate('',xy=(x2,1.17),xytext=(x1,1.17),arrowprops={'arrowstyle':'->','lw':1})
ax.text(5,.43,'Pipeline: overlap floods across groups; preserve sample order at merge',ha='center',fontsize=8)
ax.text(5,.12,'Bounded variant: compact tables + per-group slice commit (evaluated separately)',ha='center',fontsize=8,color=orange)
save(fig,'method')

(EVIDENCE/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(EVIDENCE/'paper_checks.json').write_text(json.dumps({'status':'passed','ratio_pairs_recomputed':checks,
    'original_triad_records_checked':len(measurements),'historical_audits':'passed; retained as evidence, not re-executed',
    'pending_component_experiment':'excluded from numerical paper claims','new_solver_runs':0},indent=2)+'\n')
print(f'Generated four tables, three figures; verified {checks} paired ratios and 18 original triad records.')
