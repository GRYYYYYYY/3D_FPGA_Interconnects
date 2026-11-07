"""Export audited CPU baseline, held-out-placement and scaling figures."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parents[1]/'results/native_cpu_evidence_20261102'


def main():
    data=json.loads((OUT/'analysis.json').read_text());assert data['status']=='complete'
    out=OUT/'figures';out.mkdir(exist_ok=True)
    def save(fig,name):
        for ext in ['pdf','svg','png']:fig.savefig(out/f'{name}.{ext}',dpi=170)
        plt.close(fig)
    def mark(ax,x,p,color):
        d=p['process_ratio']
        if d:
            ax.errorbar(x,d['median'],yerr=[[d['median']-d['min']],[d['max']-d['median']]],fmt='o',color=color,capsize=4)
            ax.scatter([x]*len(d['values']),d['values'],color=color,s=14,alpha=.45)
        else:ax.text(x,1,'invalid',ha='center',color='red',fontsize=8)
    fig,axes=plt.subplots(1,2,figsize=(9,4.5))
    for ax,cache in zip(axes,['rebuild','reuse']):
        for x,(control,candidate,color) in enumerate([('stock','frozen','#0072B2'),('stock','pipeline','#009E73'),('frozen','pipeline','#D55E00')]):
            p=next(p for p in data['comparisons'] if p['stage']=='triad' and p['cache']==cache and p['control']==control and p['candidate']==candidate)
            mark(ax,x,p,color)
        ax.set_xticks([0,1,2],['stock to\nsampling','stock to\npipeline','sampling to\npipeline'])
        ax.set_title('GEMM, 8 cores / '+cache);ax.axhline(1,color='.5',ls='--');ax.set_ylabel('Paired process speedup');ax.grid(axis='y',alpha=.2)
    fig.suptitle('Three-way native CPU comparison');fig.text(.5,.01,'n=3 runtime pairs; observed min/max, not confidence intervals. Shared host.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.045,1,.95]);save(fig,'triad')
    fig,axes=plt.subplots(2,2,figsize=(9,6))
    for i,cache in enumerate(['rebuild','reuse']):
        for j,control in enumerate(['stock','frozen']):
            ax=axes[i,j]
            for seed,marker,color in [(1,'o','#0072B2'),(2,'s','#D55E00')]:
                for x,circuit in enumerate(['alu4','diffeq','s38417']):
                    p=next(p for p in data['comparisons'] if p['stage']=='generalization' and p['case']==f'{circuit}_s{seed}' and p['cache']==cache and p['control']==control and p['candidate']=='pipeline')
                    if p['process_ratio']:ax.scatter(x+(seed-1.5)*.12,p['process_ratio']['median'],marker=marker,color=color,label=f'placement seed {seed}' if x==0 else None)
                    else:ax.text(x,1,f's{seed} invalid',ha='center',color='red',fontsize=7)
            ax.set_xticks([0,1,2],['alu4','diffeq','s38417']);ax.axhline(1,color='.5',ls='--');ax.set_title(f'{control} to pipeline / {cache}');ax.set_ylabel('Process speedup');ax.grid(axis='y',alpha=.2)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.95),ncol=2,frameon=False)
    fig.suptitle('Held-out circuits: two fresh placements, 8 cores');fig.text(.5,.01,'One timing sample per arm/cache/placement; seeds are not independent circuits. Shared host.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.045,1,.88]);save(fig,'heldout')
    fig,axes=plt.subplots(1,2,figsize=(9,4.5))
    for x,n in enumerate([4,8,16]):
        p=next(p for p in data['comparisons'] if p['case']=='gemm' and p['workers']==n and p['cache']=='rebuild' and p['control']=='frozen' and p['candidate']=='pipeline')
        mark(axes[0],x,p,'#009E73')
    axes[0].set_xticks([0,1,2],['4 cores','8 cores','16 cores']);axes[0].axhline(1,color='.5',ls='--');axes[0].set_ylabel('Pipeline / sampling paired speedup');axes[0].set_title('Same-core process comparisons')
    for variant,color in [('frozen','#0072B2'),('pipeline','#D55E00')]:
        points=[next(r for r in data['configuration_summaries'] if r['case']=='gemm' and r['workers']==n and r['cache']=='rebuild' and r['variant']==variant) for n in [4,8,16]]
        axes[1].plot([4,8,16],[r['peak_hwm_kib']['median']/1024 for r in points],'-o',label=variant,color=color)
    axes[1].set_xticks([4,8,16]);axes[1].set_xlabel('Physical cores');axes[1].set_ylabel('Observed process HWM (MiB)');axes[1].legend(frameon=False);axes[1].set_title('Whole-process memory, including RR load')
    axes[1].set_ylim(bottom=0)
    fig.suptitle('GEMM core-count and resource study');fig.text(.5,.01,'Observed runtime ranges, not CIs. Core-count stages ran at different times; HWM is sampled.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.045,1,.94]);save(fig,'cores_memory')
    fig,axes=plt.subplots(1,2,figsize=(9,4.5))
    for variant,color in [('frozen','#0072B2'),('pipeline','#D55E00')]:
        points=[next(r for r in data['configuration_summaries'] if r['case']=='gemm' and r['workers']==n and r['cache']=='rebuild' and r['variant']==variant) for n in [4,8,16]]
        axes[0].plot([4,8,16],[r['stage_median_seconds'].get('lookahead_build',float('nan')) for r in points],'-o',label=variant,color=color)
        axes[1].plot([4,8,16],[r['process_seconds']['median'] if r['process_seconds'] else float('nan') for r in points],'-o',label=variant,color=color)
    for ax,title in zip(axes,['Lookahead build','Complete VPR process']):
        ax.set_xticks([4,8,16]);ax.set_xlabel('Physical cores');ax.set_ylabel('Median wall time (s)');ax.set_ylim(bottom=0);ax.set_title(title);ax.legend(frameon=False);ax.grid(alpha=.2)
    fig.suptitle('GEMM observed scaling');fig.text(.5,.01,'Three runtime samples per point; core-count stages ran at different times on a shared host.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.045,1,.94]);save(fig,'cores_time')
    print(out)


if __name__=='__main__':main()
