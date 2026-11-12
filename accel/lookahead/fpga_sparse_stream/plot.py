from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[3];r=root/'results/fpga_sparse_stream_20261112'
rows=json.load(open(r/'analysis.json'))['small_runs']
fig,axs=plt.subplots(1,3,figsize=(11,3.5),layout='constrained')
parts=[('init_cycles','Init + control'),('expansion_and_fence_cycles','Expand + fence'),('commit_cycles','Commit'),('closure_cycles','Closure')]
colors=['#9ca3af','#2f6f9f','#d6a03d','#a34f64']
for ax,case in zip(axs,['native_d3_w8','native_d4_w8','stress_random']):
 selected=[next(d for d in rows if d['run']==f'{v}_{case}_l60_rtl') for v in ['f0_batch','batch_f1']]
 bottom=[0,0]
 for (key,label),color in zip(parts,colors):
  values=[(d[key]+(d['resident_cycles']-sum(d[k] for k,_ in parts) if key=='init_cycles' else 0))/1000 for d in selected];ax.bar(['F0','F1'],values,bottom=bottom,label=label,color=color,width=.6)
  bottom=[a+b for a,b in zip(bottom,values)]
 ax.set_title(case.replace('native_','').replace('_w8',''))
 ax.set_ylabel('Complete-batch RTL cycles (thousands)');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
 for i,d in enumerate(selected):ax.annotate(f"{d['resident_cycles']:,}",(i,bottom[i]),xytext=(0,4),textcoords='offset points',ha='center',fontsize=8)
 ax.margins(y=.16)
fig.suptitle('8-lane sparse tile, 60-cycle assumed memory latency; no qualified FPGA seconds')
axs[-1].legend(fontsize=8,loc='upper right')
out=r/'figures';out.mkdir(exist_ok=True)
fig.savefig(out/'tile_phase_cycles.png',dpi=180)
fig.savefig(out/'tile_phase_cycles.svg')
