"""Plot observed software times separately from functional RTL cycles."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();d=json.loads(a.report.read_text());out=a.report.parent
 fig,axes=plt.subplots(1,3,figsize=(15,4.5),layout='constrained');sw=d['software_summary']['E1_resident'];x=np.arange(2);width=.34
 for i,(label,keys,color) in enumerate([('CPU: 8 physical cores',['cpu_tseng_export','cpu_bnn_export'],'#246B8E'),('CUDA: H100',['tseng_export_B8','bnn_export_B40'],'#DB7A35')]):
  vals=np.array([sw[k]['median'] for k in keys]);lo=np.array([sw[k]['range'][0] for k in keys]);hi=np.array([sw[k]['range'][1] for k in keys]);bars=axes[0].bar(x+(i-.5)*width,vals,width,label=label,color=color,yerr=[vals-lo,hi-vals],capsize=3)
  axes[0].bar_label(bars,labels=[f'{v:.4g}' for v in vals],padding=4,fontsize=8)
 axes[0].set(xticks=x,xticklabels=['tseng (8 samples)','BNN (40 samples)'],yscale='log',ylabel='Seconds, log scale',title='E1: measured resident batch');axes[0].legend(fontsize=8)
 rows=d['native_software_summary']['E2_native'];names=['stock','per_group','pipeline','flat'];v=[rows[k]['median'] for k in names]
 bars=axes[1].bar(names,v,color='#246B8E',yerr=[[rows[k]['median']-rows[k]['range'][0] for k in names],[rows[k]['range'][1]-rows[k]['median'] for k in names]],capsize=3);axes[1].bar_label(bars,fmt='%.2f',padding=4)
 axes[1].set(ylabel='Seconds (0.01 s log resolution)',title='E2: measured native builder\n8 physical cores; cohort in report.json');axes[1].tick_params(axis='x',rotation=25)
 by={r['variant']:r for r in d['hls']};names=['hls_tiny','hls_cache_off','hls_heap31','hls_label64','hls_eligible','hls_dual_ports_v3'];labels=['F0','cache off','heap31','label64','CSR','dual'];values=[by[k]['core_cycles'] for k in names]
 bars=axes[2].barh(labels,values,color=['#64748b','#64748b','#2D8B70','#2D8B70','#2D8B70','#2D8B70']);axes[2].bar_label(bars,fmt='%d',padding=4,fontsize=8);axes[2].set(xlabel='RTL cycles; full tiny RRG, 4 samples',title='Functional AXI model\nnot measured HBM execution');axes[2].set_xlim(0,max(values)*1.3);axes[2].invert_yaxis()
 for ax in axes:ax.spines[['top','right']].set_visible(False)
 fig.suptitle('STRICT_FP32 lookahead: observed evidence, target ordering unverified',fontsize=13)
 for ext in ['pdf','svg','png']:fig.savefig(out/('evidence.'+ext),dpi=180)
 plt.close(fig);print(out/'evidence.pdf')
if __name__=='__main__':main()
