"""Rebuild the review tables from pinned Git objects without an experiment checkout."""
import csv
import hashlib
import io
import json
import math
import re
import statistics as st
import subprocess
import zipfile
from pathlib import Path

from result_figures import build as build_result_figures

ROOT = Path(__file__).resolve().parent
REVIEW = ROOT / 'review'
B = '671a31e1c9fd18d2242a5c32c4d53ac5f50ec992'
C = '11c3911bbe54332fb5d32198511ce1ae1775f9b4'
BASE = 'experiments/dac2027_unified_v3'
cases = ['gemm', 'bnn', 'lstm']
names = dict(stock='Stock', group='Group', flat='Flat', pipeline='STRICT Pipeline',
             alt_cpu='ALT CPU', alt_cuda='ALT GPU')


def blob(commit, name):
    return subprocess.check_output(['git', 'show', f'{commit}:{BASE}/{name}'], cwd=ROOT)


def rows(data):
    return list(csv.DictReader(io.StringIO(data.decode())))


def write_csv(filename, data):
    with (REVIEW / filename).open('w') as f:
        writer = csv.DictWriter(f, data[0].keys(), lineterminator='\n')
        writer.writeheader()
        writer.writerows(data)


def verify(row, values):
    assert int(row['n']) == len(values) == 3
    expected = [*values, st.mean(values), st.stdev(values)]
    for key, value in zip(('r0', 'r1', 'r2', 'mean', 'sd'), expected):
        assert math.isclose(float(row[key]), value, abs_tol=1e-12, rel_tol=0), (row, key)
    return dict(zip(('r0','r1','r2','mean','sd'), expected))


raw, seconds, ratios, routes = [], [], [], []
unique_ids, identities = set(), set()
gold = json.loads(blob(B, 'golden_maps.json'))
for alloc, rev, workloads in [('B', B, cases[:2]), ('C', C, cases[2:])]:
    prefix = f'allocation_{alloc.lower()}/audit/'
    filenames = subprocess.check_output(['git','ls-tree','--full-tree','--name-only',f'{rev}:{BASE}/{prefix[:-1]}'],text=True).splitlines()
    archive = {n: blob(rev, prefix+n) for n in filenames}
    zipdata = archive['native_process_records.zip']
    assert hashlib.sha256(zipdata).hexdigest() == json.loads(archive['verification.json'])['archive_sha256']
    z = zipfile.ZipFile(io.BytesIO(zipdata))
    assert z.testzip() is None
    def receipt(path):
        return json.loads(z.read(path))
    timing = {}
    intervals = []
    env = json.loads(archive['environment.json'])
    for row in rows(archive['raw_timing.csv']):
        c, a, r = row['case'], row['arm'], int(row['repeat'])
        p = f'formal/{c}/{r}/{a}/'
        rec = receipt(p+'record.json')
        iv = receipt(p+'invocation.json')
        assert rec['host'] == iv['host'] == row['host'] == env['host']
        assert rec['gpu'] == row['gpu'] == env['gpu'].split(',')[0]
        assert rec['returncode'] == 0 and rec['local_pass'] and c in workloads
        ns = int(row['E2_ns'])
        assert re.findall(rb'^V3_COMPUTE_NS (\d+)',z.read(p+'process.log'),re.M) == [str(ns).encode()]
        assert rec['e2_ns'] == ns and rec['wall_ns'] == int(row['elapsed_to_exit_ns'])
        assert rec['end_ns'] - rec['begin_ns'] == rec['wall_ns']
        full = a not in ('flat','group')
        assert row['Process_ns'] == (str(rec['wall_ns']) if full else '')
        assert (c,a,r) not in timing
        timing[c,a,r] = {'E2':ns,'Process':rec['wall_ns'] if full else None}
        intervals.append((rec['begin_ns'],rec['end_ns']))
        raw.append(dict(allocation=alloc,case=c,arm=a,repeat=r,E2_s=f'{ns/1e9:.9f}',
                        Process_s=f"{rec['wall_ns']/1e9:.9f}" if full else ''))
    assert len(timing) == 18*len(workloads)
    ordered = sorted(intervals)
    assert all(x[1]<=y[0] for x,y in zip(ordered,ordered[1:]))
    for row in rows(archive['seconds.csv']):
        c,a,m = (row[k] for k in ('case','arm','metric'))
        stats = verify(row,[timing[c,a,i][m]/1e9 for i in range(3)])
        seconds.append(dict(allocation=alloc,case=c,arm=a,metric=m,**stats))
    for row in rows(archive['paired.csv']):
        c,a,b,m = (row[k] for k in ('case','numerator','denominator','metric'))
        stats = verify(row,[timing[c,a,i][m]/timing[c,b,i][m] for i in range(3)])
        ratios.append(dict(allocation=alloc,case=c,numerator=a,denominator=b,metric=m,**stats))
    qrows = rows(archive['qor.csv'])
    refs = {(q['case'],q['phase'],q['repeat']):q for q in qrows if q['arm']=='stock' and q['original_route_sha']}
    for q in qrows:
        c,a,ph,r = (q[k] for k in ('case','arm','phase','repeat'))
        p = f'{ph}/{c}/{r}/{a}/'
        rec = receipt(p+'record.json')
        sha = rec['route_sha256']
        assert rec['map_sha256'] == q['map_sha'] == gold[c]['alt' if a.startswith('alt') else 'strict']
        if not sha:
            assert (alloc,c,a,ph,rec['returncode']) == ('B','lstm','stock','qualification',-11)
            continue
        rb = receipt(p+'readback/record.json')
        assert sha == q['original_route_sha'] == rb['original_sha']
        assert rb['passed'] and rb['returncode']==0 and rb['metrics']['full_check']
        assert q['independent_FULL_STA']=='True' and rec['overuse']==int(q['overuse'])==0
        for report in ('setup','hold'):
            assert z.getinfo(p+f'readback/report_timing.{report}.rpt').file_size>0
        assert rb['metrics']['critical_path_ns']==float(q['CPD_ns'])
        assert rb['metrics']['wirelength']==int(q['WL'])
        ref = refs.get((c,ph,r))
        delta = {}
        for metric, field in [('CPD','CPD_ns'),('WL','WL')]:
            if ref:
                d = 100*(float(q[field])/float(ref[field])-1)
                assert abs(d-float(q[metric+'_delta_pct']))<1e-10 and d<=5
                delta[metric] = d
        assert q['stock_gate']==('True' if ref else '')
        invocation = alloc+'/'+p.rstrip('/')
        assert invocation not in unique_ids
        unique_ids.add(invocation)
        identities.add((c,sha))
        routes.append(dict(workload=c,invocation=invocation,phase=ph,arm=a,repeat=r,route_sha=sha,
                           full_sta=True,zero_overuse=True,stock_sha=ref['original_route_sha'] if ref else '',
                           gate='pass' if ref else 'unscored',cpd_ns=q['CPD_ns'],wl=q['WL'],
                           delta_cpd_pct=delta.get('CPD',''),delta_wl_pct=delta.get('WL','')))
    if alloc=='B':
        for c in cases:
            cap=[q['capture_sha'] for q in qrows if q['case']==c and q['phase']=='qualification' and q['arm'].startswith('alt')]
            assert len(cap)==2 and cap[0] and cap[0]==cap[1]
    else:
        p='diagnostic/lstm_original_stock/'
        diag=receipt(p+'record.json')
        rb=receipt(p+'readback/record.json')
        assert diag['returncode']==0 and rb['passed'] and rb['original_sha']==diag['route_sha256']
        assert ('lstm',rb['original_sha']) not in identities
        diagnostic_sha=rb['original_sha']

