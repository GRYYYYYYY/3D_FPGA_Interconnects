"""Standalone figures from independently reviewed stage statistics."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105/scaling'
r=json.loads((OUT/'independent_review.json').read_text());assert r['status']=='passed'
graphs=['bnn','dla_like.medium','tseng_2d'];names=['BNN (3D)','DLA (3D)','tseng (2D, short stage)'];cores=[1,2,4,8,16]
colors={'per_group':'#4477AA','pipeline':'#EE7733'}
fig,axs=plt.subplots(2,3,figsize=(12,7),layout='constrained')
for j,(g,name) in enumerate(zip(graphs,names)):
 ax=axs[0,j]
 for a in ['per_group','pipeline']:
  v=[r['scaling'][f'{g}/{a}/{w}'] for w in cores];med=[x['median'] for x in v]
  ax.plot(cores,med,'o-',label=a.replace('_',' '),color=colors[a]);ax.fill_between(cores,[x['minimum'] for x in v],[x['maximum'] for x in v],color=colors[a],alpha=.14)
 ax.plot(cores,cores,':',color='gray',label='Ideal');ax.set_title(name);ax.set_ylabel('Speedup vs same method at 1 core');ax.set_ylim(0,17);ax.legend(fontsize=8)
 ax=axs[1,j];v=[r['incremental'][f'{g}/{w}'] for w in cores];med=[x['median'] for x in v]
 ax.plot(cores,med,'o-',color='#228833');ax.fill_between(cores,[x['minimum'] for x in v],[x['maximum'] for x in v],color='#228833',alpha=.15);ax.axhline(1,color='gray',linewidth=.8);ax.set_ylabel('Per-group / pipeline stage time');ax.set_ylim(.75,3.4);ax.set_xlabel('Physical cores')
 for ax in axs[:,j]:ax.set_xscale('log',base=2);ax.set_xticks(cores,[str(x) for x in cores]);ax.grid(axis='y',alpha=.2)
fig.suptitle('Complete lookahead construction — shared host, paired median and range (3 repeats)',fontsize=12)
for ext in ['pdf','svg','png']:fig.savefig(OUT/('scaling_review.'+ext),dpi=170)
plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(12,3.9),layout='constrained')
for ax,g,name in zip(axs,graphs,names):
 maxval=0
 for a in ['per_group','pipeline']:
  v=[r['memory_groups'][f'{g}/{a}/{w}'] for w in cores];med=[x['native_flow_median_mib'] for x in v];maxval=max(maxval,max(med))
  ax.plot(cores,med,'o-' if a=='per_group' else 's--',label=a.replace('_',' '),color=colors[a]);ax.fill_between(cores,[min(x['native_flow_max_rss_mib']) for x in v],[max(x['native_flow_max_rss_mib']) for x in v],color=colors[a],alpha=.15)
 ax.set_ylim(0,maxval*1.15);ax.set_xscale('log',base=2);ax.set_xticks(cores,[str(x) for x in cores]);ax.set_title(name);ax.set_xlabel('Physical cores');ax.set_ylabel('Native process lifetime max RSS (MiB)');ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
fig.suptitle('Process high-water marks include RR loading; they do not isolate lookahead workspace memory',fontsize=11)
for ext in ['pdf','svg','png']:fig.savefig(OUT/('memory_review.'+ext),dpi=170)
plt.close(fig)
print('Wrote scaling_review and memory_review in PDF/SVG/PNG')
