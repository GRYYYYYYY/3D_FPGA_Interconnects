"""Publication artifacts from verified report data; no target-frequency timing."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=json.loads(a.report.read_text());a.output.mkdir(parents=True,exist_ok=False)
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
 colors=['#405980','#28a087','#c17d32','#9469a9'];cases=['native_d3_w8','native_d4_w8','native_d5_w8','tseng_export','bnn_export'];labels=['3x3','4x4','5x5 held out','tseng','BNN']
 fig,ax=plt.subplots(figsize=(10,4.5));x=np.arange(len(cases));width=.19
 for i,(backend,mode) in enumerate([('cpu','full'),('cpu','early'),('cuda','full'),('cuda','early')]):
  rows=[min((s for s in d['software'] if s['case']==c and s['backend']==backend and s['mode']==mode),key=lambda s:s['warm_e1_s']['median']) for c in cases]
  y=np.array([s['warm_e1_s']['median']*1e6 for s in rows]);lo=np.array([s['warm_e1_s']['minimum']*1e6 for s in rows]);hi=np.array([s['warm_e1_s']['maximum']*1e6 for s in rows])
  ax.bar(x+(i-1.5)*width,y,width,label=backend.upper()+' '+mode,color=colors[i],yerr=[y-lo,hi-y],capsize=2)
 ax.set_xticks(x,labels);ax.set_yscale('log');ax.set_ylabel('Measured warm E1 (microseconds)');ax.legend(ncol=4,loc='upper left');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
 fig.text(.01,.01,'Best tested CPU worker count per mode; basic CUDA, real sample CTAs. Bars: median of process medians; whiskers: process-median range.',fontsize=8)
 fig.tight_layout(rect=[0,.05,1,1]);save(fig,a.output/'software_algorithms')
 fig,axes=plt.subplots(1,2,figsize=(11,4.5));x=np.arange(3)
 for i,h in enumerate(d['hardware']):
  if len(h['calls'])!=3:continue
  y=[c['warm_e1_cycles'] for c in h['calls']];axes[0].bar(x+(i-1.5)*width,y,width,label=h['name'],color=colors[i])
 axes[0].set_xticks(x,labels[:3]);axes[0].set_ylabel('Verified warm E1 RTL cycles');axes[0].set_yscale('log');axes[0].legend(ncol=2);axes[0].grid(axis='y',alpha=.2);axes[0].set_axisbelow(True)
 for i,engines in enumerate([1,4]):
  rows=[next((c for c in d['comparisons'] if c['case']==case and c['hardware']=='early_'+str(engines)),None) for case in cases[:3]]
  if any(c is None for c in rows):continue
  axes[1].bar(x+(i-.5)*.3,[c['same_algorithm_speedup'] for c in rows],.3,label=str(engines)+' on-chip engine(s)',color=colors[i+1])
 axes[1].axhline(1,color='black',lw=1,ls='--');axes[1].set_xticks(x,labels[:3]);axes[1].set_ylabel('Best software early E1 / FPGA early E1');axes[1].legend();axes[1].grid(axis='y',alpha=.2);axes[1].set_axisbelow(True)
 fig.text(.01,.01,'FPGA: functional RTL cycles at an internal OOC STA-verified clock; reset/writeout included. External AXI integration and board timing are unverified.',fontsize=8)
 fig.tight_layout(rect=[0,.05,1,1]);save(fig,a.output/'hardware_cycles_and_budget')

def save(fig,path):
 for suffix in ['pdf','svg','png']:fig.savefig(str(path)+'.'+suffix,dpi=180,bbox_inches='tight')
 plt.close(fig)
if __name__=='__main__':main()
