"""Export standalone figures only from independently reviewed native measurements."""
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from prepare import sha256,write_json
from scaling_common import verified


def main():
    root=Path(__file__).resolve().parents[1]
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'results/native_flat_baseline_20261105'
    review=json.loads((out/'independent_review.json').read_text())
    if review['status']=='passed_failure_record':return
    assert review['status']=='passed';verified(review['analysis']);verified(review['summary'])
    data=json.loads((out/'analysis.json').read_text())
    names={'bnn':'BNN 3D','dla_like.medium':'DLA 3D','clma_2d':'clma 2D','bnn_2d':'BNN 2D'}
    groups=list(dict.fromkeys(k.rsplit('/',1)[0] for k in data['component_times']))
    arms=['per_group','pipeline','flat'];labels=['Per group','Pipeline','Global parallel_for']
    colors=['#718096','#007f86','#cf6736'];files=[]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,len(groups),figsize=(4.2*len(groups),4.1),squeeze=False)
    for ax,g in zip(axes.flat,groups):
        widths=sorted(int(k.rsplit('/',1)[1]) for k in data['component_times'] if k.startswith(g+'/'))
        x=np.arange(len(widths));bw=.25
        for i,a in enumerate(arms):
            values=[data['component_times'][f'{g}/{w}'][a] for w in widths]
            bars=ax.bar(x+(i-1)*bw,values,bw,color=colors[i],label=labels[i])
            ax.bar_label(bars,fmt='%.2f',fontsize=8,padding=2)
        ax.set_xticks(x,[str(w)+' cores' for w in widths]);ax.set_title(names.get(g,g));ax.set_ylabel('Complete lookahead (s), median of 3')
        ax.set_ylim(0,ax.get_ylim()[1]*1.15);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle('Native lookahead construction: same corrected executable',fontsize=12)
    fig.text(.5,.015,'Shared host; one-iteration route tails are not legal end-to-end results. Formal runs exclude instrumentation.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.05,1,.93))
    for ext in ['png','pdf','svg']:
        f=out/('flat_component.'+ext);fig.savefig(f,dpi=180);files.append(f)
    plt.close(fig)
    fig,axes=plt.subplots(1,len(groups),figsize=(4.2*len(groups),4.3),squeeze=False)
    for ax,g in zip(axes.flat,groups):
        rows=[data['memory'][g+'/'+a] for a in arms]
        entry=[r['entry_mib'] for r in rows];growth=[r['observed_growth_mib'] for r in rows]
        x=np.arange(3)
        ax.bar(x,entry,color='#cbd5e0',label='Stage entry RSS')
        bars=ax.bar(x,growth,bottom=entry,color=colors,label='Observed growth')
        for i,r in enumerate(rows):ax.text(i,entry[i]+growth[i],f'+{growth[i]:.1f}',ha='center',va='bottom',fontsize=8)
        ax.set_xticks(x,['Group','Pipeline','Flat']);ax.set_title(names.get(g,g));ax.set_ylabel('Stage RSS (MiB), one diagnostic / arm')
        ax.set_ylim(0,ax.get_ylim()[1]*1.16);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle('Live RSS inside MapLookahead::compute (8 cores)',fontsize=12)
    fig.text(.5,.015,'Approximate statm samples, target 2 ms; observed peaks may miss transients. Not workspace-only memory or a hard bound.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.05,1,.93))
    for ext in ['png','pdf','svg']:
        f=out/('flat_memory.'+ext);fig.savefig(f,dpi=180);files.append(f)
    plt.close(fig)
    write_json(out/'figures.json',dict(source_review=dict(path=str(out/'independent_review.json'),sha256=sha256(out/'independent_review.json')),
        figures=[dict(path=str(f),sha256=sha256(f)) for f in files],visually_inspected=False))
    print('Exported',len(files),'figures',flush=True)


if __name__=='__main__':main()
