import pathlib,json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop';out=r/'figures';out.mkdir(exist_ok=True)
data={p.stem:json.load(open(p)) for p in (r/'large').glob('*.json') if p.name not in ['execution_plan.json'] and not p.name.endswith('.receipt.json')}
assert len(data)==12
baseline=json.load(open(r/'baselines/summary.json'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160})
fig,ax=plt.subplots(figsize=(9,4.6));labels=[];values=[];errors=[];colors=[]
for case,name in [('bnn_export','BNN'),('lstm_s2','LSTM')]:
 cpu=next(x for x in baseline if x['case']==case and x['backend']=='original_ALT_CPU');labels.append(name+'\nALT CPU');values.append(cpu['mean_s']);errors.append(cpu['sample_sd_s']);colors.append('#0072B2')
 if case=='bnn_export':
  gpu=next(x for x in baseline if x['case']==case and x['backend']=='gpu_compact');labels.append(name+'\ncompact CUDA*');values.append(gpu['mean_s']);errors.append(gpu['sample_sd_s']);colors.append('#009E73')
 labels.append(name+'\nFPGA model**');values.append(data[('bnn' if name=='BNN' else 'lstm')+'_F1_central']['cycles']/2e8);errors.append(0);colors.append('#D55E00')
x=np.arange(len(labels));ax.bar(x,values,color=colors);
for i,e in enumerate(errors):
 if e:ax.errorbar(i,values[i],yerr=e,fmt='none',color='black',capsize=3)
ax.set_xticks(x,labels);ax.set_yscale('log');ax.set_ylabel('Complete resident batch (seconds, log scale)');ax.set_ylim(.1,1e5)
for i,v in enumerate(values):ax.text(i,v*1.35,f'{v:,.3f}',ha='center',fontsize=9)
ax.set_title('40 real samples; all required internal work included');fig.text(.02,.01,'* R6.1 historical warm resident_s; separate host cohort.  ** Projected at assumed 200MHz; full clock not validated.',fontsize=8);fig.tight_layout(rect=(0,.04,1,1))
for ext in ['png','svg']:fig.savefig(out/f'resident_complete_batch.{ext}')
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10,4.6));sc=['central','bandwidth_64','bandwidth_192','latency_150','latency_600'];labels=['128 GB/s\n300 ns','64 GB/s\n300 ns','192 GB/s\n300 ns','128 GB/s\n150 ns','128 GB/s\n600 ns']
for ax,case,title in zip(axes,['bnn','lstm'],['BNN','LSTM']):
 vals=[data[case+'_F1_'+s]['cycles']/2e8 for s in sc];ax.bar(range(5),vals,color='#D55E00');ax.set_xticks(range(5),labels,fontsize=8);ax.set_ylabel('Projected seconds at 200MHz');ax.set_title(title+' / complete 40-sample F1');ax.ticklabel_format(axis='y',style='plain')
fig.text(.02,.01,'Integer link gaps: requested 64/128/192 GB/s become 51.2/102.4/102.4 GB/s; read/write share the link. No board calibration.',fontsize=8);fig.tight_layout(rect=(0,.05,1,1))
for ext in ['png','svg']:fig.savefig(out/f'memory_sensitivity.{ext}')
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10,4.5));phase_names=['Initialization','Directory scan','Graph expansion','Fence','Commit','Closure/output'];colors=['#999999','#0072B2','#E69F00','#CC79A7','#D55E00','#009E73']
for ax,case,title in zip(axes,['bnn','lstm'],['BNN','LSTM']):
 j=data[case+'_F1_central'];vals=np.array(j['phase_cycles'][:6])/j['cycles']*100;left=0
 for value,label,color in zip(vals,phase_names,colors):ax.barh([0],[value],left=left,label=label,color=color);left+=value
 ax.set_xlim(0,100);ax.set_yticks([]);ax.set_xlabel('Accounted complete-batch cycles (%)');ax.set_title(title+' / serial graph front end')
fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=3);fig.tight_layout(rect=(0,.18,1,1))
for ext in ['png','svg']:fig.savefig(out/f'cycle_breakdown.{ext}')
plt.close(fig)
print(out)
