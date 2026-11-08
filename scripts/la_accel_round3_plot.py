"""Export measured software and simulated RTL evidence as standalone figures."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',default='native_d3_w8');a=p.parse_args()
 d=json.loads(a.report.read_text());a.output.mkdir(parents=True,exist_ok=False)
 fig,axes=plt.subplots(2,2,figsize=(14,9),layout='constrained');ax=axes[0,0]
 rows=[v for v in d['software'] if v['case']==a.case];y=np.arange(len(rows));labels=[v['kind'].upper()+' '+str(v['parallel']) for v in rows]
 for delta,key,label,color in [(-.17,'cold_e1_s','Cold first call','#627da6'),(.17,'warm_e1_s','Warm E1','#1c706c')]:
  values=np.array([v[key]['median']*1e6 for v in rows]);low=values-np.array([v[key]['minimum']*1e6 for v in rows]);high=np.array([v[key]['maximum']*1e6 for v in rows])-values
  ax.barh(y+delta,values,height=.32,label=label,color=color);ax.errorbar(values,y+delta,xerr=[low,high],fmt='none',ecolor='black',capsize=2,lw=.7)
 ax.set(yticks=y,yticklabels=labels,xscale='log',xlabel='Microseconds (log scale)',title='CPU wall time / CUDA events: measured');ax.invert_yaxis();ax.legend(fontsize=8)
 sha=rows[0]['workload_sha256'];hardware={v['name']:v for v in d['hardware']}
 rtl=[v for v in d['bounded'] if v['rtl_time_s'] is not None and hardware[v['source_hls']]['binding']['workload']==sha]
 names=[v['name'].removeprefix('bounded_') for v in rtl];y=np.arange(len(rtl));ax=axes[0,1]
 ax.barh(y,[v['rtl_time_s']*1e3 for v in rtl],color='#a64d3c',label='Bounded memory')
 ax.scatter([hardware[v['source_hls']]['functional_cycles']/hardware[v['source_hls']]['verified_mhz']/1000 for v in rtl],y,color='black',marker='|',s=120,label='Functional AXI')
 best=min(v['warm_e1_s']['median'] for v in rows);ax.axvline(best*1e3,ls='--',color='#1c706c',label='Best measured warm software')
 ax.set(yticks=y,yticklabels=names,xscale='log',xlabel='Milliseconds at timing-clean OOC target (log)',title='RTL cycle-derived E1: not board measurements');ax.invert_yaxis();ax.legend(fontsize=8)
 ax=axes[1,0];bottom=np.zeros(len(rtl))
 for prefix,color in [('graph','#627da6'),('queue','#a64d3c'),('state','#c9a64c'),('result','#1c706c')]:
  values=[sum(p['reads']+p['writes'] for name,p in zip(v['config']['ports'],v['result']['memory']['ports']) if name.startswith(prefix)) for v in rtl]
  ax.barh(y,values,left=bottom,label=prefix,color=color);bottom+=values
 ax.set(yticks=y,yticklabels=names,xlabel='AXI requests, complete batch',title='Actual bounded RTL traffic');ax.invert_yaxis();ax.legend(fontsize=8)
 ax=axes[1,1];vals=[hardware[v['source_hls']]['resources']['LUT'] for v in rtl];ax.barh(y,vals,color='#627da6')
 for i,v in enumerate(rtl):
  h=hardware[v['source_hls']];ax.text(vals[i]*1.01,i,f'{h["verified_mhz"]:g} MHz',va='center',fontsize=8)
 ax.set(yticks=y,yticklabels=names,xlabel='LUTs after implementation',title='Core OOC resources and verified target');ax.invert_yaxis();ax.set_xlim(0,max(vals)*1.28)
 fig.suptitle(f'Round 3 · {a.case} · STRICT_FP32 / complete native samples',fontsize=14)
 for ax in axes.flat:ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
 for ext in ['pdf','svg','png']:fig.savefig(a.output/('evidence.'+ext),dpi=160,bbox_inches='tight',pad_inches=.15)
 plt.close(fig)
 (a.output/'metadata.json').write_text(json.dumps({'report':str(a.report.resolve()),'case':a.case,'evidence':'Software measured; RTL simulated under synthetic memory constraints; OOC frequency only.'},indent=2)+'\n')
if __name__=='__main__':main()
