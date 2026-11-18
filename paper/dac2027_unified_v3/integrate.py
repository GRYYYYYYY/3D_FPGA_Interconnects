"""Fill V3 only from the completed single-worker experiment and route archive."""
import csv,json,statistics,sys,subprocess
from pathlib import Path
here=Path(__file__).resolve().parent
audit=Path(sys.argv[1])
def draft(file):
    name='paper/dac2027_unified_v3/'+file
    return subprocess.check_output(['git','show','ca5d8106da56083750da8e0c31bf1c05a547ebb5:'+name],cwd=here,text=True)
def rows(name):
    with (audit/name).open() as f:return list(csv.DictReader(f))
cases=['gemm','bnn','lstm']
arms=['stock','group','flat','pipeline','alt_cpu','alt_cuda']
names=dict(zip(arms,['Stock','Group','Flat','STRICT Pipeline','ALT CPU','ALT CUDA']))
def tex(p,s): (here/p).write_text(s.strip()+'\n')
def pm(r,places=2):return f"${float(r['mean']):.{places}f}\\,\\pm\\,{float(r['sd']):.{places}f}$"
def fmt(x):return f'{x:.2f}'
def label(c):return c.upper()
def box(rows_):return '\n'.join(' & '.join(cells)+r' \\' for cells in rows_)
verification=json.loads((audit/'verification.json').read_text())
assert verification['distinct_worker_count']==1
assert verification['concurrency_overlaps']==0
for c in cases:
    gate = verification['cases'][c]['qualification']
    assert all(gate[k] for k in ('strict_map', 'alt_map', 'complete_capture', 'cpu_verify'))
coverage=rows('coverage.csv')
assert len(coverage)==18
measured=['gemm','bnn']
by_cell={(r['case'],r['arm']):r for r in coverage}
assert set(by_cell)=={(case,arm) for case in cases for arm in arms}
for case in measured:
    for arm in arms:
        assert all(int(by_cell[case,arm][field])==3 for field in ('invoked','recorded','passed'))
assert all(int(by_cell['lstm',arm]['invoked'])==0 for arm in arms)
case_names=' and '.join(c.upper() for c in measured)
full_count=verification['full_invocations']
control_count=verification['controls']
assert (full_count,control_count)==(24,12)
scope=(f"GEMM and BNN completed all six configurations on one worker, for "
       f"{full_count} full-process and {control_count} construction-control invocations. ")
qor=rows('qor.csv')
assert len(qor)==12+verification['formal_records'] and all(r['independent_FULL_STA'] in ('True','False') for r in qor if r['original_route_sha'])
seq=rows('raw_timing.csv');assert len(seq)==verification['formal_records']
seconds={(r['case'],r['arm'],r['metric']):r for r in rows('seconds.csv')}
paired={(r['case'],r['numerator'],r['denominator'],r['metric']):r for r in rows('paired.csv')}
stages=rows('process_stages.csv');amd=rows('amdahl.csv')
maps=json.loads((audit/'map_differences.json').read_text())
def val(c,a,b,m):return float(paired[c,a,b,m]['mean'])
def series(a,b,m):
    return ' and '.join(fmt(val(c,a,b,m)) if (c,a,b,m) in paired else 'unavailable' for c in measured)
def avg(rs,k):return statistics.mean(float(r[k]) for r in rs)
def group(c,a='pipeline',b='alt_cuda'):return [r for r in amd if r['case']==c and r['source']==a and r['candidate']==b]
def table(title,key,lines,metrics=("E2", "Process")):
    header=' & '.join(['',*(list(metrics)*len(measured))])
    cols='l'+'rr'*len(measured)
    heads=' & '.join(['',*(r'\multicolumn{2}{c}{'+c.upper()+'}' for c in measured)])
    return (r'\begin{table*}[t]\centering\caption{'+title+r'}\label{'+key+r'}\begin{tabular}{'+cols+r'}\toprule'+'\n'
            +heads+r'\\'+'\n'+header+r'\\\midrule'+'\n'+box(lines)+r'\bottomrule\end{tabular}\end{table*}')
