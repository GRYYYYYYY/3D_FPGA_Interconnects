import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105'
a=json.loads((OUT/'analysis.json').read_text());s=json.loads((OUT/'summary.json').read_text())
assert s['status']=='completed'
fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
keys=['stock_to_pipeline','fixed_serial_to_pipeline','per_group_to_pipeline'];names=['Stock → pipeline','Corrected serial → pipeline','Per-group → pipeline']
for i,m in enumerate(['rebuild','reuse']):
 vals=[a['equal_layout_aggregate'].get(m+'/'+k,float('nan')) for k in keys];axs[0].bar([x+i*.36 for x in range(3)],vals,width=.36,label=m)
axs[0].axhline(1,color='black',linewidth=.7);axs[0].set_xticks([x+.18 for x in range(3)],names,rotation=15);axs[0].set_ylabel('Native process speed ratio');axs[0].legend();axs[0].set_title('New architecture: 4 layouts / 2 circuits')
for c in ['tseng_s1','des_s1']:
 for comparison,style in [('stock_to_pipeline','-'),('per_group_to_pipeline','--')]:
  vals=[a['actual_cache_batches'].get(f'{c}/{comparison}/K{k}',{}).get('median',float('nan')) for k in [1,2,5]]
  axs[1].plot([1,2,5],vals,style,marker='o',label=c.split('_')[0]+' '+comparison.replace('_to_','→'))
axs[1].axhline(1,color='black',linewidth=.7);axs[1].set_xlabel('Requests per batch (correlated prefixes)');axs[1].set_ylabel('Native batch speed ratio');axs[1].legend(fontsize=7);axs[1].set_title('One rebuild, then cache reuse; shared host')
for ext in ['pdf','svg','png']:fig.savefig(OUT/('architecture_cache.'+ext),dpi=160)
plt.close(fig)
