"""Render the two native PGFPlots figures from the matched summary rows."""
from pathlib import Path

COLORS = ['28577B', 'D68A40', '86BAB0']
WORKLOADS = ['gemm', 'bnn', 'lstm']
SHORT = dict(stock='Stock', group='Group', flat='Flat', pipeline='Pipeline',
             alt_cpu='CPU', alt_cuda='GPU')


def draw_panel(data, metric, keys, width, limit, ticks, title, bar_width, ratios=False):
    labels = []
    for key in keys:
        if ratios:
            src, dst = key
            labels.append(r'{\shortstack{' + SHORT[src] + r'\\$\downarrow$\\' + SHORT[dst] + '}}')
        else:
            labels.append(SHORT[key])
    lines = [
        r'\begin{tikzpicture}\begin{axis}[',
        rf'width={width}\textwidth,height=1.60cm,scale only axis,',
        rf'xmin=-0.5,xmax={len(keys)-0.5},ymin=0,ymax={limit},',
        'xtick={' + ','.join(str(i) for i in range(len(keys))) + '},',
        'xticklabels={' + ','.join(labels) + '},ytick={' + ticks + '},',
        r'axis lines*=left,axis line style={black!65},tick align=outside,',
        r'ymajorgrids,grid style={black!15},tick style={black!55},',
        r'ticklabel style={font=\scriptsize},xticklabel style={align=center},',
        r'title style={font=\footnotesize},title={' + title + '}]',
    ]
    for j, case in enumerate(WORKLOADS):
        coords = []
        for i, key in enumerate(keys):
            r = data[case, metric, key]
            center = i + (j - 1) * 0.23
            coords.append(f"({center:.2f},{r['mean']}) +- (0,{r['sd']})")
        lines += [
            rf'\addplot[ybar,mark=none,bar width={bar_width}pt,bar shift=0pt,',
            rf'fill=case{j},draw=black!80,line width=0.25pt,',
            r'error bars/.cd,y dir=both,y explicit,error bar style={black,line width=0.5pt},',
            r'error mark options={mark size=1.3pt,line width=0.5pt}] coordinates {',
            '\n'.join(coords) + '};',
        ]
    if ratios:
        lines.append(rf'\draw[densely dashed,black!80,thin] (axis cs:-0.5,1)--(axis cs:{len(keys)-0.5},1);')
    return '\n'.join(lines + [r'\end{axis}\end{tikzpicture}'])


def save(root, name, panels, caption):
    colors = [rf'\definecolor{{case{i}}}{{HTML}}{{{color}}}' for i, color in enumerate(COLORS)]
    legend = r'\quad '.join(
        rf'\tikz\draw[fill=case{i},thin] (0,0) rectangle (.20,.12); {case.upper()}'
        for i, case in enumerate(WORKLOADS)
    )
    figure = [r'\begin{figure*}[t]\centering', *colors,
              r'{\scriptsize ' + legend + r'}\par\smallskip',
              r'\hfill'.join(panels), r'\caption{' + caption + r'}\label{fig:' + name + '}',
              r'\end{figure*}']
    (root / 'figures' / f'{name}.tex').write_text('\n'.join(figure) + '\n')


def build(root: Path, seconds, paired):
    times = {(r['case'], r['metric'], r['arm']): r for r in seconds}
    ratios = {(r['case'], r['metric'], (r['numerator'], r['denominator'])): r for r in paired}
    full = ['stock', 'pipeline', 'alt_cpu', 'alt_cuda']
    all_arms = ['stock', 'group', 'flat', *full[1:]]
    lower = [('group', 'flat'), ('group', 'pipeline'), ('flat', 'pipeline'), ('pipeline', 'alt_cpu')]
    higher = [('stock', 'pipeline'), ('pipeline', 'alt_cuda'), ('alt_cpu', 'alt_cuda'), ('stock', 'alt_cuda')]
    end_to_end = [higher[0], lower[-1], *higher[1:]]
    assert len(times) == 30 and len(ratios) == 39
    save(root, 'native_times', [
        draw_panel(times, 'E2', all_arms, '.51', 155, '0,50,100,150', r'\constructiontime{} (s)', 6),
        draw_panel(times, 'Process', full, '.39', 325, '0,100,200,300', r'\processtime{} (s)', 6),
    ], r'Times for three fresh processes per configuration (mean $\pm$ sample SD). Pipeline denotes STRICT Pipeline. CPU and GPU denote the ALT backends. Group and Flat measure construction only.')
    save(root, 'paired_speedups', [
        draw_panel(ratios, 'E2', lower, '.275', 2.15, '0,1,2', r'\constructionspeedup{} ($\times$)', 4.5, True),
        draw_panel(ratios, 'E2', higher, '.275', 31, '0,10,20,30', r'\constructionspeedup{} ($\times$)', 4.5, True),
        draw_panel(ratios, 'Process', end_to_end, '.315', 2.55, '0,1,2', r'\processspeedup{} ($\times$)', 4.5, True),
    ], r'Paired speedups. $A\to B$ reports $T_A/T_B$ within each workload and repeat. Bars show the mean of three ratios and whiskers show sample SD. Dashed lines mark $1\times$. The construction panels use different linear scales to resolve near-parity comparisons.')


def motivation_figure(root, shares):
    lines = [r'\begin{figure}[t]\centering',
             r'\begin{tikzpicture}[x=.056cm,y=.46cm,font=\footnotesize]',
             r'\definecolor{subtotal}{HTML}{28577B}\definecolor{complete}{HTML}{86BAB0}',
             r'\node[font=\footnotesize\bfseries] at (42,7.48) {Share of time spent in Lookahead Construction (\%)};',
             r'\draw[fill=subtotal] (-16,6.3) rectangle (-12,6.55);',
             r'\node[anchor=west] at (-11,6.42) {Construction + routing};',
             r'\draw[fill=complete] (47,6.3) rectangle (51,6.55);',
             r'\node[anchor=west] at (52,6.42) {End-to-end process};',
             r'\foreach \x in {0,50,100}{\draw[black!20] (\x,.25)--(\x,5.9);',
             r'\node[below,font=\scriptsize] at (\x,.25) {\x\%};}']
    for i, row in enumerate(shares):
        y = 5.4 - 2*i
        lines.append(rf"\node[anchor=east] at (0,{y-.32:.2f}) {{{row['case'].upper()}}};")
        for offset, metric, color, ink in [(0, 'subtotal_pct', 'subtotal', 'white'),
                                           (-.65, 'process_pct', 'complete', 'black')]:
            value = row[metric]
            center = y + offset
            lines.append(rf'\draw[fill={color},thin] (0,{center-.29:.2f}) rectangle ({value:.6f},{center+.29:.2f});')
            lines.append(rf'\node[anchor=east,text={ink},font=\scriptsize] at ({value:.6f},{center:.2f}) {{{value:.2f}\%}};')
    lines += [r'\end{tikzpicture}',
              r'\caption{Construction share in three formal Stock runs per workload. Upper bars divide median \constructiontime{} by the sum of median construction and median routing times. Lower bars divide mean \constructiontime{} by mean \processtime{}.}\label{fig:motivation}',
              r'\end{figure}']
    (root/'figures'/'motivation.tex').write_text('\n'.join(lines)+'\n')