assert len(raw)==54 and len(seconds)==30 and len(ratios)==39
assert len(identities)==len(unique_ids)==len(routes)==65
write_csv('raw_seconds.csv',raw)
write_csv('seconds.csv',seconds)
write_csv('paired.csv',ratios)
write_csv('routes.csv',routes)
summary=[]
for c in cases:
    s=[r for r in routes if r['workload']==c]
    summary.append(dict(workload=c,unique_routes=len({r['route_sha'] for r in s}),full_sta=sum(r['full_sta'] for r in s),
                        zero_overuse=sum(r['zero_overuse'] for r in s),stock_reference=sum(bool(r['stock_sha']) for r in s),
                        threshold_pass=sum(r['gate']=='pass' for r in s),formal=sum(r['phase']=='formal' for r in s)))
write_csv('route_counts.csv',summary)

def table(filename, caption, label, headers, body):
    env = 'table' if label == 'qor' else 'table*'
    style = r'\footnotesize\setlength{\tabcolsep}{2pt}' if label == 'qor' else r'\small\setlength{\tabcolsep}{4pt}'
    lines=[r'\begin{'+env+'}[t]\\centering'+style,r'\caption{'+caption+r'}\label{tab:'+label+'}',
           r'\begin{tabular}{lrrrrrr}\toprule',
           ' & '+r' & '.join(r'\multicolumn{2}{c}{'+c.upper()+'}' for c in cases)+r'\\',
           ' & '+' & '.join(headers*3)+r'\\\midrule']
    for label, cells in body:
        lines.append(' & '.join([label]+cells)+r'\\')
    lines.append(r'\bottomrule\end{tabular}\end{'+env+'}')
    (ROOT/'tables'/filename).write_text('\n'.join(lines)+'\n')

build_result_figures(ROOT, seconds, ratios)
table('unified_qor.tex','Largest signed change (\\%) against repeat-matched Stock among three formal routes per candidate. The common upper bound for each metric is $+5\\%$.','qor',['CPD','WL'],
      [(n,[f"{max(r[field] for r in routes if r['workload']==c and r['phase']=='formal' and r['arm']==a):+.3f}"
           for c in cases for field in ['delta_cpd_pct','delta_wl_pct']]) for a,n in names.items() if a!='stock'])
print(summary, 'separate original-binary diagnostic', diagnostic_sha)