times=[[names[a]]+[pm(seconds[c,a,m]) if (c,a,m) in seconds else '---' for c in measured for m in ('E2','Process')] for a in arms]
tex('tables/unified_times.tex',table('Native seconds, mean and sample SD of three fresh processes. Group and Flat are construction controls. Each successful full invocation supplies both observations. Dashes indicate an unmeasured scope or fewer than three valid observations.','tab:time',times))
contrasts=[('group','flat'),('group','pipeline'),('flat','pipeline'),('stock','pipeline'),('pipeline','alt_cuda'),('stock','alt_cuda'),('alt_cpu','alt_cuda')]
ratios=[[names[a]+' / '+names[b]]+[pm(paired[c,a,b,m],3) if (c,a,b,m) in paired else '---' for c in measured for m in ('E2','Process')] for a,b in contrasts]
tex('tables/unified_ratios.tex',table('Paired speedups. Each repeat divides the first named configuration by the second. Entries are the mean and sample SD of three ratios. Dashes indicate comparisons without three valid pairs.','tab:ratios',ratios))
gem=[r for r in stages if r['case']=='gemm' and r['arm']=='stock']
stage_means=[avg(gem,k) for k in ('rr_load','E2','routing','other')]
total=sum(stage_means)
(here/'figures').mkdir(exist_ok=True)
fig=r'''\begin{figure}[t]\centering
\begin{tikzpicture}[x=0.075cm,y=1cm,font=\footnotesize]
'''
left=0
for value,shade in zip(stage_means,['gray!35','blue!40','orange!50','gray!12']):
    right=left+100*value/total
    fig+=fr'\draw[fill={shade}] ({left:.4f},0) rectangle ({right:.4f},.4);'+'\n'
    fig+=fr'\node at ({(left+right)/2:.4f},.2) {{{100*value/total:.1f}\%}};'+'\n';left=right
fig+=r'\end{tikzpicture}\caption{Fixed-input GEMM routing evaluation on Stock. From left to right, '
fig+=', '.join(n+' '+fmt(v)+' s' for n,v in zip(['RR XML loading','lookahead','routing','remaining Process'],stage_means))
fig+=f'. Mean complete Process was {total:.2f} s. The residual includes initialization, checking, STA and serialization.'+r'}\label{fig:motivation}\end{figure}'
tex('figures/motivation.tex',fig)
results=draft('sections/native_results.tex')
start=results.index('\\subsection{Matched Native Construction')
end=results.index('\\subsection{3D RRG',start)
part=r'''\subsection{Matched Native Construction and Process}
\input{tables/unified_times}
\input{tables/unified_ratios}
'''
part+=scope+'Stock/Pipeline construction speedups were '+series('stock','pipeline','E2')+' for '+case_names+', respectively (Tables~\\ref{tab:time} and~\\ref{tab:ratios}). The corresponding Process ratios were '+series('stock','pipeline','Process')+'. '
part+='Across the same workloads, eliminating Pipeline construction while holding each repeat\'s remainder fixed gives mean upper bounds of '+', '.join(fmt(avg(group(c),'zero_E2')) for c in measured)+'. Substituting measured CUDA construction predicts '+', '.join(fmt(avg(group(c),'replace_E2')) for c in measured)+', versus observed Pipeline/CUDA ratios of '+series('pipeline','alt_cuda','Process')+'.\n'
part+=r'\subsection{Backend Comparison: ALT CPU versus ALT CUDA}'+'\n'
part+='With the ALT rule fixed, the CUDA backend gives E2 speedups of '+series('alt_cpu','alt_cuda','E2')+'. The corresponding Process ratios are '+series('alt_cpu','alt_cuda','Process')+'. Both measurements charge conversion and output handoff. Process additionally includes RR loading, routing and the native checks.\n'
results=results[:start]+part+results[end:]
results=results.replace('Matched E2 measurements determine whether this storage bound costs construction time.',
                        'Group/Pipeline construction ratios were '+series('group','pipeline','E2')+' on '+case_names+', respectively. Flat/Pipeline ratios were '+series('flat','pipeline','E2')+' (Table~\\ref{tab:ratios}).')
n=results.index('Auxiliary qualified maps')
clause=[]
for c in cases:
    d=maps[c]
    clause.append(f"{int(d['congestion_word_differences']):,}")
