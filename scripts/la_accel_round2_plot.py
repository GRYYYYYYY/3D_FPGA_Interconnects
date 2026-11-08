"""Export separate, scope-matched RTL and measured software comparison panels."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=json.loads(a.report.read_text());a.output.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    hls={r['name']:r for r in data['hls']}
    names=['hls_resident_heap127','hls_resident_labels','hls_resident']
    ax=axes[0,0];bars=ax.bar(['heap127','+ labels64','+ costs64'],[hls[n]['cycles']/1000 for n in names],color='#477aab')
    ax.bar_label(bars,fmt='%.1f',padding=3);ax.set_ylim(0,340);ax.set_ylabel('thousand RTL cycles')
    ax.set_title('A  Complete tiny native graph — functional AXI')
    bounded={r['name']:r['result'] for r in data['bounded_memory'] if r['result']['status']=='passed'}
    names=[n for n in ['bounded_f0_final','bounded_cacheoff_final','bounded_heap31_minimal','bounded_dual_final','bounded_resident_final'] if n in bounded]
    labels=dict(bounded_f0_final='F0',bounded_cacheoff_final='cache off',bounded_heap31_minimal='heap31',bounded_dual_final='dual engine',bounded_resident_final='combined')
    ax=axes[0,1];bars=ax.bar([labels[n] for n in names],[bounded[n]['rtl_cycles'][0]/1000 for n in names],color='#348780')
    ax.bar_label(bars,fmt='%.0f',padding=3);ax.set_ylabel('thousand RTL cycles');ax.set_ylim(top=3100)
    ax.set_title('B  Same tiny graph — bounded synthetic AXI')
    ax=axes[1,0];vals=[data['live'][n]['resident_s'] for n in ['cpu','cuda']]
    med=[r['median']*1000 for r in vals]
    bars=ax.bar(['CPU, 8 cores','CUDA, H100'],med,color=['#477aab','#c47c40'],
        yerr=[[m-r['minimum']*1000 for m,r in zip(med,vals)],[r['maximum']*1000-m for m,r in zip(med,vals)]],capsize=3)
    ax.bar_label(bars,fmt='%.1f',padding=4);ax.set_ylabel('milliseconds, median of 3');ax.set_ylim(top=850)
    ax.set_title('C  tseng — resident kernel, measured')
    ax=axes[1,1];names=list(data['native_controls']);values=[data['native_controls'][n]['median'] for n in names]
    names+=['CPU adapter','CUDA adapter'];values +=[data['live'][n]['complete_wire_builder_s']['median'] for n in ['cpu','cuda']]
    bars=ax.bar(names,values,color=['#8d98a6']*(len(names)-2)+['#477aab','#c47c40'])
    ax.set_yscale('log');ax.set_ylim(.01,2);ax.bar_label(bars,fmt='%.2f',padding=3);ax.tick_params(axis='x',labelrotation=25)
    ax.set_ylabel('seconds, median of 3 (log scale)');ax.set_title('D  tseng — complete wire builder, measured')
    for ax in axes.flat:ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Matched comparisons within each panel; no cross-workload FPGA speedup claim',fontsize=12)
    fig.savefig(a.output/'evidence.pdf');fig.savefig(a.output/'evidence.svg');fig.savefig(a.output/'evidence.png',dpi=180)


if __name__=='__main__':main()
