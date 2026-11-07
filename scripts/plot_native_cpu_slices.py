"""Publication-exportable paired process ratios; whiskers show observed range."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parents[1]/'results/native_cpu_slices_20261101'


def main():
    data=json.loads((OUT/'analysis.json').read_text())
    assert data['status']=='complete'
    figures=OUT/'figures';figures.mkdir(exist_ok=True)
    fig,axes=plt.subplots(2,2,figsize=(9.5,6.4),sharex=True)
    colors=['#0072B2','#D55E00','#CC79A7','#009E73']
    for row,case in enumerate(['gemm','elliptic']):
        for col,cache in enumerate(['rebuild','reuse']):
            ax=axes[row,col]
            for index,(variant,color) in enumerate(zip(['slice','compact','pipeline','bounded'],colors)):
                points=[p for p in data['paired_comparisons'] if p['case']==case and p['cache_mode']==cache
                        and p['control']=='frozen' and p['candidate']==variant]
                points.sort(key=lambda p:p['workers'])
                x=[([4,8].index(p['workers']))+(index-1.5)*0.14 for p in points]
                y=[p['process_ratio']['median'] for p in points]
                lower=[v-p['process_ratio']['min'] for v,p in zip(y,points)]
                upper=[p['process_ratio']['max']-v for v,p in zip(y,points)]
                ax.errorbar(x,y,yerr=[lower,upper],fmt='o',capsize=4,color=color,label=variant)
                for pos,p in zip(x,points):
                    ax.scatter([pos]*len(p['pairs']),[r['process_ratio'] for r in p['pairs']],s=12,alpha=.4,color=color)
            ax.axhline(1,color='0.4',linewidth=1,linestyle='--')
            ax.set_title(f'{case.upper()} / {cache}')
            ax.set_xticks([0,1],['4 cores','8 cores']);ax.set_xlim(-.45,1.45)
            ax.set_ylabel('Process speedup vs frozen CPU')
            ax.grid(axis='y',alpha=.25)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.94),frameon=False,ncol=4,fontsize=9)
    fig.suptitle('Native lookahead ablations: paired median and observed range (n=3)',fontsize=12)
    fig.text(.5,.01,'Same physical CPU set within each pair; shared host; fixed placement. Whiskers are not confidence intervals.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.035,1,.90])
    for suffix in ['pdf','svg','png']:fig.savefig(figures/f'paired_process.{suffix}',dpi=170)
    plt.close(fig)
    print(str(figures/'paired_process.pdf'))


if __name__=='__main__':
    main()
