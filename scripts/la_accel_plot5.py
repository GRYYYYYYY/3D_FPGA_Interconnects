"""Standalone figures; software measured, hardware cycles only (no verified clock)."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=json.loads(a.report.read_text());a.output.mkdir(exist_ok=False)
plt.rcParams.update({'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):
 for suffix in ['png','svg','pdf']:fig.savefig(a.output/(name+'.'+suffix),dpi=170,bbox_inches='tight')
 plt.close(fig)
rows=d['software']['new_measurements'];cases=['native_d6_w8_l1','native_d6_w8','native_d8_w8'];x=np.arange(3);fig,ax=plt.subplots(figsize=(8,4))
for i,backend in enumerate(['cpu','cuda']):
 vals=[min((z for z in rows if z['case']==c and z['backend']==backend),key=lambda z:z['warm_s']['median']) for c in cases];mid=np.array([v['warm_s']['median']*1e6 for v in vals]);lo=[m-v['warm_s']['minimum']*1e6 for m,v in zip(mid,vals)];hi=[v['warm_s']['maximum']*1e6-m for m,v in zip(mid,vals)];ax.bar(x+(i-.5)*.34,mid,.34,label=backend.upper(),yerr=[lo,hi],capsize=3)
ax.set_xticks(x,['6x6 single layer','6x6 two layers','8x8 held out']);ax.set_ylabel('Measured complete-batch warm E1 (us)');ax.set_yscale('log');ax.legend();fig.text(.01,-.02,'Best tested quota-aware CPU count; basic CUDA. Median of five process medians; whiskers show range.',fontsize=9);fig.tight_layout();save(fig,'new_software')
fig,ax=plt.subplots(figsize=(8,4));labels=['R4 early4 RTL','R5 ctx2 RTL','R5 ctx4 RTL','C1 budget at old 125MHz'];cycles=[23721]+[h['calls'][0]['rtl_cycles'] for h in d['hardware']]+[3239];bars=ax.bar(labels,cycles,color=['#517891','#5ca68e','#bf8344','#923f52']);ax.set_ylabel('Complete 3x3 warm E1 cycles / reference budget');ax.set_yscale('log');ax.tick_params(axis='x',labelsize=9)
for b,v in zip(bars,cycles):ax.text(b.get_x()+b.get_width()/2,v*1.06,f'{v:,}',ha='center',fontsize=9)
fig.text(.01,-.02,'R5 has no implemented frequency: cycles only, not FPGA latency. CPU reference budget is not an FPGA measurement.',fontsize=8);fig.tight_layout();save(fig,'rtl_cycles_gate')