qpassed=sum(r['stock_gate']=='True' and r['independent_FULL_STA']=='True' and r['overuse']=='0' for r in qor)
results=results[:n]+'Stock and STRICT wire maps agreed across all three cases, as did the complete ALT CPU/CUDA outputs. ALT changed '+', '.join(clause)+' congestion words relative to STRICT on GEMM, BNN and LSTM, respectively. '
if all(d['delay_word_differences']==d['missing_state_differences']==0 for d in maps.values()):results+='Delay words and missing masks agreed. '
available=[r for r in qor if r['stock_gate']]
passed=verification['independently_passed_routes']
results+=f"Independent FULL/STA passed for {passed} of {verification['recorded_routes']} emitted routes. "
results+=f"All {len(available)} invocations with a valid Stock reference met the CPD/WL and zero-overuse criteria. " if qpassed==len(available) else f"{qpassed} of {len(available)} scored invocations passed all three criteria. "
results+=("Two GEMM routes were read back on the editing host. LSTM Stock wrote the expected map and then "
          "faulted on an invalid predecessor edge during route-tree construction. LSTM's three legal routes "
          "therefore lack a matched Stock QoR reference. ")

# Keep the greatest signed deviation for each metric; either can fail the one-sided gate.
qor_lines=[]
for arm in arms[1:]:
    cells=[names[arm]]
    for case in measured:
        observed=[row for row in qor if row['case']==case and row['arm']==arm and row['phase']=='formal']
        assert len(observed)==3
        for metric in ('CPD_delta_pct','WL_delta_pct'):
            values=[float(r[metric]) for r in observed if r['stock_gate'] and r[metric]]
            cells.append(f"{max(values):+.3f}" if len(values)==3 else '---')
    qor_lines.append(cells)
qor_table=table(
    r'Maximum signed CPD and WL changes (\%) relative to repeat-matched Stock. Each entry requires three scored formal routes. A dash denotes insufficient matched references. The common upper limit is $+5\%$.',
    'tab:qor',qor_lines,metrics=('CPD','WL')
)
tex('tables/unified_qor.tex',qor_table.replace('table*}', 'table}'))
results+=r'Table~\ref{tab:qor} gives the greatest Stock-relative changes.'+'\n'+r'\input{tables/unified_qor}'+'\n'
failed = [r for r in qor if r['stock_gate']=='False' or r['independent_FULL_STA']=='False' or (r['original_route_sha'] and r['overuse']!='0')]
if failed:
    from collections import Counter
    failures=Counter((r['case'],r['arm']) for r in failed)
    results+='Failed qualifications by workload and configuration include '+', '.join(f"{c.upper()} {names[a]} ({n})" for (c,a),n in sorted(failures.items()))+'. '
results+='The archive retains route and map digests with each legality and QoR record. The two-layer graphs, fixed seeds and dense GPU state limit generalization. Compatible caches can remove construction entirely.\n'
tex('sections/native_results.tex',results)
intro=draft('sections/introduction.tex')
intro+=r'\input{figures/motivation}'+'\n'
intro+=f"On the fixed-input GEMM path, fresh Stock construction takes {stage_means[1]:.2f} s of a {total:.2f} s process (Fig.~\\ref{{fig:motivation}}). Construction accounts for {100*stage_means[1]/total:.1f}\\% of that time. Paired Stock/ALT CUDA Process ratios for {case_names} are {series('stock','alt_cuda','Process')}.\n"
tex('sections/introduction.tex',intro)
abstract=draft('sections/abstract.tex').split('We specify a single-worker')[0]
abstract+='GEMM and BNN each complete six configurations with three repeats on one eight-core/H100 worker. Paired Stock/ALT CUDA Process speedups are '+series('stock','alt_cuda','Process')+' on '+case_names+', respectively. The corresponding construction speedups are '+series('stock','alt_cuda','E2')+'. Results apply to fixed-input routing on these two-layer graphs.'
abstract+=' Auxiliary LSTM checks confirm STRICT map identity and ALT backend agreement.'
tex('sections/abstract.tex',abstract)
p=here/'sections/conclusion.tex'
s=draft('sections/conclusion.tex').split('Establishing the end-to-end')[0]+'On these two-layer graphs, the same-rule CPU/CUDA comparison yields construction speedups of '+series('alt_cpu','alt_cuda','E2')+'. Ordered STRICT consumption provides a conditional native-map guarantee, while ALT requires independent route qualification.\n'
s+='The 36 primary GEMM and BNN runs establish matched performance. LSTM extends the auxiliary map and backend checks.\n'
tex('sections/conclusion.tex',s)
p=here/'main.tex';p.write_text(draft('main.tex').replace(r'\clearpage','').replace('Internal draft --- unified measurements pending','Internal review --- GEMM and BNN primary evaluation'))
